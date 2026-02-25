#!/bin/bash

# Test unitario para sistema de VPNs
# Verifica servidores, conectividad, routing, y proxies

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

VPN_DIR="/etc/protonvpn"
LOG_DIR="/var/log/protonvpn"
TEST_LOG="/tmp/vpn-test-$(date +%Y%m%d-%H%M%S).log"

TESTS_PASSED=0
TESTS_FAILED=0

# Función para registrar resultados
log_test() {
    echo "$1" | tee -a "${TEST_LOG}"
}

# Función de test individual
run_test() {
    local TEST_NAME=$1
    local TEST_CMD=$2
    
    echo -n "TEST: ${TEST_NAME}... "
    
    if eval "${TEST_CMD}" &>>"${TEST_LOG}"; then
        echo -e "${GREEN}PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              Test Unitario de Sistema VPN                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Log del test: ${TEST_LOG}"
echo ""

# ========================================
# SECCIÓN 1: Tests de Prerequisitos
# ========================================
echo "═══ SECCIÓN 1: Prerequisitos ═══"

run_test "Directorio de VPNs existe" "[ -d '${VPN_DIR}' ]"
run_test "Directorio de logs existe" "[ -d '${LOG_DIR}' ]"
run_test "OpenVPN instalado" "which openvpn"
run_test "microsocks instalado" "which microsocks"
run_test "iptables disponible" "which iptables"
run_test "iproute2 disponible" "which ip"

echo ""

# ========================================
# SECCIÓN 2: Tests de Archivos de Configuración
# ========================================
echo "═══ SECCIÓN 2: Archivos de Configuración ═══"

declare -A REQUIRED_FILES=(
    ["us-free-82.protonvpn.udp.ovpn"]="USA"
    ["nl-free-164.protonvpn.udp.ovpn"]="Netherlands"
    ["no-free-7.protonvpn.udp.ovpn"]="Norway"
    ["mx-free-16.protonvpn.udp.ovpn"]="Mexico"
    ["jp-free-26.protonvpn.udp.ovpn"]="Japan"
)

for FILE in "${!REQUIRED_FILES[@]}"; do
    COUNTRY="${REQUIRED_FILES[$FILE]}"
    run_test "Archivo ${COUNTRY} existe" "[ -f '${VPN_DIR}/${FILE}' ]"
    
    if [ -f "${VPN_DIR}/${FILE}" ]; then
        run_test "Archivo ${COUNTRY} tiene credenciales" "grep -q 'auth-user-pass' '${VPN_DIR}/${FILE}'"
    fi
done

run_test "Archivo de credenciales existe" "[ -f '${VPN_DIR}/credentials.txt' ]"
run_test "Archivo de credenciales es legible" "[ -r '${VPN_DIR}/credentials.txt' ]"

echo ""

# ========================================
# SECCIÓN 3: Tests de Conectividad de Servidores
# ========================================
echo "═══ SECCIÓN 3: Conectividad de Servidores ═══"

for FILE in "${!REQUIRED_FILES[@]}"; do
    if [ -f "${VPN_DIR}/${FILE}" ]; then
        COUNTRY="${REQUIRED_FILES[$FILE]}"
        SERVER=$(grep "^remote " "${VPN_DIR}/${FILE}" | head -1 | awk '{print $2}')
        PORT=$(grep "^remote " "${VPN_DIR}/${FILE}" | head -1 | awk '{print $3}')
        
        echo -n "TEST: Servidor ${COUNTRY} (${SERVER}:${PORT}) responde... "
        
        if timeout 5 nc -zv ${SERVER} ${PORT} &>>"${TEST_LOG}"; then
            echo -e "${GREEN}PASS${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}FAIL${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
done

echo ""

# ========================================
# SECCIÓN 4: Tests de Sistema en Ejecución
# ========================================
echo "═══ SECCIÓN 4: Sistema en Ejecución ═══"

declare -A ACTIVE_VPNS=(
    ["tun0"]="usa:1080"
    ["tun1"]="netherlands:1081"
    ["tun2"]="norway:1082"
    ["tun3"]="mexico:1083"
    ["tun4"]="japan:1084"
)

for TUN_DEV in "${!ACTIVE_VPNS[@]}"; do
    IFS=':' read -r VPN_NAME PORT <<< "${ACTIVE_VPNS[$TUN_DEV]}"
    
    run_test "Interfaz ${TUN_DEV} existe" "ip addr show ${TUN_DEV} &>/dev/null"
    
    if ip addr show ${TUN_DEV} &>/dev/null; then
        run_test "Interfaz ${TUN_DEV} tiene IP" "ip -4 addr show ${TUN_DEV} | grep -q 'inet '"
        run_test "Interfaz ${TUN_DEV} ping funciona" "timeout 5 ping -I ${TUN_DEV} -c 2 8.8.8.8 &>/dev/null"
    fi
    
    run_test "Proxy ${VPN_NAME} escuchando en ${PORT}" "netstat -tln 2>/dev/null | grep -q ':${PORT} '"
    
    if netstat -tln 2>/dev/null | grep -q ":${PORT} "; then
        echo -n "TEST: Proxy ${VPN_NAME} obtiene IP externa... "
        EXTERNAL_IP=$(timeout 15 curl --socks5 127.0.0.1:${PORT} -s https://ifconfig.me 2>/dev/null)
        
        if [ -n "${EXTERNAL_IP}" ]; then
            echo -e "${GREEN}PASS${NC} (IP: ${EXTERNAL_IP})"
            log_test "Proxy ${VPN_NAME}: IP externa = ${EXTERNAL_IP}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}FAIL${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
done

echo ""

# ========================================
# SECCIÓN 5: Tests de Routing
# ========================================
echo "═══ SECCIÓN 5: Policy Routing ═══"

for TABLE_ID in 100 101 102 103 104; do
    run_test "Tabla de ruteo ${TABLE_ID} existe" "ip route show table ${TABLE_ID} | grep -q 'default'"
    run_test "Regla de ruteo para tabla ${TABLE_ID}" "ip rule list | grep -q 'lookup.*${TABLE_ID}'"
done

echo ""

# ========================================
# SECCIÓN 6: Tests de Firewall
# ========================================
echo "═══ SECCIÓN 6: Reglas de Firewall ═══"

for UID in 3100 3101 3102 3103 3104; do
    run_test "Regla iptables para UID ${UID}" "iptables -t mangle -L OUTPUT -n | grep -q 'owner UID match ${UID}'"
done

echo ""

# ========================================
# SECCIÓN 7: Tests de Procesos
# ========================================
echo "═══ SECCIÓN 7: Procesos del Sistema ═══"

OPENVPN_COUNT=$(pgrep -f openvpn | wc -l)
MICROSOCKS_COUNT=$(pgrep microsocks | wc -l)

echo -n "TEST: Procesos OpenVPN corriendo... "
if [ ${OPENVPN_COUNT} -ge 1 ]; then
    echo -e "${GREEN}PASS${NC} (${OPENVPN_COUNT} procesos)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}FAIL${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo -n "TEST: Procesos microsocks corriendo... "
if [ ${MICROSOCKS_COUNT} -ge 1 ]; then
    echo -e "${GREEN}PASS${NC} (${MICROSOCKS_COUNT} procesos)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}FAIL${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""

# ========================================
# RESUMEN FINAL
# ========================================
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                      RESUMEN DE TESTS                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "Tests ejecutados: $((TESTS_PASSED + TESTS_FAILED))"
echo -e "${GREEN}Tests pasados: ${TESTS_PASSED}${NC}"
echo -e "${RED}Tests fallados: ${TESTS_FAILED}${NC}"
echo ""

if [ ${TESTS_FAILED} -eq 0 ]; then
    echo -e "${GREEN}✓ TODOS LOS TESTS PASARON${NC}"
    EXIT_CODE=0
else
    echo -e "${RED}✗ ALGUNOS TESTS FALLARON${NC}"
    echo "Ver detalles en: ${TEST_LOG}"
    EXIT_CODE=1
fi

echo ""

# Generar reporte JSON
cat > "/tmp/vpn-test-results.json" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "total_tests": $((TESTS_PASSED + TESTS_FAILED)),
  "passed": ${TESTS_PASSED},
  "failed": ${TESTS_FAILED},
  "success_rate": $(echo "scale=2; ${TESTS_PASSED} * 100 / $((TESTS_PASSED + TESTS_FAILED))" | bc)%,
  "log_file": "${TEST_LOG}"
}
EOF

echo "Reporte JSON generado: /tmp/vpn-test-results.json"

exit ${EXIT_CODE}
