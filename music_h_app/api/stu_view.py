from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,generics
from ..models import Student
from ..serializers import StudentSerializer


class StudentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def list(self,request,*args,**kwargs):
        queryset = Student.objects.filter(teacher=request.user.id)
        serializer = StudentSerializer(queryset,many=True)
        return Response({
            'code':200,
            'message':'学生列表获取成功！',
            'data':serializer.data,
        },status=status.HTTP_200_OK)
    
    def create(self,request,*args,**kwargs):
        response = super().create(request,*args,**kwargs)
        return Response({
            'code':201,
            'message':'学生创建成功！',
            'data':response.data,
        },status=status.HTTP_201_CREATED)
    
class StudentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            'code':200,
            'message':'学生信息获取成功！',
            'data':response.data,
        },status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            'code':200,
            'message':'学生信息修改成功！',
            'data':response.data,
        },status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({
            'code':204,
            'message':'学生信息删除成功！',
        },status=status.HTTP_204_NO_CONTENT)
    