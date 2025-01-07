import os
import socket
import threading
from queue import Queue
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import ipaddress
from colorama import Fore, Style, init

# Inicializar colorama
init(autoreset=True)
print(Fore.LIGHTGREEN_EX + "\nMais Informações Acesse o site: https://ipinfo.io  PARA SABER O ASN: AS20940\n")
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

███╗   ██╗███████╗████████╗    ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗      █████╗ ███████╗███╗   ██╗
████╗  ██║██╔════╝╚══██╔══╝    ██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗    ██╔══██╗██╔════╝████╗  ██║
██╔██╗ ██║█████╗     ██║       █████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝    ███████║███████╗██╔██╗ ██║
██║╚██╗██║██╔══╝     ██║       ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗    ██╔══██║╚════██║██║╚██╗██║
██║ ╚████║███████╗   ██║       ██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║    ██║  ██║███████║██║ ╚████║
╚═╝  ╚═══╝╚══════╝   ╚═╝       ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝
                                                                                                        
""")

# Configurar cabeçalhos HTTP
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Função para realizar ping
def ping_ip(ip, queue):
    response = os.system(f"ping -n 1 -w 1000 {ip} > nul")
    if response == 0:
        queue.put(ip)

# Obter informações de IP e ASN
def get_ips_and_asn(domain):
    try:
        ip = socket.gethostbyname(domain)
        

        # Obter informações do IP usando API do ipinfo.io
        api_url = f"https://ipinfo.io/{ip}/json"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            name = data.get("org", "Desconhecido").split(" ", 1)[-1]
            asn_description = data.get("org", "Desconhecido")
            print(Fore.LIGHTGREEN_EX + f"[+] Nome da Rede: {name}")
            print(Fore.LIGHTGREEN_EX + f"[+] Descrição do ASN: {asn_description}\n")
            print(Fore.LIGHTCYAN_EX + f"[+] IP Encontrado: {ip}")
        else:
            print(Fore.RED + f"[!] Não foi possível obter informações do ASN para o IP {ip}.")

        # Criar um bloco CIDR baseado no IP
        cidr = f"{ip}/24"
        print(Fore.LIGHTCYAN_EX + f"[+] Bloco de IP: {cidr}")
        network = ipaddress.ip_network(cidr, strict=False)

        print(Fore.LIGHTMAGENTA_EX + "\n[+] IP no bloco CIDR (máximo 200)")
        queue = Queue()
        threads = []

        for i, ip in enumerate(network.hosts()):
            if i >= 200:
                break
            thread = threading.Thread(target=ping_ip, args=(str(ip), queue))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        reachable_ips = []
        while not queue.empty():
            reachable_ips.append(queue.get())

        print(Fore.LIGHTGREEN_EX + f"\n[+] Total de IP Acessíveis: {len(reachable_ips)}\n")
        for ip in reachable_ips:
            print(Fore.LIGHTWHITE_EX + f"{ip}")
    except Exception as e:
        print(Fore.RED + f"[!] Erro ao obter informações de IP: {e}")

# Obter URLs de um site
def get_urls(domain):
    try:
        url = f"http://{domain}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        urls = set(urljoin(url, link['href']) for link in soup.find_all('a', href=True))

        print(Fore.LIGHTGREEN_EX + f"\n[+] URLs Encontradas: {len(urls)}\n")
        for u in urls:
            print(Fore.LIGHTYELLOW_EX + f"\n{u}")
    except Exception as e:
        print(Fore.RED + f"[!] Erro ao obter URLs: {e}")

# Função principal
def main():
    domain = input(Fore.LIGHTGREEN_EX + "Digite o nome do website (exemplo: exemplo.com): ").strip()
    if not domain:
        print(Fore.RED + "[!] Por favor, insira um domínio válido.")
        return

    print(Fore.LIGHTMAGENTA_EX + "\n==> Informações de IP e Bloco de Rede\n")
    get_ips_and_asn(domain)
    print(Fore.LIGHTMAGENTA_EX + "\n==> URL do site")
    get_urls(domain)

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
