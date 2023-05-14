import tkinter as tk
import requests
import pyperclip
from geopy.geocoders import Nominatim
import webbrowser

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
root.title("Localização CEP")
root.geometry('1000x800')
root.configure(bg='dark blue')

cep_label = tk.Label(root, text="Digite o CEP (somente números):", fg='white', bg='dark blue',font=("Arial Bold", 12))
cep_label.grid(row=0, column=0, padx=5, pady=15, sticky='w')

cep_entry = tk.Entry(root, width=40,font=("Arial Bold", 12))
cep_entry.grid(row=0, column=1, padx=10, pady=10)

consultar_button = tk.Button(root, text="Consultar", command=get_address_info,font=("Arial Bold", 12))
consultar_button.grid(row=0, column=2, padx=5, pady=5)

rua_label = tk.Label(root, text="", fg='white', bg='dark blue',font=("Arial Bold", 12))
rua_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')

bairro_label = tk.Label(root, text="", fg='white', bg='dark blue',font=("Arial Bold", 12))
bairro_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')

cidade_label = tk.Label(root, text="", fg='white', bg='dark blue',font=("Arial Bold", 12))
cidade_label.grid(row=3, column=0, padx=5, pady=5, sticky='w')

latitude_label = tk.Label(root, text="", fg='white', bg='dark blue',font=("Arial Bold", 12))
latitude_label.grid(row=4, column=0, padx=5, pady=5, sticky='w')

longitude_label = tk.Label(root, text="", fg='white', bg='dark blue',font=("Arial Bold", 12))
longitude_label.grid(row=5, column=0, padx=5, pady=5, sticky='w')

exit_button = tk.Button(root, text="SAIR", command=root.quit, bg='red',font=("Arial Bold", 12))
exit_button.grid(row=120, column=3, pady=500, padx=5)

# Copiar tudo
def copy_all():
    text = '\n'.join([rua_label.cget('text'), bairro_label.cget('text'), cidade_label.cget('text'), latitude_label.cget('text'), longitude_label.cget('text')])
    pyperclip.copy(text)
copy_all_button = tk.Button(root, text="Copiar tudo", command=copy_all,font=("Arial Bold", 12))
copy_all_button.grid(row=120, column=1, padx=10, pady=5, sticky='w')


# Abrir Google Maps
def open_google_maps():
    latitude = latitude_label.cget("text").split(":")[1].strip()
    longitude = longitude_label.cget("text").split(":")[1].strip()
    url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
    webbrowser.open(url)

google_maps_button = tk.Button(root, text="Abrir Google Maps", command=open_google_maps, font=("Arial Bold", 12))
google_maps_button.grid(row=120, column=0, pady=5)

# Limpar tudo
def limpar_tudo():
    cep_entry.delete(0, tk.END)
    rua_label.config(text="")
    bairro_label.config(text="")
    cidade_label.config(text="")
    latitude_label.config(text="")
    longitude_label.config(text="")

limpar_tudo_button = tk.Button(root, text="Limpar tudo", command=limpar_tudo, bg='#7FFF00', font=("Arial Bold", 12))
limpar_tudo_button.grid(row=120, column=2, padx=10, pady=5, sticky='e')

root.mainloop()
