import socket
import subprocess
import ipaddress
import re
import webbrowser
import tkinter as tk
from tkinter import messagebox
from geopy.geocoders import Nominatim
import pyperclip

def check_website():
    site_name = website_entry.get()

    # Tenta acessar o site usando HTTPS
    url = f'https://{site_name}'
    command = ['curl', '-s', '--head', '-A', user_agent, url]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        status_label.config(text='Site acessado com sucesso usando HTTPS')
        status_label.config(foreground='#008000')
    else:
        # Se não funcionar, tenta acessar usando HTTP
        url = f'http://{site_name}'
        command = ['curl', '-s', '--head', '-A', user_agent, url]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            status_label.config(text='Site acessado com sucesso usando HTTP')
            status_label.config(foreground='#008000')
        else:
            status_label.config(text='Não foi possível acessar o site')
            status_label.config(foreground='#FF0000')

    # Obtém o endereço IP do site
    try:
        ip_address = socket.gethostbyname(site_name)
        ip_label.config(text=f'Endereço IP do site: {ip_address}')

        # Verifica se o endereço IP é válido no formato IPv4
        ipv4_regex = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        if ipv4_regex.match(ip_address):
            ipv4_label.config(text='Endereço IP válido no formato IPv4')

            # Usa o serviço de geocodificação do OpenStreetMap para obter as informações de latitude e longitude
            geolocator = Nominatim(user_agent=user_agent)
            location = geolocator.geocode(site_name)
            if location is not None:
                latitude_label.config(text=f'Latitude: {location.latitude}')
                longitude_label.config(text=f'Longitude: {location.longitude}')
                maps_url = f"https://www.google.com/maps/search/?api=1&query={location.latitude},{location.longitude}"
                webbrowser.open_new_tab(maps_url)
                address_label.config(text=f"Endereço: {location.address}")
            else:
                address_label.config(text='Não foi possível obter o endereço do site')
        else:
            ipv4_label.config(text='Endereço IP inválido')
    except socket.gaierror:
        ip_label.config(text='Não foi possível obter o endereço IP do site')
    except ipaddress.AddressValueError:
        ipv4_label.config(text='Endereço IP inválido')

# Cria a janela
window = tk.Tk()
window.wm_state('zoomed')
window.title('informações de sites')
window.geometry('1200x900')

# Define o cabeçalho User-Agent
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'

# Cria o label e a entrada de texto para o nome do site
website_label = tk.Label(text='Nome Do WebSite   [exemplo.com]')
website_label.pack()

website_entry = tk.Entry(window, width=40)
website_entry.pack()

# Cria o botão para verificar o site
check_button = tk.Button(text='Verificar',command=check_website)
check_button.pack()

#Cria o label para exibir o status da verificação
status_label = tk.Label(text='status')
status_label.pack()

#Cria o label para exibir o endereço IP do site
ip_label = tk.Label(text='')
ip_label.pack()

#Cria o label para exibir se o endereço IP é válido no formato IPv4
ipv4_label = tk.Label(text='')
ipv4_label.pack()

#Cria o label para exibir a latitude do site
latitude_label = tk.Label(text='')
latitude_label.pack()

#Cria o label para exibir a longitude do site
longitude_label = tk.Label(text='')
longitude_label.pack()

#Cria o label para exibir o endereço do site
address_label = tk.Label(text='')
address_label.pack()

# botao de copiar
import pyperclip
def copy_info():
    site_name = website_entry.get()
    ip_address = ip_label.cget("text")
    ipv4 = ipv4_label.cget("text")
    latitude = latitude_label.cget("text")
    longitude = longitude_label.cget("text")
    address = address_label.cget("text")
    info = f"Site: {site_name}\nEndereço IP: {ip_address}\nEndereço IP válido no formato IPv4: {ipv4}\nLatitude: {latitude}\nLongitude: {longitude}\nEndereço: {address}"
    pyperclip.copy(info)    

# Criando o botão para copiar a latitude e longitude para a área de transferência
copy_button = tk.Button(window, text="Copiar todas as informações", command=copy_info)
copy_button.pack(pady=350)

window.mainloop()
