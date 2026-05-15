import os, re, json, pyperclip, winreg
from pathlib import Path
from packaging.version import Version
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog

MIN_SAFE_VERSION = "138.0.7204.96"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def format_size(size):
    for unit in ["Bytes", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.2f} {unit}" if unit != "Bytes" else f"{int(size)} Bytes"
        size /= 1024


def folder_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try: total += os.path.getsize(fp)
            except: pass
    return total


def chrome_version():
    regs = [r"SOFTWARE\Google\Chrome\BLBeacon",
            r"SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon"]

    for reg in regs:
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg)
            return winreg.QueryValueEx(k, "version")[0]
        except:
            pass
    return "Não encontrada"


def chrome_safe(v):
    try: return Version(v) >= Version(MIN_SAFE_VERSION)
    except: return False


def profiles():
    p = Path.home() / "AppData/Local/Google/Chrome/User Data"
    return [x for x in p.iterdir()
            if x.is_dir() and (x.name == "Default" or x.name.startswith("Profile"))]


def resolve_locale(base, key):
    langs = ["pt_BR", "pt_PT", "en", "en_US"]

    for lang in langs:
        msg = os.path.join(base, "_locales", lang, "messages.json")

        if os.path.exists(msg):
            try:
                with open(msg, encoding="utf-8") as f:
                    d = json.load(f)
                if key in d:
                    return d[key]["message"]
            except:
                pass

    return key


def ext_name(path):
    try:
        latest = os.path.join(path, sorted(os.listdir(path), reverse=True)[0])
        manifest = os.path.join(latest, "manifest.json")

        with open(manifest, encoding="utf-8") as f:
            data = json.load(f)

        name = data.get("name", "Sem Nome")

        if "__MSG_" in name:
            m = re.search(r"__MSG_(.*?)__", name)
            if m:
                return resolve_locale(latest, m.group(1))

        return name

    except:
        return "Desconhecida"


