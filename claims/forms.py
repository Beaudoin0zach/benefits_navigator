"""
Forms for claims app with accessibility and validation
"""

import logging

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Document

logger = logging.getLogger(__name__)

# Check if python-magic is available at module load time
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning(
        "python-magic is not installed. File content validation will be limited. "
        "Install with: pip install python-magic"
    )


class DocumentUploadForm(forms.ModelForm):
    """
    Accessible document upload form with comprehensive validation
    """

    class Meta:
        model = Document
        fields = ['file', 'document_type']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none',
                'accept': '.pdf,.jpg,.jpeg,.png,.tiff',
                'aria-describedby': 'file-help',
            }),
            'document_type': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                'aria-describedby': 'document-type-help',
            }),
        }
        labels = {
            'file': _('Select Document'),
            'document_type': _('Document Type'),
        }
        help_texts = {
            'file': _('Accepted formats: PDF, JPG, PNG, TIFF. Maximum size: 50 MB.'),
            'document_type': _('Select the type of document you are uploading.'),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Add required asterisks for screen readers
        for field_name, field in self.fields.items():
            if field.required:
                field.label = f"{field.label} (required)"

    def clean_file(self):
        """
        Validate uploaded file
        Checks file size, type, magic bytes, and user limits
        """
        file = self.cleaned_data.get('file')

        if not file:
            raise ValidationError(_('Please select a file to upload.'))

        # Check file size
        if file.size > settings.MAX_DOCUMENT_SIZE:
            max_size_mb = settings.MAX_DOCUMENT_SIZE / (1024 * 1024)
            raise ValidationError(
                _(f'File size exceeds maximum allowed size of {max_size_mb} MB. '
                  f'Your file is {round(file.size / (1024 * 1024), 2)} MB.')
            )

        # Check file extension (first layer of defense)
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif']
        ext = file.name.lower().split('.')[-1]
        if f'.{ext}' not in allowed_extensions:
            raise ValidationError(
                _('Invalid file extension. Allowed extensions: PDF, JPG, JPEG, PNG, TIFF.')
            )

        # Check file type via content_type header
        allowed_types = settings.ALLOWED_DOCUMENT_TYPES
        if file.content_type not in allowed_types:
            raise ValidationError(
                _('File type not supported. Please upload PDF, JPG, PNG, or TIFF files only.')
            )

        # SECURITY: Validate actual file content using magic bytes
        # This prevents malicious files disguised with fake extensions
        if MAGIC_AVAILABLE:
            file.seek(0)
            file_magic = magic.from_buffer(file.read(2048), mime=True)
            file.seek(0)  # Reset file pointer

            if file_magic not in allowed_types:
                raise ValidationError(
                    _('File content does not match expected type. '
                      'Please ensure you are uploading a valid PDF or image file.')
                )
        else:
            logger.info(f"Skipping magic byte validation for {file.name} (python-magic not available)")

        # Check page count for PDFs to prevent extremely large documents
        if ext == 'pdf':
            page_count = self._get_pdf_page_count(file)
            max_pages = getattr(settings, 'MAX_DOCUMENT_PAGES', 100)
            if page_count and page_count > max_pages:
                raise ValidationError(
                    _(f'PDF has too many pages ({page_count}). Maximum allowed is {max_pages} pages.')
                )

        # Check user's monthly limit (if not premium)
        if self.user and not self.user.is_premium:
            from datetime import datetime
            current_month_docs = Document.objects.filter(
                user=self.user,
                created_at__year=datetime.now().year,
                created_at__month=datetime.now().month,
                is_deleted=False
            ).count()

            if current_month_docs >= settings.FREE_TIER_DOCUMENTS_PER_MONTH:
                raise ValidationError(
                    _(f'You have reached your free tier limit of '
                      f'{settings.FREE_TIER_DOCUMENTS_PER_MONTH} documents per month. '
                      f'Please upgrade to Premium for unlimited uploads.')
                )

        return file

    def clean(self):
        """
        Additional form-level validation
        """
        cleaned_data = super().clean()

        # Could add cross-field validation here if needed
        # For example, certain document types might have additional requirements

        return cleaned_data

    def _get_pdf_page_count(self, file):
        """
        Get page count from a PDF file.

        Returns:
            int or None: Page count, or None if unable to determine.
        """
        try:
            import PyPDF2
            file.seek(0)
            reader = PyPDF2.PdfReader(file)
            page_count = len(reader.pages)
            file.seek(0)
            return page_count
        except ImportError:
            logger.debug("PyPDF2 not available for page count validation")
            return None
        except Exception as e:
            logger.warning(f"Could not determine PDF page count: {e}")
            return None


class DenialLetterUploadForm(forms.ModelForm):
    """
    Simplified upload form specifically for VA denial letters.
    Pre-configured for decision_letter document type.
    """

    class Meta:
        model = Document
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none',
                'accept': '.pdf,.jpg,.jpeg,.png,.tiff',
                'aria-describedby': 'file-help',
            }),
        }
        labels = {
            'file': _('Upload VA Denial Letter'),
        }
        help_texts = {
            'file': _('Upload your VA Rating Decision letter (PDF or image). Maximum size: 50 MB.'),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Add required indicator
        self.fields['file'].label = f"{self.fields['file'].label} (required)"

    def clean_file(self):
        """
        Validate uploaded denial letter.
        """
        file = self.cleaned_data.get('file')

        if not file:
            raise ValidationError(_('Please select a denial letter to upload.'))

        # Check file size
        if file.size > settings.MAX_DOCUMENT_SIZE:
            max_size_mb = settings.MAX_DOCUMENT_SIZE / (1024 * 1024)
            raise ValidationError(
                _(f'File size exceeds maximum allowed size of {max_size_mb} MB.')
            )

        # Check file extension
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif']
        ext = file.name.lower().split('.')[-1]
        if f'.{ext}' not in allowed_extensions:
            raise ValidationError(
                _('Invalid file extension. Allowed extensions: PDF, JPG, JPEG, PNG, TIFF.')
            )

        # Check file type via content_type
        allowed_types = settings.ALLOWED_DOCUMENT_TYPES
        if file.content_type not in allowed_types:
            raise ValidationError(
                _('File type not supported. Please upload PDF or image files only.')
            )

        # SECURITY: Validate via magic bytes
        if MAGIC_AVAILABLE:
            file.seek(0)
            file_magic = magic.from_buffer(file.read(2048), mime=True)
            file.seek(0)

            if file_magic not in allowed_types:
                raise ValidationError(
                    _('File content does not match expected type.')
                )
        else:
            logger.info(f"Skipping magic byte validation for {file.name} (python-magic not available)")

        # Check page count for PDFs
        if ext == 'pdf':
            page_count = self._get_pdf_page_count(file)
            max_pages = getattr(settings, 'MAX_DOCUMENT_PAGES', 100)
            if page_count and page_count > max_pages:
                raise ValidationError(
                    _(f'PDF has too many pages ({page_count}). Maximum allowed is {max_pages} pages.')
                )

        # Check user's monthly limit
        if self.user and not self.user.is_premium:
            from datetime import datetime
            current_month_docs = Document.objects.filter(
                user=self.user,
                created_at__year=datetime.now().year,
                created_at__month=datetime.now().month,
                is_deleted=False
            ).count()

            if current_month_docs >= settings.FREE_TIER_DOCUMENTS_PER_MONTH:
                raise ValidationError(
                    _(f'You have reached your free tier limit of '
                      f'{settings.FREE_TIER_DOCUMENTS_PER_MONTH} documents per month.')
                )

        return file

    def _get_pdf_page_count(self, file):
        """
        Get page count from a PDF file.

        Returns:
            int or None: Page count, or None if unable to determine.
        """
        try:
            import PyPDF2
            file.seek(0)
            reader = PyPDF2.PdfReader(file)
            page_count = len(reader.pages)
            file.seek(0)
            return page_count
        except ImportError:
            logger.debug("PyPDF2 not available for page count validation")
            return None
        except Exception as e:
            logger.warning(f"Could not determine PDF page count: {e}")
            return None
