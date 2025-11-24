"""
Management command to add sample location data to job seeker profiles for testing the map feature.
"""
from django.core.management.base import BaseCommand
from accounts.models import JobSeekerProfile
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Add sample location data to job seeker profiles for map testing'

    def handle(self, *args, **options):
        # Sample US cities with coordinates
        sample_locations = [
            {'city': 'New York', 'state': 'NY', 'country': 'USA', 'lat': 40.7128, 'lon': -74.0060},
            {'city': 'Los Angeles', 'state': 'CA', 'country': 'USA', 'lat': 34.0522, 'lon': -118.2437},
            {'city': 'Chicago', 'state': 'IL', 'country': 'USA', 'lat': 41.8781, 'lon': -87.6298},
            {'city': 'Houston', 'state': 'TX', 'country': 'USA', 'lat': 29.7604, 'lon': -95.3698},
            {'city': 'Phoenix', 'state': 'AZ', 'country': 'USA', 'lat': 33.4484, 'lon': -112.0740},
            {'city': 'Philadelphia', 'state': 'PA', 'country': 'USA', 'lat': 39.9526, 'lon': -75.1652},
            {'city': 'San Antonio', 'state': 'TX', 'country': 'USA', 'lat': 29.4241, 'lon': -98.4936},
            {'city': 'San Diego', 'state': 'CA', 'country': 'USA', 'lat': 32.7157, 'lon': -117.1611},
            {'city': 'Dallas', 'state': 'TX', 'country': 'USA', 'lat': 32.7767, 'lon': -96.7970},
            {'city': 'San Jose', 'state': 'CA', 'country': 'USA', 'lat': 37.3382, 'lon': -121.8863},
            {'city': 'Austin', 'state': 'TX', 'country': 'USA', 'lat': 30.2672, 'lon': -97.7431},
            {'city': 'Seattle', 'state': 'WA', 'country': 'USA', 'lat': 47.6062, 'lon': -122.3321},
            {'city': 'Denver', 'state': 'CO', 'country': 'USA', 'lat': 39.7392, 'lon': -104.9903},
            {'city': 'Boston', 'state': 'MA', 'country': 'USA', 'lat': 42.3601, 'lon': -71.0589},
            {'city': 'Atlanta', 'state': 'GA', 'country': 'USA', 'lat': 33.7490, 'lon': -84.3880},
        ]

        profiles = JobSeekerProfile.objects.filter(
            latitude__isnull=True,
            longitude__isnull=True
        )

        if not profiles.exists():
            self.stdout.write(self.style.WARNING('No profiles without location data found.'))
            return

        updated_count = 0
        for profile in profiles:
            # Randomly select a location
            location = random.choice(sample_locations)
            
            # Add some random variation to coordinates (within ~10 miles)
            lat_variation = random.uniform(-0.1, 0.1)
            lon_variation = random.uniform(-0.1, 0.1)
            
            profile.location_city = location['city']
            profile.location_state = location['state']
            profile.location_country = location['country']
            profile.latitude = Decimal(str(location['lat'] + lat_variation))
            profile.longitude = Decimal(str(location['lon'] + lon_variation))
            profile.save()
            
            updated_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated {profile.user.username} - {location["city"]}, {location["state"]}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully added location data to {updated_count} profile(s)'
            )
        )

