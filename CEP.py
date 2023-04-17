import tkinter as tk
import requests
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
        else:
            rua_label.config(text="")
            bairro_label.config(text="")
            cidade_label.config(text="")            
            latitude_label.config(text="")
            longitude_label.config(text="impossível obter localização CEP")
    else:
        rua_label.config(text="")
        bairro_label.config(text="")
        cidade_label.config(text="")        
        latitude_label.config(text="")
        longitude_label.config(text="impossível obter informações CEP ")

root = tk.Tk()
root.title("Consultar CEP")
root.geometry('425x410')
root.configure(bg='dark blue')

cep_label = tk.Label(root, text="Digite o CEP (somente números):", fg='white', bg='dark blue')
cep_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

cep_entry = tk.Entry(root)
cep_entry.grid(row=0, column=1, padx=5, pady=5)

consultar_button = tk.Button(root, text="Consultar", command=get_address_info)
consultar_button.grid(row=0, column=2, padx=5, pady=5)

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

exit_button = tk.Button(root, text="SAIR", command=root.quit, bg='red')
exit_button.grid(row=100, column=2, pady=180)

root.mainloop()
