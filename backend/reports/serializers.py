from rest_framework import serializers

from .list_filters import document_type_of
from .models import AlertRule, ChatMessage, Report


class ReportSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 'original_filename', 'source_type', 'status',
            'report_date', 'extracted_data', 'warnings', 'error_message',
            'download_url', 'created_at', 'processed_at',
        ]
        read_only_fields = fields

    def get_download_url(self, obj: Report):
        if obj.status != Report.Status.COMPLETED:
            return None
        
        request = self.context.get('request')
        path = f'/api/reports/{obj.id}/download/'
        return request.build_absolute_uri(path) if request else path


class ReportListSerializer(serializers.ModelSerializer):
    document_type = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 'original_filename', 'source_type', 'status', 'report_date', 'created_at',
            'document_type', 'headline_metric_label', 'headline_metric_value',
        ]
        read_only_fields = fields

    def get_document_type(self, obj: Report) -> str:
        return document_type_of(obj)


class ReportAdminListSerializer(ReportListSerializer):
    owner_email = serializers.SerializerMethodField()

    class Meta(ReportListSerializer.Meta):
        fields = ReportListSerializer.Meta.fields + ['owner_email']

    def get_owner_email(self, obj: Report):
        return obj.user.email if obj.user_id else None


class ReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['original_filename']

    def validate_original_filename(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Filename cannot be empty.')
        return value


class AlertRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRule
        fields = ['id', 'metric_label', 'dataset', 'column', 'operator', 'threshold', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_metric_label(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Give this alert a label.')
        return value

    def validate_dataset(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('A dataset is required.')
        return value

    def validate_column(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('A column is required.')
        return value


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'sources', 'confidence', 'created_at']
        read_only_fields = fields
