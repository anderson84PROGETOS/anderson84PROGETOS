import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import webbrowser

# Variável global para armazenar as informações do IP
ip_info = None

def get_ip_info():
    global ip_info
    try:
        ip_address = entry_domain.get()

        # Faz a solicitação HTTP para a API ip-api.com
        url = f"http://ip-api.com/json/{ip_address}"
        response = requests.get(url)

        # Exibe as informações na janela
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)

        # Verifica se a solicitação foi bem-sucedida
        if response.status_code == 200:
            ip_info = response.json()

            # Verifica se a chave 'continent' está presente na resposta            
            continent_info = f"Continent: {ip_info['continent']} ({ip_info['continentCode']})" if 'continent' in ip_info and ip_info['continentCode'] else ''
        
            formatted_info = (
                f"Query IP: {ip_info['query']}\n"
                f"Status: {ip_info['status']}\n"
                f"{continent_info}\n"
                f"Country: {ip_info.get('country', 'N/A')} ({ip_info.get('countryCode', 'N/A')})\n"
                f"Region: {ip_info.get('region', 'N/A')} - {ip_info.get('regionName', 'N/A')}\n"
                f"City: {ip_info.get('city', 'N/A')}\n"
                f"ZIP Code: {ip_info.get('zip', 'N/A')}\n\n"
                f"Latitude: {ip_info.get('lat', 'N/A')}\n"
                f"Longitude: {ip_info.get('lon', 'N/A')}\n\n"
                f"Timezone: {ip_info.get('timezone', 'N/A')}\n"
                f"ISP: {ip_info.get('isp', 'N/A')}\n"
                f"Organization: {ip_info.get('org', 'N/A')}\n"
                f"AS: {ip_info.get('as', 'N/A')}\n\n\n\n"
                f"AS Name: {ip_info.get('asname', 'N/A')}\n"
                f"Mobile: {ip_info.get('mobile', 'N/A')}\n"
                f"Proxy: {ip_info.get('proxy', 'N/A')}\n"
                f"Hosting: {ip_info.get('hosting', 'N/A')}"
            )
            result_text.insert(tk.END, formatted_info)

            # Ativa o botão para abrir o Google Maps
            abrir_mapa_button.config(state=tk.NORMAL)
        else:
            result_text.insert(tk.END, f"Erro na solicitação: {response.status_code}")

        result_text.config(state=tk.DISABLED)

    except Exception as e:
        # Exibe uma mensagem na janela para outros erros
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"Erro desconhecido: {str(e)}")
        result_text.config(state=tk.DISABLED)

def abrir_no_google_maps():
    # Obtém a latitude e longitude do resultado
    latitude = ip_info.get('lat', 'N/A')
    longitude = ip_info.get('lon', 'N/A')

    # Abre o Google Maps no navegador com as coordenadas
    if latitude != 'N/A' and longitude != 'N/A':
        maps_url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
        webbrowser.open(maps_url)

# Cria a janela principal
window = tk.Tk()
window.wm_state('zoomed')
window.title("IP Information Tool")

# Cria os widgets
label_ip = ttk.Label(window, text="Digite o Endereço IP", font=("Arial", 12))
entry_domain = ttk.Entry(window, width=40, font=("Arial", 12))

btn_get_info = tk.Button(window, text="Obter Informações de IP", command=get_ip_info, font=("Arial", 12), bg="#00FFFF")

# Botão para abrir o Google Maps, inicialmente desativado
abrir_mapa_button = tk.Button(window, text="Abrir no Google Maps", command=abrir_no_google_maps, state=tk.DISABLED, font=("Arial", 12), bg="#00FF00")

# Posiciona os widgets na parte superior
label_ip.pack(side=tk.TOP, padx=10, pady=5)
entry_domain.pack(side=tk.TOP, padx=10, pady=5)
btn_get_info.pack(side=tk.TOP, pady=10)
abrir_mapa_button.pack(pady=10)

# Adicionando o result_frame
result_frame = tk.Frame(window)
result_frame.pack()

# ScrolledText para exibir o resultado com tamanho reduzido
result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=130, height=40, font=("Arial", 13))
result_text.grid(column=0, row=0, sticky=tk.W)

# Inicia o loop principal da interface gráfica
window.update()
window.mainloop()
