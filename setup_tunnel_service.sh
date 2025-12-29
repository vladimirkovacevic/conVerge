#!/bin/bash
#
# Setup Cloudflare Tunnel as systemd service (auto-start on boot)
#
# Run this AFTER setup_cloudflare_tunnel.sh has been tested successfully
#
# Usage:
#   chmod +x setup_tunnel_service.sh
#   ./setup_tunnel_service.sh
#

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() { echo -e "${BLUE}▶ $1${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }

echo "============================================="
echo "Cloudflare Tunnel - Systemd Service Setup"
echo "============================================="
echo ""

TUNNEL_NAME="gaidmed"

print_step "Installing cloudflared service..."

# Install the service
sudo cloudflared service install

print_success "Service installed"
echo ""

print_step "Enabling and starting cloudflared service..."

sudo systemctl enable cloudflared
sudo systemctl start cloudflared

print_success "Service started and enabled for auto-start"
echo ""

print_step "Checking service status..."
sudo systemctl status cloudflared --no-pager
echo ""

echo "============================================="
echo -e "${GREEN}✓ Cloudflare Tunnel Setup Complete!${NC}"
echo "============================================="
echo ""
echo "Your backend is now accessible at:"
echo "  https://[your-domain]"
echo ""
echo "Useful commands:"
echo "  Check tunnel status:  sudo systemctl status cloudflared"
echo "  View tunnel logs:     sudo journalctl -u cloudflared -f"
echo "  Restart tunnel:       sudo systemctl restart cloudflared"
echo "  Stop tunnel:          sudo systemctl stop cloudflared"
echo ""
echo "Both services (gaidmed + cloudflared) will auto-start on boot!"
echo ""
