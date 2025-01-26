import json
import os
import requests
import sys
import time
from urllib.parse import urlparse
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██╗    ██╗ █████╗ ██╗   ██╗██████╗  █████╗  ██████╗██╗  ██╗    ██╗   ██╗██████╗ ██╗     
██║    ██║██╔══██╗╚██╗ ██╔╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝    ██║   ██║██╔══██╗██║     
██║ █╗ ██║███████║ ╚████╔╝ ██████╔╝███████║██║     █████╔╝     ██║   ██║██████╔╝██║     
██║███╗██║██╔══██║  ╚██╔╝  ██╔══██╗██╔══██║██║     ██╔═██╗     ██║   ██║██╔══██╗██║     
╚███╔███╔╝██║  ██║   ██║   ██████╔╝██║  ██║╚██████╗██║  ██╗    ╚██████╔╝██║  ██║███████╗
 ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═╝╚══════╝
                                                                                                                                                                          
""")

# Configuração de headers para evitar erros 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def fetch_wayback_urls(domain, no_subs):
    subs_wildcard = "" if no_subs else "*."
    url = f"http://web.archive.org/cdx/search/cdx?url={subs_wildcard}{domain}/*&output=json&collapse=urlkey"
    try:
        response = requests.get(url, headers=headers)  # Adicionando os headers
        response.raise_for_status()
        data = response.json()
        return [{"date": item[1], "url": item[2]} for item in data[1:]]  # Skip header
    except Exception as e:
        print(f"\nError fetching Wayback URLs: {e}", file=sys.stderr)
        return []

def fetch_common_crawl_urls(domain, no_subs):
    subs_wildcard = "" if no_subs else "*."
    url = f"http://index.commoncrawl.org/CC-MAIN-2021-10-index?url={subs_wildcard}{domain}/*&output=json"
    urls = []
    try:
        response = requests.get(url, headers=headers, stream=True)  # Adicionando os headers
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                urls.append({"date": data.get("timestamp"), "url": data.get("url")})
    except Exception as e:
        pass
    return urls

def fetch_virustotal_urls(domain):
    api_key = os.getenv("VT_API_KEY")
    if not api_key:
        return []

    url = f"https://www.virustotal.com/vtapi/v2/domain/report?apikey={api_key}&domain={domain}"
    urls = []
    try:
        response = requests.get(url, headers=headers)  # Adicionando os headers
        response.raise_for_status()
        data = response.json()
        for item in data.get("detected_urls", []):
            urls.append({"url": item.get("url")})
    except Exception as e:
        print(f"\nError fetching VirusTotal URLs: {e}", file=sys.stderr)
    return urls

def is_subdomain(url, domain):
    try:
        parsed_url = urlparse(url)
        return parsed_url.hostname and parsed_url.hostname.lower() != domain.lower()
    except Exception:
        return False

def get_versions(url):
    archive_url = f"http://web.archive.org/cdx/search/cdx?url={url}&output=json"
    try:
        response = requests.get(archive_url, headers=headers)  # Adicionando os headers
        response.raise_for_status()
        data = response.json()
        seen = set()
        versions = []
        for entry in data[1:]:
            digest = entry[5]
            if digest not in seen:
                seen.add(digest)
                versions.append(f"https://web.archive.org/web/{entry[1]}if_/{entry[2]}")
        return versions
    except Exception as e:
        print(f"\nError fetching versions: {e}", file=sys.stderr)
        return []

def main():
    domain = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o domínio ou URL do website (ex: example.com): ").strip()

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nEscolha uma das opções abaixo\n")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "1. Incluir datas de captura nas URL")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "2. Excluir subdomínios")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "3. Listar versões arquivadas das URL")
    
    choice = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o número da opção desejada: ").strip()
    print("\n")
    include_dates = choice in ["1"]
    no_subs = choice in ["2"]
    get_versions_option = choice == "3"

    if get_versions_option:
        versions = get_versions(domain)
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nTotal de Versões Arquivadas Encontradas: {len(versions)}\n")  # Usando 'versions' ao invés de 'all_versions'
        
        if versions:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n".join(versions))
            
            # Pergunta ao usuário se deseja salvar as versões arquivadas
            save_versions_option = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDeseja salvar as versões arquivadas? (s/n): ").strip().lower()
            if save_versions_option == 's':
                filename = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar as versões (ex: versões.txt): ").strip()
                try:
                    with open(filename, "w") as file:
                        for version in versions:
                            file.write(f"{version}\n")
                    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nVersões salvas com sucesso em: {filename}")
                except Exception as e:
                    pass
        else:
            print("\nanNenhuma versão arquivada encontrada.")
        return   

    fetch_functions = [
        fetch_wayback_urls,
        fetch_common_crawl_urls,
        fetch_virustotal_urls  # No extra arguments here
    ]

    seen_urls = set()
    all_urls = []

    # Fetch URLs from each function
    for fetch_fn in fetch_functions:
        if fetch_fn == fetch_virustotal_urls:
            results = fetch_fn(domain)  # Only the domain
        else:
            results = fetch_fn(domain, no_subs)  # Pass domain and no_subs

        for result in results:
            url = result.get("url")
            if no_subs and is_subdomain(url, domain):
                continue
            if url not in seen_urls:
                seen_urls.add(url)
                all_urls.append(result)

    # Exibe as URLs encontradas    
    for entry in all_urls:
        if include_dates:
            try:
                date = time.strptime(entry.get("date"), "%Y%m%d%H%M%S")
                formatted_date = time.strftime("%Y-%m-%dT%H:%M:%SZ", date)
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{formatted_date} {entry['url']}")
            except Exception:
                print(entry['url'])
        else:
            print(entry['url'])

    # Exibe o total de URL encontradas
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n\nTotal de URL Encontradas: {len(all_urls)}\n")

    # Pergunta ao usuário se deseja salvar as URLs
    save_option = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDeseja salvar as URLs encontradas? (s/n): ").strip().lower()
    if save_option == 's':
        filename = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o nome do arquivo (ex: arquivo.txt): ").strip()
        try:
            with open(filename, "w") as file:
                for entry in all_urls:
                    if include_dates:
                        try:
                            date = time.strptime(entry.get("date"), "%Y%m%d%H%M%S")
                            formatted_date = time.strftime("%Y-%m-%dT%H:%M:%SZ", date)
                            file.write(f"{formatted_date} {entry['url']}\n")
                        except Exception:
                            file.write(f"{entry['url']}\n")
                    else:
                        file.write(f"{entry['url']}\n")
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nURL salvas com sucesso em: {filename}")
        except Exception as e:
            pass

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")

