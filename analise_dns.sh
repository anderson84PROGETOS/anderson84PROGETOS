#!/bin/bash

echo ""

# Prompt the user to input the domain name
read -p "Digite o nome do Website: " domain_name

# Gather MX records for the domain
mx_records=$(dig mx $domain_name +short)

# Display the MX records
echo "MX Records for $domain_name:"
echo "$mx_records"

echo ""
# Prompt the user to input the result of 'dig mx'
read -p "Digite o resultado do dig mx: " dig_mx_result

# Extract mail server addresses from MX records
mail_servers=$(echo "$mx_records" | awk '{print $2}')

echo ""
# Ping each mail server and display the result
echo "Ping Results for Mail Servers of $domain_name:"
for mail_server in $mail_servers; do
    ping_result=$(ping -c 1 $mail_server)
    echo "$ping_result"
done

echo ""
# Prompt the user to input the domain name or IP address for WHOIS lookup
read -p "Digite o nome do Website ou endereço IP para a consulta WHOIS: " whois_input

# Perform a WHOIS lookup on the provided domain name or IP address
whois_result=$(whois $whois_input)

# Display the WHOIS result
echo "WHOIS Result for $whois_input:"
echo "$whois_result"

echo ""
# Prompt the user to input the IP block from the WHOIS result
read -p "Digite o Bloco de IP do resultado WHOIS: " whois_ip_block

# Perform an Nmap scan using the WHOIS IP block
nmap_result=$(nmap -sL -n $whois_ip_block | awk '/Nmap scan report/{print $NF}' | tee Bloco_ip.txt )

# Display the list of IPs
echo "IPs associated with $whois_ip_block:"
echo "$nmap_result"
echo ""

read -p "Escan Terminado Sucesso ENTER SAIR" ENTER
echo ""
