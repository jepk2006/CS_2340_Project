from django.urls import path
from . import views


app_name = "accounts"


urlpatterns = [
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("signup/", views.signup, name="signup"),
    path("talent/", views.recruiter_talent_search, name="recruiter_talent_search"),
    path("talent/save-search/", views.save_search, name="save_search"),
    path("saved-searches/", views.saved_searches_list, name="saved_searches"),
    path("saved-searches/<int:search_id>/", views.saved_search_detail, name="saved_search_detail"),
    path("saved-searches/<int:search_id>/edit/", views.edit_saved_search, name="edit_saved_search"),
    path("saved-searches/<int:search_id>/delete/", views.delete_saved_search, name="delete_saved_search"),
    path("saved-searches/<int:search_id>/toggle/", views.toggle_saved_search, name="toggle_saved_search"),
    path("talent/messages/", views.talent_messages, name="talent_messages"),
    path("talent/check-matches/", views.check_new_matches, name="check_new_matches"),
    path("talent/unread-count/", views.get_unread_messages_count, name="unread_messages_count"),
    
    # Messaging URLs
    path("messages/", views.conversations_list, name="conversations_list"),
    path("messages/<int:conversation_id>/", views.conversation_detail, name="conversation_detail"),
    path("messages/start/<int:candidate_id>/", views.start_conversation, name="start_conversation"),
    path("messages/<int:conversation_id>/send/", views.send_message, name="send_message"),
    
    # Admin Export URLs
    path("admin/export/", views.admin_export_dashboard, name="admin_export_dashboard"),
    path("admin/export/users/", views.export_users, name="admin_export_users"),
    path("admin/export/profiles/", views.export_profiles, name="admin_export_profiles"),
    path("admin/export/jobs/", views.export_jobs, name="admin_export_jobs"),
    path("admin/export/applications/", views.export_applications, name="admin_export_applications"),
    path("admin/export/skills/", views.export_skills, name="admin_export_skills"),
    path("admin/export/conversations/", views.export_conversations, name="admin_export_conversations"),
    path("admin/export/messages/", views.export_messages, name="admin_export_messages"),
    path("admin/export/saved-searches/", views.export_saved_searches, name="admin_export_saved_searches"),
]


