import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import subprocess

# Preferências para desativar a IA do Firefox
AI_PREFS = {
    # Booleanas (false)
    "browser.ml.enable": False,
    "browser.ml.chat.enabled": False,
    "browser.ml.chat.sidebar": False,
    "browser.ml.chat.menu": False,
    "browser.ml.chat.page": False,
    "browser.ml.chat.shortcuts": False,
    "browser.ml.chat.page.footerBadge": False,
    "browser.ml.chat.page.menuBadge": False,
    "browser.ml.linkPreview.enabled": False,
    "browser.ml.pageAssist.enabled": False,
    "browser.ml.smartAssist.enabled": False,
    "extensions.ml.enabled": False,
    "browser.tabs.groups.smart.enabled": False,
    "browser.tabs.groups.smart.userEnabled": False,
    "browser.search.visualSearch.featureGate": False,
    "browser.urlbar.quicksuggest.mlEnabled": False,
    "pdfjs.enableAltText": False,
    "pdfjs.enableAltTextModelDownload": False,
    "pdfjs.enableGuessAltText": False,
    "places.semanticHistory.featureGate": False,
    
    # Strings (blocked)
    "browser.ai.control.default": "blocked",
    "browser.ai.control.sidebarChatbot": "blocked",
    "browser.ai.control.linkPreviewKeyPoints": "blocked",
    "browser.ai.control.smartTabGroups": "blocked",
    "browser.ai.control.translations": "blocked",
    "browser.ai.control.pdfjsAltText": "blocked",
}

def encontrar_perfil_firefox():
    """Encontra o perfil padrão do Firefox no Windows"""
    appdata = Path(os.environ.get("APPDATA", ""))
    firefox_dir = appdata / "Mozilla" / "Firefox"
    
    if not firefox_dir.exists():
        return None, "Pasta do Firefox não encontrada em AppData."
    
    profiles_ini = firefox_dir / "profiles.ini"
    profiles_dir = firefox_dir / "Profiles"
    
    default_path = None
    
    if profiles_ini.exists():
        try:
            with open(profiles_ini, "r", encoding="utf-8") as f:
                content = f.read()
            
            current_section = None
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("["):
                    current_section = line
                elif line.startswith("Path=") and current_section and "Profile" in current_section:
                    path_value = line.split("=", 1)[1].strip()
                    possible = profiles_dir / path_value
                    if possible.exists():
                        default_path = possible
                        break
                    possible = Path(path_value)
                    if possible.exists():
                        default_path = possible
                        break
        except Exception:
            pass
    
    # Fallback: perfil mais recente com "default" no nome
    if default_path is None and profiles_dir.exists():
        candidatos = list(profiles_dir.glob("*default*"))
        if not candidatos:
            candidatos = list(profiles_dir.glob("*"))
        if candidatos:
            default_path = max(candidatos, key=lambda p: p.stat().st_mtime)
    
    if default_path and default_path.exists():
        return default_path, None
    return None, "Nenhum perfil do Firefox encontrado."

def verificar_status_ia(perfil: Path):
    """Verifica se as preferências de IA estão desativadas"""
    user_js = perfil / "user.js"
    prefs_js = perfil / "prefs.js"
    
    encontrados = {}
    arquivos_para_ler = []
    
    if user_js.exists():
        arquivos_para_ler.append(user_js)
    if prefs_js.exists():
        arquivos_para_ler.append(prefs_js)
    
    for arquivo in arquivos_para_ler:
        try:
            with open(arquivo, "r", encoding="utf-8", errors="ignore") as f:
                conteudo = f.read()
                for pref, valor_esperado in AI_PREFS.items():
                    if f'user_pref("{pref}"' in conteudo:
                        if isinstance(valor_esperado, bool):
                            if f'user_pref("{pref}", false)' in conteudo or f'user_pref("{pref}",false)' in conteudo:
                                encontrados[pref] = False
                            elif f'user_pref("{pref}", true)' in conteudo or f'user_pref("{pref}",true)' in conteudo:
                                encontrados[pref] = True
                        else:
                            if f'user_pref("{pref}", "{valor_esperado}")' in conteudo:
                                encontrados[pref] = valor_esperado
        except Exception:
            continue
    
    desativadas = 0
    for pref, valor_esperado in AI_PREFS.items():
        if pref in encontrados and encontrados[pref] == valor_esperado:
            desativadas += 1
    
    return desativadas, len(AI_PREFS), encontrados

