import requests
from urllib.parse import urljoin
import re
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███████╗██╗████████╗███████╗███╗   ███╗ █████╗ ██████╗ 
██╔════╝██║╚══██╔══╝██╔════╝████╗ ████║██╔══██╗██╔══██╗
███████╗██║   ██║   █████╗  ██╔████╔██║███████║██████╔╝
╚════██║██║   ██║   ██╔══╝  ██║╚██╔╝██║██╔══██║██╔═══╝ 
███████║██║   ██║   ███████╗██║ ╚═╝ ██║██║  ██║██║     
╚══════╝╚═╝   ╚═╝   ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝     
""")

def get_sitemap(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    sitemap_url = urljoin(url, '/sitemap.xml')
    try:
        response = requests.get(sitemap_url, headers=headers, timeout=10)
        if response.status_code == 200:
            urls = re.findall(r'<loc>(.*?)</loc>', response.text)
            if urls:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n\nForam encontradas: {len(urls)} URLs no sitemap\n")
                global_count = 0
                for idx, u in enumerate(urls, start=1):
                    global_count += 1
                    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n{idx:<4}  =  {u}")

                # Perguntar se o usuário deseja salvar os resultados
                save_choice = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\nDeseja salvar os resultados (s/n): ").strip().lower()
                if save_choice == 's':
                    file_name = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (exemplo: arquivo.txt): ").strip()
                    with open(file_name, 'w') as f:
                        for idx, u in enumerate(urls, start=1):
                            f.write(f"{idx:<4}  =  {u}\n")
                    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nURL salvas com sucesso no arquivo: {file_name}")
            else:
                print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhuma URL encontrada no sitemap.")
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nSitemap não encontrado ({response.status_code})")
    except requests.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao acessar o sitemap: {e}")

if __name__ == "__main__":
    site = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Digite a URL do website: ").strip()
    if not site.startswith("http"):
        site = "https://" + site
    get_sitemap(site)

input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
