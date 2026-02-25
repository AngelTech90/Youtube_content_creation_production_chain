#!/bin/bash

# Control script for VPN Security Monitor

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PID_FILE="/var/run/vpn-security-monitor.pid"
LOG_FILE="/var/log/protonvpn/security-monitor.log"

status() {
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        if ps -p ${PID} > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Security monitor is running (PID: ${PID})"
            
            # Show last check
            echo ""
            echo "Last security check:"
            tail -15 "${LOG_FILE}" | grep -A 5 "Starting security check"
            
            return 0
        else
            echo -e "${RED}✗${NC} PID file exists but process not running"
            rm -f "${PID_FILE}"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} Security monitor is not running"
        return 1
    fi
}

start() {
    if status > /dev/null 2>&1; then
        echo "Security monitor already running"
        return 1
    fi
    
    echo "Starting security monitor..."
    /usr/local/bin/vpn-security-monitor.sh --daemon
    sleep 2
    status
}

stop() {
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        echo "Stopping security monitor (PID: ${PID})..."
        kill ${PID} 2>/dev/null
        rm -f "${PID_FILE}"
        sleep 2
        echo "Stopped"
    else
        echo "Security monitor not running"
    fi
}

logs() {
    tail -f "${LOG_FILE}"
}

check_now() {
    echo "Running immediate security check..."
    /usr/local/bin/vpn-security-monitor.sh --once
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 2
        start
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    check)
        check_now
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|check}"
        echo ""
        echo "Commands:"
        echo "  start   - Start security monitor daemon"
        echo "  stop    - Stop security monitor daemon"
        echo "  restart - Restart security monitor"
        echo "  status  - Show monitor status and last check"
        echo "  logs    - Follow security monitor logs"
        echo "  check   - Run immediate security check"
        exit 1
        ;;
esac
