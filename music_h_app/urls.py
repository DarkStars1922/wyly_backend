from django.urls import path

from .api.expression_view import(
    ExpressionAPIView
)
from .api.home_view import(
    HomeAPIView,
    LyricAPIView
    
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
    GenerateMusicView
)
urlpatterns = [
    path('',HomeAPIView.as_view(),name='home'),
    path('register/',UserRegisterAPIView.as_view(),name='register'),
    path('login/',UserLoginAPIView.as_view(),name='login'),
    path('logout/',UserLogoutAPIView.as_view(),name='logout'),
    path('students/',StudentListCreateAPIView.as_view(),name='students-list'),
    path('students/<int:pk>/',StudentRetrieveUpdateDestroyAPIView.as_view(),name="student-details"),
    path('generate/', GenerateMusicView.as_view(), name='generate-music'),
    path('expressions/', ExpressionAPIView.as_view(), name='expression-api'),
    path('lyric/', LyricAPIView.as_view(), name='lyric-api'),
]