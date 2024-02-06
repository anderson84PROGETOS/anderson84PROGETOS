#!/bin/bash

# Verifica se o netcat está instalado
if ! command -v ncat &> /dev/null; then
    echo -e "\e[31mNetcat não está instalado. Por favor, instale-o para continuar.\e[0m"
    exit 1
fi

echo ""
# Solicita ao usuário o nome do site
read -p "Digite o nome do site: " site

# Verifica se o nome do site foi fornecido
if [[ -z "$site" ]]; then
    echo -e "\e[31mVocê não forneceu um nome de site válido. Saindo...\e[0m"
    exit 1
fi

# Define as portas
portas=(80 443)
echo ""
# Loop pelas portas e envia a solicitação HEAD para cada uma
for porta in "${portas[@]}"; do
    echo -e "\e[32mEnviando solicitação 🟢 HEAD 🟢 para $site na porta $porta...\e[0m"
    echo ""
    echo -e "HEAD / HTTP/1.1\r\nHost: $site\r\nConnection: close\r\n\r\n" | nc -w 5 $site $porta
    echo ""
done

echo -e "\e[31mSaindo do script. Obrigado por usar🚩  [🎯 APERTE ENTER PARA SAIR 🎯]\e[0m"
read -r
