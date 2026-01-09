"""
AI Service - Analyze documents using OpenAI GPT
"""

import logging
import openai
from typing import Dict
from django.conf import settings

logger = logging.getLogger(__name__)


class AIService:
    """
    Service for analyzing document text using OpenAI GPT
    """

    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS

    def analyze_document(self, text: str, document_type: str) -> Dict:
        """
        Analyze document text and provide structured insights

        Args:
            text: Extracted text from document
            document_type: Type of document (e.g., 'medical_records', 'decision_letter')

        Returns:
            dict with keys:
                - analysis: Structured analysis (dict)
                - model: Model used
                - tokens_used: Number of tokens consumed
        """
        # Truncate text if too long (leave room for response)
        max_input_tokens = self.max_tokens - 1000
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = max_input_tokens * 4
        truncated_text = text[:max_chars] if len(text) > max_chars else text

        if len(text) > max_chars:
            logger.warning(f"Text truncated from {len(text)} to {len(truncated_text)} characters")

        # Build prompt based on document type
        system_prompt = self._get_system_prompt(document_type)
        user_prompt = self._build_user_prompt(truncated_text, document_type)

        try:
            logger.info(f"Sending {len(truncated_text)} characters to OpenAI for analysis")

            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=1000,
            )

            # Extract response
            analysis_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            # Parse structured output (expecting JSON-like format)
            analysis = self._parse_analysis(analysis_text)

            logger.info(f"Analysis complete. Used {tokens_used} tokens")

            return {
                'analysis': analysis,
                'model': self.model,
                'tokens_used': tokens_used,
            }

        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            raise

    def _get_system_prompt(self, document_type: str) -> str:
        """
        Get system prompt tailored to document type
        """
        base_prompt = """You are an expert VA benefits advisor helping veterans understand their documents and claims.
Your role is to analyze VA-related documents and provide clear, actionable insights in plain language.

Always be:
- Factual and accurate
- Supportive and empathetic
- Clear and concise
- Focused on actionable next steps

Never:
- Provide legal advice
- Make guarantees about VA decisions
- Include personal opinions
- Use overly technical jargon"""

        document_specific = {
            'decision_letter': "\n\nFocus on: Decision outcome, reasons for approval/denial, effective date, appeal rights and deadlines.",
            'medical_records': "\n\nFocus on: Diagnoses mentioned, treatment history, service connection evidence, any gaps in medical evidence.",
            'nexus_letter': "\n\nFocus on: Medical opinion strength, link to service, supporting evidence cited.",
            'service_records': "\n\nFocus on: Service dates, events/injuries documented, potential service connection events.",
        }

        return base_prompt + document_specific.get(document_type, "")

    def _build_user_prompt(self, text: str, document_type: str) -> str:
        """
        Build user prompt with document text
        """
        return f"""Analyze this VA-related document and provide:

1. **Document Summary** (2-3 sentences): What is this document and what are the key points?

2. **Key Findings** (bullet points): List the most important information from this document.

3. **Evidence Assessment**:
   - What evidence for service connection is present?
   - What evidence might be missing or weak?

4. **Suggested Next Steps** (bullet points): Based on this document, what should the veteran consider doing next?

5. **Service Connection Elements**:
   - In-service event/injury: [present/mentioned/missing]
   - Current diagnosis: [present/clear/missing]
   - Nexus (medical link): [established/suggested/missing]

Document text:
{text}

Provide your analysis in clear sections as outlined above."""

    def _parse_analysis(self, analysis_text: str) -> Dict:
        """
        Parse AI response into structured format
        """
        # For MVP, return the text as-is with basic structure
        # In future, could parse into more structured JSON

        return {
            'summary': analysis_text,
            'raw_response': analysis_text,
            'structured': True,  # Flag for template to know this is structured
        }
