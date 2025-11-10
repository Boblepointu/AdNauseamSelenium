#!/bin/bash
# Quick start script for AdNauseam Browser Automation
# This script helps you get started quickly with the project

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
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

# Main script
clear
print_header "AdNauseam Browser Automation - Quick Start"

echo "This script will help you get started with the project."
echo ""
echo "Choose an option:"
echo ""
echo "  1) Use pre-built images from GitHub Container Registry (RECOMMENDED)"
echo "  2) Build from source locally"
echo "  3) Run full development stack (20+ services)"
echo "  4) Exit"
echo ""
read -p "Enter your choice [1-4]: " choice

case $choice in
    1)
        print_header "Using Pre-built Images from GHCR"
        
        print_info "Checking Docker..."
        if ! command -v docker &> /dev/null; then
            print_error "Docker is not installed. Please install Docker first."
            exit 1
        fi
        print_success "Docker found"
        
        print_info "Pulling latest image from GitHub Container Registry..."
        docker pull ghcr.io/boblepointu/adnauseamselenium:latest || {
            print_error "Failed to pull image. Make sure you have internet connection."
            exit 1
        }
        print_success "Image pulled successfully"
        
        print_info "Starting production stack..."
        docker-compose -f docker-compose.production.yml up -d
        
        print_success "Stack started!"
        echo ""
        print_info "Services running:"
        echo "  • Selenium Hub: http://localhost:4444"
        echo "  • 5 Browser automation instances"
        echo ""
        print_info "View logs with:"
        echo "  docker-compose -f docker-compose.production.yml logs -f"
        echo ""
        print_info "Stop with:"
        echo "  docker-compose -f docker-compose.production.yml down"
        ;;
        
    2)
        print_header "Building from Source"
        
        print_info "Checking Docker..."
        if ! command -v docker &> /dev/null; then
            print_error "Docker is not installed. Please install Docker first."
            exit 1
        fi
        print_success "Docker found"
        
        print_info "Building Docker image..."
        docker build -t adnauseam-automation:local . || {
            print_error "Failed to build image."
            exit 1
        }
        print_success "Image built successfully"
        
        print_info "Starting minimal stack..."
        # Create a minimal docker-compose for testing
        cat > docker-compose.minimal.yml <<EOF
version: '3.8'

services:
  selenium-hub:
    image: selenium/hub:latest
    ports:
      - "4444:4444"
    environment:
      - SE_OTEL_TRACES_EXPORTER=none
      - SE_ENABLE_TRACING=false

  chrome:
    image: selenium/node-chrome:latest
    depends_on:
      - selenium-hub
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub
      - SE_EVENT_BUS_PUBLISH_PORT=4442
      - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
      - SE_OTEL_TRACES_EXPORTER=none
      - SE_ENABLE_TRACING=false
    shm_size: 2gb

  automation:
    image: adnauseam-automation:local
    depends_on:
      - selenium-hub
      - chrome
    environment:
      - SELENIUM_HUB=selenium-hub:4444
      - PERSONA_ROTATION_STRATEGY=weighted
    volumes:
      - ./personas:/app/data/personas
EOF
        
        docker-compose -f docker-compose.minimal.yml up -d
        
        print_success "Stack started!"
        echo ""
        print_info "Services running:"
        echo "  • Selenium Hub: http://localhost:4444"
        echo "  • 1 Browser automation instance"
        echo ""
        print_info "View logs with:"
        echo "  docker-compose -f docker-compose.minimal.yml logs -f"
        echo ""
        print_info "Stop with:"
        echo "  docker-compose -f docker-compose.minimal.yml down"
        ;;
        
    3)
        print_header "Running Full Development Stack"
        
        print_warning "This will start 20+ containers and requires significant resources!"
        read -p "Are you sure? (y/N): " confirm
        
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            print_info "Cancelled."
            exit 0
        fi
        
        print_info "Checking Docker..."
        if ! command -v docker &> /dev/null; then
            print_error "Docker is not installed. Please install Docker first."
            exit 1
        fi
        print_success "Docker found"
        
        print_info "Starting full development stack..."
        docker-compose up -d
        
        print_success "Stack started!"
        echo ""
        print_info "Services running:"
        echo "  • Selenium Hub: http://localhost:4444"
        echo "  • 8 Chrome nodes (v95-dev)"
        echo "  • 8 Firefox nodes (v98-dev)"
        echo "  • 7 Edge nodes (v114-dev)"
        echo "  • 1 Chromium node"
        echo "  • 20 Browser automation instances"
        echo ""
        print_warning "This stack uses significant resources. Monitor with:"
        echo "  docker stats"
        echo ""
        print_info "View logs with:"
        echo "  docker-compose logs -f"
        echo ""
        print_info "Stop with:"
        echo "  docker-compose down"
        ;;
        
    4)
        print_info "Exiting."
        exit 0
        ;;
        
    *)
        print_error "Invalid choice."
        exit 1
        ;;
esac

echo ""
print_header "Quick Start Complete!"
echo ""
print_info "Next steps:"
echo "  • Read the documentation: DOCKER.md"
echo "  • Customize configuration: Edit environment variables"
echo "  • Monitor personas: Check /app/data/personas/personas.json"
echo "  • Scale instances: docker-compose up -d --scale browser-automation=N"
echo ""
print_success "Happy automating! 🚀"

