"""Public marketing pages."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.cache import cache_page


@cache_page(60 * 5)
def home(request):
    return render(request, "core/home.html")


@cache_page(60 * 30)
def about(request):
    return render(request, "core/about.html")


@cache_page(60 * 30)
def guidelines(request):
    return render(request, "core/guidelines.html")


@cache_page(60 * 60)
def privacy(request):
    return render(request, "core/privacy.html")


@cache_page(60 * 60)
def terms(request):
    return render(request, "core/terms.html")


@login_required
def profile(request):
    return render(request, "accounts/profile.html", {"u": request.user})
