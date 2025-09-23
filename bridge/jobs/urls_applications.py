from django.urls import path
from . import views_applications


app_name = "applications"


urlpatterns = [
    path("my/", views_applications.my_applications, name="my_applications"),
    path("recruiter/", views_applications.recruiter_applications, name="recruiter_applications"),
]


