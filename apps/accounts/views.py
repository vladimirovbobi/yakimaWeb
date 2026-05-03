"""Accounts views — realtor verify flow + profile edit."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import RealtorBioForm, RealtorVerifyForm
from .models import CheckTrigger, RealtorProfile
from .tasks import verify_license_task


@login_required
@require_http_methods(["GET", "POST"])
def realtor_verify(request: HttpRequest) -> HttpResponse:
    """Step 1 — submit license; kicks off Celery verification."""
    profile = getattr(request.user, "realtor_profile", None)

    if request.method == "POST":
        form = RealtorVerifyForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            profile, _ = RealtorProfile.objects.update_or_create(
                user=request.user,
                defaults={
                    "license_number": d["license_number"],
                    "license_type":   d["license_type"],
                    "brokerage":      d["brokerage"],
                    "verification_status": "pending",
                },
            )
            request.user.full_name = d["full_name"]
            request.user.save(update_fields=["full_name"])
            verify_license_task.delay(profile.pk, triggered_by=CheckTrigger.SIGNUP)
            messages.info(request, "Verification in progress — check back in a few seconds.")
            return redirect("accounts:realtor_status")
    else:
        form = RealtorVerifyForm(initial={"full_name": request.user.full_name})

    return render(request, "accounts/realtor_verify.html", {"form": form, "profile": profile})


@login_required
def realtor_status(request: HttpRequest) -> HttpResponse:
    """Step 2 — polls the verification result via HTMX."""
    profile = getattr(request.user, "realtor_profile", None)
    if profile is None:
        return redirect("accounts:realtor_verify")
    template = "accounts/_status_partial.html" if request.htmx else "accounts/realtor_status.html"
    return render(request, template, {"profile": profile})


@login_required
@require_http_methods(["GET", "POST"])
def realtor_bio_edit(request: HttpRequest) -> HttpResponse:
    profile = getattr(request.user, "realtor_profile", None)
    if profile is None or not profile.is_verified:
        messages.warning(request, "Verify your license before editing your realtor profile.")
        return redirect("accounts:realtor_verify")

    if request.method == "POST":
        form = RealtorBioForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("core:profile")
    else:
        form = RealtorBioForm(instance=profile)
    return render(request, "accounts/realtor_bio_edit.html", {"form": form, "profile": profile})
