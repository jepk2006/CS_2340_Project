from django.urls import path
from . import views_applications


app_name = "applications"


urlpatterns = [
    # Job seeker views
    path("my/", views_applications.my_applications, name="my_applications"),
    
    # Recruiter views
    path("recruiter/", views_applications.recruiter_applications, name="recruiter_applications"),
    path("<int:pk>/", views_applications.application_detail, name="application_detail"),
    
    # Application management
    path("update-status/", views_applications.update_application_status, name="update_status"),
    path("<int:pk>/toggle-flag/", views_applications.toggle_flag, name="toggle_flag"),
    path("<int:pk>/update-priority/", views_applications.update_priority, name="update_priority"),
    path("bulk-update/", views_applications.bulk_update_status, name="bulk_update_status"),
]


