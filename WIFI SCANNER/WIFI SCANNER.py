import subprocess
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime

class HackerWiFiScanner:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WI-FI SCANNER")
        self.root.geometry("1150x720")
        self.root.state("zoomed")
        self.root.resizable(True, True)
        self.root.configure(bg="#0a0a0a")

        # Título
        title = tk.Label(self.root, text="WI-FI SCANNER", 
                        font=("Consolas", 26, "bold"), 
                        fg="#00ff41", bg="#0a0a0a")
        title.pack(pady=12)

        subtitle = tk.Label(self.root, text="NEURAL INTERFACE // SCANNING WIRELESS NETWORKS", 
                           font=("Consolas", 11), fg="#00cc33", bg="#0a0a0a")
        subtitle.pack(pady=(0, 10))

        # Botões
        btn_frame = tk.Frame(self.root, bg="#0a0a0a")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="▶ ESCANEAR REDES", font=("Consolas", 12, "bold"),
                  bg="#003300", fg="#00ff41", width=22, height=2,
                  activebackground="#006600", relief="ridge", bd=3,
                  command=self.scan_wifi).pack(side="left", padx=12)

        tk.Button(btn_frame, text="💾 SALVAR RESULTADOS", font=("Consolas", 12, "bold"),
                  bg="#003300", fg="#00ff41", width=22, height=2,
                  activebackground="#006600", relief="ridge", bd=3,
                  command=self.save_results).pack(side="left", padx=12)

        tk.Button(btn_frame, text="⌫ LIMPAR", font=("Consolas", 12, "bold"),
                  bg="#003300", fg="#00ff41", width=18, height=2,
                  activebackground="#006600", relief="ridge", bd=3,
                  command=self.clear_all).pack(side="left", padx=12)

        # ==================== TABELA ====================
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#0a0a0a", foreground="#00ff41",
                       fieldbackground="#0a0a0a", font=("Consolas", 10))
        style.configure("Treeview.Heading", background="#003300", 
                       foreground="#00ff41", font=("Consolas", 11, "bold"))
        style.map("Treeview", background=[('selected', '#004400')],
                  foreground=[('selected', '#88ff88')])

        columns = ("BSSID", "ESSID", "Canal", "Sinal", "Autenticação", "Criptografia")

        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=18)

        self.tree.heading("BSSID", text="BSSID  (AP) MAC")
        self.tree.heading("ESSID", text="SSID   NOME DA REDE")
        self.tree.heading("Canal", text="CANAL")
        self.tree.heading("Sinal", text="SINAL")
        self.tree.heading("Autenticação", text="AUTENTICAÇÃO")
        self.tree.heading("Criptografia", text="CRIPTOGRAFIA")

        # === Tamanhos exatos que você pediu ===
        self.tree.column("BSSID", width=160, anchor="center")
        self.tree.column("ESSID", width=280)
        self.tree.column("Canal", width=80, anchor="center")
        self.tree.column("Sinal", width=100, anchor="center")
        self.tree.column("Autenticação", width=200)
        self.tree.column("Criptografia", width=160)

        self.tree.pack(padx=20, pady=10, fill="both", expand=True)

        # Duplo clique
        self.tree.bind("<Double-1>", self.copy_on_double_click)

        # Log
        log_frame = tk.LabelFrame(self.root, text=" TERMINAL LOG ", 
                                 font=("Consolas", 10), fg="#00ff41", bg="#0a0a0a")
        log_frame.pack(fill="both", padx=20, pady=5)

        self.log = tk.Text(log_frame, height=9, bg="#000000", fg="#00ff41",
                          font=("Consolas", 10), relief="flat")
        self.log.pack(fill="both", padx=8, pady=8)

        # Rodapé
        footer = tk.Label(self.root, 
            text="""📖 Duplo-clique na célula para copiar | BSSID ou ESSID = informação individual | Outras colunas = dados completos""",
            bg="#111111", fg="#05fdf1", font=("Consolas", 10), justify="left", anchor="w", padx=15, pady=12)
        footer.pack(side="bottom", fill="x")

        self.log_message("[+] Sistema carregado. Pronto para escanear\n")

    def log_message(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log.see(tk.END)

    def scan_wifi(self):
        self.log_message("[*] Iniciando varredura completa de redes...\n")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.root.update()

        try:
            output = subprocess.check_output(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                shell=True, text=True, encoding='utf-8', errors='ignore'
            )

            networks = re.split(r'\n\n+', output.strip())
            results = []

            for net in networks:
                if "BSSID" not in net:
                    continue

                ssid_match = re.search(r'SSID\s+\d+\s+:\s+(.+)', net)
                bssid_match = re.search(r'BSSID\s+\d+\s+:\s+([0-9A-Fa-f:]+)', net)
                signal_match = re.search(r'Sinal\s+:\s+(\d+)', net)
                channel_match = re.search(r'Canal\s+:\s+(\d+)', net)
                auth_match = re.search(r'(?:Autenticação|Authentication)\s+:\s+(.+)', net)
                enc_match = re.search(r'(?:Criptografia|Encryption)\s+:\s+(.+)', net)

                essid = ssid_match.group(1).strip() if ssid_match else "N/D"
                bssid = bssid_match.group(1).strip() if bssid_match else "N/D"
                canal = channel_match.group(1).strip() if channel_match else "?"
                sinal_raw = int(signal_match.group(1).strip()) if signal_match else 0
                sinal_str = f"{sinal_raw}%"
                autenticacao = auth_match.group(1).strip() if auth_match else "N/D"
                criptografia = enc_match.group(1).strip() if enc_match else "N/D"

                results.append((bssid, essid, canal, sinal_str, sinal_raw, autenticacao, criptografia))

            # Ordenar por força do sinal
            results.sort(key=lambda x: x[4], reverse=True)

            for item in results:
                self.tree.insert("", "end", values=(item[0], item[1], item[2], item[3], item[5], item[6]))

            self.log_message(f"[+] {len(results)} redes detectadas e ordenadas por força de sinal\n")

        except Exception as e:
            self.log_message(f"[!] Erro: {e}")
            messagebox.showerror("Erro", f"Falha no scan:\n{e}")

    def copy_on_double_click(self, event):
        # Identificar qual coluna foi clicada
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0])['values']
        bssid = values[0]
        essid = values[1]
        canal = values[2]
        sinal = values[3]
        auth = values[4]
        enc = values[5]

        text_to_copy = ""

        # Lógica inteligente por coluna
        if column == "#1":   # BSSID
            text_to_copy = bssid
            self.log_message(f"[✓] BSSID copiado: {bssid}\n")

        elif column == "#2": # Nome da Rede (ESSID)
            text_to_copy = essid
            self.log_message(f"[✓] SSID Nome da rede copiado: {essid}\n")

        else:                # Qualquer outra coluna
            text_to_copy = f"BSSID : {bssid}\nRede  : {essid}\nCanal : {canal}\nSinal : {sinal}\nAuth  : {auth}\nCripto: {enc}"
            self.log_message(f"[✓] Informações completas copiadas: {essid}\n")

        # Copiar para clipboard
        if text_to_copy:
            self.root.clipboard_clear()
            self.root.clipboard_append(text_to_copy)
            self.root.update()

    def save_results(self):
        if not self.tree.get_children():
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar\n")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt")],
            initialfile=f"wifi_scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("=== WI-FI SCANNER ===\n")
                    f.write(f"Data: {datetime.datetime.now()}\n\n")
                    for child in self.tree.get_children():
                        v = self.tree.item(child)['values']
                        f.write(f"BSSID        : {v[0]}\n")
                        f.write(f"Rede         : {v[1]}\n")
                        f.write(f"Canal        : {v[2]}\n")
                        f.write(f"Sinal        : {v[3]}\n")
                        f.write(f"Autenticação : {v[4]}\n")
                        f.write(f"Criptografia : {v[5]}\n")
                        f.write("-" * 70 + "\n\n")
                self.log_message(f"[💾] Salvo em: {file_path}")
                messagebox.showinfo("Sucesso", "Resultados salvos!")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def clear_all(self):
        if messagebox.askyesno("Confirmar", "Limpar tudo\n"):
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.log.delete(1.0, tk.END)
            self.log_message("[+] Interface limpa\n")

if __name__ == "__main__":
    app = HackerWiFiScanner()
    app.root.mainloop()
