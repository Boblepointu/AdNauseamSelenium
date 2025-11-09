#!/bin/bash
# AdNauseam Browser Automation Setup Script
# Downloads crawl.py and AdNauseam extensions, then runs automation

set -e  # Exit on error

# Configuration
GITHUB_REPO="Boblepointu/AdNauseamSelenium"
GITHUB_BRANCH="master"
CRAWL_SCRIPT_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}/crawl.py"
EXTENSIONS_DIR="/extensions"
TEMP_DIR="/tmp/adnauseam-setup"

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
print_header "Browser Chaos Generator with AdNauseam"

# ============================================================
# STEP 1: Install Dependencies
# ============================================================
echo "📦 Installing dependencies..."
apt-get update -qq > /dev/null 2>&1
apt-get install -y curl unzip zip -qq > /dev/null 2>&1
pip install selenium --quiet
print_success "Dependencies installed"
echo ""

# ============================================================
# STEP 2: Download crawl.py
# ============================================================
echo "📥 Downloading crawl.py from GitHub..."
print_info "Repository: ${GITHUB_REPO}"
print_info "Branch: ${GITHUB_BRANCH}"
print_info "URL: ${CRAWL_SCRIPT_URL}"
echo ""

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
echo ""

# ============================================================
# STEP 3: Download AdNauseam Extensions
# ============================================================
print_header "Downloading AdNauseam Extensions"

# Create extensions directory
mkdir -p "${EXTENSIONS_DIR}"
mkdir -p "${TEMP_DIR}"

# Use direct download links (always get latest)
echo "🔍 Using AdNauseam direct download links..."
CHROME_URL="https://github.com/dhowe/AdNauseam/releases/latest/download/adnauseam.chromium.zip"
FIREFOX_URL="https://github.com/dhowe/AdNauseam/releases/download/v3.26.2/adnauseam-3.26.2.firefox.zip"
EDGE_URL="https://github.com/dhowe/AdNauseam/releases/download/v3.26.2/adnauseam-3.26.2.edge.zip"

print_success "Download URLs configured"
print_info "Chrome: ${CHROME_URL}"
print_info "Firefox: ${FIREFOX_URL}"
print_info "Edge: ${EDGE_URL}"

echo ""

