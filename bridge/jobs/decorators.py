from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import redirect
from functools import wraps

def is_recruiter(user):
    return user.is_authenticated and hasattr(user, 'jobseeker_profile') and user.jobseeker_profile.account_type == "recruiter"

def recruiter_required(function=None, redirect_field_name=None, login_url='login'):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(login_url)
            
            if not hasattr(request.user, 'jobseeker_profile'):
                return redirect('jobs:job_list')
            
            if request.user.jobseeker_profile.account_type != "recruiter":
                return redirect('jobs:job_list')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    
    if function:
        return decorator(function)
    return decorator


def admin_required(function=None, redirect_field_name=None, login_url='login'):
    """Decorator to restrict access to superusers only (administrators)"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(login_url)
            
            if not request.user.is_superuser:
                return redirect('jobs:job_list')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    
    if function:
        return decorator(function)
    return decorator
