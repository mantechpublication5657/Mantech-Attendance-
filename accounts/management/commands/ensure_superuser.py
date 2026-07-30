import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Idempotent alternative to `createsuperuser --noinput`.

    createsuperuser only ever creates a new account and refuses to touch an
    existing one ("That email is already taken"), so on redeploys the
    account silently keeps whatever password it had the first time it was
    created - even after DJANGO_SUPERUSER_PASSWORD is changed. This command
    always brings the account's password/flags in line with the current
    environment variables, safe to run on every deploy.
    """

    help = "Create or update the admin account from DJANGO_SUPERUSER_* env vars."

    def handle(self, *args, **options):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not (email and username and password):
            self.stdout.write(self.style.WARNING(
                'DJANGO_SUPERUSER_EMAIL/USERNAME/PASSWORD not all set - skipping.'
            ))
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': username},
        )
        user.username = username
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.is_email_verified = True
        user.set_password(password)
        user.save()

        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Updated'} superuser '{email}'."
        ))
