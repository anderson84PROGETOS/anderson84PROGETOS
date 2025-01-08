import requests
from googlesearch import search
import time
import os
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██████╗ ██████╗ ███████╗    ███████╗██╗██╗     ███████╗███████╗
██╔══██╗██╔══██╗██╔════╝    ██╔════╝██║██║     ██╔════╝██╔════╝
██████╔╝██║  ██║█████╗      █████╗  ██║██║     █████╗  ███████╗
██╔═══╝ ██║  ██║██╔══╝      ██╔══╝  ██║██║     ██╔══╝  ╚════██║
██║     ██████╔╝██║         ██║     ██║███████╗███████╗███████║
╚═╝     ╚═════╝ ╚═╝         ╚═╝     ╚═╝╚══════╝╚══════╝╚══════╝
                                                             
""")

def buscar_arquivos(website, max_arquivos, termo, tipo_arquivo):
    query = f"site:{website} {termo} filetype:{tipo_arquivo}"
    print(Fore.LIGHTYELLOW_EX + f"\n\n\nProcurando até: {max_arquivos} arquivos {termo} {website}\n")
    
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
            if contador >= max_arquivos:
                break
            if link.endswith(f".{tipo_arquivo}"):
                try:
                    response = requests.head(link, headers=headers, timeout=5)
                    if response.status_code == 200:
                        contador += 1
                        print(Fore.LIGHTGREEN_EX + f"{contador} = " + Fore.LIGHTMAGENTA_EX + f"Encontrado: " + Fore.LIGHTGREEN_EX + f"{link}\n")
                        resultados.append(link)
                except requests.RequestException as e:
                    print()
            time.sleep(1)  # Evitar bloqueios por excesso de requisições
    except Exception as e:
        print(f"\nErro durante a pesquisa: {e}")
    
    if not resultados:
        print(Fore.LIGHTRED_EX + "\nNenhum arquivo encontrado\n")
    return resultados

def buscar_arquivos_geral(max_arquivos, termo, tipo_arquivo):
    query = f"{termo} filetype:{tipo_arquivo}"
    print(Fore.LIGHTYELLOW_EX + f"\n\n\nProcurando até: {max_arquivos} arquivos {termo} em sites gerais\n")
    
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
            if contador >= max_arquivos:
                break
            if link.endswith(f".{tipo_arquivo}"):
                try:
                    response = requests.head(link, headers=headers, timeout=5)
                    if response.status_code == 200:
                        contador += 1
                        print(Fore.LIGHTGREEN_EX + f"{contador} = " + Fore.LIGHTMAGENTA_EX + f"Encontrado: " + Fore.LIGHTGREEN_EX + f"{link}\n")
                        resultados.append(link)
                except requests.RequestException as e:
                    print()
            time.sleep(1)  # Evitar bloqueios por excesso de requisições
    except Exception as e:
        print(f"\nErro durante a pesquisa: {e}")
    
    if not resultados:
        print(Fore.LIGHTRED_EX + "\nNenhum arquivo encontrado\n")
    return resultados

def salvar_em_arquivo(resultados):
    # Perguntar se o usuário deseja salvar os resultados
    resposta = input(Fore.LIGHTCYAN_EX + "\nDeseja salvar os Links Encontrados? (s/n): ").strip().lower()
    if resposta == 's':
        nome_arquivo = input(Fore.LIGHTYELLOW_EX + "\nDigite o nome do arquivo (exemplo: arquivo.txt): ").strip()
        try:
            with open(nome_arquivo, 'w') as f:
                # Escrevendo a quantidade de arquivos encontrados no início do arquivo
                f.write(f"Foram salvos: {len(resultados)}  Links Encontrados\n\n")
                
                # Escrevendo as URLs dos arquivos encontrados
                for link in resultados:
                    f.write(link + '\n\n')  # Salvando as URLs com espaçamento entre elas

            print(Fore.LIGHTGREEN_EX + f"\nOs Links foram salvos em: {nome_arquivo}")
        except Exception as e:
            print(Fore.LIGHTRED_EX + f"\nErro ao salvar o arquivo: {e}")
    else:
        print(Fore.LIGHTRED_EX + "\nOs Links não foram salvos.")    

if __name__ == "__main__":
    # Menu de seleção
    print(Fore.LIGHTMAGENTA_EX + "\nEscolha o tipo de pesquisa\n")
    print("1 - Procurar PDF")
    print("2 - Procurar Livros (PDF)")
    print("3 - Procurar outros tipos de arquivos (PDF, DOCX, XLSX, TXT)")

    tipo_pesquisa = input(Fore.LIGHTGREEN_EX + "\nDigite o número da opção desejada (1, 2, 3): ").strip()

    if tipo_pesquisa == "1":
        termo = "filetype:pdf"
        tipo_arquivo = "pdf"
        # Solicitar o nome do site apenas para a opção 1
        site = input(Fore.LIGHTGREEN_EX + "\nDigite o nome do website (exemplo: example.com): ")
    elif tipo_pesquisa == "2":
        nome_livro = input(Fore.LIGHTYELLOW_EX + "\nDigite o nome do livro que deseja procurar (exemplo: Python para Iniciantes): ").strip()
        termo = f"livro {nome_livro} filetype:pdf"  # Incluir o filetype:pdf na pesquisa
        tipo_arquivo = "pdf"
        # Não solicitar o nome do site na opção 2
        site = None  # Não precisa de um site específico
    elif tipo_pesquisa == "3":
        termo = input(Fore.LIGHTMAGENTA_EX + "\nDigite o termo a ser pesquisado: ").strip()
        tipo_arquivo = input(Fore.LIGHTMAGENTA_EX + "\nDigite o tipo de arquivo desejado (pdf, docx, xlsx, txt): ").strip().lower()
        # Garantir que a pesquisa seja feita corretamente para os tipos de arquivo escolhidos
        if tipo_arquivo not in ["pdf", "docx", "xlsx", "txt"]:
            print(Fore.LIGHTRED_EX + "\nTipo de arquivo inválido. Escolha entre pdf, docx, xlsx ou txt.")
            exit()
        termo += f" filetype:{tipo_arquivo}"
        site = None  # Não precisa de um site específico
    else:
        print(Fore.LIGHTRED_EX + "\nOpção inválida.")
        exit()

    try:
        max_arquivos = int(input(Fore.LIGHTCYAN_EX + "\nDigite o Número Máximo de Arquivos Que Deseja Encontrar: "))
    except ValueError:
        print("\nEntrada inválida. Usando o padrão de 10 arquivos.\n")
        max_arquivos = 10    

    print(Fore.LIGHTYELLOW_EX + f"\nPesquisando por: {termo}\n")

    # Realiza a busca de arquivos
    if site:
        print(Fore.LIGHTYELLOW_EX + f"\nProcurando até: {max_arquivos} arquivos de {tipo_arquivo} no site: {site}")
        resultados = buscar_arquivos(site, max_arquivos, termo, tipo_arquivo)
    else:
        print(Fore.LIGHTYELLOW_EX + f"\nProcurando até: {max_arquivos} arquivos de {tipo_arquivo} com o termo: {termo}\n")
        resultados = buscar_arquivos_geral(max_arquivos, termo, tipo_arquivo)

    # Excluir o arquivo .google-cookie, se ele existir
    if os.path.exists(".google-cookie"):
        os.remove(".google-cookie")

    # Perguntar se deseja salvar os arquivos encontrados
    salvar_em_arquivo(resultados)

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
