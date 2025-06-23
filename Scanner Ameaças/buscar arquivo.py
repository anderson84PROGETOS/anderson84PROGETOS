import os
from tqdm import tqdm
import time
from colorama import init, Fore, Style

# Inicializa colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██████╗ ██╗   ██╗███████╗ ██████╗ █████╗ ██████╗      █████╗ ██████╗  ██████╗ ██╗   ██╗██╗██╗   ██╗ ██████╗ 
██╔══██╗██║   ██║██╔════╝██╔════╝██╔══██╗██╔══██╗    ██╔══██╗██╔══██╗██╔═══██╗██║   ██║██║██║   ██║██╔═══██╗
██████╔╝██║   ██║███████╗██║     ███████║██████╔╝    ███████║██████╔╝██║   ██║██║   ██║██║██║   ██║██║   ██║
██╔══██╗██║   ██║╚════██║██║     ██╔══██║██╔══██╗    ██╔══██║██╔══██╗██║▄▄ ██║██║   ██║██║╚██╗ ██╔╝██║   ██║
██████╔╝╚██████╔╝███████║╚██████╗██║  ██║██║  ██║    ██║  ██║██║  ██║╚██████╔╝╚██████╔╝██║ ╚████╔╝ ╚██████╔╝
╚═════╝  ╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═══╝   ╚═════╝ 
                                                                                                          
""")

def buscar_arquivo(caminho_raiz, nome_arquivo):
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n🔍 Procurando por: {nome_arquivo}\n")
    encontrados = []

    # Cria lista com todas as pastas a percorrer
    lista_pastas = list(os.walk(caminho_raiz))

    # Substitui a barra original pela nova barra com 100 iterações
    pbar = tqdm(total=100)
    for i in range(100):
        time.sleep(0.05)
        pbar.update(1)
    pbar.close()

    # Mantém a lógica de busca, mas sem atualizar a barra durante o loop
    for pasta_atual, subpastas, arquivos in lista_pastas:
        if nome_arquivo in arquivos:
            caminho_completo = os.path.join(pasta_atual, nome_arquivo)
            encontrados.append(caminho_completo)

    if encontrados:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n[✔] Arquivo Encontrado\n")
        for caminho in encontrados:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + caminho,"\n")
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n❌ Arquivo não encontrado.\n")

    return encontrados

if __name__ == "__main__":
    nome = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome exato do arquivo (ex: arquivo.txt): ").strip()
    caminho = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o caminho para iniciar a busca (ex: C:\\): ").strip()

    if not os.path.exists(caminho):
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\n❗ Caminho inválido.\n")
    else:
        buscar_arquivo(caminho, nome)

input(Fore.LIGHTRED_EX + "\n========== PRESSIONE ENTER PARA SAIR ==========\n")
