from django.urls import path
from . import views

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
    path('api/register/', views.register_user, name='register'),  # 注册表单提交api
    path('login/',views.login_page,name='login_page'), # 登录页面
    path('api/login/', views.login_user, name='login'), # 登录表单提交api
    path('api/logout/', views.logout_view, name='logout'),
    path('register/', views.register_page, name='register_page'), # 注册页面

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
    path('music-visualizer/', views.music_visualizer_enhanced_page, name='music_visualizer_enhanced'),
    # 疗愈空间
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
    # 赛博形象
    path('saibo/', views.saibo_page, name='saibo'),
    # 疗愈总结页
    path('report_page/', views.report_page, name='report_page'),
]
