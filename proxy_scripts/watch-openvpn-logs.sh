#!/bin/bash

# Watch OpenVPN logs for disconnections in real-time

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ALERT_LOG="/var/log/protonvpn/connection-alerts.log"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          Real-time OpenVPN Connection Monitor                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Monitoring for disconnections, errors, and warnings..."
echo "Press Ctrl+C to stop"
echo ""

# Create alert log if doesn't exist
touch "${ALERT_LOG}"

# Function to log and display alerts
alert() {
    local SEVERITY=$1
    local VPN=$2
    local MESSAGE=$3
    
    case $SEVERITY in
        ERROR)
            COLOR=$RED
            ICON="🚨"
            ;;
        WARN)
            COLOR=$YELLOW
            ICON="⚠️ "
            ;;
        INFO)
            COLOR=$GREEN
            ICON="ℹ️ "
            ;;
    esac
    
    echo -e "${COLOR}${ICON} [$(date '+%H:%M:%S')] ${VPN}: ${MESSAGE}${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${SEVERITY} - ${VPN}: ${MESSAGE}" >> "${ALERT_LOG}"
}

# Monitor all OpenVPN logs
tail -f /var/log/protonvpn/*-openvpn.log 2>/dev/null | while read -r line; do
    # Extract VPN name from log line
    if [[ $line =~ /var/log/protonvpn/([a-z]+)-openvpn\.log ]]; then
        VPN_NAME="${BASH_REMATCH[1]}"
    fi
    
    # Check for different events
    if echo "$line" | grep -qi "Initialization Sequence Completed"; then
        alert "INFO" "$VPN_NAME" "Connected successfully"
    
    elif echo "$line" | grep -qi "connection reset\|Connection reset"; then
        alert "ERROR" "$VPN_NAME" "Connection reset by peer"
    
    elif echo "$line" | grep -qi "auth.*fail\|AUTH_FAILED"; then
        alert "ERROR" "$VPN_NAME" "Authentication failed"
    
    elif echo "$line" | grep -qi "SIGTERM\|process exiting"; then
        alert "WARN" "$VPN_NAME" "Process terminated"
    
    elif echo "$line" | grep -qi "Inactivity timeout"; then
        alert "ERROR" "$VPN_NAME" "Inactivity timeout - no data received"
    
    elif echo "$line" | grep -qi "TLS.*error\|TLS Error"; then
        alert "ERROR" "$VPN_NAME" "TLS encryption error"
    
    elif echo "$line" | grep -qi "link remote.*timeout"; then
        alert "ERROR" "$VPN_NAME" "Remote link timeout"
    
    elif echo "$line" | grep -qiE "RESOLVE.*fail|Cannot resolve"; then
        alert "ERROR" "$VPN_NAME" "DNS resolution failed"
    
    elif echo "$line" | grep -qi "Restart pause.*second"; then
        alert "WARN" "$VPN_NAME" "Attempting to reconnect..."
    
    elif echo "$line" | grep -qi "ERROR\|error"; then
        # Generic error catch
        ERROR_MSG=$(echo "$line" | grep -oP "ERROR:.*" | head -c 60)
        if [ -n "$ERROR_MSG" ]; then
            alert "ERROR" "$VPN_NAME" "$ERROR_MSG"
        fi
    fi
done

