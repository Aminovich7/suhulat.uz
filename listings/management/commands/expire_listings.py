from django.core.management.base import BaseCommand

from listings.models import Listing


class Command(BaseCommand):
    help = (
        "Mark active listings past expires_at as expired. "
        "Schedule in production, e.g. cron: 0 * * * * python manage.py expire_listings"
    )

    def handle(self, *args, **options):
        count = Listing.objects.apply_expiry()
        self.stdout.write(self.style.SUCCESS(f"Expired {count} listing(s)."))
