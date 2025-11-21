from django.db import models
from django.contrib.auth import get_user_model


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    class WorkType(models.TextChoices):
        ONSITE = "onsite", "On-site"
        REMOTE = "remote", "Remote"
        HYBRID = "hybrid", "Hybrid"

    class ModerationStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        PENDING = "pending", "Pending Review"
        FLAGGED = "flagged", "Flagged"
        REMOVED = "removed", "Removed"

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    skills = models.ManyToManyField(Skill, related_name="jobs", blank=True)

    location_city = models.CharField(max_length=100, blank=True)
    location_state = models.CharField(max_length=100, blank=True)
    location_country = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    min_salary = models.PositiveIntegerField(null=True, blank=True)
    max_salary = models.PositiveIntegerField(null=True, blank=True)
    work_type = models.CharField(max_length=10, choices=WorkType.choices, default=WorkType.ONSITE)
    visa_sponsorship = models.BooleanField(default=False)

    posted_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name="posted_jobs")
    created_at = models.DateTimeField(auto_now_add=True)

    moderation_status = models.CharField(
        max_length=20,
        choices=ModerationStatus.choices,
        default=ModerationStatus.ACTIVE,
        help_text="Moderation status to control visibility",
    )
    moderation_reason = models.TextField(
        blank=True,
        help_text="Optional reason explaining why moderation status was changed",
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderated_jobs",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} @ {self.company}"


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        REVIEW = "review", "Review"
        INTERVIEW = "interview", "Interview"
        OFFER = "offer", "Offer"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="applications")
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    
    # Kanban enhancements
    recruiter_notes = models.TextField(blank=True, help_text="Internal notes for recruiter use only")
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    flagged = models.BooleanField(default=False, help_text="Flag important candidates")
    position_in_stage = models.PositiveIntegerField(default=0, help_text="Order within status column")
    stage_changed_at = models.DateTimeField(null=True, blank=True, help_text="When status last changed")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("job", "applicant")
        ordering = ["position_in_stage", "-updated_at"]

    def __str__(self):
        return f"{self.applicant} -> {self.job} ({self.status})"
    
    def days_in_current_stage(self):
        """Calculate days spent in current status stage"""
        from django.utils import timezone
        if self.stage_changed_at:
            delta = timezone.now() - self.stage_changed_at
            return delta.days
        # If no stage_changed_at, use created_at
        delta = timezone.now() - self.created_at
        return delta.days
    
    def save(self, *args, **kwargs):
        """Track when status changes"""
        from django.utils import timezone
        if self.pk:  # Existing application
            old_app = Application.objects.filter(pk=self.pk).first()
            if old_app and old_app.status != self.status:
                self.stage_changed_at = timezone.now()
        else:  # New application
            self.stage_changed_at = timezone.now()
        super().save(*args, **kwargs)

# Create your models here.
