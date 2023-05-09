from tkinter import *
from selenium import webdriver
import subprocess
import tkinter as tk
import requests
import pyperclip

# Função que é chamada quando o botão é pressionado
def buscar():
    site = entrada.get()  # Obtém o valor digitado na caixa de texto
    subprocess.Popen(["C:\Program Files\Google\Chrome\Application\chrome.exe", site])  # Inicializa o driver do Google Chrome
    resultado['text'] = f"Site buscado: {site}\n\n↓↓ Cabeçalhos Headers ↓↓\n\n{get_headers(site)}"
    
# Função para obter os cabeçalhos HTTP
def get_headers(url):
    try:
        response = requests.head(url)
        headers = response.headers
        headers_str = ""
        for key, value in headers.items():
            headers_str += f"{key}: {value}\n"
        return headers_str
    except requests.exceptions.RequestException as e:
        return f"Erro ao obter cabeçalhos: {e}"

# Função que é chamada quando o botão de limpar é pressionado
def limpar():
    entrada.delete(0, END)
    resultado['text'] = ''

# Função que é chamada quando o botão de copiar é pressionado
def copiar():
    texto = resultado['text']
    pyperclip.copy(texto)

# Cria a interface gráfica
janela = Tk()
url_label = tk.Label(text="Digite a url do site para buscar (ex: https://www.google.com)", font=("Arial", 10, "bold"))
url_label.pack()
janela.title('Busca no Google')
janela.geometry('400x250')
janela.wm_state('zoomed')

# Cria a caixa de texto e os botões
entrada = Entry(janela, width=80)
entrada.pack(pady=5)
botao_buscar = Button(janela, text='Buscar', command=buscar, bg='blue', fg='white', font=('Arial', '12', 'bold'))
botao_buscar.pack(side=TOP, pady=20)

botao_limpar = Button(janela, text='Limpar', command=limpar, bg='red', fg='white')
botao_limpar.pack(side=TOP)

# pular linha
espaco_vazio = Label(janela, height=1)
espaco_vazio.pack()

botao_copiar = Button(janela, text='Copiar', command=copiar, bg='green', fg='white')
botao_copiar.pack(side=TOP)

# pular linha
espaco_vazio = Label(janela, height=1)
espaco_vazio.pack()

# Cria o espaço para exibir o resultado
resultado = Label(janela, text='', font=("Arial", 12))
resultado.pack(pady=10)

janela.mainloop()
