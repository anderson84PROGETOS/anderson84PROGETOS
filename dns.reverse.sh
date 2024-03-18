#!/bin/bash

# exemplo de uso: para saber o IP:  dig -t mx exemplo.com +short  ====>    ping -c 1 -4 mail.h-email.net   depois copiar ip: 162.55.164

echo ""
# Solicita ao usuário que insira o prefixo do IP
read -p "Digite o prefixo do endereço IP (ex: 192.168.0): " prefixo


echo ""
# Loop através de todos os IPs possíveis na rede
for ip in $(seq 0 255); do
    # Executa o comando 'host' para cada IP na rede, redireciona a saída de erro para /dev/null e filtra a mensagem "not found: 3(NXDOMAIN)"
    host $prefixo.$ip 2>/dev/null | grep -v "not found: 3(NXDOMAIN)" | grep -v ".eu." | grep -v ".re." | grep -v ".net."
done
