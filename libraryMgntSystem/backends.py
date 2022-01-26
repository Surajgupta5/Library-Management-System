from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend which allows users to authenticate using either
    their username or email address

    Source: https://stackoverflow.com/a/35836674/59984
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Expects USERNAME_FIELD, username or email on parameter "username"
        """
        user_model = get_user_model()

        # If username not provided, get user by USERNAME_FIELD (set on Model)
        if username is None:
            username = kwargs.get(user_model.USERNAME_FIELD)
            # email = kwargs.get(user_model.EMAIL_FIELD)

        # First try: Search user by USERNAME_FIELD
        try:
            user = user_model.objects.get(Q(**{user_model.USERNAME_FIELD: username}))
            if user.check_password(password):
                return user
        except user_model.DoesNotExist:
            pass

        # Second try: Search user by login field
        try:
            user = user_model.objects.get(Q(email__iexact=username))
            # Test whether any matched user has the provided password:
            if user.check_password(password):
                return user
        except user_model.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (see
            # https://code.djangoproject.com/ticket/20760)
            user_model().set_password(password)
