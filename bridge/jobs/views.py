from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, CreateView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django_filters.views import FilterView
from django import forms
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
import django_filters
import math

from .models import Job, Skill, Application
from django.views.decorators.http import require_POST
from accounts.models import JobSeekerProfile
from .decorators import admin_required
from .forms import JobForm


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on Earth using the Haversine formula.
    Returns distance in miles.
    """
    if not all([lat1, lon1, lat2, lon2]):
        return None
    
    # Convert latitude and longitude from decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in miles
    r = 3959
    return c * r


def _get_jobseeker_profile(user):
    if not user.is_authenticated:
        return None
    try:
        return user.jobseeker_profile
    except JobSeekerProfile.DoesNotExist:
        return None


def apply_commute_radius_filter(queryset, user):
    profile = _get_jobseeker_profile(user)
    if not profile or not profile.commute_radius or not profile.latitude or not profile.longitude:
        return queryset

    user_lat = float(profile.latitude)
    user_lon = float(profile.longitude)
    jobs_within_radius = []

    for job in queryset:
        if job.latitude and job.longitude:
            distance = calculate_distance(
                user_lat,
                user_lon,
                float(job.latitude),
                float(job.longitude),
            )
            if distance is not None and distance <= profile.commute_radius:
                jobs_within_radius.append(job.pk)

    if not jobs_within_radius:
        return queryset.none()

    return queryset.filter(pk__in=jobs_within_radius)


def build_distance_lookup(jobs, user):
    profile = _get_jobseeker_profile(user)
    if not profile or not profile.latitude or not profile.longitude:
        return {}

    user_lat = float(profile.latitude)
    user_lon = float(profile.longitude)
    distances = {}

    for job in jobs:
        if job.latitude and job.longitude:
            distance = calculate_distance(
                user_lat,
                user_lon,
                float(job.latitude),
                float(job.longitude),
            )
            if distance is not None:
                distances[job.pk] = round(distance, 1)

    return distances


class JobFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    company = django_filters.CharFilter(field_name="company", lookup_expr="icontains")
    skills = django_filters.ModelMultipleChoiceFilter(queryset=Skill.objects.all(), field_name="skills", conjoined=False)
    location_city = django_filters.CharFilter(field_name="location_city", lookup_expr="icontains")
    location_state = django_filters.CharFilter(field_name="location_state", lookup_expr="icontains")
    location_country = django_filters.CharFilter(field_name="location_country", lookup_expr="icontains")
    min_salary = django_filters.NumberFilter(field_name="min_salary", lookup_expr="gte")
    max_salary = django_filters.NumberFilter(field_name="max_salary", lookup_expr="lte")
    work_type = django_filters.ChoiceFilter(field_name="work_type", choices=Job.WorkType.choices)
    visa_sponsorship = django_filters.BooleanFilter(field_name="visa_sponsorship")

    class Meta:
        model = Job
        fields = [
            "title",
            "company",
            "skills",
            "location_city",
            "location_state",
            "location_country",
            "min_salary",
            "max_salary",
            "work_type",
            "visa_sponsorship",
        ]


class JobListView(FilterView):
    model = Job
    template_name = "jobs/job_list.html"
    context_object_name = "jobs"
    paginate_by = 10
    filterset_class = JobFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        if not (self.request.user.is_authenticated and self.request.user.is_superuser):
            queryset = queryset.exclude(moderation_status=Job.ModerationStatus.REMOVED)
        return apply_commute_radius_filter(queryset, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job_list = context.get("jobs", [])
        context["job_distances"] = build_distance_lookup(job_list, self.request.user)
        return context


class JobDetailView(DetailView):
    model = Job
    template_name = "jobs/job_detail.html"
    context_object_name = "job"

    def get_queryset(self):
        queryset = super().get_queryset()
        if not (self.request.user.is_authenticated and self.request.user.is_superuser):
            queryset = queryset.exclude(moderation_status=Job.ModerationStatus.REMOVED)
        return queryset


@login_required
@require_POST
def apply_one_click(request, pk):
    job = get_object_or_404(Job, pk=pk)
    note = request.POST.get("note", "")
    application, created = Application.objects.get_or_create(job=job, applicant=request.user, defaults={"note": note})
    if not created and note:
        application.note = note
        application.save()
    return redirect("applications:my_applications")


def job_map_data(request):
    base_qs = Job.objects.all()
    if not (request.user.is_authenticated and request.user.is_superuser):
        base_qs = base_qs.exclude(moderation_status=Job.ModerationStatus.REMOVED)

    filterset = JobFilter(request.GET, queryset=base_qs)
    qs = filterset.qs

    # Optional map-specific filtering via query params
    lat_param = request.GET.get("user_lat")
    lon_param = request.GET.get("user_lon")
    max_dist_param = request.GET.get("max_distance")

    profile = _get_jobseeker_profile(request.user)

    user_lat = None
    user_lon = None
    distance_limit = None

    # Prefer explicit query params if provided
    try:
        if lat_param is not None and lon_param is not None:
            user_lat = float(lat_param)
            user_lon = float(lon_param)
    except (TypeError, ValueError):
        user_lat = None
        user_lon = None

    if max_dist_param:
        try:
            distance_limit = float(max_dist_param)
        except (TypeError, ValueError):
            distance_limit = None

    # Fallback to saved profile location / commute radius if not provided
    if (user_lat is None or user_lon is None) and profile and profile.latitude and profile.longitude:
        user_lat = float(profile.latitude)
        user_lon = float(profile.longitude)

    if distance_limit is None and profile and profile.commute_radius:
        distance_limit = float(profile.commute_radius)

    # Apply distance filter only if we have both a location and a distance
    if user_lat is not None and user_lon is not None and distance_limit:
        pks_within = []
        for job in qs:
            if job.latitude and job.longitude:
                d = calculate_distance(
                    user_lat,
                    user_lon,
                    float(job.latitude),
                    float(job.longitude),
                )
                if d is not None and d <= distance_limit:
                    pks_within.append(job.pk)
        if pks_within:
            qs = qs.filter(pk__in=pks_within)
        else:
            qs = qs.none()

    jobs = list(qs)

    user_location = None
    if user_lat is not None and user_lon is not None:
        user_location = {
            "latitude": float(user_lat),
            "longitude": float(user_lon),
        }

    results = []
    missing_count = 0

    for job in jobs:
        if not job.latitude or not job.longitude:
            missing_count += 1
            continue

        lat = float(job.latitude)
        lon = float(job.longitude)
        distance = None

        if user_location:
            distance = calculate_distance(
                user_location["latitude"],
                user_location["longitude"],
                lat,
                lon,
            )
            if distance is not None:
                distance = round(distance, 1)

        location_parts = [job.location_city, job.location_state, job.location_country]
        location = ", ".join([part for part in location_parts if part])

        salary_range = None
        if job.min_salary and job.max_salary:
            salary_range = f"${job.min_salary:,} - ${job.max_salary:,}"
        elif job.min_salary:
            salary_range = f"From ${job.min_salary:,}"
        elif job.max_salary:
            salary_range = f"Up to ${job.max_salary:,}"

        results.append(
            {
                "id": job.pk,
                "title": job.title,
                "company": job.company,
                "latitude": lat,
                "longitude": lon,
                "work_type": job.get_work_type_display(),
                "location": location,
                "salary_range": salary_range,
                "visa_sponsorship": job.visa_sponsorship,
                "detail_url": reverse("jobs:job_detail", args=[job.pk]),
                "distance_miles": distance,
            }
        )

    return JsonResponse(
        {
            "results": results,
            "missing_count": missing_count,
            "total_count": len(jobs),
            "user_location": user_location,
        }
    )

# ===== JOB POSTING FORMS AND VIEWS =====

class RecruiterRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure user is authenticated and is a recruiter"""
    
    def test_func(self):
        profile = _get_jobseeker_profile(self.request.user)
        return profile and profile.account_type == 'recruiter'
    
    def handle_no_permission(self):
        messages.error(self.request, "Only recruiters can access this page.")
        return redirect('jobs:job_list')


