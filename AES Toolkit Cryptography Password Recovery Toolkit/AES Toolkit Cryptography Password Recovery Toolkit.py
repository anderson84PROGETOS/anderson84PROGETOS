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
        self.root.title("AES Toolkit – Cryptography & Password Recovery Toolkit")
        self.root.configure(bg="#1e1e2e")

        if platform.system() == "Windows":
            self.root.state("zoomed")
        else:
            self.root.attributes("-zoomed", True)

        self.stop_flag = False
        self.ultimo_resultado = None  # <- armazena o texto descriptografado
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

        ttk.Label(main, text="🔐 AES Toolkit – Cryptography & Password Recovery Toolkit", style="Header.TLabel").pack(pady=(0, 10))

        # ==================== ABA CRIAR ====================
        create_frame = ttk.LabelFrame(main, text=" 1. Criar arquivo output.bin ", padding=10)
        create_frame.pack(fill=tk.X, pady=5)

        ttk.Label(create_frame, text="Senha que o cracker deve descobrir:").pack(anchor=tk.W)
        self.senha_criar = tk.StringVar()
        ttk.Entry(create_frame, textvariable=self.senha_criar, show="*").pack(fill=tk.X, pady=2)

        ttk.Label(create_frame, text="Digite o texto aqui (ou use o carregador abaixo):").pack(anchor=tk.W, pady=(6, 0))
        self.texto_frame = ttk.Frame(create_frame)
        self.texto_frame.pack(fill=tk.BOTH, pady=2, expand=False)
        self.texto_widget = scrolledtext.ScrolledText(
            self.texto_frame, height=5, wrap=tk.WORD,
            bg="#1e1e2e", fg="#cdd6f4", insertbackground="white",
            font=("Consolas", 10)
        )
        self.texto_widget.pack(fill=tk.BOTH, expand=True)
        self.texto_widget.insert("1.0", "Este é um texto secreto de teste")

        ttk.Separator(create_frame, orient="horizontal").pack(fill=tk.X, pady=6)

        ttk.Label(create_frame, text="Carregar arquivo .txt ou .csv (com barra de progresso):").pack(anchor=tk.W)

        load_row = ttk.Frame(create_frame)
        load_row.pack(fill=tk.X, pady=2)

        self.load_file_label = tk.StringVar(value="Nenhum arquivo selecionado")
        ttk.Label(load_row, textvariable=self.load_file_label).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(load_row, text="Procurar...", command=self.browse_texto).pack(side=tk.LEFT)

        self.load_progress = ttk.Progressbar(create_frame, orient="horizontal", mode="determinate",
                                             style="green.Horizontal.TProgressbar")
        self.load_progress.pack(fill=tk.X, pady=(2, 0))

        self.load_progress_label = tk.StringVar(value="")
        ttk.Label(create_frame, textvariable=self.load_progress_label, style="Status.TLabel").pack(anchor=tk.W, pady=(0, 4))

        ttk.Label(create_frame, text="Nome do arquivo .bin de saída:").pack(anchor=tk.W, pady=(6, 0))
        self.nome_bin = tk.StringVar(value="output.bin")
        ttk.Entry(create_frame, textvariable=self.nome_bin).pack(fill=tk.X, pady=2)

        ttk.Button(create_frame, text="▶ Gerar output.bin", command=self.gerar_bin).pack(pady=8)

        # ==================== ABA QUEBRAR ====================
        crack_frame = ttk.LabelFrame(main, text=" 2. Quebrar arquivo .bin ", padding=10)
        crack_frame.pack(fill=tk.X, pady=5)

        bin_row = ttk.Frame(crack_frame)
        bin_row.pack(fill=tk.X, pady=2)
        ttk.Label(bin_row, text="Arquivo .bin:").pack(side=tk.LEFT)
        self.bin_path = tk.StringVar()
        ttk.Entry(bin_row, textvariable=self.bin_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(bin_row, text="Procurar...", command=self.browse_bin).pack(side=tk.LEFT)

        wl_row = ttk.Frame(crack_frame)
        wl_row.pack(fill=tk.X, pady=4)
        ttk.Label(wl_row, text="Wordlist:").pack(side=tk.LEFT)
        self.wl_path = tk.StringVar()
        ttk.Entry(wl_row, textvariable=self.wl_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(wl_row, text="Procurar...", command=self.browse_wordlist).pack(side=tk.LEFT)

        btn_row = ttk.Frame(crack_frame)
        btn_row.pack(fill=tk.X, pady=8)

        self.start_btn = ttk.Button(btn_row, text="▶ Iniciar Ataque", command=self.start_attack)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_btn = ttk.Button(btn_row, text="⏹ Parar", command=self.stop_attack, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))

        # --- BOTÃO SALVAR RESULTADO ---
        self.save_btn = ttk.Button(btn_row, text="💾 Salvar resultado...", command=self.salvar_resultado, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT)

        # Progresso do ataque
        self.progress = ttk.Progressbar(main, orient="horizontal", mode="determinate",
                                        style="green.Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, pady=(8, 2))

        self.progress_label = tk.StringVar(value="0%")
        ttk.Label(main, textvariable=self.progress_label, style="Status.TLabel").pack(anchor=tk.W)

        self.status = tk.StringVar(value="Pronto. Crie um .bin ou selecione um existente + wordlist.")
        ttk.Label(main, textvariable=self.status, style="Status.TLabel").pack(anchor=tk.W, pady=(4, 6))

        log_frame = ttk.LabelFrame(main, text=" Log / Resultado ", padding=6)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log = scrolledtext.ScrolledText(
            log_frame, height=10, wrap=tk.WORD,
            bg="#11111b", fg="#a6e3a1", insertbackground="white",
            font=("Consolas", 10)
        )
        self.log.pack(fill=tk.BOTH, expand=True)

        self.log.tag_configure("pumpkin", foreground="#FF7518")

    # ==================== CARREGAR ARQUIVO COM PROGRESSO ====================
    def browse_texto(self):
        path = filedialog.askopenfilename(
            title="Selecione um arquivo de texto ou CSV",
            filetypes=[
                ("Arquivos de texto", "*.txt"),
                ("CSV", "*.csv"),
                ("Todos os arquivos", "*.*")
            ]
        )
        if path:
            self.load_file_label.set(os.path.basename(path))
            threading.Thread(target=self._carregar_arquivo, args=(path,), daemon=True).start()

    def _carregar_arquivo(self, path):
        try:
            tamanho_total = os.path.getsize(path)
            if tamanho_total == 0:
                self.root.after(0, lambda: self.load_progress_label.set("Arquivo vazio."))
                return

            self.root.after(0, lambda: self.load_progress.configure(maximum=100))
            self.root.after(0, lambda: self.load_progress.configure(value=0))
            self.root.after(0, lambda: self.load_progress_label.set("Carregando... 0%"))

            CHUNK = 64 * 1024
            lido = 0
            conteudo = []
            ultimo_percentual = -1

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                while True:
                    chunk = f.read(CHUNK)
                    if not chunk:
                        break
                    conteudo.append(chunk)
                    lido += len(chunk.encode("utf-8"))

                    percentual = int((lido / tamanho_total) * 100)
                    if percentual != ultimo_percentual:
                        ultimo_percentual = percentual
                        self.root.after(0, lambda p=percentual: self.load_progress.configure(value=p))
                        self.root.after(0, lambda p=percentual: self.load_progress_label.set(
                            f"Carregando... {p}% ({lido:,}/{tamanho_total:,} bytes)"
                        ))

            texto_completo = "".join(conteudo)
            self.root.after(0, lambda: self._finalizar_carga(texto_completo, path, tamanho_total))

        except Exception as e:
            self.root.after(0, lambda: self.load_progress_label.set(f"Erro: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{str(e)}"))

    def _finalizar_carga(self, texto, path, tamanho):
        self.texto_widget.delete("1.0", tk.END)
        self.texto_widget.insert("1.0", texto)
        self.load_progress.configure(value=100)
        self.load_progress_label.set(
            f"✓ Carregado: {os.path.basename(path)} ({tamanho:,} bytes, {len(texto):,} caracteres)"
        )
        self.status.set(f"Arquivo carregado: {os.path.basename(path)}")
        self.log_msg(f"[+] Arquivo carregado: {os.path.basename(path)} ({tamanho:,} bytes, {len(texto):,} caracteres)")

    # ==================== FUNÇÕES DE CRIAR ====================
    def gerar_bin(self):
        senha = self.senha_criar.get().strip()
        texto = self.texto_widget.get("1.0", tk.END).strip()
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
            preview = texto[:80].replace("\n", "\\n")
            self.log_msg(f"[+] Texto     : {preview}{'...' if len(texto) > 80 else ''}")
            self.log_msg(f"[+] Tamanho txt: {len(texto)} caracteres")
            self.log_msg(f"[+] IV (hex)  : {iv.hex()}")
            self.log_msg(f"[+] .bin size : {16 + len(ciphertext)} bytes")
            self.log_msg("\nAgora selecione esse .bin na seção 2 + wordlist para quebrar.")

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

    # ==================== SALVAR RESULTADO DESCRIPTOGRAFADO ====================
    def salvar_resultado(self):
        if self.ultimo_resultado is None:
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar. Execute o ataque primeiro.")
            return

        path = filedialog.asksaveasfilename(
            title="Salvar resultado descriptografado como...",
            defaultextension=".txt",
            filetypes=[
                ("Arquivo de texto", "*.txt"),
                ("CSV", "*.csv"),
                ("Todos os arquivos", "*.*")
            ]
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.ultimo_resultado)
                self.log_msg(f"\n[+] Resultado salvo em: {path}")
                self.status.set(f"✓ Salvo: {os.path.basename(path)}")
                messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso!\n{path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar:\n{str(e)}")

    # ==================== ATAQUE ====================
    def start_attack(self):
        self.stop_flag = False
        self.ultimo_resultado = None
        self.save_btn.config(state=tk.DISABLED)  # desabilita enquanto ataca
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
                        self.progress_label.set(f"{percent:.1f}% | {idx:,}/{total:,} | {speed:.0f} Senhas/s")
                        self.status.set(f"Testando: {pwd}")

                    if idx - last_log >= 2000 or idx == 1:
                        self.log_msg(f"[-] {idx:,} → {pwd}")
                        last_log = idx

                    if result is not None:
                        elapsed = time.time() - start_time
                        self.ultimo_resultado = result  # <- GUARDA O TEXTO
                        self.log_msg("\n" + "=" * 55)
                        self.log_msg(f"[+] SENHA ENCONTRADA: {pwd}\n\n", tag="pumpkin")
                        self.log_msg(f"[+] Posição na wordlist: {idx:,}\n")
                        self.log_msg(f"[+] Tempo total: {elapsed:.1f} segundos\n\n")
                        self.log_msg(f"[+] Texto Descriptografado:\n{result}\n\n")
                        self.log_msg("=" * 55)
                        self.status.set(f"✓ SUCESSO! Senha: {pwd}")
                        self.progress["value"] = total
                        self.progress_label.set("100% - SENHA ENCONTRADA")
                        # HABILITA O BOTÃO DE SALVAR
                        self.root.after(0, lambda: self.save_btn.config(state=tk.NORMAL))
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
