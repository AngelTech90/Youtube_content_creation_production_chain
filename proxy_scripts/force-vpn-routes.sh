#!/bin/bash

echo "Forzando rutas para VPNs que no tienen conectividad..."

declare -A BROKEN_VPNS=(
    ["tun0"]="100:switzerland:ch-free-8"
    ["tun1"]="101:canada:ca-free-7"
    ["tun2"]="102:usa:us-free-80"
)

for TUN_DEV in "${!BROKEN_VPNS[@]}"; do
    IFS=':' read -r TABLE VPN_NAME SERVER <<< "${BROKEN_VPNS[$TUN_DEV]}"
    
    echo ""
    echo "=== Reparando ${VPN_NAME} (${TUN_DEV}) ==="
    
    # Obtener IP local
    LOCAL_IP=$(ip -4 addr show "${TUN_DEV}" 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
    
    if [ -z "${LOCAL_IP}" ]; then
        echo "✗ ${TUN_DEV} no existe o no tiene IP"
        continue
    fi
    
    echo "IP local: ${LOCAL_IP}"
    
    # Obtener información de la red desde el log de OpenVPN
    LOG_FILE="/var/log/protonvpn/${VPN_NAME}-openvpn.log"
    
    # Buscar el remote gateway en el log
    REMOTE_GW=$(grep -oP 'remote.*?(\d+\.\d+\.\d+\.\d+)' "${LOG_FILE}" | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1)
    echo "Servidor remoto: ${REMOTE_GW}"
    
    # Obtener la interfaz física de salida (para no romper la conexión al servidor VPN)
    PHYSICAL_DEV=$(ip route get ${REMOTE_GW} | grep -oP 'dev \K\S+')
    PHYSICAL_GW=$(ip route get ${REMOTE_GW} | grep -oP 'via \K[\d.]+')
    
    echo "Interfaz física: ${PHYSICAL_DEV}, Gateway físico: ${PHYSICAL_GW}"
    
    # 1. Asegurar que la ruta al servidor VPN está protegida (no va por el túnel)
    ip route add ${REMOTE_GW}/32 via ${PHYSICAL_GW} dev ${PHYSICAL_DEV} 2>/dev/null || true
    
    # 2. El gateway del túnel normalmente es .1 en la subred 10.96.0.0/16
    TUNNEL_GW="10.96.0.1"
    
    # 3. Agregar ruta por defecto en la tabla personalizada
    ip route flush table ${TABLE}
    ip route add ${REMOTE_GW}/32 via ${PHYSICAL_GW} dev ${PHYSICAL_DEV} table ${TABLE} 2>/dev/null || true
    ip route add 10.96.0.0/16 dev ${TUN_DEV} scope link table ${TABLE} 2>/dev/null || true
    ip route add default via ${TUNNEL_GW} dev ${TUN_DEV} table ${TABLE} 2>/dev/null || true
    
    echo "Rutas agregadas a tabla ${TABLE}"
    
    # 4. Verificar con ping
    echo -n "Probando ping... "
    if timeout 3 ping -I ${TUN_DEV} -c 1 8.8.8.8 &>/dev/null; then
        echo "✓ FUNCIONA"
    else
        echo "✗ Sigue fallando - probando ruta directa"
        
        # Intentar sin gateway específico
        ip route flush table ${TABLE}
        ip route add ${REMOTE_GW}/32 via ${PHYSICAL_GW} dev ${PHYSICAL_DEV} table ${TABLE} 2>/dev/null || true
        ip route add default dev ${TUN_DEV} table ${TABLE} 2>/dev/null || true
        
        if timeout 3 ping -I ${TUN_DEV} -c 1 8.8.8.8 &>/dev/null; then
            echo "✓ Funciona con ruta directa"
        else
            echo "✗ Aún falla - puede ser problema del servidor"
        fi
    fi
done

echo ""
echo "Flushing route cache..."
ip route flush cache

echo ""
echo "=== Resumen de tablas de ruteo ==="
for i in 100 101 102; do
    echo "Tabla $i:"
    ip route show table $i
done
