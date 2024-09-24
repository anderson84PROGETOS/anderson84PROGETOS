import tkinter as tk
from tkinter import filedialog, messagebox
import pyshark
import re
import os

# Função para carregar o último diretório selecionado a partir de um arquivo de configuração
def load_last_directory():
    config_file = 'config.txt'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return f.read().strip()  # Ler o último diretório do arquivo
    return os.path.expanduser('~')  # Retornar o diretório home padrão

# Função para salvar o último diretório selecionado em um arquivo de configuração
def save_last_directory(directory):
    config_file = 'config.txt'
    with open(config_file, 'w') as f:
        f.write(directory)  # Salvar o último diretório no arquivo

# Variável global para armazenar o último diretório selecionado
last_directory = load_last_directory()  # Carregar o último diretório

# Função para localizar o executável tshark no sistema
def find_tshark():
    # Tentando encontrar o tshark pelo caminho padrão no PATH
    if os.name == 'posix':
        tshark_path = os.popen('which tshark').read().strip()
        if tshark_path:
            return tshark_path

    # Para Windows, tentamos encontrar em diretórios comuns e no PATH
    for path in os.environ['PATH'].split(os.pathsep):
        tshark_path = os.path.join(path, 'tshark.exe')
        if os.path.exists(tshark_path):
            return tshark_path

    # Definindo diretórios comuns onde o tshark pode estar
    possible_dirs = [
        os.path.join(os.getenv('PROGRAMFILES', ''), 'Wireshark'),
        os.path.join(os.getenv('PROGRAMFILES(X86)', ''), 'Wireshark'),
        os.getenv('SYSTEMDRIVE', '') + '\\Wireshark',
        os.getenv('APPDATA', ''),
    ]

    # Verificar os diretórios comuns no Windows
    for directory in possible_dirs:
        tshark_path = os.path.join(directory, 'tshark.exe')
        if os.path.exists(tshark_path):
            return tshark_path

    return None

# Função para processar o arquivo .pcapng
def process_pcap_file(file_path, tshark_path):
    try:
        # Abrindo o arquivo .pcapng com PyShark, utilizando o tshark encontrado
        capture = pyshark.FileCapture(file_path, display_filter='http', tshark_path=tshark_path)
        form_items = []
        
        # Iterando sobre os pacotes capturados
        for packet in capture:
            try:
                # Convertendo o conteúdo do pacote para string
                packet_str = str(packet)
                
                # Procurando por "Form item" nos pacotes HTTP
                form_item_matches = re.findall(r'Form item.*', packet_str, re.IGNORECASE)

                # Adicionando resultados ao array
                if form_item_matches:
                    form_items.extend(form_item_matches)
            except Exception:
                continue
        
        capture.close()
        
        # Exibindo os resultados na interface gráfica
        if form_items:
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "\n".join(form_items))
        else:
            messagebox.showinfo("Resultado", "Nenhum 'Form item' encontrado.")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao processar o arquivo: {e}")

# Função para abrir o diálogo de arquivo
def open_file():
    global last_directory  # Usar a variável global
    # Permitir ao usuário escolher qualquer arquivo .pcapng no PC
    file_path = filedialog.askopenfilename(initialdir=last_directory,  # Usar o último diretório selecionado
                                           filetypes=[("PCAPNG files", "*.pcapng")])
    if file_path:
        file_label.config(text=f"Arquivo selecionado: {file_path}")
        last_directory = os.path.dirname(file_path)  # Atualizar o último diretório
        save_last_directory(last_directory)  # Salvar o último diretório em um arquivo
        tshark_path = find_tshark()
        if tshark_path:
            process_pcap_file(file_path, tshark_path)
        else:
            messagebox.showerror("Erro", "O Wireshark (tshark) não foi encontrado no sistema.")

# Função para salvar as informações
def save_information():
    # Salvar o conteúdo atual do result_text em um arquivo
    save_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                               filetypes=[("Text files", "*.txt")])
    if save_path:
        try:
            with open(save_path, 'w') as f:
                f.write(result_text.get(1.0, tk.END))  # Escrever o conteúdo da caixa de texto
            messagebox.showinfo("Sucesso", "Informações salvas com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o arquivo: {e}")

# Criando a interface gráfica
root = tk.Tk()
root.geometry("1000x900")
root.title("Leitor de PCAPNG - Form Items")

# Botão para selecionar o arquivo
file_button = tk.Button(root, text="Abrir Arquivo PCAPNG", command=open_file, bg="#13f007", font=("TkDefaultFont", 11, "bold"))
file_button.pack(pady=10)

# Rótulo para exibir o caminho do arquivo
file_label = tk.Label(root, text="Nenhum arquivo selecionado.", font=("TkDefaultFont", 11, "bold"))
file_label.pack(pady=5)

# Botão para salvar as informações
save_button = tk.Button(root, text="Salvar Informações", command=save_information, bg="#07f5e5", font=("TkDefaultFont", 11, "bold"))
save_button.pack(pady=10)

# Caixa de texto para exibir os resultados
result_text = tk.Text(root, width=120, height=40, font=("TkDefaultFont", 11, "bold"))
result_text.pack(pady=10)

# Iniciando a interface gráfica
root.mainloop()
