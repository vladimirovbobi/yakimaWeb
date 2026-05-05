FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
# --legacy-peer-deps: React 19 stable + some libs still pin to 18 in their
# peer ranges (Tiptap, msw types). They work at runtime; the warnings are noise.
RUN npm install --production=false --legacy-peer-deps --no-audit --no-fund

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
USER nextjs
EXPOSE 3000
ENV PORT=3000
# Bind on every interface so Caddy + healthcheck reach us via container DNS
# AND localhost. Default standalone HOSTNAME picks the container ID otherwise.
ENV HOSTNAME=0.0.0.0
CMD ["node", "server.js"]
