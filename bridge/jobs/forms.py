from django import forms
from .models import Job, Skill, Application


class JobForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select all relevant skills for this job."
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
