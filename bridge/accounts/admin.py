from django.contrib import admin
from .models import JobSeekerProfile


@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "visibility", "updated_at")
    list_filter = ("visibility",)
    search_fields = ("user__username", "headline", "bio")

# Register your models here.
