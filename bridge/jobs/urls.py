from django.urls import path
from . import views


app_name = "jobs"


urlpatterns = [
    path("", views.JobListView.as_view(), name="job_list"),
    path("map-data/", views.job_map_data, name="job_map_data"),
    path("new/", views.JobCreateView.as_view(), name="job_create"),
    path("my-jobs/", views.MyJobsListView.as_view(), name="my_jobs"),
    path("<int:pk>/", views.JobDetailView.as_view(), name="job_detail"),
    path("<int:pk>/edit/", views.JobUpdateView.as_view(), name="job_edit"),
    path("<int:pk>/apply/", views.apply_one_click, name="apply_one_click"),

    # Moderation (Admin)
    path("moderate/", views.moderate_jobs, name="moderate_jobs"),
    path("moderate/<int:job_id>/action/", views.moderate_job_action, name="moderate_job_action"),
    path("moderate/<int:job_id>/", views.job_detail_moderation, name="job_detail_moderation"),
]


