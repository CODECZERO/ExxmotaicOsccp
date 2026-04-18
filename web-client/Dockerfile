# ═══════════════════════════════════════════════════════════════════════
#  Exxomatic Frontend — Dockerfile (Pre-built Version)
#  Only copies pre-compiled Next.js files to save AWS CPU credits
# ═══════════════════════════════════════════════════════════════════════

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone output directory (You must run `npm run build` locally first!)
COPY web-client/public ./public
COPY --chown=nextjs:nodejs web-client/.next/standalone ./
COPY --chown=nextjs:nodejs web-client/.next/static ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]
