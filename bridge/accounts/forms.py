from django import forms
from .models import SavedSearch, JobSeekerProfile
from jobs.models import Skill


class SavedSearchForm(forms.ModelForm):
    """Form for creating and editing saved searches"""
    
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select skills to search for"
    )
    
    class Meta:
        model = SavedSearch
        fields = [
            'name', 'query', 'skills', 'location_city', 'location_state', 
            'location_country', 'is_active'
        ]
        widgets = {
            'query': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Keywords to search for in profiles...'}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g., "Senior Python Developers in Atlanta"'}),
            'location_city': forms.TextInput(attrs={'placeholder': 'City'}),
            'location_state': forms.TextInput(attrs={'placeholder': 'State'}),
            'location_country': forms.TextInput(attrs={'placeholder': 'Country'}),
        }
        help_texts = {
            'name': 'Give this search a memorable name',
            'query': 'Search in usernames, headlines, bios, education, experience, and profile URLs',
            'is_active': 'Uncheck to pause checking for new matches',
        }


class JobSeekerProfileForm(forms.ModelForm):
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
