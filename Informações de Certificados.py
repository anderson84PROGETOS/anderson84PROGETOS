import requests
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
from io import BytesIO

def obter_informacoes():
    alvo = entrada_alvo.get().rstrip()
    saida.delete(1.0, tk.END)  # Limpar a área de texto de saída
    progress_var.set(0)  # Reiniciar o valor da barra de progresso

    if alvo:
        # Adiciona uma mensagem na área de saída
        saida.insert(tk.END, "Carregando, por favor, aguarde........\n\n")
        
        # Atualiza a interface gráfica
        janela.update_idletasks()

        # Simula um atraso para dar a sensação de carregamento
        janela.after(500)

        resultado = obter_dados(alvo)
        if resultado is not None:
            if resultado:  # Verificar se há dados para processar
                total = len(resultado)
                for i, valor in enumerate(resultado):
                    saida.insert(tk.END, valor.get('name_value', '') + '\n')

                    progress_percent = min(100, int((i + 1) / total * 100))
                    progress_var.set(progress_percent)
                    janela.update_idletasks()
            else:
                saida.insert(tk.END, "Nenhum certificado encontrado para o site alvo.")
        else:
            saida.insert(tk.END, "Erro ao obter informações. Verifique sua conexão com a internet e tente novamente.")
    else:
        saida.insert(tk.END, "Por favor, digite um nome de site alvo.")

def obter_dados(alvo):
    try:
        req = requests.get("https://crt.sh/?q=%.{d}&output=json".format(d=alvo))
        req.raise_for_status()  # Lança uma exceção se o status da resposta for um erro (4xx ou 5xx)

        # Verificar se o conteúdo é um JSON válido antes de decodificar
        content_type = req.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            dados = req.json()
            return dados
        else:
            # Agendando a inserção da mensagem de erro na área de saída
            janela.after(1, lambda: saida.insert(tk.END, f"O conteúdo retornado não é um JSON válido. Tipo de conteúdo recebido: {content_type}\n"))
    except requests.exceptions.RequestException as e:
        # Agendando a inserção da mensagem de erro na área de saída
        janela.after(1, lambda: saida.insert(tk.END, f"Erro na requisição: {e}\n"))
    except json.JSONDecodeError as e:
        # Agendando a inserção da mensagem de erro na área de saída
        janela.after(1, lambda: saida.insert(tk.END, f"Erro ao decodificar JSON: {e}\n"))
        
    return None

# Configuração da janela principal
janela = tk.Tk()
janela.wm_state('zoomed')
janela.title("Coletor de Informações de Certificados")

# URL do ícone
icon_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQczDn3CZlgW_ecfJOUQgMJtpYdkO_KMGWHW45yLESYX1wNZi42"  # Substitua pela URL do seu ícone

# Função para baixar o ícone da web
def download_icon(url):
    response = requests.get(url)
    icon_data = BytesIO(response.content)
    return Image.open(icon_data)

# Baixar o ícone da web
icon_image = download_icon(icon_url)

# Converter a imagem para o formato TKinter
tk_icon = ImageTk.PhotoImage(icon_image)

# Definir o ícone da janela
janela.iconphoto(True, tk_icon)

# Configuração do layout
label_alvo = tk.Label(janela, text="Digite o nome do site alvo", font=("Arial", 12))
label_alvo.pack(pady=5)
entrada_alvo = tk.Entry(janela, width=40, font=("Arial", 12))
entrada_alvo.pack(pady=1)

btn_coletar = tk.Button(janela, text="Coletar Informações", command=obter_informacoes, font=("Arial", 12), bg="#42f5ec")
btn_coletar.pack(pady=10)

progress_var = tk.DoubleVar()
style = ttk.Style()
style.configure('green.Horizontal.TProgressbar', background='#12f50a')
progress_bar = ttk.Progressbar(janela, orient=tk.HORIZONTAL, mode='determinate', variable=progress_var, style='green.Horizontal.TProgressbar', length=1080)
progress_bar.place(x=90, y=125 + 10)  # Adicionei 20 à posição y

saida = scrolledtext.ScrolledText(janela, width=120, height=45, font=("Arial", 12))
saida.pack(padx=10, pady=50)

def main():
    # Agendando a inserção da mensagem na área de saída
    janela.after(1, lambda: saida.insert(tk.END, "Carregando, por favor, aguarde...\n"))
    
    # Atualiza a interface gráfica
    janela.update_idletasks()    

# Iniciar o loop principal da interface gráfica
janela.mainloop()
