import requests
from bs4 import BeautifulSoup
import re

print("""

███████╗██╗  ██╗████████╗██████╗  █████╗  ██████╗████████╗    ██╗   ██╗██████╗ ██╗     
██╔════╝╚██╗██╔╝╚══██╔══╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝    ██║   ██║██╔══██╗██║     
█████╗   ╚███╔╝    ██║   ██████╔╝███████║██║        ██║       ██║   ██║██████╔╝██║     
██╔══╝   ██╔██╗    ██║   ██╔══██╗██╔══██║██║        ██║       ██║   ██║██╔══██╗██║     
███████╗██╔╝ ██╗   ██║   ██║  ██║██║  ██║╚██████╗   ██║       ╚██████╔╝██║  ██║███████╗
╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝   ╚═╝        ╚═════╝ ╚═╝  ╚═╝╚══════╝
                                                                                                                                                                                     
""")

def get_page_links(url):
    try:
        # Headers para evitar erro 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

        # Faz a solicitação HTTP para a URL fornecida com os headers definidos
        response = requests.get(url, headers=headers)
        
        # Verifica se a solicitação foi bem-sucedida (código de status 200)
        if response.status_code == 200:
            # Analisa o conteúdo HTML da página
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Encontra todos os elementos 'a' que contêm links
            links = soup.find_all('a')
            
            # Extrai os links que começam com 'http://' ou 'https://'
            hrefs = set()  # Usando um conjunto para armazenar URLs únicas
            for link in links:
                href = link.get('href')
                if href and (href.startswith('http://') or href.startswith('https://')):
                    hrefs.add(href)
            
            # Encontrar todos os subdomínios nos URLs
            subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', response.text))
            
            # Imprimir subdomínios na tela
            print(f"\nForam Encontrados Subdomínios: {len(subdomains)} \n")
            for subdomain in subdomains:
                print(subdomain)
            
            # Imprimir hrefs na tela
            print(f"\n\n\nForam Encontradas Hrefs: {len(hrefs)} \n")
            for href in hrefs:
                print(href)

            # Perguntar ao usuário se deseja salvar os resultados em um arquivo
            salvar_arquivo = input("\n\nDeseja salvar os resultados em um arquivo? (s/n): ").strip().lower()

            if salvar_arquivo == 's':
                arquivo_saida = input("\n\nNome do Arquivo de Saída (exemplo: arquivo.txt): ")

                with open(arquivo_saida, 'w', encoding='utf-8') as file:
                    file.write(f"Foram Encontrados Subdomínios: {len(subdomains)} \n\n")
                    for subdomain in subdomains:
                        file.write(subdomain + '\n')

                    file.write(f"\n\nForam Encontradas Hrefs: {len(hrefs)} \n\n")
                    for href in hrefs:
                        file.write(href + '\n')

                print(f"\n\nOs Resultados Foram Salvos Em: {arquivo_saida}\n")
            elif salvar_arquivo == 'n':
                print("\n\nOs Resultados Não Foram Salvos\n")
            else:
                print("\n\nOpção inválida. Os Resultados Não Foram Salvos\n")

        else:
            print("Erro ao acessar a página:", response.status_code)
    except Exception as e:
        print("Ocorreu um erro:", str(e))


# URL da página da web a ser analisada
url = input("Digite a URL do website: ").strip()
print("\n")

# Chama a função para obter os links da página
get_page_links(url)

input("\n\n=================== PRESSIONE ENTER PARA SAIR ===================\n\n")
