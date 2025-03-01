import requests
import os
import sys
import socket
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██╗  ██╗████████╗████████╗██████╗ ██╗  ██╗    ██╗    ██╗███████╗██████╗ 
██║  ██║╚══██╔══╝╚══██╔══╝██╔══██╗╚██╗██╔╝    ██║    ██║██╔════╝██╔══██╗
███████║   ██║      ██║   ██████╔╝ ╚███╔╝     ██║ █╗ ██║█████╗  ██████╔╝
██╔══██║   ██║      ██║   ██╔═══╝  ██╔██╗     ██║███╗██║██╔══╝  ██╔══██╗
██║  ██║   ██║      ██║   ██║     ██╔╝ ██╗    ╚███╔███╔╝███████╗██████╔╝
╚═╝  ╚═╝   ╚═╝      ╚═╝   ╚═╝     ╚═╝  ╚═╝     ╚══╝╚══╝ ╚══════╝╚═════╝ 
                                                                                                                                                                                                                                  
""")

# Cabeçalhos com User-Agent personalizado
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Função para resolver o IP de um domínio
def get_ip(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return "N/A"

# Função para verificar um único URL
def check_url(url, timeout=5, verbose=False):
    try:
        if not urlparse(url).scheme:
            url = f"http://{url}"
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc or parsed_url.path  # Extrai o domínio

        response = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers)
        
        result = {
            "url": response.url,
            "status": response.status_code,
            "content_length": len(response.content),
            "server": response.headers.get("Server", "N/A"),
            "title": extract_title(response.text) if verbose else None,
            "ip": get_ip(domain)  # Obtém o IP do domínio
        }
        
        return result
    
    except requests.exceptions.RequestException as e:
        return {"url": url, "status": "ERROR", "error": str(e)}

# Função para extrair o título da página
def extract_title(html):
    try:
        start = html.find("<title>")
        end = html.find("</title>")
        if start != -1 and end != -1:
            return html[start + 7:end].strip()
        return "N/A"
    except:
        return "N/A"

# Função para exibir os resultados
def print_result(result, verbose=False):
    if "error" in result:
        pass
    else:
        # Define a cor com base no status
        if result['status'] in [200]:
            color = Fore.LIGHTGREEN_EX + Style.BRIGHT
        elif result['status'] in [301, 302]:
            color = Fore.LIGHTYELLOW_EX + Style.BRIGHT  # Amarelo para redirecionamentos
        elif result['status'] in [403, 404]:
            color = Fore.LIGHTRED_EX + Style.BRIGHT
        else:
            color = Fore.LIGHTCYAN_EX + Style.BRIGHT  # Outros códigos

        output = color + Style.BRIGHT + f"\n[{result['status']}] {result['url']:<35} [IP: {result['ip']:<15} ] [Size: {result['content_length']:<10}] [Server: {result['server']}]"
        if verbose and result["title"]:
            output += f" [Title: {result['title']}]"
        print(output)

# Função para listar arquivos .txt na pasta onde o script está
def listar_txt_na_pasta():
    pasta_atual = os.getcwd()  # Obtém o diretório atual
    txt_files = [f for f in os.listdir(pasta_atual) if f.endswith('.txt')]

    if not txt_files:
        print("\nNenhum arquivo .txt encontrado na pasta.")
        sys.exit()

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Escolha um arquivo de wordlist\n")
    for idx, file in enumerate(txt_files, start=1):
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n{idx} = {file}")

    while True:
        try:
            choice = int(input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o número do arquivo wordlist: "))
            if 1 <= choice <= len(txt_files):
                return os.path.join(pasta_atual, txt_files[choice - 1])
            else:
                print("Opção inválida. Tente novamente.")
        except ValueError:
            print("\nPor favor, insira um número válido.")

# Função para gerar URLs com subdomínios a partir da wordlist
def generate_subdomain_urls(base_url, subdominios):
    parsed = urlparse(base_url)
    domain = parsed.netloc or parsed.path  # Extrai o domínio base
    if not domain:
        raise ValueError("Domínio inválido fornecido.")
    
    # Gera URLs com subdomínios da wordlist
    urls = [base_url]  # Inclui o domínio base
    for subdomain in subdominios:
        urls.append(f"http://{subdomain}.{domain}")
    return urls

# Função principal
def main():
    # Configurações padrão
    timeout = 5
    verbose = True
    max_workers = 10  # Número de threads para verificar subdomínios em paralelo
    
    try:
        # Primeiro seleciona a wordlist
        wordlist_file = listar_txt_na_pasta()
        with open(wordlist_file, 'r', encoding='utf-8') as f:
            subdominios = [line.strip() for line in f.read().splitlines() if line.strip()]  # Remove linhas vazias
        
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n[+] A wordlist contém {len(subdominios)} Palavras\n")
        
        # Depois solicita a URL do website
        url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL do website (exemplo: web.com.br): ").strip()
        
        if not url:
            print("Erro: Nenhuma URL fornecida.")
            return
        
        # Gera a lista de URLs com subdomínios
        urls_to_check = generate_subdomain_urls(url, subdominios)
        
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nVerificando {len(urls_to_check)} URL no subdomínios\n")
        
        # Usa ThreadPoolExecutor para verificar URLs em paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(check_url, u, timeout, verbose): u for u in urls_to_check}
            for future in future_to_url:
                result = future.result()
                print_result(result, verbose)
                
    except ValueError as e:
        print(f"Erro: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")    
