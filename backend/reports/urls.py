from django.urls import path

from . import views

urlpatterns = [
    path('', views.ReportListView.as_view(), name='report-list'),
    path('upload/', views.ReportUploadView.as_view(), name='report-upload'),
    path('admin/', views.ReportAdminListView.as_view(), name='report-admin-list'),
    path('bulk-delete/', views.ReportBulkDeleteView.as_view(), name='report-bulk-delete'),
    path('<uuid:pk>/', views.ReportDetailView.as_view(), name='report-detail'),
    path('<uuid:pk>/download/', views.ReportDownloadView.as_view(), name='report-download'),
    path('<uuid:pk>/chat/', views.ReportChatView.as_view(), name='report-chat'),
]
