from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from .models import JobSeekerProfile, SavedSearch, TalentMessage


@receiver(post_save, sender=get_user_model())
def create_profile_for_new_user(sender, instance, created, **kwargs):
    if created:
        JobSeekerProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=JobSeekerProfile)
def check_saved_searches_on_profile_update(sender, instance, created, **kwargs):
    """
    Automatically check if a job seeker profile matches any recruiter's saved searches
    and send notifications when matches are found.
    """
    # Only check for job seekers who are publicly visible or visible to recruiters
    if instance.account_type != JobSeekerProfile.AccountType.JOB_SEEKER:
        return
    
    if instance.visibility not in [JobSeekerProfile.Visibility.PUBLIC, JobSeekerProfile.Visibility.RECRUITERS]:
        return
    
    # Only check if the profile has skills
    if not instance.skills.exists():
        return
    
    # Get all active saved searches
    active_searches = SavedSearch.objects.filter(is_active=True).prefetch_related('skills')
    
    for saved_search in active_searches:
        # Check if this profile matches the saved search criteria
        if profile_matches_search(instance, saved_search):
            # Determine message type and content
            if created:
                message_type = TalentMessage.MessageType.NEW_MATCH
                title = f'New candidate matches "{saved_search.name}"'
                content = f'New candidate {instance.user.username} matches your saved search. '
            else:
                message_type = TalentMessage.MessageType.PROFILE_UPDATE
                title = f'Updated candidate matches "{saved_search.name}"'
                content = f'Candidate {instance.user.username} has updated their profile and matches your saved search. '
            
            if instance.headline:
                content += f'Headline: {instance.headline}'
            
            # Create or update the message
            TalentMessage.objects.get_or_create(
                recruiter=saved_search.recruiter,
                saved_search=saved_search,
                profile=instance,
                message_type=message_type,
                defaults={
                    'title': title,
                    'content': content
                }
            )


@receiver(m2m_changed, sender=JobSeekerProfile.skills.through)
def check_saved_searches_on_skills_change(sender, instance, action, **kwargs):
    """
    Check saved searches when a job seeker's skills are changed.
    This handles the case where skills are added/removed after profile creation.
    """
    # Only act on post_add and post_remove actions
    if action not in ['post_add', 'post_remove']:
        return
    
    # Only check for job seekers who are publicly visible or visible to recruiters
    if instance.account_type != JobSeekerProfile.AccountType.JOB_SEEKER:
        return
    
    if instance.visibility not in [JobSeekerProfile.Visibility.PUBLIC, JobSeekerProfile.Visibility.RECRUITERS]:
        return
    
    # Only check if the profile has skills after the change
    if not instance.skills.exists():
        return
    
    # Get all active saved searches
    active_searches = SavedSearch.objects.filter(is_active=True).prefetch_related('skills')
    
    for saved_search in active_searches:
        # Check if this profile matches the saved search criteria
        if profile_matches_search(instance, saved_search):
            # Create notification for skills update
            TalentMessage.objects.get_or_create(
                recruiter=saved_search.recruiter,
                saved_search=saved_search,
                profile=instance,
                message_type=TalentMessage.MessageType.PROFILE_UPDATE,
                defaults={
                    'title': f'Candidate with your desired skills: "{saved_search.name}"',
                    'content': f'Candidate {instance.user.username} now has skills matching your saved search. '
                              f'{"Headline: " + instance.headline if instance.headline else ""}'
                }
            )


def profile_matches_search(profile, saved_search):
    """
    Helper function to check if a profile matches a saved search criteria.
    Returns True if the profile matches all the search criteria.
    """
    from django.db.models import Q
    
    # Check query match (if query is specified)
    if saved_search.query:
        query_match = (
            saved_search.query.lower() in profile.user.username.lower() or
            saved_search.query.lower() in profile.headline.lower() or
            saved_search.query.lower() in profile.bio.lower() or
            saved_search.query.lower() in profile.education.lower() or
            saved_search.query.lower() in profile.experience.lower() or
            saved_search.query.lower() in profile.portfolio_url.lower() or
            saved_search.query.lower() in profile.linkedin_url.lower() or
            saved_search.query.lower() in profile.github_url.lower()
        )
        if not query_match:
            return False
    
    # Check skills match (if skills are specified)
    if saved_search.skills.exists():
        profile_skill_ids = set(profile.skills.values_list('id', flat=True))
        search_skill_ids = set(saved_search.skills.values_list('id', flat=True))
        # Profile must have at least one skill that matches
        if not profile_skill_ids.intersection(search_skill_ids):
            return False
    
    # Check location matches (if location is specified)
    if saved_search.location_city:
        if saved_search.location_city.lower() not in profile.location_city.lower():
            return False
    
    if saved_search.location_state:
        if saved_search.location_state.lower() not in profile.location_state.lower():
            return False
    
    if saved_search.location_country:
        if saved_search.location_country.lower() not in profile.location_country.lower():
            return False
    
    return True


