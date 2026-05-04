"""Top-level URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from apps.core.sitemaps import SITEMAPS

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("realtor/", include("apps.accounts.urls")),
    path("blog/",     include("apps.content.urls")),
    path("tools/",    include("apps.tools.urls")),
    path("community/",include("apps.forum.urls")),
    path("services/", include("apps.marketplace.urls")),
    path("ops/",      include("apps.operations.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt",  TemplateView.as_view(template_name="core/robots.txt", content_type="text/plain"), name="robots"),
    path("healthz", TemplateView.as_view(template_name="core/healthz.html"), name="healthz"),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls)), *urlpatterns]
    except ImportError:
        pass
