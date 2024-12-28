import requests
from urllib.parse import urlparse
import socket
import pycountry  # Biblioteca para obter o nome completo do país

print("""

██╗    ██╗███████╗██████╗ ██████╗ ███████╗████████╗███████╗ ██████╗████████╗
██║    ██║██╔════╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝
██║ █╗ ██║█████╗  ██████╔╝██║  ██║█████╗     ██║   █████╗  ██║        ██║   
██║███╗██║██╔══╝  ██╔══██╗██║  ██║██╔══╝     ██║   ██╔══╝  ██║        ██║   
╚███╔███╔╝███████╗██████╔╝██████╔╝███████╗   ██║   ███████╗╚██████╗   ██║   
 ╚══╝╚══╝ ╚══════╝╚═════╝ ╚═════╝ ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝   ╚═╝   
                                                                                                                               
""")

def obter_pais_completo(codigo_pais):
    try:
        pais = pycountry.countries.get(alpha_2=codigo_pais)
        return pais.name if pais else "DESCONHECIDO"
    except Exception as e:
        print(f"Erro ao converter código do país: {e}")
    return "DESCONHECIDO"

def obter_pais(endereco_ip):
    try:
        # Usando a API pública do ipinfo.io para obter o país
        resposta = requests.get(f"https://ipinfo.io/{endereco_ip}/json")
        if resposta.status_code == 200:
            dados = resposta.json()
            codigo_pais = dados.get("country", "DESCONHECIDO")
            return obter_pais_completo(codigo_pais)
    except Exception as e:
        print(f"Erro ao obter o país: {e}")
    return "DESCONHECIDO"

def obter_informacoes_do_site(url):
    try:
        # Adicionar esquema (http ou https) se estiver ausente
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        # Cabeçalhos para evitar erro 403
        cabecalhos = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/',
            'Cache-Control': 'no-cache'
        }
        
        # Realizar a requisição ao site
        resposta = requests.get(url, headers=cabecalhos)
        url_analisada = urlparse(url)
        
        # Obter informações do IP
        endereco_ip = socket.gethostbyname(url_analisada.netloc)
        pais = obter_pais(endereco_ip)  # Obter o país usando a função
        
        # Processar cabeçalhos HTTP
        cabecalhos_site = resposta.headers
        servidor = cabecalhos_site.get("Server", "DESCONHECIDO")
        cookies = list(resposta.cookies.keys())
        metodos_acesso = cabecalhos_site.get("Access-Control-Allow-Methods", "DESCONHECIDO")
        cabecalhos_incomuns = [k for k in cabecalhos_site.keys() if k.lower() not in 
                                ["content-type", "content-length", "server", "date", "set-cookie"]]
        
        # Exibir o resultado
        print(f"Relatório WhatWeb para: {url}")
        print(f"Status    : {resposta.status_code} {resposta.reason}")
        print(f"Título    : {url_analisada.netloc}")
        print(f"IP        : {endereco_ip}")
        print(f"País      : {pais}")
        print(f"Servidor  : {servidor}\n")
        
        print("Resumo    :", end=" ")
        if metodos_acesso != "DESCONHECIDO":
            print(f"Access-Control-Allow-Methods[{metodos_acesso}], ", end="")
        if cookies:
            print(f"Cookies[{', '.join(cookies)}], ", end="")
        if servidor != "DESCONHECIDO":
            print(f"ServidorHTTP[{servidor}], ", end="")
        if cabecalhos_incomuns:
            print(f"CabeçalhosIncomuns[{', '.join(cabecalhos_incomuns)}]")

        print("\nPlugins Detectados\n")
        if metodos_acesso != "DESCONHECIDO":
            print(f"[ Access-Control-Allow-Methods ]\n    Especifica os métodos permitidos ao acessar um recurso.")
            print(f"    Valor        : {metodos_acesso}\n")
        if servidor != "DESCONHECIDO":
            print(f"[ ServidorHTTP ]\n    Informação do cabeçalho do servidor HTTP.")
            print(f"    Valor        : {servidor} (do cabeçalho do servidor)\n")
        if cookies:
            print(f"[ Cookies ]\n    Exibe os nomes dos cookies encontrados nos cabeçalhos HTTP.")
            print(f"    Valor        : {', '.join(cookies)}\n")
        if cabecalhos_incomuns:
            print(f"[ CabeçalhosIncomuns ]\n    Cabeçalhos HTTP incomuns encontrados.")
            print(f"    Valor        : {', '.join(cabecalhos_incomuns)}\n")
        
        print("\nCabeçalhos HTTP\n")
        for k, v in cabecalhos_site.items():
            print(f"    {k}: {v}")
    
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    site = input("\nDigite o nome do website: ")
    print("\n")
    obter_informacoes_do_site(site)
    
    input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
