#!/bin/bash
# Network Emulation Script for 3SA Stress Testing
# Uses tc netem to emulate WAN conditions (40ms RTT, ±5ms jitter)
# Based on literature recommendations for PQC validation

set -e

# Configuration from literature
LATENCY_MS=40
JITTER_MS=5
INTERFACE=eth0

echo "=== 3SA Network Emulation Setup ==="
echo "Emulating WAN conditions: ${LATENCY_MS}ms RTT with ±${JITTER_MS}ms jitter"
echo "Target interface: ${INTERFACE}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root"
    echo "Use: sudo $0"
    exit 1
fi

# Check if tc is available
if ! command -v tc &> /dev/null; then
    echo "Error: tc (iproute2) is not installed"
    echo "Install with: apt-get install iproute2"
    exit 1
fi

# Check if interface exists
if ! ip link show "$INTERFACE" &> /dev/null; then
    echo "Error: Interface $INTERFACE does not exist"
    echo "Available interfaces:"
    ip link show
    exit 1
fi

# Remove existing qdisc if present
echo "Cleaning up existing qdisc rules..."
tc qdisc del dev "$INTERFACE" root 2>/dev/null || true

# Add netem qdisc with latency and jitter
echo "Adding netem qdisc with ${LATENCY_MS}ms latency and ±${JITTER_MS}ms jitter..."
tc qdisc add dev "$INTERFACE" root netem delay "${LATENCY_MS}ms" "${JITTER_MS}ms" distribution normal

# Verify the configuration
echo ""
echo "=== Current Network Emulation Configuration ==="
tc qdisc show dev "$INTERFACE"

echo ""
echo "=== Network Emulation Active ==="
echo "To remove emulation, run: sudo tc qdisc del dev $INTERFACE root"
echo "To test with emulation, run: python3 3SA.py --kem ML-KEM-768"
