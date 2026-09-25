from django.urls import path

from . import views


urlpatterns = [
    path("config/", views.config, name="vr-config"),
    path("sessions/", views.sessions, name="vr-sessions"),
    path("sessions/<uuid:session_id>/", views.session_detail, name="vr-session-detail"),
    path("sessions/<uuid:session_id>/assessments/", views.assessment, name="vr-assessment"),
    path("sessions/<uuid:session_id>/recommendation/", views.recommendation, name="vr-recommendation"),
    path("sessions/<uuid:session_id>/experience/", views.experience, name="vr-experience"),
    path("sessions/<uuid:session_id>/report/", views.report, name="vr-report"),
    path("sessions/<uuid:session_id>/analysis/", views.analysis, name="vr-analysis"),
    path("device-assessments/", views.device_assessment, name="vr-device-assessment"),
]
