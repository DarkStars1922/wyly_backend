from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
from rest_framework import status
from django.contrib.auth import login,logout,authenticate

from ..models import User

class UserRegisterAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def post(self,request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if User.objects.filter(username = username) :
             return Response({
                'code' : 400,
                'error':'用户已经存在'
            },status=status.HTTP_400_BAD_REQUEST)
        if password != password2:
            return Response({
                'code' : 400,
                'error':'两次输入密码不一致！'
            },status=status.HTTP_400_BAD_REQUEST)
        elif username == None or password == None:
             return Response({
                'code' : 400,
                'error':'用户名或密码不能为空！'
            },status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.create_user(username=username,password=password)
            login(request,user)
            return Response({
                'user_id':user.id,
                'code':201,
                'message':'注册成功！'
            },status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'code' : 400,
                'error':f'出现错误：{e}'
            },status=status.HTTP_400_BAD_REQUEST)
        
        
class UserLoginAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def post(self,request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request=request,username=username,password=password)

        if user is not None and user.is_active:
            login(request,user)
            return Response({
                'user_id':user.id,
                'code': 200,
                'message':'登录成功！'
            },status=status.HTTP_200_OK)
        else:
            return Response({
                'code': 400,
                'error':'用户名或密码错误'
            },status=status.HTTP_400_BAD_REQUEST)
        
class UserLogoutAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get(self,request):
        logout(request)
        return Response({
                'code': 200,
                'message':'登出成功！'
            },status=status.HTTP_200_OK)

