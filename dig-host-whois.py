import os

# Obter informações do MX record
domain = input("\nDigite o nome de domínio para obter informações do MX record: ")
os.system(f"dig {domain} MX +short")

# Obter informações do host
ip_address = input("\nDigite o endereço IP ou nome do host para obter informações: ")
os.system(f"host {ip_address}")

# Obter informações do whois
domain = input("\nDigite o nome de domínio para obter informações do whois: ")
os.system(f"whois {domain}")

input("\ninformações terminada\n")
