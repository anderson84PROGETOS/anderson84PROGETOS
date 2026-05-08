import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import ctypes
import os
import shutil
import threading
import time

# =========================================================
# CONFIG
# =========================================================

BG = "#1e1e1e"
FG = "#00ff88"
BLUE = "#00ddff"

CREATE_NO_WINDOW = 0x08000000

# =========================================================
# POLITICAS BLOQUEIO IA
# =========================================================

REG_COMMANDS = [

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v AIModeSettings /t REG_DWORD /d 2 /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v GeminiSettings /t REG_DWORD /d 2 /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v HelpMeWriteSettings /t REG_DWORD /d 2 /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v CreateThemesSettings /t REG_DWORD /d 2 /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v HistorySearchSettings /t REG_DWORD /d 2 /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v TabCompareSettings /t REG_DWORD /d 2 /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v AutofillPredictionSettings /t REG_DWORD /d 2 /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v DevToolsGenAiSettings /t REG_DWORD /d 2 /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v SearchContentSharingSettings /t REG_DWORD /d 2 /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v TabOrganizerSettings /t REG_DWORD /d 2 /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v GeminiActOnWebSettings /t REG_DWORD /d 2 /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v GenAILocalFoundationalModelSettings /t REG_DWORD /d 2 /f',

    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v BrowserLabsEnabled /t REG_DWORD /d 0 /f'
]

# =========================================================
# PASTAS IA
# =========================================================

FOLDERS_TO_DELETE = [

    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\OptGuideOnDeviceModel"),

    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\optimization_guide_model_store"),

    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\OnDeviceHeadSuggestModel"),

    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\OptimizationHints"),

    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\OnDeviceModel"),

    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\GeminiNano"),

    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\OptGuideOnDeviceClassifierModel")
]

# =========================================================
# APP
# =========================================================

