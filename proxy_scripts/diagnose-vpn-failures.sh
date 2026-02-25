#!/bin/bash

# Deep diagnostic for VPN failures

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          VPN Failure Root Cause Analysis                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "=== System Resources ==="
free -h
echo ""
uptime
echo ""

echo "=== CPU and Load ==="
top -bn1 | head -20
echo ""

echo "=== Disk Usage ==="
df -h | grep -E "Filesystem|/dev/"
echo ""

echo "=== OpenVPN Processes ==="
ps aux | grep openvpn | grep -v grep
echo ""
echo "Total OpenVPN processes: $(pgrep -c openvpn)"
echo ""

echo "=== Microsocks Processes ==="
ps aux | grep microsocks | grep -v grep
echo ""
echo "Total microsocks processes: $(pgrep -c microsocks)"
echo ""

echo "=== Network Interfaces ==="
ip addr show | grep -E "^[0-9]+:|inet "
echo ""

echo "=== OpenVPN Logs - Last disconnections ==="
for log in /var/log/protonvpn/*-openvpn.log; do
    if [ -f "$log" ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "File: $(basename $log)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Look for errors and disconnections
        echo "Last errors/warnings:"
        grep -iE "error|warning|disconnect|reset|auth.*fail|timeout|tls.*error" "$log" | tail -10
        
        echo ""
        echo "Last 15 lines of log:"
        tail -15 "$log"
        echo ""
    fi
done

echo "=== Check for keepalive settings ==="
for ovpn in /etc/protonvpn/*.ovpn; do
    if [ -f "$ovpn" ]; then
        echo "File: $(basename $ovpn)"
        grep -iE "keepalive|ping|persist" "$ovpn" || echo "  No keepalive/persistence settings found"
        echo ""
    fi
done

echo "=== System Logs (syslog) - Network/VPN related ==="
if [ -f /var/log/syslog ]; then
    echo "Last network-related entries:"
    grep -iE "network|openvpn|tun[0-9]" /var/log/syslog | tail -20
elif [ -f /var/log/messages ]; then
    echo "Last network-related entries:"
    grep -iE "network|openvpn|tun[0-9]" /var/log/messages | tail -20
else
    echo "No syslog found"
fi
echo ""

echo "=== Kernel Messages (dmesg) - Network interfaces ==="
dmesg | grep -iE "tun|network|link" | tail -15
echo ""

echo "=== Memory usage by OpenVPN ==="
TOTAL_MEM=$(ps aux | grep openvpn | grep -v grep | awk '{sum+=$6} END {print sum}')
if [ -n "$TOTAL_MEM" ]; then
    echo "Total memory used by OpenVPN: $((TOTAL_MEM/1024)) MB"
else
    echo "No OpenVPN processes found"
fi
echo ""

echo "=== Memory usage by microsocks ==="
TOTAL_MEM=$(ps aux | grep microsocks | grep -v grep | awk '{sum+=$6} END {print sum}')
if [ -n "$TOTAL_MEM" ]; then
    echo "Total memory used by microsocks: $((TOTAL_MEM/1024)) MB"
else
    echo "No microsocks processes found"
fi
echo ""

echo "=== Connection uptime ==="
for pid_file in /var/run/openvpn-*.pid; do
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        VPN_NAME=$(basename "$pid_file" .pid | sed 's/openvpn-//')
        if ps -p $PID > /dev/null 2>&1; then
            UPTIME=$(ps -p $PID -o etime= | tr -d ' ')
            echo "  $VPN_NAME (PID $PID): $UPTIME"
        else
            echo "  $VPN_NAME: Process not running (stale PID file)"
        fi
    fi
done
echo ""

echo "=== Routing Tables Status ==="
for i in 100 101 102 103 104 105; do
    echo "Table $i:"
    if ip route show table $i | grep -q "default"; then
        ip route show table $i | head -3
    else
        echo "  No default route"
    fi
done
echo ""

echo "=== iptables mangle rules count ==="
RULE_COUNT=$(iptables -t mangle -L OUTPUT -n | grep -c "owner UID match")
echo "Total mangle rules: $RULE_COUNT (expected: 6)"
echo ""

echo "=== Last Security Monitor checks ==="
if [ -f /var/log/protonvpn/security-monitor.log ]; then
    echo "Last 20 lines:"
    tail -20 /var/log/protonvpn/security-monitor.log
else
    echo "Security monitor log not found"
fi
echo ""

echo "=== Timestamp ==="
date
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Diagnostic Complete                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
