import requests

print("""

██████╗ ███████╗██████╗ ██╗██████╗ ███████╗ ██████╗████████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗███████╗██████╗ 
██╔══██╗██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██████╔╝█████╗  ██║  ██║██║██████╔╝█████╗  ██║        ██║       ██║     ███████║█████╗  ██║     █████╔╝ █████╗  ██████╔╝
██╔══██╗██╔══╝  ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║       ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ ██╔══╝  ██╔══██╗
██║  ██║███████╗██████╔╝██║██║  ██║███████╗╚██████╗   ██║       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗███████╗██║  ██║
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝        ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                                                        
                                                                                                                      
""")

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

if __name__ == "__main__":
    input_url = input("\nDigite a URL para verificar os redirecionamentos: ")
    redirect_scanner(input_url)

input("\n\n\n\nPRESSIONE ENTER PARA SAIR\n")  # Aguarda a entrada do usuário antes de sair
