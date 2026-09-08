from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_filename', 'source_type', 'status', 'report_date', 'created_at')
    list_filter = ('source_type', 'status')
    search_fields = ('original_filename',)
    readonly_fields = ('id', 'created_at', 'processed_at', 'extracted_data', 'warnings')
