from django.urls import path
from . import views


app_name = "jobs"


urlpatterns = [
    path("", views.JobListView.as_view(), name="job_list"),
    path("<int:pk>/", views.JobDetailView.as_view(), name="job_detail"),
    path("<int:pk>/apply/", views.apply_one_click, name="apply_one_click"),
]


