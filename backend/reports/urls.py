from django.urls import path

from . import views

urlpatterns = [
    path('upload/', views.ReportUploadView.as_view(), name='report-upload'),
    path('<uuid:pk>/', views.ReportDetailView.as_view(), name='report-detail'),
    path('<uuid:pk>/download/', views.ReportDownloadView.as_view(), name='report-download'),
]
