from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer
from rest_framework import status
from ..models import ExpressionRecord
from ..serializers import ExpressionSerializer
from django.utils import timezone

class ExpressionAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/expression.html'

    def get(self,request):
       return render(request,'music_h_app/expression.html')
    
    def post(self, request, format=None):
        serializer = ExpressionSerializer(data=request.data)
        if serializer.is_valid():
            # Add timestamp before saving
            serializer.save(timestamp=timezone.now())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)