from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect, render, get_object_or_404
from django.forms import ModelForm, Form, CharField, EmailField, ChoiceField, PasswordInput
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
import csv
from datetime import datetime

from .models import JobSeekerProfile, SavedSearch, TalentMessage, Conversation, Message
from .forms import SavedSearchForm, JobSeekerProfileForm, MessageForm
from jobs.models import Skill, Job, Application
from jobs.decorators import recruiter_required, admin_required




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
    saved_search_id = request.GET.get("saved_search")

    # If loading a saved search, populate the form with its criteria
    saved_search = None
    if saved_search_id:
        try:
            saved_search = SavedSearch.objects.get(id=saved_search_id, recruiter=request.user)
            query = saved_search.query
            skill_ids = list(saved_search.skills.values_list('id', flat=True))
            location_city = saved_search.location_city
            location_state = saved_search.location_state
            location_country = saved_search.location_country
        except SavedSearch.DoesNotExist:
            pass

    profiles = JobSeekerProfile.objects.all()
    # Recruiters see public and recruiters-only profiles
    profiles = profiles.filter(
        visibility__in=[JobSeekerProfile.Visibility.PUBLIC, JobSeekerProfile.Visibility.RECRUITERS],
        account_type=JobSeekerProfile.AccountType.JOB_SEEKER
    )

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
    user_saved_searches = SavedSearch.objects.filter(recruiter=request.user, is_active=True)
    
    # Add match counts to saved searches
    for search in user_saved_searches:
        search.match_count = search.get_matching_profiles().count()

    context = {
        "page_obj": page_obj,
        "skills": all_skills,
        "selected_skills": [int(s) if isinstance(s, str) else s for s in skill_ids if str(s).isdigit()],
        "query": query,
        "city": location_city,
        "state": location_state,
        "country": location_country,
        "saved_searches": user_saved_searches,
        "current_saved_search": saved_search,
        "has_search_criteria": bool(query or skill_ids or location_city or location_state or location_country),
    }
    return render(request, "accounts/recruiter_search.html", context)


@recruiter_required
@require_POST
def save_search(request):
    """Save current search criteria as a saved search"""
    name = request.POST.get('name', '').strip()
    query = request.POST.get('query', '').strip()
    skill_ids = request.POST.getlist('skills')
    location_city = request.POST.get('city', '').strip()
    location_state = request.POST.get('state', '').strip()
    location_country = request.POST.get('country', '').strip()
    
    if not name:
        return JsonResponse({'success': False, 'error': 'Search name is required'})
    
    # Check if name already exists for this user
    if SavedSearch.objects.filter(recruiter=request.user, name=name).exists():
        return JsonResponse({'success': False, 'error': 'A search with this name already exists'})
    
    # Create the saved search
    saved_search = SavedSearch.objects.create(
        recruiter=request.user,
        name=name,
        query=query,
        location_city=location_city,
        location_state=location_state,
        location_country=location_country
    )
    
    # Add skills
    if skill_ids:
        skills = Skill.objects.filter(id__in=skill_ids)
        saved_search.skills.set(skills)
    
    return JsonResponse({
        'success': True, 
        'message': f'Search "{name}" saved successfully!',
        'saved_search_id': saved_search.id
    })


@recruiter_required
def saved_searches_list(request):
    """List all saved searches for the current recruiter"""
    saved_searches = SavedSearch.objects.filter(recruiter=request.user).prefetch_related('skills')
    
    # Add match counts for each saved search
    for search in saved_searches:
        search.match_count = search.get_matching_profiles().count()
        search.new_matches_count = search.get_new_matches_since_last_check().count()
    
    context = {
        'saved_searches': saved_searches,
    }
    return render(request, 'accounts/saved_searches.html', context)


@recruiter_required
def saved_search_detail(request, search_id):
    """View details and matches for a specific saved search"""
    saved_search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user)
    
    # Get matching profiles
    profiles = saved_search.get_matching_profiles()
    
    paginator = Paginator(profiles, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'saved_search': saved_search,
        'page_obj': page_obj,
        'total_matches': profiles.count(),
    }
    return render(request, 'accounts/saved_search_detail.html', context)


