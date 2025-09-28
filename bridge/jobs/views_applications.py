from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from .models import Application
from accounts.models import JobSeekerProfile


@login_required
def my_applications(request):
    applications = (
        Application.objects.filter(applicant=request.user)
        .select_related("job")
        .order_by("-updated_at")
    )
    grouped = {key: [] for key, _ in Application.Status.choices}
    for app in applications:
        grouped[app.status].append(app)
    status_groups = [
        {"key": key, "label": label, "apps": grouped.get(key, [])}
        for key, label in Application.Status.choices
    ]

    recommended_jobs = []
    if hasattr(request.user, 'jobseeker_profile'):
        recommended_jobs = request.user.jobseeker_profile.get_recommended_jobs()[:5] # Limit to 5 recommended jobs

    return render(
        request,
        "applications/my_applications.html",
        {"status_groups": status_groups, "recommended_jobs": recommended_jobs},
    )


@login_required
def recruiter_applications(request):
    # Handle status updates
    if request.method == "POST":
        application_id = request.POST.get("application_id")
        new_status = request.POST.get("status")
        if application_id and new_status:
            application = get_object_or_404(Application, pk=application_id, job__posted_by=request.user)
            application.status = new_status
            application.save()
            return redirect("applications:recruiter_applications")

    # Optional filters (GET request handling)
    job_id = request.GET.get("job")
    status = request.GET.get("status")

    qs = Application.objects.filter(job__posted_by=request.user).select_related("job", "applicant").order_by("-updated_at")
    if job_id:
        qs = qs.filter(job_id=job_id)
    if status:
        qs = qs.filter(status=status)

    # Group by job, then by status
    jobs_map = {}
    for app in qs:
        jobs_map.setdefault(app.job, {key: [] for key, _ in Application.Status.choices})
        jobs_map[app.job][app.status].append(app)

    grouped = [
        {
            "job": job,
            "status_groups": [
                {"key": key, "label": label, "apps": apps_by_status.get(key, [])}
                for key, label in Application.Status.choices
            ],
        }
        for job, apps_by_status in jobs_map.items()
    ]

    # For filter dropdown
    posted_jobs = {app.job for app in Application.objects.filter(job__posted_by=request.user).select_related("job")}

    context = {
        "grouped": grouped,
        "statuses": Application.Status.choices,
        "posted_jobs": sorted(posted_jobs, key=lambda j: (j.company, j.title)),
        "current_job": int(job_id) if job_id else None,
        "current_status": status or "",
    }
    return render(request, "applications/recruiter_applications.html", context)


