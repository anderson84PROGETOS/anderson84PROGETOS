import subprocess
from urllib.parse import urlparse
import socket
import requests

print("""

███████╗██╗███╗   ██╗██████╗ ██╗███╗   ██╗ ██████╗     ███████╗██╗   ██╗██████╗     ██╗██████╗ 
██╔════╝██║████╗  ██║██╔══██╗██║████╗  ██║██╔════╝     ██╔════╝██║   ██║██╔══██╗    ██║██╔══██╗
█████╗  ██║██╔██╗ ██║██║  ██║██║██╔██╗ ██║██║  ███╗    ███████╗██║   ██║██████╔╝    ██║██████╔╝
██╔══╝  ██║██║╚██╗██║██║  ██║██║██║╚██╗██║██║   ██║    ╚════██║██║   ██║██╔══██╗    ██║██╔═══╝ 
██║     ██║██║ ╚████║██████╔╝██║██║ ╚████║╚██████╔╝    ███████║╚██████╔╝██████╔╝    ██║██║     
╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝     ╚══════╝ ╚═════╝ ╚═════╝     ╚═╝╚═╝     
                                                                                               
""")

def get_subdomains(domain, wordlist_url):
    results = ""
    try:
        # Baixa a lista de subdomínios do URL fornecido
        response = requests.get(wordlist_url)
        response.raise_for_status()
        subdominios = response.text.splitlines()
    except requests.RequestException as e:
        print(f"Erro ao baixar a lista de subdomínios: {e}")
        return results

    for subdomain in subdominios:
        full_domain = f"{subdomain}.{domain}"
        try:
            # Realiza a consulta DNS
            result = socket.gethostbyname(full_domain)
            result_line = f"{full_domain:<40}  IP: {result}\n"
            results += result_line
            print(result_line, end="")
        except socket.gaierror:
            # Caso não encontre endereço para o subdomínio
            pass

    return results

def save_results(results):
    save_option = input("\n\nDeseja salvar os resultados? (s/n): ").strip().lower()
    if save_option == 's':
        file_name = input("\nDigite o nome do arquivo (exemplo: arquivo.txt): ").strip()
        try:
            with open(file_name, 'w') as file:
                file.write(results)
            print(f"\nResultados salvos Em: {file_name}")
        except IOError as e:
            print(f"\nErro ao salvar o arquivo: {e}")

if __name__ == "__main__":
    url = input("\nDigite a URL do website: ")
    print("\n\nFinding Subdomains\n==================\n")
    parsed_url = urlparse(url)
    domain = parsed_url.netloc or parsed_url.path
    wordlist_url = 'https://raw.githubusercontent.com/anderson84PROGETOS/anderson84PROGETOS/meu-progetos/lista.txt'
    results = get_subdomains(domain, wordlist_url)

    # Salva os resultados
    save_results(results)

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