class ChromeAIDisabler:

    def __init__(self, root):

        self.root = root

        self.monitor_running = False

        self.root.title("Chrome AI Killer")
        self.root.geometry("950x720")
        self.root.state("zoomed")
        self.root.configure(bg=BG)

        self.create_widgets()

    # =====================================================

    def check_folders(self):

        self.write_log(
            "\n========== VERIFICANDO PASTAS ==========\n"
        )

        found = 0

        for folder in FOLDERS_TO_DELETE:

            try:

                # se virou pasta
                if os.path.isdir(folder):

                    self.write_log(
                        f"\n[PASTA IA DETECTADA]\n{folder}\n"
                    )

                    found += 1

                # se existe como arquivo bloqueado
                elif os.path.isfile(folder):

                    self.write_log(
                        f"\n[PROTEGIDO COM ARQUIVO BLOQUEADO]\n{folder}\n"
                    )

                # nao existe
                else:

                    self.write_log(
                        f"\n[NAO EXISTE]\n{folder}\n"
                    )

            except Exception as e:

                self.write_log(
                    f"\n[ERRO]\n{folder}\n{str(e)}\n"
                )

        self.write_log(
            "\n========== FIM VERIFICACAO ==========\n"
        )

        if found > 0:

            messagebox.showwarning(
                "IA DETECTADA",
                f"{found} pasta(s) IA encontrada(s)."
            )

        else:

            messagebox.showinfo(
                "TUDO PROTEGIDO",
                "Nenhuma pasta IA encontrada."
            )
    
    # =====================================================

    def create_widgets(self):

        title = tk.Label(
            self.root,
            text="GEMINI NANO KILLER",
            font=("Segoe UI", 22, "bold"),
            fg=BLUE,
            bg=BG
        )

        title.pack(pady=15)

        desc = tk.Label(
            self.root,
            text="Remove permanentemente IA do Google Chrome",
            font=("Segoe UI", 11),
            fg="#aaaaaa",
            bg=BG
        )

        desc.pack()

        # =================================================

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(pady=20)


        # =================================================

        btn5 = tk.Button(
            frame,
            text="VERIFICAR PASTAS IA",
            width=25,
            height=2,
            bg="#ffaa00",
            fg="black",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            command=self.check_folders
        )

        btn5.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        # =================================================

        btn1 = tk.Button(
            frame,
            text="REMOVER IA",
            width=25,
            height=2,
            bg="#00aa00",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            command=self.full_clean
        )

        btn1.grid(row=0, column=0, padx=10, pady=10)

        # =================================================

        btn2 = tk.Button(
            frame,
            text="ATIVAR MONITOR",
            width=25,
            height=2,
            bg="#0066cc",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            command=self.start_monitor
        )

        btn2.grid(row=0, column=1, padx=10, pady=10)

        # =================================================

        btn3 = tk.Button(
            frame,
            text="PARAR MONITOR",
            width=25,
            height=2,
            bg="#aa0000",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            command=self.stop_monitor
        )

        btn3.grid(row=1, column=0, padx=10, pady=10)

        # =================================================

        btn4 = tk.Button(
            frame,
            text="ABRIR chrome://policy",
            width=25,
            height=2,
            bg="#8844ff",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            command=self.open_policy
        )

        btn4.grid(row=1, column=1, padx=10, pady=10)

        # =================================================

        self.status = tk.Label(
            self.root,
            text="MONITOR: DESATIVADO",
            font=("Segoe UI", 10, "bold"),
            fg="#ff4444",
            bg=BG
        )

        self.status.pack(pady=5)

        # =================================================

        log_frame = tk.LabelFrame(
            self.root,
            text=" LOG ",
            fg=BLUE,
            bg=BG,
            font=("Segoe UI", 10, "bold")
        )

        log_frame.pack(fill="both", expand=True, padx=15, pady=15)

        self.log = scrolledtext.ScrolledText(
            log_frame,
            bg="#0d0d0d",
            fg=FG,
            font=("Consolas", 10)
        )

        self.log.pack(fill="both", expand=True)

        self.write_log("Programa iniciado.\n")

    # =====================================================

    def write_log(self, text):

        # vermelho para erros/deteccao
        if (
            "[ERRO]" in text or
            "[IA DETECTADA]" in text or
            "[PASTA IA DETECTADA]" in text
        ):

            self.log.insert(
                tk.END,
                text,
                "red"
            )

        # verde protegido
        elif (
            "[OK PROTEGIDO]" in text or
            "[BLOQUEADO" in text or
            "[RESTAURADO BLOQUEIO]" in text
        ):

            self.log.insert(
                tk.END,
                text,
                "green"
            )

        # amarelo verificacao
        elif (
            "[MONITOR VERIFICANDO IA...]" in text or
            "[ENCONTRADO]" in text
        ):

            self.log.insert(
                tk.END,
                text,
                "yellow"
            )

        # azul info
        else:

            self.log.insert(
                tk.END,
                text,
                "blue"
            )

        self.log.tag_config(
            "red",
            foreground="#ff4444"
        )

        self.log.tag_config(
            "green",
            foreground="#00ff88"
        )

        self.log.tag_config(
            "yellow",
            foreground="#ffaa00"
        )

        self.log.tag_config(
            "blue",
            foreground="#00ddff"
        )

        self.log.see(tk.END)

    # =====================================================

    def run_hidden(self, command):

        return subprocess.run(
            command,
            shell=True,
            creationflags=CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    # =====================================================

    def close_chrome(self):

        self.write_log("Fechando Google Chrome...\n")

        self.run_hidden("taskkill /F /IM chrome.exe")

    # =====================================================

    def apply_registry(self):

        self.write_log("\nAplicando bloqueios IA...\n\n")

        for command in REG_COMMANDS:

            try:

                result = self.run_hidden(command)

                if result.returncode == 0:

                    self.write_log(f"[OK] {command}\n")

                else:

                    self.write_log(f"[ERRO] {command}\n")

            except Exception as e:

                self.write_log(f"[ERRO] {str(e)}\n")

    # =====================================================

    def remove_folder(self, folder):

        try:

            if os.path.exists(folder):

                self.write_log(f"\n[ENCONTRADO]\n{folder}\n")

                self.run_hidden(
                    f'attrib -r -s -h "{folder}" /S /D'
                )

                # se for pasta
                if os.path.isdir(folder):

                    shutil.rmtree(
                        folder,
                        ignore_errors=True
                    )

                # se for arquivo
                else:

                    try:
                        os.remove(folder)
                    except:
                        pass

                time.sleep(1)

            # remove novamente caso ainda exista
            if os.path.exists(folder):

                try:

                    if os.path.isdir(folder):

                        shutil.rmtree(
                            folder,
                            ignore_errors=True
                        )

                    else:

                        os.remove(folder)

                except:
                    pass

            # cria arquivo falso
            with open(folder, "w") as f:
                f.write("BLOCKED")

            # protege arquivo
            self.run_hidden(
                f'attrib +r +s +h "{folder}"'
            )

            self.write_log(
                f"[BLOQUEADO DEFINITIVAMENTE]\n{folder}\n"
            )

        except Exception as e:

            self.write_log(
                f"[ERRO]\n{folder}\n{str(e)}\n"
            )

    # =====================================================

    def delete_ai_folders(self):

        self.write_log("\nRemovendo modelos IA...\n")

        for folder in FOLDERS_TO_DELETE:

            self.remove_folder(folder)

    # =====================================================

    def full_clean(self):

        if not self.is_admin():

            messagebox.showerror(
                "ADMIN",
                "Execute como ADMINISTRADOR"
            )

            return

        self.close_chrome()

        self.apply_registry()

        self.delete_ai_folders()

        self.write_log(
            "\nFINALIZADO COM SUCESSO.\n"
        )

        messagebox.showinfo(
            "FINALIZADO",
            "IA removida e bloqueada!"
        )

    # =====================================================

    def monitor_loop(self):

        while self.monitor_running:

            self.write_log(
                "\n[MONITOR VERIFICANDO IA...]\n"
            )

            for folder in FOLDERS_TO_DELETE:

                try:

                    # virou pasta novamente
                    if os.path.isdir(folder):

                        self.write_log(
                            f"\n[IA DETECTADA]\n{folder}\n"
                        )

                        self.run_hidden(
                            f'attrib -r -s -h "{folder}" /S /D'
                        )

                        shutil.rmtree(
                            folder,
                            ignore_errors=True
                        )

                        time.sleep(1)

                        with open(folder, "w") as f:
                            f.write("BLOCKED")

                        self.run_hidden(
                            f'attrib +r +s +h "{folder}"'
                        )

                        self.write_log(
                            f"[BLOQUEADO NOVAMENTE]\n{folder}\n"
                        )

                    # nao existe mais
                    elif not os.path.exists(folder):

                        with open(folder, "w") as f:
                            f.write("BLOCKED")

                        self.run_hidden(
                            f'attrib +r +s +h "{folder}"'
                        )

                        self.write_log(
                            f"[RESTAURADO BLOQUEIO]\n{folder}\n"
                        )

                    # protegido corretamente
                    else:

                        self.write_log(
                            f"\n[OK PROTEGIDO]\n{folder}\n"
                        )

                except Exception as e:

                    self.write_log(
                        f"[ERRO MONITOR]\n{folder}\n{str(e)}\n"
                    )

            time.sleep(5)

    # =====================================================

    def start_monitor(self):

        if not self.monitor_running:

            self.monitor_running = True

            threading.Thread(
                target=self.monitor_loop,
                daemon=True
            ).start()

            self.status.config(
                text="MONITOR: ATIVO",
                fg="#00ff88"
            )

            self.write_log(
                "\nMONITOR TEMPO REAL ATIVADO\n"
            )

    # =====================================================

    def stop_monitor(self):

        self.monitor_running = False

        self.status.config(
            text="MONITOR: DESATIVADO",
            fg="#ff4444"
        )

        self.write_log(
            "\nMONITOR PARADO\n"
        )

    # =====================================================

    def open_policy(self):

        try:

            chrome_path = (
                r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            )

            if os.path.exists(chrome_path):

                subprocess.Popen(
                    [chrome_path, "chrome://policy"],
                    creationflags=CREATE_NO_WINDOW
                )

                self.write_log(
                    "\nchrome://policy aberto\n"
                )

        except Exception as e:

            self.write_log(
                f"\nERRO: {str(e)}\n"
            )

    # =====================================================

    def is_admin(self):

        try:

            return ctypes.windll.shell32.IsUserAnAdmin()

        except:

            return False

# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = ChromeAIDisabler(root)

    root.mainloop()
