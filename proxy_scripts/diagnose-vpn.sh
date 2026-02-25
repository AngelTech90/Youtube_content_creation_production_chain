#!/bin/bash

echo "=== Diagnóstico detallado de VPNs ==="
echo ""

declare -A VPN_CONFIG=(
    ["switzerland"]="1080:100:tun0"
    ["canada"]="1081:101:tun1"
    ["usa"]="1082:102:tun2"
    ["mexico"]="1083:103:tun3"
    ["japan"]="1084:104:tun4"
)

for VPN_NAME in "${!VPN_CONFIG[@]}"; do
    IFS=':' read -r PORT TABLE TUN <<< "${VPN_CONFIG[$VPN_NAME]}"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "VPN: ${VPN_NAME} (Puerto ${PORT}, Tabla ${TABLE}, ${TUN})"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 1. Verificar proceso OpenVPN
    if pgrep -f "openvpn.*${VPN_NAME}" > /dev/null; then
        echo "✓ OpenVPN está corriendo"
    else
        echo "✗ OpenVPN NO está corriendo"
        continue
    fi
    
    # 2. Verificar interfaz
    if ip addr show "${TUN}" &>/dev/null; then
        IP=$(ip -4 addr show "${TUN}" | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
        echo "✓ Interfaz ${TUN} activa: ${IP}"
    else
        echo "✗ Interfaz ${TUN} NO existe"
        continue
    fi
    
    # 3. Verificar proxy
    if netstat -tln | grep -q ":${PORT} "; then
        echo "✓ Proxy escuchando en ${PORT}"
    else
        echo "✗ Proxy NO está escuchando"
    fi
    
    # 4. Ping test por la interfaz
    echo -n "Test de conectividad (ping 8.8.8.8): "
    if timeout 3 ping -I "${TUN}" -c 1 8.8.8.8 &>/dev/null; then
        echo "✓ OK"
    else
        echo "✗ FALLO"
    fi
    
    # 5. Test de routing
    echo -n "Test de routing (curl por IP): "
    RESULT=$(timeout 5 curl --socks5 127.0.0.1:${PORT} -s http://1.1.1.1/cdn-cgi/trace 2>/dev/null | grep "ip=" | cut -d'=' -f2)
    if [ -n "${RESULT}" ]; then
        echo "✓ IP obtenida: ${RESULT}"
    else
        echo "✗ No se pudo obtener IP"
    fi
    
    # 6. Test DNS
    echo -n "Test DNS (ifconfig.me): "
    RESULT=$(timeout 10 curl --socks5 127.0.0.1:${PORT} -s https://ifconfig.me 2>/dev/null)
    if [ -n "${RESULT}" ]; then
        echo "✓ IP obtenida: ${RESULT}"
    else
        echo "✗ Timeout o error DNS"
    fi
    
    # 7. Ver últimas líneas del log
    echo "Últimas 5 líneas del log:"
    tail -5 /var/log/protonvpn/${VPN_NAME}-openvpn.log 2>/dev/null | sed 's/^/  /'
    
    echo ""
done
