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

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def cleanup_old_documents():
    """
    Periodic task to clean up old soft-deleted documents
    Can be scheduled via Celery Beat
    """
    from datetime import timedelta

    threshold_date = timezone.now() - timedelta(days=90)

    deleted_docs = Document.objects.filter(
        is_deleted=True,
        deleted_at__lt=threshold_date
    )

    count = deleted_docs.count()
    deleted_docs.hard_delete()  # Permanently delete

    logger.info(f"Cleaned up {count} old documents")
    return f"Cleaned up {count} documents"
