import requests
import tkinter as tk
from tkinter import messagebox, scrolledtext
import webbrowser

# Variável global para armazenar as informações do CEP
informacoes_cep = {}

def obter_informacoes_cep(cep):
    url = f"https://cep.awesomeapi.com.br/json/{cep}"
    resposta = requests.get(url)

    if resposta.status_code == 200:
        dados = resposta.json()
        return dados
    else:
        messagebox.showerror("Erro", f"Falha na requisição. Código de status: {resposta.status_code}")
        return None

def exibir_resultado(result_text):
    result_text.delete(1.0, tk.END)  # Limpa o texto existente

    if informacoes_cep:
        result_text.tag_configure("red", foreground="#f74134")  # Define a cor da tag "red"        
        result_text.tag_configure("green", foreground="#069906")  # Define a cor da tag "green"        
        result_text.insert(tk.END, f"Informações do CEP\n\n", "red")  # Insere o texto usando a tag "red"
        
        result_text.insert(tk.END, f"CEP {informacoes_cep['cep']}\n", "black")
        result_text.insert(tk.END, f"Rua: {informacoes_cep['address']}\n", "black")
        result_text.insert(tk.END, f"Bairro: {informacoes_cep['district']}\n", "black")
        result_text.insert(tk.END, f"Cidade: {informacoes_cep['city']}\n", "black")
        result_text.insert(tk.END, f"Estado: {informacoes_cep['state']}\n", "black")
        result_text.insert(tk.END, f"City IBGE: {informacoes_cep['city_ibge']}\n", "black")
        result_text.insert(tk.END, f"DDD: {informacoes_cep['ddd']}\n\n", "black")

        if 'lat' in informacoes_cep and 'lng' in informacoes_cep:
            result_text.insert(tk.END, f"Latitude: {informacoes_cep['lat']}\n", "green")
            result_text.insert(tk.END, f"Longitude: {informacoes_cep['lng']}", "green")
    else:
        result_text.insert(tk.END, "Não foi possível obter informações para o CEP fornecido.")

def abrir_no_google_maps():
    if informacoes_cep and 'lat' in informacoes_cep and 'lng' in informacoes_cep:
        latitude = informacoes_cep['lat']
        longitude = informacoes_cep['lng']
        url = f"https://www.google.com/maps/place/{latitude},{longitude}"
        webbrowser.open_new_tab(url)
    else:
        messagebox.showwarning("Aviso", "As informações do CEP não incluem coordenadas para o Google Maps.")

def consultar_cep():
    global informacoes_cep  # Usando a variável global

    cep = cep_entry.get()
    informacoes_cep = obter_informacoes_cep(cep)
    exibir_resultado(result_text)

# Configuração da interface gráfica
app = tk.Tk()
app.wm_state('zoomed')
app.title("Consulta de CEP")

# Entrada de texto para o CEP
cep_label = tk.Label(app, text="Digite o CEP da rua para consultar", font=("Arial", 11))
cep_label.pack(pady=10)
cep_entry = tk.Entry(app, font=("Arial", 11), width=30)  # Defina o valor de width conforme necessário
cep_entry.pack(pady=10)

# Botão para consultar o CEP
consultar_button = tk.Button(app, text="Consultar CEP", command=consultar_cep, font=("Arial", 11), bg="#05f7f3")
consultar_button.pack(pady=10)

# Botão para abrir no Google Maps
maps_button = tk.Button(app, text="Abrir no Google Maps", command=abrir_no_google_maps, font=("Arial", 11), bg="#0af759")
maps_button.pack(pady=10)

# Área de texto rolável para exibir o resultado
result_text = tk.Text(app, wrap=tk.WORD, width=80, height=30, font=("Arial", 15))
result_text.pack(pady=10)

# Inicia o loop principal da interface gráfica
app.mainloop()