@recruiter_required
def edit_saved_search(request, search_id):
    """Edit a saved search"""
    saved_search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user)
    
    if request.method == 'POST':
        form = SavedSearchForm(request.POST, instance=saved_search)
        if form.is_valid():
            form.save()
            messages.success(request, f'Saved search "{saved_search.name}" updated successfully!')
            return redirect('accounts:saved_searches')
    else:
        form = SavedSearchForm(instance=saved_search)
    
    context = {
        'form': form,
        'saved_search': saved_search,
        'is_edit': True,
    }
    return render(request, 'accounts/saved_search_form.html', context)


@recruiter_required
@require_POST
def delete_saved_search(request, search_id):
    """Delete a saved search"""
    saved_search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user)
    search_name = saved_search.name
    saved_search.delete()
    messages.success(request, f'Saved search "{search_name}" deleted successfully!')
    return redirect('accounts:saved_searches')


@recruiter_required
@require_POST
def toggle_saved_search(request, search_id):
    """Toggle active status of a saved search"""
    saved_search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user)
    saved_search.is_active = not saved_search.is_active
    saved_search.save()
    
    status = "activated" if saved_search.is_active else "deactivated"
    messages.success(request, f'Saved search "{saved_search.name}" {status}!')
    return redirect('accounts:saved_searches')


@recruiter_required
def talent_messages(request):
    """View for recruiters to see messages about new talent matches"""
    # Get all messages for the current recruiter
    messages_list = TalentMessage.objects.filter(recruiter=request.user).select_related('saved_search', 'profile__user')
    
    # Mark messages as read when viewed
    unread_messages = messages_list.filter(is_read=False)
    unread_messages.update(is_read=True)
    
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'unread_count': unread_messages.count(),
    }
    return render(request, 'accounts/talent_messages.html', context)


@recruiter_required
def check_new_matches(request):
    """Check for new matches across all active saved searches and create messages"""
    saved_searches = SavedSearch.objects.filter(recruiter=request.user, is_active=True)
    new_messages_count = 0
    
    for saved_search in saved_searches:
        new_matches = saved_search.get_new_matches_since_last_check()
        
        for profile in new_matches:
            # Create a message for each new match
            message, created = TalentMessage.objects.get_or_create(
                recruiter=request.user,
                saved_search=saved_search,
                profile=profile,
                message_type=TalentMessage.MessageType.NEW_MATCH,
                defaults={
                    'title': f'New match for "{saved_search.name}"',
                    'content': f'{profile.user.username} matches your saved search criteria. '
                              f'{"Headline: " + profile.headline if profile.headline else ""}'
                }
            )
            if created:
                new_messages_count += 1
        
        # Mark this search as checked
        if new_matches.exists():
            saved_search.mark_checked()
    
    return JsonResponse({
        'success': True,
        'new_messages': new_messages_count,
        'message': f'Found {new_messages_count} new matches!'
    })


@recruiter_required
def get_unread_messages_count(request):
    """Get count of unread messages for the current recruiter"""
    count = TalentMessage.objects.filter(recruiter=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})


# Messaging Views

