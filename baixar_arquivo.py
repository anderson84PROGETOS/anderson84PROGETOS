import requests
from pytube import YouTube

def baixar_arquivo(url, nome_arquivo):
    # Faz a requisição HTTP para baixar o arquivo
    response = requests.get(url)

    # Verifica se o download foi bem-sucedido
    if response.status_code == 200:
        # Abre o arquivo em modo de gravação binária e grava o conteúdo baixado
        with open(nome_arquivo, 'wb') as f:
            f.write(response.content)
        print(f"{nome_arquivo} baixado com sucesso!")
    else:
        print(f"Falha ao baixar {nome_arquivo}.")

# Obtém o tipo de arquivo que o usuário deseja baixar
tipo_arquivo = input("\nDigite 'V'  baixar vídeo YouTube,  'M' baixar música YouTube  'O' outros arquivo: ")

# Verifica se o tipo de arquivo é um vídeo do YouTube
if tipo_arquivo == "v":
    # Obtém o link do vídeo do YouTube
    url = input("\nDigite o URL completo do vídeo do YouTube: ")

    # Cria um objeto YouTube para fazer o download do vídeo
    video = YouTube(url)

    # Seleciona o vídeo com resolução 720p e faz o download
    nome_arquivo = input("\nDigite o nome do arquivo de vídeo (exemplo: video.mp4): ")
    video.streams.filter(res="720p").first().download(filename=nome_arquivo)

    print(f"{nome_arquivo} baixado com sucesso!")

# Verifica se o tipo de arquivo é uma música do YouTube
elif tipo_arquivo == "m":
    # Obtém o link do vídeo do YouTube
    url = input("\nDigite o URL completo do vídeo do YouTube: ")

    # Cria um objeto YouTube para fazer o download do vídeo
    video = YouTube(url)

    # Obtém a primeira faixa de áudio disponível do vídeo e faz o download
    nome_arquivo = input("\nDigite o nome do arquivo de música (exemplo: musica.mp3): ")
    video.streams.filter(only_audio=True).first().download(filename=nome_arquivo)

    print(f"{nome_arquivo} baixado com sucesso!")
       

# Verifica se o tipo de arquivo é outro tipo de arquivo
elif tipo_arquivo == "o":
    # Obtém o nome do arquivo que o usuário deseja baixar
    nome_arquivo = input("\nDigite o nome do arquivo que deseja baixar (exemplo: arquivo.pdf): ")

    # Obtém o link de download do arquivo
    url = input("\nDigite o URL de download do arquivo: ")

    # Chama a função baixar_arquivo para fazer o download do arquivo
    baixar_arquivo(url, nome_arquivo)

# Se o tipo de arquivo não for reconhecido, exibe uma mensagem de erro
else:
    print("Tipo de arquivo inválido")

input("\nbaixado com sucesso! [ENTER SAIR]\n")
