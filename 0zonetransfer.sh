#!/bin/bash

echo "Exemplo: Digite o nome do website: zonetransfer.me "
echo ""
read -p "Digite o nome do website: " domain

echo ""
echo "Lista de registros DNS 👉 $domain"
echo ""

for server in $(host -t ns $domain | cut -d " " -f4); do
  host -l $domain $server
done
