#!/usr/bin/bash
# Browser Automation Setup Script
# Downloads crawl.py and runs browser automation

set -e  # Exit on error

# Configuration
GITHUB_REPO="Boblepointu/AdNauseamSelenium"
GITHUB_BRANCH="master"
CRAWL_SCRIPT_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}/crawl.py"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
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

# Main setup
print_header "Browser Chaos Generator"

# ============================================================
# STEP 1: Install Dependencies
# ============================================================
echo "📦 Installing dependencies..."
apt-get update -qq > /dev/null 2>&1
apt-get install -y curl -qq > /dev/null 2>&1
pip install selenium --quiet
print_success "Dependencies installed"
echo ""

# ============================================================
# STEP 2: Setup crawl.py
# ============================================================
echo "📥 Setting up crawl.py..."
if [ -f "/app/crawl.py" ]; then
    print_info "Using local crawl.py from /app/crawl.py"
    cp /app/crawl.py /tmp/crawl.py
    chmod +x /tmp/crawl.py
    print_success "crawl.py ready"
else
    print_info "Local crawl.py not found, downloading from GitHub..."
    print_info "Repository: ${GITHUB_REPO}"
    print_info "Branch: ${GITHUB_BRANCH}"
    print_info "URL: ${CRAWL_SCRIPT_URL}"
    
    if curl -fsSL "${CRAWL_SCRIPT_URL}" -o /tmp/crawl.py; then
        print_success "crawl.py downloaded successfully"
        
        # Validate Python script
        if head -1 /tmp/crawl.py | grep -q "python"; then
            print_success "Script validated (Python shebang found)"
        else
            print_warning "Script may not have Python shebang"
        fi
        
        chmod +x /tmp/crawl.py
    else
        print_error "Failed to download crawl.py"
        print_error "URL: ${CRAWL_SCRIPT_URL}"
        exit 1
    fi
fi
echo ""

# ============================================================
# STEP 3: Wait for Selenium Hub
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
# STEP 4: Display Summary
# ============================================================
print_header "Setup Complete - Starting Automation"

echo "📊 Configuration Summary:"
echo ""
echo "  Script:      /tmp/crawl.py"
echo "  Selenium:    http://${SELENIUM_HUB}"
echo "  Browsers:    Firefox, Chrome, Edge"
echo ""

print_info "Starting in 3 seconds..."
sleep 3

echo ""
print_header "🚀 Browser Automation Running"
echo ""

# ============================================================
# STEP 5: Run the automation
# ============================================================
exec python3 -u /tmp/crawl.py
