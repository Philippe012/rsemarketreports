import uuid

from django.conf import settings
from django.db import models


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

    report_date = models.DateField(null=True, blank=True)

    extracted_data = models.JSONField(null=True, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True, default='')

    generated_excel = models.FileField(upload_to=generated_path, null=True, blank=True)

    
    headline_metric_label = models.CharField(max_length=120, blank=True, default='')
    headline_metric_value = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} ({self.status})"


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
