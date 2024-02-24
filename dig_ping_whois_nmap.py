import subprocess

print("")

# Prompt the user to input the domain name
domain_name = input("\nDigite o nome do Website: ")

# Gather MX records for the domain
mx_records = subprocess.run(["dig", "mx", domain_name, "+short"], capture_output=True, text=True).stdout.strip()

# Display the MX records
print(f"\nRegistros MX: {domain_name}\n")
print(mx_records)

print("")

# Prompt the user to input the result of 'dig mx'
dig_mx_result = input("Digite o resultado do dig mx: ")

# Extract mail server addresses from MX records
mail_servers = [line.split()[1] for line in mx_records.splitlines()]

# Ping each mail server and display the result
print(f"\nResultados de ping para servidores {domain_name}")
for mail_server in mail_servers:
    ping_result = subprocess.run(["ping", "-c", "1", mail_server], capture_output=True, text=True).stdout.strip()
    print(ping_result)

print("")

# Prompt the user to input the domain name or IP address for WHOIS lookup
whois_input = input("Digite o nome do Website ou endereço IP para a consulta WHOIS: ")

# Perform a WHOIS lookup on the provided domain name or IP address
whois_result = subprocess.run(["whois", whois_input], capture_output=True, text=True).stdout.strip()

# Display the WHOIS result
print(f"\nResultado WHOIS: {whois_input}\n")
print(whois_result)

print("")

# Prompt the user to input the IP block from the WHOIS result
whois_ip_block = input("Digite o Bloco de IP do resultado WHOIS: ")

# Perform an Nmap scan using the WHOIS IP block to list all IPs
nmap_result = subprocess.run(["nmap", "-sL", "-n", whois_ip_block], capture_output=True, text=True).stdout.strip()

# Filter only the IPs from the Nmap result using awk
nmap_filtered_result = subprocess.run(["awk", "/Nmap scan report/{print $NF}"], input=nmap_result, capture_output=True, text=True).stdout.strip()

# Print all IPs in the block
print(f"\nBloco de IP: {whois_ip_block}\n")
print(nmap_filtered_result)

# Ask if the user wants to save the IP block
save_ip_block = input("\nDeseja salvar o bloco de IP? (s/n): ")
if save_ip_block.lower() == 's':
    # Save the filtered IPs to a file
    with open("Bloco_ip.txt", "w") as file:
        file.write(nmap_filtered_result)
    print("\nBloco de IP salvo en: Bloco_ip.txt")

input("\nScanner Terminado [ENTER SAIR]\n")

