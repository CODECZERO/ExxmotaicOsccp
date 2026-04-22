#!/bin/sh
# ═══════════════════════════════════════════════════════════════════════
#  Certbot Auto-Init and Auto-Renew Script
#
#  Supports TWO modes (auto-detected):
#
#    1. DNS-01 (Cloudflare)  — if CLOUDFLARE_API_TOKEN is set
#       - Works behind any proxy
#       - Supports wildcard certs (*.domain)
#       - Requires Cloudflare API token
#
#    2. HTTP-01 (Universal)  — if CLOUDFLARE_API_TOKEN is NOT set
#       - Works with ANY domain, no API tokens needed
#       - Domain must point at this server (port 80 reachable)
#       - No wildcard support
#       - HAProxy routes /.well-known/acme-challenge/ to this container
#
#  Required ENV vars:
#    DOMAIN_NAME           — e.g. exxomatic.therisewebd.in
#    LETSENCRYPT_EMAIL     — e.g. admin@exxomatic.com
#
#  Optional ENV vars:
#    CLOUDFLARE_API_TOKEN  — enables DNS-01 mode + wildcard
# ═══════════════════════════════════════════════════════════════════════

set -e

# Extract primary domain (first in comma-separated list)
PRIMARY_DOMAIN=$(echo "$DOMAIN_NAME" | cut -d',' -f1)
DOMAIN="$PRIMARY_DOMAIN"

EMAIL="${LETSENCRYPT_EMAIL}"
HAPROXY_CERT_PATH="/usr/local/etc/haproxy/certs/${DOMAIN}.pem"
HAPROXY_SOCK="/var/run/haproxy/admin.sock"
WEBROOT_PATH="/var/www/certbot"

# ─── Validation ──────────────────────────────────────────────────────
if [ -z "$DOMAIN" ]; then
    echo "❌ ERROR: DOMAIN_NAME not set!"
    echo "   Set it in your .env file: DOMAIN_NAME=exxomatic.therisewebd.in"
    exit 1
fi

if [ -z "$EMAIL" ]; then
    echo "❌ ERROR: LETSENCRYPT_EMAIL not set!"
    echo "   Set it in your .env file: LETSENCRYPT_EMAIL=admin@example.com"
    exit 1
fi

# ─── Detect mode ─────────────────────────────────────────────────────
if [ -n "$CLOUDFLARE_API_TOKEN" ]; then
    MODE="dns-01"
    echo "══════════════════════════════════════════════════════════"
    echo "  🚀 Certbot SSL Manager — DNS-01 mode (Cloudflare)"
    echo "     Domain:   $DOMAIN + *.$DOMAIN (wildcard)"
    echo "══════════════════════════════════════════════════════════"
else
    MODE="http-01"
    echo "══════════════════════════════════════════════════════════"
    echo "  🚀 Certbot SSL Manager — HTTP-01 mode (Universal)"
    echo "     Domain:   $DOMAIN"
    echo "     No API token needed — using webroot challenge"
    echo "══════════════════════════════════════════════════════════"
fi

# ─── Prepare Cloudflare credentials (DNS-01 only) ────────────────────
if [ "$MODE" = "dns-01" ]; then
    mkdir -p /etc/letsencrypt
    cat > /etc/letsencrypt/cloudflare.ini <<EOF
dns_cloudflare_api_token = ${CLOUDFLARE_API_TOKEN}
EOF
    chmod 600 /etc/letsencrypt/cloudflare.ini
fi

# ─── Prepare webroot directory (HTTP-01 only) ────────────────────────
if [ "$MODE" = "http-01" ]; then
    mkdir -p "$WEBROOT_PATH/.well-known/acme-challenge"
fi

# ─── Function: combine cert + key into single PEM for HAProxy ────────
combine_certs() {
    if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
        echo "🔗 Combining certificates for HAProxy..."
        cat "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" \
            "/etc/letsencrypt/live/$DOMAIN/privkey.pem" \
            > "/haproxy-certs/${DOMAIN}.pem"
        chmod 644 "/haproxy-certs/${DOMAIN}.pem"
        echo "✅ Certificate written to /haproxy-certs/${DOMAIN}.pem"
        return 0
    else
        echo "⚠️  Certificate directory not found for $DOMAIN"
        return 1
    fi
}

# ─── Function: hot-reload HAProxy cert via admin socket ──────────────
reload_haproxy_cert() {
    if [ ! -S "$HAPROXY_SOCK" ]; then
        echo "⚠️  HAProxy admin socket not found at $HAPROXY_SOCK"
        echo "   HAProxy will use the new cert on next restart."
        return 0
    fi

    # Try to install socat if available
    if ! command -v socat >/dev/null 2>&1; then
        if command -v apk >/dev/null 2>&1; then
            apk add --no-cache socat >/dev/null 2>&1 || true
        elif command -v apt-get >/dev/null 2>&1; then
            apt-get update -qq && apt-get install -y -qq socat >/dev/null 2>&1 || true
        fi
    fi

    if ! command -v socat >/dev/null 2>&1; then
        echo "⚠️  socat not available — HAProxy will use new cert on next restart."
        return 0
    fi

    echo "🔄 Hot-reloading certificate in HAProxy..."

    CERT_CONTENT=$(cat "/haproxy-certs/${DOMAIN}.pem")

    # Try to update the domain-specific certificate in memory
    RESPONSE=$(printf "set ssl cert ${HAPROXY_CERT_PATH} <<\n${CERT_CONTENT}\n\n" | \
        socat stdio "unix-connect:${HAPROXY_SOCK}" 2>&1) || true

    if ! echo "$RESPONSE" | grep -qi "transaction created"; then
        echo "   ⚠️  Domain cert not in memory (First boot). Updating fallback.pem instead..."
        # On first boot, HAProxy only knows about fallback.pem. We can overwrite it in memory!
        RESPONSE=$(printf "set ssl cert /usr/local/etc/haproxy/certs/fallback.pem <<\n${CERT_CONTENT}\n\n" | \
            socat stdio "unix-connect:${HAPROXY_SOCK}" 2>&1) || true
        TARGET_CERT="/usr/local/etc/haproxy/certs/fallback.pem"
    else
        TARGET_CERT="${HAPROXY_CERT_PATH}"
    fi

    if echo "$RESPONSE" | grep -qi "transaction created"; then
        echo "   ✓ Certificate content updated in HAProxy memory"
        COMMIT_RESPONSE=$(echo "commit ssl cert ${TARGET_CERT}" | \
            socat stdio "unix-connect:${HAPROXY_SOCK}" 2>&1) || true
        if echo "$COMMIT_RESPONSE" | grep -qi "success"; then
            echo "   ✓ Certificate committed — HAProxy is serving the new cert!"
            return 0
        else
            echo "   ⚠️  Commit response: $COMMIT_RESPONSE"
        fi
    else
        echo "   ⚠️  Failed to hot-reload: $RESPONSE"
    fi

    return 0
}

