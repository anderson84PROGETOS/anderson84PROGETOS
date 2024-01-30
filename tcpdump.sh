#!/bin/bash

# Solicitar ao usuário que digite o nome do website
read -p "Digite o Nome do website: " website_url

# Verificar se o usuário forneceu o nome do website
if [ -z "$website_url" ]; then
    echo "Por favor, forneça o Nome do website."
    exit 1
fi

# Nome do arquivo para salvar os resultados
output_file="resultados_tcpdump.txt"
echo ""

# Exibir o cabeçalho da página usando o comando curl
echo -e "\e[32mCabeçalho da página $website_url\e[0m"
curl -I "$website_url"

# Exibir o texto em verde
echo -e "\e[32mtcpdump: listening on eth0, link-type EN10MB (Ethernet), snapshot length 262144 bytes\e[0m"

# Executar o tcpdump com o Nome do website fornecido e exibir os resultados no terminal
sudo tcpdump -nStA host "$website_url" -E algo:secret -v -A | tee "$output_file"

echo ""
# Exibir mensagem indicando que os resultados foram salvos automaticamente
echo -e "\e[32mResultados da varredura foram salvos em $output_file\e[0m"
echo ""