def criar_user_js(perfil: Path):
    """Cria ou atualiza o user.js e retorna o caminho do backup (se existir)"""
    user_js = perfil / "user.js"
    backup_path = None
    
    linhas = [
        "// ============================================",
        "// Desativação completa das funcionalidades de IA do Firefox",
        "// Gerado automaticamente pelo script",
        "// ============================================",
        ""
    ]
    
    for pref, valor in AI_PREFS.items():
        if isinstance(valor, bool):
            valor_str = "true" if valor else "false"
            linhas.append(f'user_pref("{pref}", {valor_str});')
        else:
            linhas.append(f'user_pref("{pref}", "{valor}");')
    
    linhas.append("")
    linhas.append("// Fim das preferências de IA")
    
    try:
        if user_js.exists():
            backup_path = perfil / "user.js.bak"
            # Se já existir um .bak antigo, sobrescreve
            if backup_path.exists():
                backup_path.unlink()
            user_js.rename(backup_path)
        
        with open(user_js, "w", encoding="utf-8") as f:
            f.write("\n".join(linhas))
        
        return True, None, backup_path
    except Exception as e:
        return False, str(e), None

def abrir_pasta(caminho: Path):
    """Abre a pasta no Explorador de Arquivos do Windows"""
    try:
        if caminho.is_file():
            subprocess.Popen(f'explorer /select,"{caminho}"')
        else:
            subprocess.Popen(f'explorer "{caminho}"')
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Remover IA do Firefox - Windows 10")
        self.root.geometry("680x580")
        self.root.resizable(True, True)
        
        self.perfil = None
        self.ultimo_backup = None
        
        self.criar_interface()
        self.verificar()
    
    def criar_interface(self):
        # Título
        titulo = ttk.Label(self.root, text="Desativar IA do Firefox", font=("Segoe UI", 16, "bold"))
        titulo.pack(pady=(12, 4))
        
        subtitulo = ttk.Label(self.root, text="Verifica e remove as funcionalidades de Inteligência Artificial do Firefox", 
                              font=("Segoe UI", 9))
        subtitulo.pack(pady=(0, 12))
        
        # Frame de status
        frame_status = ttk.LabelFrame(self.root, text="Status atual", padding=10)
        frame_status.pack(fill="x", padx=15, pady=5)
        
        self.label_perfil = ttk.Label(frame_status, text="Procurando perfil...", wraplength=620, cursor="hand2", foreground="#0066cc")
        self.label_perfil.pack(anchor="w")
        self.label_perfil.bind("<Button-1>", self.clicar_perfil)
        
        self.label_status = ttk.Label(frame_status, text="", font=("Segoe UI", 10, "bold"))
        self.label_status.pack(anchor="w", pady=(8, 0))
        
        self.label_backup = ttk.Label(frame_status, text="", wraplength=620, cursor="hand2", foreground="#0066cc")
        self.label_backup.pack(anchor="w", pady=(6, 0))
        self.label_backup.bind("<Button-1>", self.clicar_backup)
        
        # Área de detalhes
        frame_detalhes = ttk.LabelFrame(self.root, text="Detalhes", padding=5)
        frame_detalhes.pack(fill="both", expand=True, padx=15, pady=8)
        
        self.texto = scrolledtext.ScrolledText(frame_detalhes, height=13, font=("Consolas", 9), state="disabled")
        self.texto.pack(fill="both", expand=True)
        
        # Botões
        frame_botoes = ttk.Frame(self.root)
        frame_botoes.pack(fill="x", padx=15, pady=10)
        
        self.btn_verificar = ttk.Button(frame_botoes, text="Verificar novamente", command=self.verificar)
        self.btn_verificar.pack(side="left", padx=(0, 10))
        
        self.btn_remover = ttk.Button(frame_botoes, text="Desativar IA do Firefox", command=self.remover, state="disabled")
        self.btn_remover.pack(side="left")
        
        ttk.Button(frame_botoes, text="Sair", command=self.root.destroy).pack(side="right")
        
        # Aviso
        aviso = ttk.Label(self.root, 
                          text="⚠ Feche o Firefox completamente antes de desativar a IA.  |  Clique nos caminhos azuis para abrir a pasta",
                          foreground="#b36b00", font=("Segoe UI", 9))
        aviso.pack(pady=(0, 10))
    
    def clicar_perfil(self, event=None):
        if self.perfil and self.perfil.exists():
            abrir_pasta(self.perfil)
    
    def clicar_backup(self, event=None):
        if self.ultimo_backup and self.ultimo_backup.exists():
            abrir_pasta(self.ultimo_backup)
    
    def log(self, texto):
        self.texto.config(state="normal")
        self.texto.insert("end", texto + "\n")
        self.texto.see("end")
        self.texto.config(state="disabled")
    
    def limpar_log(self):
        self.texto.config(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.config(state="disabled")
    
    def verificar(self):
        self.limpar_log()
        self.btn_remover.config(state="disabled")
        self.label_backup.config(text="")
        self.ultimo_backup = None
        
        self.log("Procurando instalação do Firefox...")
        perfil, erro = encontrar_perfil_firefox()
        
        if erro:
            self.label_perfil.config(text=f"Erro: {erro}", foreground="red", cursor="")
            self.label_status.config(text="Firefox não encontrado ou perfil não localizado", foreground="red")
            self.log(f"ERRO: {erro}")
            return
        
        self.perfil = perfil
        self.label_perfil.config(text=f"Perfil encontrado (clique para abrir):\n{perfil}", foreground="#0066cc", cursor="hand2")
        self.log(f"Perfil localizado: {perfil}")
        
        # Verifica se existe backup
        backup = perfil / "user.js.bak"
        if backup.exists():
            self.ultimo_backup = backup
            self.label_backup.config(text=f"Backup encontrado (clique para abrir):\n{backup}")
            self.log(f"Backup existente: {backup}")
        
        desativadas, total, encontrados = verificar_status_ia(perfil)
        
        self.log(f"\nPreferências de IA verificadas: {desativadas}/{total} já estão desativadas.")
        
        if desativadas == total:
            self.label_status.config(text="✓ IA já está desativada neste perfil", foreground="green")
            self.log("\nTodas as principais preferências de IA já estão configuradas como desativadas.")
            self.btn_remover.config(state="disabled")
        else:
            self.label_status.config(text=f"⚠ IA ainda ativa ({desativadas}/{total} desativadas)", foreground="#b36b00")
            self.log("\nAlgumas (ou todas) as funcionalidades de IA ainda estão ativas.")
            self.log("Clique em 'Desativar IA do Firefox' para aplicar as configurações.")
            self.btn_remover.config(state="normal")
        
        self.log("\n--- Preferências principais ---")
        importantes = [
            "browser.ml.enable",
            "browser.ml.chat.enabled",
            "browser.ai.control.default",
            "browser.ml.chat.sidebar",
            "extensions.ml.enabled"
        ]
        for p in importantes:
            status = encontrados.get(p, "não definido / padrão do Firefox")
            self.log(f"  {p}: {status}")
    
    def remover(self):
        if not self.perfil:
            messagebox.showerror("Erro", "Nenhum perfil válido encontrado.")
            return
        
        resposta = messagebox.askyesno(
            "Confirmar desativação",
            "Deseja realmente desativar todas as funcionalidades de IA do Firefox?\n\n"
            "Isso irá criar/atualizar o arquivo user.js no perfil do Firefox.\n"
            "Um backup do user.js antigo (se existir) será feito automaticamente.\n\n"
            "IMPORTANTE: Feche o Firefox completamente antes de continuar."
        )
        
        if not resposta:
            return
        
        self.log("\nAplicando configurações...")
        sucesso, erro, backup_path = criar_user_js(self.perfil)
        
        if sucesso:
            self.log("✓ Arquivo user.js criado/atualizado com sucesso!")
            
            if backup_path:
                self.ultimo_backup = backup_path
                self.label_backup.config(text=f"Backup criado (clique para abrir):\n{backup_path}")
                self.log(f"Backup salvo em: {backup_path}")
            else:
                self.log("Nenhum user.js antigo existia (não foi necessário backup).")
            
            self.log("\nReinicie o Firefox para que as mudanças tenham efeito.")
            
            msg = "As preferências de IA foram desativadas com sucesso!\n\n"
            if backup_path:
                msg += f"Backup salvo em:\n{backup_path}\n\n"
            msg += "Feche e abra o Firefox novamente para aplicar as mudanças."
            
            messagebox.showinfo("Sucesso", msg)
            self.verificar()
        else:
            self.log(f"ERRO ao criar user.js: {erro}")
            messagebox.showerror("Erro", f"Não foi possível criar o arquivo:\n{erro}")

if __name__ == "__main__":
    if sys.platform != "win32":
        print("Este script foi feito para Windows.")
        sys.exit(1)
    
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    
    app = App(root)
    root.mainloop()