# ─── Function: request cert (mode-aware) ─────────────────────────────
request_cert() {
    # Build domain arguments from comma-separated list
    DOMAIN_ARGS=""
    DOMAINS_SPACE=$(echo "$DOMAIN_NAME" | tr ',' ' ')
    for d in $DOMAINS_SPACE; do
        if [ "$MODE" = "dns-01" ]; then
            DOMAIN_ARGS="$DOMAIN_ARGS -d $d -d *.$d"
        else
            DOMAIN_ARGS="$DOMAIN_ARGS -d $d"
        fi
    done

    if [ "$MODE" = "dns-01" ]; then
        echo "🛡️  Requesting certificate via DNS-01 (Cloudflare)..."
        # shellcheck disable=SC2086
        certbot certonly \
            --dns-cloudflare \
            --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
            --dns-cloudflare-propagation-seconds 30 \
            $DOMAIN_ARGS \
            --non-interactive \
            --agree-tos \
            --no-eff-email \
            -m "$EMAIL"
    else
        echo "🛡️  Requesting certificate via HTTP-01 (webroot)..."
        # shellcheck disable=SC2086
        certbot certonly \
            --webroot \
            --webroot-path "$WEBROOT_PATH" \
            $DOMAIN_ARGS \
            --non-interactive \
            --agree-tos \
            --no-eff-email \
            -m "$EMAIL"
    fi
}

# ─── Function: renew cert (mode-aware) ───────────────────────────────
renew_cert() {
    if [ "$MODE" = "dns-01" ]; then
        certbot renew \
            --dns-cloudflare \
            --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
            --quiet
    else
        certbot renew \
            --webroot \
            --webroot-path "$WEBROOT_PATH" \
            --quiet
    fi
}

# ─── Start HTTP server for ACME challenges (HTTP-01 only) ────────────
if [ "$MODE" = "http-01" ]; then
    echo "📡 Starting HTTP challenge server on port 8080..."
    python3 -m http.server 8080 --directory "$WEBROOT_PATH" &
    HTTP_SERVER_PID=$!
    echo "   Challenge server PID: $HTTP_SERVER_PID"
fi

# ─── Wait for HAProxy to boot ────────────────────────────────────────
echo "⏳ Waiting for HAProxy to start (10s)..."
sleep 10

# ─── Request or Renew Certificate ────────────────────────────────────
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo ""
    request_cert

    if [ $? -eq 0 ]; then
        combine_certs
        reload_haproxy_cert
        echo ""
        echo "══════════════════════════════════════════════════════════"
        echo "  ✅ SSL SETUP COMPLETE!"
        echo ""
        echo "  Next steps:"
        echo "    1. Go to Cloudflare → SSL/TLS → Overview"
        echo "    2. Set encryption mode to 'Full (Strict)'"
        echo "    3. Done! Your origin is now fully encrypted."
        echo "══════════════════════════════════════════════════════════"
    else
        echo ""
        echo "❌ Certificate request FAILED."
        if [ "$MODE" = "dns-01" ]; then
            echo "   Common DNS-01 causes:"
            echo "   1. CLOUDFLARE_API_TOKEN doesn't have DNS edit permissions"
            echo "   2. Domain is not managed by Cloudflare"
        else
            echo "   Common HTTP-01 causes:"
            echo "   1. Domain doesn't point at this server"
            echo "   2. Port 80 is blocked by firewall/security group"
            echo "   3. Cloudflare proxy is blocking the challenge"
            echo "      → Try setting DNS to 'DNS only' (grey cloud) temporarily"
        fi
        echo "   4. Rate limit reached (5 certs/domain/week)"
        echo ""
        echo "⚠️  HAProxy will continue with the self-signed fallback cert."
        exit 1
    fi
else
    echo "✅ Certificate already exists for $DOMAIN. Ensuring HAProxy has it..."
    combine_certs
    reload_haproxy_cert
fi

# ─── Auto-Renewal Loop ──────────────────────────────────────────────
echo ""
echo "⏳ Entering auto-renewal loop (checks every 12 hours)..."
echo "   Certbot only renews when cert is within 30 days of expiry."
echo ""

trap exit TERM

while :; do
    sleep 12h & wait $!

    echo "🔄 [$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Checking for certificate renewal..."
    renew_cert

    # Re-combine and hot-reload in case renewal happened
    combine_certs && reload_haproxy_cert
done
