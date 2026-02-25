#!/bin/bash

# Configuración
VPN_DIR="/etc/protonvpn"
LOG_DIR="/var/log/protonvpn"
RUN_DIR="/var/run"
CONFIG_FILE="/etc/protonvpn/vpn-config.conf"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Crear directorios
mkdir -p "${LOG_DIR}"
mkdir -p /etc/iproute2

# Asegurar rt_tables
if [ ! -f /etc/iproute2/rt_tables ]; then
    echo "255     local
254     main
253     default
0       unspec" > /etc/iproute2/rt_tables
fi

# Definición de VPNs con servidores primarios y de respaldo
declare -A VPN_SERVERS=(
    # País:Puerto:Tabla:TunDev:Primario:Respaldo1:Respaldo2
    ["usa"]="1080:100:tun0:us-free-82.protonvpn.udp.ovpn:us-free-80.protonvpn.udp.ovpn:"
    ["netherlands"]="1081:101:tun1:nl-free-164.protonvpn.udp.ovpn::"
    ["norway"]="1082:102:tun2:no-free-7.protonvpn.udp.ovpn::"
    ["mexico"]="1083:103:tun3:mx-free-16.protonvpn.udp.ovpn::"
    ["japan"]="1084:104:tun4:jp-free-26.protonvpn.udp.ovpn::"
    ["canada"]="1085:105:tun5:ca-free-7.protonvpn.udp.ovpn::"
)

# Función para cargar configuración activa
load_active_config() {
    if [ -f "${CONFIG_FILE}" ]; then
        source "${CONFIG_FILE}"
    fi
}

# Función para guardar configuración activa
save_active_config() {
    local VPN_NAME=$1
    local OVPN_FILE=$2
    
    echo "ACTIVE_${VPN_NAME^^}=\"${OVPN_FILE}\"" >> "${CONFIG_FILE}"
}

# Función para obtener gateway VPN
get_vpn_gateway() {
    local TUN_DEV=$1
    local VPN_NAME=$2
    
    sleep 5
    
    local GW=$(grep -oP 'route_gateway \K[\d.]+' "${LOG_DIR}/${VPN_NAME}-openvpn.log" 2>/dev/null | tail -1)
    
    if [ -n "${GW}" ]; then
        echo "${GW}"
        return 0
    fi
    
    GW=$(ip addr show "${TUN_DEV}" | grep -oP 'peer \K[\d.]+' | head -1)
    
    if [ -n "${GW}" ]; then
        echo "${GW}"
        return 0
    fi
    
    echo "10.96.0.1"
}

# Función para verificar si una VPN funciona
test_vpn_connectivity() {
    local TUN_DEV=$1
    local TIMEOUT=${2:-5}
    
    if ! ip addr show "${TUN_DEV}" &>/dev/null; then
        return 1
    fi
    
    if timeout ${TIMEOUT} ping -I "${TUN_DEV}" -c 2 8.8.8.8 &>/dev/null; then
        return 0
    fi
    
    return 1
}

