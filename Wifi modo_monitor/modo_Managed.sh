#!/bin/bash

# Defina o intervalo de tempo em segundos
INTERVALO=5  # 5 segundos entre as execuções

while true; do
    sudo ip link set wlan0 down
    sudo iw dev wlan0 set type managed
    sudo ip link set wlan0 up
    sudo systemctl restart NetworkManager
    
    # Aguardar o usuário pressionar Enter
    read -p "Pressione Enter para continuar..."

    echo "Script terminado. A rede está normal em modo Managed."

    # Espera pelo intervalo antes de repetir
    sleep $INTERVALO
done