@login_required
def conversations_list(request):
    """List all conversations for the current user"""
    # Check if user has a profile and is a recruiter
    is_recruiter = (
        hasattr(request.user, 'jobseeker_profile') and 
        request.user.jobseeker_profile.account_type == JobSeekerProfile.AccountType.RECRUITER
    )
    
    if is_recruiter:
        # Recruiters see conversations they started
        conversations = Conversation.objects.filter(recruiter=request.user).select_related('candidate', 'candidate__jobseeker_profile').prefetch_related('messages')
    else:
        # Candidates see conversations where they are the candidate
        conversations = Conversation.objects.filter(candidate=request.user).select_related('recruiter', 'recruiter__jobseeker_profile').prefetch_related('messages')
    
    # Add unread counts for each conversation
    for conversation in conversations:
        conversation.unread_count = conversation.get_unread_count_for_user(request.user)
        conversation.latest_message = conversation.get_latest_message()
    
    context = {
        'conversations': conversations,
        'is_recruiter': is_recruiter,
    }
    return render(request, 'accounts/conversations_list.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """View a specific conversation and its messages"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is part of this conversation
    if request.user not in [conversation.recruiter, conversation.candidate]:
        messages.error(request, "You don't have permission to view this conversation.")
        return redirect('accounts:conversations_list')
    
    # Get all messages in this conversation
    message_list = conversation.messages.all()
    
    # Mark messages as read when viewed
    unread_messages = message_list.filter(is_read=False).exclude(sender=request.user)
    unread_messages.update(is_read=True)
    
    # Create form for new messages
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            return redirect('accounts:conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    # Determine the other participant
    other_user = conversation.candidate if request.user == conversation.recruiter else conversation.recruiter
    
    # Check if user has a profile and is a recruiter
    is_recruiter = (
        hasattr(request.user, 'jobseeker_profile') and 
        request.user.jobseeker_profile.account_type == JobSeekerProfile.AccountType.RECRUITER
    )
    
    context = {
        'conversation': conversation,
        'message_list': message_list,
        'form': form,
        'other_user': other_user,
        'is_recruiter': is_recruiter,
    }
    return render(request, 'accounts/conversation_detail.html', context)


@recruiter_required
def start_conversation(request, candidate_id):
    """Start a new conversation with a candidate (recruiters only)"""
    candidate = get_object_or_404(get_user_model(), id=candidate_id)
    
    # Check if candidate is actually a job seeker
    if not hasattr(candidate, 'jobseeker_profile') or candidate.jobseeker_profile.account_type != JobSeekerProfile.AccountType.JOB_SEEKER:
        messages.error(request, "You can only message job seekers.")
        return redirect('accounts:recruiter_talent_search')
    
    # Get or create conversation
    conversation, created = Conversation.objects.get_or_create(
        recruiter=request.user,
        candidate=candidate
    )
    
    if created:
        messages.success(request, f"Started conversation with {candidate.username}")
    else:
        messages.info(request, f"Resumed conversation with {candidate.username}")
    
    return redirect('accounts:conversation_detail', conversation_id=conversation.id)


@login_required
def send_message(request, conversation_id):
    """Send a message in a conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is part of this conversation
    if request.user not in [conversation.recruiter, conversation.candidate]:
        messages.error(request, "You don't have permission to send messages in this conversation.")
        return redirect('accounts:conversations_list')
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            messages.success(request, "Message sent successfully!")
        else:
            messages.error(request, "Failed to send message. Please try again.")
    
    return redirect('accounts:conversation_detail', conversation_id=conversation.id)


# Admin Data Export Views

@admin_required
def admin_export_dashboard(request):
    """Dashboard for administrators to select and export data"""
    User = get_user_model()
    
    # Get counts for display
    stats = {
        'users': User.objects.count(),
        'profiles': JobSeekerProfile.objects.count(),
        'jobs': Job.objects.count(),
        'applications': Application.objects.count(),
        'skills': Skill.objects.count(),
        'conversations': Conversation.objects.count(),
        'messages': Message.objects.count(),
        'saved_searches': SavedSearch.objects.count(),
    }
    
    context = {
        'stats': stats,
    }
    return render(request, 'accounts/admin_export.html', context)


@admin_required
def export_users(request):
    """Export all users to CSV"""
    User = get_user_model()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Is Staff', 'Is Superuser', 'Is Active', 'Date Joined', 'Last Login'])
    
    for user in User.objects.all():
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            user.is_staff,
            user.is_superuser,
            user.is_active,
            user.date_joined,
            user.last_login,
        ])
    
    return response


@admin_required
def export_profiles(request):
    """Export all job seeker profiles to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="profiles_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'User ID', 'Username', 'Account Type', 'Headline', 'Bio', 
        'Education', 'Experience', 'Location City', 'Location State', 
        'Location Country', 'Latitude', 'Longitude', 'Commute Radius',
        'Portfolio URL', 'LinkedIn URL', 'GitHub URL', 
        'Visibility', 'Show Email', 'Skills', 'Updated At'
    ])
    
    for profile in JobSeekerProfile.objects.select_related('user').prefetch_related('skills').all():
        skills_list = ', '.join([skill.name for skill in profile.skills.all()])
        writer.writerow([
            profile.user.id,
            profile.user.username,
            profile.account_type,
            profile.headline,
            profile.bio,
            profile.education,
            profile.experience,
            profile.location_city,
            profile.location_state,
            profile.location_country,
            profile.latitude,
            profile.longitude,
            profile.commute_radius,
            profile.portfolio_url,
            profile.linkedin_url,
            profile.github_url,
            profile.visibility,
            profile.show_email,
            skills_list,
            profile.updated_at,
        ])
    
    return response


