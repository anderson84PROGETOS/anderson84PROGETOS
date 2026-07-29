#!/usr/bin/env python3
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
import psutil

def formatar_tempo(segundos):
    """Converte segundos float para string HH:MM:SS ou DD:HH:MM:SS se necessário."""
    segundos_int = int(segundos)
    h = segundos_int // 3600
    m = (segundos_int % 3600) // 60
    s = segundos_int % 60

    if h > 0:
        return f"{h}h {m:02d}min {s:02d}s"
    elif m > 0:
        return f"{m}min {s:02d}s"
    else:
        return f"{s}s"

class AESToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AES Toolkit – Cryptography & Password Recovery Toolkit")
        self.root.configure(bg="#1e1e2e")

        sistema = platform.system()

        if sistema == "Windows":
            self.root.state("zoomed")
        else:
            largura = self.root.winfo_screenwidth()
            altura = self.root.winfo_screenheight()
            self.root.geometry(f"{largura}x{altura}+0+0")

        self.stop_flag = False
        self.ultimo_resultado = None
        self.pause_idx = 0
        self.paned = None

        # --- Monitoramento de recursos ---
        self.start_time = time.time()
        self.process = psutil.Process(os.getpid())

        self.setup_style()
        self.create_widgets()

    def alternar_senha(self):
        if self.mostrar_senha:
            self.entry_senha.config(show="*")
            self.btn_olho.config(text="👁")
            self.mostrar_senha = False
        else:
            self.entry_senha.config(show="")
            self.btn_olho.config(text="🙈")
            self.mostrar_senha = True    

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabelframe", background="#1e1e2e", foreground="#cdd6f4")
        style.configure("TLabelframe.Label", background="#1e1e2e", foreground="#89b4fa", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#89b4fa")
        style.configure("Status.TLabel", font=("Segoe UI", 12, "bold"), foreground="#a6e3a1")
        style.configure("green.Horizontal.TProgressbar", troughcolor="#313244", background="#a6e3a1")

    def create_widgets(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="🔐 AES Toolkit – Cryptography & Password Recovery Toolkit",
                  style="Header.TLabel").pack(pady=(0, 8))

        self.paned = ttk.PanedWindow(main, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)        

        # ==================== LEFT SIDE ====================
        left = ttk.Frame(self.paned, padding=5)
        self.paned.add(left, weight=1)

        # --- 1. CREATE ---
        create_frame = ttk.LabelFrame(left, text=" 1. Criar arquivo output.bin ", padding=10)
        create_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(create_frame, text="Senha que o cracker deve descobrir").pack(anchor=tk.W)

        self.senha_criar = tk.StringVar()
        self.mostrar_senha = False

        senha_frame = ttk.Frame(create_frame)
        senha_frame.pack(fill=tk.X, pady=2)

        self.entry_senha = ttk.Entry(senha_frame, textvariable=self.senha_criar, show="*", font=("Consolas", 12, "bold"))
        self.entry_senha.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.btn_olho = ttk.Button(senha_frame, text="👁", width=3, command=self.alternar_senha)
        self.btn_olho.pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(create_frame, text="Digite o texto aqui (ou carregue um arquivo)").pack(anchor=tk.W, pady=(6, 0))
        self.texto_widget = scrolledtext.ScrolledText(
            create_frame, height=6, wrap=tk.WORD,
            bg="#1e1e2e", fg="#cdd6f4", insertbackground="white",
            font=("Consolas", 12)
        )
        
        self.texto_widget.pack(fill=tk.BOTH, expand=True, pady=2)
        self.texto_widget.insert("1.0", "Este é um texto secreto de teste")

        ttk.Separator(create_frame, orient="horizontal").pack(fill=tk.X, pady=6)

        ttk.Label(create_frame, text="Carregar arquivo .txt / .csv").pack(anchor=tk.W)
        load_row = ttk.Frame(create_frame)
        load_row.pack(fill=tk.X, pady=2)
        self.load_file_label = tk.StringVar(value="Nenhum arquivo selecionado")
        ttk.Label(load_row, textvariable=self.load_file_label).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(load_row, text="Procurar...", command=self.browse_texto).pack(side=tk.LEFT)

        self.load_progress = ttk.Progressbar(create_frame, orient="horizontal", mode="determinate",
                                             style="green.Horizontal.TProgressbar")
        self.load_progress.pack(fill=tk.X, pady=(2, 0))
        self.load_progress_label = tk.StringVar(value="")
        ttk.Label(create_frame, textvariable=self.load_progress_label, style="Status.TLabel").pack(anchor=tk.W)

        ttk.Label(create_frame, text="Nome do arquivo .bin de saída").pack(anchor=tk.W, pady=(6, 0))
        self.nome_bin = tk.StringVar(value="output.bin")
        ttk.Entry(create_frame, textvariable=self.nome_bin, font=("Consolas", 12, "bold")).pack(fill=tk.X, pady=2)

        ttk.Button(create_frame, text="▶ Gerar output.bin", command=self.gerar_bin).pack(pady=8)

        # --- 2. CRACK ---
        crack_frame = ttk.LabelFrame(left, text=" 2. Quebrar arquivo .bin ", padding=10)
        crack_frame.pack(fill=tk.X, pady=5)

        bin_row = ttk.Frame(crack_frame)
        bin_row.pack(fill=tk.X, pady=2)
        ttk.Label(bin_row, text="Arquivo .bin").pack(side=tk.LEFT)
        self.bin_path = tk.StringVar()
        ttk.Entry(bin_row, textvariable=self.bin_path, font=("Consolas", 12, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(bin_row, text="Procurar...", command=self.browse_bin).pack(side=tk.LEFT)

        wl_row = ttk.Frame(crack_frame)
        wl_row.pack(fill=tk.X, pady=4)
        ttk.Label(wl_row, text="Wordlist").pack(side=tk.LEFT)
        self.wl_path = tk.StringVar()
        ttk.Entry(wl_row, textvariable=self.wl_path, font=("Consolas", 11, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(wl_row, text="Procurar...", command=self.browse_wordlist).pack(side=tk.LEFT)

        btn_row = ttk.Frame(crack_frame)
        btn_row.pack(fill=tk.X, pady=10)

        self.start_btn = ttk.Button(btn_row, text="▶ Iniciar Ataque", command=self.start_attack)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.stop_btn = ttk.Button(btn_row, text="⏹ Parar", command=self.stop_attack, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.continue_btn = ttk.Button(btn_row, text="▶ Continuar", command=self.continue_attack, state=tk.DISABLED)
        self.continue_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.save_btn = ttk.Button(btn_row, text="💾 Salvar resultado", command=self.salvar_resultado, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(left, orient="horizontal", mode="determinate",
                                        style="green.Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, pady=(10, 2))

        self.progress_label = tk.StringVar(value="0%")
        ttk.Label(left, textvariable=self.progress_label, style="Status.TLabel").pack(anchor=tk.W)

        self.status = tk.StringVar(value="Pronto. Crie um .bin ou selecione um existente + wordlist.")
        ttk.Label(left, textvariable=self.status, style="Status.TLabel").pack(anchor=tk.W, pady=(4, 0))

        # ==================== RIGHT SIDE ====================
        right = ttk.Frame(self.paned, padding=5)
        self.paned.add(right, weight=2)

        log_frame = ttk.LabelFrame(right, text=" Log / Resultado (Senha + Texto Descriptografado) ", padding=6)
        log_frame.pack(fill=tk.BOTH, expand=True, anchor="n", pady=(0, 100))

        self.log = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD,
            bg="#11111b", fg="#a6e3a1", insertbackground="white",
            font=("Consolas", 11)
        )
        self.log.pack(fill=tk.BOTH, expand=True)

        self.log.tag_configure("pumpkin", foreground="#FF7518", font=("Consolas", 12, "bold"))
        self.log.tag_configure("success", foreground="#a6e3a1", font=("Consolas", 11, "bold"))
        self.log.tag_configure("info", foreground="#89b4fa")

        self.root.after(200, lambda: self.paned.sashpos(0, 650))

        # ==================== FOOTER ====================
        footer = tk.Frame(self.root, bg="#181825", height=30)
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        texto = (
            "AES Toolkit  |  "
            "AES-256 CBC  |  "
            "Criação de arquivos criptografados (.bin)  |  "
            "Ataque por Wordlist  |  "
            "Recuperação de senha  |  "
            "Descriptografia de arquivos  |  "
            "Suporte: TXT / CSV"
        )

        tk.Label(
            footer,
            text=texto,
            bg="#181825",
            fg="#89b4fa",
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT, padx=10)

        # --- Monitoramento de recursos no footer ---
        self.footer_status = tk.StringVar(value="RAM: 0 MB | CPU: 0% | Tempo: 00:00:00")

        tk.Label(
            footer,
            textvariable=self.footer_status,
            bg="#181825",
            fg="#a6e3a1",
            font=("Consolas", 10, "bold")
        ).pack(side=tk.RIGHT, padx=10)

        self.update_footer()

    # ==================== FOOTER MONITOR ====================
    def update_footer(self):
        try:
            ram = self.process.memory_info().rss / 1024 / 1024
            cpu = psutil.cpu_percent(interval=None)

            tempo = int(time.time() - self.start_time)

            h = tempo // 3600
            m = (tempo % 3600) // 60
            s = tempo % 60

            self.footer_status.set(
                f"RAM: {ram:.0f} MB | CPU: {cpu:.0f}% | Tempo: {h:02}:{m:02}:{s:02}"
            )
        except:
            pass

        self.root.after(1000, self.update_footer)

    # ==================== LOAD FILE ====================
    def browse_texto(self):
        path = filedialog.askopenfilename(
            title="Selecione um arquivo de texto ou CSV",
            filetypes=[("Arquivos de texto", "*.txt"), ("CSV", "*.csv"), ("Todos", "*.*")]
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

            self.root.after(0, lambda: self.load_progress.configure(maximum=100, value=0))
            self.root.after(0, lambda: self.load_progress_label.set("Carregando... 0%"))

            CHUNK = 64 * 1024
            lido = 0
            conteudo = []
            ultimo = -1

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                while True:
                    chunk = f.read(CHUNK)
                    if not chunk:
                        break
                    conteudo.append(chunk)
                    lido += len(chunk.encode("utf-8"))
                    p = int((lido / tamanho_total) * 100)
                    if p != ultimo:
                        ultimo = p
                        self.root.after(0, lambda p=p: self.load_progress.configure(value=p))
                        self.root.after(0, lambda p=p, l=lido, t=tamanho_total: 
                            self.load_progress_label.set(f"Carregando... {p}% ({l:,}/{t:,} bytes)")
                        )

            texto = "".join(conteudo)
            self.root.after(0, lambda: self._finalizar_carga(texto, path, tamanho_total))
        except Exception as e:
            self.root.after(0, lambda e=e: self.load_progress_label.set(f"Erro: {e}"))
            self.root.after(0, lambda e=e: messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{e}"))

    def _finalizar_carga(self, texto, path, tamanho):
        self.texto_widget.delete("1.0", tk.END)
        self.texto_widget.insert("1.0", texto)
        self.load_progress.configure(value=100)
        self.load_progress_label.set(
            f"✓ Carregado: {os.path.basename(path)} ({tamanho:,} bytes, {len(texto):,} caracteres)"
        )
        self.status.set(f"Arquivo carregado: {os.path.basename(path)}")
        self.log_msg(f"[+] Arquivo carregado: {os.path.basename(path)} ({tamanho:,} bytes)", tag="info")

    # ==================== CREATE BIN ====================
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
            self.log_msg("[+] Arquivo gerado com sucesso!", tag="success")
            self.log_msg(f"[+] Nome   : {nome}")
            self.log_msg(f"[+] Senha  : {senha}", tag="pumpkin")
            preview = texto[:100].replace("\n", "\\n")
            self.log_msg(f"[+] Texto  : {preview}{'...' if len(texto) > 100 else ''}")
            self.log_msg(f"[+] Tamanho: {len(texto)} caracteres")
            self.log_msg(f"[+] IV     : {iv.hex()}")
            self.log_msg(f"[+] Size   : {16 + len(ciphertext)} bytes")
            self.log_msg("\nAgora selecione esse .bin na seção 2 + wordlist para quebrar.")

            self.bin_path.set(os.path.abspath(nome))
            self.status.set(f"Arquivo {nome} criado com sucesso!")
            messagebox.showinfo("Sucesso", f"Arquivo  {nome}   Criado\n\nSenha: {senha}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # ==================== BROWSE ====================
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
        self.continue_btn.config(state=tk.DISABLED)
        self.status.set("Parando... aguarde a senha atual terminar.")

    def continue_attack(self):
        """Retoma o ataque de onde parou."""
        self.stop_flag = False
        self.continue_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        threading.Thread(target=self.run_attack, args=(self.pause_idx,), daemon=True).start()

    def salvar_resultado(self):
        if self.ultimo_resultado is None:
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar.")
            return

        path = filedialog.asksaveasfilename(
            title="Salvar resultado descriptografado",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("CSV", "*.csv"), ("Todos", "*.*")]
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.ultimo_resultado)
                self.log_msg(f"\n[+] Resultado salvo em: {path}", tag="success")
                self.status.set(f"✓ Salvo: {os.path.basename(path)}")
                messagebox.showinfo("Sucesso", f"Arquivo salvo!\n{path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar:\n{e}")

    # ==================== ATTACK ====================
    def start_attack(self):
        self.stop_flag = False
        self.pause_idx = 0
        self.ultimo_resultado = None
        self.save_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.continue_btn.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.progress_label.set("0%")
        self.log_msg("", clear=True)
        threading.Thread(target=self.run_attack, args=(1,), daemon=True).start()

    # ----- Helpers thread-safe para UI -----
    def _safe_log(self, msg, tag=None):
        self.root.after(0, lambda m=msg, t=tag: self.log_msg(m, tag=t))

    def _safe_status(self, msg):
        self.root.after(0, lambda m=msg: self.status.set(m))

    def _safe_progress_config(self, **kwargs):
        self.root.after(0, lambda kw=kwargs: self.progress.configure(**kw))

    def _safe_progress_label(self, texto):
        self.root.after(0, lambda t=texto: self.progress_label.set(t))

    def _safe_msgbox_error(self, titulo, msg):
        self.root.after(0, lambda t=titulo, m=msg: messagebox.showerror(t, m))

    def _safe_enable_save(self):
        self.root.after(0, lambda: self.save_btn.config(state=tk.NORMAL))

    def _safe_finish_buttons(self):
        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))

    def run_attack(self, start_idx=1):
        try:
            bin_path = self.bin_path.get().strip()
            wl_path = self.wl_path.get().strip()

            if not bin_path or not os.path.exists(bin_path):
                self._safe_msgbox_error("Erro", "Arquivo binário inválido.")
                return
            if not wl_path or not os.path.exists(wl_path):
                self._safe_msgbox_error("Erro", "Wordlist inválida.")
                return

            with open(bin_path, "rb") as f:
                data = f.read()

            if len(data) < 17:
                self._safe_msgbox_error("Erro", "Arquivo muito curto (mínimo 17 bytes).")
                return

            iv = data[:16]
            ciphertext = data[16:]

            self._safe_log(f"[*] Arquivo   : {os.path.basename(bin_path)}", tag="info")
            self._safe_log(f"[*] Tamanho   : {len(data)} bytes")
            self._safe_log(f"[*] IV        : {iv.hex()}")
            self._safe_log(f"[*] Ciphertext: {len(ciphertext)} bytes\n")

            self._safe_status("Contando senhas da wordlist...")
            total = 0
            with open(wl_path, "r", encoding="utf-8", errors="ignore") as f:
                for _ in f:
                    total += 1

            # Configura a barra de progresso com o total real
            self._safe_progress_config(maximum=total, value=(start_idx - 1))

            if start_idx > 1:
                self._safe_log(f"[*] Retomando da linha {start_idx:,} de {total:,} senhas\n")
            else:
                self._safe_log(f"[*] Wordlist  : {total:,} senhas\n")
                self._safe_log("[*] Iniciando ataque completo...\n")

            found = False
            attack_start = time.time()

            with open(wl_path, "r", encoding="utf-8", errors="ignore") as f:
                # Pula as linhas já testadas (se for retomada)
                if start_idx > 1:
                    for _ in range(start_idx - 1):
                        try:
                            next(f)
                        except StopIteration:
                            break

                for idx, line in enumerate(f, start_idx):
                    if self.stop_flag:
                        self.pause_idx = idx
                        self._safe_log(f"\n[!] Interrompido na senha {idx:,}")
                        decorrido = formatar_tempo(time.time() - attack_start)
                        self._safe_status(f"⏸ Parado na senha {idx:,} ({decorrido}) — aperte Continuar para retomar.")
                        self.root.after(0, lambda i=idx, t=total: self.continue_btn.config(state=tk.NORMAL)
                                        if i < t else None)
                        break

                    pwd = line.strip()
                    if not pwd:
                        continue

                    result = self.try_decrypt(ciphertext, iv, pwd)

                    # Atualiza UI a cada 100 senhas
                    if idx % 100 == 0 or idx == 1:
                        elapsed = time.time() - attack_start
                        speed = idx / elapsed if elapsed > 0 else 0
                        percent = (idx / total) * 100
                        restante = total - idx
                        eta = restante / speed if speed > 0 else 0

                        self._safe_progress_config(value=idx)
                        self._safe_progress_label(
                            f"{percent:5.1f}% | {idx:,}/{total:,} | {speed:,.0f} senhas/s | ETA: {eta/60:.1f} min"
                        )
                        self._safe_status(f"Testando: {pwd}")

                    # Mostra senha no log a cada 2.000 tentativas
                    if idx % 2000 == 0 or idx == 1:
                        self._safe_log(f"[-] {idx:,} → {pwd}")                     

                    if result is not None:
                        elapsed = time.time() - attack_start
                        self.ultimo_resultado = result

                        tempo_str = formatar_tempo(elapsed)

                        self._safe_log("\n" + "=" * 60)
                        self._safe_log(f"[+] SENHA ENCONTRADA", tag="pumpkin")
                        self._safe_log(f"\n[+] Linha:{idx:,}      Senha: {pwd}", tag="pumpkin")
                        self._safe_log(f"\n[+] Tempo total: {tempo_str}", tag="success")
                        self._safe_log("\n[+] TEXTO DESCRIPTOGRAFADO\n", tag="success")
                        self._safe_log(result + "\n")
                        self._safe_log("=" * 60)

                        self._safe_status(f"✓ SUCESSO! Senha: {pwd:<40}  | Tempo: {tempo_str}")
                        self._safe_progress_config(value=total)
                        self._safe_progress_label("100% - SENHA ENCONTRADA")
                        self._safe_enable_save()
                        found = True
                        break

            if not found and not self.stop_flag:
                elapsed = time.time() - attack_start
                tempo_str = formatar_tempo(elapsed)
                self._safe_log(f"\n[-] Terminou toda a wordlist ({total:,} senhas).")
                self._safe_log(f"[-] Tempo total: {tempo_str}")
                self._safe_log("[-] Nenhuma senha funcionou.")
                self._safe_status(f"Nenhuma senha encontrada. Tempo: {tempo_str}")
                self._safe_progress_config(value=total)
                self._safe_progress_label("100% - Finalizado")

        except Exception as e:
            self._safe_log(f"\n[ERRO] {str(e)}")
            self._safe_status("Erro ocorrido.")
            self._safe_msgbox_error("Erro", str(e))
        finally:
            self._safe_finish_buttons()

if __name__ == "__main__":
    root = tk.Tk()
    app = AESToolGUI(root)
    root.mainloop()
