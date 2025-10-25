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
]


