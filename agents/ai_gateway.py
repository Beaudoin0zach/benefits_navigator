"""
AI Gateway - Centralized OpenAI API interface for Benefits Navigator.

This module provides a single entry point for all OpenAI API calls with:
- Timeout handling (60s default, configurable)
- Retry with exponential backoff (3 retries by default)
- Pydantic schema validation for structured outputs
- Result types for error handling (no exceptions raised to callers)
- Consolidated input sanitization
- Centralized token/cost tracking
- PII-safe logging
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Callable, Generic, Optional, TypeVar

from django.conf import settings
from openai import APIError, APITimeoutError, OpenAI, RateLimitError
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T')
U = TypeVar('U')


# =============================================================================
# ERROR TYPES
# =============================================================================

class ErrorCode(Enum):
    """Standard error codes for AI gateway operations."""
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    API_ERROR = "api_error"
    VALIDATION_ERROR = "validation_error"
    PARSE_ERROR = "parse_error"
    SANITIZATION_ERROR = "sanitization_error"
    UNKNOWN = "unknown"


@dataclass
class GatewayError:
    """Structured error from AI gateway operations."""
    code: ErrorCode
    message: str
    retryable: bool
    details: Optional[dict] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            'code': self.code.value,
            'message': self.message,
            'retryable': self.retryable,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
        }


# =============================================================================
# RESULT TYPE
# =============================================================================

@dataclass
class Result(Generic[T]):
    """
    Result type for gateway operations.

    Either contains a success value or an error, never both.
    Callers should check is_success before accessing value.

    Usage:
        result = gateway.complete(...)
        if result.is_success:
            process(result.value)
        else:
            handle_error(result.error)
    """
    _value: Optional[T] = None
    _error: Optional[GatewayError] = None
    tokens_used: int = 0
    cost_estimate: Decimal = Decimal('0')
    duration_ms: int = 0

    @property
    def is_success(self) -> bool:
        return self._error is None

    @property
    def is_failure(self) -> bool:
        return self._error is not None

    @property
    def value(self) -> T:
        if self._error is not None:
            raise ValueError(f"Cannot access value on failed result: {self._error.message}")
        return self._value

    @property
    def error(self) -> GatewayError:
        if self._error is None:
            raise ValueError("Cannot access error on successful result")
        return self._error

    @classmethod
    def success(
        cls,
        value: T,
        tokens: int = 0,
        cost: Decimal = Decimal('0'),
        duration_ms: int = 0
    ) -> 'Result[T]':
        return cls(_value=value, tokens_used=tokens, cost_estimate=cost, duration_ms=duration_ms)

    @classmethod
    def failure(
        cls,
        error: GatewayError,
        tokens: int = 0,
        duration_ms: int = 0
    ) -> 'Result[T]':
        return cls(_error=error, tokens_used=tokens, duration_ms=duration_ms)

    def map(self, fn: Callable[[T], U]) -> 'Result[U]':
        """Transform the value if successful, propagate error if not."""
        if self.is_success:
            try:
                return Result.success(
                    fn(self._value),
                    self.tokens_used,
                    self.cost_estimate,
                    self.duration_ms
                )
            except Exception as e:
                return Result.failure(GatewayError(
                    code=ErrorCode.UNKNOWN,
                    message=str(e),
                    retryable=False
                ))
        return Result.failure(self._error, self.tokens_used, self.duration_ms)


# =============================================================================
# RESPONSE TYPES
# =============================================================================

@dataclass
class CompletionResponse:
    """Raw completion response from OpenAI."""
    content: str
    tokens_used: int
    model: str
    finish_reason: str


@dataclass
class StructuredResponse(Generic[T]):
    """Structured response validated against a Pydantic schema."""
    data: T
    tokens_used: int
    model: str
    raw_content: str


# =============================================================================
# INPUT SANITIZATION
# =============================================================================

# Patterns that indicate prompt injection attempts
INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous",
    "disregard previous",
    "forget previous",
    "new instructions:",
    "system prompt:",
    "you are now",
    "act as",
    "pretend to be",
    "roleplay as",
    "ignore the above",
    "ignore everything above",
    "do not follow",
    "override",
    "bypass",
]


def sanitize_input(text: str) -> str:
    """
    Sanitize user-provided text to prevent prompt injection attacks.

    This function:
    1. Removes/redacts common prompt injection patterns
    2. Preserves legitimate document content
    3. Does NOT log the input (may contain PII)

    Args:
        text: User-provided text (may contain PII, document content)

    Returns:
        Sanitized text safe for inclusion in prompts
    """
    if not text:
        return ""

    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern in text_lower:
            # Replace with redaction marker
            text = re.sub(
                re.escape(pattern),
                f"[REDACTED: {pattern[:10]}...]",
                text,
                flags=re.IGNORECASE
            )

    return text


# =============================================================================
# GATEWAY CONFIGURATION
# =============================================================================

@dataclass
class GatewayConfig:
    """Configuration for AI Gateway."""
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 4000
    default_temperature: float = 0.3
    timeout_seconds: int = 60
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0

    @classmethod
    def from_settings(cls) -> 'GatewayConfig':
        """Create config from Django settings."""
        return cls(
            model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
            max_tokens=getattr(settings, 'OPENAI_MAX_TOKENS', 4000),
            timeout_seconds=getattr(settings, 'OPENAI_TIMEOUT_SECONDS', 60),
            max_retries=getattr(settings, 'OPENAI_MAX_RETRIES', 3),
            retry_base_delay=getattr(settings, 'OPENAI_RETRY_BASE_DELAY', 1.0),
            retry_max_delay=getattr(settings, 'OPENAI_RETRY_MAX_DELAY', 60.0),
        )


# =============================================================================
# AI GATEWAY
# =============================================================================

class AIGateway:
    """
    Centralized gateway for all OpenAI API calls.

    Features:
    - Single entry point for all AI operations
    - Automatic retry with exponential backoff
    - Timeout handling
    - Pydantic schema validation
    - Result types (no exceptions raised)
    - Token and cost tracking
    - PII-safe logging

    Usage:
        gateway = AIGateway()

        # Raw completion
        result = gateway.complete(
            system_prompt="You are a helpful assistant.",
            user_prompt="Analyze this document.",
        )

        # Structured completion with Pydantic validation
        result = gateway.complete_structured(
            system_prompt="Extract data as JSON.",
            user_prompt="Document text here.",
            response_schema=MyPydanticModel,
        )
    """

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig.from_settings()
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            self._client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=self.config.timeout_seconds,
            )
        return self._client

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        sanitize: bool = True,
    ) -> Result[CompletionResponse]:
        """
        Make a chat completion request with retry and timeout handling.

        Args:
            system_prompt: System message (instructions)
            user_prompt: User message (may contain document content)
            temperature: Override default temperature
            max_tokens: Override default max tokens
            model: Override default model
            sanitize: Whether to sanitize user_prompt (default True)

        Returns:
            Result containing CompletionResponse or GatewayError
        """
        start_time = time.time()

        # Sanitize user input if requested
        if sanitize:
            user_prompt = sanitize_input(user_prompt)

        model = model or self.config.model
        temperature = temperature if temperature is not None else self.config.default_temperature
        max_tokens = max_tokens or self.config.max_tokens

        last_error: Optional[Exception] = None
        tokens_used = 0

        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                content = response.choices[0].message.content or ""
                tokens_used = response.usage.total_tokens if response.usage else 0
                finish_reason = response.choices[0].finish_reason or "unknown"

                duration_ms = int((time.time() - start_time) * 1000)
                cost = self._estimate_cost(tokens_used, model)

                # Log success without PII
                logger.info(
                    f"AI completion successful: model={model} tokens={tokens_used} "
                    f"duration_ms={duration_ms}"
                )

                return Result.success(
                    CompletionResponse(
                        content=content,
                        tokens_used=tokens_used,
                        model=model,
                        finish_reason=finish_reason,
                    ),
                    tokens=tokens_used,
                    cost=cost,
                    duration_ms=duration_ms,
                )

            except APITimeoutError as e:
                last_error = e
                logger.warning(f"AI timeout (attempt {attempt + 1}/{self.config.max_retries + 1})")
                if attempt < self.config.max_retries:
                    self._wait_with_backoff(attempt)

            except RateLimitError as e:
                last_error = e
                logger.warning(f"AI rate limited (attempt {attempt + 1}/{self.config.max_retries + 1})")
                if attempt < self.config.max_retries:
                    self._wait_with_backoff(attempt, multiplier=2.0)

            except APIError as e:
                last_error = e
                logger.error(f"AI API error (attempt {attempt + 1}/{self.config.max_retries + 1}): {e}")
                if attempt < self.config.max_retries and self._is_retryable(e):
                    self._wait_with_backoff(attempt)
                else:
                    break

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected AI error: {e}", exc_info=True)
                break

        # All retries exhausted or non-retryable error
        duration_ms = int((time.time() - start_time) * 1000)
        error = self._create_error_from_exception(last_error)

        return Result.failure(error, tokens=tokens_used, duration_ms=duration_ms)

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel],
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        sanitize: bool = True,
    ) -> Result[StructuredResponse]:
        """
        Make a completion request and validate response against Pydantic schema.

        Args:
            system_prompt: System message
            user_prompt: User message
            response_schema: Pydantic model class for validation
            temperature: Override default temperature
            model: Override default model
            sanitize: Whether to sanitize user_prompt

        Returns:
            Result containing validated StructuredResponse or GatewayError
        """
        # Get raw completion
        result = self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            model=model,
            sanitize=sanitize,
        )

        if result.is_failure:
            return Result.failure(result.error, result.tokens_used, result.duration_ms)

        # Parse and validate JSON
        raw_content = result.value.content
        json_data = self._extract_json(raw_content)

        if json_data is None:
            return Result.failure(
                GatewayError(
                    code=ErrorCode.PARSE_ERROR,
                    message="Failed to extract JSON from response",
                    retryable=True,
                    details={'raw_content_preview': raw_content[:500]},
                ),
                tokens=result.tokens_used,
                duration_ms=result.duration_ms,
            )

        try:
            validated = response_schema.model_validate(json_data)
            return Result.success(
                StructuredResponse(
                    data=validated,
                    tokens_used=result.tokens_used,
                    model=result.value.model,
                    raw_content=raw_content,
                ),
                tokens=result.tokens_used,
                cost=result.cost_estimate,
                duration_ms=result.duration_ms,
            )
        except ValidationError as e:
            return Result.failure(
                GatewayError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message=f"Response validation failed: {e}",
                    retryable=False,
                    details={'validation_errors': e.errors()},
                ),
                tokens=result.tokens_used,
                duration_ms=result.duration_ms,
            )

    def _extract_json(self, content: str) -> Optional[dict]:
        """Extract JSON from response, handling markdown code blocks."""
        # Try to find JSON in code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from AI response")
            return None

    def _wait_with_backoff(self, attempt: int, multiplier: float = 1.0) -> None:
        """Wait with exponential backoff."""
        delay = min(
            self.config.retry_base_delay * (2 ** attempt) * multiplier,
            self.config.retry_max_delay
        )
        logger.info(f"Waiting {delay:.1f}s before retry")
        time.sleep(delay)

    def _is_retryable(self, error: APIError) -> bool:
        """Determine if an API error is retryable."""
        if hasattr(error, 'status_code'):
            return error.status_code in {500, 502, 503, 504}
        return False

    def _create_error_from_exception(self, exc: Exception) -> GatewayError:
        """Create a GatewayError from an exception."""
        if isinstance(exc, APITimeoutError):
            return GatewayError(
                code=ErrorCode.TIMEOUT,
                message="Request timed out after retries",
                retryable=True,
            )
        elif isinstance(exc, RateLimitError):
            return GatewayError(
                code=ErrorCode.RATE_LIMITED,
                message="Rate limit exceeded after retries",
                retryable=True,
            )
        elif isinstance(exc, APIError):
            return GatewayError(
                code=ErrorCode.API_ERROR,
                message=str(exc),
                retryable=self._is_retryable(exc),
            )
        else:
            return GatewayError(
                code=ErrorCode.UNKNOWN,
                message=str(exc) if exc else "Unknown error",
                retryable=False,
            )

    def _estimate_cost(self, tokens: int, model: str) -> Decimal:
        """Estimate cost based on token usage."""
        # Pricing per token (approximate)
        rates = {
            'gpt-3.5-turbo': Decimal('0.000002'),  # $0.002 per 1K tokens
            'gpt-4': Decimal('0.00003'),  # $0.03 per 1K tokens
            'gpt-4o': Decimal('0.000015'),  # $0.015 per 1K tokens
            'gpt-4o-mini': Decimal('0.00000015'),  # $0.00015 per 1K tokens
        }
        rate = rates.get(model, Decimal('0.000002'))
        return Decimal(str(tokens)) * rate


# =============================================================================
# MODULE-LEVEL CONVENIENCE
# =============================================================================

# Default gateway instance (singleton)
_default_gateway: Optional[AIGateway] = None


def get_gateway() -> AIGateway:
    """Get the default gateway instance (singleton)."""
    global _default_gateway
    if _default_gateway is None:
        _default_gateway = AIGateway()
    return _default_gateway


def reset_gateway() -> None:
    """Reset the default gateway (useful for testing)."""
    global _default_gateway
    _default_gateway = None


def complete(
    system_prompt: str,
    user_prompt: str,
    **kwargs
) -> Result[CompletionResponse]:
    """Convenience function for raw completion."""
    return get_gateway().complete(system_prompt, user_prompt, **kwargs)


def complete_structured(
    system_prompt: str,
    user_prompt: str,
    response_schema: type[BaseModel],
    **kwargs
) -> Result[StructuredResponse]:
    """Convenience function for structured completion."""
    return get_gateway().complete_structured(
        system_prompt, user_prompt, response_schema, **kwargs
    )
