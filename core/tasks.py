"""
Celery tasks for core app - data retention enforcement and maintenance.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def enforce_data_retention():
    """
    Periodic task to enforce data retention policies.

    Checks DataRetentionPolicy records and purges expired data accordingly.
    Should be scheduled via Celery Beat (e.g., daily at 2 AM).
    """
    from .models import DataRetentionPolicy, AuditLog

    policies = DataRetentionPolicy.objects.filter(is_active=True, retention_days__gt=0)
    results = {}

    for policy in policies:
        try:
            cutoff_date = timezone.now() - timedelta(days=policy.retention_days)
            deleted_count = 0

            if policy.data_type == 'audit_logs':
                deleted_count = _purge_audit_logs(cutoff_date)
            elif policy.data_type == 'documents':
                deleted_count = _purge_old_documents(cutoff_date)
            elif policy.data_type == 'analyses':
                deleted_count = _purge_old_analyses(cutoff_date)
            elif policy.data_type == 'session_data':
                deleted_count = _purge_session_data(cutoff_date)

            # Update last cleanup timestamp
            policy.last_cleanup = timezone.now()
            policy.save(update_fields=['last_cleanup'])

            results[policy.data_type] = deleted_count
            logger.info(
                f"Data retention: purged {deleted_count} {policy.data_type} "
                f"older than {policy.retention_days} days"
            )

        except Exception as e:
            logger.error(f"Data retention failed for {policy.data_type}: {e}")
            results[policy.data_type] = f"Error: {e}"

    return results


def _purge_audit_logs(cutoff_date):
    """Purge audit logs older than cutoff date."""
    from .models import AuditLog

    old_logs = AuditLog.objects.filter(timestamp__lt=cutoff_date)
    count = old_logs.count()
    old_logs.delete()
    return count


def _purge_old_documents(cutoff_date):
    """
    Purge soft-deleted documents older than cutoff date.
    Note: This only handles documents that are already soft-deleted.
    """
    from claims.models import Document

    # Only purge documents that were soft-deleted before the cutoff
    old_docs = Document.objects.filter(
        is_deleted=True,
        deleted_at__lt=cutoff_date
    )
    count = old_docs.count()

    for doc in old_docs:
        try:
            # Delete file from storage
            if doc.file:
                doc.file.delete(save=False)
            doc.hard_delete()
        except Exception as e:
            logger.error(f"Failed to purge document {doc.id}: {e}")

    return count


def _purge_old_analyses(cutoff_date):
    """Purge old AI analysis records."""
    try:
        from agents.models import AgentInteraction, DecisionLetterAnalysis, DenialDecoding

        # Delete old denial decodings first (depends on analysis)
        old_decodings = DenialDecoding.objects.filter(
            analysis__created_at__lt=cutoff_date
        )
        decoding_count = old_decodings.count()
        old_decodings.delete()

        # Delete old analyses
        old_analyses = DecisionLetterAnalysis.objects.filter(
            created_at__lt=cutoff_date
        )
        analysis_count = old_analyses.count()
        old_analyses.delete()

        # Delete old agent interactions
        old_interactions = AgentInteraction.objects.filter(
            created_at__lt=cutoff_date
        )
        interaction_count = old_interactions.count()
        old_interactions.delete()

        return decoding_count + analysis_count + interaction_count

    except ImportError:
        logger.warning("agents app not available for analysis purge")
        return 0


def _purge_session_data(cutoff_date):
    """Purge expired session data."""
    from django.contrib.sessions.models import Session

    # Django sessions have an expire_date field
    old_sessions = Session.objects.filter(expire_date__lt=cutoff_date)
    count = old_sessions.count()
    old_sessions.delete()
    return count


@shared_task
def create_default_retention_policies():
    """
    Create default data retention policies if they don't exist.
    Run this once during initial setup.
    """
    from .models import DataRetentionPolicy

    defaults = [
        {
            'data_type': 'audit_logs',
            'retention_days': 365,  # 1 year
            'description': 'Security audit logs retained for compliance',
        },
        {
            'data_type': 'documents',
            'retention_days': 90,  # 90 days after soft delete
            'description': 'Soft-deleted documents purged after 90 days',
        },
        {
            'data_type': 'analyses',
            'retention_days': 180,  # 6 months
            'description': 'AI analysis results retained for 6 months',
        },
        {
            'data_type': 'session_data',
            'retention_days': 30,  # 30 days
            'description': 'Expired sessions cleaned up after 30 days',
        },
    ]

    created = 0
    for policy_data in defaults:
        policy, was_created = DataRetentionPolicy.objects.get_or_create(
            data_type=policy_data['data_type'],
            defaults={
                'retention_days': policy_data['retention_days'],
                'description': policy_data['description'],
                'is_active': True,
            }
        )
        if was_created:
            created += 1
            logger.info(f"Created retention policy: {policy_data['data_type']}")

    return f"Created {created} new retention policies"
