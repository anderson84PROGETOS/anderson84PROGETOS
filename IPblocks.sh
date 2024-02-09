#!/bin/bash

# Definindo códigos de escape ANSI para cor verde e reset
green_color='\033[0;32m'
no_color='\033[0m'

echo ""
# Solicita ao usuário o nome do website
read -p "Digite o nome do website: " website

# Verifica se o argumento foi fornecido
if [ -z "$website" ]; then
    echo -e "${green_color}O nome do website não foi fornecido.${no_color}"
    exit 1
fi
echo ""
# Realiza a consulta MX
echo -e "${green_color}Consultando registros MX para $website${no_color}"
echo ""
dig -t mx $website +short

echo ""
# Solicita ao usuário o nome do Post
read -p "Digite o Post (exemplo: post02.Exemplo.com): " post

echo ""
# Se o usuário não fornecer nenhum valor para o post, exibe uma mensagem de aviso
if [ -z "$post" ]; then
    echo -e "${green_color}O nome do Post não foi fornecido. Não será usado na consulta.${no_color}"
    echo ""    
else
    # Realiza a consulta MX com o nome do Post
    echo -e "${green_color}Consultando registros MX para $post${no_color}"
    echo ""
    post_ip=$(dig +short $post)
    if [ -z "$post_ip" ]; then
        echo -e "${green_color}Não foi possível encontrar o IP para $post.${no_color}"
    else
        echo ""
        echo -e "${green_color}Ping para $post${no_color}"
        echo ""
        ping -4 -c 1 $post_ip
        echo ""
    fi
fi
echo ""
# Realiza o ping para o website original
echo -e "${green_color}Ping para $website${no_color}"
echo ""
ping -4 -c 1 $website

echo ""
# Solicita ao usuário o endereço IP
echo ""
# Solicita ao usuário o endereço IP
echo -ne "${green_color}Digite o endereço IP para a consulta Whois: ${no_color}"
read ip_address
# Verifica se o endereço IP foi fornecido
if [ -z "$ip_address" ]; then
    echo -e "${green_color}O endereço IP não foi fornecido. Consultando Whois para $website...${no_color}"
    whois $website
else
    echo ""	
    echo -e "${green_color}Consultando Whois para o endereço IP $ip_address ${no_color}"
    whois $ip_address
fi

echo ""
echo ""
read -p "➡️ PRESSIONE ENTER PARA SAIR ➡️" SAIR
