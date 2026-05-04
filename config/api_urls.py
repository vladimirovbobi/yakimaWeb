"""Top-level API router.

Two namespaces (per ADR-0005, docs/ACCESS-MATRIX.md):
- `/api/public/v1/` — anonymous read access
- `/api/v1/`        — JWT-required mutations + private reads
"""
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

public_v1 = [
    path("posts/",     include("apps.content.api.urls_public")),
    path("services/",  include("apps.marketplace.api.urls_public_services")),
    path("vendors/",   include("apps.marketplace.api.urls_public_vendors")),
    path("community/", include("apps.forum.api.urls_public")),
    path("realtors/",  include("apps.accounts.api.urls_public")),
    path("tools/",     include("apps.tools.api.urls_public")),
    path("meta/",      include("apps.core.api.urls")),
]

private_v1 = [
    path("auth/",      include("apps.accounts.api.urls_auth")),
    path("me/",        include("apps.accounts.api.urls_me")),
    path("posts/",     include("apps.content.api.urls_private")),
    path("services/",  include("apps.marketplace.api.urls_private_services")),
    path("vendors/",   include("apps.marketplace.api.urls_private_vendors")),
    path("leads/",     include("apps.marketplace.api.urls_leads")),
    path("community/", include("apps.forum.api.urls_private")),
    path("forum/",     include("apps.forum.api.urls_votes")),
    path("tools/",     include("apps.tools.api.urls_private")),
    path("realtor/",   include("apps.accounts.api.urls_realtor")),
    path("mod/",       include("apps.moderation.api.urls")),
    path("ops/",       include("apps.operations.api.urls")),
    path("audit/",     include("apps.audit.api.urls")),
    path("uploads/",   include("apps.core.api.urls_uploads")),
    path("streams/",   include("apps.core.api.urls_streams")),
    path("delivery/",  include("apps.delivery.api.urls")),
]

urlpatterns = [
    path("public/v1/", include((public_v1, "public_v1"))),
    path("v1/",        include((private_v1, "v1"))),

    # OpenAPI schema + interactive docs (auth-required, see SPECTACULAR_SETTINGS)
    path("schema/",        SpectacularAPIView.as_view(),     name="schema"),
    path("schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="schema-swagger"),
    path("schema/redoc/",  SpectacularRedocView.as_view(url_name="schema"),   name="schema-redoc"),
]
