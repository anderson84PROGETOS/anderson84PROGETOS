import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import requests
from threading import Thread
from datetime import datetime
import html
import re

# ==============================
# CONFIGURAÇÕES
# ==============================

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


import platform

class GobusterGUI(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Directory Brute Forcer")
        self.geometry("950x700")
        self.minsize(800, 600)

        try:
            if platform.system() == "Windows":
                self.after(100, lambda: self.state("zoomed"))

                # Kali linux
            else:
                largura = self.winfo_screenwidth()
                altura = self.winfo_screenheight()
                self.geometry(f"{largura}x{altura}+0+0")
        except Exception:
            pass

        self.scanning = False
        self.wordlist_path = tk.StringVar()

        self.total_words = 0
        self.remaining_words = 0
        self.found_count = 0
        self.results = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # ==============================
        # CONFIGURAÇÃO
        # ==============================

        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=20, pady=15, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="URL Alvo:").grid(row=0, column=0, padx=10, pady=8, sticky="w")

        self.url_entry = ctk.CTkEntry(frame, placeholder_text="")
        self.url_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(frame, text="Wordlist:").grid(row=1, column=0, padx=10, pady=8, sticky="w")

        ctk.CTkEntry(frame, textvariable=self.wordlist_path, placeholder_text="Caminho para .txt").grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkButton(frame, text="Procurar", width=100, command=self.browse_file).grid(row=1, column=2, padx=10, pady=8)

        ctk.CTkLabel(frame, text="Status Codes:").grid(row=2, column=0, padx=10, pady=8, sticky="w")

        self.filter_entry = ctk.CTkEntry(frame, placeholder_text="200,204,301,302,307,403")
        self.filter_entry.insert(0, "200,204,301,302,307,403")
        self.filter_entry.grid(row=2, column=1, padx=10, pady=8, sticky="ew")

        # ==============================
        # CONTROLES
        # ==============================
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.grid(row=1, column=0, padx=20, pady=5, sticky="ew")      
        
        self.start_btn=ctk.CTkButton(ctrl,text="▶ Iniciar Scan",fg_color="#00a000",hover_color="#006b00",text_color="#000000",command=self.toggle_scan);self.start_btn.pack(side="left",padx=5)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn=ctk.CTkButton(ctrl,text="■ Parar",fg_color="#cc2222",hover_color="#881111",text_color="#030303",command=self.stop_scan,state="disabled");self.stop_btn.pack(side="left",padx=5)
        self.stop_btn.pack(side="left", padx=5)

        self.save_btn=ctk.CTkButton(ctrl,text="💾 Salvar HTML",fg_color="#0066aa",hover_color="#004477",text_color="#070707",command=self.save_html);self.save_btn.pack(side="left",padx=5)
        self.save_btn.pack(side="left", padx=5)

        # ==============================
        # CONTADORES
        # ==============================

        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.total_label = ctk.CTkLabel(stats, text="WORDLIST: 0", font=("Consolas", 12, "bold"))
        self.total_label.pack(side="left", padx=12)

        self.remaining_label = ctk.CTkLabel(stats, text="RESTANTES: 0", font=("Consolas", 12, "bold"), text_color="#ffff00")
        self.remaining_label.pack(side="left", padx=12)

        self.found_label = ctk.CTkLabel(stats, text="ENCONTRADOS: 0", font=("Consolas", 12, "bold"), text_color="#00ff41")
        self.found_label.pack(side="left", padx=12)

        # ==============================
        # URL ATUAL
        # ==============================

        self.current_url = ctk.CTkLabel(stats, text="", font=("Consolas", 12), text_color="#00ffff", anchor="w")

        self.current_url.pack(side="left", padx=(150, 10), fill="x", expand=True)

        # ==============================
        # RESULTADOS
        # ==============================

        self.result_area = ctk.CTkTextbox(self, font=("Consolas", 15), height=610)

        self.result_area.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.result_area.insert("0.0", "Aguardando início do scan...\n")

        self.result_area.configure(state="disabled")

        text = self.result_area._textbox

        text.tag_config("green", foreground="#00ff41")

        text.tag_config("pumpkin", foreground="#ff9900")

        text.tag_config("red", foreground="#ff3333")

        text.tag_config("yellow", foreground="#ffff00")

        text.tag_config("normal", foreground="#b8ffb8")

    # ==============================
    # WORDLIST
    # ==============================

    def browse_file(self):

        filename = filedialog.askopenfilename(
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if filename:

            self.wordlist_path.set(filename)

            try:

                with open(
                    filename,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as f:

                    words = [
                        line.strip()
                        for line in f
                        if line.strip()
                    ]

                self.total_words = len(words)
                self.remaining_words = self.total_words

                self.update_counters()

                self.log(
                    f"[*] Wordlist carregada: "
                    f"{self.total_words} entradas"
                )

            except Exception as e:

                messagebox.showerror(
                    "Erro",
                    f"Não foi possível ler a wordlist:\n{e}"
                )

    # ==============================
    # CONTADORES
    # ==============================

    def update_counters(self):

        self.total_label.configure(
            text=f"WORDLIST: {self.total_words}"
        )

        self.remaining_label.configure(
            text=f"RESTANTES: {self.remaining_words}"
        )

        self.found_label.configure(
            text=f"ENCONTRADOS: {self.found_count}"
        )

    # ==============================
    # LOG COLORIDO
    # ==============================

    def log(self, message):

        self.result_area.configure(
            state="normal"
        )

        text = self.result_area._textbox

        match = re.search(
            r"\[\+\]\s+(\d{3})\s+->",
            message
        )

        tag = "normal"

        if match:

            code = match.group(1)

            if code in ("200", "204"):
                tag = "green"

            elif code in ("301", "302", "307"):
                tag = "pumpkin"

            elif code == "403":
                tag = "red"

        elif "[*]" in message:
            tag = "yellow"

        text.insert(
            "end",
            message + "\n",
            tag
        )

        text.see("end")

        self.result_area.configure(
            state="disabled"
        )

    # ==============================
    # PARAR
    # ==============================

    def stop_scan(self):

        self.scanning = False

        self.log(
            "[!] Scan interrompido pelo usuário."
        )

    # ==============================
    # TOGGLE
    # ==============================

    def toggle_scan(self):

        if self.scanning:
            self.stop_scan()
        else:
            self.start_scan()

    # ==============================
    # INICIAR
    # ==============================

    def start_scan(self):

        url = self.url_entry.get().strip()
        wordlist = self.wordlist_path.get().strip()

        codes = [
            x.strip()
            for x in self.filter_entry.get().split(",")
            if x.strip()
        ]

        if not url or not wordlist:

            messagebox.showerror(
                "Erro",
                "Preencha a URL e selecione a Wordlist."
            )
            return

        if not url.startswith(
            ("http://", "https://")
        ):
            url = "http://" + url

        url = url.rstrip("/") + "/"

        # Recarrega a quantidade da wordlist
        try:

            with open(
                wordlist,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:

                words = [
                    line.strip()
                    for line in f
                    if line.strip()
                ]

        except Exception as e:

            messagebox.showerror(
                "Erro",
                f"Erro ao abrir Wordlist:\n{e}"
            )
            return

        self.total_words = len(words)
        self.remaining_words = self.total_words
        self.found_count = 0
        self.results.clear()

        self.update_counters()

        self.scanning = True

        self.start_btn.configure(
            text="Scanning...",
            state="disabled"
        )

        self.stop_btn.configure(
            state="normal"
        )

        self.result_area.configure(
            state="normal"
        )

        self.result_area.delete(
            "0.0",
            "end"
        )

        self.result_area.configure(
            state="disabled"
        )

        self.log(
            f"[*] Alvo: {url}"
        )

        self.log(
            f"[*] Wordlist: {self.total_words} entradas"
        )

        self.log(
            f"[*] Status: {', '.join(codes)}"
        )

        self.log(
            "-" * 70
        )

        Thread(
            target=self.run_scan,
            args=(url, words, codes),
            daemon=True
        ).start()

    # ==============================
    # SCAN
    # ==============================

    def run_scan(
        self,
        base_url,
        words,
        codes
    ):

        try:

            for word in words:

                if not self.scanning:
                    break

                word = word.lstrip("/")

                if not word:
                    continue

                target = base_url + word

                self.after(0, lambda t=target:
                    self.current_url.configure(text=f"Testando: {t}"))

                try:

                    response = requests.get(
                        target,
                        timeout=3,
                        allow_redirects=False
                    )

                    status = str(
                        response.status_code
                    )

                    if status in codes:

                        result = {
                            "status": status,
                            "url": target,
                            "size": len(response.content)
                        }

                        self.results.append(
                            result
                        )

                        self.found_count += 1

                        self.after(
                            0,
                            lambda s=status,
                                   t=target:
                            self.log(
                                f"[+] {s} -> {t}"
                            )
                        )

                except requests.RequestException:
                    pass

                # Diminui o contador
                self.remaining_words -= 1

                self.after(
                    0,
                    self.update_counters
                )

            if self.scanning:

                self.after(
                    0,
                    lambda: self.log(
                        "-" * 70 +
                        "\n[*] Scan finalizado."
                    )
                )

            else:

                self.after(
                    0,
                    lambda: self.log(
                        "[!] Scan interrompido."
                    )
                )

        except Exception as e:

            self.after(
                0,
                lambda: self.log(
                    f"[!] Erro: {e}"
                )
            )

        finally:

            self.scanning = False

            self.after(
                0,
                lambda: self.start_btn.configure(
                    text="▶ Iniciar Scan",
                    state="normal"
                )
            )

            self.after(
                0,
                lambda: self.stop_btn.configure(
                    state="disabled"
                )
            )

    # ==============================
    # SALVAR HTML
    # ==============================

    def save_html(self):

        if not self.results:

            messagebox.showinfo(
                "Salvar HTML",
                "Ainda não existem resultados para salvar."
            )

            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[
                ("HTML", "*.html"),
                ("Todos os arquivos", "*.*")
            ],
            initialfile="Directory Brute Forcer_resultados.html")

        if not filename:
            return

        rows = ""

        for result in self.results:

            status = result["status"]
            url = html.escape(result["url"])
            size = result["size"]

            if status in ("200", "204"):
                cls = "green"

            elif status in ("301", "302", "307"):
                cls = "pumpkin"

            elif status == "403":
                cls = "red"

            else:
                cls = "normal"

            rows += f"""
            <tr>
                <td class="{cls}">{status}</td>
                <td>{url}</td>
                <td>{size} bytes</td>
            </tr>
            """

        now = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">

<title>Directory Brute Forcer - Relatório</title>

<style>

body {{
    background:#030603;
    color:#b8ffb8;
    font-family:Consolas,monospace;
    margin:0;
    padding:30px;
}}

.container {{
    max-width:1200px;
    margin:auto;
}}

h1 {{
    color:#00ff41;
    text-align:center;
}}

.info {{
    background:#071007;
    border:1px solid #174d17;
    padding:18px;
    border-radius:10px;
    margin-bottom:20px;
}}

table {{
    width:100%;
    border-collapse:collapse;
    background:#071007;
}}

th {{
    background:#101d10;
    color:#00ff41;
    padding:12px;
    text-align:left;
}}

td {{
    padding:10px;
    border-bottom:1px solid #173017;
}}

.green {{
    color:#00ff41;
    font-weight:bold;
}}

.pumpkin {{
    color:#ff9900;
    font-weight:bold;
}}

.red {{
    color:#ff3333;
    font-weight:bold;
}}

.normal {{
    color:#b8ffb8;
}}

.footer {{
    margin-top:25px;
    text-align:center;
    color:#777;
}}

</style>
</head>

<body>

<div class="container">

<h1>🔎 Directory Brute Forcer SCAN REPORT</h1>

<div class="info">

<b>Data:</b> {now}<br><br>
<b>Total Wordlist:</b> {self.total_words}<br><br>
<b>Resultados ENCONTRADOS:</b> {self.found_count}

</div>

<table>

<thead>
<tr>
<th>STATUS</th>
<th>URL</th>
<th>TAMANHO</th>
</tr>
</thead>

<tbody>

{rows}

</tbody>

</table>

<div class="footer">
Directory Brute Forcer
</div>

</div>

</body>
</html>
"""

        try:

            with open(
                filename,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(html_content)

            messagebox.showinfo(
                "HTML salvo",
                f"Relatório salvo com sucesso:\n\n{filename}"
            )

        except Exception as e:

            messagebox.showerror(
                "Erro",
                f"Erro ao salvar HTML:\n{e}"
            )


# ==============================
# EXECUÇÃO
# ==============================

if __name__ == "__main__":
    app = GobusterGUI()
    app.mainloop()
