"""
VSO Signals - Activity tracking and automatic condition derivation.

This module provides signals for:
- Updating last_activity_at on cases when related objects change
- Automatically deriving conditions when analyses are shared
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import CaseNote, CaseCondition, SharedDocument, SharedAnalysis, VeteranCase
from .services import ConditionDerivationService

logger = logging.getLogger(__name__)


def update_case_activity(case_id: int) -> None:
    """
    Update the last_activity_at field for a case.

    Uses update() instead of save() to avoid recursion and improve performance.
    """
    VeteranCase.objects.filter(pk=case_id).update(last_activity_at=timezone.now())


@receiver(post_save, sender=CaseNote)
def update_case_activity_on_note(sender, instance, created, **kwargs):
    """Update case activity when a note is added or updated."""
    if hasattr(instance, 'case') and instance.case_id:
        update_case_activity(instance.case_id)


@receiver(post_save, sender=SharedDocument)
def update_case_activity_on_document(sender, instance, created, **kwargs):
    """Update case activity when a document is shared."""
    if hasattr(instance, 'case') and instance.case_id:
        update_case_activity(instance.case_id)


@receiver(post_save, sender=SharedAnalysis)
def update_case_activity_on_analysis(sender, instance, created, **kwargs):
    """Update case activity when an analysis is shared."""
    if hasattr(instance, 'case') and instance.case_id:
        update_case_activity(instance.case_id)


@receiver(post_save, sender=CaseCondition)
def update_case_activity_on_condition(sender, instance, created, **kwargs):
    """Update case activity when a condition is added or updated."""
    if hasattr(instance, 'case') and instance.case_id:
        update_case_activity(instance.case_id)


@receiver(post_save, sender=SharedAnalysis)
def derive_conditions_on_analysis_share(sender, instance, created, **kwargs):
    """
    Automatically derive conditions when a new analysis is shared.

    Only runs on creation to avoid duplicate processing.
    """
    if created:
        try:
            conditions = ConditionDerivationService.derive_conditions_from_analysis(instance)
            if conditions:
                logger.info(
                    f"Derived {len(conditions)} conditions from analysis {instance.pk} "
                    f"for case {instance.case_id}"
                )
        except Exception as e:
            logger.error(f"Failed to derive conditions from analysis {instance.pk}: {e}")
