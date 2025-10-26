from django.urls import path
from . import views_applications


app_name = "applications"


urlpatterns = [
    path("my/", views_applications.my_applications, name="my_applications"),
    path("recruiter/", views_applications.recruiter_applications, name="recruiter_applications"),
    path("update-status/", views_applications.update_application_status, name="update_status"),
    path("email/", views_applications.send_candidate_email, name="send_candidate_email"),
]


