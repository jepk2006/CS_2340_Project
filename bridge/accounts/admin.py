from django.contrib import admin
from .models import JobSeekerProfile, SavedSearch, TalentMessage


@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "visibility", "account_type", "updated_at")
    list_filter = ("visibility", "account_type", "updated_at")
    search_fields = ("user__username", "headline", "bio")


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ("name", "recruiter", "is_active", "created_at", "last_check")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "recruiter__username", "query")
    readonly_fields = ("created_at", "updated_at", "last_check")
    filter_horizontal = ("skills",)
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("recruiter", "name", "query")
        }),
        ("Search Criteria", {
            "fields": ("skills", "location_city", "location_state", "location_country")
        }),
        ("Settings", {
            "fields": ("is_active", "last_check")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(TalentMessage)
class TalentMessageAdmin(admin.ModelAdmin):
    list_display = ("title", "recruiter", "saved_search", "profile", "message_type", "is_read", "created_at")
    list_filter = ("message_type", "is_read", "created_at", "recruiter")
    search_fields = ("title", "content", "recruiter__username", "profile__user__username", "saved_search__name")
    readonly_fields = ("created_at",)
    
    fieldsets = (
        ("Message Information", {
            "fields": ("recruiter", "saved_search", "profile", "message_type")
        }),
        ("Content", {
            "fields": ("title", "content")
        }),
        ("Status", {
            "fields": ("is_read", "created_at")
        }),
    )

# Register your models here.
