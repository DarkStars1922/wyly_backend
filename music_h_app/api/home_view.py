from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer,JSONRenderer

from ..models import User

class HomeAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/index.html'

    def get(self,request):
       return render(request,'music_h_app/index.html')
    
class LyricAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/lyric_creator.html'

    def get(self,request):
       return render(request,'music_h_app/lyric_creator.html')
        

