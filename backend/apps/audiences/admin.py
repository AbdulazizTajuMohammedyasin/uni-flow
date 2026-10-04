"""Back-office page for audiences ("who is this for?"), opened from an insight's form."""

from django.contrib import admin

from .models import Audience


@admin.register(Audience)
class AudienceAdmin(admin.ModelAdmin):
    list_display = ("__str__", "created_at")
    filter_horizontal = ("schools", "programmes", "intakes", "courses")
    raw_id_fields = ("sections",)
