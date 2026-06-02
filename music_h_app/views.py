from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from json import JSONDecodeError
from music_h_app.models import User
from django.contrib.auth import authenticate, login, logout
from .api.graduation_wall_view import build_graduation_wall_config


def _read_json_body(request):
    try:
        return json.loads(request.body or b"{}")
    except (TypeError, JSONDecodeError):
        return None


def _api_error(message, status=400):
    return JsonResponse({'success': False, 'message': message}, status=status)


@csrf_exempt
def register_user(request):
    if request.method != 'POST':
        return _api_error('请使用 POST 提交注册信息', status=405)

    data = _read_json_body(request)
    if data is None:
        return _api_error('请求格式不正确，请刷新页面后重试')

    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    confirm_password = data.get('confirm_password') or ''

    if not username or not email or not password:
        return _api_error('用户名、邮箱和密码不能为空')

    if password != confirm_password:
        return _api_error('两次密码不一致')

    if User.objects.filter(username=username).exists():
        return _api_error('用户名已存在')

    if User.objects.filter(email=email).exists():
        return _api_error('邮箱已注册')

    try:
        user = User.objects.create_user(username=username, email=email, password=password)
    except Exception:
        return _api_error('注册失败，请稍后重试', status=500)

    return JsonResponse({'success': True, 'username': user.username})


def register_page(request):
    return render(request, 'music_h_app/register.html')


@csrf_exempt
def login_user(request):
    if request.method != 'POST':
        return _api_error('请使用 POST 提交登录信息', status=405)

    data = _read_json_body(request)
    if data is None:
        return _api_error('请求格式不正确，请刷新页面后重试')

    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return _api_error('请输入用户名和密码')

    user = authenticate(request, username=username, password=password)
    if user is None:
        return _api_error('用户名或密码错误')

    login(request, user)
    return JsonResponse({'success': True, 'username': user.username})


def login_page(request):
    return render(request, 'music_h_app/login.html')


@csrf_exempt
def logout_view(request):
    if request.method != 'POST':
        return _api_error('请使用 POST 退出登录', status=405)

    logout(request)
    return JsonResponse({'success': True})
    
# 其他页面视图
def music_creation_page(request):
    return render(request, 'music_h_app/music_creation.html')

def lyric_creator_page(request):
    return render(request, 'music_h_app/lyric_creator.html')

def meditation_music_page(request):
    return render(request, 'music_h_app/meditation_music.html')

def music_visualizer_enhanced_page(request):
    return render(request, 'music_h_app/music_visualizer_enhanced.html')

def showcase_page_page(request):
    return render(request, 'music_h_app/showcase_page.html')

def video_creation_page(request):
    return render(request, 'music_h_app/video_creation.html')

def mindfulness_page(request):
    return render(request, 'music_h_app/mindfulness.html')

def wood_page(request):
    return render(request, 'music_h_app/wood_xiao.html')

def fire_page(request):
    return render(request, 'music_h_app/fire_erhu.html')

def earth_page(request):
    return render(request, 'music_h_app/earth_pipa.html')

def metal_page(request):
    return render(request, 'music_h_app/metal_zhudi.html')

def water_page(request):
    return render(request, 'music_h_app/water_guqin.html')

def earth_360_page(request):
    video_id = request.GET.get('id', '')
    return render(request, 'music_h_app/earth_360.html', {'video_id': video_id})

def fire_360_page(request):
    video_id = request.GET.get('id', '')
    return render(request, 'music_h_app/fire_360.html', {'video_id': video_id})

def metal_360_page(request):
    video_id = request.GET.get('id', '')
    return render(request, 'music_h_app/metal_360.html', {'video_id': video_id})

def water_360_page(request):
    video_id = request.GET.get('id', '')
    return render(request, 'music_h_app/water_360.html', {'video_id': video_id})

def wood_360_page(request):
    video_id = request.GET.get('id', '')
    return render(request, 'music_h_app/wood_360.html', {'video_id': video_id})

def saibo_page(request):
    return render(request, 'music_h_app/saibo.html')

def report_page(request):
    return render(request, 'music_h_app/report_page.html') 

def graduation_wall_page(request):
    return render(
        request,
        'music_h_app/graduation_wall.html',
        {'graduation_wall_config': build_graduation_wall_config()},
    )
