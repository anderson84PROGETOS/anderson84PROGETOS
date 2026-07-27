import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import threading
import os
import time
import platform

class AESToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AES Tool - Encrypt & Password Recovery")
        self.root.configure(bg="#1e1e2e")

        if platform.system() == "Windows":
            self.root.state("zoomed")
        else:
            self.root.attributes("-zoomed", True)

        self.stop_flag = False
        self.setup_style()
        self.create_widgets()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Header.TLabel", font=("Segoe UI", 15, "bold"), foreground="#89b4fa")
        style.configure("Status.TLabel", font=("Segoe UI", 9), foreground="#a6e3a1")
        style.configure("green.Horizontal.TProgressbar", troughcolor="#313244", background="#a6e3a1")

    def create_widgets(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="🔐 AES Tool - Encrypt & Password Recovery", style="Header.TLabel").pack(pady=(0, 10))

        # ==================== ABA CRIAR ====================
        create_frame = ttk.LabelFrame(main, text=" 1. Criar arquivo output.bin ", padding=10)
        create_frame.pack(fill=tk.X, pady=5)

        ttk.Label(create_frame, text="Senha que o cracker deve descobrir:").pack(anchor=tk.W)
        self.senha_criar = tk.StringVar()
        ttk.Entry(create_frame, textvariable=self.senha_criar, show="*").pack(fill=tk.X, pady=2)

        ttk.Label(create_frame, text="Texto que será criptografado:").pack(anchor=tk.W, pady=(6, 0))
        self.texto_criar = tk.StringVar(value="Este é um texto secreto de teste")
        ttk.Entry(create_frame, textvariable=self.texto_criar).pack(fill=tk.X, pady=2)

        ttk.Label(create_frame, text="Nome do arquivo de saída:").pack(anchor=tk.W, pady=(6, 0))
        self.nome_bin = tk.StringVar(value="output.bin")
        ttk.Entry(create_frame, textvariable=self.nome_bin).pack(fill=tk.X, pady=2)

        ttk.Button(create_frame, text="▶ Gerar output.bin", command=self.gerar_bin).pack(pady=8)

        # ==================== ABA QUEBRAR ====================
        crack_frame = ttk.LabelFrame(main, text=" 2. Quebrar arquivo .bin ", padding=10)
        crack_frame.pack(fill=tk.X, pady=5)

        # Arquivo binário
        bin_row = ttk.Frame(crack_frame)
        bin_row.pack(fill=tk.X, pady=2)
        ttk.Label(bin_row, text="Arquivo .bin:").pack(side=tk.LEFT)
        self.bin_path = tk.StringVar()
        ttk.Entry(bin_row, textvariable=self.bin_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(bin_row, text="Procurar...", command=self.browse_bin).pack(side=tk.LEFT)

        # Wordlist
        wl_row = ttk.Frame(crack_frame)
        wl_row.pack(fill=tk.X, pady=4)
        ttk.Label(wl_row, text="Wordlist:").pack(side=tk.LEFT)
        self.wl_path = tk.StringVar()
        ttk.Entry(wl_row, textvariable=self.wl_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(wl_row, text="Procurar...", command=self.browse_wordlist).pack(side=tk.LEFT)

        # Botões de ataque
        btn_row = ttk.Frame(crack_frame)
        btn_row.pack(fill=tk.X, pady=8)

        self.start_btn = ttk.Button(btn_row, text="▶ Iniciar Ataque", command=self.start_attack)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_btn = ttk.Button(btn_row, text="⏹ Parar", command=self.stop_attack, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        # Progresso
        self.progress = ttk.Progressbar(main, orient="horizontal", mode="determinate",
                                        style="green.Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, pady=(8, 2))

        self.progress_label = tk.StringVar(value="0%")
        ttk.Label(main, textvariable=self.progress_label, style="Status.TLabel").pack(anchor=tk.W)

        self.status = tk.StringVar(value="Pronto. Crie um .bin ou selecione um existente + wordlist.")
        ttk.Label(main, textvariable=self.status, style="Status.TLabel").pack(anchor=tk.W, pady=(4, 6))

        # Log
        log_frame = ttk.LabelFrame(main, text=" Log / Resultado ", padding=6)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log = scrolledtext.ScrolledText(
            log_frame, height=12, wrap=tk.WORD,
            bg="#11111b", fg="#a6e3a1", insertbackground="white",
            font=("Consolas", 10)
        )
        self.log.pack(fill=tk.BOTH, expand=True)

        # Configura a cor de abóbora (só uma vez)
        self.log.tag_configure("pumpkin", foreground="#FF7518")

    # ==================== FUNÇÕES DE CRIAR ====================
    def gerar_bin(self):
        senha = self.senha_criar.get().strip()
        texto = self.texto_criar.get().strip()
        nome = self.nome_bin.get().strip() or "output.bin"

        if not senha or not texto:
            messagebox.showerror("Erro", "Senha e texto não podem ficar vazios.")
            return

        try:
            iv = get_random_bytes(16)
            key = SHA256.new(senha.encode()).digest()
            cipher = AES.new(key, AES.MODE_CBC, iv)
            ciphertext = cipher.encrypt(pad(texto.encode("utf-8"), AES.block_size))

            with open(nome, "wb") as f:
                f.write(iv + ciphertext)

            self.log_msg("", clear=True)
            self.log_msg("[+] Arquivo gerado com sucesso!")
            self.log_msg(f"[+] Nome      : {nome}")
            self.log_msg(f"[+] Senha     : {senha}")
            self.log_msg(f"[+] Texto     : {texto}")
            self.log_msg(f"[+] IV (hex)  : {iv.hex()}")
            self.log_msg(f"[+] Tamanho   : {16 + len(ciphertext)} bytes")
            self.log_msg("\nAgora selecione esse arquivo embaixo e a wordlist para quebrar.")

            self.bin_path.set(os.path.abspath(nome))
            self.status.set(f"Arquivo {nome} criado com sucesso!")
            messagebox.showinfo("Sucesso", f"Arquivo {nome} criado!\nSenha: {senha}")

        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # ==================== FUNÇÕES DE QUEBRAR ====================
    def browse_bin(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo binário",
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
        )
        if path:
            self.bin_path.set(path)

    def browse_wordlist(self):
        path = filedialog.askopenfilename(
            title="Selecione a wordlist",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            self.wl_path.set(path)

    def log_msg(self, msg, clear=False, tag=None):
        if clear:
            self.log.delete("1.0", tk.END)
        if tag:
            self.log.insert(tk.END, msg + "\n", tag)
        else:
            self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.root.update_idletasks()

    def try_decrypt(self, ciphertext, iv, password):
        try:
            key = SHA256.new(password.encode()).digest()
            cipher = AES.new(key, AES.MODE_CBC, iv)
            plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
            return plaintext.decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

    def stop_attack(self):
        self.stop_flag = True
        self.status.set("Parando... aguarde a senha atual terminar.")

    def start_attack(self):
        self.stop_flag = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress["value"] = 0
        self.progress_label.set("0%")
        self.log_msg("", clear=True)
        threading.Thread(target=self.run_attack, daemon=True).start()

    def run_attack(self):
        try:
            bin_path = self.bin_path.get().strip()
            wl_path = self.wl_path.get().strip()

            if not bin_path or not os.path.exists(bin_path):
                messagebox.showerror("Erro", "Arquivo binário inválido.")
                return
            if not wl_path or not os.path.exists(wl_path):
                messagebox.showerror("Erro", "Wordlist inválida.")
                return

            with open(bin_path, "rb") as f:
                data = f.read()

            if len(data) < 17:
                messagebox.showerror("Erro", "Arquivo muito curto (precisa de pelo menos 17 bytes).")
                return

            iv = data[:16]
            ciphertext = data[16:]

            self.log_msg(f"[*] Arquivo: {os.path.basename(bin_path)}")
            self.log_msg(f"[*] Tamanho: {len(data)} bytes")
            self.log_msg(f"[*] IV: {iv.hex()}")
            self.log_msg(f"[*] Ciphertext: {len(ciphertext)} bytes")
            self.log_msg("")

            self.status.set("Contando senhas da wordlist...")
            total = 0
            with open(wl_path, "r", encoding="utf-8", errors="ignore") as f:
                for _ in f:
                    total += 1

            self.log_msg(f"[*] Wordlist: {total:,} senhas\n")
            self.log_msg("[*] Iniciando ataque completo...\n")
            self.progress["maximum"] = total

            found = False
            start_time = time.time()
            last_log = 0

            with open(wl_path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, 1):
                    if self.stop_flag:
                        self.log_msg(f"\n[!] Interrompido na senha {idx:,}")
                        self.status.set("Interrompido pelo usuário.")
                        break

                    pwd = line.strip()
                    if not pwd:
                        continue

                    result = self.try_decrypt(ciphertext, iv, pwd)

                    if idx % 500 == 0 or idx == 1:
                        elapsed = time.time() - start_time
                        speed = idx / elapsed if elapsed > 0 else 0
                        percent = (idx / total) * 100
                        self.progress["value"] = idx
                        self.progress_label.set(f"{percent:.1f}% | {idx:,}/{total:,} | {speed:.0f} Senhas")
                        self.status.set(f"Testando: {pwd}")

                    if idx - last_log >= 2000 or idx == 1:
                        self.log_msg(f"[-] {idx:,} → {pwd}")
                        last_log = idx

                    if result is not None:
                        elapsed = time.time() - start_time
                        self.log_msg("\n" + "=" * 55)
                        self.log_msg(f"[+] SENHA ENCONTRADA: {pwd}\n\n", tag="pumpkin")
                        self.log_msg(f"[+] Posição na wordlist: {idx:,}\n")
                        self.log_msg(f"[+] Tempo total: {elapsed:.1f} segundos\n\n")
                        self.log_msg(f"[+] Texto Descriptografado: {result}\n\n")
                        self.log_msg("=" * 55)
                        self.status.set(f"SUCESSO Senha: {pwd}")
                        self.progress["value"] = total
                        self.progress_label.set("100% - SENHA ENCONTRADA")
                        found = True
                        break

            if not found and not self.stop_flag:
                elapsed = time.time() - start_time
                self.log_msg(f"\n[-] Terminou toda a wordlist ({total:,} senhas).")
                self.log_msg(f"[-] Tempo total: {elapsed:.1f} segundos")
                self.log_msg("[-] Nenhuma senha funcionou.")
                self.status.set("Nenhuma senha encontrada.")
                self.progress["value"] = total
                self.progress_label.set("100% - Finalizado")

        except Exception as e:
            self.log_msg(f"\n[ERRO] {str(e)}")
            self.status.set("Erro ocorrido.")
            messagebox.showerror("Erro", str(e))
        finally:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = AESToolGUI(root)
    root.mainloop()
