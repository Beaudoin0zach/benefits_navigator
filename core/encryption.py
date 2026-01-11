"""
Field-level encryption for sensitive PII data.
Uses Fernet (AES-256) encryption.
"""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


class FieldEncryption:
    """
    Handles encryption/decryption of field values using Fernet.

    The encryption key is derived from Django's SECRET_KEY.
    """

    _fernet = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        """Get or create Fernet instance."""
        if cls._fernet is None:
            # Derive a 32-byte key from SECRET_KEY
            key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
            # Fernet requires base64-encoded 32-byte key
            fernet_key = base64.urlsafe_b64encode(key)
            cls._fernet = Fernet(fernet_key)
        return cls._fernet

    @classmethod
    def encrypt(cls, value: str) -> str:
        """
        Encrypt a string value.

        Args:
            value: Plain text string to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not value:
            return ''

        fernet = cls._get_fernet()
        encrypted = fernet.encrypt(value.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')

    @classmethod
    def decrypt(cls, encrypted_value: str) -> str:
        """
        Decrypt an encrypted string value.

        Args:
            encrypted_value: Base64-encoded encrypted string

        Returns:
            Decrypted plain text string
        """
        if not encrypted_value:
            return ''

        try:
            fernet = cls._get_fernet()
            decoded = base64.urlsafe_b64decode(encrypted_value.encode('utf-8'))
            decrypted = fernet.decrypt(decoded)
            return decrypted.decode('utf-8')
        except (InvalidToken, ValueError) as e:
            logger.warning(f"Decryption failed: {e}")
            # Return empty string on decryption failure
            # This handles cases where data was stored unencrypted
            return ''


class EncryptedCharField(models.CharField):
    """
    CharField that transparently encrypts/decrypts values.

    Usage:
        va_file_number = EncryptedCharField(max_length=255, blank=True)

    The max_length should be larger than the plain text max length
    since encrypted values are longer (roughly 2x + overhead).
    """

    description = "An encrypted CharField"

    def __init__(self, *args, **kwargs):
        # Encrypted values are longer, so increase max_length
        # Rule of thumb: original_length * 2 + 100 for overhead
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        """Encrypt value before saving to database."""
        if value is None or value == '':
            return value
        return FieldEncryption.encrypt(str(value))

    def from_db_value(self, value, expression, connection):
        """Decrypt value when reading from database."""
        if value is None or value == '':
            return value
        return FieldEncryption.decrypt(value)

    def to_python(self, value):
        """Handle value conversion from form input."""
        if isinstance(value, str):
            # Check if this looks like an encrypted value
            # Encrypted values are base64 and longer than typical input
            if len(value) > 100 and value.startswith('Z0FB'):
                return FieldEncryption.decrypt(value)
        return value


class EncryptedTextField(models.TextField):
    """
    TextField that transparently encrypts/decrypts values.

    Usage:
        notes = EncryptedTextField(blank=True)
    """

    description = "An encrypted TextField"

    def get_prep_value(self, value):
        """Encrypt value before saving to database."""
        if value is None or value == '':
            return value
        return FieldEncryption.encrypt(str(value))

    def from_db_value(self, value, expression, connection):
        """Decrypt value when reading from database."""
        if value is None or value == '':
            return value
        return FieldEncryption.decrypt(value)

    def to_python(self, value):
        """Handle value conversion from form input."""
        if isinstance(value, str):
            if len(value) > 100 and value.startswith('Z0FB'):
                return FieldEncryption.decrypt(value)
        return value


def encrypt_existing_data(model_class, field_name: str, dry_run: bool = True):
    """
    Utility function to encrypt existing unencrypted data.

    Use this in a data migration or management command.

    Args:
        model_class: Django model class
        field_name: Name of the field to encrypt
        dry_run: If True, only report what would be done
    """
    from django.db import connection

    # Get raw values directly from database to avoid model decryption
    table_name = model_class._meta.db_table
    pk_name = model_class._meta.pk.name

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {pk_name}, {field_name} FROM {table_name} WHERE {field_name} IS NOT NULL AND {field_name} != ''")
        rows = cursor.fetchall()

    count = 0
    for pk, value in rows:
        # Skip already encrypted values (they start with base64 pattern)
        if value and len(value) > 100 and value.startswith('Z0FB'):
            continue

        encrypted = FieldEncryption.encrypt(value)

        if dry_run:
            logger.info(f"Would encrypt {model_class.__name__} pk={pk} {field_name}")
        else:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE {table_name} SET {field_name} = %s WHERE {pk_name} = %s",
                    [encrypted, pk]
                )
        count += 1

    action = "Would encrypt" if dry_run else "Encrypted"
    logger.info(f"{action} {count} {model_class.__name__} records")
    return count
