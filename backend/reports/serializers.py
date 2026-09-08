from rest_framework import serializers

from .models import Report


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
    class Meta:
        model = Report
        fields = ['id', 'original_filename', 'source_type', 'status', 'report_date', 'created_at']
        read_only_fields = fields