class JobCreateView(RecruiterRequiredMixin, CreateView):
    """View for recruiters to create new job postings"""
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    success_url = reverse_lazy('jobs:my_jobs')
    
    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        messages.success(self.request, f"Job posting '{form.instance.title}' has been created successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Post a New Job'
        context['submit_text'] = 'Post Job'
        context['is_edit'] = False
        return context


class JobUpdateView(RecruiterRequiredMixin, UpdateView):
    """View for recruiters to edit their job postings"""
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    
    def test_func(self):
        # Must be a recruiter AND the job owner
        if not super().test_func():
            return False
        job = self.get_object()
        return job.posted_by == self.request.user
    
    def get_success_url(self):
        return reverse('jobs:job_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"Job posting '{form.instance.title}' has been updated successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Job Posting'
        context['submit_text'] = 'Update Job'
        context['is_edit'] = True
        return context


class MyJobsListView(RecruiterRequiredMixin, ListView):
    """View for recruiters to see all their posted jobs"""
    model = Job
    template_name = 'jobs/my_jobs.html'
    context_object_name = 'jobs'
    paginate_by = 10
    
    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add statistics
        jobs = self.get_queryset()
        context['total_jobs'] = jobs.count()
        context['total_applications'] = Application.objects.filter(job__in=jobs).count()
        return context

# ===== Job Moderation (Admin) =====

@admin_required
def moderate_jobs(request):
    """Admin dashboard to review and moderate job posts."""
    status_filter = request.GET.get("status", "all")
    search_query = request.GET.get("q", "").strip()

    jobs = Job.objects.all().select_related("posted_by", "moderated_by").prefetch_related("skills")

    if status_filter != "all":
        jobs = jobs.filter(moderation_status=status_filter)

    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query)
            | Q(company__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    jobs = jobs.order_by("-created_at")
    paginator = Paginator(jobs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    status_counts = {
        "all": Job.objects.count(),
        "active": Job.objects.filter(moderation_status=Job.ModerationStatus.ACTIVE).count(),
        "pending": Job.objects.filter(moderation_status=Job.ModerationStatus.PENDING).count(),
        "flagged": Job.objects.filter(moderation_status=Job.ModerationStatus.FLAGGED).count(),
        "removed": Job.objects.filter(moderation_status=Job.ModerationStatus.REMOVED).count(),
    }

    context = {
        "page_obj": page_obj,
        "status_filter": status_filter,
        "search_query": search_query,
        "status_counts": status_counts,
        "status_choices": Job.ModerationStatus.choices,
    }
    return render(request, "jobs/moderate_jobs.html", context)


@admin_required
@require_POST
def moderate_job_action(request, job_id):
    """Handle moderation actions like approve/remove/flag."""
    job = get_object_or_404(Job, id=job_id)
    action = request.POST.get("action")
    reason = request.POST.get("reason", "").strip()

    if action == "approve":
        job.moderation_status = Job.ModerationStatus.ACTIVE
        job.moderation_reason = ""
        messages.success(request, f'"{job.title}" is now active.')
    elif action == "remove":
        job.moderation_status = Job.ModerationStatus.REMOVED
        job.moderation_reason = reason or "Removed by administrator"
        messages.success(request, f'"{job.title}" has been removed.')
    elif action == "flag":
        job.moderation_status = Job.ModerationStatus.FLAGGED
        job.moderation_reason = reason or "Flagged for review"
        messages.success(request, f'"{job.title}" has been flagged.')
    elif action == "pending":
        job.moderation_status = Job.ModerationStatus.PENDING
        job.moderation_reason = reason or "Pending review"
        messages.info(request, f'"{job.title}" set to pending review.')
    else:
        messages.error(request, "Invalid moderation action.")
        return redirect("jobs:moderate_jobs")

    job.moderated_by = request.user
    job.moderated_at = timezone.now()
    job.save()

    status_filter = request.POST.get("status_filter", "all")
    redirect_url = f"{reverse('jobs:moderate_jobs')}?status={status_filter}"
    return redirect(redirect_url)


@admin_required
def job_detail_moderation(request, job_id):
    """Detailed view of a job for moderation purposes."""
    job = get_object_or_404(Job, id=job_id)
    context = {
        "job": job,
        "applications_count": job.applications.count(),
    }
    return render(request, "jobs/job_detail_moderation.html", context)

