from tkinter import *
from tkinter.ttk import Progressbar
from pytube import YouTube
from moviepy.audio.fx.audio_fadein import audio_fadein
import pyperclip
import os

def download():
    # Obter o tipo de download (vídeo ou áudio) a partir do valor selecionado no menu
    download_type = download_menu.get()
    
    # Obter a URL do vídeo a partir do valor inserido no campo de entrada
    url = url_entry.get()
    
    # Verificar se a URL é válida
    if "youtube.com" not in url:
        status_label.config(text="A URL fornecida não é do YouTube.")
        return
    
    # Copiar a URL do YouTube da área de transferência
    pyperclip.copy(url)

    # Baixar o vídeo ou o áudio
    status_label.config(text="Aguarde enquanto o download é realizado...")
    yt = YouTube(url)
    if download_type == 'Vídeo':
        video = yt.streams.get_highest_resolution()
        video_file = video.download()
        status_label.config(text="O vídeo foi salvo com sucesso com o nome do arquivo original.")
    elif download_type == 'Áudio':
        audio = yt.streams.get_audio_only()
        output_filename = os.path.splitext(audio.default_filename)[0] + '.mp3'
        audio_file = audio.download(filename=output_filename)
        status_label.config(text="O arquivo de áudio MP3 foi salvo com sucesso com o nome do arquivo original.")
    else:
        status_label.config(text="Tipo de download inválido. Digite Vídeo ou Áudio.")
        return
    
    # Atualizar a barra de progresso para 100%
    progress_bar['value'] = 100
    
    # Exibir a mensagem de conclusão e limpar o campo de entrada
    url_entry.delete(0, END)
    status_label.config(text="Download concluído.")

def update_progress(stream, chunk, file_handle, bytes_remaining):
    # Atualizar o valor da barra de progresso com base no número de bytes baixados
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percent_complete = int(bytes_downloaded / total_size * 100)
    progress_bar['value'] = percent_complete
    root.update_idletasks()

# Criar a janela principal
root = Tk()
root.geometry('450x420')
root.title("Baixar Vídeos e Musica do YouTube")

# Criar o rótulo e o campo de entrada para a URL
url_label = Label(root, text="URL do vídeo:")
url_label.pack()
url_entry = Entry(root, width=50)
url_entry.pack()

# Criar o menu para selecionar o tipo de download
download_label = Label(root, text="Tipo de download:")
download_label.pack()
download_options = ['Vídeo', 'Áudio']
download_menu = StringVar(root)
download_menu.set(download_options[0])
download_dropdown = OptionMenu(root, download_menu, *download_options)
download_dropdown.pack()

# Criar a barra de progresso
progress_bar = Progressbar(root, orient=HORIZONTAL, length=300, mode='determinate')
progress_bar.pack()

# Criar o botão para iniciar o download
download_button = Button(root, text="Baixar", command=lambda: download())
download_button.pack()

# Criar o rótulo para exibir o status do download
status_label = Label(root, text="")
status_label.pack()

# Iniciar a janela principal
root.mainloop()
