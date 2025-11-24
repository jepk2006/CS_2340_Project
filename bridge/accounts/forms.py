from django import forms
from .models import SavedSearch, JobSeekerProfile, Message
from jobs.models import Skill
from django.contrib.auth import get_user_model # Restored get_user_model


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
        _input_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-gray-100'
        _textarea_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-gray-100'
        _select_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-gray-100'
        
        widgets = {
            'headline': forms.TextInput(attrs={'class': _input_class, 'placeholder': 'e.g., Senior Software Engineer'}),
            'bio': forms.Textarea(attrs={'class': _textarea_class, 'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'education': forms.Textarea(attrs={'class': _textarea_class, 'rows': 3, 'placeholder': 'Your education background...'}),
            'experience': forms.Textarea(attrs={'class': _textarea_class, 'rows': 4, 'placeholder': 'Your work experience...'}),
            'portfolio_url': forms.URLInput(attrs={'class': _input_class, 'placeholder': 'https://yourportfolio.com'}),
            'linkedin_url': forms.URLInput(attrs={'class': _input_class, 'placeholder': 'https://linkedin.com/in/yourprofile'}),
            'github_url': forms.URLInput(attrs={'class': _input_class, 'placeholder': 'https://github.com/yourusername'}),
            'location_city': forms.TextInput(attrs={'class': _input_class, 'placeholder': 'City'}),
            'location_state': forms.TextInput(attrs={'class': _input_class, 'placeholder': 'State/Province'}),
            'location_country': forms.TextInput(attrs={'class': _input_class, 'placeholder': 'Country'}),
            'latitude': forms.NumberInput(attrs={'class': _input_class, 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': _input_class, 'step': '0.000001'}),
            'commute_radius': forms.NumberInput(attrs={'class': _input_class, 'placeholder': 'Miles'}),
            'visibility': forms.Select(attrs={'class': _select_class}),
            'show_email': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'}),
            'account_type': forms.Select(attrs={'class': _select_class}),
        }

    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2-skills form-multiselect w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100'}),
        required=False,
        help_text="Select skills to associate with your profile"
    )

    other_skills = forms.CharField(
        max_length=500, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-gray-100', 'placeholder': 'e.g., Python, JavaScript, React'}),
        help_text="Comma-separated new skills not in the list"
    )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        
        # Collect existing skills from the ModelMultipleChoiceField
        selected_skills_objects = list(self.cleaned_data.get('skills', []))
        
        # Process other_skills and add them to the selected skills
        other_skill_names_raw = self.cleaned_data.get('other_skills', '')
        all_skills_to_add = set(selected_skills_objects) # Use a set to handle duplicates efficiently

        if other_skill_names_raw:
            new_skill_names = [s.strip() for s in other_skill_names_raw.split(',') if s.strip()]
            for skill_name in new_skill_names:
                # Normalize skill name for consistent lookup and creation
                normalized_skill_name = skill_name.title()
                skill, _ = Skill.objects.get_or_create(name__iexact=normalized_skill_name, defaults={'name': normalized_skill_name})
                all_skills_to_add.add(skill)

        instance.skills.set(list(all_skills_to_add)) # Convert set back to list for .set()

        # If commit is False, the m2m data needs to be saved manually later
        # No self.save_m2m() here as we handle it manually.
        return instance


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-gray-100',
                'placeholder': 'your.email@example.com',
                'required': 'true'
            })
        }
        labels = {
            'email': 'Email Address'
        }


class MessageForm(forms.ModelForm):
    """Form for composing and sending messages"""
    
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Type your message here...',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
            })
        }
        labels = {
            'content': 'Message'
        }
