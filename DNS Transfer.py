import subprocess
import requests
import re

print("""


██████╗ ███╗   ██╗███████╗    ████████╗██████╗  █████╗ ███╗   ██╗███████╗███████╗███████╗██████╗ 
██╔══██╗████╗  ██║██╔════╝    ╚══██╔══╝██╔══██╗██╔══██╗████╗  ██║██╔════╝██╔════╝██╔════╝██╔══██╗
██║  ██║██╔██╗ ██║███████╗       ██║   ██████╔╝███████║██╔██╗ ██║███████╗█████╗  █████╗  ██████╔╝
██║  ██║██║╚██╗██║╚════██║       ██║   ██╔══██╗██╔══██║██║╚██╗██║╚════██║██╔══╝  ██╔══╝  ██╔══██╗
██████╔╝██║ ╚████║███████║       ██║   ██║  ██║██║  ██║██║ ╚████║███████║██║     ███████╗██║  ██║
╚═════╝ ╚═╝  ╚═══╝╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                                                                                                              
""")

def get_ipv4_addresses(site):
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    output_list_dns = []
    for server in servers:
        output = subprocess.run(['nslookup', '-type=A', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    ipv4_addresses = []
    for output in output_list_dns:
        ipv4_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
        ipv4_addresses.extend(ipv4_matches)

    ipv4_addresses = list(set(ipv4_addresses))
    return ipv4_addresses

def exibir_ipv4(site):
    ipv4_addresses = get_ipv4_addresses(site)
    if ipv4_addresses:
        print("\n\n========================================== Endereços IPv4 Encontrados =====================================\n\n\n")
        for ipv4_address in ipv4_addresses:
            print(ipv4_address)
    else:
        print("\nNenhum Endereço IPv4 encontrado.")

def obter_informacoes_website(endereco):
    try:
        resposta = requests.get(f"http://ip-api.com/json/{endereco}", headers={'User-Agent': 'Mozilla/5.0'})
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados['status'] == 'success':
                print("\n\n\n\n========================================== Informações do Website ==========================================\n\n\n")
                print(f"TECNOLOGIA: {dados['isp']}")
                print(f"\nIP: {dados['query']}\n")
            else:
                print(f"Erro ao obter informações do site: {dados['message']}")
        else:
            print(f"Erro ao consultar serviço para informações do site: Código {resposta.status_code}")
    except Exception as e:
        print(f"Erro ao obter informações do site: {str(e)}")

def dns_transfer(site):
    print("\n\n\n========================================== Transferência de Zona DNS =========================================\n")
    # Executa o comando 'nslookup' e captura a saída
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    
    # Divide a saída em linhas e extrai os servidores DNS
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]
    
    # Conjunto para armazenar e verificar duplicatas de saída
    unique_outputs = set()
    
    # Itera sobre cada servidor DNS e executa o comando 'nslookup -type=any'
    for server in servers:
        output = subprocess.run(['nslookup', '-type=any', site, server], capture_output=True, text=True)
        # Verifica se a saída já foi armazenada
        if output.stdout not in unique_outputs:
            unique_outputs.add(output.stdout)
    
    # Imprime a saída única do nslookup na tela
    for output in unique_outputs:
        print(output)

# Obter e exibir endereços IPv4 antes de solicitar a URL do usuário
url = input("\nDigite a URL do website: ")
site = url.replace('http://', '').replace('https://', '').split('/')[0]

exibir_ipv4(site)

# Obter informações do website
obter_informacoes_website(site)

# Executar a função de transferência de zona DNS
dns_transfer(site)

input("\n\n🎯============ PRESSIONE ENTER PARA SAIR ============🎯\n")
