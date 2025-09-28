from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect, render
from django.forms import ModelForm, Form, CharField, EmailField, ChoiceField, PasswordInput

from .models import JobSeekerProfile


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

# Create your views here.
