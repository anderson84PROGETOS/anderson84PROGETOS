import requests

print("""

██████╗ ███████╗██████╗ ██╗██████╗ ███████╗ ██████╗████████╗
██╔══██╗██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝
██████╔╝█████╗  ██║  ██║██║██████╔╝█████╗  ██║        ██║   
██╔══██╗██╔══╝  ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║   
██║  ██║███████╗██████╔╝██║██║  ██║███████╗╚██████╗   ██║   
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝   
                                                         
""")

status_code_translation = {
    200: "OK",
    301: "MOVIDO PERMANENTEMENTE",
    302: "ENCONTRADO",
    403: "ACESSO PROIBIDO",
    404: "NÃO ENCONTRADO",
    500: "ERRO INTERNO DO SERVIDOR",
    502: "BAD GATEWAY",
    503: "SERVIÇO INDISPONÍVEL",
    504: "GATEWAY TIMEOUT",
}

def obter_cabecalho_http(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        # Tenta acessar via HTTPS (porta 443)
        url_https = f"https://{url}"
        response = requests.get(url_https, headers=headers, timeout=5, allow_redirects=True)
        print(f"\nCabeçalhos HTTP para: {url_https}")
       
        exibir_historico_redirecionamentos(response)
        exibir_cabecalhos(response)
    except requests.exceptions.RequestException:
        try:
            # Tenta acessar via HTTP (porta 80)
            url_http = f"http://{url}"
            response = requests.get(url_http, headers=headers, timeout=5, allow_redirects=True)
            print(f"\n\nCabeçalhos HTTP para: {url_http}")
        
            exibir_historico_redirecionamentos(response)
            exibir_cabecalhos(response)
        except requests.exceptions.RequestException as e:
            print(f"Erro ao conectar-se a {url}: {e}")    

def exibir_historico_redirecionamentos(response):
    print("\n\nHistórico de Redirecionamentos\n")

    # Mostrar primeiro o status 200 (se aplicável)
    if response.status_code == 200:
        print(f"200 - OK -> {response.url}\n")
    
    # Exibir o restante dos redirecionamentos, exceto 200
    for resp in response.history:
        if resp.status_code != 200:  # Ignorar status 200 nos redirecionamentos
            status_code = resp.status_code
            status_name = status_code_translation.get(status_code, "DESCONHECIDO")
            print(f"{status_code} - {status_name} -> {resp.url}\n")

    # Exibir a resposta final, se não for 200
    if response.status_code != 200:
        status_code = response.status_code
        status_name = status_code_translation.get(status_code, "DESCONHECIDO")
        print(f"{status_code} - {status_name} -> {response.url}\n")

def exibir_cabecalhos(response):
    print("\nCabeçalhos HTTP\n")
    for key, value in response.headers.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    site = input("\nDigite o nome do site: ")
    obter_cabecalho_http(site)

input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
