import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
 █████╗ ██╗      █████╗ ███╗   ██╗██╗███████╗███████╗    ██╗    ██╗███████╗██████╗ 
██╔══██╗██║     ██╔══██╗████╗  ██║██║██╔════╝██╔════╝    ██║    ██║██╔════╝██╔══██╗
███████║██║     ███████║██╔██╗ ██║██║███████╗█████╗      ██║ █╗ ██║█████╗  ██████╔╝
██╔══██║██║     ██╔══██║██║╚██╗██║██║╚════██║██╔══╝      ██║███╗██║██╔══╝  ██╔══██╗
██║  ██║███████╗██║  ██║██║ ╚████║██║███████║███████╗    ╚███╔███╔╝███████╗██████╔╝
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚══════╝╚══════╝     ╚══╝╚══╝ ╚══════╝╚═════╝
""")


def abrir_imagem(img_data, img_url):
    try:
        img = Image.open(BytesIO(img_data))
        img.show()
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n[+] URL da imagem: {img_url}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao abrir a imagem: {e}" + Style.RESET_ALL)


def captura_tela(url):
    try:
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n[+] Capturando tela do site: {url}" + Style.RESET_ALL)
        screenshot_url = f"https://image.thum.io/get/width/1200/crop/800/{url}"
        response = requests.get(screenshot_url)
        response.raise_for_status()
        abrir_imagem(response.content, screenshot_url)
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n[+] Captura de tela exibida com sucesso!" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao capturar a tela: {e}" + Style.RESET_ALL)


def analisar_dominio(url):
    try:
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nAnalisando: {url}" + Style.RESET_ALL)
        response = requests.get(url)
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n[+] Status: {response.status_code}" + Style.RESET_ALL)
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n[+] Headers HTTP" + Style.RESET_ALL)
        for header, value in response.headers.items():
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{header}: {value}")
        soup = BeautifulSoup(response.text, 'html.parser')
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n[+] Links encontrados" + Style.RESET_ALL)
        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{full_url}")
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n[+] Scripts externos encontrados" + Style.RESET_ALL)
        for script in soup.find_all('script', src=True):
            full_url = urljoin(url, script['src'])
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{full_url}")
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n[+] Iframes encontrados" + Style.RESET_ALL)
        for iframe in soup.find_all('iframe', src=True):
            full_url = urljoin(url, iframe['src'])
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{full_url}")
        captura_tela(url)
    except requests.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao acessar o site: {e}" + Style.RESET_ALL)


url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o domínio ou URL (ex: https://exemplo.com): " + Style.RESET_ALL)
analisar_dominio(url)

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========" + Style.RESET_ALL)
