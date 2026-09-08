import uuid

from django.db import models


def upload_path(instance, filename):
    return f"uploads/{instance.id}_{filename}"


def generated_path(instance, filename):
    return f"generated/{instance.id}_{filename}"


class Report(models.Model):

    class SourceType(models.TextChoices):
        PDF = 'pdf', 'PDF'
        EXCEL = 'excel', 'Excel'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_filename = models.CharField(max_length=255)
    source_file = models.FileField(upload_to=upload_path)
    source_type = models.CharField(max_length=10, choices=SourceType.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    report_date = models.DateField(null=True, blank=True)

    extracted_data = models.JSONField(null=True, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True, default='')

    generated_excel = models.FileField(upload_to=generated_path, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} ({self.status})"
