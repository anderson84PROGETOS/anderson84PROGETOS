import requests
from PIL import Image
from io import BytesIO
from colorama import Fore, Style, init
from urllib.parse import urlparse

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███████╗███╗   ██╗ █████╗ ██████╗     ███████╗██╗  ██╗ ██████╗ ████████╗
██╔════╝████╗  ██║██╔══██╗██╔══██╗    ██╔════╝██║  ██║██╔═══██╗╚══██╔══╝
███████╗██╔██╗ ██║███████║██████╔╝    ███████╗███████║██║   ██║   ██║   
╚════██║██║╚██╗██║██╔══██║██╔═══╝     ╚════██║██╔══██║██║   ██║   ██║   
███████║██║ ╚████║██║  ██║██║         ███████║██║  ██║╚██████╔╝   ██║   
╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝         ╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   
                                                                       
""")

# Solicita a URL do site ao usuário
site_url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL do website (ex: https://exemplo.com): ").strip()

# Extrai o domínio da URL para usar no nome do arquivo
parsed_url = urlparse(site_url)
domain = parsed_url.netloc or parsed_url.path.split('/')[0]  # Obtém o domínio (ex: exemplo.com)
if not domain:
    domain = "screenshot"  # Nome padrão caso a URL seja inválida

# Monta a URL da API (sem necessidade de chave de API)
screenshot_url = f"https://image.thum.io/get/width/1280/crop/800/noanimate/{site_url}"

# Faz o download da imagem
response = requests.get(screenshot_url)

# Verifica se a imagem foi baixada com sucesso
if response.status_code == 200:
    img = Image.open(BytesIO(response.content))
    img.show()  # Mostra a imagem

    # Pergunta se deseja salvar a imagem
    save_choice = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDeseja salvar a imagem? (s/n): ").strip().lower()

    if save_choice == "s":
        filename = f"{domain}.png"  # Nome do arquivo baseado no domínio
        img.save(filename)  # Salva localmente
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nScreenshot salva como: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{filename}")
    else:
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nImagem não foi salva.")
else:
    print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nErro ao capturar imagem.")

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
