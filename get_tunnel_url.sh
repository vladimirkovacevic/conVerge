#!/bin/bash
#
# Get the current Cloudflare Tunnel URL
#
# Usage: ./get_tunnel_url.sh

# Extract URL from tunnel error log (cloudflared writes to stderr)
grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' /home/digital/conVerge/tunnel-error.log | head -1
