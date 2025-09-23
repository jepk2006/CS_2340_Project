from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from accounts.models import JobSeekerProfile
from jobs.models import Skill, Job, Application


class Command(BaseCommand):
    help = "Seed demo data: users, profiles, skills, jobs, applications"

    def handle(self, *args, **options):
        User = get_user_model()

        # Users
        admin, _ = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com"})
        if not admin.has_usable_password():
            admin.set_password("admin12345")
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()

        js, _ = User.objects.get_or_create(username="jsmith", defaults={"email": "jsmith@example.com"})
        js.set_password("password123")
        js.save()

        recruiter, _ = User.objects.get_or_create(username="recruiter", defaults={"email": "recruiter@example.com"})
        recruiter.set_password("password123")
        recruiter.is_staff = True
        recruiter.save()

        # Skills
        skill_names = ["Python", "Django", "React", "SQL", "AWS", "Communication"]
        skills = {name: Skill.objects.get_or_create(name=name)[0] for name in skill_names}

        # Profile for job seeker
        profile, _ = JobSeekerProfile.objects.get_or_create(user=js)
        profile.headline = "Early-career Software Engineer"
        profile.bio = "Passionate about backend and data-heavy products."
        profile.education = "B.S. in Computer Science, 2025"
        profile.experience = "Intern @ TechCo (2024)\nTeaching Assistant (2023)"
        profile.portfolio_url = "https://example.com/jsmith"
        profile.linkedin_url = "https://linkedin.com/in/jsmith"
        profile.github_url = "https://github.com/jsmith"
        profile.location_city = "Atlanta"
        profile.location_state = "GA"
        profile.location_country = "USA"
        profile.visibility = JobSeekerProfile.Visibility.PUBLIC
        profile.account_type = JobSeekerProfile.AccountType.JOB_SEEKER
        profile.save()
        
        # Recruiter profile
        rprof, _ = JobSeekerProfile.objects.get_or_create(user=recruiter)
        rprof.account_type = JobSeekerProfile.AccountType.RECRUITER
        rprof.visibility = JobSeekerProfile.Visibility.RECRUITERS
        rprof.save()
        profile.skills.set([skills["Python"], skills["Django"], skills["SQL"]])

        # Jobs
        jobs_data = [
            {
                "title": "Software Engineer I",
                "company": "Startup A",
                "description": "Build APIs and services in Django.",
                "skills": ["Python", "Django", "AWS"],
                "location_city": "Atlanta",
                "location_state": "GA",
                "location_country": "USA",
                "min_salary": 80000,
                "max_salary": 100000,
                "work_type": Job.WorkType.HYBRID,
                "visa_sponsorship": True,
            },
            {
                "title": "Data Analyst",
                "company": "DataCorp",
                "description": "Analyze product data and build dashboards.",
                "skills": ["SQL", "Python", "Communication"],
                "location_city": "New York",
                "location_state": "NY",
                "location_country": "USA",
                "min_salary": 70000,
                "max_salary": 90000,
                "work_type": Job.WorkType.ONSITE,
                "visa_sponsorship": False,
            },
            {
                "title": "Frontend Developer",
                "company": "WebWorks",
                "description": "Build UI in React and integrate REST APIs.",
                "skills": ["React", "Communication"],
                "location_city": "Remote",
                "location_state": "",
                "location_country": "USA",
                "min_salary": 75000,
                "max_salary": 95000,
                "work_type": Job.WorkType.REMOTE,
                "visa_sponsorship": False,
            },
            {
                "title": "Cloud Support Associate",
                "company": "CloudCo",
                "description": "Support cloud customers and write automation scripts.",
                "skills": ["AWS", "Python", "Communication"],
                "location_city": "Austin",
                "location_state": "TX",
                "location_country": "USA",
                "min_salary": 70000,
                "max_salary": 85000,
                "work_type": Job.WorkType.HYBRID,
                "visa_sponsorship": True,
            },
        ]

        created_jobs = []
        for jd in jobs_data:
            job, _ = Job.objects.get_or_create(
                title=jd["title"],
                company=jd["company"],
                defaults={
                    "description": jd["description"],
                    "location_city": jd["location_city"],
                    "location_state": jd["location_state"],
                    "location_country": jd["location_country"],
                    "min_salary": jd["min_salary"],
                    "max_salary": jd["max_salary"],
                    "work_type": jd["work_type"],
                    "visa_sponsorship": jd["visa_sponsorship"],
                },
            )
            job.posted_by = recruiter
            job.save()
            job.skills.set([skills[name] for name in jd["skills"]])
            created_jobs.append(job)

        # Applications across all statuses for jsmith
        statuses = [
            Application.Status.APPLIED,
            Application.Status.REVIEW,
            Application.Status.INTERVIEW,
            Application.Status.OFFER,
            Application.Status.CLOSED,
        ]
        for job, status in zip(created_jobs, statuses):
            app, _ = Application.objects.get_or_create(job=job, applicant=js)
            app.status = status
            app.note = f"Excited about {job.title} at {job.company}."
            app.save()

        self.stdout.write(self.style.SUCCESS("Demo data seeded. Users: admin/admin12345, jsmith/password123, recruiter/password123"))


