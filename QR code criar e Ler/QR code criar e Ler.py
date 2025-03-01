import os
import sys
import requests
import qrcode
from colorama import Fore, Style, init
from PIL import Image

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"""

 ██████╗ ██████╗      ██████╗ ██████╗ ██████╗ ███████╗
██╔═══██╗██╔══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
██║   ██║██████╔╝    ██║     ██║   ██║██║  ██║█████╗  
██║▄▄ ██║██╔══██╗    ██║     ██║   ██║██║  ██║██╔══╝  
╚██████╔╝██║  ██║    ╚██████╗╚██████╔╝██████╔╝███████╗
 ╚══▀▀═╝ ╚═╝  ╚═╝     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
                                                                                                
""")

# Função para gerar QR Code
def generate_qr(data, filename, box_size, image_size):
    try:
        if not data.strip():
            raise ValueError(Fore.LIGHTRED_EX + Style.BRIGHT + "\nO texto ou URL não pode estar vazio.")

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nAqui está o QR Code em formato ASCII\n")
        qr.print_ascii()

        url = f"https://api.qrserver.com/v1/create-qr-code/?size={image_size}x{image_size}&data={data}"
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nQR Code gerado e salvo como: {filename} (tamanho: {image_size}x{image_size})\n\nSalvo com sucesso!")
            if sys.platform == "win32":
                os.startfile(filename)
            elif sys.platform == "darwin":
                os.system(f"open {filename}")
            else:
                os.system(f"xdg-open {filename}")
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao gerar o QR Code. Status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro de conexão: {e}")
    except ValueError as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro: {e}")
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro inesperado: {e}")

# Função para listar arquivos .png na pasta
def listar_png_na_pasta():
    pasta_atual = os.getcwd()
    png_files = [f for f in os.listdir(pasta_atual) if f.endswith('.png')]

    if not png_files:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhum arquivo .png encontrado na pasta.")
        return None

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nEscolha um arquivo de imagem PNG\n")
    for idx, file in enumerate(png_files, start=1):
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{idx} = {file}")

    while True:
        try:
            choice = int(input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o número do arquivo PNG: "))
            if 1 <= choice <= len(png_files):
                return os.path.join(pasta_atual, png_files[choice - 1])
            else:
                print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nOpção inválida. Tente novamente.")
        except ValueError:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nPor favor, insira um número válido.")

# Função para ler QR Code usando a API QRServer
def read_qr():
    png_file = listar_png_na_pasta()
    if not png_file:
        return
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nArquivo selecionado: {png_file}")

    try:
        # Abrir o arquivo PNG e enviá-lo para a API
        with open(png_file, 'rb') as f:
            files = {'file': f}
            url = "https://api.qrserver.com/v1/read-qr-code/"
            response = requests.post(url, files=files)

        if response.status_code == 200:
            result = response.json()
            if result[0]["symbol"][0]["data"]:
                qr_data = result[0]["symbol"][0]["data"]
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nQR Code detectado: {qr_data}")
            else:
                print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhum QR Code encontrado na imagem.")
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao ler o QR Code. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro de conexão: {e}")
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao ler o QR Code: {e}")

# Função principal
def main():
    try:
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nEscolha uma opção:\n")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT  + "1 = Criar QR Code")
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "2 = Ler QR Code")

        choice = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite sua escolha (1 ou 2): ")

        if choice == "1":
            # Criar QR Code
            data = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nDigite o texto ou URL para gerar o QR Code: ")

            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\nEscolha o tamanho do QR Code\n")
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "1 = 150x150 | 2 = 200x200 | 3 = 250x250 | 4 = 300x300 | 5 = 350x350")
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "6 = 400x400 | 7 = 450x450 | 8 = 500x500 | 9 = 550x550 | 10 = 600x600")

            while True:
                try:
                    size_choice = int(input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o tamanho do QR Code (1 a 10): "))
                    if 1 <= size_choice <= 10:
                        break
                    else:
                        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nPor favor, digite um número entre 1 e 10.")
                except ValueError:
                    print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nEntrada inválida. Digite um número inteiro entre 1 e 10.")

            size_mapping = {
                1: (1, 150), 2: (2, 200), 3: (3, 250), 4: (4, 300), 5: (5, 350),
                6: (6, 400), 7: (7, 450), 8: (8, 500), 9: (9, 550), 10: (10, 600)
            }
            box_size, image_size = size_mapping[size_choice]

            filename = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar: ").strip()
            if not filename:
                filename = "qrcode"
            if not filename.endswith(".png"):
                filename += ".png"

            if os.path.exists(filename):
                overwrite = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nO arquivo {filename} já existe. Deseja sobrescrever? (s/n): ").lower()
                if overwrite != 's':
                    print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nOperação cancelada.")
                    return

            generate_qr(data, filename, box_size, image_size)

        elif choice == "2":
            # Ler QR Code
            read_qr()

        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nOpção inválida. Escolha 1 ou 2.")

    except KeyboardInterrupt:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nOperação cancelada pelo usuário.")
        sys.exit(0)

if __name__ == "__main__":
    main()
    input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
