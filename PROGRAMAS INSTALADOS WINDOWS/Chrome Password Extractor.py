import json
import os
import base64
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from Cryptodome.Cipher import AES
import win32crypt
from shutil import copy

# ====================== FUNÇÕES DE CRIPTOGRAFIA ======================
def obter_chave_criptografia():
    try:
        caminho = os.path.join(os.environ['USERPROFILE'], 
                              r'AppData\Local\Google\Chrome\User Data\Local State')
        with open(caminho, 'r', encoding='utf-8') as f:
            local_state = json.loads(f.read())
        chave_criptografada = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
        return win32crypt.CryptUnprotectData(chave_criptografada, None, None, None, 0)[1]
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível obter a chave:\n{e}")
        return None

def descriptografar_senha(senha_criptografada, chave):
    try:
        iv = senha_criptografada[3:15]
        ciphertext = senha_criptografada[15:-16]
        cipher = AES.new(chave, AES.MODE_GCM, iv)
        return cipher.decrypt(ciphertext).decode('utf-8')
    except:
        return None

# ====================== CLASSE PRINCIPAL ======================
class ChromePasswordExtractor:
    def __init__(self):
        self.chave = obter_chave_criptografia()
        self.senhas = []

    def obter_senhas(self):
        if not self.chave:
            return []
        
        caminho_bd = os.path.join(os.environ['USERPROFILE'], 
                                 r'AppData\Local\Google\Chrome\User Data\Default\Login Data')
        
        if not os.path.exists(caminho_bd):
            messagebox.showerror("Erro", "Banco de dados do Chrome não encontrado!")
            return []

        temp_db = "Login_Data_Temp.db"
        try:
            copy(caminho_bd, temp_db)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT action_url, username_value, password_value FROM logins")
            
            self.senhas = []
            for url, user, pwd in cursor.fetchall():
                if pwd:
                    senha = descriptografar_senha(pwd, self.chave)
                    if senha:
                        self.senhas.append({
                            'url': url,
                            'usuario': user or "Sem usuário",
                            'senha': senha
                        })
            conn.close()
            os.remove(temp_db)
            return self.senhas
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na extração:\n{e}")
            return []

# ====================== INTERFACE GRÁFICA ======================
class HackerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chrome Password Extractor")
        self.root.geometry("1100x750")
        self.root.state("zoomed")
        self.root.configure(bg="#000000")
        self.root.minsize(900, 600)
        
        self.extractor = ChromePasswordExtractor()
        self.create_widgets()
        
    def create_widgets(self):
        # Título
        tk.Label(self.root, text="CHROME PASSWORD EXTRACTOR", 
                font=("Consolas", 26, "bold"), fg="#00ff41", bg="#000000").pack(pady=15)
        
        tk.Label(self.root, text="ESTILO MATRIX • EXTRAÇÃO SEGURA", 
                font=("Consolas", 12), fg="#00cc00", bg="#000000").pack(pady=(0, 8))

        # ====================== BOTÕES NO TOPO ======================
        btn_frame = tk.Frame(self.root, bg="#000000")
        btn_frame.pack(pady=8)

        tk.Button(btn_frame, text="🔍 EXTRAIR SENHAS", width=28, height=2,
                 bg="#003300", fg="#00ff41", font=("Consolas", 12, "bold"),
                 command=self.start_extraction).grid(row=0, column=0, padx=15)

        tk.Button(btn_frame, text="💾 SALVAR COMO .TXT", width=28, height=2,
                 bg="#003300", fg="#00ff41", font=("Consolas", 12, "bold"),
                 command=self.save_file).grid(row=0, column=1, padx=15)

        # ====================== AVISO LOGO ABAIXO DOS BOTÕES ======================
        tk.Label(self.root, text="Use com responsabilidade • Apenas no seu próprio computador", 
                font=("Consolas", 9), fg="#03990F", bg="#000000").pack(pady=(0, 15))

        # ====================== ÁREA DE TEXTO (GRANDE) ======================        
        frame_texto = tk.Frame(self.root, bg="#000000")        

        frame_texto.place(
        x=150,      # mais para a direita
        y=215,     # mais para baixo
        width=1000, # largura
        height=690  # altura
    )

        self.text_area = tk.Text(frame_texto, bg="#001a00", fg="#00ff41", 
                                font=("Consolas", 11), insertbackground="#00ff41", 
                                relief="flat", padx=12, pady=12)
        scrollbar = ttk.Scrollbar(frame_texto, orient="vertical", command=self.text_area.yview)
        
        self.text_area.configure(yscrollcommand=scrollbar.set)

        self.text_area.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def start_extraction(self):
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, "Extraindo senhas do Chrome...\n\n")
        self.root.update()

        def thread_extract():
            senhas = self.extractor.obter_senhas()
            self.root.after(0, self.display_results, senhas)

        threading.Thread(target=thread_extract, daemon=True).start()

    def display_results(self, senhas):
        self.text_area.delete(1.0, tk.END)
        if not senhas:
            self.text_area.insert(tk.END, "Nenhuma senha encontrada.\n")
            return

        self.text_area.insert(tk.END, f"✅ {len(senhas)} senhas recuperadas com sucesso!\n\n")
        self.text_area.insert(tk.END, "="*90 + "\n\n")

        for i, s in enumerate(senhas, 1):
            self.text_area.insert(tk.END, f"{i:02d}. URL: {s['url']}\n")
            self.text_area.insert(tk.END, f"    Usuário: {s['usuario']}\n")
            self.text_area.insert(tk.END, f"    Senha:   {s['senha']}\n")
            self.text_area.insert(tk.END, "-"*80 + "\n\n")

    def save_file(self):
        if not self.extractor.senhas:
            messagebox.showwarning("Aviso", "Extraia as senhas primeiro!")
            return

        caminho = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt")],
            initialfile="minhas_senhas_chrome.txt"
        )
        if caminho:
            try:
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write("CHROME PASSWORD EXTRACTOR - GHOST MODE\n")
                    f.write("="*70 + "\n\n")
                    for s in self.extractor.senhas:
                        f.write(f"URL: {s['url']}\n")
                        f.write(f"Usuário: {s['usuario']}\n")
                        f.write(f"Senha: {s['senha']}\n")
                        f.write("="*60 + "\n\n")
                messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso!\n\n{caminho}")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = HackerGUI()
    app.run()
