from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from music_h_app.models import User
from django.contrib.auth import logout

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print('收到注册信息:', data)  # 打印收到的数据
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirm_password')

            if password != confirm_password:
                return JsonResponse({'success': False, 'message': '两次密码不一致'})

            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'message': '用户名已存在'})

            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': '邮箱已注册'})

            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    elif request.method == 'GET':
        return JsonResponse({'success': False, 'message': '请使用POST提交注册信息'})
    else:
        return JsonResponse({'success': False, 'message': '不支持的请求方法'})
    
def register_page(request):
    # 只负责渲染注册页面
    return render(request, 'music_h_app/register.html')

from django.contrib.auth import authenticate, login

@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print('收到登录信息:', data)  # 打印收到的数据
            username = data.get('username')
            password = data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'success': True, 'username': user.username })
            else:
                return JsonResponse({'success': False, 'message': '用户名或密码错误'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': '仅支持POST'})
    
def login_page(request):
    # 登录页面
    return render(request, 'music_h_app/login.html')


@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'message': '仅支持 POST 请求'})
    
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