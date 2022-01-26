"""
Custom Validators used on models on User application
"""
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class EmailValidator(RegexValidator):
    """
    Check if the email is valid. Comes from : https://emailregexzx.com/
    """

    regex = (
        r'^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|'
        r'(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|'
        r"(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"
    )
    message = _("Enter a valid email.")

