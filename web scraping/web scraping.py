import requests
import re
from bs4 import BeautifulSoup
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """\n
██╗    ██╗███████╗██████╗     ███████╗ ██████╗██████╗  █████╗ ██████╗ ██╗███╗   ██╗ ██████╗ 
██║    ██║██╔════╝██╔══██╗    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║██╔════╝ 
██║ █╗ ██║█████╗  ██████╔╝    ███████╗██║     ██████╔╝███████║██████╔╝██║██╔██╗ ██║██║  ███╗
██║███╗██║██╔══╝  ██╔══██╗    ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██║██║╚██╗██║██║   ██║
╚███╔███╔╝███████╗██████╔╝    ███████║╚██████╗██║  ██║██║  ██║██║     ██║██║ ╚████║╚██████╔╝
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝  
""")

# Solicita a URL ao usuário
url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + " Digite a URL do website: ")

# Cabeçalhos para evitar erro 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

try:
    # Faz a requisição usando requests
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()  # Garante que não houve erro HTTP

    # Obtém o conteúdo HTML da página
    html_content = response.text

    # Usa BeautifulSoup para analisar o HTML
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text()

    # Expressões regulares para capturar URLs, e-mails e números de telefone
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
    phone_pattern = re.compile(r'\(?\d{2,4}\)?[-.\s]?\d{4,5}[-.\s]?\d{4}')

    # Extração dos dados
    urls = set(url_pattern.findall(html_content))
    emails = set(email_pattern.findall(text))
    phones = set(phone_pattern.findall(text))

    # Captura o conteúdo do rodapé se existir a classe 'legal-info-container'
    footer_text_1 = ""
    footer_div_1 = soup.find(class_="legal-info-container")
    if footer_div_1:
        footer_text_1 = footer_div_1.get_text(strip=True)

    # Tentando encontrar o conteúdo do rodapé geral
    footer_text_2 = ""
    footer_div_2 = soup.find('footer')
    if footer_div_2:
        footer_text_2 = footer_div_2.get_text(strip=True)

    # Preparando os resultados
    results = ""

    if urls:
        results += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\n URL Encontradas: {len(urls)}"
        for u in urls:
            results += Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n\n ➜   " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{u}"

    if emails:
        results += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\n\n E-mails Encontrados: {len(emails)}\n"
        for e in emails:
            results += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n ✉  " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{e}"

    if phones:
        results += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\n\n Telefones Encontrados: {len(phones)}\n"
        for p in phones:
            results += Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n ☎  " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{p}"

    if footer_text_1:
        results += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\n\nRodapé 1 \n\n" + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{footer_text_1}\n"

    if footer_text_2:
        results += Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\n\nRodapé 2 \n\n" + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{footer_text_2}\n"
    
    # Função para remover as sequências de escape ANSI de uma string
    def remove_colors(text):
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_escape.sub('', text)

    # Exibição dos resultados
    print(results)

    # Pergunta ao usuário se deseja salvar os resultados
    save_option = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\n\nDeseja salvar os resultados? (s/n): ").lower()
    if save_option == 's':
        # Solicita o nome do arquivo
        file_name = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o nome do arquivo (exemplo: arquivo.txt): ")

        # Remove as cores dos resultados antes de salvar
        results_clean = remove_colors(results)

        # Salva os resultados no arquivo sem as cores
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(results_clean)

        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nResultados salvos em: {file_name}")
    else:
        print(Fore.LIGHTRED_EX + "\nResultados não salvos.")

finally:
    input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
