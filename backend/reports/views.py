import os

from django.conf import settings
from django.http import FileResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from services.extraction.excel_extractor import ExcelExtractionError
from services.extraction.pdf_extractor import PdfExtractionError
from services.normalization.validate_data import ReportValidationError
from services.pipeline import UnsupportedFileType, detect_source_type, export_report_excel, process_report_file

from .models import Report
from .serializers import ReportSerializer

KNOWN_EXTRACTION_ERRORS = (PdfExtractionError, ExcelExtractionError, ReportValidationError, UnsupportedFileType)


class ReportUploadView(APIView):
    def post(self, request):
        upload = request.FILES.get('file')
        if not upload:
            return Response({'detail': 'No file was uploaded. Attach a file under the "file" field.'},
                             status=status.HTTP_400_BAD_REQUEST)

        if upload.size > settings.MAX_UPLOAD_SIZE:
            max_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
            return Response({'detail': f'File is too large. The maximum accepted size is {max_mb}MB.'},
                             status=status.HTTP_400_BAD_REQUEST)

        try:
            source_type = detect_source_type(upload.name)
        except UnsupportedFileType as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        report = Report.objects.create(
            original_filename=upload.name,
            source_file=upload,
            source_type=source_type,
            status=Report.Status.PROCESSING,
        )

        try:
            result = process_report_file(report.source_file.path, upload.name)
        except KNOWN_EXTRACTION_ERRORS as exc:
            report.status = Report.Status.FAILED
            report.error_message = str(exc)
            report.processed_at = timezone.now()
            report.save(update_fields=['status', 'error_message', 'processed_at'])
            return Response(ReportSerializer(report, context={'request': request}).data,
                             status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as exc:  # noqa: BLE001 - guard against unexpected extractor bugs
            report.status = Report.Status.FAILED
            report.error_message = f'Unexpected error while processing the document: {exc}'
            report.processed_at = timezone.now()
            report.save(update_fields=['status', 'error_message', 'processed_at'])
            return Response(ReportSerializer(report, context={'request': request}).data,
                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        report.status = Report.Status.COMPLETED
        report.extracted_data = result['data']
        report.warnings = result['warnings']
        report.report_date = result['data'].get('report_date') or None
        report.processed_at = timezone.now()
        report.save(update_fields=['status', 'extracted_data', 'warnings', 'report_date', 'processed_at'])

        return Response(ReportSerializer(report, context={'request': request}).data,
                         status=status.HTTP_201_CREATED)


class ReportDetailView(APIView):
    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ReportSerializer(report, context={'request': request}).data)


class ReportDownloadView(APIView):
    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)

        if report.status != Report.Status.COMPLETED or not report.extracted_data:
            return Response({'detail': 'This report has not completed processing yet.'},
                             status=status.HTTP_409_CONFLICT)

        if not report.generated_excel or not os.path.exists(report.generated_excel.path):
            filename = f'{report.id}.xlsx'
            output_path = os.path.join(settings.GENERATED_DIR, filename)
            export_report_excel(report.extracted_data, output_path)
            report.generated_excel.name = f'generated/{filename}'
            report.save(update_fields=['generated_excel'])

        date_part = report.report_date.isoformat() if report.report_date else 'report'
        download_name = f'RSE_Report_{date_part}.xlsx'
        return FileResponse(
            open(report.generated_excel.path, 'rb'),
            as_attachment=True,
            filename=download_name,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
