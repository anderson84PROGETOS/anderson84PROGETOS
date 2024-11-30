import socket
import os
import requests

print("""

███████╗██╗   ██╗██████╗ ██████╗  ██████╗ ███╗   ███╗ █████╗ ██╗███╗   ██╗    ██████╗ ███╗   ██╗███████╗
██╔════╝██║   ██║██╔══██╗██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██║████╗  ██║    ██╔══██╗████╗  ██║██╔════╝
███████╗██║   ██║██████╔╝██║  ██║██║   ██║██╔████╔██║███████║██║██╔██╗ ██║    ██║  ██║██╔██╗ ██║███████╗
╚════██║██║   ██║██╔══██╗██║  ██║██║   ██║██║╚██╔╝██║██╔══██║██║██║╚██╗██║    ██║  ██║██║╚██╗██║╚════██║
███████║╚██████╔╝██████╔╝██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║██║██║ ╚████║    ██████╔╝██║ ╚████║███████║
╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                                        
""")

def clean_subdomain(subdomain):
    """Remove invalid trailing periods and clean subdomain."""
    return subdomain.strip().rstrip(".")

def is_accessible(url):
    """Check if a URL is accessible (responds to a request)."""
    try:
        response = requests.get(url, timeout=3)
        # Return True if any response is received
        return True
    except requests.exceptions.RequestException:
        return False

def dns_sub(alvo, arquivo):
    subdominios_encontrados = 0  # Contador de subdomínios encontrados

    try:
        with open(arquivo, 'r') as sub:
            for linha in sub:
                subdominio = clean_subdomain(linha)  # Clean trailing periods
                if not subdominio:  # Skip empty lines
                    continue
                
                host = f"{subdominio}.{alvo}".strip()
                url_https = f"https://{host}"
                url_http = f"http://{host}"

                # Check accessibility for both protocols and display the accessible one
                if is_accessible(url_https):
                    print(f"HOST ENCONTRADO: {url_https:<40} ====> IP: {socket.gethostbyname(host)}")
                    subdominios_encontrados += 1
                elif is_accessible(url_http):
                    print(f"HOST ENCONTRADO: {url_http:<40} ====> IP: {socket.gethostbyname(host)}")
                    subdominios_encontrados += 1

        # Exibir a quantidade de subdomínios encontrados
        print(f"\nTotal de subdomínios Encontrados: {subdominios_encontrados}")

    except FileNotFoundError:
        print(f"Erro: O arquivo '{arquivo}' não foi encontrado.")
    except socket.gaierror:
        pass  # Ignore invalid hostnames without printing an error

if __name__ == "__main__":
    alvo = input("\nDigite o nome do website (exemplo: exemplo.com): ").strip()
    print("\n")
    
    arquivo = os.path.join(os.path.dirname(__file__), 'subdomain.txt')

    if not os.path.exists(arquivo):
        print(f"Erro: O arquivo '{arquivo}' não foi encontrado na pasta do script.")
    else:
        dns_sub(alvo, arquivo)
        
    input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
