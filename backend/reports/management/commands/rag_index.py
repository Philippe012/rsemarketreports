"""Builds RAG chunks for completed reports — use once to backfill reports
uploaded before RAG existed, or with --all after changing embedders."""
from django.core.management.base import BaseCommand

from reports.models import Report
from services.rag.indexing import index_report


class Command(BaseCommand):
    help = 'Index completed reports for RAG chat (pending/failed only unless --all).'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Re-index every completed report.')

    def handle(self, *args, **options):
        reports = Report.objects.filter(status=Report.Status.COMPLETED)
        if not options['all']:
            reports = reports.exclude(index_status=Report.IndexStatus.INDEXED)

        ok = failed = 0
        for report in reports.iterator():
            if index_report(report):
                ok += 1
            else:
                failed += 1
                self.stderr.write(f'Failed: {report.pk} ({report.original_filename}): {report.index_error}')
        self.stdout.write(self.style.SUCCESS(f'Indexed {ok} report(s); {failed} failed.'))