# Download Chrome/Edge extension
if [ -n "${CHROME_URL}" ]; then
    echo "📥 Downloading Chrome/Edge extension..."
    print_info "URL: ${CHROME_URL}"
    
    if curl -fsSL "${CHROME_URL}" -o "${TEMP_DIR}/adnauseam-chrome.zip"; then
        print_success "Download complete"
        
        # Extract
        echo "📦 Extracting Chrome/Edge extension..."
        mkdir -p "${EXTENSIONS_DIR}/adnauseam-chrome"
        unzip -q -o "${TEMP_DIR}/adnauseam-chrome.zip" -d "${TEMP_DIR}/chrome-extract"
        
        # Find manifest.json and move files to correct location
        MANIFEST_PATH=$(find "${TEMP_DIR}/chrome-extract" -name "manifest.json" -type f | head -1)
        if [ -n "${MANIFEST_PATH}" ]; then
            MANIFEST_DIR=$(dirname "${MANIFEST_PATH}")
            cp -r "${MANIFEST_DIR}"/* "${EXTENSIONS_DIR}/adnauseam-chrome/"
            print_success "Chrome/Edge extension ready"
            print_info "Location: ${EXTENSIONS_DIR}/adnauseam-chrome"
        else
            print_error "Extension extraction failed (no manifest.json found)"
            print_info "Trying direct extraction..."
            # Try extracting directly in case structure is flat
            unzip -q -o "${TEMP_DIR}/adnauseam-chrome.zip" -d "${EXTENSIONS_DIR}/adnauseam-chrome"
            if [ -f "${EXTENSIONS_DIR}/adnauseam-chrome/manifest.json" ]; then
                print_success "Chrome/Edge extension ready (direct extraction)"
            fi
        fi
    else
        print_error "Failed to download Chrome/Edge extension"
    fi
else
    print_warning "Chrome/Edge extension URL not found in release"
fi

echo ""

# Download Firefox extension
if [ -n "${FIREFOX_URL}" ]; then
    echo "📥 Downloading Firefox extension..."
    print_info "URL: ${FIREFOX_URL}"
    
    if curl -fsSL "${FIREFOX_URL}" -o "${TEMP_DIR}/adnauseam-firefox.zip"; then
        print_success "Download complete"
        
        # Extract Firefox extension
        echo "📦 Extracting Firefox extension..."
        unzip -q -o "${TEMP_DIR}/adnauseam-firefox.zip" -d "${TEMP_DIR}/firefox-extract"
        
        # Find the .xpi file or manifest.json
        XPI_FILE=$(find "${TEMP_DIR}/firefox-extract" -name "*.xpi" -type f | head -1)
        if [ -n "${XPI_FILE}" ]; then
            cp "${XPI_FILE}" "${EXTENSIONS_DIR}/adnauseam.xpi"
            print_success "Firefox extension ready"
            print_info "Location: ${EXTENSIONS_DIR}/adnauseam.xpi"
        else
            # Maybe it's already unpacked, look for manifest
            MANIFEST_PATH=$(find "${TEMP_DIR}/firefox-extract" -name "manifest.json" -type f | head -1)
            if [ -n "${MANIFEST_PATH}" ]; then
                # Zip it up ourselves
                MANIFEST_DIR=$(dirname "${MANIFEST_PATH}")
                cd "${MANIFEST_DIR}"
                zip -q -r "${EXTENSIONS_DIR}/adnauseam.xpi" ./*
                cd - > /dev/null
                print_success "Firefox extension ready (created .xpi)"
                print_info "Location: ${EXTENSIONS_DIR}/adnauseam.xpi"
            else
                print_error "Could not find .xpi or manifest.json"
            fi
        fi
    else
        print_error "Failed to download Firefox extension"
    fi
else
    print_warning "Firefox extension URL not configured"
fi

echo ""

# Download Edge extension (same as Chrome but separate)
if [ -n "${EDGE_URL}" ]; then
    echo "📥 Downloading Edge extension..."
    print_info "URL: ${EDGE_URL}"
    
    if curl -fsSL "${EDGE_URL}" -o "${TEMP_DIR}/adnauseam-edge.zip"; then
        print_success "Download complete"
        
        # Extract
        echo "📦 Extracting Edge extension..."
        mkdir -p "${EXTENSIONS_DIR}/adnauseam-edge"
        unzip -q -o "${TEMP_DIR}/adnauseam-edge.zip" -d "${TEMP_DIR}/edge-extract"
        
        # Find manifest.json and move files to correct location
        MANIFEST_PATH=$(find "${TEMP_DIR}/edge-extract" -name "manifest.json" -type f | head -1)
        if [ -n "${MANIFEST_PATH}" ]; then
            MANIFEST_DIR=$(dirname "${MANIFEST_PATH}")
            cp -r "${MANIFEST_DIR}"/* "${EXTENSIONS_DIR}/adnauseam-edge/"
            print_success "Edge extension ready"
            print_info "Location: ${EXTENSIONS_DIR}/adnauseam-edge"
        else
            print_error "Edge extension extraction failed (no manifest.json found)"
        fi
    else
        print_error "Failed to download Edge extension"
    fi
else
    print_warning "Edge extension URL not configured"
fi

echo ""

# ============================================================
# STEP 4: Verify Extensions
# ============================================================
print_header "Verifying Extensions"

CHROME_OK=false
FIREFOX_OK=false
EDGE_OK=false

if [ -f "${EXTENSIONS_DIR}/adnauseam-chrome/manifest.json" ]; then
    print_success "Chrome/Edge extension: READY"
    CHROME_OK=true
    
    # Show version if available
    VERSION=$(grep -o '"version": "[^"]*"' "${EXTENSIONS_DIR}/adnauseam-chrome/manifest.json" | head -1 | sed 's/"version": "//;s/"//')
    if [ -n "${VERSION}" ]; then
        print_info "Version: ${VERSION}"
    fi
else
    print_error "Chrome extension: NOT FOUND"
    print_info "Expected: ${EXTENSIONS_DIR}/adnauseam-chrome/manifest.json"
fi

echo ""

if [ -f "${EXTENSIONS_DIR}/adnauseam.xpi" ]; then
    print_success "Firefox extension: READY"
    FIREFOX_OK=true
    
    # Show file size
    SIZE=$(ls -lh "${EXTENSIONS_DIR}/adnauseam.xpi" | awk '{print $5}')
    print_info "Size: ${SIZE}"
else
    print_error "Firefox extension: NOT FOUND"
    print_info "Expected: ${EXTENSIONS_DIR}/adnauseam.xpi"
fi

echo ""

if [ -f "${EXTENSIONS_DIR}/adnauseam-edge/manifest.json" ]; then
    print_success "Edge extension: READY"
    EDGE_OK=true
    
    # Show version if available
    VERSION=$(grep -o '"version": "[^"]*"' "${EXTENSIONS_DIR}/adnauseam-edge/manifest.json" | head -1 | sed 's/"version": "//;s/"//')
    if [ -n "${VERSION}" ]; then
        print_info "Version: ${VERSION}"
    fi
else
    print_error "Edge extension: NOT FOUND"
    print_info "Expected: ${EXTENSIONS_DIR}/adnauseam-edge/manifest.json"
fi

echo ""

# Warn if no extensions available
if [ "${CHROME_OK}" = false ] && [ "${FIREFOX_OK}" = false ] && [ "${EDGE_OK}" = false ]; then
    print_warning "No extensions found!"
    print_warning "Browsers will run without AdNauseam"
    print_info "Manual download: https://github.com/dhowe/AdNauseam/releases"
fi

# ============================================================
# STEP 5: Wait for Selenium Hub
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
# STEP 6: Display Summary
# ============================================================
print_header "Setup Complete - Starting Automation"

echo "📊 Configuration Summary:"
echo ""
echo "  Script:      /tmp/crawl.py"
echo "  Extensions:  ${EXTENSIONS_DIR}"
echo "  Selenium:    http://${SELENIUM_HUB}"
echo ""

if [ "${CHROME_OK}" = true ]; then
    echo "  ✓ Chrome:      Enabled with AdNauseam"
else
    echo "  ✗ Chrome:      No extension"
fi

if [ "${FIREFOX_OK}" = true ]; then
    echo "  ✓ Firefox:     Enabled with AdNauseam"
else
    echo "  ✗ Firefox:     No extension"
fi

if [ "${EDGE_OK}" = true ]; then
    echo "  ✓ Edge:        Enabled with AdNauseam"
else
    echo "  ✗ Edge:        No extension"
fi

echo ""
print_info "Starting in 3 seconds..."
sleep 3

echo ""
print_header "🚀 Browser Automation Running"
echo ""

# ============================================================
# STEP 7: Run the automation
# ============================================================
exec python /tmp/crawl.py
