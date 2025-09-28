from django.db import models
from django.contrib.auth import get_user_model


class JobSeekerProfile(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        RECRUITERS = "recruiters", "Recruiters Only"
        PRIVATE = "private", "Private"

    class AccountType(models.TextChoices):
        JOB_SEEKER = "job_seeker", "Job Seeker"
        RECRUITER = "recruiter", "Recruiter"

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="jobseeker_profile")
    headline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)

    education = models.TextField(blank=True)
    experience = models.TextField(blank=True)

    # Links
    portfolio_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)

    # Location
    location_city = models.CharField(max_length=100, blank=True)
    location_state = models.CharField(max_length=100, blank=True)
    location_country = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    commute_radius = models.PositiveIntegerField(null=True, blank=True, help_text="Preferred commute radius in miles")

    # Skills (referencing jobs.Skill by app label to avoid circular import)
    skills = models.ManyToManyField("jobs.Skill", blank=True, related_name="profiles")

    # Privacy
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC)
    show_email = models.BooleanField(default=False)
    account_type = models.CharField(max_length=20, choices=AccountType.choices, default=AccountType.JOB_SEEKER)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile({self.user.username})"

# Create your models here.