@admin_required
def export_jobs(request):
    """Export all jobs to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="jobs_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'Company', 'Description', 'Location City', 
        'Location State', 'Location Country', 'Latitude', 'Longitude',
        'Min Salary', 'Max Salary', 'Work Type', 'Visa Sponsorship',
        'Posted By (Username)', 'Skills', 'Created At'
    ])
    
    for job in Job.objects.select_related('posted_by').prefetch_related('skills').all():
        skills_list = ', '.join([skill.name for skill in job.skills.all()])
        posted_by = job.posted_by.username if job.posted_by else 'N/A'
        writer.writerow([
            job.id,
            job.title,
            job.company,
            job.description,
            job.location_city,
            job.location_state,
            job.location_country,
            job.latitude,
            job.longitude,
            job.min_salary,
            job.max_salary,
            job.work_type,
            job.visa_sponsorship,
            posted_by,
            skills_list,
            job.created_at,
        ])
    
    return response


@admin_required
def export_applications(request):
    """Export all applications to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="applications_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Job Title', 'Job Company', 'Applicant Username', 
        'Applicant Email', 'Status', 'Priority', 'Flagged', 
        'Applicant Note', 'Recruiter Notes', 'Position in Stage',
        'Days in Current Stage', 'Stage Changed At', 'Created At', 'Updated At'
    ])
    
    for app in Application.objects.select_related('job', 'applicant').all():
        writer.writerow([
            app.id,
            app.job.title,
            app.job.company,
            app.applicant.username,
            app.applicant.email,
            app.status,
            app.priority,
            app.flagged,
            app.note,
            app.recruiter_notes,
            app.position_in_stage,
            app.days_in_current_stage(),
            app.stage_changed_at,
            app.created_at,
            app.updated_at,
        ])
    
    return response


@admin_required
def export_skills(request):
    """Export all skills to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="skills_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Skill Name', 'Number of Jobs', 'Number of Profiles'])
    
    for skill in Skill.objects.all():
        jobs_count = skill.jobs.count()
        profiles_count = skill.profiles.count()
        writer.writerow([
            skill.id,
            skill.name,
            jobs_count,
            profiles_count,
        ])
    
    return response


@admin_required
def export_conversations(request):
    """Export all conversations to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="conversations_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Recruiter Username', 'Candidate Username', 
        'Message Count', 'Created At', 'Updated At'
    ])
    
    for conversation in Conversation.objects.select_related('recruiter', 'candidate').all():
        message_count = conversation.messages.count()
        writer.writerow([
            conversation.id,
            conversation.recruiter.username,
            conversation.candidate.username,
            message_count,
            conversation.created_at,
            conversation.updated_at,
        ])
    
    return response


@admin_required
def export_messages(request):
    """Export all messages to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="messages_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Conversation ID', 'Sender Username', 'Content', 
        'Is Read', 'Created At'
    ])
    
    for message in Message.objects.select_related('conversation', 'sender').all():
        writer.writerow([
            message.id,
            message.conversation.id,
            message.sender.username,
            message.content,
            message.is_read,
            message.created_at,
        ])
    
    return response


@admin_required
def export_saved_searches(request):
    """Export all saved searches to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="saved_searches_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Recruiter Username', 'Search Name', 'Query', 
        'Skills', 'Location City', 'Location State', 'Location Country',
        'Is Active', 'Last Check', 'Created At', 'Updated At'
    ])
    
    for search in SavedSearch.objects.select_related('recruiter').prefetch_related('skills').all():
        skills_list = ', '.join([skill.name for skill in search.skills.all()])
        writer.writerow([
            search.id,
            search.recruiter.username,
            search.name,
            search.query,
            skills_list,
            search.location_city,
            search.location_state,
            search.location_country,
            search.is_active,
            search.last_check,
            search.created_at,
            search.updated_at,
        ])
    
    return response


# Create your views here.
