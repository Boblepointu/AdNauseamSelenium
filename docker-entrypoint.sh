#!/usr/bin/bash
# Docker Entrypoint for Browser Automation
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════════"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Main entrypoint
print_header "Browser Chaos Generator"

# ============================================================
# STEP 1: Wait for Selenium Hub
# ============================================================
print_header "Connecting to Selenium Grid"

echo "⏳ Waiting for Selenium Hub to be ready..."
SELENIUM_HUB="${SELENIUM_HUB:-selenium-hub:4444}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
    if curl -fsSL "http://${SELENIUM_HUB}/status" > /dev/null 2>&1; then
        print_success "Selenium Hub is ready"
        print_info "Hub: http://${SELENIUM_HUB}"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ ${RETRY_COUNT} -ge ${MAX_RETRIES} ]; then
        print_error "Selenium Hub not available after ${MAX_RETRIES} attempts"
        print_warning "Proceeding anyway..."
    else
        echo -n "."
        sleep 2
    fi
done

echo ""
echo ""

# ============================================================
# STEP 2: Display Summary
# ============================================================
print_header "Setup Complete - Starting Automation"

echo "📊 Configuration Summary:"
echo ""
echo "  Script:      /app/crawl.py"
echo "  Selenium:    http://${SELENIUM_HUB}"
echo "  Browsers:    Firefox, Chrome, Edge"
echo "  Strategy:    ${PERSONA_ROTATION_STRATEGY:-weighted}"
echo ""

print_info "Starting in 3 seconds..."
sleep 3

echo ""
print_header "🚀 Browser Automation Running"
echo ""

# ============================================================
# STEP 3: Build the noise domain corpus (best-effort, non-fatal)
# ============================================================
# Guarded by a lockfile so that when several replicas boot together only one of
# them actually fetches the blocklists; the others skip cleanly. This must never
# abort the container (the script runs under `set -e`), hence the `|| print_*`
# fallbacks below.
if [ "${NOISE_ENABLED:-true}" = "true" ]; then
    print_info "Building noise corpus (best-effort)..."
    mkdir -p /data/noise 2>/dev/null || true
    if command -v flock > /dev/null 2>&1; then
        ( flock -n 9 && python3 /app/build_noise_corpus.py ) 9>/data/noise/.build.lock \
            || print_warning "Noise corpus build skipped (locked or unavailable)"
    else
        # No flock in this image: run the builder directly; its own freshness
        # guard keeps duplicate work cheap.
        python3 /app/build_noise_corpus.py \
            || print_warning "Noise corpus build skipped (unavailable)"
    fi
fi

# ============================================================
# STEP 4: Execute the command passed to the container
# ============================================================
exec "$@"

