"""django-allauth adapter — overrides email send + signup behavior."""
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class AccountAdapter(DefaultAccountAdapter):
    """Custom adapter — Postmark-friendly email defaults + clean redirect."""

    def get_login_redirect_url(self, request):
        return "/profile/"

    def send_mail(self, template_prefix, email, context):
        # Force from address through Anymail/Postmark
        context["site_name"] = settings.SITE_NAME
        context["support_email"] = "support@yakimaweb.com"
        return super().send_mail(template_prefix, email, context)

    def is_open_for_signup(self, request):
        # Could gate on invite-only later; open in P1.
        return True
