"""
Forms for claims app with accessibility and validation
"""

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Document


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
        Checks file size, type, and user limits
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

        # Check file type
        allowed_types = settings.ALLOWED_DOCUMENT_TYPES
        if file.content_type not in allowed_types:
            raise ValidationError(
                _('File type not supported. Please upload PDF, JPG, PNG, or TIFF files only.')
            )

        # Check file extension (additional security)
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff']
        ext = file.name.lower().split('.')[-1]
        if f'.{ext}' not in allowed_extensions:
            raise ValidationError(
                _('Invalid file extension. Allowed extensions: PDF, JPG, JPEG, PNG, TIFF.')
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
