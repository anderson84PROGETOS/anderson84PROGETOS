import mmh3
import requests
import codecs

# instalar: pip install -r requirements.txt

# Solicita ao usuário que digite a URL do site
favicon_url = input('\nDigite a URL completa do favicon: ')

# Obtém o favicon
response = requests.get(favicon_url)

# Calcula o hash do favicon
if response.status_code == 200:
    favicon = codecs.encode(response.content, "base64")
    favicon_hash = mmh3.hash(favicon)
    print(f"\nO hash do favicon de {favicon_url} é: {favicon_hash}")
    
    print(f"\n[!] http.favicon.hash:{favicon_hash}")
    
    print(f"\n[*] ↓↓ Ver Resultados ↓↓")
    
    print(f"\n> https://www.shodan.io/search?query=http.favicon.hash%3A{favicon_hash}")
    
else:
    print(f"\nNão foi possível obter o favicon de {favicon_url}")
    
input("\nResultado Terminado [ENTER SAIR]\n")    
