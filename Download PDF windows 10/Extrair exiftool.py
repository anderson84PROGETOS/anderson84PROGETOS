import os
from datetime import datetime
from PyPDF2 import PdfReader
import geocoder  # Biblioteca para obter informações de geolocalização
import socket  # Para resolver domínios em IPs

# Diretório onde os PDFs estão armazenados
pasta_pdfs = "pdfs"
arquivo_saida = "resultado.txt"

# Lista de domínios relacionados aos PDFs (substitua pelos reais)
dominios_pdfs = {
    "exemplo1.pdf": "exemplo1.com",
    "exemplo2.pdf": "exemplo2.org",
    # Adicione os nomes dos arquivos e seus respectivos domínios
}

# Função para converter bytes em um tamanho legível
def converter_tamanho(bytes):
    for unidade in ['B', 'kB', 'MB', 'GB', 'TB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unidade}"
        bytes /= 1024

# Função para obter permissões de arquivo
def obter_permissoes(caminho_arquivo):
    perm = os.stat(caminho_arquivo).st_mode
    return oct(perm)[-3:]

# Função para obter a geolocalização a partir de um IP ou endereço
def obter_geolocalizacao(ip):
    try:
        g = geocoder.ip(ip)
        if g.ok:
            cidade = g.city
            pais = g.country
            latitude = g.latlng[0]
            longitude = g.latlng[1]
            google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
            return (f"Cidade: {cidade}\n"
                    f"País: {pais}\n"
                    f"Latitude: {latitude}\n"
                    f"Longitude: {longitude}\n"
                    f"URL do Google Maps: {google_maps_url}")
        else:
            return "Geolocalização não encontrada."
    except Exception as e:
        return f"Erro ao buscar geolocalização: {str(e)}"

# Função para resolver o IP a partir de um domínio
def resolver_ip(dominio):
    try:
        ip = socket.gethostbyname(dominio)
        return ip
    except socket.gaierror:
        return "IP não encontrado"

# Função para extrair metadados detalhados de PDFs
def extrair_metadados_pdfs(pasta, arquivo_txt):
    with open(arquivo_txt, 'w', encoding='utf-8', errors='replace') as f:
        for arquivo in os.listdir(pasta):
            if arquivo.endswith(".pdf"):
                caminho_arquivo = os.path.join(pasta, arquivo)
                print(f"Processando: {caminho_arquivo}")

                # Informações sobre o arquivo
                try:
                    estatisticas = os.stat(caminho_arquivo)
                    tamanho_arquivo = converter_tamanho(estatisticas.st_size)
                    modificacao = datetime.fromtimestamp(estatisticas.st_mtime).strftime('%Y:%m:%d %H:%M:%S%z')
                    acesso = datetime.fromtimestamp(estatisticas.st_atime).strftime('%Y:%m:%d %H:%M:%S%z')
                    inode_change = datetime.fromtimestamp(estatisticas.st_ctime).strftime('%Y:%m:%d %H:%M:%S%z')
                    permissoes = obter_permissoes(caminho_arquivo)
                    
                    f.write(f"File Name                       : {arquivo}\n")
                    f.write(f"Directory                       : {pasta}\n")
                    f.write(f"File Size                       : {tamanho_arquivo}\n")
                    f.write(f"File Modification Date/Time     : {modificacao}\n")
                    f.write(f"File Access Date/Time           : {acesso}\n")
                    f.write(f"File Inode Change Date/Time     : {inode_change}\n")
                    f.write(f"File Permissions                : {permissoes}\n")
                    f.write(f"File Type                       : PDF\n")
                    f.write(f"File Type Extension             : pdf\n")
                    f.write(f"MIME Type                       : application/pdf\n")

                    try:
                        # Abrir o PDF e extrair os metadados
                        with open(caminho_arquivo, 'rb') as pdf_file:
                            pdf_reader = PdfReader(pdf_file)
                            info = pdf_reader.metadata
                            page_count = len(pdf_reader.pages)
                            
                            f.write(f"PDF Version                     : {pdf_reader.pdf_header}\n")
                            f.write(f"Linearized                      : {'Yes' if pdf_reader.is_encrypted else 'No'}\n")
                            f.write(f"Page Count                      : {page_count}\n")
                            
                            if info:
                                f.write(f"Producer                        : {getattr(info, 'producer', 'Unknown')}\n")
                                f.write(f"Creator Tool                    : {getattr(info, 'creator', 'Unknown')}\n")
                                f.write(f"Modify Date                     : {getattr(info, 'mod_date', 'Unknown')}\n")
                                f.write(f"Create Date                     : {getattr(info, 'creation_date', 'Unknown')}\n")
                                f.write(f"Title                           : {getattr(info, 'title', 'Unknown')}\n")
                                f.write(f"Author                          : {getattr(info, 'author', 'Unknown')}\n")

                                # Resolver o domínio do PDF em um IP
                                dominio = dominios_pdfs.get(arquivo)
                                if dominio:
                                    ip = resolver_ip(dominio)
                                    f.write(f"Domain                          : {dominio}\n")
                                    f.write(f"IP Address                      : {ip}\n")

                                    # Geolocalização baseada no IP real
                                    if ip != "IP não encontrado":
                                        geo_info = obter_geolocalizacao(ip)
                                        f.write(f"{geo_info}\n")
                                    else:
                                        f.write("\nNão foi possível obter geolocalização.\n")
                                else:
                                    f.write("\nDomínio não encontrado para este PDF\n")

                            else:
                                f.write("\nMetadados do PDF não encontrados.\n")

                    except Exception as e:
                        f.write(f"\nErro ao processar o PDF {arquivo}: {str(e)}\n")

                except Exception as e:
                    f.write(f"\nErro ao processar o arquivo {arquivo}: {str(e)}\n")

                f.write("\n" + "-"*50 + "\n")
                    
    print(f"\n\nResultados salvos em: {arquivo_txt}")

# Chama a função para processar todos os PDFs
extrair_metadados_pdfs(pasta_pdfs, arquivo_saida)


input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
