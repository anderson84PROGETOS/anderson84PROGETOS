import tkinter as tk
import requests
import pyperclip
from geopy.geocoders import Nominatim

def get_address_info():
    cep = cep_entry.get()
    url = f"https://viacep.com.br/ws/{cep}/json/"
    response = requests.get(url)

    if response.status_code == 200:
        endereco = response.json()
        uf = endereco['uf']
        regiao_url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}"
        regiao_response = requests.get(regiao_url)
        if regiao_response.status_code == 200:
            regiao = regiao_response.json()['regiao']['nome']
        else:
            regiao = "Desconhecido"
        geolocator = Nominatim(user_agent="geoapiExercises")
        location = geolocator.geocode(f"{endereco['logradouro']}, {endereco['localidade']}, {endereco['uf']}, Brasil")
        if location:
            latitude = location.latitude
            longitude = location.longitude
            location = geolocator.reverse(f"{latitude}, {longitude}", exactly_one=True)
            rua_label.config(text=f"Rua:    {endereco['logradouro']}")
            bairro_label.config(text=f"Bairro: {endereco['bairro']}")
            cidade_label.config(text=f"Cidade: {endereco['localidade']}")            
            latitude_label.config(text=f"Latitude: {latitude}")
            longitude_label.config(text=f"Longitude: {longitude}")
            copy_button.config(state="normal")
        else:
            rua_label.config(text="")
            bairro_label.config(text="")
            cidade_label.config(text="")            
            latitude_label.config(text="")
            longitude_label.config(text="impossível obter localização CEP")
            copy_button.config(state="disabled")
    else:
        rua_label.config(text="")
        bairro_label.config(text="")
        cidade_label.config(text="")        
        latitude_label.config(text="")
        longitude_label.config(text="impossível obter informações CEP ")
        copy_button.config(state="disabled")

def get_ip_info(ip_address):
    url = f"http://ip-api.com/json/{ip_address}"
    response = requests.get(url)
    if response.status_code == 200:
        ip_info = response.json()
        rua_label.config(text=f"País: {ip_info['country']}")
        bairro_label.config(text=f"Cidade: {ip_info['city']}")
        cidade_label.config(text=f"Região: {ip_info['regionName']}")
        latitude_label.config(text=f"Latitude: {ip_info['lat']}")
        longitude_label.config(text=f"Longitude: {ip_info['lon']}")
        copy_button.config(state="normal")
    else:
        rua_label.config(text="")
        bairro_label.config(text="")
        cidade_label.config(text="")        
        latitude_label.config(text="")
        longitude_label.config(text="impossível obter informações IP")
        copy_button.config(state="disabled")

def copy_lat_long():
    latitude = latitude_label.cget("text").split(":")[1].strip()
    longitude = longitude_label.cget("text").split(":")[1].strip()
    lat_long = f"{latitude}, {longitude}"
    pyperclip.copy(lat_long)
    copy_button.config(text="Copiado!", state="disabled")

def search_info():
    cep = cep_entry.get()
    ip_address = ip_entry.get()

    if cep:
        get_address_info()
    elif ip_address:
        get_ip_info(ip_address)

def copy_lat_long():
    latitude = latitude_label.cget("text").split(":")[1].strip()
    longitude = longitude_label.cget("text").split(":")[1].strip()
    lat_long = f"{latitude}, {longitude}"
    pyperclip.copy(lat_long)
    copy_button.config(text="Copiado!", state="disabled")
    root.after(2000, lambda: copy_button.config(text="Copiar latitude e longitude", state="normal"))


root = tk.Tk()
root.title("Consultar CEP IP")
root.geometry('600x440')
root.configure(bg='dark blue')

# create the widgets
cep_label = tk.Label(root, text="Digite o CEP:")
cep_entry = tk.Entry(root, width=30)

cep_label = tk.Label(root, text="Digite o CEP:")
cep_entry = tk.Entry(root, width=30)

ip_label = tk.Label(root, text="Digite o endereço IP:")
ip_entry = tk.Entry(root, width=30)

search_button = tk.Button(root, text="Pesquisar", command=search_info)
rua_label = tk.Label(root, text="")

rua_label = tk.Label(root, text="", fg='white', bg='dark blue')
rua_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')

bairro_label = tk.Label(root, text="", fg='white', bg='dark blue')
bairro_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')

cidade_label = tk.Label(root, text="", fg='white', bg='dark blue')
cidade_label.grid(row=3, column=0, padx=5, pady=5, sticky='w')

latitude_label = tk.Label(root, text="", fg='white', bg='dark blue')
latitude_label.grid(row=4, column=0, padx=5, pady=5, sticky='w')

longitude_label = tk.Label(root, text="", fg='white', bg='dark blue')
longitude_label.grid(row=5, column=0, padx=5, pady=5, sticky='w')

copy_button = tk.Button(root, text="Copiar Latitude e Longitude", state="disabled", command=copy_lat_long)
cep_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)

cep_entry.grid(row=0, column=1, padx=5, pady=5)
ip_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
ip_entry.grid(row=1, column=1, padx=5, pady=5)
search_button.grid(row=2, column=1, padx=5, pady=5)
rua_label.grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
bairro_label.grid(row=4, column=0, padx=5, pady=5, sticky=tk.E)
cidade_label.grid(row=5, column=0, padx=5, pady=5, sticky=tk.E)
latitude_label.grid(row=6, column=0, padx=5, pady=5, sticky=tk.E)
longitude_label.grid(row=7, column=0, padx=5, pady=5, sticky=tk.E)

# Create button to copy latitude and longitude to clipboard
copy_button = tk.Button(text="Copiar latitude e longitude", command=copy_lat_long, state="disabled")
copy_button.grid(row=100, column=1, padx=10, pady=5, sticky='w') 

root.mainloop()
