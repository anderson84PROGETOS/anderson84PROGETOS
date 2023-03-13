#!/bin/bash
cat lista.txt | while read hostname; do
ip=$(echo $hostname | awk '{print $2}')
porta=$(echo $hostname | awk '{print $3}')
nmap -T5 -sS -p$porta $ip | grep -i open >/dev/null && echo "socks4  $ip $porta" >> proxychains.txt || echo -ne "Testando: $ip $porta\e[K\r"
done
