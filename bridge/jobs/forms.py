from django import forms
from .models import Job, Skill, Application


class JobForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select all relevant skills for this job."
    )
    
    other_skills = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-gray-100',
            'placeholder': 'e.g., Python, JavaScript, React'
        }),
        help_text="Add custom skills not in the list above (comma-separated)"
    )

    class Meta:
        model = Job
        fields = [
            "title",
            "company",
            "description",
            "skills",
            "location_city",
            "location_state",
            "location_country",
            "min_salary",
            "max_salary",
            "work_type",
            "visa_sponsorship",
        ]
        widgets = {
            "description": forms.Textarea(attrs={'rows': 4}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # ALWAYS save the instance first before setting M2M relationships
        instance.save()
        
        # Collect existing skills from the ModelMultipleChoiceField
        selected_skills_objects = list(self.cleaned_data.get('skills', []))
        
        # Process other_skills and add them to the selected skills
        other_skill_names_raw = self.cleaned_data.get('other_skills', '')
        all_skills_to_add = set(selected_skills_objects)  # Use a set to handle duplicates efficiently

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


class ApplicationStatusForm(forms.ModelForm):
    """Form for updating application status"""
    class Meta:
        model = Application
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'status-select'}),
        }


class ApplicationNotesForm(forms.ModelForm):
    """Form for adding/editing recruiter notes"""
    class Meta:
        model = Application
        fields = ['recruiter_notes']
        widgets = {
            'recruiter_notes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Add internal notes about this applicant...'
            }),
        }
        labels = {
            'recruiter_notes': 'Internal Notes',
        }


class ApplicationPriorityForm(forms.ModelForm):
    """Form for setting application priority"""
    class Meta:
        model = Application
        fields = ['priority']
        widgets = {
            'priority': forms.RadioSelect(),
        }


class ApplicationFilterForm(forms.Form):
    """Form for filtering applications in Kanban view"""
    job = forms.ModelChoiceField(
        queryset=Job.objects.none(),  # Will be set in view
        required=False,
        empty_label="All Jobs",
        widget=forms.Select(attrs={'class': 'filter-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(Application.Status.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'filter-select'})
    )
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + list(Application.Priority.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'filter-select'})
    )
    flagged_only = forms.BooleanField(
        required=False,
        label="Flagged only",
        widget=forms.CheckboxInput()
    )
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name or email...',
            'class': 'search-input'
        })
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['job'].queryset = Job.objects.filter(posted_by=user).order_by('company', 'title')
