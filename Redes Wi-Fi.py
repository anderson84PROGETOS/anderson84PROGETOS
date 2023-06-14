import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from tkinter import filedialog
import subprocess
from tkinter import messagebox

def obter_detalhes_rede_wifi(nome_rede):
    try:
        resultado = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles', 'name=', nome_rede, 'key=clear'])
        resultado_decodificado = resultado.decode('latin-1', errors='ignore')
        return resultado_decodificado
    except subprocess.CalledProcessError:
        return "Erro ao obter os detalhes da rede Wi-Fi"

def exibir_detalhes_rede_wifi():
    nome_rede = entrada_rede.get()
    detalhes_rede_wifi = obter_detalhes_rede_wifi(nome_rede)
    texto_resultado.delete('1.0', tk.END)
    texto_resultado.tag_configure('negrito', font=('Arial', 10, 'bold'))
    texto_resultado.insert(tk.END, f"Nome da rede Wi-Fi {nome_rede}\n\n", 'negrito')
    texto_resultado.insert(tk.END, detalhes_rede_wifi)

def exibir_usuarios_conectados():
    resultado = subprocess.check_output(['netsh', 'wlan', 'show', 'network', 'mode=bssid'])
    resultado_decodificado = resultado.decode('latin-1', errors='ignore')
    texto_resultado.delete('1.0', tk.END)
    texto_resultado.tag_configure('negrito', font=('Arial', 10, 'bold'))
    texto_resultado.insert(tk.END, "Usuários conectados à rede Wi-Fi\n\n", 'negrito')
    texto_resultado.insert(tk.END, resultado_decodificado)

def limpar_texto():
    texto_resultado.delete('1.0', tk.END)

def salvar_dados():
    dados = texto_resultado.get('1.0', tk.END)
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo de Texto", "*.txt")])
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as arquivo:
            arquivo.write(dados)
        messagebox.showinfo("Sucesso", "Dados salvos com sucesso!")

janela = tk.Tk()
janela.wm_state('zoomed')
janela.title("Redes Wi-Fi")
janela.geometry("400x300")

rotulo_rede = tk.Label(janela, text="Nome da rede Wi-Fi")
rotulo_rede.pack()

entrada_rede = tk.Entry(janela, width=50)
entrada_rede.pack()

botao_detalhes = tk.Button(janela, text="Exibir Detalhes", command=exibir_detalhes_rede_wifi, bg="#00FF00")
botao_detalhes.pack(pady=10)

botao_usuarios = tk.Button(janela, text="Exibir Usuários Conectados", command=exibir_usuarios_conectados, bg="#6495ED")
botao_usuarios.pack(pady=10)

botao_limpar = tk.Button(janela, text="Limpar tudo", command=limpar_texto, bg="#D2691E")
botao_limpar.pack(pady=10)

texto_resultado_frame = tk.Frame(janela)
texto_resultado_frame.pack()

texto_resultado = tk.Text(texto_resultado_frame, height=40, width=150)
texto_resultado.pack(side=tk.LEFT)

scrollbar = ttk.Scrollbar(texto_resultado_frame, command=texto_resultado.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
texto_resultado.config(yscrollcommand=scrollbar.set)

botao_salvar = tk.Button(janela, text="Salvar Dados", command=salvar_dados, bg="#FFD700")
botao_salvar.pack(pady=10)

janela.mainloop()
