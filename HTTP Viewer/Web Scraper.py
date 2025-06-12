import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from tkinter import Canvas
import requests
from PIL import Image, ImageTk
import socket
from urllib.parse import urlparse, urljoin
from io import BytesIO
import os
from bs4 import BeautifulSoup

# Cabeçalhos personalizados
headers_customizados = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

img_original = None  # Variável global para salvar imagem original
html_atual = ""      # Guardar HTML atual para extrair informações e scripts

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

        # Ignorar src em base64 ou inválidos
        if src_url.startswith('data:'):
            continue

        try:
            resp_img = requests.get(src_url, headers=headers_customizados, timeout=15)
            resp_img.raise_for_status()

            # Determinar extensão correta; se não identificada, usa .png
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
    if not url.startswith(("http://", "https://")):
        url = "http://" + url  # Adiciona esquema padrão

    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        if not hostname:
            raise ValueError("URL inválida: hostname não encontrado.")

        ip = socket.gethostbyname(hostname)
        porta = parsed_url.port if parsed_url.port else (443 if parsed_url.scheme == "https" else 80)

        resposta = requests.get(url, headers=headers_customizados, timeout=15)
        resposta.raise_for_status()

        # Aba Geral
        geral_texto = (
            f"URL Da Solicitação: {resposta.url}\n"
            f"\nEndereço Remoto: {ip}:{porta}\n"
            f"\nMétodo Da Solicitação: {resposta.request.method}\n"
            f"\nCódigo De Status: {resposta.status_code} {resposta.reason}\n"
            f"\nPolítica Do Referenciador: origin"
        )
        aba_geral_texto.delete(1.0, tk.END)
        aba_geral_texto.insert(tk.END, geral_texto)

        # Aba Cabeçalhos
        resposta_sem_ua = requests.get(url)
        cabecalhos_texto = "\n".join(f"{k}: {v}" for k, v in resposta_sem_ua.headers.items())
        aba_cabecalhos_texto.delete(1.0, tk.END)
        aba_cabecalhos_texto.insert(tk.END, cabecalhos_texto)

        # Aba Resposta
        html_atual = resposta.text
        aba_resposta_texto.delete(1.0, tk.END)
        aba_resposta_texto.insert(tk.END, html_atual[:10000])

        # Aba Payload (Scripts)
        soup_payload = BeautifulSoup(html_atual, 'html.parser')
        script_tags = soup_payload.find_all('script')
        payload_text = ""
        for script in script_tags:
            if script.has_attr('src'):
                script_url = urljoin(url, script['src'])
                try:
                    resp_script = requests.get(script_url, headers=headers_customizados, timeout=15)
                    resp_script.raise_for_status()
                    payload_text += f"<!-- Script from {script_url} -->\n{resp_script.text}\n\n"
                except Exception as ex:
                    payload_text += f"<!-- Erro ao carregar script de {script_url}: {ex} -->\n\n"
            else:
                if script.string:
                    payload_text += script.string + "\n\n"
        aba_payload_texto.delete(1.0, tk.END)
        aba_payload_texto.insert(tk.END, payload_text if payload_text.strip() else "Nenhum script encontrado no payload.")

        # Aba Iniciador (Recursos)
        soup_iniciador = BeautifulSoup(html_atual, 'html.parser')
        recursos = []

        # Scripts
        for script in soup_iniciador.find_all('script', src=True):
            recursos.append({
                'tipo': 'Script',
                'url': urljoin(url, script.get('src')),
                'status': 'N/A',
                'tamanho': 'N/A'
            })

        # CSS (via <link>)
        for link in soup_iniciador.find_all('link', href=True):
            if link.get('rel') and 'stylesheet' in link.get('rel'):
                recursos.append({
                    'tipo': 'CSS',
                    'url': urljoin(url, link.get('href')),
                    'status': 'N/A',
                    'tamanho': 'N/A'
                })

        # Imagens
        for img in soup_iniciador.find_all('img', src=True):
            if not img.get('src').startswith('data:'):
                recursos.append({
                    'tipo': 'Imagem',
                    'url': urljoin(url, img.get('src')),
                    'status': 'N/A',  # Corrigido de '756N/A'
                    'tamanho': 'N/A'
                })

        # Obter status e tamanho dos recursos
        for recurso in recursos:
            try:
                resp = requests.head(recurso['url'], headers=headers_customizados, timeout=5)
                recurso['status'] = f"{resp.status_code} {resp.reason}"
                if 'Content-Length' in resp.headers:
                    tamanho = int(resp.headers['Content-Length'])
                    recurso['tamanho'] = f"{tamanho / 1024:.2f} KB"
            except Exception:
                recurso['status'] = 'Erro'
                recurso['tamanho'] = 'N/A'

        # Formatar saída
        iniciador_text = ""
        for idx, recurso in enumerate(recursos, 1):
            iniciador_text += (
                f"Recurso #{idx}\n"
                f"Tipo: {recurso['tipo']}\n"
                f"URL: {recurso['url']}\n"
                f"Status: {recurso['status']}\n"
                f"Tamanho: {recurso['tamanho']}\n"
                f"{'-'*50}\n"
            )
        aba_iniciador_texto.delete(1.0, tk.END)
        aba_iniciador_texto.insert(tk.END, iniciador_text if iniciador_text.strip() else "Nenhum recurso iniciador encontrado.")

        # Aba URLs (Todas as URLs do site, incluindo relativas e meta content)
        soup_urls = BeautifulSoup(html_atual, 'html.parser')
        urls_encontradas = set()  # Usar set para evitar duplicatas

        # Tags e atributos que podem conter URLs
        tags_atributos = [
            ('a', 'href'),         # Links
            ('img', 'src'),        # Imagens
            ('script', 'src'),     # Scripts
            ('link', 'href'),      # CSS, favicon, etc.
            ('iframe', 'src'),     # Iframes
            ('source', 'src'),     # Vídeo/áudio
            ('video', 'src'),      # Vídeo
            ('audio', 'src'),      # Áudio
            ('form', 'action'),    # Formulários
            ('object', 'data'),    # Objetos
            ('embed', 'src'),      # Embeds
            ('area', 'href'),      # Mapas de imagem
            ('track', 'src'),      # Legendas de vídeo
            ('base', 'href'),      # URL base
            ('input', 'src'),      # Inputs de imagem
            ('param', 'value'),    # Parâmetros de objetos
            ('meta', 'content'),   # Meta tags com URLs
        ]

        # Extrair URLs de tags HTML
        for tag, attr in tags_atributos:
            for elemento in soup_urls.find_all(tag, {attr: True}):
                url_encontrada = elemento.get(attr)
                if url_encontrada and not url_encontrada.startswith('data:'):
                    url_absoluta = urljoin(url, url_encontrada)
                    urls_encontradas.add(url_absoluta)

        # Extrair URLs de atributos content em tags <meta> (caso especial)
        for meta in soup_urls.find_all('meta', content=True):
            content = meta.get('content')
            if content and not content.startswith('data:'):
                # Verificar se o content parece ser uma URL
                if content.startswith(('http://', 'https://', '/', './', '../')):
                    url_absoluta = urljoin(url, content)
                    urls_encontradas.add(url_absoluta)

        # Formatar saída
        urls_text = ""
        for idx, url_encontrada in enumerate(sorted(urls_encontradas), 1):
            urls_text += f"URL #{idx}: {url_encontrada}\n"
        aba_urls_texto.delete(1.0, tk.END)
        aba_urls_texto.insert(tk.END, urls_text if urls_text.strip() else "Nenhuma URL encontrada no site ou em tags meta.")

        # Aba Visualização (Screenshot)
        screenshot_url = f"https://image.thum.io/get/fullpage/{url}"
        try:
            screen_response = requests.get(screenshot_url, timeout=15)
            screen_response.raise_for_status()
            img_data = BytesIO(screen_response.content)
            img_original = Image.open(img_data)

            # Redimensionar proporcionalmente
            max_width = 1220
            ratio = max_width / img_original.width
            new_height = int(img_original.height * ratio)
            img_exibicao = img_original.resize((max_width, new_height), Image.LANCZOS)

            tk_img = ImageTk.PhotoImage(img_exibicao)

            # Atualizar canvas com rolagem
            aba_visualizacao_canvas.delete("all")
            aba_visualizacao_canvas.image = tk_img  # Manter referência
            aba_visualizacao_canvas.create_image(0, 0, anchor='nw', image=tk_img)
            aba_visualizacao_canvas.config(scrollregion=(0, 0, max_width, new_height))
            aba_visualizacao_texto.config(text="")
        except Exception as e:
            img_original = None
            aba_visualizacao_canvas.delete("all")
            aba_visualizacao_texto.config(text=f"Screenshot não disponível: {e}")

    except Exception as e:
        aba_geral_texto.delete(1.0, tk.END)
        aba_geral_texto.insert(tk.END, f"Erro: {e}")
        aba_cabecalhos_texto.delete(1.0, tk.END)
        aba_resposta_texto.delete(1.0, tk.END)
        aba_payload_texto.delete(1.0, tk.END)
        aba_iniciador_texto.delete(1.0, tk.END)
        aba_urls_texto.delete(1.0, tk.END)
        aba_visualizacao_canvas.delete("all")
        aba_visualizacao_texto.config(text="")

# Interface gráfica
root = tk.Tk()
root.title("Web Scraper")
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

# Aba URLs
frame_urls = ttk.Frame(abas)
aba_urls_texto = scrolledtext.ScrolledText(frame_urls, wrap=tk.WORD, width=154, height=52)
aba_urls_texto.pack()
abas.add(frame_urls, text="Link URL")

# Aba Payload
frame_payload = ttk.Frame(abas)
aba_payload_texto = scrolledtext.ScrolledText(frame_payload, wrap=tk.WORD, width=154, height=52)
aba_payload_texto.pack()
abas.add(frame_payload, text="Payload")

# Aba Visualização
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

# Aba Salvar Imagens
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
