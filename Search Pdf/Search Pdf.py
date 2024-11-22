import requests
from googlesearch import search
import time
import os

print("""

███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗    ██████╗ ██████╗ ███████╗
██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║    ██╔══██╗██╔══██╗██╔════╝
███████╗█████╗  ███████║██████╔╝██║     ███████║    ██████╔╝██║  ██║█████╗  
╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║    ██╔═══╝ ██║  ██║██╔══╝  
███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║    ██║     ██████╔╝██║     
╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝    ╚═╝     ╚═════╝ ╚═╝     
                                                                                                                                                 
""")

def buscar_pdfs(website, max_pdfs):
    query = f"site:{website} filetype:pdf"
    print(f"\n\n\nProcurando até {max_pdfs} arquivos PDF no site: {website}\n\n")
    
    resultados = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    try:
        contador = 0
        for link in search(query):
            if contador >= max_pdfs:
                break
            if link.endswith(".pdf"):
                try:
                    response = requests.head(link, headers=headers, timeout=5)
                    if response.status_code == 200:
                        print(f"Encontrado: {link}\n")
                        resultados.append(link)
                        contador += 1
                except requests.RequestException as e:
                    print(f"\nErro ao acessar {link}: {e}")
            time.sleep(1)  # Evitar bloqueios por excesso de requisições
    except Exception as e:
        print(f"\nErro durante a pesquisa: {e}")
    
    if not resultados:
        print("\nNenhum arquivo PDF encontrado.")
    return resultados

if __name__ == "__main__":
    site = input("\nDigite o nome do website (exemplo: example.com): ")
    try:
        max_pdfs = int(input("\nDigite o número máximo de PDFs que deseja encontrar: "))
    except ValueError:
        print("\nEntrada inválida. Usando o padrão de 10 PDFs.")
        max_pdfs = 10    
    buscar_pdfs(site, max_pdfs)

     # Excluir o arquivo .google-cookie, se ele existir
    if os.path.exists(".google-cookie"):
        os.remove(".google-cookie")        

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
