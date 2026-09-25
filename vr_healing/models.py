import uuid

from django.conf import settings
from django.db import models


class VRSession(models.Model):
    STATUS_CHOICES = (
        ("created", "Created"),
        ("started", "Started"),
        ("completed", "Completed"),
        ("abandoned", "Abandoned"),
    )
    ANALYSIS_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("ready", "Ready"),
        ("unavailable", "Unavailable"),
        ("failed", "Failed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vr_sessions",
    )
    session_key = models.CharField(max_length=64, db_index=True)
    consent = models.BooleanField(default=False)
    companion = models.CharField(max_length=16)
    preferences = models.JSONField(default=dict)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    plan = models.JSONField(null=True, blank=True)
    elapsed_seconds = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="created")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    analysis_revision = models.PositiveIntegerField(default=0)
    analysis_status = models.CharField(
        max_length=16, choices=ANALYSIS_STATUS_CHOICES, default="pending"
    )
    analysis_text = models.TextField(null=True, blank=True)
    analysis_model = models.CharField(max_length=80, null=True, blank=True)
    analysis_generated_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("session_key", "-created_at"))]


class MediaAsset(models.Model):
    KIND_CHOICES = (
        ("video", "Video"),
        ("music", "Music"),
        ("soundscape", "Soundscape"),
    )

    asset_id = models.CharField(max_length=100, unique=True)
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    title = models.CharField(max_length=200, blank=True)
    url = models.URLField(blank=True)
    local_path = models.CharField(max_length=300, blank=True)
    scene = models.CharField(max_length=40, blank=True)
    function_tag = models.CharField(max_length=80, blank=True)
    tags = models.JSONField(default=list, blank=True)
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("kind", "asset_id")

    def __str__(self):
        return self.title or self.asset_id
