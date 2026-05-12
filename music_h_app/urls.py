from django.urls import path

from .api.expression_view import(
    ExpressionAPIView
)
from .api.home_view import(
    HomeAPIView,
    LyricAPIView,
    MusicCreationView,
    MeditationMusicView,
    OptimizePromptView,
    ShowcaseView
)
from .api.auth_view import(
    UserLoginAPIView,
    UserRegisterAPIView,
    UserLogoutAPIView
)
from .api.stu_view import(
    StudentListCreateAPIView,
    StudentRetrieveUpdateDestroyAPIView
)
from .api.music_generator_view import(
    GenerateMusicView,
    ProgressView
)
from .api.video_generator_view import (
    GenerateVideoView,
)
urlpatterns = [
    path('',HomeAPIView.as_view(),name='home'),
    path('register/',UserRegisterAPIView.as_view(),name='register'),
    path('login/',UserLoginAPIView.as_view(),name='login'),
    path('logout/',UserLogoutAPIView.as_view(),name='logout'),
    path('students/',StudentListCreateAPIView.as_view(),name='students-list'),
    path('students/<int:pk>/',StudentRetrieveUpdateDestroyAPIView.as_view(),name="student-details"),
    path('generate/', GenerateMusicView.as_view(), name='generate-music'),
    path('video/generate/', GenerateVideoView.as_view(), name='generate-video'),
    path('progress/<str:task_id>/', ProgressView.as_view(), name='progress'),
    path('expressions/', ExpressionAPIView.as_view(), name='expression-api'),
    path('lyric/', LyricAPIView.as_view(), name='lyric-api'),
    path('music-creation/', MusicCreationView.as_view(), name='music-creation'),
    path('meditation-music/', MeditationMusicView.as_view(), name='meditation-music'),
    path('showcase/', ShowcaseView.as_view(), name='showcase'),
    path('optimize-prompt/', OptimizePromptView.as_view(), name='optimize-prompt'),
]