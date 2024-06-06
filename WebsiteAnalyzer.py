import tkinter as tk
from tkinter import scrolledtext
import urllib.request
import urllib.error
import socket
import requests
import webbrowser

def analyze_and_check_website():
    url = website_entry.get()
    try:
        response = urllib.request.urlopen("http://" + url, timeout=5)
        result_text.insert(tk.END, '\nCabeçalhos HTTP do Response\n')
        result_text.insert(tk.END, response.headers)
        
        status_code = response.getcode()
        result_text.insert(tk.END, f'\nStatus da conexão: {status_code}')
        if status_code == 200:
            result_text.insert(tk.END, f'\nConexão com o {url} estabelecida com sucesso!\n\n')
        else:
            result_text.insert(tk.END, f'\nErro ao conectar-se ao {url}: {response.reason}')
    except urllib.error.HTTPError as e:
        if e.code == 403:
            result_text.insert(tk.END, '\n============== Cabeçalhos HTTP ===============\n\n')
            result_text.insert(tk.END, e.headers)            
        else:
            result_text.insert(tk.END, f'\nErro ao conectar-se ao {url}: {e}')
    except Exception as e:
        result_text.insert(tk.END, f'\nErro ao conectar-se ao {url}: {e}')

def get_ipv4_addresses():
    site = website_entry.get()
    try:
        ipv4_addresses = socket.gethostbyname_ex(site)[2]
        if ipv4_addresses:
            result_text.insert(tk.END, "\n============== Endereços IPv4 Encontrados ===============\n\n")
            for ipv4_address in ipv4_addresses:
                result_text.insert(tk.END, ipv4_address + "\n")
        else:
            result_text.insert(tk.END, "\nNenhum Endereço IPv4 encontrado.")
    except socket.gaierror as e:
        result_text.insert(tk.END, f'\nErro ao resolver o endereço IP do {site}: {e}')

def get_geolocation_info():
    ip = socket.gethostbyname(website_entry.get())
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                result_text.insert(tk.END, "\n============== Informações de Geolocalização ===============\n\n")
                result_text.insert(tk.END, f"Provedor de Internet: {data['isp']}\n")
                result_text.insert(tk.END, f"País: {data['country']}\n")
                result_text.insert(tk.END, f"Cidade: {data['city']}\n")        
                result_text.insert(tk.END, f"Latitude: {data['lat']}\n")
                result_text.insert(tk.END, f"Longitude: {data['lon']}\n")
                
                # Adicionando a URL do Google Maps
                lat = data['lat']
                lon = data['lon']
                google_maps_url = f"https://www.google.com/maps/place/{lat},{lon}"
                result_text.insert(tk.END, f"\nURL do Google Maps: {google_maps_url}\n")
            else:
                result_text.insert(tk.END, "Erro ao obter informações de geolocalização: status não é 'success'\n")
        else:
            result_text.insert(tk.END, f"Erro ao obter informações de geolocalização: {response.status_code}\n")
    except Exception as e:
        result_text.insert(tk.END, f"Erro ao obter informações de geolocalização: {e}\n")

def obter_informacoes_website():
    endereco = website_entry.get()
    user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'}
    try:
        resposta = requests.get(f"http://ip-api.com/json/{endereco}")
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados['status'] == 'success':
                result_text.insert(tk.END, "\n========= Informações sobre o website ==============\n\n")                
                result_text.insert(tk.END, f"\nIP: {dados['query']}\n")
                result_text.insert(tk.END, f"\nPaís: {dados['country']}\n")
                result_text.insert(tk.END, f"\nCidade: {dados['city']}\n")
                result_text.insert(tk.END, f"\nProvedor de Internet: {dados['isp']}\n")

                if 'lat' in dados and 'lon' in dados:
                    lat = dados['lat']
                    lon = dados['lon']
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'}
                    endereco_completo = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json", headers=headers)
                    if endereco_completo.status_code == 200:
                        endereco_completo = endereco_completo.json()
                        result_text.insert(tk.END, f"\nNome da Rua: {endereco_completo['display_name']}\n")
                    else:
                        result_text.insert(tk.END, f"Erro ao obter informações do Nominatim: {endereco_completo.status_code}\n")
            else:
                result_text.insert(tk.END, "Não foi possível obter informações para este endereço.\n")
        else:
            result_text.insert(tk.END, f"Erro ao obter informações do site: {resposta.status_code}\n")
    except Exception as e:
        result_text.insert(tk.END, f"Ocorreu um erro: {e}\n")

def open_google_maps():
    ip = socket.gethostbyname(website_entry.get())
    response = requests.get(f"http://ip-api.com/json/{ip}")
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            lat = data['lat']
            lon = data['lon']
            google_maps_url = f"https://www.google.com/maps/place/{lat},{lon}"
            webbrowser.open(google_maps_url)

window = tk.Tk()
window.wm_state('zoomed')
window.title("Website Analyzer")

# Criar o frame para a entrada do website
input_frame = tk.Frame(window)
input_frame.grid(column=0, row=0, columnspan=2, padx=5, pady=2)

# Label e entrada para o nome do website
website_label = tk.Label(input_frame, text="Digite o nome do Website", font=("Arial", 12))
website_label.grid(column=0, row=0)

website_entry = tk.Entry(input_frame, width=30, font=("Arial", 12))
website_entry.grid(column=0, row=1, padx=5, pady=5)

# Adicionando um espaço vazio entre a entrada de texto e os botões
empty_space = tk.Label(input_frame)
empty_space.grid(column=0, row=2)

# Botão "Analisar Website"
button_analyze = tk.Button(input_frame, text="Analisar Website Cabeçalhos HTTP", command=analyze_and_check_website)
button_analyze.grid(column=0, row=3, pady=5)

# Botão "Exibir Endereços IPv4"
button_ipv4 = tk.Button(input_frame, text="Exibir Endereços IPv4", command=get_ipv4_addresses)
button_ipv4.grid(column=0, row=4, pady=5)

# Botão "Obter Geolocalização"
button_geolocation = tk.Button(input_frame, text="Obter Geolocalização", command=get_geolocation_info)
button_geolocation.grid(column=0, row=5, pady=5)

# Botão "Obter Informações do Website"
button_website_info = tk.Button(input_frame, text="Obter Informações do Website", command=obter_informacoes_website)
button_website_info.grid(column=0, row=6, pady=5)

# Botão "Abrir Mapa no Google Maps"
button_open_maps = tk.Button(input_frame, text="Abrir Mapa no Google Maps", command=open_google_maps, bg="#0bfc03")
button_open_maps.grid(column=0, row=7, pady=10)

# Ajustando a disposição do input_frame para centralizar os botões verticalmente
input_frame.grid_rowconfigure(3, weight=1)
input_frame.grid_rowconfigure(4, weight=1)
input_frame.grid_rowconfigure(5, weight=1)
input_frame.grid_rowconfigure(6, weight=1)
input_frame.grid_rowconfigure(7, weight=1)

# Criar o frame para os resultados
result_frame = tk.Frame(window)
result_frame.grid(column=0, row=7, columnspan=2, padx=5, pady=2)

# Criar o widget ScrolledText para os resultados
result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=135, height=36, font=("Arial", 12))
result_text.grid(column=0, row=0, sticky=tk.W)

window.mainloop()

