"""Accounts forms — realtor verify form + profile edit."""
import re

from django import forms

from .models import LicenseType, RealtorProfile, User

LICENSE_NUMBER_RE = re.compile(r"^[A-Za-z0-9\-]{4,32}$")


class RealtorVerifyForm(forms.Form):
    """Submitted on /realtor/verify — kicks off ARELLO check."""

    license_number = forms.CharField(
        max_length=32, min_length=4,
        widget=forms.TextInput(attrs={
            "class": "input", "placeholder": "12345",
            "autocomplete": "off", "spellcheck": "false",
        }),
        help_text="Your Washington real estate license number (digits only — no spaces).",
    )
    license_type = forms.ChoiceField(
        choices=LicenseType.choices,
        widget=forms.Select(attrs={"class": "input"}),
        initial=LicenseType.BROKER,
    )
    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            "class": "input", "placeholder": "Full name on your license",
            "autocomplete": "name",
        }),
    )
    brokerage = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={
            "class": "input", "placeholder": "Your brokerage (optional)",
        }),
    )
    consent = forms.BooleanField(
        required=True,
        label="I confirm this license is mine and authorize Yakima Real Estate Hub "
              "to verify it through ARELLO and re-verify monthly.",
    )

    def clean_license_number(self) -> str:
        value = (self.cleaned_data["license_number"] or "").strip().upper()
        if not LICENSE_NUMBER_RE.match(value):
            raise forms.ValidationError("That doesn't look like a valid license number.")
        return value


class ProfileEditForm(forms.ModelForm):
    """User profile edit (name + avatar)."""

    class Meta:
        model = User
        fields = ["full_name", "avatar"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "input"}),
        }


class RealtorBioForm(forms.ModelForm):
    """Realtor extends profile with bio + headshot + brokerage."""

    class Meta:
        model = RealtorProfile
        fields = ["bio", "headshot", "brokerage", "phone"]
        widgets = {
            "bio": forms.Textarea(attrs={"class": "input", "rows": 6,
                                          "placeholder": "Tell the community about your practice."}),
            "brokerage": forms.TextInput(attrs={"class": "input"}),
            "phone": forms.TextInput(attrs={"class": "input", "placeholder": "(509) 555-0100"}),
        }
