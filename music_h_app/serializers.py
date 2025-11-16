from rest_framework import serializers
from .models import ExpressionRecord, Student,User

class StudentSerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(queryset = User.objects.all())
    class Meta:
        model = Student
        fields = ['id','teacher','name','account']

class ExpressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpressionRecord
        fields = '__all__'
        read_only_fields = ('timestamp',)

class MusicGenerationSerializer(serializers.Serializer):
    prompt = serializers.CharField(
        max_length=500,
        required=True,
        help_text="音乐描述文本"
    )
    duration = serializers.IntegerField(
        min_value=5,
        max_value=120,
        default=30,
        help_text="音乐时长(秒), 5-120秒"
    )
    format = serializers.ChoiceField(
        choices=['mp3', 'wav'],
        default='mp3',
        help_text="输出格式: mp3或wav"
    )
    quality = serializers.ChoiceField(
        choices=['low', 'medium', 'high'],
        default='medium',
        required=False,
        help_text="生成质量"
    )


class VideoGenerationSerializer(serializers.Serializer):
    prompt = serializers.CharField(
        max_length=500,
        required=True,
        help_text="视频描述文本"
    )
    duration = serializers.IntegerField(
        min_value=2,
        max_value=6,
        default=4,
        required=False,
        help_text="视频时长(秒)，受模型限制"
    )
    fps = serializers.IntegerField(
        min_value=4,
        max_value=12,
        default=8,
        required=False,
        help_text="帧率"
    )
    resolution = serializers.ChoiceField(
        choices=['512x512', '768x512', '512x768'],
        default='512x512',
        required=False,
        help_text="输出分辨率"
    )