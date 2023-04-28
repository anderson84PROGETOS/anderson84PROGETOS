import tkinter as tk
import requests
import webbrowser
from geopy.geocoders import Nominatim
import pyperclip

def search_address():
    cep = cep_entry.get()
    url = f"https://viacep.com.br/ws/{cep}/json/"
    
    response = requests.get(url)
    data = response.json()
    
    if "erro" in data:
        error_label.config(text="CEP inválido ou não encontrado.")
        return
    if "logradouro" not in data or "localidade" not in data or "uf" not in data or "cep" not in data or "bairro" not in data:
        error_label.config(text="Não foi possível obter o endereço.")
        return
    logradouro = data["logradouro"]
    bairro = data["bairro"]
    localidade = data["localidade"]
    uf = data["uf"]
    cep = data["cep"]
    
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(f"{logradouro}, {bairro}, {localidade}, {uf}, Brasil")
    if location:
        latitude = location.latitude
        longitude = location.longitude
        location = geolocator.reverse(f"{latitude}, {longitude}", exactly_one=True)

    maps_url = f"https://www.google.com/maps/search/?api=1&query={logradouro}, {bairro}, {localidade}, {uf}"
    webbrowser.open_new_tab(maps_url)

    address_label.config(text=f"Endereço: {logradouro}, {bairro}, {localidade}, {uf}, {cep}")
    latitude_label.config(text=f"Latitude: {latitude}")
    longitude_label.config(text=f"Longitude: {longitude}")
    
def copy_lat_long():
    latitude = latitude_label.cget("text").split(":")[1].strip()
    longitude = longitude_label.cget("text").split(":")[1].strip()
    lat_long = f"{latitude}, {longitude}"
    pyperclip.copy(lat_long)

# Criando a interface gráfica
root = tk.Tk()
root.title("Localizador de CEP")
root.geometry('900x570')

# Criando a entrada de texto para o CEP
cep_label = tk.Label(root, text="Digite o CEP")
cep_label.pack()
cep_entry = tk.Entry(root, width=40)
cep_entry.pack()

# Criando o botão para buscar o endereço
search_button = tk.Button(root, text="Buscar endereço", command=search_address)
search_button.pack()

# Criando a label para exibir erros
error_label = tk.Label(root, fg="red")
error_label.pack()

# Criando a label para exibir o endereço pesquisado
address_label = tk.Label(root, text="")
address_label.pack()

# Criando as labels para exibir latitude e longitude
latitude_label = tk.Label(root, text="")
latitude_label.pack()
longitude_label = tk.Label(root, text="")
longitude_label.pack()

# Criando o botão para copiar a latitude e longitude para a área de transferência
copy_button = tk.Button(root, text="Copiar latitude e longitude", command=copy_lat_long)
copy_button.pack(pady=200)

root.mainloop()
