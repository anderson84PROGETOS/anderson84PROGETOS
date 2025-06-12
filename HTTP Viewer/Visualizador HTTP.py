import tkinter as tk
from tkinter import ttk, scrolledtext, Canvas, filedialog, messagebox
import requests
from PIL import Image, ImageTk
import socket
from urllib.parse import urlparse, urljoin
from io import BytesIO
import re
from bs4 import BeautifulSoup
import os

# Cabeçalhos personalizados
headers_customizados = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

img_original = None  # Variável global para salvar imagem original
html_atual = ""  # Guardar HTML atual para extrair imagens

def salvar_imagem():
    global img_original
    if img_original:
        caminho = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("Imagem PNG", "*.png")])
        if caminho:
            img_original.save(caminho, format='PNG')
            messagebox.showinfo("Sucesso", f"Imagem salva em:\n{caminho}")
    else:
        messagebox.showwarning("Aviso", "Nenhuma screenshot carregada para salvar.")

def salvar_todas_imagens():
    global html_atual
    url = entrada_url.get()
    if not html_atual:
        messagebox.showwarning("Aviso", "Nenhum conteúdo HTML carregado para extrair imagens.")
        return

    pasta = filedialog.askdirectory(title="Escolha a pasta para salvar as imagens")
    if not pasta:
        return

    soup = BeautifulSoup(html_atual, 'html.parser')
    tags_img = soup.find_all('img')

    if not tags_img:
        messagebox.showinfo("Resultado", "Nenhuma imagem encontrada no site.")
        return

    baixadas = 0
    erros = 0

    for idx, tag in enumerate(tags_img, 1):
        src = tag.get('src')
        if not src:
            continue
        
        src_url = urljoin(url, src)

        # Alguns src podem ser base64 ou dados inválidos - ignorar estes
        if src_url.startswith('data:'):
            continue

        try:
            resp_img = requests.get(src_url, headers=headers_customizados, timeout=15)
            resp_img.raise_for_status()

            # Pegando extensão correta da URL, se não tiver, usa .png
            ext = os.path.splitext(urlparse(src_url).path)[1]
            if ext.lower() not in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                ext = '.png'

            nome_arquivo = f"imagem_{idx}{ext}"
            caminho_arquivo = os.path.join(pasta, nome_arquivo)

            with open(caminho_arquivo, 'wb') as f:
                f.write(resp_img.content)
            baixadas += 1
        except Exception as e:
            erros += 1
            print(f"Erro ao baixar {src_url}: {e}")

    messagebox.showinfo("Download finalizado",
                        f"Imagens baixadas: {baixadas}\nErros: {erros}")

def buscar_dados():
    global img_original, html_atual
    url = entrada_url.get()
    if not url.startswith("http"):
        url = "http://" + url  # Adiciona esquema padrão

    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        ip = socket.gethostbyname(hostname)
        porta = parsed_url.port if parsed_url.port else (80 if parsed_url.scheme == "http" else 443 if parsed_url.scheme == "https" else "Desconhecida")

        resposta = requests.get(url, headers=headers_customizados)

        geral_texto = (
            f"URL Da Solicitação: {resposta.url}\n"
            f"\nEndereço Remoto: {ip}:{porta}\n"
            f"\nMétodo Da Solicitação: {resposta.request.method}\n"
            f"\nCódigo De Status: {resposta.status_code} {resposta.reason}\n"
            f"\nPolítica Do Referenciador: origin"
        )
        aba_geral_texto.delete(1.0, tk.END)
        aba_geral_texto.insert(tk.END, geral_texto)

        resposta_sem_ua = requests.get(url)
        cabecalhos_texto = "\n".join(f"{k}: {v}" for k, v in resposta_sem_ua.headers.items())
        aba_cabecalhos_texto.delete(1.0, tk.END)
        aba_cabecalhos_texto.insert(tk.END, cabecalhos_texto)

        html_atual = resposta.text  # Salva o HTML para uso posterior

        aba_resposta_texto.delete(1.0, tk.END)
        aba_resposta_texto.insert(tk.END, html_atual[:10000])

        urls_encontradas = re.findall(r'https?://[^\s\'"<>]+', html_atual[:10000])
        texto_urls = "\n".join(sorted(set(urls_encontradas))) if urls_encontradas else "Nenhuma URL http(s) encontrada."
        aba_iniciador_texto.delete(1.0, tk.END)
        aba_iniciador_texto.insert(tk.END, texto_urls)

        # Screenshot completa
        screenshot_url = f"https://image.thum.io/get/fullpage/{url}"
        try:
            screen_response = requests.get(screenshot_url, timeout=15)
            img_data = BytesIO(screen_response.content)
            img_original = Image.open(img_data)

            # Redimensionar proporcionalmente
            max_width = 1220
            ratio = max_width / img_original.width
            new_height = int(img_original.height * ratio)
            img_exibicao = img_original.resize((max_width, new_height), Image.LANCZOS)

            tk_img = ImageTk.PhotoImage(img_exibicao)

            # Mostrar imagem com rolagem
            aba_visualizacao_canvas.delete("all")
            aba_visualizacao_canvas.image = tk_img
            aba_visualizacao_canvas.create_image(0, 0, anchor='nw', image=tk_img)
            aba_visualizacao_canvas.config(scrollregion=(0, 0, max_width, new_height))
            aba_visualizacao_texto.config(text="")

        except Exception:
            img_original = None
            aba_visualizacao_canvas.delete("all")
            aba_visualizacao_texto.config(text="Screenshot não disponível ou não encontrada")

    except Exception as e:
        aba_geral_texto.delete(1.0, tk.END)
        aba_geral_texto.insert(tk.END, f"Erro: {e}")
        aba_visualizacao_canvas.delete("all")
        aba_visualizacao_texto.config(text="")

