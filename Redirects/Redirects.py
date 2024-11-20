import requests
from http import HTTPStatus  # Para obter o nome do status_code

print("""

██████╗ ███████╗██████╗ ██╗██████╗ ███████╗ ██████╗████████╗███████╗
██╔══██╗██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔════╝
██████╔╝█████╗  ██║  ██║██║██████╔╝█████╗  ██║        ██║   ███████╗
██╔══██╗██╔══╝  ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║   ╚════██║
██║  ██║███████╗██████╔╝██║██║  ██║███████╗╚██████╗   ██║   ███████║
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝   ╚══════╝
                                                                   
""")

# Dicionário para tradução dos status codes para português
status_code_translation = {
    200: "OK",
    301: "MOVIDO PERMANENTEMENTE",  # Tradução do status 301
    302: "ENCONTRADO",
    403: "ACESSO PROIBIDO",
    404: "NÃO ENCONTRADO",
    500: "ERRO INTERNO DO SERVIDOR",
    502: "BAD GATEWAY",
    503: "SERVIÇO INDISPONÍVEL",
    504: "GATEWAY TIMEOUT",
    # Adicione mais traduções conforme necessário
}

def obter_cabecalho_http(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    headers_2 = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'DNT': '1',  # "Do Not Track" header
        'Cache-Control': 'max-age=0',  # Não usar cache
        'TE': 'Trailers',
        'Origin': url,  # Adiciona o cabeçalho 'Origin' para simular uma requisição legítima
        'Referer': url  # Referência da requisição
    }

    try:
        # Tenta acessar via HTTPS (porta 443)
        url_https = f"https://{url}"
        response = requests.get(url_https, headers=headers, timeout=5, allow_redirects=True)
        if response.status_code == 403:
            print(f"⚠️ Acesso proibido a {url_https} (403). Tentando outra abordagem...")
            response = contornar_erro_403(url_https, headers)
        print(f"\nCabeçalhos HTTP para: {url_https}")
        print_status_code(response)
        exibir_detalhes_resposta(response)  # Exibe o histórico apenas para a primeira requisição
        
        # Segunda requisição com cabeçalhos diferentes
        response_2 = requests.get(url_https, headers=headers_2, timeout=5, allow_redirects=True)
        print(f"\n\n\nCabeçalhos HTTP da segunda requisição para: {url_https}")
        print_status_code(response_2)
        exibir_detalhes_resposta(response_2, show_redirects=False)  # Não exibe redirecionamentos na segunda requisição
    except requests.exceptions.RequestException:
        try:
            # Se falhar, tenta acessar via HTTP (porta 80)
            url_http = f"http://{url}"
            response = requests.get(url_http, headers=headers, timeout=5, allow_redirects=True)
            if response.status_code == 403:
                print(f"⚠️ Acesso proibido a {url_http} (403). Tentando outra abordagem...")
                response = contornar_erro_403(url_http, headers)
            print(f"\nCabeçalhos HTTP para: {url_http}")
            print_status_code(response)
            exibir_detalhes_resposta(response)  # Exibe o histórico apenas para a primeira requisição
            
            # Segunda requisição com cabeçalhos diferentes
            response_2 = requests.get(url_http, headers=headers_2, timeout=5, allow_redirects=True)
            print(f"\n\n\nCabeçalhos HTTP da segunda requisição para: {url_http}")
            print_status_code(response_2)
            exibir_detalhes_resposta(response_2, show_redirects=False)  # Não exibe redirecionamentos na segunda requisição
        except requests.exceptions.RequestException as e:
            print(f"Erro ao conectar-se a {url}: {e}")

def contornar_erro_403(url, headers):
    """Tenta contornar o erro 403 ajustando os cabeçalhos."""
    headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1"
    headers["Referer"] = url
    response = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
    return response

def print_status_code(response):
    """Exibe o código de status e sua descrição em português."""
    status_code = response.status_code
    status_name = status_code_translation.get(status_code, "DESCONHECIDO")
    print(f"\nStatus Code: {status_code} - {status_name}\n")

def exibir_detalhes_resposta(response, show_redirects=True):
    """Exibe detalhes da resposta, incluindo redirecionamentos e cabeçalhos."""
    if show_redirects and response.history:
        print("\nHistórico de Redirecionamentos\n")
        for redirect in response.history:
            status_code = redirect.status_code
            status_name = status_code_translation.get(status_code, "DESCONHECIDO")
            print(f"{status_code} - {status_name} -> {redirect.url}\n\n")
            
    else:        
        print("\nCabeçalhos HTTP\n")
    for key, value in response.headers.items():
        print(f"{key}: {value}")

# Exemplo de uso
if __name__ == "__main__":
    site = input("\nDigite o nome do site: ")
    obter_cabecalho_http(site)

input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
