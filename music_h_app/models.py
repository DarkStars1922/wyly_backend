from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):

    class Meta:
        def __str__(self):
            return f"{self.username}"
        
class Student(models.Model):

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='students',
        verbose_name="所属老师")
    name = models.CharField(max_length=255,verbose_name="姓名")
    account = models.CharField(max_length=255,verbose_name="账号")

    class Meta:
        def __str__(self):
            return f'学生名称：{self.name} 学生账号： {self.account}'
        
class ExpressionRecord(models.Model):
    EXPRESSION_CHOICES = [
        ('neutral', 'Neutral'),
        ('happy', 'Happy'),
        ('sad', 'Sad'),
        ('angry', 'Angry'),
        ('fearful', 'Fearful'),
        ('disgusted', 'Disgusted'),
        ('surprised', 'Surprised'),
    ]
    
    timestamp = models.DateTimeField(default=timezone.now)
    expression = models.CharField(max_length=20, choices=EXPRESSION_CHOICES)
    confidence = models.FloatField()
    neutral = models.FloatField()
    happy = models.FloatField()
    sad = models.FloatField()
    angry = models.FloatField()
    fearful = models.FloatField()
    disgusted = models.FloatField()
    surprised = models.FloatField()
    #image = models.TextField(blank=True, null=True)  # Base64 encoded image
    
    def __str__(self):
        return f"{self.timestamp} - {self.expression} ({self.confidence:.1%})"



