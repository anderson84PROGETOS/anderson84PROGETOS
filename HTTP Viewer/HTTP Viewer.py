import tkinter as tk
from tkinter import ttk, scrolledtext, Canvas
import requests
from PIL import Image, ImageTk
import socket
from urllib.parse import urlparse
from io import BytesIO
import re

# Cabeçalhos personalizados
headers_customizados = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Função principal de busca
def buscar_dados():
    url = entrada_url.get()
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        ip = socket.gethostbyname(hostname)
        porta = parsed_url.port if parsed_url.port else \
                (80 if parsed_url.scheme == "http" else 443 if parsed_url.scheme == "https" else "Desconhecida")

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

        aba_resposta_texto.delete(1.0, tk.END)
        aba_resposta_texto.insert(tk.END, resposta.text[:10000])

        html_content = resposta.text[:10000]
        urls_encontradas = re.findall(r'https?://[^\s\'"<>]+', html_content)
        texto_urls = "\n".join(sorted(set(urls_encontradas))) if urls_encontradas else "Nenhuma URL http(s) encontrada."
        aba_iniciador_texto.delete(1.0, tk.END)
        aba_iniciador_texto.insert(tk.END, texto_urls)

        # Screenshot completa (sem crop)
        screenshot_url = f"https://image.thum.io/get/fullpage/{url}"
        try:
            screen_response = requests.get(screenshot_url, timeout=15)
            img_data = BytesIO(screen_response.content)
            img = Image.open(img_data)

            # Redimensionar mantendo proporção, se necessário
            max_width = 1220
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)

            tk_img = ImageTk.PhotoImage(img)

            # Atualizar canvas com rolagem
            aba_visualizacao_canvas.delete("all")
            aba_visualizacao_canvas.image = tk_img  # manter referência
            aba_visualizacao_canvas.create_image(0, 0, anchor='nw', image=tk_img)
            aba_visualizacao_canvas.config(scrollregion=aba_visualizacao_canvas.bbox("all"))
            aba_visualizacao_texto.config(text="")

        except Exception:
            aba_visualizacao_canvas.delete("all")
            aba_visualizacao_texto.config(text="Screenshot não disponível ou não encontrada")
    except Exception as e:
        aba_geral_texto.delete(1.0, tk.END)
        aba_geral_texto.insert(tk.END, f"Erro: {e}")
        aba_visualizacao_canvas.delete("all")
        aba_visualizacao_texto.config(text="")

# Janela principal
root = tk.Tk()
root.title("HTTP Viewer")
root.geometry("1200x900")
root.wm_state('zoomed')

# Entrada de URL
frame_url = ttk.Frame(root)
frame_url.pack(pady=10, padx=10, fill='x')

label_url = ttk.Label(frame_url, text="Digite a URL do website:")
label_url.pack(side='left', padx=(0, 5))

entrada_url = ttk.Entry(frame_url)
entrada_url.pack(side='left', fill='x', expand=True)

botao_buscar = ttk.Button(frame_url, text="Buscar", command=buscar_dados)
botao_buscar.pack(side='left', padx=5)

# Abas
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

# Aba Visualização (com Canvas + Scroll)
frame_visualizacao = ttk.Frame(abas)
aba_visualizacao_canvas = Canvas(frame_visualizacao, bg='white', width=1000, height=620)
scrollbar_v = ttk.Scrollbar(frame_visualizacao, orient='vertical', command=aba_visualizacao_canvas.yview)
aba_visualizacao_canvas.configure(yscrollcommand=scrollbar_v.set)

aba_visualizacao_canvas.pack(side='left', fill='both', expand=True)
scrollbar_v.pack(side='right', fill='y')

aba_visualizacao_texto = ttk.Label(frame_visualizacao, text="")
aba_visualizacao_texto.pack()

abas.add(frame_visualizacao, text="Visualização")

# Loop principal
root.mainloop()
