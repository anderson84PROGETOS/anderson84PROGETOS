import os
import re
import requests
from urllib.parse import urljoin
from colorama import Fore, Style, init

init(autoreset=True)

# Banner
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███╗   ███╗███████╗████████╗ █████╗     ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
████╗ ████║██╔════╝╚══██╔══╝██╔══██╗    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██╔████╔██║█████╗     ██║   ███████║    ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
██║╚██╔╝██║██╔══╝     ██║   ██╔══██║    ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
██║ ╚═╝ ██║███████╗   ██║   ██║  ██║    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                                                             
""")

# Headers para evitar erro 403
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def baixar_arquivos(url, destino="downloads"):
    # Criar pastas
    pasta_fotos = os.path.join(destino, "fotos")
    pasta_videos = os.path.join(destino, "videos")
    pasta_links = os.path.join(destino, "links")
    os.makedirs(pasta_fotos, exist_ok=True)
    os.makedirs(pasta_videos, exist_ok=True)
    os.makedirs(pasta_links, exist_ok=True)

    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n[+] Acessando: {url}")
    try:
        resposta = requests.get(url, headers=HEADERS)
        resposta.raise_for_status()
    except Exception as e:
        print("\n[-] Erro ao acessar a página:", e)
        return

    html = resposta.text

    # Regex para capturar links tradicionais (src e href)
    padrao_links = r'(src|href)="([^"]+)"'
    links_tradicionais = re.findall(padrao_links, html, re.IGNORECASE)
    links_tradicionais = [link for _, link in links_tradicionais]

    # Regex para capturar conteúdo de meta tags
    padrao_meta = r'<meta[^>]+content="([^"]+)"'
    links_meta = re.findall(padrao_meta, html, re.IGNORECASE)

    # Combinar todos os links
    todos_links = links_tradicionais + links_meta

    if not todos_links:
        print("\n[-] Nenhum link encontrado.")
        return

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[+] {len(todos_links)} links Encontrados\n")

    # Separar links por categoria
    lista_fotos = []
    lista_videos = []
    lista_outros = []

    for idx, link in enumerate(todos_links, start=1):
        link_absoluto = urljoin(url, link)
        nome_arquivo = os.path.basename(link_absoluto.split("?")[0])

        if re.search(r'\.(jpg|jpeg|png|ico|gif)$', nome_arquivo, re.IGNORECASE):
            lista_fotos.append(link_absoluto)
            destino_arquivo = os.path.join(pasta_fotos, nome_arquivo)
            tipo = "imagem"
        elif re.search(r'\.(mp4|webm|avi|mov|mkv|flv|wmv|m4v)$', nome_arquivo, re.IGNORECASE):
            lista_videos.append(link_absoluto)
            destino_arquivo = os.path.join(pasta_videos, nome_arquivo)
            tipo = "vídeo"
        else:
            lista_outros.append(link_absoluto)
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n[{idx}] Link externo/meta: {link_absoluto}")
            continue

        # Baixar arquivos de imagem e vídeo
        try:
            print(Fore.LIGHTGREEN_EX + f"\n\n[{idx}] Baixando {tipo}: {link_absoluto}\n")
            r = requests.get(link_absoluto, headers=HEADERS, stream=True)
            r.raise_for_status()
            with open(destino_arquivo, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            print(f"\n[-] Erro ao baixar {link_absoluto}: {e}")

    # Salvar links nos arquivos .txt com cabeçalho
    arq_fotos = os.path.join(pasta_links, "links_fotos.txt")
    arq_videos = os.path.join(pasta_links, "links_videos.txt")
    arq_outros = os.path.join(pasta_links, "links_outros.txt")

    with open(arq_fotos, "w", encoding="utf-8") as f:
        f.write(f"[+] {len(lista_fotos)} links de IMAGENS Encontrados\n\n")
        f.write("\n\n".join(lista_fotos))

    with open(arq_videos, "w", encoding="utf-8") as f:
        f.write(f"[+] {len(lista_videos)} links de VÍDEOS Encontrados\n\n")
        f.write("\n\n".join(lista_videos))

    with open(arq_outros, "w", encoding="utf-8") as f:
        f.write(f"[+] {len(lista_outros)} links EXTERNOS/META Encontrados\n\n")
        f.write("\n\n".join(lista_outros))

    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n\n[✓] Download finalizado!\n")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[✓] Links salvos:\n{arq_fotos}\n{arq_videos}\n{arq_outros}")

if __name__ == "__main__":
    site = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL do site: ").strip()
    baixar_arquivos(site)

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
