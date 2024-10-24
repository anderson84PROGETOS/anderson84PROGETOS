import subprocess
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

print("""

██╗    ██╗██╗  ██╗ █████╗ ████████╗██╗    ██╗███████╗██████╗ 
██║    ██║██║  ██║██╔══██╗╚══██╔══╝██║    ██║██╔════╝██╔══██╗
██║ █╗ ██║███████║███████║   ██║   ██║ █╗ ██║█████╗  ██████╔╝
██║███╗██║██╔══██║██╔══██║   ██║   ██║███╗██║██╔══╝  ██╔══██╗
╚███╔███╔╝██║  ██║██║  ██║   ██║   ╚███╔███╔╝███████╗██████╔╝
 ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚══╝╚══╝ ╚══════╝╚═════╝ 
                            
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

def obter_informacoes_website(endereco):
    try:
        resposta = requests.get(f"http://ip-api.com/json/{endereco}", headers={'User-Agent': 'Mozilla/5.0'})
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados['status'] == 'success':
                print(f"Country : {dados['country']}")
                print(f"Company : {dados['isp']}")
                print(f"\nWeb IP  : {dados['query']}")

                # Obtém e exibe endereços IPv4
                ipv4_addresses = get_ipv4_addresses(endereco)
                if ipv4_addresses:
                    
                    for ipv4_address in ipv4_addresses:
                        print("Web IP  :",ipv4_address)
                else:
                    print("Nenhum Endereço IPv4 encontrado.")
            else:
                print(f"Erro ao obter informações do site: {dados['message']}")
        else:
            print(f"Erro ao consultar serviço para informações do site: Código {resposta.status_code}")
    except Exception as e:
        print(f"Erro ao obter informações do site: {str(e)}")

def capturar_pacotes(url):
    try:
        response = requests.head(url)
        headers = response.headers
        print(f"\n\n\nCabeçalhos HTTP para: {url}\n")
        for header, value in headers.items():
            print(f"{header}: {value}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao tentar extrair cabeçalhos HTTP da URL: {e}")

def obter_informacoes_do_site(alvo):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

        # Faz a requisição HTTP para obter as informações da página
        response = requests.get(alvo, headers=headers)
        if response.status_code == 200:
            print(f"\n\n\nRelatório WhatWeb para: {response.url}\n")
            print(f"Status  : {response.status_code} {response.reason}")

            # Extrai o título da página
            soup = BeautifulSoup(response.text, 'html.parser')
            titulo = soup.title.string if soup.title else "Nenhum título encontrado"
            print(f"Título  : {titulo}")

            # Exibe as informações do site obtidas pela função obter_informacoes_website
            exibir_ipv4(alvo)

            # Captura e exibe os cabeçalhos HTTP
            capturar_pacotes(alvo)

        else:
            print(f"Falha ao obter informações de {alvo}. Código de status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Ocorreu um erro: {e}")

def exibir_ipv4(site):
    # Remove o protocolo 'http://' ou 'https://' da URL para obter apenas o domínio
    if site.startswith(('http://', 'https://')):
        site = site.split('//')[1]

    # Chama a função para obter informações do site, incluindo o endereço IP
    obter_informacoes_website(site)

# Exemplo de uso:
if __name__ == "__main__":
    alvo = input("\nDigite a URL do website: ").strip()
    obter_informacoes_do_site(alvo)

    input("\n\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
