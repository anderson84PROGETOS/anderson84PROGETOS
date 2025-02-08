import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)
# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """   
    ███████╗██╗   ██╗██████╗     ███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗    
    ██╔════╝██║   ██║██╔══██╗    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║    
    ███████╗██║   ██║██████╔╝    ███████╗█████╗  ███████║██████╔╝██║     ███████║    
    ╚════██║██║   ██║██╔══██╗    ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║    
    ███████║╚██████╔╝██████╔╝    ███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║    
    ╚══════╝ ╚═════╝ ╚═════╝     ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝                                                                                   
""")

# Cabeçalhos para evitar erro 403
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.google.com/'
}

def get_crtsh_subdomains(domain):
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {entry['name_value'] for entry in data}
    except requests.RequestException:
        pass
    return set()

def get_rapiddns_subdomains(domain):
    url = f"https://rapiddns.io/subdomain/{domain}?full=1"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            return {a.text.strip() for a in soup.select("td a[href^='http']")}
    except requests.RequestException:
        pass
    return set()

def get_alienvault_subdomains(domain):
    url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {entry['hostname'] for entry in data.get('passive_dns', []) if 'hostname' in entry}
    except requests.RequestException:
        pass
    return set()

def get_threatcrowd_subdomains(domain):
    url = f"https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return set(data.get("subdomains", []))
    except requests.RequestException:
        pass
    return set()

def main():
    domain = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do website: ").strip()
    if not domain:
        print("\nNenhum domínio inserido!")
        return
    
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nBuscando subdomínios para: {domain}\n")

    sources = [
        get_crtsh_subdomains,
        get_rapiddns_subdomains,
        get_alienvault_subdomains,
        get_threatcrowd_subdomains
    ]
    
    subdomains = set()
    for source in sources:
        subdomains.update(source(domain))

    if subdomains:
        for sub in sorted(subdomains):
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"SUBDOMÍNIO ENCONTRADO: {sub}")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nTotal de subdomínios Encontrados: {len(subdomains)}")
        
        # Perguntar se deseja salvar os resultados
        salvar = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDeseja salvar os resultados? (s/n): ").strip().lower()
        if salvar == "s":
            nome_arquivo = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (ex: subdomains.txt): ").strip()
            with open(nome_arquivo, "w") as f:
                for sub in subdomains:
                    f.write(sub + "\n")
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[+] Resultados salvos em: {nome_arquivo}")
        else:
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n[-] Resultados não foram salvos.")
    else:
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n[-] Nenhum subdomínio encontrado.")     

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
