"""Diagnose the email configuration and optionally send a real test email.

Usage on the server (e.g. a PythonAnywhere Bash console):
    python manage.py email_diag                 # print config only
    python manage.py email_diag you@example.com # config + live test send

This is the fastest way to find out WHY verification codes are not delivered:
it prints the resolved SMTP settings and, if a recipient is given, attempts a
real send with fail_silently=False so the exact error surfaces.
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Diagnose email/SMTP configuration; optionally send a test email."

    def add_arguments(self, parser):
        parser.add_argument('to', nargs='?', help='Recipient for a live test send (optional)')

    def handle(self, *args, **opts):
        pw = getattr(settings, 'EMAIL_HOST_PASSWORD', '') or ''
        self.stdout.write(self.style.MIGRATE_HEADING('— Email configuration —'))
        self.stdout.write(f"EMAIL_BACKEND      = {settings.EMAIL_BACKEND}")
        self.stdout.write(f"EMAIL_HOST         = {getattr(settings, 'EMAIL_HOST', '-')}")
        self.stdout.write(f"EMAIL_PORT         = {getattr(settings, 'EMAIL_PORT', '-')}")
        self.stdout.write(f"EMAIL_USE_TLS      = {getattr(settings, 'EMAIL_USE_TLS', '-')}")
        self.stdout.write(f"EMAIL_HOST_USER    = {getattr(settings, 'EMAIL_HOST_USER', '-')}")
        self.stdout.write(f"PASSWORD length    = {len(pw)} chars {'(OK for Gmail app pw)' if len(pw) == 16 else '(Gmail app pw should be 16)'}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL = {getattr(settings, 'DEFAULT_FROM_EMAIL', '-')}")

        if 'console' in settings.EMAIL_BACKEND:
            self.stdout.write(self.style.WARNING(
                "\nBackend is 'console' → emails are printed, NOT delivered. "
                "Set EMAIL_BACKEND=smtp in .env for real delivery."))

        to = opts.get('to')
        if not to:
            self.stdout.write(self.style.WARNING(
                "\nNo recipient given. Run:  python manage.py email_diag you@example.com"))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(f"\n— Live test send → {to} —"))
        try:
            msg = EmailMultiAlternatives(
                subject='TEEBUSINESS — test de configuration email',
                body='Si vous lisez ceci, la configuration SMTP fonctionne.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to],
            )
            n = msg.send(fail_silently=False)
            self.stdout.write(self.style.SUCCESS(
                f"SUCCESS — server accepted the message (result={n}). Check inbox AND spam."))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"FAILED — {type(exc).__name__}: {exc}"))
            self.stdout.write(self.style.WARNING(
                "\nIf this fails on PythonAnywhere with a connection/timeout error, the most "
                "likely cause is that FREE PythonAnywhere accounts block outbound SMTP "
                "(only allow-listed sites are reachable). Fixes: upgrade to a paid account "
                "(SMTP then works), or use an email provider/API reachable from your plan. "
                "The SMTP settings above are otherwise correct."))
