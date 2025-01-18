import requests
import time
import os
from colorama import Fore, Style, init
from bs4 import BeautifulSoup
from googlesearch import search as google_search

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██████╗ ██████╗ ███████╗     ██████╗  ██████╗  ██████╗  ██████╗ ██╗     ███████╗    ██████╗ ██╗███╗   ██╗ ██████╗     
██╔══██╗██╔══██╗██╔════╝    ██╔════╝ ██╔═══██╗██╔═══██╗██╔════╝ ██║     ██╔════╝    ██╔══██╗██║████╗  ██║██╔════╝     
██████╔╝██║  ██║█████╗      ██║  ███╗██║   ██║██║   ██║██║  ███╗██║     █████╗      ██████╔╝██║██╔██╗ ██║██║  ███╗    
██╔═══╝ ██║  ██║██╔══╝      ██║   ██║██║   ██║██║   ██║██║   ██║██║     ██╔══╝      ██╔══██╗██║██║╚██╗██║██║   ██║    
██║     ██████╔╝██║         ╚██████╔╝╚██████╔╝╚██████╔╝╚██████╔╝███████╗███████╗    ██████╔╝██║██║ ╚████║╚██████╔╝    
╚═╝     ╚═════╝ ╚═╝          ╚═════╝  ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝╚══════╝    ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝     
                                                                                                                                                                                                                                                                                                                     
""")

def buscar_arquivos_google(query, max_arquivos):
    """Busca arquivos usando o Google."""
    resultados = []
    try:
        contador = 0
        for link in google_search(query):
            if contador >= max_arquivos:
                break
            resultados.append(link)
            contador += 1
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{contador} = {link}")
            time.sleep(1)
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao buscar no Google: {e}")
    return resultados

def buscar_arquivos_bing(query, max_arquivos):
    """Busca arquivos usando o Bing com filtro para tipo de arquivo PDF."""
    resultados = []
    try:
        # Inicializa o colorama
        init(autoreset=True)

        # Filtro para buscar arquivos PDF
        query_com_filtro = f"{query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        }
        
        # URL para pesquisa no Bing com filtro de tipo de arquivo PDF
        url = f"https://www.bing.com/search?q={query_com_filtro}&FORM=HDRSC1"
        
        # Realizando a requisição HTTP para buscar no Bing
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Usando BeautifulSoup para analisar o conteúdo HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontra todos os links dentro das tags <a>
        links = soup.find_all('a', href=True)

        contador = 0
        for link in links:
            href = link['href']
            # Verifica se o link é válido (inicia com 'http') e não está duplicado
            if href.startswith("http") and href not in resultados:
                if contador >= max_arquivos:
                    break
                resultados.append(href)
                contador += 1

        # Exibe os resultados encontrados com numeração
        for i, resultado in enumerate(resultados, start=1):
            print(f"\n{i} = {Fore.LIGHTYELLOW_EX + Style.BRIGHT + resultado}")
        
    except Exception as e:
        print(f"Erro ao buscar no Bing: {e}")
    
    return resultados    

def salvar_em_arquivo(resultados):
    """Salva os resultados encontrados em um arquivo."""
    resposta = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDeseja salvar os Links Encontrados? (s/n): ").strip().lower()
    if resposta == 's':
        nome_arquivo = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo (exemplo: arquivo.txt): ").strip()
        try:
            with open(nome_arquivo, 'w') as f:
                f.write(f"Foram encontrados: {len(resultados)} links\n\n")
                for link in resultados:
                    f.write(link + '\n')
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nOs Links foram salvos em: {nome_arquivo}")
        except Exception as e:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao salvar o arquivo: {e}")
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nOs Links não foram salvos.")

if __name__ == "__main__":
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nEscolha o mecanismo de busca")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "1 - Google")
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT +  "2 - Bing")
    mecanismo = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o número da opção desejada (1 ou 2): ").strip()

    if mecanismo not in ['1', '2']:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nOpção inválida.")
        exit()

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nEscolha a categoria de pesquisa")
    print(Fore.LIGHTRED_EX + Style.BRIGHT + "1 - Procurar PDF")
    print(Fore.LIGHTRED_EX + Style.BRIGHT + "2 - Procurar Livros (PDF)")
    print(Fore.LIGHTRED_EX + Style.BRIGHT + "3 - Procurar outros tipos de arquivos (PDF, DOCX, XLSX, TXT)")
    print(Fore.LIGHTRED_EX + Style.BRIGHT + "4 - Buscar por Email (Formato: \"email@example.com\")")

    opcao = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o número da opção desejada (1, 2, 3 ou 4): ").strip()

    if opcao not in ['1', '2', '3', '4']:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nOpção inválida.")
        exit()

    if opcao == '2':
        nome_livro = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do livro que deseja procurar (exemplo: Python para Iniciantes): ").strip()
        query_google = f"{nome_livro} filetype:pdf"
        query_bing = f"{nome_livro} livro filetype:pdf"
        
    else:
        if opcao == '4':  # Se a opção for 4, direto para o email
            email = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o e-mail (exemplo: email@example.com): ").strip()
            query_google = f"\"{email}\""
            query_bing = f"\"{email}\""

        else:
            if opcao == '1':  # Para a opção 1, pedirá uma URL e buscará por PDFs
                # Mensagem formatada com cores
                url = input(
                    Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite a URL para pesquisa no Google " +
                    Fore.LIGHTCYAN_EX + Style.BRIGHT + " Digite o nome para pesquisa no bing: "
                ).strip()
                query_google = f"{url} filetype:pdf"
                query_bing = f"{url} filetype:pdf"
                
            elif opcao == '3':
                tipo_arquivo = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o tipo de arquivo desejado (pdf, docx, xlsx, txt): ").strip().lower()
                url = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite a URL para pesquisa: ").strip()
                query_google = f"{url} filetype:{tipo_arquivo}"
                query_bing = f"{url} filetype:{tipo_arquivo}"

    try:
        max_arquivos = int(input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o Número Máximo de Arquivos Que Deseja Encontrar: "))
    except ValueError:
        print(Fore.LIGHTRED_EX + "\nEntrada inválida. Usando o padrão de 10 arquivos.")
        max_arquivos = 10

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nPesquisando por: {query_google}\n")

    if mecanismo == '1':
        resultados = buscar_arquivos_google(query_google, max_arquivos)
    else:
        resultados = buscar_arquivos_bing(query_bing, max_arquivos)

    # Excluir o arquivo .google-cookie, se ele existir
    if os.path.exists(".google-cookie"):
        os.remove(".google-cookie")

    salvar_em_arquivo(resultados)

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========")
