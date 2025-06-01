#!/bin/bash

# Verifica se o usuário é root
if [ "$(id -u)" -ne "0" ]; then
  echo "Este script deve ser executado como root." 1>&2
  exit 1
fi

# Define a interface de rede
INTERFACE="wlan0"  # Substitua pelo nome da sua interface monitor

# Inicia o airodump-ng para escanear redes Wi-Fi
echo "Iniciando o escaneamento de redes Wi-Fi..."
sudo airodump-ng $INTERFACE

echo ""
# Finaliza o script
echo "Escaneamento concluído."
