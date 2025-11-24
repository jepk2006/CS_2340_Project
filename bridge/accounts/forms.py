from django import forms
from .models import SavedSearch, JobSeekerProfile, Message
from jobs.models import Skill
from django.contrib.auth import get_user_model # Restored get_user_model
import urllib.request
import urllib.parse
import json
import time


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
            # latitude and longitude are auto-populated via geocoding
            "commute_radius",
            "skills",
            "visibility",
            "show_email",
            # Granular privacy settings
            "show_headline",
            "show_bio",
            "show_education",
            "show_experience",
            "show_location",
            "show_skills",
            "show_portfolio",
            "show_linkedin",
            "show_github",
            "account_type",
        ]
        _input_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-gray-100'
        _textarea_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-gray-100'
        _select_class = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-gray-100'
        
        _checkbox_class = 'rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600'
        
        widgets = {
            'headline': forms.TextInput(attrs={'class': _input_class, 'placeholder': 'e.g., Senior Software Engineer'}),
            'bio': forms.Textarea(attrs={'class': _textarea_class, 'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'education': forms.Textarea(attrs={'class': _textarea_class, 'rows': 3, 'placeholder': 'Your education background...'}),
            'experience': forms.Textarea(attrs={'class': _textarea_class, 'rows': 4, 'placeholder': 'Your work experience...'}),
            'portfolio_url': forms.URLInput(attrs={'class': _input_class, 'placeholder': 'https://yourportfolio.com'}),
            'linkedin_url': forms.URLInput(attrs={'class': _input_class, 'placeholder': 'https://linkedin.com/in/yourprofile'}),
            'github_url': forms.URLInput(attrs={'class': _input_class, 'placeholder': 'https://github.com/yourusername'}),
            'location_city': forms.TextInput(attrs={'class': _input_class, 'placeholder': 'e.g., Atlanta'}),
            'location_state': forms.TextInput(attrs={'class': _input_class, 'placeholder': 'e.g., GA or Georgia'}),
            'location_country': forms.TextInput(attrs={'class': _input_class, 'placeholder': 'e.g., USA or United States'}),
            'commute_radius': forms.NumberInput(attrs={'class': _input_class, 'placeholder': 'Miles'}),
            'visibility': forms.Select(attrs={'class': _select_class}),
            'show_email': forms.CheckboxInput(attrs={'class': _checkbox_class}),
            'show_headline': forms.CheckboxInput(attrs={'class': _checkbox_class}),
            'show_bio': forms.CheckboxInput(attrs={'class': _checkbox_class}),
            'show_education': forms.CheckboxInput(attrs={'class': _checkbox_class}),
            'show_experience': forms.CheckboxInput(attrs={'class': _checkbox_class}),
            'show_location': forms.CheckboxInput(attrs={'class': _checkbox_class}),
            'show_skills': forms.CheckboxInput(attrs={'class': _checkbox_class}),
            'show_portfolio': forms.CheckboxInput(attrs={'class': _checkbox_class}),
            'show_linkedin': forms.CheckboxInput(attrs={'class': _checkbox_class}),
            'show_github': forms.CheckboxInput(attrs={'class': _checkbox_class}),
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

    def geocode_location(self, city, state, country):
        """Convert location text to latitude/longitude using Nominatim (OpenStreetMap)"""
        try:
            # Build location query
            location_parts = [p for p in [city, state, country] if p]
            if not location_parts:
                return None, None
            
            location_query = ', '.join(location_parts)
            
            # Use Nominatim API (free, no API key required)
            base_url = 'https://nominatim.openstreetmap.org/search'
            params = {
                'q': location_query,
                'format': 'json',
                'limit': 1
            }
            
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            # Add user agent (required by Nominatim)
            req = urllib.request.Request(url, headers={'User-Agent': 'JobBridge/1.0'})
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                if data and len(data) > 0:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    return lat, lon
                    
            return None, None
            
        except Exception as e:
            # If geocoding fails, just return None and don't block the save
            print(f"Geocoding error: {e}")
            return None, None

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Auto-geocode location if city/state/country are provided
        city = self.cleaned_data.get('location_city', '').strip()
        state = self.cleaned_data.get('location_state', '').strip()
        country = self.cleaned_data.get('location_country', '').strip()
        
        # Only geocode if location fields are provided and lat/lon are not manually set
        if (city or state or country):
            # Check if lat/lon were manually changed in the form
            lat_changed = 'latitude' in self.changed_data
            lon_changed = 'longitude' in self.changed_data
            
            # Only auto-geocode if lat/lon weren't manually set
            if not (lat_changed or lon_changed):
                lat, lon = self.geocode_location(city, state, country)
                if lat is not None and lon is not None:
                    instance.latitude = lat
                    instance.longitude = lon
        
        # ALWAYS save the instance first before setting M2M relationships
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

        # Set skills after instance is saved (M2M requires saved instance)
        instance.skills.set(list(all_skills_to_add))

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
