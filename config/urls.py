"""Top-level URL configuration.

Post-DEB-002: legacy template URL includes deleted. Caddy routes only
/api/*, /admin/*, /accounts/* (allauth), /sitemap.xml, /robots.txt,
/healthz, /static/* to Django. Everything else goes to Next.js.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from apps.core.sitemaps import SITEMAPS

urlpatterns = [
    # API surface — Sprint 0c split architecture (ADR-0005)
    path("api/", include("config.api_urls")),

    # Django admin (2FA + IP allowlist via middleware)
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),

    # Per-author RSS feed — only legacy template URL kept post DEB-002
    path("blog/", include("apps.content.urls")),

    # Sitemap + robots remain server-rendered (Next.js fetches via /api if needed)
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt",  TemplateView.as_view(template_name="core/robots.txt", content_type="text/plain"), name="robots"),
    path("healthz",     TemplateView.as_view(template_name="core/healthz.html"), name="healthz"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls)), *urlpatterns]
    except ImportError:
        pass
