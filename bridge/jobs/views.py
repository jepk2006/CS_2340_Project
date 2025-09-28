from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView
from django_filters.views import FilterView
import django_filters
import math

from .models import Job, Skill, Application
from django.views.decorators.http import require_POST


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
        
        # Filter by commute radius if user is authenticated and has a profile with commute radius
        if self.request.user.is_authenticated:
            try:
                profile = self.request.user.jobseeker_profile
                if profile.commute_radius and profile.latitude and profile.longitude:
                    # Filter jobs within the commute radius
                    jobs_within_radius = []
                    for job in queryset:
                        if job.latitude and job.longitude:
                            distance = calculate_distance(
                                float(profile.latitude),
                                float(profile.longitude),
                                float(job.latitude),
                                float(job.longitude)
                            )
                            if distance is not None and distance <= profile.commute_radius:
                                jobs_within_radius.append(job.pk)
                    
                    # Filter the queryset to only include jobs within radius
                    queryset = queryset.filter(pk__in=jobs_within_radius)
            except:
                # If no profile exists, continue with all jobs
                pass
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add distance information for each job if user has location set
        if self.request.user.is_authenticated:
            try:
                profile = self.request.user.jobseeker_profile
                if profile.latitude and profile.longitude:
                    job_distances = {}
                    for job in context['jobs']:
                        if job.latitude and job.longitude:
                            distance = calculate_distance(
                                float(profile.latitude),
                                float(profile.longitude),
                                float(job.latitude),
                                float(job.longitude)
                            )
                            if distance is not None:
                                job_distances[job.pk] = round(distance, 1)
                    context['job_distances'] = job_distances
            except:
                pass
        
        return context


class JobDetailView(DetailView):
    model = Job
    template_name = "jobs/job_detail.html"
    context_object_name = "job"


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

# Create your views here.
