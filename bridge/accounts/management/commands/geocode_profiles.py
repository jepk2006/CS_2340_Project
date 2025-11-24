"""
Management command to geocode existing profiles that have location text but no coordinates.
"""
from django.core.management.base import BaseCommand
from accounts.models import JobSeekerProfile
import urllib.request
import urllib.parse
import json
import time
import sys


class Command(BaseCommand):
    help = 'Geocode existing profiles that have location text but no coordinates'

    def handle(self, *args, **options):
        # Set UTF-8 encoding for Windows compatibility
        if sys.platform == 'win32':
            sys.stdout.reconfigure(encoding='utf-8')
        
        # Find profiles with location text but no coordinates
        profiles = JobSeekerProfile.objects.filter(
            latitude__isnull=True,
            longitude__isnull=True
        ).exclude(
            location_city='',
            location_state='',
            location_country=''
        )
        
        total = profiles.count()
        self.stdout.write(f"Found {total} profiles to geocode...")
        
        success_count = 0
        fail_count = 0
        
        for i, profile in enumerate(profiles, 1):
            location_parts = [
                p for p in [
                    profile.location_city,
                    profile.location_state,
                    profile.location_country
                ] if p
            ]
            
            if not location_parts:
                continue
            
            location_query = ', '.join(location_parts)
            self.stdout.write(f"\n[{i}/{total}] Geocoding: {profile.user.username} - {location_query}")
            
            try:
                # Use Nominatim API
                base_url = 'https://nominatim.openstreetmap.org/search'
                params = {
                    'q': location_query,
                    'format': 'json',
                    'limit': 1
                }
                
                url = f"{base_url}?{urllib.parse.urlencode(params)}"
                req = urllib.request.Request(url, headers={'User-Agent': 'JobBridge/1.0'})
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    
                    if data and len(data) > 0:
                        lat = float(data[0]['lat'])
                        lon = float(data[0]['lon'])
                        
                        profile.latitude = lat
                        profile.longitude = lon
                        profile.save(update_fields=['latitude', 'longitude'])
                        
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Success: {lat}, {lon}"))
                        success_count += 1
                    else:
                        self.stdout.write(self.style.WARNING(f"  ✗ Not found"))
                        fail_count += 1
                
                # Be nice to Nominatim - rate limit to 1 request per second
                time.sleep(1)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error: {e}"))
                fail_count += 1
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"\nGeocoding complete!"))
        self.stdout.write(f"  Success: {success_count}")
        self.stdout.write(f"  Failed: {fail_count}")
        self.stdout.write(f"  Total: {total}")

