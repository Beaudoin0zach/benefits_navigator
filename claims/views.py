"""
Views for claims app - Document upload and management
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings

from .models import Document
from .forms import DocumentUploadForm, DenialLetterUploadForm
from .tasks import process_document_task, decode_denial_letter_task


@login_required
def document_list(request):
    """
    Display list of user's uploaded documents
    Accessible table with sortable columns
    """
    documents = Document.objects.filter(
        user=request.user,
        is_deleted=False
    ).order_by('-created_at')

    context = {
        'documents': documents,
        'documents_this_month': documents.filter(
            created_at__month=request.user.date_joined.month
        ).count() if hasattr(request.user, 'date_joined') else 0,
        'free_tier_limit': settings.FREE_TIER_DOCUMENTS_PER_MONTH,
        'is_premium': request.user.is_premium if hasattr(request.user, 'is_premium') else False,
    }

    return render(request, 'claims/document_list.html', context)


@login_required
def document_upload(request):
    """
    Handle document upload with accessible form
    Includes inline validation and clear error messages
    """
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            # Create document instance
            document = form.save(commit=False)
            document.user = request.user

            # Set file metadata
            uploaded_file = request.FILES['file']
            document.file_name = uploaded_file.name
            document.file_size = uploaded_file.size
            document.mime_type = uploaded_file.content_type

            document.save()

            # Trigger async processing
            process_document_task.delay(document.id)

            # Success message for screen readers
            messages.success(
                request,
                f'Document "{document.file_name}" uploaded successfully. '
                'Processing has started and you will be notified when complete.'
            )

            return redirect('claims:document_detail', pk=document.id)
        else:
            # Form has errors - they will be displayed in template
            # Add a general error message for screen readers
            messages.error(
                request,
                'There were errors in your upload. Please review the form below.'
            )
    else:
        form = DocumentUploadForm(user=request.user)

    context = {
        'form': form,
    }

    return render(request, 'claims/document_upload.html', context)


@login_required
def document_detail(request, pk):
    """
    Display document details and analysis results
    Accessible layout with clear headings and sections
    """
    document = get_object_or_404(
        Document,
        pk=pk,
        user=request.user,
        is_deleted=False
    )

    context = {
        'document': document,
    }

    return render(request, 'claims/document_detail.html', context)


@login_required
@require_http_methods(["GET"])
def document_status(request, pk):
    """
    HTMX endpoint to check document processing status
    Returns JSON for ARIA live region updates
    """
    document = get_object_or_404(
        Document,
        pk=pk,
        user=request.user,
        is_deleted=False
    )

    # Return HTML fragment for HTMX
    if request.headers.get('HX-Request'):
        return render(request, 'claims/partials/document_status.html', {
            'document': document
        })

    # Fallback JSON response
    return JsonResponse({
        'status': document.status,
        'is_processing': document.is_processing,
        'is_complete': document.is_complete,
        'has_failed': document.has_failed,
        'error_message': document.error_message if document.has_failed else None,
    })


@login_required
@require_http_methods(["POST"])
def document_delete(request, pk):
    """
    Soft delete document
    Includes confirmation and accessible feedback
    """
    document = get_object_or_404(
        Document,
        pk=pk,
        user=request.user,
        is_deleted=False
    )

    document_name = document.file_name
    document.delete()  # Soft delete from SoftDeleteModel

    messages.success(
        request,
        f'Document "{document_name}" has been deleted.'
    )

    return redirect('claims:document_list')


# =============================================================================
# Denial Decoder Views
# =============================================================================

@login_required
def denial_decoder_upload(request):
    """
    Upload VA denial letter for decoding.
    Extracts denial reasons, matches to M21 sections, and generates evidence guidance.
    """
    if request.method == 'POST':
        form = DenialLetterUploadForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            # Create document instance
            document = form.save(commit=False)
            document.user = request.user
            document.document_type = 'decision_letter'

            # Set file metadata
            uploaded_file = request.FILES['file']
            document.file_name = uploaded_file.name
            document.file_size = uploaded_file.size
            document.mime_type = uploaded_file.content_type

            document.save()

            # Trigger denial decoding task
            decode_denial_letter_task.delay(document.id)

            messages.success(
                request,
                f'Denial letter "{document.file_name}" uploaded successfully. '
                'Analysis in progress - this may take 1-2 minutes.'
            )

            return redirect('claims:denial_decoder_result', pk=document.id)
        else:
            messages.error(
                request,
                'There were errors in your upload. Please review the form below.'
            )
    else:
        form = DenialLetterUploadForm(user=request.user)

    context = {
        'form': form,
    }

    return render(request, 'claims/denial_decoder_upload.html', context)


@login_required
def denial_decoder_result(request, pk):
    """
    Display denial decoding results.
    Shows extracted denials, M21 matches, and evidence guidance.
    """
    document = get_object_or_404(
        Document,
        pk=pk,
        user=request.user,
        is_deleted=False
    )

    # Get associated analysis and decoding
    analysis = None
    decoding = None

    # Check if document has been analyzed
    if hasattr(document, 'decision_analyses'):
        analysis = document.decision_analyses.first()
        if analysis and hasattr(analysis, 'denial_decoding'):
            decoding = analysis.denial_decoding

    context = {
        'document': document,
        'analysis': analysis,
        'decoding': decoding,
    }

    return render(request, 'claims/denial_decoder_result.html', context)


@login_required
@require_http_methods(["GET"])
def denial_decoder_status(request, pk):
    """
    HTMX endpoint to check denial decoding status.
    Returns status fragment for polling during processing.
    """
    document = get_object_or_404(
        Document,
        pk=pk,
        user=request.user,
        is_deleted=False
    )

    # Check for analysis
    analysis = None
    decoding = None
    if hasattr(document, 'decision_analyses'):
        analysis = document.decision_analyses.first()
        if analysis and hasattr(analysis, 'denial_decoding'):
            decoding = analysis.denial_decoding

    context = {
        'document': document,
        'analysis': analysis,
        'decoding': decoding,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'claims/partials/denial_decoder_status.html', context)

    return JsonResponse({
        'status': document.status,
        'is_processing': document.is_processing,
        'is_complete': document.is_complete,
        'has_analysis': analysis is not None,
        'has_decoding': decoding is not None,
    })
