from django.urls import path

from . import views
from .api.expression_view import ExpressionAPIView
from .api.home_view import (
    HomeAPIView,
    LyricAPIView,
    MusicCreationView,
    MeditationMusicView,
    OptimizePromptView,
    ShowcaseView,
)
from .api.stu_view import StudentListCreateAPIView, StudentRetrieveUpdateDestroyAPIView
from .api.music_generator_view import GenerateMusicView, ProgressView
from .api.video_generator_view import GenerateVideoView

urlpatterns = [
    path('', HomeAPIView.as_view(), name='home'),
    path('login/', views.login_page, name='login_page'),
    path('register/', views.register_page, name='register_page'),

    # Legacy non-/api endpoints kept so existing links/bookmarks continue to work.
    path('students/', StudentListCreateAPIView.as_view(), name='students-list'),
    path('students/<int:pk>/', StudentRetrieveUpdateDestroyAPIView.as_view(), name='student-details'),
    path('generate/', GenerateMusicView.as_view(), name='generate-music'),
    path('video/generate/', GenerateVideoView.as_view(), name='generate-video'),
    path('progress/<str:task_id>/', ProgressView.as_view(), name='progress'),
    path('expressions/', ExpressionAPIView.as_view(), name='expression-api'),
    path('optimize-prompt/', OptimizePromptView.as_view(), name='optimize-prompt'),

    path('lyric/', LyricAPIView.as_view(), name='lyric-api'),
    path('music-creation/', MusicCreationView.as_view(), name='music-creation'),
    path('meditation-music/', MeditationMusicView.as_view(), name='meditation-music'),
    path('showcase/', ShowcaseView.as_view(), name='showcase'),
    path('music-visualizer/', views.music_visualizer_enhanced_page, name='music_visualizer_enhanced'),
    # Healing spaces
    path('mindfulness/', views.mindfulness_page, name='mindfulness'),
    path('wood/', views.wood_page, name='wood_xiao'),
    path('fire/', views.fire_page, name='fire_erhu'),
    path('earth/', views.earth_page, name='earth_pipa'),
    path('metal/', views.metal_page, name='metal_zhudi'),
    path('water/', views.water_page, name='water_guqin'),
    path('earth_360/', views.earth_360_page, name='earth_360'),
    path('fire_360/', views.fire_360_page, name='fire_360'),
    path('metal_360/', views.metal_360_page, name='metal_360'),
    path('water_360/', views.water_360_page, name='water_360'),
    path('wood_360/', views.wood_360_page, name='wood_360'),
    # Cyber avatar
    path('saibo/', views.saibo_page, name='saibo'),
    # Healing report
    path('report_page/', views.report_page, name='report_page'),
]
