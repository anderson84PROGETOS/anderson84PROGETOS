import requests

print("""

 █████╗ ███╗   ██╗ █████╗ ██╗     ██╗   ██╗███████╗███████╗    ██╗  ██╗███████╗ █████╗ ██████╗ ███████╗██████╗ 
██╔══██╗████╗  ██║██╔══██╗██║     ╚██╗ ██╔╝╚══███╔╝██╔════╝    ██║  ██║██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗
███████║██╔██╗ ██║███████║██║      ╚████╔╝   ███╔╝ █████╗      ███████║█████╗  ███████║██║  ██║█████╗  ██████╔╝
██╔══██║██║╚██╗██║██╔══██║██║       ╚██╔╝   ███╔╝  ██╔══╝      ██╔══██║██╔══╝  ██╔══██║██║  ██║██╔══╝  ██╔══██╗
██║  ██║██║ ╚████║██║  ██║███████╗   ██║   ███████╗███████╗    ██║  ██║███████╗██║  ██║██████╔╝███████╗██║  ██║
╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚══════╝    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                                                               

""")

def get_headers(url):
    try:
        user_agent_android = "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
        user_agent_firefox = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
        
        # Tentar acessar o site com o agente de usuário Android
        response = requests.get(url, allow_redirects=False, headers={'User-Agent': user_agent_android})
        headers = response.headers

        print("\nscheme:", response.url.split("://")[0])
        print("\nhost:", response.url.split("/")[2])      
        print("\nStatus:", response.status_code, response.reason)
        print("\nVersãoHTTP:", response.raw.version)
                
        content_length = response.headers.get('Content-Length')
        if content_length:
            print("\nTransferido:", content_length, "(tamanho", content_length, ")")
        
        referrer_policy = response.headers.get('Referrer-Policy')
        if referrer_policy:
            print("\nReferrer Policy:", referrer_policy)
        
        priority = response.headers.get('Priority')
        if priority:
            print("\nPrioridade da requisição:", priority)
        
        print("\nUser Agente:", user_agent_android)

        print("\n")
        for header, value in headers.items():
            print(f"{header}: {value}")
        
        # Se o site redirecionar, tentar novamente com o agente de usuário Firefox
        if response.is_redirect:
            print("\n\nO site redirecionou. Tentando novamente com o agente de usuário Firefox")
            response = requests.get(url, allow_redirects=False, headers={'User-Agent': user_agent_firefox})
            headers = response.headers

            print("\nUser Agente:", user_agent_firefox)

            print("\n")
            for header, value in headers.items():
                print(f"{header}: {value}")

    except Exception as e:
        print("\nOcorreu um erro ao tentar capturar os cabeçalhos HTTP:", e)

if __name__ == "__main__":
    url = input("\nDigite a URL completa do website: ")
    get_headers(url)

input("\nPRESSIONE ENTER PARA SAIR\n")
