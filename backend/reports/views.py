import os

from django.conf import settings
from django.http import FileResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from services.chat import service as chat_service
from services.documents.headline import compute_headline_metric
from services.extraction.csv_extractor import CsvExtractionError
from services.extraction.docx_extractor import DocxExtractionError
from services.extraction.excel_extractor import ExcelExtractionError
from services.extraction.pdf_extractor import PdfExtractionError
from services.extraction.txt_extractor import TxtExtractionError
from services.intelligence.adapter import to_analysis_datasets
from services.intelligence.bundle import build_analysis
from services.intelligence.dashboard_builder import suggest_visualization
from services.intelligence.explain import explain_chart, explain_metric
from services.intelligence.timeline import compare_reports
from services.normalization.validate_data import ReportValidationError
from services.pipeline import UnsupportedFileType, detect_source_type, export_report_excel, process_report_file

from .list_filters import apply_filters, apply_sort, available_facets, paginate
from .models import AlertRule, ChatMessage, Report
from .serializers import (
    AlertRuleSerializer,
    ChatMessageSerializer,
    ReportAdminListSerializer,
    ReportListSerializer,
    ReportSerializer,
    ReportUpdateSerializer,
)

MAX_CHAT_MESSAGE_LENGTH = 2000

KNOWN_EXTRACTION_ERRORS = (
    PdfExtractionError, ExcelExtractionError, CsvExtractionError, DocxExtractionError,
    TxtExtractionError, ReportValidationError, UnsupportedFileType,
)


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
            user=request.user,
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
        except Exception as exc: 
            report.status = Report.Status.FAILED
            report.error_message = f'Unexpected error while processing the document: {exc}'
            report.processed_at = timezone.now()
            report.save(update_fields=['status', 'error_message', 'processed_at'])
            return Response(ReportSerializer(report, context={'request': request}).data,
                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        headline_label, headline_value = compute_headline_metric(result['data'])

        report.status = Report.Status.COMPLETED
        report.extracted_data = result['data']
        report.warnings = result['warnings']
        report.report_date = result['data'].get('report_date') or None
        report.headline_metric_label = headline_label
        report.headline_metric_value = headline_value
        report.processed_at = timezone.now()
        report.save(update_fields=[
            'status', 'extracted_data', 'warnings', 'report_date',
            'headline_metric_label', 'headline_metric_value', 'processed_at',
        ])

        return Response(ReportSerializer(report, context={'request': request}).data,
                         status=status.HTTP_201_CREATED)


class ReportListView(APIView):
    def get(self, request):
        base = list(Report.objects.filter(user=request.user))
        facets = available_facets(base)
        filtered = apply_filters(base, request.query_params)
        sorted_reports = apply_sort(filtered, request.query_params.get('sort'))
        page_items, meta = paginate(sorted_reports, request.query_params)
        return Response({
            'results': ReportListSerializer(page_items, many=True, context={'request': request}).data,
            'facets': facets,
            **meta,
        })


class ReportDetailView(APIView):
    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk, user=request.user)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ReportSerializer(report, context={'request': request}).data)

    def patch(self, request, pk):
        try:
            report = Report.objects.get(pk=pk, user=request.user)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReportUpdateSerializer(report, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReportSerializer(report, context={'request': request}).data)

    def delete(self, request, pk):
        try:
            report = Report.objects.get(pk=pk, user=request.user)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        report.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReportAdminListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        base = list(Report.objects.select_related('user').all())
        facets = available_facets(base)
        filtered = apply_filters(base, request.query_params)
        owner = (request.query_params.get('owner') or '').strip().lower()
        if owner:
            filtered = [r for r in filtered if r.user_id and owner in r.user.email.lower()]
        sorted_reports = apply_sort(filtered, request.query_params.get('sort'))
        page_items, meta = paginate(sorted_reports, request.query_params)
        return Response({
            'results': ReportAdminListSerializer(page_items, many=True, context={'request': request}).data,
            'facets': facets,
            **meta,
        })


class ReportBulkDeleteView(APIView):
    
    def post(self, request):
        ids = request.data.get('ids')
        if not isinstance(ids, list) or not ids:
            return Response({'detail': 'Provide a non-empty list of report ids.'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Report.objects.filter(pk__in=ids)
        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user)

        deleted_ids = list(queryset.values_list('id', flat=True))
        queryset.delete()
        return Response({'deleted': [str(pk) for pk in deleted_ids]})


class ReportDownloadView(APIView):
    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk, user=request.user)
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

        if report.extracted_data.get('kind') == 'generic_document':
            base_name = os.path.splitext(report.original_filename)[0]
            safe_name = ''.join(c if c.isalnum() or c in '-_ ' else '_' for c in base_name).strip() or 'document'
            download_name = f'{safe_name}_analysis.xlsx'
        else:
            date_part = report.report_date.isoformat() if report.report_date else 'report'
            download_name = f'RSE_Report_{date_part}.xlsx'
        return FileResponse(
            open(report.generated_excel.path, 'rb'),
            as_attachment=True,
            filename=download_name,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )


class ReportChatView(APIView):
    def _get_report(self, request, pk):
        return Report.objects.get(pk=pk, user=request.user)

    def get(self, request, pk):
        try:
            report = self._get_report(request, pk)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        if report.status != Report.Status.COMPLETED or not report.extracted_data:
            return Response({'detail': 'This document has not finished processing yet.'},
                             status=status.HTTP_409_CONFLICT)

        messages = report.chat_messages.all()
        suggestions = chat_service.suggested_questions(report.extracted_data)
        return Response({
            'messages': ChatMessageSerializer(messages, many=True).data,
            'suggested_questions': suggestions,
        })

    def post(self, request, pk):
        try:
            report = self._get_report(request, pk)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        if report.status != Report.Status.COMPLETED or not report.extracted_data:
            return Response({'detail': 'This document has not finished processing yet.'},
                             status=status.HTTP_409_CONFLICT)

        question = (request.data.get('message') or '').strip()
        if not question:
            return Response({'detail': 'Please enter a question.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(question) > MAX_CHAT_MESSAGE_LENGTH:
            return Response({'detail': f'Questions are limited to {MAX_CHAT_MESSAGE_LENGTH} characters.'},
                             status=status.HTTP_400_BAD_REQUEST)

        user_message = ChatMessage.objects.create(report=report, role=ChatMessage.Role.USER, content=question)
        result = chat_service.answer_question(report.extracted_data, question)
        assistant_message = ChatMessage.objects.create(
            report=report,
            role=ChatMessage.Role.ASSISTANT,
            content=result.answer,
            sources=[s.to_dict() for s in result.sources],
            confidence=result.confidence,
        )

        return Response({
            'user_message': ChatMessageSerializer(user_message).data,
            'assistant_message': ChatMessageSerializer(assistant_message).data,
        }, status=status.HTTP_201_CREATED)


class ReportAnalysisView(APIView):
    """Advanced Intelligence bundle: Investigate, Anomaly Radar, Data
    Forensics, Discoveries/What Matters Most, the Entity Relationship
    Graph, Geographic Intelligence, Document Vision, Intelligent Alerts,
    and (RSE only) the Trading/Market view — computed fresh on every
    request from the current extracted_data. See services.intelligence.
    """

    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk, user=request.user)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        if report.status != Report.Status.COMPLETED or not report.extracted_data:
            return Response({'detail': 'This document has not finished processing yet.'},
                             status=status.HTTP_409_CONFLICT)

        rules = AlertRuleSerializer(report.alert_rules.all(), many=True).data
        analysis = build_analysis(report.extracted_data, alert_rules=rules)
        return Response(analysis)


class ReportExplainView(APIView):
    """Explain This: the literal calculation and source rows behind one
    metric or chart already shown on the dashboard."""

    def post(self, request, pk):
        try:
            report = Report.objects.get(pk=pk, user=request.user)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        if report.status != Report.Status.COMPLETED or not report.extracted_data:
            return Response({'detail': 'This document has not finished processing yet.'},
                             status=status.HTTP_409_CONFLICT)

        datasets = to_analysis_datasets(report.extracted_data)
        chart = request.data.get('chart')
        if chart:
            return Response(explain_chart(datasets, chart))

        dataset_name = request.data.get('dataset')
        column_name = request.data.get('column', '')
        kind = request.data.get('kind', 'sum')
        if not dataset_name:
            return Response({'detail': 'A "dataset" (and optionally "column"/"kind") or "chart" is required.'},
                             status=status.HTTP_400_BAD_REQUEST)
        return Response(explain_metric(datasets, dataset_name, column_name, kind))


class ReportDashboardBuilderView(APIView):
    """AI Dashboard Builder: matches a free-text request against this
    document's own datasets/columns and returns the closest matching
    chart — never a fabricated one."""

    def post(self, request, pk):
        try:
            report = Report.objects.get(pk=pk, user=request.user)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        if report.status != Report.Status.COMPLETED or not report.extracted_data:
            return Response({'detail': 'This document has not finished processing yet.'},
                             status=status.HTTP_409_CONFLICT)

        query = (request.data.get('query') or '').strip()
        if not query:
            return Response({'detail': 'Please describe what you want to see.'}, status=status.HTTP_400_BAD_REQUEST)

        datasets = to_analysis_datasets(report.extracted_data)
        return Response(suggest_visualization(datasets, query))


class ReportCompareView(APIView):
    """Time Machine: compares this report against another of the user's
    own reports."""

    def get(self, request, pk):
        try:
            base = Report.objects.get(pk=pk, user=request.user)
            other = Report.objects.get(pk=request.query_params.get('with'), user=request.user)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        except (ValueError, TypeError):
            return Response({'detail': 'Provide a valid "with" report id to compare against.'},
                             status=status.HTTP_400_BAD_REQUEST)

        for report in (base, other):
            if report.status != Report.Status.COMPLETED or not report.extracted_data:
                return Response({'detail': 'Both documents must have finished processing.'},
                                 status=status.HTTP_409_CONFLICT)

        return Response(compare_reports(base.extracted_data, other.extracted_data))


class ReportAlertsView(APIView):
    """Intelligent Alerts: threshold rules a user attaches to one report."""

    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk, user=request.user)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AlertRuleSerializer(report.alert_rules.all(), many=True).data)

    def post(self, request, pk):
        try:
            report = Report.objects.get(pk=pk, user=request.user)
        except Report.DoesNotExist:
            return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AlertRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(report=report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReportAlertDetailView(APIView):
    def delete(self, request, pk, alert_id):
        try:
            rule = AlertRule.objects.get(pk=alert_id, report_id=pk, report__user=request.user)
        except AlertRule.DoesNotExist:
            return Response({'detail': 'Alert not found.'}, status=status.HTTP_404_NOT_FOUND)
        rule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
