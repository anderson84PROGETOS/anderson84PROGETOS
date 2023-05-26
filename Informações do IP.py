import requests
import json
import tkinter as tk
import socket

def get_external_ip_info():
    response = requests.get("https://ipinfo.io/ip")
    external_ip = response.text.strip()
    return external_ip
  
def get_internal_ip():
    hostname = socket.gethostname()
    internal_ip = socket.gethostbyname(hostname)
    return internal_ip

def get_additional_info():
    response = requests.get("https://wtfismyip.com/json")
    data = response.json()
    return data

def get_ip_info():
    external_ip = get_external_ip_info()
    internal_ip = get_internal_ip()
    additional_info = get_additional_info()
    
    ip_info = {
        "Additional Info": additional_info,
        "Externo IP": external_ip,
        "Interno IP": internal_ip,        
    }
    return ip_info

def show_ip_info():
    ip_info = get_ip_info()
    ip_info_str = json.dumps(ip_info, indent=4)
    text.insert(tk.END, ip_info_str)

# Cria uma janela
window = tk.Tk()
window.title("Informações do IP")
window.geometry("700x550")

# Cria uma caixa de texto
text = tk.Text(window, height=30, width=80)
text.pack()

# Cria um botão
button = tk.Button(window, text="Obter Informações do IP", command=show_ip_info)
button.pack()

# Inicia o loop da interface gráfica
window.mainloop()
