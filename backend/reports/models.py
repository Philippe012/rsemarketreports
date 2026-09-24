import uuid

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


def upload_path(instance, filename):
    return f"uploads/{instance.id}_{filename}"


def generated_path(instance, filename):
    return f"generated/{instance.id}_{filename}"


class Report(models.Model):

    class SourceType(models.TextChoices):
        PDF = 'pdf', 'PDF'
        EXCEL = 'excel', 'Excel'
        CSV = 'csv', 'CSV'
        DOCX = 'docx', 'Word'
        TXT = 'txt', 'Text'
        JSON = 'json', 'JSON'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.CASCADE, related_name='reports',
    )
    original_filename = models.CharField(max_length=255)
    source_file = models.FileField(upload_to=upload_path)
    source_type = models.CharField(max_length=10, choices=SourceType.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    # SHA-256 of the uploaded bytes, computed once at upload time — lets a
    # re-upload of a file this user has already processed be recognized and
    # short-circuited (see ReportUploadView) instead of reprocessed from
    # scratch, without needing a job queue to make that idempotent.
    file_hash = models.CharField(max_length=64, blank=True, default='', db_index=True)

    report_date = models.DateField(null=True, blank=True)

    extracted_data = models.JSONField(null=True, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True, default='')

    generated_excel = models.FileField(upload_to=generated_path, null=True, blank=True)

    
    headline_metric_label = models.CharField(max_length=120, blank=True, default='')
    headline_metric_value = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    # RAG indexing state (see services.rag.indexing). Kept separate from
    # `status` so a failed index never marks the report itself as failed.
    class IndexStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        INDEXED = 'indexed', 'Indexed'
        FAILED = 'failed', 'Failed'

    index_status = models.CharField(max_length=20, choices=IndexStatus.choices, default=IndexStatus.PENDING)
    index_error = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} ({self.status})"


@receiver(post_delete, sender=Report)
def _delete_report_files(sender, instance, **kwargs):
    """Deleting a Report row (individually or via a bulk queryset delete —
    post_delete fires for both) previously left its uploaded source file
    and generated workbook orphaned on disk forever, since only the
    database row was ever removed. Both are cleaned up here instead;
    Django's default storage silently no-ops if a file is already gone."""
    for field_file in (instance.source_file, instance.generated_excel):
        if field_file:
            field_file.storage.delete(field_file.name)


class AlertRule(models.Model):
    """A user-defined Intelligent Alert threshold on one report. Only the
    rule itself is persisted — whether it's currently triggered is always
    recomputed live from the report's current extracted_data (see
    services.intelligence.alerts), so a stored alert can never go stale.
    """

    class Operator(models.TextChoices):
        GREATER_THAN = 'gt', 'Greater than'
        GREATER_OR_EQUAL = 'gte', 'Greater than or equal to'
        LESS_THAN = 'lt', 'Less than'
        LESS_OR_EQUAL = 'lte', 'Less than or equal to'

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='alert_rules')
    metric_label = models.CharField(max_length=200)
    dataset = models.CharField(max_length=200)
    column = models.CharField(max_length=200)
    operator = models.CharField(max_length=4, choices=Operator.choices)
    threshold = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.metric_label} {self.operator} {self.threshold}'


class ChatMessage(models.Model):

    class Role(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    confidence = models.CharField(max_length=10, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:40]}'


class DocumentChunk(models.Model):
    """One searchable passage of a report for RAG retrieval (see
    services.rag). The embedding is stored as a JSON list of floats rather
    than a pgvector column so the app keeps working on a Postgres without
    the `vector` extension; ``embedding_model`` records which embedder
    produced it so vectors from different models are never compared."""

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    section = models.CharField(max_length=255, blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    embedding = models.JSONField(default=list, blank=True)
    embedding_model = models.CharField(max_length=100, blank=True, default='', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['report']),
        ]

    def __str__(self):
        return f'{self.report_id} · {self.section or "chunk"}'