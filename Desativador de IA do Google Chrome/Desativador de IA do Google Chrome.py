import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import ctypes
import os
import shutil
import winreg

# ====================== REG_COMMANDS ======================
REG_COMMANDS = [
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /f',
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v AIModeSettings /t REG_DWORD /d 2 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v GeminiSettings /t REG_DWORD /d 1 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v HelpMeWriteSettings /t REG_DWORD /d 2 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v CreateThemesSettings /t REG_DWORD /d 2 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v HistorySearchSettings /t REG_DWORD /d 2 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v TabCompareSettings /t REG_DWORD /d 2 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v AutofillPredictionSettings /t REG_DWORD /d 2 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v DevToolsGenAiSettings /t REG_DWORD /d 2 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v SearchContentSharingSettings /t REG_DWORD /d 1 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v TabOrganizerSettings /t REG_DWORD /d 2 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v GeminiActOnWebSettings /t REG_DWORD /d 1 /f',
    r'reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v GenAILocalFoundationalModelSettings /t REG_DWORD /d 1 /f'
]

FOLDERS_TO_DELETE = [
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\OptGuideOnDeviceModel"),
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\optimization_guide_model_store"),
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\OnDeviceHeadSuggestModel")
]

# ====================== POLÍTICAS ADICIONAIS ======================
CHROME_POLICY = r"SOFTWARE\Policies\Google\Chrome"

POLICIES = {
    "BrowserLabsEnabled": 0,
    "AIPromptsEnabled": 0,
    "SearchSuggestEnabled": 0,
    "BackgroundModeEnabled": 0,
    "ChromeLabsEnabled": 0,
    "GenAiDefaultSettings": 2,
}

FLAGS_DISABLE = [
    "OptimizationGuideModelDownloading", "OptimizationHints", "Compose", "TabOrganizer",
    "Glic", "GlicActor", "GlicSettings", "HistorySearch", "AiSettingsPageRefresh",
    "HelpMeWrite", "PromptApiForGeminiNano", "SummarizationApiForGeminiNano",
    "WriterApiForGeminiNano", "Proofreader", "TabSearch", "ReadAnythingWithScreen2x",
    "DesktopPWAsTabStrip"
]

