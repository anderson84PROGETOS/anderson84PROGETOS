import requests
import concurrent.futures
from urllib.parse import urljoin
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██╗    ██╗███████╗██████╗     ███████╗██╗   ██╗███████╗███████╗
██║    ██║██╔════╝██╔══██╗    ██╔════╝██║   ██║╚══███╔╝╚══███╔╝
██║ █╗ ██║█████╗  ██████╔╝    █████╗  ██║   ██║  ███╔╝   ███╔╝ 
██║███╗██║██╔══╝  ██╔══██╗    ██╔══╝  ██║   ██║ ███╔╝   ███╔╝  
╚███╔███╔╝███████╗██████╔╝    ██║     ╚██████╔╝███████╗███████╗
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═╝      ╚═════╝ ╚══════╝╚══════╝
                                                             
""")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

results = []

def download_wordlist(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Garantir que a requisição tenha sido bem-sucedida
        return response.text.splitlines()
    except requests.RequestException as e:
        print(f"\nOcorreu um erro ao baixar o wordlist: {e}")
        return []

def fuzz_url(base_url, word):
    url = urljoin(base_url, word.strip())
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)  # Timeout menor
        status = response.status_code
        size = len(response.content)

        # Mostrar apenas status 200 e 301
        if status == 200 or status == 301:
            # Determinando o tipo de página
            if size < 1024:
                page_type = "Página bem pequena"  # Menor que 1 KB (1024 bytes)
            elif size < 10240:
                page_type = "Página pequena"  # De 1 KB até 10 KB (1024 - 10240 bytes)
            elif size < 1048576:
                page_type = "Página média"  # De 10 KB até 1 MB (10240 - 1048576 bytes)
            elif size < 10485760:  # Até 10 MB (1048576 - 10485760 bytes)
                page_type = "Página de tamanho normal"
            else:
                page_type = "Página grande"  # Maior que 10 MB (10485760 bytes em diante)

            # Exibindo status 200 com cor verde
            if status == 200:
                result = Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{url:<32}" + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f" Status: {status}, Tamanho: {size / (1024 * 1024):.2f} MB, Tamanho (bytes): {size:<10} Tipo: {page_type}"
                results.append(result)
                print(result)

            # Exibindo status 301 com cor magenta
            elif status == 301:
                result = Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"{url:<32}" + Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f" Status: {status}, Tamanho: {size / (1024 * 1024):.2f} MB, Tamanho (bytes): {size:<10} Tipo: {page_type}"
                results.append(result)
                print(result)

    except requests.RequestException:
        pass

def save_results():
    save_choice = input("\n\nDeseja salvar os resultados? (s/n): ").strip().lower()
    if save_choice == 's':
        filename = input("\nDigite o nome do arquivo para salvar os resultados (ex: arquivo.txt): ").strip()
        if not filename.endswith('.txt'):
            filename += '.txt'
        with open(filename, 'w') as file:
            for result in results:
                file.write(result + '\n')
        print(f"\nResultados salvos em: {filename}")

def main():
    base_url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite a URL do website (ex: https://example.com): ").strip()
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\nCarregando WEB FUZZ DIRB \n")
    if not base_url.endswith("/FUZZ"):
        if not base_url.endswith("/"):
            base_url += "/"
        base_url += "FUZZ"
    
    wordlist_url = 'https://raw.githubusercontent.com/anderson84PROGETOS/anderson84PROGETOS/meu-progetos/lista.txt'
    words = download_wordlist(wordlist_url)
    
    if not words:
        print("\nOcorreu um problema ao baixar o arquivo 'lista.txt'.")
        return

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:  # Aumentando o número de threads
            futures = [executor.submit(fuzz_url, base_url, word) for word in words]
            concurrent.futures.wait(futures)
        
        if not results:
            print("\nNenhum URL retornou o status 200 ou 301.")
        else:
            print(f"\nTotal de URL Encontradas: {len(results)}")

    except Exception as e:
        print(f"\nOcorreu um erro ao processar o arquivo: {e}")

    save_results()

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
