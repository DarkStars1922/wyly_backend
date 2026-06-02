from django.urls import path

from . import views
from .api.expression_view import ExpressionAPIView
from .api.home_view import OptimizePromptView
from .api.stu_view import StudentListCreateAPIView, StudentRetrieveUpdateDestroyAPIView
from .api.music_generator_view import GenerateMusicView, ProgressView
from .api.video_generator_view import GenerateVideoView
from .api.graduation_wall_view import GraduationWallConfigAPIView

urlpatterns = [
    path('register/', views.register_user, name='api-register'),
    path('login/', views.login_user, name='api-login'),
    path('logout/', views.logout_view, name='api-logout'),
    path('students/', StudentListCreateAPIView.as_view(), name='api-students-list'),
    path('students/<int:pk>/', StudentRetrieveUpdateDestroyAPIView.as_view(), name='api-student-details'),
    path('generate/', GenerateMusicView.as_view(), name='api-generate-music'),
    path('video/generate/', GenerateVideoView.as_view(), name='api-generate-video'),
    path('progress/<str:task_id>/', ProgressView.as_view(), name='api-progress'),
    path('expressions/', ExpressionAPIView.as_view(), name='api-expression'),
    path('optimize-prompt/', OptimizePromptView.as_view(), name='api-optimize-prompt'),
    path('graduation-wall/config/', GraduationWallConfigAPIView.as_view(), name='api-graduation-wall-config'),
]
