from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
import json

from .models import Application, Job
from accounts.models import JobSeekerProfile
from .forms import (
    ApplicationStatusForm, 
    ApplicationNotesForm, 
    ApplicationPriorityForm,
    ApplicationFilterForm
)


@login_required
def my_applications(request):
    applications = (
        Application.objects.filter(applicant=request.user)
        .select_related("job")
        .order_by("-updated_at")
    )
    grouped = {key: [] for key, _ in Application.Status.choices}
    for app in applications:
        grouped[app.status].append(app)
    status_groups = [
        {"key": key, "label": label, "apps": grouped.get(key, [])}
        for key, label in Application.Status.choices
    ]

    recommended_jobs = []
    if hasattr(request.user, 'jobseeker_profile'):
        recommended_jobs = request.user.jobseeker_profile.get_recommended_jobs()[:5] # Limit to 5 recommended jobs

    return render(
        request,
        "applications/my_applications.html",
        {"status_groups": status_groups, "recommended_jobs": recommended_jobs},
    )


@login_required
def recruiter_applications(request):
    """Enhanced Kanban-style view for recruiters to manage applicants"""
    
    # Handle status updates via POST
    if request.method == "POST":
        application_id = request.POST.get("application_id")
        new_status = request.POST.get("status")
        if application_id and new_status:
            application = get_object_or_404(Application, pk=application_id, job__posted_by=request.user)
            old_status = application.status
            application.status = new_status
            application.save()
            messages.success(request, f"Moved applicant to {application.get_status_display()}")
            return redirect(request.path + '?' + request.GET.urlencode())

    # Initialize filter form
    filter_form = ApplicationFilterForm(request.GET or None, user=request.user)
    
    # Base queryset - all applications for jobs posted by this recruiter
    qs = Application.objects.filter(
        job__posted_by=request.user
    ).select_related(
        "job", 
        "applicant", 
        "applicant__jobseeker_profile"
    ).prefetch_related(
        "applicant__jobseeker_profile__skills"
    )

    # Apply filters from form
    if filter_form.is_valid():
        # Filter by job
        if filter_form.cleaned_data.get('job'):
            qs = qs.filter(job=filter_form.cleaned_data['job'])
        
        # Filter by status
        if filter_form.cleaned_data.get('status'):
            qs = qs.filter(status=filter_form.cleaned_data['status'])
        
        # Filter by priority
        if filter_form.cleaned_data.get('priority'):
            qs = qs.filter(priority=filter_form.cleaned_data['priority'])
        
        # Filter flagged only
        if filter_form.cleaned_data.get('flagged_only'):
            qs = qs.filter(flagged=True)
        
        # Search by name or email
        search_query = filter_form.cleaned_data.get('search')
        if search_query:
            qs = qs.filter(
                Q(applicant__username__icontains=search_query) |
                Q(applicant__email__icontains=search_query) |
                Q(applicant__first_name__icontains=search_query) |
                Q(applicant__last_name__icontains=search_query)
            )

    # Group by job, then by status for Kanban layout
    jobs_map = {}
    for app in qs:
        if app.job not in jobs_map:
            jobs_map[app.job] = {key: [] for key, _ in Application.Status.choices}
        jobs_map[app.job][app.status].append(app)

    # Format data for template
    grouped = []
    for job, apps_by_status in jobs_map.items():
        status_groups = []
        for key, label in Application.Status.choices:
            apps_in_status = apps_by_status.get(key, [])
            status_groups.append({
                "key": key,
                "label": label,
                "apps": apps_in_status,
                "count": len(apps_in_status)
            })
        
        grouped.append({
            "job": job,
            "status_groups": status_groups,
            "total_applicants": sum(len(apps) for apps in apps_by_status.values())
        })

    # Sort jobs by company and title
    grouped.sort(key=lambda x: (x['job'].company, x['job'].title))

    # Statistics for dashboard
    total_applications = qs.count()
    flagged_count = qs.filter(flagged=True).count()
    high_priority_count = qs.filter(priority=Application.Priority.HIGH).count()

    context = {
        "grouped": grouped,
        "statuses": Application.Status.choices,
        "priorities": Application.Priority.choices,
        "filter_form": filter_form,
        "total_applications": total_applications,
        "flagged_count": flagged_count,
        "high_priority_count": high_priority_count,
    }
    
    return render(request, "applications/recruiter_applications.html", context)


