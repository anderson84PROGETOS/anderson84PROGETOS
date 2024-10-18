import os
import sqlite3
import win32crypt  # Para decriptografia no Windows
import shutil
import json
from tkinter import filedialog, Tk, Text, Scrollbar, RIGHT, Y, END, BOTH, Button, Label
from tkinter.scrolledtext import ScrolledText  # Área de texto com rolagem
from Cryptodome.Cipher import AES
import base64

# Caminho padrão para o arquivo Login Data
chrome_login_data_path = os.path.join(os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Default\Login Data')

def get_encryption_key(local_state_path):
    with open(local_state_path, "r") as file:
        local_state = file.read()
        local_state = json.loads(local_state)

    # Decodificar a chave de criptografia
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    decrypted_key = win32crypt.CryptUnprotectData(encrypted_key[5:], None, None, None, 0)[1]
    return decrypted_key

def decrypt_password(password, encryption_key):
    try:
        iv = password[3:15]
        password = password[15:]
        cipher = AES.new(encryption_key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(password)[:-16].decode()
        return decrypted_pass
    except Exception as e:
        return ""

def fetch_saved_passwords(login_data_path, text_widget):
    # Caminho do arquivo Local State
    local_state_path = os.path.join(os.environ['USERPROFILE'],
                                    r'AppData\Local\Google\Chrome\User Data\Local State')
    encryption_key = get_encryption_key(local_state_path)

    # Copiar o arquivo de Login para evitar problemas de bloqueio
    shutil.copyfile(login_data_path, "LoginData_copy.db")
    
    # Conectar ao banco de dados SQLite
    conn = sqlite3.connect("LoginData_copy.db")
    cursor = conn.cursor()

    # Selecionar as senhas salvas
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")

    # Exibir as senhas decriptografadas na interface gráfica
    for row in cursor.fetchall():
        url = row[0]
        username = row[1]
        encrypted_password = row[2]
        decrypted_password = decrypt_password(encrypted_password, encryption_key)
        if username or decrypted_password:
            text_widget.insert(END, f"URL: {url}\nUsername: {username}\nPassword: {decrypted_password}\n\n")
    
    cursor.close()
    conn.close()
    os.remove("LoginData_copy.db")

def open_file_dialog(text_widget, label_path):
    # Criar uma janela para selecionar o arquivo Login Data
    file_path = filedialog.askopenfilename(title="Selecione o arquivo Login Data",
                                           filetypes=[("All Files", "*.*")])
    if file_path:
        # Limpar o conteúdo da área de texto antes de exibir novos resultados
        text_widget.delete("1.0", END)
        # Exibir o caminho do arquivo selecionado no rótulo
        label_path.config(text=f"Caminho do arquivo: {file_path}")
        # Buscar e exibir as senhas
        fetch_saved_passwords(file_path, text_widget)

def save_to_file(text_widget):
    # Abrir diálogo de salvamento
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(text_widget.get("1.0", END))

def load_default_passwords(text_widget):
    """Carrega as senhas automaticamente do caminho padrão"""
    text_widget.delete("1.0", END)
    if os.path.exists(chrome_login_data_path):
        fetch_saved_passwords(chrome_login_data_path, text_widget)
    else:
        text_widget.insert(END, "Caminho padrão não encontrado.\n")

if __name__ == "__main__":

    # Criar a janela principal
    root = Tk()
    root.title("Decriptografar Senhas do Chrome")
    root.geometry("1100x960")    

    # Rótulo para mostrar o caminho do arquivo (padrão inicial)
    if os.path.exists(chrome_login_data_path):
        initial_path = chrome_login_data_path
    else:
        initial_path = "Caminho padrão não encontrado"

    label_caminho = Label(root, text=initial_path, font=("TkDefaultFont", 10, "bold"))
    label_caminho.pack(pady=5)

    # Botão para carregar automaticamente as senhas do caminho padrão
    btn_carregar_auto = Button(root, text="Carregar Automaticamente", command=lambda: load_default_passwords(saida_texto), font=("TkDefaultFont", 11, "bold"), bg='#07b5f5')
    btn_carregar_auto.pack(pady=5)

    # Botão para selecionar o arquivo Login Data
    btn_selecionar = Button(root, text="Selecionar Outro Arquivo Login Data", command=lambda: open_file_dialog(saida_texto, label_caminho), font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
    btn_selecionar.pack(pady=5)

    # Botão para salvar as senhas em um arquivo .txt
    btn_salvar = Button(root, text="Salvar em arquivo .txt", command=lambda: save_to_file(saida_texto), font=("TkDefaultFont", 11, "bold"), bg='#eb4034')
    btn_salvar.pack(pady=5)

    # Área de texto com rolagem para exibir os resultados
    saida_texto = ScrolledText(root, wrap="word", width=120, height=40, font=("TkDefaultFont", 11, "bold"))
    saida_texto.pack(pady=10)

    # Executar o loop da interface gráfica
    root.mainloop()
