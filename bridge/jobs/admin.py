from django.contrib import admin
from .models import Skill, Job, Application


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "work_type", "moderation_status", "visa_sponsorship", "created_at")
    list_filter = ("work_type", "visa_sponsorship", "moderation_status", "created_at")
    search_fields = ("title", "company", "description")
    filter_horizontal = ("skills",)
    readonly_fields = ("moderated_at",)
    fieldsets = (
        ("Job Details", {
            "fields": ("title", "company", "description", "skills", "work_type", "visa_sponsorship")
        }),
        ("Location", {
            "fields": ("location_city", "location_state", "location_country", "latitude", "longitude")
        }),
        ("Compensation", {
            "fields": ("min_salary", "max_salary")
        }),
        ("Moderation", {
            "fields": ("moderation_status", "moderation_reason", "moderated_by", "moderated_at")
        }),
        ("Metadata", {
            "fields": ("posted_by", "created_at")
        }),
    )


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
