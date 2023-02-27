#!/bin/bash

#executar o programa exemplo: ./bruter.sh exemplo.com wl.txt

dominio=$1
arquivo=$2
echo ""
echo "[🔎] INICIANDO BRUTE FORCE EM ➡️ $dominio [🔍]"
echo ""
for subd in `cat $2`;
do
	dig -t A $subd.$dominio +short | grep -ve '^$' > /dev/null && echo "[🔎] - ENCONTRADO: $subd.$dominio"
done
