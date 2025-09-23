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
    list_display = ("job", "applicant", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("job__title", "applicant__username")

# Register your models here.
