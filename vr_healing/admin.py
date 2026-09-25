from django.contrib import admin

from .models import MediaAsset, VRSession


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("asset_id", "kind", "title", "scene", "enabled", "updated_at")
    list_filter = ("kind", "enabled", "scene")
    search_fields = ("asset_id", "title", "function_tag")


@admin.register(VRSession)
class VRSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "companion", "status", "analysis_status", "created_at")
    list_filter = ("status", "analysis_status", "companion")
    search_fields = ("id", "session_key")
    readonly_fields = ("id", "created_at", "updated_at")
