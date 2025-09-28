from django.urls import path
from . import views


app_name = "jobs"


urlpatterns = [
    path("", views.JobListView.as_view(), name="job_list"),
    path("map-data/", views.job_map_data, name="job_map_data"),
    path("<int:pk>/", views.JobDetailView.as_view(), name="job_detail"),
    path("<int:pk>/apply/", views.apply_one_click, name="apply_one_click"),
    path("new/", views.job_create, name="job_create"),
]


