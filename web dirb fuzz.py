import requests
import concurrent.futures
import os
from urllib.parse import urljoin

print("""

██╗    ██╗███████╗██████╗     ██████╗ ██╗██████╗ ██████╗     ███████╗██╗   ██╗███████╗███████╗
██║    ██║██╔════╝██╔══██╗    ██╔══██╗██║██╔══██╗██╔══██╗    ██╔════╝██║   ██║╚══███╔╝╚══███╔╝
██║ █╗ ██║█████╗  ██████╔╝    ██║  ██║██║██████╔╝██████╔╝    █████╗  ██║   ██║  ███╔╝   ███╔╝ 
██║███╗██║██╔══╝  ██╔══██╗    ██║  ██║██║██╔══██╗██╔══██╗    ██╔══╝  ██║   ██║ ███╔╝   ███╔╝  
╚███╔███╔╝███████╗██████╔╝    ██████╔╝██║██║  ██║██████╔╝    ██║     ╚██████╔╝███████╗███████╗
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═════╝ ╚═╝╚═╝  ╚═╝╚═════╝     ╚═╝      ╚═════╝ ╚══════╝╚══════╝
                                                                                              
""")

# Cabeçalhos HTTP personalizados para evitar erros 403
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

results = []  # Lista para armazenar resultados

# Função para realizar a requisição e processar o resultado
def fuzz_url(base_url, word):
    url = urljoin(base_url, word.strip())
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        status = response.status_code
        size = len(response.content)
        
        # Adiciona uma verificação para garantir que a resposta não seja uma página padrão ou um redirecionamento
        if status == 200 and size > 100:
            result = f"{url:<50} [Status: {status}, Size: {size}]"
            results.append(result)
            print(result)
    except requests.RequestException:
        # Não exibe mensagens de erro
        pass

# Função para salvar resultados em um arquivo
def save_results():
    save_choice = input("\n\nDeseja salvar os resultados? (s/n): ").strip().lower()
    if save_choice == 's':
        filename = input("\nDigite o nome do arquivo para salvar os resultados (ex: arquivo.txt): ").strip()
        if not filename.endswith('.txt'):
            filename += '.txt'
        with open(filename, 'w') as file:
            for result in results:
                file.write(result + '\n')
        print(f"\nResultados salvos Em: {filename}")

# Função para baixar o wordlist
def download_wordlist(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
        return response.text.splitlines()  # Divide o conteúdo em linhas
    except requests.RequestException as e:
        print(f"\nOcorreu um erro ao baixar o wordlist: {e}")
        return []

# Função principal
def main():
    base_url = input("\nDigite a URL do website (ex: https://example.com): ").strip()
    print("\n\nCarregando WEB FUZZ DIRB \n")
    if not base_url.endswith("/FUZZ"):
        if not base_url.endswith("/"):
            base_url += "/"
        base_url += "FUZZ"
    
    # URL do arquivo wordlist
    wordlist_url = 'https://raw.githubusercontent.com/anderson84PROGETOS/anderson84PROGETOS/meu-progetos/lista.txt'
    
    # Baixar o wordlist
    words = download_wordlist(wordlist_url)
    
    if not words:
        print("\nOcorreu um problema ao baixar o arquivo 'lista.txt'.")
        return

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fuzz_url, base_url, word) for word in words]
            concurrent.futures.wait(futures)
        
        if not results:
            print("\nNenhum URL retornou o status 200.")
        else:
            print(f"\nTotal de URL Encontradas: {len(results)}")

    except Exception as e:
        print(f"\nOcorreu um erro ao processar o arquivo: {e}")

    save_results()

if __name__ == "__main__":
    main()

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
