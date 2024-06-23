import subprocess
import requests
from urllib.parse import urlparse

print("""

 ██████╗ █████╗ ██████╗ ████████╗██╗   ██╗██████╗ ███████╗    ██╗    ██╗███████╗██████╗ ███████╗██╗████████╗███████╗
██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██╔════╝    ██║    ██║██╔════╝██╔══██╗██╔════╝██║╚══██╔══╝██╔════╝
██║     ███████║██████╔╝   ██║   ██║   ██║██████╔╝█████╗      ██║ █╗ ██║█████╗  ██████╔╝███████╗██║   ██║   █████╗  
██║     ██╔══██║██╔═══╝    ██║   ██║   ██║██╔══██╗██╔══╝      ██║███╗██║██╔══╝  ██╔══██╗╚════██║██║   ██║   ██╔══╝  
╚██████╗██║  ██║██║        ██║   ╚██████╔╝██║  ██║███████╗    ╚███╔███╔╝███████╗██████╔╝███████║██║   ██║   ███████╗
 ╚═════╝╚═╝  ╚═╝╚═╝        ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝     ╚══╝╚══╝ ╚══════╝╚═════╝ ╚══════╝╚═╝   ╚═╝   ╚══════╝
                                                                                                                    
""")

def capturar_pacotes(url):
    # Fazendo uma requisição HEAD para extrair o nome do host corretamente
    try:
        response = requests.head(url)
        response.raise_for_status()  # Lança uma exceção para erros HTTP
        host = urlparse(response.url).hostname
    except requests.exceptions.RequestException as e:
        print(f"Erro ao tentar extrair o nome do host da URL: {e}")
        return

    if host:
        # Filtrando apenas pacotes HTTP com tcpdump
        comando_tcpdump = f"tcpdump -n -i any -s 0 -A 'tcp dst port 80 and host {host}'"

        # Executando o comando tcpdump usando subprocess
        try:
            print(f"\nCapturando cabeçalhos HTTP para o host: {host}\n")
            subprocess.run(comando_tcpdump, shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar tcpdump: {e}")
    else:
        print("URL inválida. Certifique-se de fornecer uma URL válida.")

def main():
    # Solicita ao usuário a URL do site alvo
    url = input("\nDigite a URL do website para capturar os pacotes: ").strip()
    print("\n========== Capturando cabeçalhos HTTP ==========\n")
    
    # Chamando a função para capturar pacotes
    capturar_pacotes(url)

if __name__ == "__main__":
    main()