# Función principal de configuración con failover
setup_vpn_proxy() {
    local VPN_NAME=$1
    local PRIMARY_OVPN=$2
    local BACKUP_OVPN=$3
    local PROXY_PORT=$4
    local ROUTE_TABLE=$5
    local TUN_DEV=$6
    local PROXY_UID=$((3000 + ROUTE_TABLE))
    
    echo -e "${BLUE}[${VPN_NAME}]${NC} Configurando VPN y proxy..."
    
    # Crear usuario si no existe
    if ! id "vpnproxy${ROUTE_TABLE}" &>/dev/null; then
        useradd -r -s /bin/false -u ${PROXY_UID} "vpnproxy${ROUTE_TABLE}" 2>/dev/null || true
    fi
    
    # Intentar con servidor primario
    local OVPN_FILE="${PRIMARY_OVPN}"
    local SUCCESS=0
    
    for attempt in 1 2; do
        echo -e "${YELLOW}[${VPN_NAME}]${NC} Intento ${attempt}: ${OVPN_FILE}"
        
        if [ ! -f "${VPN_DIR}/${OVPN_FILE}" ]; then
            echo -e "${RED}[${VPN_NAME}]${NC} Archivo no encontrado: ${OVPN_FILE}"
            
            if [ ${attempt} -eq 1 ] && [ -n "${BACKUP_OVPN}" ]; then
                OVPN_FILE="${BACKUP_OVPN}"
                continue
            else
                return 1
            fi
        fi
        
        # Preparar archivo OpenVPN
        local TEMP_OVPN="/tmp/${VPN_NAME}.ovpn"
        cp "${VPN_DIR}/${OVPN_FILE}" "${TEMP_OVPN}"
        
        sed -i "/^dev /d" "${TEMP_OVPN}"
        echo "dev ${TUN_DEV}" >> "${TEMP_OVPN}"
        echo "pull-filter ignore \"redirect-gateway\"" >> "${TEMP_OVPN}"
        
        # Iniciar OpenVPN
        openvpn --config "${TEMP_OVPN}" \
                --daemon \
                --writepid "${RUN_DIR}/openvpn-${VPN_NAME}.pid" \
                --log "${LOG_DIR}/${VPN_NAME}-openvpn.log" \
                --status "${LOG_DIR}/${VPN_NAME}-status.log" 10 \
                --verb 4
        
        # Esperar interfaz
        echo -e "${YELLOW}[${VPN_NAME}]${NC} Esperando interfaz ${TUN_DEV}..."
        for i in {1..30}; do
            if ip addr show "${TUN_DEV}" &>/dev/null 2>&1; then
                local TUN_IP=$(ip -4 addr show "${TUN_DEV}" | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
                echo -e "${GREEN}[${VPN_NAME}]${NC} Interfaz ${TUN_DEV} lista (${TUN_IP})"
                break
            fi
            sleep 1
            if [ $i -eq 30 ]; then
                echo -e "${RED}[${VPN_NAME}]${NC} Timeout esperando ${TUN_DEV}"
                rm -f "${TEMP_OVPN}"
                
                if [ ${attempt} -eq 1 ] && [ -n "${BACKUP_OVPN}" ]; then
                    kill $(cat "${RUN_DIR}/openvpn-${VPN_NAME}.pid") 2>/dev/null || true
                    rm -f "${RUN_DIR}/openvpn-${VPN_NAME}.pid"
                    OVPN_FILE="${BACKUP_OVPN}"
                    sleep 2
                    continue 2
                else
                    return 1
                fi
            fi
        done
        
        # Probar conectividad
        echo -e "${YELLOW}[${VPN_NAME}]${NC} Probando conectividad..."
        if test_vpn_connectivity "${TUN_DEV}" 10; then
            echo -e "${GREEN}[${VPN_NAME}]${NC} ✓ Conectividad OK con ${OVPN_FILE}"
            SUCCESS=1
            save_active_config "${VPN_NAME}" "${OVPN_FILE}"
            rm -f "${TEMP_OVPN}"
            break
        else
            echo -e "${RED}[${VPN_NAME}]${NC} ✗ Sin conectividad con ${OVPN_FILE}"
            
            if [ ${attempt} -eq 1 ] && [ -n "${BACKUP_OVPN}" ]; then
                kill $(cat "${RUN_DIR}/openvpn-${VPN_NAME}.pid") 2>/dev/null || true
                rm -f "${RUN_DIR}/openvpn-${VPN_NAME}.pid"
                OVPN_FILE="${BACKUP_OVPN}"
                rm -f "${TEMP_OVPN}"
                sleep 3
            else
                rm -f "${TEMP_OVPN}"
                return 1
            fi
        fi
    done
    
    if [ ${SUCCESS} -eq 0 ]; then
        echo -e "${RED}[${VPN_NAME}]${NC} ERROR: No se pudo establecer conexión funcional"
        return 1
    fi
    
    # Obtener gateway
    local VPN_GW=$(get_vpn_gateway "${TUN_DEV}" "${VPN_NAME}")
    echo -e "${GREEN}[${VPN_NAME}]${NC} Gateway: ${VPN_GW}"
    
    # Configurar routing
    configure_routing_v3 "${VPN_NAME}" "${TUN_DEV}" "${ROUTE_TABLE}" "${PROXY_UID}" "${VPN_GW}"
    
    # Iniciar proxy
    echo -e "${GREEN}[${VPN_NAME}]${NC} Iniciando proxy en puerto ${PROXY_PORT}..."
    su -s /bin/bash "vpnproxy${ROUTE_TABLE}" -c "microsocks -i 127.0.0.1 -p ${PROXY_PORT}" &
    echo $! > "${RUN_DIR}/microsocks-${VPN_NAME}.pid"
    
    # Esperar proxy
    for i in {1..30}; do
        if netstat -tln 2>/dev/null | grep -q ":${PROXY_PORT} "; then
            echo -e "${GREEN}[${VPN_NAME}]${NC} ✓ Proxy activo en 127.0.0.1:${PROXY_PORT}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}[${VPN_NAME}]${NC} ✗ Proxy no pudo iniciar"
    return 1
}

# Función de routing mejorada
configure_routing_v3() {
    local VPN_NAME=$1
    local TUN_DEV=$2
    local ROUTE_TABLE=$3
    local PROXY_UID=$4
    local VPN_GW=$5
    
    echo -e "${YELLOW}[${VPN_NAME}]${NC} Configurando policy routing..."
    
    if ! grep -q "^${ROUTE_TABLE} ${VPN_NAME}" /etc/iproute2/rt_tables 2>/dev/null; then
        echo "${ROUTE_TABLE} ${VPN_NAME}" >> /etc/iproute2/rt_tables
    fi
    
    ip route flush table ${ROUTE_TABLE} 2>/dev/null || true
    
    local VPN_SUBNET=$(ip -4 addr show "${TUN_DEV}" | grep -oP '(?<=inet\s)\d+(\.\d+){3}/\d+')
    ip route add ${VPN_SUBNET} dev ${TUN_DEV} scope link table ${ROUTE_TABLE} 2>/dev/null || true
    ip route add default via ${VPN_GW} dev ${TUN_DEV} table ${ROUTE_TABLE} 2>/dev/null || true
    
    while ip rule del fwmark ${ROUTE_TABLE} 2>/dev/null; do :; done
    while ip rule del uidrange ${PROXY_UID}-${PROXY_UID} 2>/dev/null; do :; done
    
    ip rule add uidrange ${PROXY_UID}-${PROXY_UID} table ${ROUTE_TABLE} priority $((10000 + ROUTE_TABLE))
    
    iptables -t mangle -D OUTPUT -m owner --uid-owner ${PROXY_UID} -j MARK --set-mark ${ROUTE_TABLE} 2>/dev/null || true
    iptables -t mangle -A OUTPUT -m owner --uid-owner ${PROXY_UID} -j MARK --set-mark ${ROUTE_TABLE}
    ip rule add fwmark ${ROUTE_TABLE} table ${ROUTE_TABLE} priority $((11000 + ROUTE_TABLE)) 2>/dev/null || true
    
    ip route flush cache 2>/dev/null || true
    
    echo -e "${GREEN}[${VPN_NAME}]${NC} Policy routing configurado"
}

# Función de limpieza
cleanup_vpn() {
    local VPN_NAME=$1
    local ROUTE_TABLE=$2
    local PROXY_PORT=$3
    local PROXY_UID=$((3000 + ROUTE_TABLE))
    
    echo -e "${RED}[${VPN_NAME}]${NC} Deteniendo servicios..."
    
    if [ -f "${RUN_DIR}/microsocks-${VPN_NAME}.pid" ]; then
        kill -9 $(cat "${RUN_DIR}/microsocks-${VPN_NAME}.pid") 2>/dev/null || true
        rm -f "${RUN_DIR}/microsocks-${VPN_NAME}.pid"
    fi
    pkill -9 -U ${PROXY_UID} 2>/dev/null || true
    
    if [ -f "${RUN_DIR}/openvpn-${VPN_NAME}.pid" ]; then
        kill $(cat "${RUN_DIR}/openvpn-${VPN_NAME}.pid") 2>/dev/null || true
        rm -f "${RUN_DIR}/openvpn-${VPN_NAME}.pid"
    fi
    
    iptables -t mangle -D OUTPUT -m owner --uid-owner ${PROXY_UID} -j MARK --set-mark ${ROUTE_TABLE} 2>/dev/null || true
    
    while ip rule del fwmark ${ROUTE_TABLE} 2>/dev/null; do :; done
    while ip rule del uidrange ${PROXY_UID}-${PROXY_UID} 2>/dev/null; do :; done
    ip route flush table ${ROUTE_TABLE} 2>/dev/null || true
}

# Función de estado
show_status() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║          Estado de VPNs y Proxies ProtonVPN                    ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    load_active_config
    
    for VPN_NAME in "${!VPN_SERVERS[@]}"; do
        IFS=':' read -r PROXY_PORT ROUTE_TABLE TUN_DEV PRIMARY BACKUP1 BACKUP2 <<< "${VPN_SERVERS[$VPN_NAME]}"
        local PID_FILE="${RUN_DIR}/openvpn-${VPN_NAME}.pid"
        
        if [ -f "${PID_FILE}" ] && ps -p $(cat "${PID_FILE}") > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} VPN: ${VPN_NAME}"
            
            # Mostrar servidor activo
            local VAR_NAME="ACTIVE_${VPN_NAME^^}"
            if [ -n "${!VAR_NAME}" ]; then
                echo "  ├─ Servidor: ${!VAR_NAME}"
            fi
            
            if ip addr show "${TUN_DEV}" &>/dev/null 2>&1; then
                local TUN_IP=$(ip -4 addr show "${TUN_DEV}" 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
                echo "  ├─ Interfaz: ${TUN_DEV} (${TUN_IP})"
            fi
            
            if netstat -tln 2>/dev/null | grep -q ":${PROXY_PORT} "; then
                echo -e "  └─ Proxy: ${GREEN}activo${NC} en 127.0.0.1:${PROXY_PORT}"
                
                local VPN_IP=$(timeout 10 curl --socks5 127.0.0.1:${PROXY_PORT} -s https://ifconfig.me 2>/dev/null)
                if [ -n "${VPN_IP}" ]; then
                    echo "     └─ IP pública: ${VPN_IP}"
                fi
            else
                echo -e "  └─ Proxy: ${RED}no responde${NC}"
            fi
            echo ""
        fi
    done
    
    echo "─────────────────────────────────────────────────────────────────"
    echo "Conexión normal del sistema (sin proxy):"
    local NORMAL_IP=$(timeout 5 curl -s https://ifconfig.me 2>/dev/null)
    echo "  IP pública: ${NORMAL_IP}"
    echo ""
}

# Main
case "$1" in
    start)
        echo "Iniciando VPNs y proxies con failover automático..."
        echo ""
        
        # Limpiar configuración anterior
        rm -f "${CONFIG_FILE}"
        
        $0 stop 2>/dev/null || true
        sleep 3
        
        # Iniciar cada VPN con sus servidores de respaldo
        for VPN_NAME in "${!VPN_SERVERS[@]}"; do
            IFS=':' read -r PORT TABLE TUN PRIMARY BACKUP1 BACKUP2 <<< "${VPN_SERVERS[$VPN_NAME]}"
            setup_vpn_proxy "${VPN_NAME}" "${PRIMARY}" "${BACKUP1}" "${PORT}" "${TABLE}" "${TUN}" &
            sleep 5
        done
        
        wait
        
        echo ""
        echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✓ Proceso de inicio completado${NC}"
        echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
        echo ""
        sleep 3

        show_status
        ;;
        
    stop)
        echo "Deteniendo todas las VPNs y proxies..."
        
        for VPN_NAME in "${!VPN_SERVERS[@]}"; do
            IFS=':' read -r PORT TABLE TUN PRIMARY BACKUP1 BACKUP2 <<< "${VPN_SERVERS[$VPN_NAME]}"
            cleanup_vpn "${VPN_NAME}" "${TABLE}" "${PORT}"
        done
        
        pkill -f openvpn 2>/dev/null || true
        pkill -f microsocks 2>/dev/null || true 

        rm -f "${CONFIG_FILE}"
        
        echo -e "${GREEN}✓ Todos los servicios detenidos${NC}"
        ;;
        
    restart)
        $0 stop
        sleep 5
        $0 start
        ;;
        
    status)
        show_status
        ;;
        
    test)
        echo "Probando conectividad de cada proxy..."
        echo ""
        
        for VPN_NAME in "${!VPN_SERVERS[@]}"; do
            IFS=':' read -r PORT TABLE TUN PRIMARY BACKUP1 BACKUP2 <<< "${VPN_SERVERS[$VPN_NAME]}"
            echo -n "Probando ${VPN_NAME} (${PORT})... "
            IP=$(timeout 15 curl --socks5 127.0.0.1:${PORT} -s https://ifconfig.me 2>/dev/null)
            if [ -n "${IP}" ]; then
                echo -e "${GREEN}✓${NC} IP: ${IP}"
            else
                echo -e "${RED}✗ Error de conexión${NC}"
            fi
        done
        
        echo ""
        echo "Conexión normal (sin proxy):"
        NORMAL_IP=$(timeout 10 curl -s https://ifconfig.me 2>/dev/null)
        echo "IP: ${NORMAL_IP}"
        ;;
        
    *)
        echo "Uso: $0 {start|stop|restart|status|test}"
        exit 1
        ;;
esac

exit 0
