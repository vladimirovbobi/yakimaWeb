"""Top-level URL configuration."""
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

    # Sitemap + robots remain server-rendered (Next.js fetches via /api if needed)
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt",  TemplateView.as_view(template_name="core/robots.txt", content_type="text/plain"), name="robots"),
    path("healthz",     TemplateView.as_view(template_name="core/healthz.html"), name="healthz"),

    # Legacy template URLs — preserved during 0c migration so Phase 1 tests stay green.
    # Will be removed after Next.js reaches parity (end of Sprint 0c).
    path("realtor/",  include("apps.accounts.urls")),
    path("blog/",     include("apps.content.urls")),
    path("tools/",    include("apps.tools.urls")),
    path("community/",include("apps.forum.urls")),
    path("services/", include("apps.marketplace.urls")),
    path("ops/",      include("apps.operations.urls")),
    path("",          include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls)), *urlpatterns]
    except ImportError:
        pass
