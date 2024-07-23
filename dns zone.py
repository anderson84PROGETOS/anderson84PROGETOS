import subprocess

print("""

██████╗ ███╗   ██╗███████╗    ███████╗ ██████╗ ███╗   ██╗███████╗
██╔══██╗████╗  ██║██╔════╝    ╚══███╔╝██╔═══██╗████╗  ██║██╔════╝
██║  ██║██╔██╗ ██║███████╗      ███╔╝ ██║   ██║██╔██╗ ██║█████╗  
██║  ██║██║╚██╗██║╚════██║     ███╔╝  ██║   ██║██║╚██╗██║██╔══╝  
██████╔╝██║ ╚████║███████║    ███████╗╚██████╔╝██║ ╚████║███████╗
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                              
""")

def clean_output(output):
    # Filtra linhas que contêm "Authoritative answers can be found from:" e "Non-authoritative answer:"
    # Remove o ponto final do final do nome do servidor de nomes
    filtered_lines = []
    for line in output.splitlines():
        if not (line.startswith("Authoritative answers can be found from:") or
                line.startswith("Non-authoritative answer:")):
            # Remove o ponto final do final do nome do servidor de nomes
            filtered_lines.append(line.rstrip('.'))
    return "\n".join(filtered_lines)

def dns_zone_transfer():
    # Solicita ao usuário o nome do website
    website = input("\nDigite o nome do website (ex: businesscorp.com.br): ")
    print()
    
    # Executa o comando nslookup para listar os registros NS
    print(f"\nListando registros NS para o website: {website}")
    print()
    nslookup_ns_command = f"nslookup -type=ns {website}"
    nslookup_ns_result = subprocess.run(nslookup_ns_command, shell=True, capture_output=True, text=True)
    cleaned_ns_result = clean_output(nslookup_ns_result.stdout)
    print(cleaned_ns_result)

    # Solicita ao usuário o servidor DNS para a transferência de zona
    dns_server = input("\nDigite o servidor DNS (ex: ns2.businesscorp.com.br): ")

    # Executa o comando nslookup para transferência de zona DNS
    print(f"\nTransferindo zona DNS para: {website} usando o servidor DNS: {dns_server}")
    print()
    nslookup_any_command = f"nslookup -type=any {website} {dns_server}"
    nslookup_any_result = subprocess.run(nslookup_any_command, shell=True, capture_output=True, text=True)
    cleaned_any_result = clean_output(nslookup_any_result.stdout)
    print(cleaned_any_result)

if __name__ == "__main__":
    dns_zone_transfer()
    
input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")    
