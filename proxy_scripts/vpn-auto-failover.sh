#!/bin/bash

# Sistema de failover automático basado en resultados del test unitario

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

RUN_DIR="/var/run"
LOG_DIR="/var/log/protonvpn"
FAILOVER_LOG="/var/log/protonvpn/failover.log"

# Configuración de VPNs y sus respaldos
declare -A VPN_BACKUPS=(
    ["usa"]="us-free-80.protonvpn.udp.ovpn"
    ["netherlands"]=""
    ["norway"]=""
    ["mexico"]=""
    ["japan"]=""
)

declare -A VPN_PORTS=(
    ["usa"]="1080:100:tun0"
    ["netherlands"]="1081:101:tun1"
    ["norway"]="1082:102:tun2"
    ["mexico"]="1083:103:tun3"
    ["japan"]="1084:104:tun4"
)

log_failover() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${FAILOVER_LOG}"
}

# Función para verificar salud de una VPN
check_vpn_health() {
    local VPN_NAME=$1
    local PORT=$2
    local TUN_DEV=$3
    
    # Test 1: Interfaz existe
    if ! ip addr show "${TUN_DEV}" &>/dev/null; then
        log_failover "UNHEALTHY: ${VPN_NAME} - Interfaz ${TUN_DEV} no existe"
        return 1
    fi
    
    # Test 2: Proxy responde
    if ! netstat -tln 2>/dev/null | grep -q ":${PORT} "; then
        log_failover "UNHEALTHY: ${VPN_NAME} - Proxy no responde en puerto ${PORT}"
        return 1
    fi
    
    # Test 3: Conectividad por el túnel
    if ! timeout 5 ping -I "${TUN_DEV}" -c 2 8.8.8.8 &>/dev/null; then
        log_failover "UNHEALTHY: ${VPN_NAME} - Sin conectividad por ${TUN_DEV}"
        return 1
    fi
    
    # Test 4: Proxy puede obtener IP externa
    local EXTERNAL_IP=$(timeout 10 curl --socks5 127.0.0.1:${PORT} -s https://ifconfig.me 2>/dev/null)
    if [ -z "${EXTERNAL_IP}" ]; then
        log_failover "UNHEALTHY: ${VPN_NAME} - Proxy no puede obtener IP externa"
        return 1
    fi
    
    log_failover "HEALTHY: ${VPN_NAME} - Todo OK (IP: ${EXTERNAL_IP})"
    return 0
}

# Función para hacer failover a servidor de respaldo
do_failover() {
    local VPN_NAME=$1
    local BACKUP_SERVER=$2
    local PORT=$3
    local TABLE=$4
    local TUN_DEV=$5
    
    log_failover "FAILOVER: Intentando cambiar ${VPN_NAME} a servidor de respaldo: ${BACKUP_SERVER}"
    
    if [ -z "${BACKUP_SERVER}" ] || [ ! -f "/etc/protonvpn/${BACKUP_SERVER}" ]; then
        log_failover "FAILOVER FAILED: No hay servidor de respaldo disponible para ${VPN_NAME}"
        return 1
    fi
    
    # Detener VPN actual
    if [ -f "${RUN_DIR}/openvpn-${VPN_NAME}.pid" ]; then
        kill $(cat "${RUN_DIR}/openvpn-${VPN_NAME}.pid") 2>/dev/null
        rm -f "${RUN_DIR}/openvpn-${VPN_NAME}.pid"
    fi
    
    sleep 3
    
    # Iniciar con servidor de respaldo
    /usr/local/bin/multi-vpn-proxy-v3.sh stop-single "${VPN_NAME}" 2>/dev/null || true
    
    # Aquí llamaríamos a setup_vpn_proxy con el servidor de respaldo
    log_failover "FAILOVER: Reiniciando ${VPN_NAME} con ${BACKUP_SERVER}"
    
    # Nota: Esto requeriría exponer la función setup_vpn_proxy o usar el script principal
    # Por ahora, registramos y retornamos
    log_failover "FAILOVER: Se requiere reinicio manual o automático del servicio completo"
    
    return 0
}

# Función principal de monitoreo
monitor_vpns() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║         Monitor de Salud y Failover Automático VPN             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    log_failover "====== Iniciando ciclo de monitoreo ======"
    
    local UNHEALTHY_VPNS=()
    
    for VPN_NAME in "${!VPN_PORTS[@]}"; do
        IFS=':' read -r PORT TABLE TUN_DEV <<< "${VPN_PORTS[$VPN_NAME]}"
        
        echo -n "Verificando ${VPN_NAME}... "
        
        if check_vpn_health "${VPN_NAME}" "${PORT}" "${TUN_DEV}"; then
            echo -e "${GREEN}✓ OK${NC}"
        else
            echo -e "${RED}✗ UNHEALTHY${NC}"
            UNHEALTHY_VPNS+=("${VPN_NAME}")
        fi
    done
    
    echo ""
    
    if [ ${#UNHEALTHY_VPNS[@]} -eq 0 ]; then
        log_failover "RESULTADO: Todas las VPNs están saludables"
        return 0
    else
        log_failover "RESULTADO: ${#UNHEALTHY_VPNS[@]} VPN(s) no saludables: ${UNHEALTHY_VPNS[*]}"
        
        # Intentar failover para VPNs no saludables
        for VPN_NAME in "${UNHEALTHY_VPNS[@]}"; do
            IFS=':' read -r PORT TABLE TUN_DEV <<< "${VPN_PORTS[$VPN_NAME]}"
            BACKUP="${VPN_BACKUPS[$VPN_NAME]}"
            
            if [ -n "${BACKUP}" ]; then
                do_failover "${VPN_NAME}" "${BACKUP}" "${PORT}" "${TABLE}" "${TUN_DEV}"
            else
                log_failover "WARNING: No hay servidor de respaldo configurado para ${VPN_NAME}"
            fi
        done
        
        return 1
    fi
}

# Modo de operación
case "$1" in
    check)
        monitor_vpns
        ;;
        
    watch)
        INTERVAL=${2:-60}
        echo "Iniciando monitor continuo (cada ${INTERVAL} segundos)"
        echo "Presiona Ctrl+C para detener"
        echo ""
        
        while true; do
            monitor_vpns
            echo ""
            echo "Esperando ${INTERVAL} segundos..."
            sleep ${INTERVAL}
            echo ""
        done
        ;;
        
    report)
        echo "╔════════════════════════════════════════════════════════════════╗"
        echo "║              Reporte de Salud de VPNs                          ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        
        if [ ! -f "${FAILOVER_LOG}" ]; then
            echo "No hay datos de monitoreo disponibles"
            exit 0
        fi
        
        echo "Últimas 20 entradas del log:"
        tail -20 "${FAILOVER_LOG}"
        
        echo ""
        echo "Resumen de eventos:"
        echo "  Total de checks: $(grep -c 'HEALTHY\|UNHEALTHY' ${FAILOVER_LOG})"
        echo "  VPNs saludables: $(grep -c 'HEALTHY' ${FAILOVER_LOG})"
        echo "  VPNs no saludables: $(grep -c 'UNHEALTHY' ${FAILOVER_LOG})"
        echo "  Failovers realizados: $(grep -c 'FAILOVER:' ${FAILOVER_LOG})"
        ;;
        
    *)
        echo "Uso: $0 {check|watch [intervalo]|report}"
        echo ""
        echo "Comandos:"
        echo "  check        - Verificar salud de todas las VPNs una vez"
        echo "  watch [seg]  - Monitoreo continuo (default: 60 segundos)"
        echo "  report       - Mostrar reporte de eventos de failover"
        exit 1
        ;;
esac

exit 0
