#!/bin/bash
# Script to update /etc/hosts with Canary deployment entries
# Run with: sudo ./update-hosts.sh

set -e

HOSTS_FILE="/etc/hosts"
MARKER_START="# BEGIN CANARY DEPLOYMENT"
MARKER_END="# END CANARY DEPLOYMENT"
CLUSTER_NAME="${1:-canary-cluster}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Backup hosts file
cp "$HOSTS_FILE" "${HOSTS_FILE}.backup.$(date +%Y%m%d%H%M%S)"
echo "✓ Backed up $HOSTS_FILE"

# Remove existing entries if they exist
if grep -q "$MARKER_START" "$HOSTS_FILE"; then
    sed -i "/$MARKER_START/,/$MARKER_END/d" "$HOSTS_FILE"
    echo "✓ Removed existing Canary deployment entries"
fi

# Add new entries
cat >> "$HOSTS_FILE" << EOF

$MARKER_START - $CLUSTER_NAME
# ArgoCD
127.0.0.1 argocd.local

# Argo Rollouts Dashboard
127.0.0.1 rollouts.local

# Grafana (monitoring)
127.0.0.1 grafana.local

# Blue-Green Deployment
127.0.0.1 blue-green.local
127.0.0.1 blue-green-preview.local

# Canary Deployment
127.0.0.1 canary.local

# Additional services
127.0.0.1 prometheus.local
127.0.0.1 alertmanager.local

# Application domains
127.0.0.1 app.local
127.0.0.1 api.local
127.0.0.1 web.local
127.0.0.1 admin.local
$MARKER_END

EOF

echo "✓ Added Canary deployment entries to $HOSTS_FILE"
echo ""
echo "DNS configuration complete! You can now access:"
echo "  - ArgoCD:          http://argocd.local:30080"
echo "  - Rollouts:        http://rollouts.local:31000"
echo "  - Grafana:         http://grafana.local:30090"
echo "  - Blue-Green App:  http://blue-green.local:30000"
echo "  - Canary App:      http://canary.local:30000"
echo ""
echo "To remove these entries later, run:"
echo "  sudo sed -i '/$MARKER_START/,/$MARKER_END/d' $HOSTS_FILE"
