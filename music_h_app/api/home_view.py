from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

class HomeAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/index.html'

    def get(self, request):
        return render(request, self.template_name)
    
class LyricAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/lyric_creator.html'

    def get(self, request):
        return render(request, self.template_name)
        

class MusicCreationView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/music_creation.html'

    def get(self, request):
        return render(request, self.template_name)


class MeditationMusicView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/meditation_music.html'

    def get(self, request):
        return render(request, self.template_name)


class ShowcaseView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'music_h_app/showcase_page.html'

    def get(self, request):
        return render(request, self.template_name)


