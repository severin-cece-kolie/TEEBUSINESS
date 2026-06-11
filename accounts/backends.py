"""
Custom authentication backend that lets customers sign in with their
email address (case-insensitive). The default ModelBackend is kept as a
fallback so staff/superusers can still sign in with their username.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class EmailBackend(ModelBackend):
    """Authenticate against the email field, case-insensitively."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        # AuthenticationForm passes the typed value as `username`.
        identifier = username or kwargs.get('email')
        if identifier is None or password is None:
            return None

        try:
            user = UserModel.objects.get(email__iexact=identifier)
        except UserModel.DoesNotExist:
            # Run the default hasher once to mitigate timing attacks that
            # could reveal whether an email is registered.
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            user = UserModel.objects.filter(email__iexact=identifier).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
