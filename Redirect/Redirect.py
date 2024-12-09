import requests
import subprocess

print("""

██████╗ ███████╗██████╗ ██╗██████╗ ███████╗ ██████╗████████╗
██╔══██╗██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝
██████╔╝█████╗  ██║  ██║██║██████╔╝█████╗  ██║        ██║   
██╔══██╗██╔══╝  ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║   
██║  ██║███████╗██████╔╝██║██║  ██║███████╗╚██████╗   ██║   
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝   
                                                          
""")
# Dicionário para traduzir os códigos de status HTTP para seus nomes
STATUS_HTTP = {
    200: "OK",
    301: "Movido Permanentemente",
    302: "Encontrado",
    403: "Proibido",
    404: "Não Encontrado",
    500: "Erro Interno do Servidor",
    503: "Serviço Indisponível",
}

def traduzir_status(codigo):
    return STATUS_HTTP.get(codigo, "Unknown Status")

def obter_cabecalho_http(url):
    try:
        # Adiciona http:// se o usuário inserir apenas o nome do site
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        
        # Configura os cabeçalhos HTTP para evitar erros 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

        # Envia a solicitação com redirecionamentos automáticos
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)

        # Exibe os redirecionamentos e códigos de status
        cabecalho = ""
        for resp in response.history:
            nome_status = traduzir_status(resp.status_code)
            cabecalho += f"Status Code: {resp.status_code} ({nome_status}) | URL: {resp.url}\n\n"
        
        # Inclui a última resposta (URL final)
        nome_status_final = traduzir_status(response.status_code)
        cabecalho += f"Status Code: {response.status_code} ({nome_status_final}) | URL: {response.url}\n\n"

        # Usa o curl para obter o cabeçalho HTTP da URL final
        comando_curl = ["curl", "-I", response.url]
        resultado_curl = subprocess.run(comando_curl, capture_output=True, text=True)
        
        cabecalho += "\n\nCabeçalho HTTP\n\n"
        cabecalho += resultado_curl.stdout.strip()

        return cabecalho
    except requests.RequestException as e:
        return f"Erro ao executar a solicitação HTTP: {e}"
    except subprocess.SubprocessError as e:
        return f"Erro ao executar o comando curl: {e}"

# Solicita ao usuário a URL ou nome do website
url = input("\nDigite a URL ou nome do website: ").strip()

# Obtém o cabeçalho HTTP
cabecalho_http = obter_cabecalho_http(url)

# Exibe o histórico de redirecionamentos com formatação especial
print("\n\nHistórico de Redirecionamentos\n")
print(cabecalho_http)

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
