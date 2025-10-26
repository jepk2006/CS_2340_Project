from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from jobs.models import Skill, Job


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

    def get_recommended_jobs(self):
        # Get the skills associated with the job seeker's profile
        seeker_skills = self.skills.all()

        # If the job seeker has no skills, return an empty queryset
        if not seeker_skills:
            return Job.objects.none()

        # Get all jobs that have at least one matching skill
        recommended_jobs = Job.objects.filter(skills__in=seeker_skills).distinct()

        return recommended_jobs


class SavedSearch(models.Model):
    """Model to store recruiter's saved talent searches"""
    recruiter = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="saved_searches")
    name = models.CharField(max_length=200, help_text="Name for this saved search")
    
    # Search criteria fields
    query = models.TextField(blank=True, help_text="Keywords search")
    skills = models.ManyToManyField(Skill, blank=True, related_name="saved_searches")
    location_city = models.CharField(max_length=100, blank=True)
    location_state = models.CharField(max_length=100, blank=True)
    location_country = models.CharField(max_length=100, blank=True)
    
    # Notification settings
    last_check = models.DateTimeField(null=True, blank=True, help_text="Last time matches were checked")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Whether to check for new matches")
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['recruiter', 'name']
    
    def __str__(self):
        return f"{self.recruiter.username} - {self.name}"
    
    def get_matching_profiles(self):
        """Get profiles that match this saved search criteria"""
        from django.db.models import Q
        
        profiles = JobSeekerProfile.objects.filter(
            visibility__in=[JobSeekerProfile.Visibility.PUBLIC, JobSeekerProfile.Visibility.RECRUITERS],
            account_type=JobSeekerProfile.AccountType.JOB_SEEKER
        )
        
        # Apply query filter
        if self.query:
            profiles = profiles.filter(
                Q(user__username__icontains=self.query)
                | Q(headline__icontains=self.query)
                | Q(bio__icontains=self.query)
                | Q(education__icontains=self.query)
                | Q(experience__icontains=self.query)
                | Q(portfolio_url__icontains=self.query)
                | Q(linkedin_url__icontains=self.query)
                | Q(github_url__icontains=self.query)
            )
        
        # Apply skills filter
        if self.skills.exists():
            profiles = profiles.filter(skills__in=self.skills.all()).distinct()
        
        # Apply location filters
        if self.location_city:
            profiles = profiles.filter(location_city__icontains=self.location_city)
        if self.location_state:
            profiles = profiles.filter(location_state__icontains=self.location_state)
        if self.location_country:
            profiles = profiles.filter(location_country__icontains=self.location_country)
        
        # Only show candidates with at least one skill
        profiles = profiles.filter(skills__isnull=False).select_related("user").prefetch_related("skills").distinct()
        
        return profiles
    
    def get_new_matches_since_last_check(self):
        """Get profiles that match and have been updated since last check"""
        profiles = self.get_matching_profiles()
        
        if self.last_check:
            profiles = profiles.filter(updated_at__gt=self.last_check)
        
        return profiles
    
    def mark_checked(self):
        """Mark that matches have been checked for this search"""
        self.last_check = timezone.now()
        self.save(update_fields=['last_check'])


class TalentMessage(models.Model):
    """Model for in-app messages about new talent matches"""
    class MessageType(models.TextChoices):
        NEW_MATCH = "new_match", "New Match"
        PROFILE_UPDATE = "profile_update", "Profile Update"
    
    recruiter = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="talent_messages")
    saved_search = models.ForeignKey(SavedSearch, on_delete=models.CASCADE, related_name="messages")
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.NEW_MATCH)
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['saved_search', 'profile', 'message_type']
    
    def __str__(self):
        return f"{self.title} - {self.recruiter.username}"

class Conversation(models.Model):
    """Model for conversations between recruiters and candidates"""
    recruiter = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="recruiter_conversations")
    candidate = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="candidate_conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['recruiter', 'candidate']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation: {self.recruiter.username} <-> {self.candidate.username}"
    
    def get_latest_message(self):
        """Get the most recent message in this conversation"""
        return self.messages.first()
    
    def get_unread_count_for_user(self, user):
        """Get count of unread messages for a specific user (messages sent TO the user that are unread)"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    """Model for individual messages in conversations"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username}: {self.content[:50]}..."
    
    def mark_as_read(self):
        """Mark this message as read"""
        self.is_read = True
        self.save(update_fields=['is_read'])


# Create your models here.
