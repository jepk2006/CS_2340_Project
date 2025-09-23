from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView
from django_filters.views import FilterView
import django_filters

from .models import Job, Skill, Application
from django.views.decorators.http import require_POST


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
