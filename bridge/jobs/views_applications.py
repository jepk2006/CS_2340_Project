from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Application


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
    return render(
        request,
        "applications/my_applications.html",
        {"status_groups": status_groups},
    )


@login_required
def recruiter_applications(request):
    # Optional filters
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


