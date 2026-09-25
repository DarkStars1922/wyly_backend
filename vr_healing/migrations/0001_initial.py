# Generated manually for the small VR healing data model.
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MediaAsset",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("asset_id", models.CharField(max_length=100, unique=True)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("video", "Video"),
                            ("music", "Music"),
                            ("soundscape", "Soundscape"),
                        ],
                        max_length=16,
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=200)),
                ("url", models.URLField(blank=True)),
                ("local_path", models.CharField(blank=True, max_length=300)),
                ("scene", models.CharField(blank=True, max_length=40)),
                ("function_tag", models.CharField(blank=True, max_length=80)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("enabled", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("kind", "asset_id")},
        ),
        migrations.CreateModel(
            name="VRSession",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("session_key", models.CharField(db_index=True, max_length=64)),
                ("consent", models.BooleanField(default=False)),
                ("companion", models.CharField(max_length=16)),
                ("preferences", models.JSONField(default=dict)),
                ("before", models.JSONField(blank=True, null=True)),
                ("after", models.JSONField(blank=True, null=True)),
                ("plan", models.JSONField(blank=True, null=True)),
                ("elapsed_seconds", models.PositiveIntegerField(default=0)),
                ("duration_seconds", models.PositiveIntegerField(blank=True, null=True)),
                ("feedback", models.JSONField(default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("started", "Started"),
                            ("completed", "Completed"),
                            ("abandoned", "Abandoned"),
                        ],
                        default="created",
                        max_length=16,
                    ),
                ),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("analysis_revision", models.PositiveIntegerField(default=0)),
                (
                    "analysis_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("ready", "Ready"),
                            ("unavailable", "Unavailable"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("analysis_text", models.TextField(blank=True, null=True)),
                ("analysis_model", models.CharField(blank=True, max_length=80, null=True)),
                ("analysis_generated_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="vr_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.AddIndex(
            model_name="vrsession",
            index=models.Index(fields=("session_key", "-created_at"), name="vr_healing__session_183a19_idx"),
        ),
    ]
