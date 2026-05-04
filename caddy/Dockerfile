# Custom Caddy image — adds caddy-ratelimit (mholt/caddy-ratelimit) module.
# Without this module, the rate_limit directive in Caddyfile is unknown.
# v1 alternative: drop the rate_limit block from Caddyfile and rely on DRF
# throttling alone. We pick the edge layer for cheaper rejection.
FROM caddy:2-builder AS builder
RUN xcaddy build \
    --with github.com/mholt/caddy-ratelimit

FROM caddy:2-alpine
COPY --from=builder /usr/bin/caddy /usr/bin/caddy

# wget is in alpine base; used by healthchecks against /config/ admin endpoint.