# Interface gráfica
root = tk.Tk()
root.title("HTTP Viewer")
root.geometry("1200x900")
root.wm_state('zoomed')

frame_url = ttk.Frame(root)
frame_url.pack(pady=10, padx=10, fill='x')

label_url = ttk.Label(frame_url, text="Digite a URL do website:")
label_url.pack(side='left', padx=(0, 5))

entrada_url = ttk.Entry(frame_url)
entrada_url.pack(side='left', fill='x', expand=True)

botao_buscar = ttk.Button(frame_url, text="Buscar", command=buscar_dados)
botao_buscar.pack(side='left', padx=5)

abas = ttk.Notebook(root)
abas.pack(fill='both', expand=True, padx=10, pady=10)

# Aba Geral
frame_geral = ttk.Frame(abas)
aba_geral_texto = scrolledtext.ScrolledText(frame_geral, wrap=tk.WORD, width=154, height=52)
aba_geral_texto.pack()
abas.add(frame_geral, text="Geral")

# Aba Cabeçalhos
frame_cabecalhos = ttk.Frame(abas)
aba_cabecalhos_texto = scrolledtext.ScrolledText(frame_cabecalhos, wrap=tk.WORD, width=154, height=52)
aba_cabecalhos_texto.pack()
abas.add(frame_cabecalhos, text="Cabeçalhos")

# Aba Resposta
frame_resposta = ttk.Frame(abas)
aba_resposta_texto = scrolledtext.ScrolledText(frame_resposta, wrap=tk.WORD, width=154, height=52)
aba_resposta_texto.pack()
abas.add(frame_resposta, text="Resposta")

# Aba Iniciador
frame_iniciador = ttk.Frame(abas)
aba_iniciador_texto = scrolledtext.ScrolledText(frame_iniciador, wrap=tk.WORD, width=154, height=52)
aba_iniciador_texto.pack()
abas.add(frame_iniciador, text="Iniciador")

# Aba Visualização com Canvas e Scrollbar
frame_visualizacao = ttk.Frame(abas)

canvas_frame = tk.Frame(frame_visualizacao)
canvas_frame.pack(fill='both', expand=True)

aba_visualizacao_canvas = Canvas(canvas_frame, bg='white', width=1000, height=700)
scrollbar_v = ttk.Scrollbar(canvas_frame, orient='vertical', command=aba_visualizacao_canvas.yview)
aba_visualizacao_canvas.configure(yscrollcommand=scrollbar_v.set)

scrollbar_v.pack(side='right', fill='y')
aba_visualizacao_canvas.pack(side='left', fill='both', expand=True)

aba_visualizacao_texto = ttk.Label(frame_visualizacao, text="")
aba_visualizacao_texto.pack()

abas.add(frame_visualizacao, text="Visualização")

# Aba para salvar a imagem
frame_salvar = ttk.Frame(abas)
aba_salvar_texto = scrolledtext.ScrolledText(frame_salvar, wrap=tk.WORD, width=154, height=48)
aba_salvar_texto.insert(tk.END, "Clique no botão abaixo para salvar a screenshot da página completa em formato .PNG.\n\n"
                                "Ou clique em 'Salvar todas as imagens' para baixar todas as imagens presentes no site.")
aba_salvar_texto.config(state='disabled')
aba_salvar_texto.pack(pady=10)

botao_salvar = ttk.Button(frame_salvar, text="Salvar Screenshot", command=salvar_imagem)
botao_salvar.pack(pady=5)

botao_salvar_todas = ttk.Button(frame_salvar, text="Salvar todas as imagens do site", command=salvar_todas_imagens)
botao_salvar_todas.pack(pady=5)

abas.add(frame_salvar, text="Salvar Imagens")

root.mainloop()