def scan_extensions():
    result = []

    for profile in profiles():
        ext_dir = profile / "Extensions"

        if not ext_dir.exists():
            continue

        for ext in ext_dir.iterdir():
            if ext.is_dir():
                result.append({
                    "profile": profile.name,
                    "id": ext.name,
                    "name": ext_name(str(ext)),
                    "size": format_size(folder_size(str(ext))),
                    "path": str(ext)
                })

    return result


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("🧩 Chrome Extension Scanner")
        self.geometry("1400x850")

        # MAXIMIZAR DE VERDADE
        self.after(100, lambda: self.state("zoomed"))

        self.extensions = []

        self.info = ctk.CTkLabel(self, text="Clique em 🔍 Escanear", font=("Segoe UI", 15))
        self.info.pack(pady=10)

        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=15, pady=10)

        self.search = ctk.StringVar()
        self.search.trace_add("write", lambda *_: self.filter())

        ctk.CTkEntry(top, textvariable=self.search,
                     placeholder_text="Buscar extensão...").pack(side="left", fill="x", expand=True, padx=8)

        ctk.CTkButton(top, text="🔍 Escanear",
                      command=self.scan).pack(side="left", padx=5)

        ctk.CTkButton(top, text="💾 SALVAR TXT",
                      command=self.save_txt).pack(side="left", padx=5)

        ctk.CTkButton(top, text="📋 Copiar ID",
                      command=self.copy_id).pack(side="left", padx=5)

        cols = ("Perfil", "ID", "Nome", "Tamanho", "Caminho")

        self.tree = ttk.Treeview(self, columns=cols, show="headings")

        for c in cols:
            self.tree.heading(c, text=c)

        self.tree.column("Perfil", width=80)
        self.tree.column("ID", width=250)
        self.tree.column("Nome", width=300)
        self.tree.column("Tamanho", width=120)
        self.tree.column("Caminho", width=700)

        self.tree.pack(fill="both", expand=True, padx=15, pady=15)
        self.tree.bind("<Double-1>", self.open_folder)

    def scan(self):
        self.info.configure(text="🔍 Escaneando extensões...")
        self.update()

        self.extensions = scan_extensions()
        self.filter()
        self.auto_save()

        v = chrome_version()
        status = "✅ Segura" if chrome_safe(v) else "⚠️ Atualize"

        self.info.configure(
            text=f"Chrome {v} | {status} | {len(self.extensions)} extensões"
        )

    def filter(self):
        text = self.search.get().lower()

        for i in self.tree.get_children():
            self.tree.delete(i)

        for e in self.extensions:
            if text in (e["name"] + e["id"]).lower():
                self.tree.insert("", "end", values=(
                    e["profile"], e["id"], e["name"],
                    e["size"], e["path"]
                ))

    def copy_id(self):
        s = self.tree.selection()
        if not s: return

        ext_id = self.tree.item(s[0])["values"][1]
        pyperclip.copy(ext_id)

        messagebox.showinfo("Copiado", ext_id)

    def open_folder(self, event):
        s = self.tree.selection()
        if s:
            os.startfile(self.tree.item(s[0])["values"][4])

    def auto_save(self):

        file_path = "chrome_extensions_resultado.txt"

        v = chrome_version()

        status = (
            "Atualizada e Segura"
            if chrome_safe(v)
            else "Desatualizada"
        )

        ext_path = str(
            Path.home()
            / "AppData"
            / "Local"
            / "Google"
            / "Chrome"
            / "User Data"
            / "Default"
            / "Extensions"
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                f"Versão do Chrome Detectada: {v}\n\n"
            )

            f.write(
                f"Versão mínima segura: "
                f"{MIN_SAFE_VERSION}\n\n"
            )

            if chrome_safe(v):
                f.write(
                    "✅ Sua versão está "
                    "atualizada e segura.\n\n"
                )
            else:
                f.write(
                    "⚠️ Sua versão NÃO "
                    "está segura.\n\n"
                )

            f.write(
                f"Caminho das Extensões: "
                f"{ext_path}\n\n"
            )

            f.write(
                "🔍 Verificando "
                "Extensões instaladas "
                "em Todos os Perfis\n\n"
            )

            for e in self.extensions:

                linha = (
                    f"[{e['profile']}] "
                    f"ID: {e['id']}  "
                    f"Nome: {e['name']}  "
                    f"Tamanho: {e['size']}\n\n"
                )

                f.write(linha)

            f.write(
                f"\n🔢 Total de "
                f"Extensões Encontradas: "
                f"{len(self.extensions)}\n"
            )

    def save_txt(self):

        file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("TXT", "*.txt")]
        )

        if not file:
            return

        v = chrome_version()

        status = (
            "Atualizada e Segura"
            if chrome_safe(v)
            else "Desatualizada"
        )

        ext_path = str(
            Path.home()
            / "AppData"
            / "Local"
            / "Google"
            / "Chrome"
            / "User Data"
            / "Default"
            / "Extensions"
        )

        with open(
            file,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                f"Versão do Chrome Detectada: {v}\n\n"
            )

            f.write(
                f"Versão mínima segura: "
                f"{MIN_SAFE_VERSION}\n\n"
            )

            if chrome_safe(v):
                f.write(
                    "✅ Sua versão está "
                    "atualizada e segura.\n\n"
                )
            else:
                f.write(
                    "⚠️ Sua versão NÃO "
                    "está segura.\n\n"
                )

            f.write(
                f"Caminho das Extensões: "
                f"{ext_path}\n\n"
            )

            f.write(
                "🔍 Verificando "
                "Extensões instaladas "
                "em Todos os Perfis\n\n"
            )

            for e in self.extensions:

                linha = (
                    f"[{e['profile']}] "
                    f"ID: {e['id']}  "
                    f"Nome: {e['name']}  "
                    f"Tamanho: {e['size']}\n\n"
                )

                f.write(linha)

            f.write(
                f"\n🔢 Total de "
                f"Extensões Encontradas: "
                f"{len(self.extensions)}\n"
            )

        messagebox.showinfo(
            "Sucesso",
            "TXT salvo completo!"
        )


if __name__ == "__main__":
    App().mainloop()