@login_required
@require_POST
def update_application_status(request):
    """AJAX endpoint for updating application status (kept for compatibility)"""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        new_status = data.get('status')
        
        if not app_id or not new_status:
            return JsonResponse({'error': 'Missing application_id or status'}, status=400)
        
        # Validate status
        valid_statuses = [choice[0] for choice in Application.Status.choices]
        if new_status not in valid_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        # Get application and check permissions
        app = get_object_or_404(Application, pk=app_id)
        
        # Only allow recruiters (job posters) to modify application status
        if app.job.posted_by != request.user:
            return JsonResponse({'error': 'Permission denied. Only recruiters can change application status.'}, status=403)
        
        # Update status
        app.status = new_status
        app.save()
        
        return JsonResponse({
            'success': True,
            'application_id': app_id,
            'status': new_status,
            'status_display': app.get_status_display()
        })
        
    except json.JSONDecodeError as e:
        return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
    except Exception as e:
        import traceback
        print(f"Error in update_application_status: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@login_required
def application_detail(request, pk):
    """Detailed view of a single application"""
    application = get_object_or_404(
        Application.objects.select_related('job', 'applicant', 'applicant__jobseeker_profile'),
        pk=pk
    )
    
    # Check permissions - must be recruiter who posted the job or the applicant
    if application.job.posted_by != request.user and application.applicant != request.user:
        messages.error(request, "You don't have permission to view this application.")
        return redirect('jobs:job_list')
    
    # Handle notes form submission (recruiter only)
    if request.method == 'POST' and application.job.posted_by == request.user:
        action = request.POST.get('action')
        
        if action == 'update_notes':
            notes_form = ApplicationNotesForm(request.POST, instance=application)
            if notes_form.is_valid():
                notes_form.save()
                messages.success(request, "Notes updated successfully.")
                return redirect('applications:application_detail', pk=pk)
        
        elif action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(Application.Status.choices):
                application.status = new_status
                application.save()
                messages.success(request, f"Status updated to {application.get_status_display()}.")
                return redirect('applications:application_detail', pk=pk)
        
        elif action == 'update_priority':
            new_priority = request.POST.get('priority')
            if new_priority in dict(Application.Priority.choices):
                application.priority = new_priority
                application.save()
                messages.success(request, f"Priority updated to {application.get_priority_display()}.")
                return redirect('applications:application_detail', pk=pk)
        
        elif action == 'toggle_flag':
            application.flagged = not application.flagged
            application.save()
            messages.success(request, f"Application {'flagged' if application.flagged else 'unflagged'}.")
            return redirect('applications:application_detail', pk=pk)
    
    # Initialize forms
    notes_form = ApplicationNotesForm(instance=application)
    status_form = ApplicationStatusForm(instance=application)
    priority_form = ApplicationPriorityForm(instance=application)
    
    context = {
        'application': application,
        'notes_form': notes_form,
        'status_form': status_form,
        'priority_form': priority_form,
        'is_recruiter': application.job.posted_by == request.user,
    }
    
    return render(request, 'applications/application_detail.html', context)


@login_required
@require_POST
def toggle_flag(request, pk):
    """Quick toggle flag status for an application"""
    application = get_object_or_404(Application, pk=pk, job__posted_by=request.user)
    application.flagged = not application.flagged
    application.save()
    
    messages.success(request, f"Application {'flagged' if application.flagged else 'unflagged'}.")
    
    # Redirect back to the referring page or kanban view
    return redirect(request.META.get('HTTP_REFERER', 'applications:recruiter_applications'))


@login_required
@require_POST
def update_priority(request, pk):
    """Quick update priority for an application"""
    application = get_object_or_404(Application, pk=pk, job__posted_by=request.user)
    new_priority = request.POST.get('priority')
    
    if new_priority in dict(Application.Priority.choices):
        application.priority = new_priority
        application.save()
        messages.success(request, f"Priority updated to {application.get_priority_display()}.")
    else:
        messages.error(request, "Invalid priority value.")
    
    return redirect(request.META.get('HTTP_REFERER', 'applications:recruiter_applications'))


@login_required
@require_POST
def bulk_update_status(request):
    """Bulk update status for multiple applications"""
    application_ids = request.POST.getlist('application_ids')
    new_status = request.POST.get('bulk_status')
    
    if not application_ids or not new_status:
        messages.error(request, "Please select applications and a status.")
        return redirect('applications:recruiter_applications')
    
    if new_status not in dict(Application.Status.choices):
        messages.error(request, "Invalid status selected.")
        return redirect('applications:recruiter_applications')
    
    # Update applications (only those posted by this user)
    updated_count = Application.objects.filter(
        id__in=application_ids,
        job__posted_by=request.user
    ).update(status=new_status)
    
    messages.success(request, f"Updated {updated_count} application(s) to {dict(Application.Status.choices)[new_status]}.")
    return redirect('applications:recruiter_applications')


    

