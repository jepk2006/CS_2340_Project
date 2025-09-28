from django import forms
from .models import Job, Skill


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
