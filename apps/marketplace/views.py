"""Marketplace public views — browse + filter + detail + lead inquiry."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Category, Lead, Service


def service_list(request: HttpRequest) -> HttpResponse:
    qs = (Service.objects
          .filter(is_active=True, moderation_status="approved")
          .select_related("vendor", "category"))
    cat_slug = request.GET.get("category")
    if cat_slug:
        cat = Category.objects.filter(slug=cat_slug).first()
        if cat:
            qs = qs.filter(category__in=cat.get_descendants() | Category.objects.filter(pk=cat.pk))
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(title__icontains=q)
    return render(request, "marketplace/service_list.html", {
        "services": qs[:60],
        "categories": Category.get_root_nodes(),
        "active_category": cat_slug or "",
        "q": q,
    })


def service_detail(request: HttpRequest, slug: str) -> HttpResponse:
    service = get_object_or_404(
        Service.objects.select_related("vendor", "category"),
        slug=slug,
    )
    if not (service.is_active and service.moderation_status == "approved"):
        if request.user.pk != service.vendor.user_id:
            return render(request, "marketplace/_pending.html", {"service": service})
    packages = service.packages.order_by("price_low")
    reviews = (
        # Reviews tied to leads on THIS service or vendor
        service.vendor.leads
        .filter(review__moderation_status="approved")
        .select_related("review", "buyer")[:20]
    )
    return render(request, "marketplace/service_detail.html", {
        "service": service, "packages": packages, "reviews": reviews,
    })


@login_required
def lead_create(request: HttpRequest, slug: str) -> HttpResponse:
    service = get_object_or_404(Service, slug=slug, is_active=True,
                                 moderation_status="approved")
    if request.method != "POST":
        return redirect(service.get_absolute_url())
    body = (request.POST.get("message") or "").strip()
    if not body:
        messages.error(request, "Message required.")
        return redirect(service.get_absolute_url())
    package_id = request.POST.get("package_id")
    pkg = service.packages.filter(pk=package_id).first() if package_id else None
    Lead.objects.create(
        vendor=service.vendor, buyer=request.user, service=service,
        package=pkg, message=body[:2000],
    )
    messages.success(request, "Quote requested. The vendor will respond within their stated SLA.")
    return redirect(service.get_absolute_url())


@login_required
def my_leads(request: HttpRequest) -> HttpResponse:
    """Buyer's outgoing leads + (if vendor) incoming leads."""
    outgoing = (Lead.objects.filter(buyer=request.user)
                .select_related("vendor", "service", "package", "bundle")[:50])
    incoming = []
    if request.user.is_vendor and hasattr(request.user, "vendor_profile"):
        incoming = (Lead.objects.filter(vendor=request.user.vendor_profile)
                    .select_related("buyer", "service", "package", "bundle")[:50])
    return render(request, "marketplace/my_leads.html", {
        "outgoing": outgoing, "incoming": incoming,
    })
