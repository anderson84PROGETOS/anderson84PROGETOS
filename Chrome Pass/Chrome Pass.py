import json
import os
import base64
import sqlite3
from shutil import copy
from Cryptodome.Cipher import AES  # PyCryptodome
import win32crypt
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

def obter_chave_criptografia():
    """Recupera a chave AES usada para criptografar as senhas do Chrome"""
    caminho_local_state = os.path.join(
        os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Local State'
    )
    with open(caminho_local_state, 'r', encoding='utf-8') as file:
        local_state = json.load(file)
    
    chave_criptografada = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
    chave_descriptografada = win32crypt.CryptUnprotectData(chave_criptografada, None, None, None, 0)[1]
    return chave_descriptografada

def descriptografar_senha(senha_criptografada, chave):
    """Descriptografa uma senha criptografada com AES GCM (Chrome v80+) ou DPAPI (versões antigas)"""
    try:
        if not senha_criptografada:
            return None
        
        # Converter memoryview para bytes, se necessário
        if isinstance(senha_criptografada, memoryview):
            senha_criptografada = senha_criptografada.tobytes()
        
        if senha_criptografada[:3] == b'v10':
            nonce = senha_criptografada[3:15]
            ciphertext = senha_criptografada[15:-16]
            tag = senha_criptografada[-16:]
            cipher = AES.new(chave, AES.MODE_GCM, nonce)
            senha_descriptografada = cipher.decrypt_and_verify(ciphertext, tag)
            return senha_descriptografada.decode('utf-8')
        else:
            senha_descriptografada = win32crypt.CryptUnprotectData(senha_criptografada, None, None, None, 0)[1]
            if senha_descriptografada:
                return senha_descriptografada.decode('utf-8')
            else:
                return None
    except Exception as e:
        return f"Erro ao descriptografar a senha: {e}"

class Chrome:
    def __init__(self):
        self.caminho_bd = os.path.join(
            os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Default\Login Data'
        )
        self.chave = obter_chave_criptografia()

    def obter_senhas(self):
        try:
            copy(self.caminho_bd, "Login Data.db")
            conn = sqlite3.connect("Login Data.db")
            cursor = conn.cursor()
            cursor.execute("SELECT action_url, username_value, password_value FROM logins")
            
            senhas = []
            for url, usuario, senha_criptografada in cursor.fetchall():
                senha = descriptografar_senha(senha_criptografada, self.chave)
                if senha and not senha.startswith("Erro ao descriptografar"):
                    senhas.append({
                        'url': url,
                        'nome_usuario': usuario,
                        'senha': senha
                    })
            conn.close()
            os.remove("Login Data.db")
            return senhas
        except Exception as e:
            return [{"url": "Erro", "nome_usuario": "", "senha": f"Erro ao acessar o banco de dados: {e}"}]

class ChromePasswordGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chrome Pass")
        self.root.geometry("1200x900")
        self.root.state("zoomed")  # Abrir maximizado

        # Botão para salvar
        self.btn_save = tk.Button(root, text="Salvar como .txt", bg="#03fc0b", fg="black", command=self.salvar_senhas)
        self.btn_save.pack(pady=5)
        
        # Campo de texto com rolagem
        self.txt_output = scrolledtext.ScrolledText(root, width=150, height=54)
        self.txt_output.pack(pady=5)
        
        # Configurar tags para cores
        self.txt_output.tag_configure("url", foreground="red")
        self.txt_output.tag_configure("usuario", foreground="green")
        self.txt_output.tag_configure("senha", foreground="purple")     
           
        # Inicializar e exibir senhas
        self.exibir_senhas()

    def exibir_senhas(self):
        chrome = Chrome()
        senhas = chrome.obter_senhas()
        self.txt_output.delete(1.0, tk.END)  # Limpar o campo de texto
        for e in senhas:
            self.txt_output.insert(tk.END, f"URL: {e['url']}\n", "url")
            self.txt_output.insert(tk.END, f"Usuário: {e['nome_usuario']}\n", "usuario")
            self.txt_output.insert(tk.END, f"Senha: {e['senha']}\n", "senha")
            self.txt_output.insert(tk.END, "="*100 + "\n")

    def salvar_senhas(self):
        chrome = Chrome()
        senhas = chrome.obter_senhas()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Salvar senhas como"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for e in senhas:
                        f.write(f"URL: {e['url']}\n")
                        f.write(f"Usuário: {e['nome_usuario']}\n")
                        f.write(f"Senha: {e['senha']}\n")
                        f.write("="*100 + "\n")
                messagebox.showinfo("Sucesso", f"Senhas salvas em: {file_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar o arquivo: {e}")

def main():
    root = tk.Tk()
    app = ChromePasswordGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
