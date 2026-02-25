#!/bin/bash
source /usr/local/bin/multi-vpn-proxy.sh

# Limpiar todo
pkill openvpn
pkill microsocks
sleep 3

# Iniciar SOLO Japan y Netherlands
echo "Iniciando SOLO Japan y Netherlands..."
setup_vpn_proxy "japan" "jp-free-26.protonvpn.udp.ovpn" "" 1084 104 "tun4" &
sleep 8
setup_vpn_proxy "netherlands" "nl-free-164.protonvpn.udp.ovpn" "" 1081 101 "tun1" &
wait

echo ""
echo "Esperando 30 segundos..."
sleep 30

echo ""
echo "Probando conectividad..."
ping -I tun4 -c 3 8.8.8.8
ping -I tun1 -c 3 8.8.8.8
