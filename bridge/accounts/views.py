from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect, render
from django.forms import ModelForm, Form, CharField, EmailField, ChoiceField, PasswordInput
from django.core.paginator import Paginator
from django.db.models import Q

from .models import JobSeekerProfile
from jobs.models import Skill
from jobs.decorators import recruiter_required


class JobSeekerProfileForm(ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            "headline",
            "bio",
            "education",
            "experience",
            "portfolio_url",
            "linkedin_url",
            "github_url",
            "location_city",
            "location_state",
            "location_country",
            "latitude",
            "longitude",
            "commute_radius",
            "skills",
            "visibility",
            "show_email",
            "account_type",
        ]


@login_required
def profile_edit(request):
    profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = JobSeekerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("accounts:profile_edit")
    else:
        form = JobSeekerProfileForm(instance=profile)
    return render(request, "accounts/profile_edit.html", {"form": form})


class SignupForm(Form):
    username = CharField(max_length=150)
    email = EmailField(required=False)
    password = CharField(widget=PasswordInput)
    account_type = ChoiceField(choices=JobSeekerProfile.AccountType.choices)


def signup(request):
    if request.user.is_authenticated:
        return redirect("jobs:job_list")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            User = get_user_model()

            if User.objects.filter(username=form.cleaned_data["username"]).exists():
                form.add_error("username", "This username is already taken.")
                return render(request, "accounts/signup.html", {"form": form})
            
            email_value = (form.cleaned_data.get("email") or "").strip()
            if email_value and User.objects.filter(email__iexact=email_value).exists():
                form.add_error("email", "This email is already taken.")
                return render(request, "accounts/signup.html", {"form": form})
            
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data.get("email", ""),
                password=form.cleaned_data["password"],
            )
            profile, _ = JobSeekerProfile.objects.get_or_create(user=user)
            profile.account_type = form.cleaned_data["account_type"]
            profile.save()
            if profile.account_type == JobSeekerProfile.AccountType.RECRUITER:
                user.is_staff = True
                user.save()
            login(request, user)
            return redirect("jobs:job_list")
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})

@recruiter_required
def recruiter_talent_search(request):
    query = request.GET.get("q", "").strip()
    skill_ids = request.GET.getlist("skills")
    location_city = request.GET.get("city", "").strip()
    location_state = request.GET.get("state", "").strip()
    location_country = request.GET.get("country", "").strip()

    profiles = JobSeekerProfile.objects.all()
    # Recruiters see public and recruiters-only profiles
    profiles = profiles.filter(visibility__in=[JobSeekerProfile.Visibility.PUBLIC, JobSeekerProfile.Visibility.RECRUITERS])

    if query:
        profiles = profiles.filter(
            Q(user__username__icontains=query)
            | Q(headline__icontains=query)
            | Q(bio__icontains=query)
            | Q(education__icontains=query)
            | Q(experience__icontains=query)
            | Q(portfolio_url__icontains=query)
            | Q(linkedin_url__icontains=query)
            | Q(github_url__icontains=query)
        )

    if skill_ids:
        profiles = profiles.filter(skills__in=skill_ids).distinct()

    if location_city:
        profiles = profiles.filter(location_city__icontains=location_city)
    if location_state:
        profiles = profiles.filter(location_state__icontains=location_state)
    if location_country:
        profiles = profiles.filter(location_country__icontains=location_country)

    # Only show candidates with at least one skill filled out
    profiles = profiles.filter(skills__isnull=False).select_related("user").prefetch_related("skills").distinct().order_by("-updated_at")

    paginator = Paginator(profiles, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    all_skills = Skill.objects.order_by("name")

    context = {
        "page_obj": page_obj,
        "skills": all_skills,
        "selected_skills": [int(s) for s in skill_ids if s.isdigit()],
        "query": query,
        "city": location_city,
        "state": location_state,
        "country": location_country,
    }
    return render(request, "accounts/recruiter_search.html", context)

# Create your views here.
