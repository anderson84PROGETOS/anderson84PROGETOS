#!/bin/bash

echo ""

# Exibe a mensagem de solicitação em verde
tput setaf 2  # Define a cor verde 2
read -p "Digite o nome ou a URL do website: " website
tput sgr0  # Reseta a cor de volta para a padrão

echo ""

# Captura as URLs
urls=$(curl -L -s "$website" \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0" \
    -H "Accept-Language: en-US,en;q=0.5" \
    -H "Connection: keep-alive" \
    -H "Upgrade-Insecure-Requests: 1" \
    -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8" \
    -H "Referer: https://google.com" \
    -H "Cache-Control: no-cache" \
    -b "cookies.txt" \
    --compressed \
    -k | grep -Poi '(http|https)://[^"]+' | sort -u)

# Exibe as URLs em azul
tput setaf 6  # Define a cor azul 4 ou    6 azul Fraco

# Exibe as URL numeradas
count=0

while IFS= read -r url; do
    count=$((count + 1))
    echo "$count = $url"
done <<< "$urls"

tput sgr0  # Reseta a cor de volta para a padrão

# Conta e exibe o total de URLs encontradas
url_count=$(echo "$urls" | wc -l)
echo ""

# Exibe a mensagem de solicitação em Amarelo
tput setaf 3  # Define a cor verde 3
echo "Total de URL Encontradas: $url_count"
tput sgr0  # Reseta a cor de volta para a padrão
echo ""
echo ""

# Exibe a mensagem de saída em vermelho usando tput
tput setaf 1  # Define a cor vermelha 1
read -p "PRESSIONE ENTER PARA SAIR" ENTER
tput sgr0  # Reseta a cor de volta para a padrão
