import socket
import requests
from bs4 import BeautifulSoup
from ipwhois import IPWhois
from urllib.parse import urljoin, urlparse
from colorama import Fore, Style, init
import ipaddress
import os
import threading
from queue import Queue

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTGREEN_EX + "\nMais Informações Acesse o site: https://ipinfo.io\n")
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """\

███╗   ██╗███████╗████████╗     █████╗ ███████╗███╗   ██╗    ███████╗ ██████╗ █████╗ ███╗   ██╗
████╗  ██║██╔════╝╚══██╔══╝    ██╔══██╗██╔════╝████╗  ██║    ██╔════╝██╔════╝██╔══██╗████╗  ██║
██╔██╗ ██║█████╗     ██║       ███████║███████╗██╔██╗ ██║    ███████╗██║     ███████║██╔██╗ ██║
██║╚██╗██║██╔══╝     ██║       ██╔══██║╚════██║██║╚██╗██║    ╚════██║██║     ██╔══██║██║╚██╗██║
██║ ╚████║███████╗   ██║       ██║  ██║███████║██║ ╚████║    ███████║╚██████╗██║  ██║██║ ╚████║
╚═╝  ╚═══╝╚══════╝   ╚═╝       ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
                                                                                                                                                                                
""")

# Cabeçalhos HTTP para evitar bloqueio por 403
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Função de ping otimizada com threads
def ping_ip(ip, queue):
    # Verifica se o IP está acessível com um ping, mas suprime a saída
    response = os.system(f"ping -n 1 -w 1 {ip} >nul 2>&1")
    if response == 0:
        queue.put(ip)  # Coloca o IP no Queue se estiver acessível

def get_ips_and_asn(domain):
    try:
        # Obter o endereço IPv4 do domínio
        ip = socket.gethostbyname(domain)        
        print(Fore.LIGHTGREEN_EX + f"[+] IP Encontrado: {ip}")

        # Buscar informações do ASN
        obj = IPWhois(ip)
        results = obj.lookup_rdap()
        asn = results.get("asn", "Não encontrado")
        asn_description = results.get("asn_description", "Não encontrado")
        network_info = results.get("network", {})

        print(Fore.LIGHTGREEN_EX + f"[+] AS{asn}")
        print(Fore.LIGHTGREEN_EX + f"[+] Descrição do ASN: {asn_description}")

        # Exibir blocos de IP associados
        cidr = network_info.get("cidr", "Não encontrado")
        name = network_info.get("name", "Não encontrado")
        country = network_info.get("country", "Não encontrado")

        print(Fore.LIGHTCYAN_EX + f"[+] Bloco de IP: {cidr}")
        print(Fore.LIGHTCYAN_EX + f"[+] Nome da Rede: {name}")
        print(Fore.LIGHTCYAN_EX + f"[+] País: {country}")

        # Exibir CIDR e gerar intervalos de IPs
        if cidr != "Não encontrado":
            print(Fore.LIGHTMAGENTA_EX + "\n[+] Intervalo de IP no bloco CIDR\n")
            network = ipaddress.ip_network(cidr, strict=False)
            
            print(Fore.LIGHTGREEN_EX + f"[+] CIDR: {cidr}")
            print(Fore.LIGHTCYAN_EX + "\n\n[+] IP no bloco CIDR (até 100 IP funcionando)")

            # Limite de 100 IP
            queue = Queue()
            threads = []
            ip_count = 0

            for ip in network.hosts():  # Gerar todos os IP dentro do intervalo CIDR
                if ip_count >= 100:
                    break
                thread = threading.Thread(target=ping_ip, args=(str(ip), queue))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # Exibir os IP que estão funcionando
            reachable_ips = []
            while not queue.empty():
                ip = queue.get()
                reachable_ips.append(ip)
                ip_count += 1

            # Mostrar o número de IPs encontrados
            print(Fore.LIGHTMAGENTA_EX + f"\n[+] Total de IP Encontrados e Acessíveis: {len(reachable_ips)}\n")
            for ip in reachable_ips:
                print(Fore.LIGHTGREEN_EX + f"[+] {ip}")

    except Exception as e:
        print(f"[!] Erro ao obter informações do IP e ASN: {e}")

def get_urls(domain):
    try:
        # Construir URL HTTP
        url = f"http://{domain}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        urls = set()

        # Coletar URLs do conteúdo HTML
        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])
            parsed_url = urlparse(full_url)

            # Ignorar URLs repetidas ou inválidas
            if parsed_url.netloc:
                urls.add(full_url)

        print(Fore.LIGHTMAGENTA_EX + f"\n\n[+] URL Encontradas: {len(urls)}")
        for u in urls:
            print(Fore.LIGHTGREEN_EX + f"\n{u}")

    except Exception as e:
        print(f"[!] Erro ao obter URLs: {e}")

def main():
    domain = input(Fore.LIGHTGREEN_EX + "Digite o nome do website (exemplo: exemplo.com): ").strip()
    if not domain:
        print("[!] Por favor, insira um domínio válido.")
        return

    print(Fore.LIGHTMAGENTA_EX + "\n==> Informações de IP e ASN\n")
    get_ips_and_asn(domain)    
    get_urls(domain)

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
