"""
Celery tasks for document processing
"""

import time
import logging
from celery import shared_task
from django.utils import timezone

from .models import Document
from .services.ocr_service import OCRService
from .services.ai_service import AIService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id):
    """
    Async task to process uploaded document:
    1. Extract text via OCR
    2. Analyze with AI
    3. Save results

    This task is accessible-aware: it updates status fields that
    are announced to screen readers via ARIA live regions
    """
    start_time = time.time()

    try:
        # Get document
        document = Document.objects.get(id=document_id)
        document.mark_processing()

        logger.info(f"Starting OCR processing for document {document_id}")

        # Step 1: OCR Processing
        ocr_service = OCRService()
        ocr_result = ocr_service.extract_text(document.file.path)

        document.ocr_text = ocr_result['text']
        document.ocr_confidence = ocr_result.get('confidence', None)
        document.page_count = ocr_result.get('page_count', 0)
        document.save(update_fields=['ocr_text', 'ocr_confidence', 'page_count'])

        logger.info(f"OCR complete for document {document_id}. Extracted {len(ocr_result['text'])} characters")

        # Step 2: AI Analysis
        document.mark_analyzing()
        logger.info(f"Starting AI analysis for document {document_id}")

        ai_service = AIService()
        ai_result = ai_service.analyze_document(
            text=document.ocr_text,
            document_type=document.document_type
        )

        document.ai_summary = ai_result['analysis']
        document.ai_model_used = ai_result['model']
        document.ai_tokens_used = ai_result['tokens_used']

        # Calculate processing duration
        duration = time.time() - start_time
        document.mark_completed(duration=duration)

        logger.info(f"Document {document_id} processed successfully in {duration:.2f} seconds")

        # Send email notification (async)
        try:
            from core.tasks import send_document_analysis_complete_email
            send_document_analysis_complete_email.delay(document_id)
        except Exception as e:
            logger.warning(f"Failed to queue email notification for document {document_id}: {e}")

        return {
            'document_id': document_id,
            'status': 'completed',
            'duration': duration,
            'ocr_length': len(document.ocr_text),
            'tokens_used': document.ai_tokens_used,
        }

    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        raise

    except Exception as exc:
        logger.error(f"Error processing document {document_id}: {str(exc)}", exc_info=True)

        # Try to update document status
        try:
            document = Document.objects.get(id=document_id)
            error_message = f"Processing failed: {str(exc)}"
            document.mark_failed(error_message)
        except Exception as e:
            logger.error(f"Failed to update document status: {str(e)}")

        # Record failure for health monitoring
        try:
            import traceback
            from core.models import ProcessingFailure
            ProcessingFailure.record_failure(
                failure_type='ocr' if 'ocr' in str(exc).lower() else 'document_processing',
                error_message=str(exc),
                stack_trace=traceback.format_exc(),
                document_id=str(document_id),
                task_id=self.request.id
            )
        except Exception as e:
            logger.error(f"Failed to record processing failure: {str(e)}")

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def decode_denial_letter_task(self, document_id, user_id=None):
    """
    Complete denial decoding pipeline:
    1. OCR extraction (if not already done)
    2. Decision letter analysis (extract denied conditions)
    3. M21 matching (find relevant manual sections)
    4. Evidence guidance generation

    Creates DecisionLetterAnalysis and DenialDecoding records.
    """
    from agents.models import AgentInteraction, DecisionLetterAnalysis, DenialDecoding
    from agents.services import DecisionLetterAnalyzer, DenialDecoderService

    start_time = time.time()

    try:
        # Get document
        document = Document.objects.get(id=document_id)
        user = document.user

        # Step 1: OCR if not already done
        if not document.ocr_text:
            document.mark_processing()
            logger.info(f"Starting OCR for denial letter {document_id}")

            ocr_service = OCRService()
            ocr_result = ocr_service.extract_text(document.file.path)

            document.ocr_text = ocr_result['text']
            document.ocr_confidence = ocr_result.get('confidence', None)
            document.page_count = ocr_result.get('page_count', 0)
            document.save(update_fields=['ocr_text', 'ocr_confidence', 'page_count'])

            logger.info(f"OCR complete: {len(ocr_result['text'])} characters")

        # Step 2: Decision Letter Analysis
        document.mark_analyzing()
        logger.info(f"Analyzing decision letter {document_id}")

        analyzer = DecisionLetterAnalyzer()
        analysis_result = analyzer.analyze(document.ocr_text)

        # Create interaction record
        interaction = AgentInteraction.objects.create(
            user=user,
            agent_type='decision_analyzer',
            status='completed',
            tokens_used=analysis_result.get('_tokens_used', 0),
            cost_estimate=analysis_result.get('_cost_estimate', 0)
        )

        # Create analysis record
        analysis = DecisionLetterAnalysis.objects.create(
            interaction=interaction,
            user=user,
            document=document,
            raw_text=document.ocr_text,
            decision_date=_parse_date(analysis_result.get('decision_date')),
            conditions_granted=analysis_result.get('conditions_granted', []),
            conditions_denied=analysis_result.get('conditions_denied', []),
            conditions_deferred=analysis_result.get('conditions_deferred', []),
            summary=analysis_result.get('summary', ''),
            appeal_options=analysis_result.get('appeal_options', []),
            evidence_issues=analysis_result.get('evidence_issues', []),
            action_items=analysis_result.get('action_items', []),
            appeal_deadline=_parse_date(analysis_result.get('appeal_deadline'))
        )

        logger.info(f"Analysis complete: {len(analysis_result.get('conditions_denied', []))} denied conditions")

        # Step 3: Denial Decoding (M21 matching + evidence guidance)
        denied_conditions = analysis_result.get('conditions_denied', [])

        if denied_conditions:
            logger.info(f"Decoding {len(denied_conditions)} denials with M21 matching")

            decoder = DenialDecoderService()
            denial_mappings, evidence_strategy, m21_sections_searched = decoder.decode_all_denials(
                denied_conditions
            )

            # Create priority order based on critical evidence count
            priority_order = sorted(
                range(len(denial_mappings)),
                key=lambda i: sum(
                    1 for e in denial_mappings[i].get('required_evidence', [])
                    if e.get('priority') == 'critical'
                ),
                reverse=True
            )

            # Create decoding record
            decoding = DenialDecoding.objects.create(
                analysis=analysis,
                denial_mappings=denial_mappings,
                evidence_strategy=evidence_strategy,
                priority_order=priority_order,
                m21_sections_searched=m21_sections_searched,
                processing_time_seconds=time.time() - start_time
            )

            logger.info(f"Denial decoding complete: {m21_sections_searched} M21 sections searched")
        else:
            logger.info("No denied conditions to decode")
            decoding = None

        # Mark document complete
        duration = time.time() - start_time
        document.mark_completed(duration=duration)

        # Send email notification (async)
        try:
            from core.tasks import send_document_analysis_complete_email
            send_document_analysis_complete_email.delay(document_id)
        except Exception as e:
            logger.warning(f"Failed to queue email notification for document {document_id}: {e}")

        return {
            'document_id': document_id,
            'analysis_id': analysis.id,
            'decoding_id': decoding.id if decoding else None,
            'denied_count': len(denied_conditions),
            'status': 'completed',
            'duration': duration,
        }

    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        raise

    except Exception as exc:
        logger.error(f"Error decoding denial letter {document_id}: {str(exc)}", exc_info=True)

        try:
            document = Document.objects.get(id=document_id)
            document.mark_failed(f"Decoding failed: {str(exc)}")
        except Exception as e:
            logger.error(f"Failed to update document status: {str(e)}")

        # Record failure for health monitoring
        try:
            import traceback
            from core.models import ProcessingFailure
            ProcessingFailure.record_failure(
                failure_type='ai_analysis',
                error_message=str(exc),
                stack_trace=traceback.format_exc(),
                document_id=str(document_id),
                task_id=self.request.id
            )
        except Exception as e:
            logger.error(f"Failed to record processing failure: {str(e)}")

        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


def _parse_date(date_str):
    """Parse date string to date object."""
    if not date_str:
        return None
    try:
        from datetime import datetime
        if isinstance(date_str, str):
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        return date_str
    except (ValueError, TypeError):
        return None


@shared_task
def cleanup_old_documents():
    """
    Periodic task to clean up old soft-deleted documents
    Can be scheduled via Celery Beat
    """
    from datetime import timedelta

    threshold_date = timezone.now() - timedelta(days=90)

    # Use all_objects to find soft-deleted documents (objects manager excludes them)
    deleted_docs = Document.all_objects.filter(
        is_deleted=True,
        deleted_at__lt=threshold_date
    )

    count = deleted_docs.count()

    # Permanently delete each document (hard_delete is an instance method)
    for doc in deleted_docs:
        try:
            # Delete the file from storage if it exists
            if doc.file:
                doc.file.delete(save=False)
            doc.hard_delete()
        except Exception as e:
            logger.error(f"Failed to hard delete document {doc.id}: {e}")

    logger.info(f"Cleaned up {count} old documents")
    return f"Cleaned up {count} documents"
