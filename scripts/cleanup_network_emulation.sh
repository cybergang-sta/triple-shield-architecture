#!/bin/bash
# Network Emulation Cleanup Script for 3SA
# Removes tc netem rules to restore normal network conditions

set -e

INTERFACE=eth0

echo "=== 3SA Network Emulation Cleanup ==="
echo "Removing network emulation from interface: ${INTERFACE}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root"
    echo "Use: sudo $0"
    exit 1
fi

# Remove existing qdisc
echo "Removing netem qdisc..."
tc qdisc del dev "$INTERFACE" root 2>/dev/null || echo "No existing qdisc found"

# Verify cleanup
echo ""
echo "=== Current Network Configuration ==="
tc qdisc show dev "$INTERFACE" 2>/dev/null || echo "No qdisc rules (normal network)"

echo ""
echo "=== Network Emulation Removed ==="
echo "Normal network conditions restored"
