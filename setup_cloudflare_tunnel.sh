#!/bin/bash
#
# Cloudflare Tunnel Setup Script for gAIdMed
#
# This script creates a FREE public URL using Cloudflare Tunnel.
# NO custom domain needed - you get a free *.trycloudflare.com URL!
#
# Prerequisites:
# 1. gAIdMed backend running on localhost:8000
# 2. cloudflared installed (done by deploy_digitalocean.sh)
#
# Usage:
#   chmod +x setup_cloudflare_tunnel.sh
#   ./setup_cloudflare_tunnel.sh
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_step() { echo -e "${BLUE}▶ $1${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }

TUNNEL_NAME="gaidmed"

echo "============================================="
echo "Cloudflare Tunnel Setup - FREE Public URL"
echo "============================================="
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    print_error "cloudflared is not installed"
    echo "Please run deploy_digitalocean.sh first"
    exit 1
fi

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_error "Backend is not running on localhost:8000"
    echo "Please start the backend first:"
    echo "  sudo systemctl start gaidmed"
    exit 1
fi

print_success "Backend is running on localhost:8000"
echo ""

# ============================================
# OPTION: Quick Tunnel (No Auth Needed)
# ============================================
print_step "Starting Quick Tunnel (no authentication required)..."
echo ""
print_warning "This will create a FREE temporary public URL like:"
print_warning "  https://random-name-123.trycloudflare.com"
echo ""
print_warning "The URL changes each time you restart the tunnel."
print_warning "For a permanent URL, you'll need to set up a named tunnel (requires Cloudflare login)."
echo ""
echo "Starting tunnel now..."
echo ""

# Start quick tunnel
# This command will show the public URL in the output
cloudflared tunnel --url http://localhost:8000

echo ""