class ChromeAIDisabler:
    def __init__(self, root):
        self.root = root
        self.root.title("Desativador de IA do Google Chrome")
        self.root.geometry("900x720")
        self.root.resizable(True, True)
        self.root.configure(bg="#1e1e1e")

        try:
            self.root.iconbitmap("chrome.ico")
        except:
            pass

        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(self.root, text="Desativador de IA do Google Chrome",
                         font=("Segoe UI", 20, "bold"), fg="#00ddff", bg="#1e1e1e")
        title.pack(pady=15)

        desc = tk.Label(self.root, text="Aplique políticas para desativar recursos de Inteligência Artificial do Google Chrome.",
                        font=("Segoe UI", 11), fg="#aaaaaa", bg="#1e1e1e", wraplength=800)
        desc.pack(pady=(0, 20))

        btn_frame = tk.Frame(self.root, bg="#1e1e1e")
        btn_frame.pack(pady=10)

        apply_btn = tk.Button(btn_frame, text="Aplicar Bloqueios de IA", font=("Segoe UI", 10, "bold"),
                              width=28, height=2, bg="#00aa00", fg="white", activebackground="#00cc00",
                              relief="raised", command=self.apply_registry)
        apply_btn.grid(row=0, column=0, padx=12, pady=8)

        remove_btn = tk.Button(btn_frame, text="Apagar Modelos de IA", font=("Segoe UI", 10, "bold"),
                               width=28, height=2, bg="#f2ae38", fg="black", activebackground="#ff6600",
                               relief="raised", command=self.delete_ai_folders)
        remove_btn.grid(row=0, column=1, padx=12, pady=8)

        close_chrome_btn = tk.Button(btn_frame, text="Fechar Google Chrome", font=("Segoe UI", 10, "bold"),
                                     width=28, height=2, bg="#aa0000", fg="white", activebackground="#dd0000",
                                     relief="raised", command=self.close_chrome)
        close_chrome_btn.grid(row=1, column=0, padx=12, pady=8)

        policy_btn = tk.Button(btn_frame, text="Abrir chrome://policy", font=("Segoe UI", 10, "bold"),
                               width=28, height=2, bg="#0066cc", fg="white", activebackground="#0088ff",
                               relief="raised", command=self.open_policy_page)
        policy_btn.grid(row=1, column=1, padx=12, pady=8)

        # Botão principal
        full_disable_btn = tk.Button(btn_frame, text="DESLIGAR TODA IA DO Chrome", 
                                     font=("Segoe UI", 11, "bold"), width=58, height=2,
                                     bg="#00aa55", fg="white", activebackground="#00cc66",
                                     relief="raised", command=self.desligar_ia_completo)
        full_disable_btn.grid(row=2, column=0, columnspan=2, padx=12, pady=12)

        log_frame = tk.LabelFrame(self.root, text=" Log de Execução ", 
                                  font=("Segoe UI", 10, "bold"), fg="#00ddff", bg="#1e1e1e")
        log_frame.pack(fill="both", expand=True, padx=20, pady=15)

        self.log = scrolledtext.ScrolledText(log_frame, font=("Consolas", 10),
                                             bg="#0d0d0d", fg="#00ff88", height=18)
        self.log.pack(fill="both", expand=True, padx=8, pady=8)

        self.write_log("✅ Programa iniciado com sucesso.\n\n")
        self.write_log("Pronto para desativar os recursos de IA do Chrome.\n")

    def write_log(self, text):
        self.log.insert(tk.END, text)
        self.log.see(tk.END)

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def apply_registry(self):
        if not self.is_admin():
            messagebox.showerror("Permissão Necessária", "Execute este programa como Administrador.")
            return

        self.write_log("🔧 Aplicando políticas de registro\n\n")
        for command in REG_COMMANDS:
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    self.write_log(f"✅ [OK] {command.split('/v')[-1].strip()}\n")
                else:
                    self.write_log(f"❌ [ERRO] {command}\n")
            except Exception as e:
                self.write_log(f"❌ Erro: {str(e)}\n")

        messagebox.showinfo("Sucesso", "Políticas de bloqueio de IA aplicadas com sucesso!")

    def close_chrome(self):
        try:
            subprocess.run("taskkill /F /IM chrome.exe", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.write_log("\n🛑 Google Chrome fechado com sucesso.\n\n")
        except Exception as e:
            self.write_log(f"❌ Erro ao fechar Chrome: {e}\n")

    def delete_ai_folders(self):
        self.close_chrome()
        self.write_log("🗑️ Removendo pastas de modelos de IA\n\n")
        removed = 0
        for folder in FOLDERS_TO_DELETE:
            try:
                if os.path.exists(folder):
                    shutil.rmtree(folder, ignore_errors=True)
                    self.write_log(f"✅ Removido: {folder}\n")
                    removed += 1
                else:
                    self.write_log(f"ℹ️ Não encontrado: {folder}\n")
            except Exception as e:
                self.write_log(f"❌ Erro ao remover {folder}: {e}\n")
        messagebox.showinfo("Concluído", f"{removed} pasta(s) de IA removida(s) com sucesso.")

    def open_policy_page(self):
        try:
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if os.path.exists(chrome_path):
                subprocess.Popen([chrome_path, "chrome://policy"], creationflags=subprocess.CREATE_NO_WINDOW)
                self.write_log("🌐 Página chrome://policy aberta.\n")
            else:
                messagebox.showwarning("Chrome não encontrado", "Não foi possível localizar o executável do Chrome.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def desligar_ia_completo(self):
        if not self.is_admin():
            messagebox.showerror("ERRO", "Execute o programa como ADMINISTRADOR")
            return

        self.write_log("===================================\n")
        self.write_log("DESATIVANDO TODA IA DO GOOGLE CHROME\n")
        self.write_log("===================================\n\n")

        # 1. Aplicar políticas do registro
        self.write_log("Aplicando políticas adicionais\n\n")
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, CHROME_POLICY)
            for nome, valor in POLICIES.items():
                winreg.SetValueEx(key, nome, 0, winreg.REG_DWORD, valor)
                self.write_log(f"[OK] Política aplicada: {nome}\n")
            winreg.CloseKey(key)
        except Exception as e:
            self.write_log(f"[ERRO] Falha ao aplicar políticas: {e}\n")

        # 2. Fechar Chrome
        self.close_chrome()

        self.write_log("\n===================================\n")
        self.write_log("IA DESATIVADA COM SUCESSO!\n")
        self.write_log("===================================\n")
        messagebox.showinfo("CONCLUÍDO", "Toda a IA do Google Chrome foi desativada com sucesso!")


if __name__ == "__main__":
    root = tk.Tk()
    app = ChromeAIDisabler(root)
    root.mainloop()
