#!/bin/bash

#executar: exemplo: ./tcp_scanner.sh tcp google.com 80 443

for porta in `seq $3 $4`;
do
timeout 1 bash -c "</dev/$1/$2/$porta" &>/dev/null && echo "$1/$porta ----> ABERTA " || echo -ne "Escaneando: $porta /$1\e[K\r"
done
