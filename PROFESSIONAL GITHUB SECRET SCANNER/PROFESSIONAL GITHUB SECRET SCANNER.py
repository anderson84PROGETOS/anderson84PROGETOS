# =========================================================
# PROFESSIONAL GITHUB SECRET SCANNER
# ✔ GUI MODERNA
# ✔ MULTITHREAD
# ✔ DARK MODE
# ✔ SCAN COMPLETO
# ✔ FILTRO
# ✔ EXPORTAR TXT
# ✔ TEMPO REAL
# ✔ WINDOWS 10/11
# =========================================================

import customtkinter as ctk
from tkinter import filedialog, messagebox
import requests
import threading
import concurrent.futures
import re
import queue
import time

# =========================================================
# CONFIG
# =========================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# =========================================================
# APP
# =========================================================

class SecretScanner:

    def __init__(self):

        self.app = ctk.CTk()

        self.app.title("PROFESSIONAL GITHUB SECRET SCANNER")

        self.app.geometry("1400x900")

        self.app.after(100, lambda: self.app.state("zoomed"))

        self.resultados = []

        self.queue_logs = queue.Queue()

        self.scanning = False

        # =====================================================
        # HEADER
        # =====================================================

        self.titulo = ctk.CTkLabel(
            self.app,
            text="GITHUB SECRET SCANNER",
            font=("Consolas", 32, "bold"),
            text_color="#00ff99"
        )

        self.titulo.pack(pady=20)

        # =====================================================
        # URL
        # =====================================================

        frame_url = ctk.CTkFrame(self.app)

        frame_url.pack(fill="x", padx=20, pady=10)

        self.url_entry = ctk.CTkEntry(
            frame_url,
            placeholder_text="https://github.com/user/repository",
            height=40,
            font=("Consolas", 14)
        )

        self.url_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=10,
            pady=10
        )

        self.btn_scan = ctk.CTkButton(
            frame_url,
            text="START SCAN",
            command=self.start_scan,
            fg_color="#00aa66",
            hover_color="#008844",
            text_color="black",
            width=180,
            height=40,
            font=("Arial", 14, "bold")
        )

        self.btn_scan.pack(side="left", padx=10)

        # =====================================================
        # BUTTONS
        # =====================================================

        frame_buttons = ctk.CTkFrame(self.app)

        frame_buttons.pack(fill="x", padx=20, pady=10)

        self.btn_clear = ctk.CTkButton(
            frame_buttons,
            text="CLEAR",
            command=self.clear,
            fg_color="#aa00aa",
            text_color="black",
            width=150
        )

        self.btn_clear.pack(side="left", padx=10, pady=10)

        self.btn_save = ctk.CTkButton(
            frame_buttons,
            text="EXPORT TXT",
            command=self.save_txt,
            fg_color="#cc3333",
            text_color="black",
            width=150
        )

        self.btn_save.pack(side="left", padx=10)

        # =====================================================
        # SEARCH
        # =====================================================

        self.search_entry = ctk.CTkEntry(
            frame_buttons,
            placeholder_text="Search result...",
            width=300
        )

        self.search_entry.pack(side="left", padx=20)

        self.btn_search = ctk.CTkButton(
            frame_buttons,
            text="SEARCH",
            text_color="black",
            command=self.search
        )

        self.btn_search.pack(side="left", padx=5)

        # =====================================================
        # STATUS
        # =====================================================

        self.status = ctk.CTkLabel(
            self.app,
            text="READY",
            font=("Consolas", 14, "bold"),
            text_color="#00ff99"
            
        )

        self.status.pack(pady=5)

        self.progress = ctk.CTkProgressBar(self.app)

        self.progress.pack(fill="x", padx=20)

        self.progress.set(0)

        # =====================================================
        # TEXTBOX
        # =====================================================

        self.textbox = ctk.CTkTextbox(
            self.app,
            font=("Consolas", 13),
            text_color="#00ff99"
        )

        self.textbox.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        # =====================================================
        # PATTERNS
        # =====================================================

        self.patterns = [

            r"password",
            r"passwd",
            r"secret",
            r"token",
            r"api_key",
            r"access_token",

            r"ghp_[A-Za-z0-9]{20,}",
            r"github_pat_[A-Za-z0-9_]+",

            r"AKIA[0-9A-Z]{16}",

            r"AIza[0-9A-Za-z\-_]{35}",

            r"sk_live_[A-Za-z0-9]+",

            r"BEGIN RSA PRIVATE KEY",

            r"mongodb://",

            r"postgres://",

            r"mysql://",

            r"firebaseio\.com",

            r"discord",

            r"webhook",

            r"\.env",

            r"bearer",

            r"authorization",

            r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"

            # =====================================================
            # SENHAS / TOKENS
            # =====================================================  
            
            r"senha",            
            r"pwd",                     
            r"client_secret",            
            r"refresh_token",           
            
            # =====================================================
            # API KEYS
            # =====================================================
            
            r"apikey",
            r"x-api-key",

            # =====================================================
            # GITHUB
            # =====================================================

            r"ghp_[A-Za-z0-9]{36}",            

            # =====================================================
            # STRIPE
            # =====================================================

            r"pk_live_[A-Za-z0-9]+",

            # =====================================================
            # DISCORD / TELEGRAM
            # =====================================================

            r"telegram",
            r"bot_token",

            # =====================================================
            # EMAILS
            # =====================================================

            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",

            r"@gmail\.com",
            r"@hotmail\.com",
            r"@outlook\.com",
            r"@yahoo\.com",
            r"@protonmail\.com",

            # =====================================================
            # DATABASE
            # =====================================================

            r"database",
            r"mongodb",
            r"mysql",
            r"postgres",
            r"postgresql",
            r"sqlite",
            r"redis",

            # =====================================================
            # URLs
            # =====================================================

            r"https://",
            r"http://",

            # =====================================================
            # ARQUIVOS SENSÍVEIS
            # =====================================================

            r"\.env\.local",
            r"\.env\.prod",
            r"config\.json",
            r"credentials",

            # =====================================================
            # IP
            # =====================================================

            r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",

            # =====================================================
            # CPF
            # =====================================================

            r"\d{3}\.\d{3}\.\d{3}-\d{2}",

            # =====================================================
            # PIX
            # =====================================================

            r"pix",

            # =====================================================
            # FIREBASE
            # =====================================================

            r"firebase",            

            # =====================================================
            # PRIVATE KEY
            # =====================================================

            r"BEGIN PRIVATE KEY",
            r"BEGIN OPENSSH PRIVATE KEY",

            # =====================================================
            # CLOUD
            # =====================================================

            r"amazonaws\.com",
            r"cloudflare",
            r"digitalocean",

        ]

        # =====================================================
        # UPDATE LOOP
        # =====================================================

        self.update_logs()

        self.app.mainloop()

    # =========================================================
    # LOG
    # =========================================================

    def log(self, text):

        self.queue_logs.put(text)

    def update_logs(self):

        while not self.queue_logs.empty():

            text = self.queue_logs.get()

            self.textbox.insert("end", text + "\n")

            self.textbox.see("end")

        self.app.after(100, self.update_logs)

    # =========================================================
    # CLEAR
    # =========================================================

    def clear(self):

        self.textbox.delete("1.0", "end")

        self.resultados.clear()

    # =========================================================
    # SAVE
    # =========================================================

    def save_txt(self):

        file = filedialog.asksaveasfilename(
            defaultextension=".txt"
        )

        if not file:
            return

        with open(file, "w", encoding="utf-8") as f:

            f.write(
                self.textbox.get("1.0", "end")
            )

        messagebox.showinfo(
            "SUCCESS",
            "TXT EXPORTED"
        )

    # =========================================================
    # SEARCH
    # =========================================================

    def search(self):

        term = self.search_entry.get().lower()

        self.textbox.delete("1.0", "end")

        for item in self.resultados:

            if term in item.lower():

                self.log(item)

    # =========================================================
    # EXTRACT
    # =========================================================

    def extract_repo(self, url):

        try:

            parts = url.split("github.com/")[1].split("/")

            return parts[0], parts[1]

        except:

            return None, None

    # =========================================================
    # GET FILES
    # =========================================================

    def get_files(self, user, repo):

        api = f"https://api.github.com/repos/{user}/{repo}"

        r = requests.get(api)

        branch = r.json().get(
            "default_branch",
            "main"
        )

        tree_url = (
            f"https://api.github.com/repos/"
            f"{user}/{repo}/git/trees/"
            f"{branch}?recursive=1"
        )

        r2 = requests.get(tree_url)

        tree = r2.json()

        files = []

        for item in tree.get("tree", []):

            if item.get("type") == "blob":

                files.append(item.get("path"))

        return files, branch

    # =========================================================
    # MASK
    # =========================================================

    def mask(self, line):

        line = re.sub(
            r'ghp_[A-Za-z0-9]+',
            'ghp_********',
            line
        )

        line = re.sub(
            r'AKIA[0-9A-Z]+',
            'AKIA********',
            line
        )

        return line

    # =========================================================
    # START
    # =========================================================

    def start_scan(self):

        if self.scanning:
            return

        threading.Thread(
            target=self.scan,
            daemon=True
        ).start()

    # =========================================================
    # SCAN FILE
    # =========================================================

    def scan_file(self, user, repo, branch, file):

        raw = (
            f"https://raw.githubusercontent.com/"
            f"{user}/{repo}/{branch}/{file}"
        )

        try:

            r = requests.get(
                raw,
                timeout=10
            )

            if r.status_code != 200:
                return

            lines = r.text.splitlines()

            for n, line in enumerate(lines):

                for pattern in self.patterns:

                    if re.search(
                        pattern,
                        line,
                        re.IGNORECASE
                    ):

                        safe = self.mask(line.strip())

                        result = (

                            "\n"
                            + "="*70 + "\n"
                            + f"FILE: {file}\n"
                            + f"LINE: {n+1}\n"
                            + f"PATTERN: {pattern}\n"
                            + f"CONTENT: {safe[:500]}\n"
                            + "="*70
                        )

                        self.resultados.append(result)

                        self.log(result)

                        break

        except Exception as e:

            self.log(f"ERROR {file}: {e}")

    # =========================================================
    # SCAN
    # =========================================================

    def scan(self):

        self.scanning = True

        self.progress.set(0)

        self.clear()

        url = self.url_entry.get().strip()

        user, repo = self.extract_repo(url)

        if not user:

            messagebox.showerror(
                "ERROR",
                "INVALID URL"
            )

            self.scanning = False

            return

        self.log("="*70)

        self.log(f"REPOSITORY: {user}/{repo}")

        self.log("="*70)

        try:

            files, branch = self.get_files(
                user,
                repo
            )

            total = len(files)

            self.log(f"BRANCH: {branch}")

            self.log(f"FILES: {total}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:

                futures = []

                for i, file in enumerate(files):

                    self.status.configure(
                        text=f"SCANNING: {file}"
                    )

                    progress = (i + 1) / total

                    self.progress.set(progress)

                    future = executor.submit(
                        self.scan_file,
                        user,
                        repo,
                        branch,
                        file
                    )

                    futures.append(future)

                for f in futures:
                    f.result()

            self.progress.set(1)

            self.status.configure(
                text="SCAN COMPLETED"
            )

            self.log("")

            self.log("="*70)

            self.log(
                f"TOTAL DETECTIONS: {len(self.resultados)}"
            )

            self.log("="*70)

            messagebox.showinfo(
                "FINISHED",
                "SCAN COMPLETE"
            )

        except Exception as e:

            messagebox.showerror(
                "ERROR",
                str(e)
            )

        self.scanning = False

# =========================================================
# RUN
# =========================================================

SecretScanner()
