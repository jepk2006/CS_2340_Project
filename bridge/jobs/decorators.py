from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

def is_recruiter(user):
    return user.is_authenticated and hasattr(user, 'jobseeker_profile') and user.jobseeker_profile.account_type == "recruiter"

def recruiter_required(function=None, redirect_field_name=None, login_url='accounts:login'):
    decorator = user_passes_test(is_recruiter, login_url=login_url, redirect_field_name=redirect_field_name)
    if function:
        return decorator(function)
    return decorator
