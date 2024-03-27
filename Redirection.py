import requests

def print_banner():
    banner = r"""            
  
██████╗ ███████╗██████╗ ██╗██████╗ ███████╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║
██████╔╝█████╗  ██║  ██║██║██████╔╝█████╗  ██║        ██║   ██║██║   ██║██╔██╗ ██║
██╔══██╗██╔══╝  ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║   ██║██║   ██║██║╚██╗██║
██║  ██║███████╗██████╔╝██║██║  ██║███████╗╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                                                                                                                                                                                                                     
"""
    print(banner)

def follow_redirects(url):
    try:
        response = requests.get(url, allow_redirects=True)
        print("\n ⬇️   Redirecionamentos ⬇️")
        for i, resp in enumerate(response.history, start=1):
            print(f"\n\n{i}. 🔵 ({resp.status_code}) {resp.url}")
        
        if response.status_code == 200:
            print(f"\n\n\n{len(response.history) + 1}. 🟢 (200 - OK) {response.url}")
        else:
            print(f"\n{len(response.history) + 1}. 🔴 ({response.status_code}) {response.url}")

    except requests.RequestException as e:
        print("\nErro ao seguir redirecionamentos:", e)

def redirect_scanner(url):
    try:
        print("\n\n\nWebSite:", url)  # Adiciona o prefixo "WebSite:" antes da URL original
        print("\n\n")
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'}
        while True:
            response = requests.get(url, allow_redirects=False, headers=headers)
            status_code = response.status_code
            final_url = response.headers.get('Location') if 'Location' in response.headers else None
            
            print("\n", status_code, response.reason)            
            if final_url:
                print(final_url)               
                url = final_url
                print("\n")  # Adiciona uma linha em branco após cada redirecionamento
               
            elif status_code == 200:
                print(url)  # Adiciona a URL do site após o código 200
                break
            elif status_code == 403:
                print("\nAcesso negado. Esta página está protegida.\n")
                break
        
    except requests.RequestException as e:
        print(f"Ocorreu um erro ao acessar a URL: {e}")

def exibir_cabecalho_http(url):
    try:
        # Mesmo User-Agent utilizado na função redirect_scanner
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0'}
        
        # Faz a requisição HTTP com follow redirection
        resposta = requests.get(url, headers=headers)
        
        # Verifica se a requisição foi bem sucedida
        if resposta.status_code == 200:
            print("\n\n\nCabeçalhos HTTP para:", url)
            print("----------------------------------------------")
            
            # Itera sobre os cabeçalhos e os imprime
            for chave, valor in resposta.headers.items():
                print(f"{chave}: {valor}")
        else:
            print(f"A requisição falhou com código de status {resposta.status_code}")
    except requests.exceptions.RequestException as e:
        print("Erro durante a requisição:", e)
   

def main():
    print_banner()
    url = input("\nDigite a URL para verificar o redirecionamento: ")
    follow_redirects(url)
    
    print("\n\n\n\n")
    print("\n======​ ↓ Outros Redirecionamento ↓ ========​\n")
    redirect_scanner(url)
    
    # Chamada para exibir o cabeçalho HTTP após o redirecionamento
    exibir_cabecalho_http(url)

if __name__ == "__main__":
    main()
    
input("\n\nRedirecionamento Finalizado. Pressione 🔚  ​ENTER  🔚​\n")
