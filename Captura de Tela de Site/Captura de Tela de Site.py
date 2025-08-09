import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import threading
import time

def formatar_tempo(segundos):
    minutos = segundos // 60
    seg_restantes = segundos % 60
    if minutos > 0:
        if seg_restantes > 0:
            return f"{minutos} minuto{'s' if minutos > 1 else ''} e {seg_restantes} segundo{'s' if seg_restantes > 1 else ''}"
        else:
            return f"{minutos} minuto{'s' if minutos > 1 else ''}"
    else:
        return f"{segundos} segundo{'s' if segundos > 1 else ''}"

def capturar_site():    
    progress_var.set(0)
    tempo_restante_var.set("Tempo decorrido: 0 segundos")
    barra_progresso.update()
    label_tempo.update()
    janela.update_idletasks()

    site = entrada.get().strip()
    if not site.startswith("http"):
        site = "https://" + site

    url_thumio = f"https://image.thum.io/get/fullpage/{site}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    progresso_fake = True
    tempo_decorrido_segundos = 0
    atualizar_tempo = True

    def atualizar_tempo_decorrido():
        nonlocal tempo_decorrido_segundos
        if not atualizar_tempo:
            return
        tempo_decorrido_segundos += 1
        texto = f"Tempo Decorrido: {tempo_decorrido_segundos} segundo{'s' if tempo_decorrido_segundos > 1 else ''}"
        tempo_restante_var.set(texto)
        label_tempo.update()
        janela.after(1000, atualizar_tempo_decorrido)

    def progresso_barra():
        for i in range(0, 96):
            if not progresso_fake:
                break
            progress_var.set(i)
            barra_progresso.update()
            time.sleep(0.03)

    def baixar_imagem():
        nonlocal progresso_fake, atualizar_tempo, tempo_decorrido_segundos
        try:
            resp = requests.get(url_thumio, headers=headers, stream=True, timeout=60)
            resp.raise_for_status()

            total_length = resp.headers.get('content-length')

            if total_length is None:
                data = resp.content
                janela.after(0, atualizar_tempo_restante, "Tempo Estimado: --")
            else:
                total_length = int(total_length)
                data_bytes = BytesIO()
                downloaded = 0
                chunk_size = 1024
                start_time = time.time()

                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        data_bytes.write(chunk)
                        downloaded += len(chunk)

                        progresso_real = int(downloaded * 100 / total_length)
                        progress_var.set(progresso_real)
                        barra_progresso.update()

                        tempo_decorrido_real = time.time() - start_time
                        if tempo_decorrido_real > 0:
                            velocidade = downloaded / tempo_decorrido_real
                            bytes_restantes = total_length - downloaded
                            segundos_restantes = int(bytes_restantes / velocidade)
                            texto_formatado = f"Tempo Estimado restante: {formatar_tempo(segundos_restantes)}"
                            janela.after(0, atualizar_tempo_restante, texto_formatado)
                        else:
                            janela.after(0, atualizar_tempo_restante, "Tempo Estimado restante: 0 segundos")

            data = data_bytes.getvalue() if total_length else data

            global img_original
            img_original = Image.open(BytesIO(data))

            janela.after(0, atualizar_imagem_display, 1.0)

        except Exception as e:
            def erro():
                canvas.delete("all")
                canvas.create_text(10, 10, anchor="nw", text=f"Erro: {e}", fill="red", font=("Arial", 14))
                tempo_restante_var.set("Erro ao baixar a imagem.")
                label_tempo.update()
                btn.config(state="normal")
            janela.after(0, erro)

        finally:
            progresso_fake = False
            atualizar_tempo = False  # Para de atualizar o tempo decorrido
            progress_var.set(100)
            barra_progresso.update()
            texto_final = f"Download concluído em {tempo_decorrido_segundos} segundo{'s' if tempo_decorrido_segundos > 1 else ''}."
            janela.after(0, atualizar_tempo_restante, texto_final)
            btn.config(state="normal")

    atualizar_tempo_decorrido()
    threading.Thread(target=progresso_barra, daemon=True).start()
    threading.Thread(target=baixar_imagem, daemon=True).start()

def atualizar_tempo_restante(texto):
    tempo_restante_var.set(texto)
    label_tempo.update()

def atualizar_imagem_display(fator_zoom):
    global img_original, img_display, zoom_atual
    if img_original is None:
        return

    zoom_atual = fator_zoom

    largura = int(img_original.width * fator_zoom)
    altura = int(img_original.height * fator_zoom)
    img_resized = img_original.resize((largura, altura), Image.LANCZOS)
    img_display = ImageTk.PhotoImage(img_resized)

    canvas.delete("all")
    canvas.config(scrollregion=(0, 0, largura, altura))
    canvas.create_image(0, 0, anchor="nw", image=img_display)

def zoom_in():
    global zoom_atual
    if img_original is None:
        return
    novo_zoom = zoom_atual * 1.2
    if novo_zoom > 5.0:
        novo_zoom = 5.0
    atualizar_imagem_display(novo_zoom)

def zoom_out():
    global zoom_atual
    if img_original is None:
        return
    novo_zoom = zoom_atual / 1.2
    if novo_zoom < 0.1:
        novo_zoom = 0.1
    atualizar_imagem_display(novo_zoom)

def salvar_imagem():
    if img_original is None:
        messagebox.showwarning("Aviso", "Nenhuma imagem para salvar.")
        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("Todos os arquivos", "*.*")],
        title="Salvar imagem como"
    )
    if caminho:
        try:
            img_original.save(caminho, "PNG")
            messagebox.showinfo("Sucesso", f"Imagem salva em:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar a imagem:\n{e}")

# Variáveis globais
img_original = None
img_display = None
zoom_atual = 1.0

# Janela principal
janela = tk.Tk()
janela.title("Captura de Site (Página Inteira) via thum.io")
janela.geometry("1208x900")

ttk.Label(janela, text="Digite a url do website").pack(pady=5)
entrada = ttk.Entry(janela, width=50)
entrada.pack()

def on_release(event):
    event.widget.config(bg="#03e8fc")

btn = tk.Button(janela, text="Capturar", bg="#05fc32", fg="black", command=capturar_site)
btn.pack(pady=5)
btn.bind("<ButtonRelease>", on_release)

progress_var = tk.IntVar()
barra_progresso = ttk.Progressbar(janela, orient="horizontal", length=400, mode="determinate", variable=progress_var)
barra_progresso.pack(pady=5)

tempo_restante_var = tk.StringVar()
label_tempo = ttk.Label(janela, textvariable=tempo_restante_var)
label_tempo.pack()

frame_canvas = ttk.Frame(janela)
frame_canvas.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(frame_canvas, bg="white")
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scroll_y = ttk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

scroll_x = ttk.Scrollbar(janela, orient="horizontal", command=canvas.xview)
scroll_x.pack(fill=tk.X)

canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

frame_botoes = ttk.Frame(janela)
frame_botoes.pack(pady=10)

btn_zoom_in = ttk.Button(frame_botoes, text="Zoom +", command=zoom_in)
btn_zoom_in.pack(side=tk.LEFT, padx=5)

btn_zoom_out = ttk.Button(frame_botoes, text="Zoom -", command=zoom_out)
btn_zoom_out.pack(side=tk.LEFT, padx=5)

btn_salvar = ttk.Button(frame_botoes, text="Salvar Imagem", command=salvar_imagem)
btn_salvar.pack(side=tk.LEFT, padx=5)

janela.mainloop()
