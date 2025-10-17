from django.contrib import admin
from .models import Skill, Job, Application


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "work_type", "visa_sponsorship", "created_at")
    list_filter = ("work_type", "visa_sponsorship")
    search_fields = ("title", "company", "description")
    filter_horizontal = ("skills",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "applicant", "status", "priority", "flagged", "created_at", "stage_changed_at")
    list_filter = ("status", "priority", "flagged", "created_at")
    search_fields = ("job__title", "applicant__username", "applicant__email")
    readonly_fields = ("created_at", "updated_at", "stage_changed_at")
    fieldsets = (
        ("Application Info", {
            "fields": ("job", "applicant", "status", "note")
        }),
        ("Recruiter Management", {
            "fields": ("priority", "flagged", "recruiter_notes", "position_in_stage")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "stage_changed_at"),
            "classes": ("collapse",)
        }),
    )

# Register your models here.
