from flask import Flask
import webbrowser
import folium
import geocoder
import socket
import subprocess

app = Flask(__name__)

# Iniciar ngrok e expor a porta 8080
subprocess.Popen(['/usr/bin/ngrok', 'http', '8080'])

@app.route('/')
def index():
    # Obter o endereço IP do servidor
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)    

    # Obter as coordenadas geográficas da sua localização atual
    g = geocoder.ip('me')
    latitude, longitude = g.latlng

    # Cria um mapa usando a biblioteca folium
    mapa = folium.Map(location=[latitude, longitude], zoom_start=15)

    # Adiciona um marcador à sua localização atual no mapa
    folium.Marker([latitude, longitude]).add_to(mapa)

    # Salva o mapa em um arquivo HTML
    mapa.save('mapa.html')

    # URL do link que você deseja abrir
    url = 'https://www.youtube.com/'

    # Define o caminho para o executável do Firefox na sua máquina   
    firefox_path = '/usr/lib/firefox-esr/firefox-esr %s'
  
    # Abre o link no navegador com a localização no mapa
    webbrowser.get(firefox_path).open_new_tab(url)   
    # Retorna uma mensagem para a página web
    print('\nSua localização atual é: Latitude {}, Longitude {}'.format(latitude, longitude))
   
    print('\nSeu endereço IP é: {}'.format(ip_address))
    print("\n")
    return 'Sua localização atual é: Latitude {}, Longitude {}'.format(latitude, longitude)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
