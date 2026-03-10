import tkinter as tk
from tkinter import messagebox
import win32gui
import win32process
import win32con
import psutil
import os
import signal
import random

# =========================
# PALETA DE CORES
# =========================
APP_COLORS = [
    "#22c55e",  # verde
    "#3b82f6",  # azul
    "#f59e0b",  # laranja
    "#ef4444",  # vermelho
    "#a855f7",  # roxo
    "#14b8a6",  # teal
    "#eab308",  # amarelo
    "#f472b6",  # rosa
]

# =========================
# FILTRO DE JANELA REAL
# =========================
def is_real_window(hwnd):
    if not win32gui.IsWindowVisible(hwnd):
        return False

    title = win32gui.GetWindowText(hwnd)
    if not title.strip():
        return False

    if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
        return False

    exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if exstyle & win32con.WS_EX_TOOLWINDOW:
        return False

    return True


# =========================
# PEGAR APPS
# =========================
def get_visible_apps():
    apps = []

    def enum_handler(hwnd, _):
        if not is_real_window(hwnd):
            return

        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            exe = proc.name()
            title = win32gui.GetWindowText(hwnd)

            apps.append({
                "title": title,
                "pid": pid,
                "exe": exe
            })
        except:
            pass

    win32gui.EnumWindows(enum_handler, None)
    return apps


# =========================
# APP
# =========================
class AppKiller:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ Apps da Barra de Tarefas")
        self.root.geometry("900x600")
        self.root.configure(bg="#0f172a")

        self.apps = []

        title_lbl = tk.Label(
            root,
            text="Gerenciador de Apps",
            font=("Segoe UI", 16, "bold"),
            fg="#e5e7eb",
            bg="#0f172a"
        )
        title_lbl.pack(pady=(10, 5))

        frame = tk.Frame(root, bg="#0f172a")
        frame.pack(fill="both", expand=True, padx=12, pady=8)

        self.listbox = tk.Listbox(
            frame,
            font=("Segoe UI", 11),
            bg="#111827",
            fg="#e5e7eb",
            selectbackground="#2563eb",
            selectforeground="white",
            relief="flat",
            highlightthickness=0,
            activestyle="none"
        )
        self.listbox.pack(fill="both", expand=True, padx=4, pady=4)

        # duplo clique
        self.listbox.bind("<Double-Button-1>", self.kill_selected)

        btn_frame = tk.Frame(root, bg="#0f172a")
        btn_frame.pack(pady=8)

        btn_style = {
            "font": ("Segoe UI", 10, "bold"),
            "bd": 0,
            "padx": 12,
            "pady": 6,
            "cursor": "hand2"
        }

        tk.Button(
            btn_frame,
            text="🔄 Atualizar",
            bg="#1f2937",
            fg="white",
            activebackground="#374151",
            command=self.refresh,
            **btn_style
        ).pack(side="left", padx=6)

        tk.Button(
            btn_frame,
            text="❌ Finalizar",
            bg="#dc2626",
            fg="white",
            activebackground="#ef4444",
            command=self.kill_selected,
            **btn_style
        ).pack(side="left", padx=6)

        self.status_var = tk.StringVar()
        status_bar = tk.Label(
            root,
            textvariable=self.status_var,
            anchor="w",
            bg="#020617",
            fg="#9ca3af",
            font=("Segoe UI", 14, "bold")
        )
        status_bar.pack(fill="x", side="bottom")

        self.refresh()
        self.auto_refresh()

    # =========================
    # ATUALIZAR COM CORES
    # =========================
    def refresh(self):
        self.listbox.delete(0, tk.END)
        self.apps = get_visible_apps()

        color_index = 0

        for i, app in enumerate(self.apps):
            text = f"⚡ {app['title']} ({app['exe']}) - PID {app['pid']}"
            self.listbox.insert(tk.END, text)

            # 🔥 aplica cor ao item
            color = APP_COLORS[color_index % len(APP_COLORS)]
            self.listbox.itemconfig(tk.END, fg=color)
            color_index += 1

            # linha vazia
            if i < len(self.apps) - 1:
                self.listbox.insert(tk.END, "")

        self.status_var.set(f"{len(self.apps)}  Apps Abertos")

    # =========================
    # FINALIZAR
    # =========================
    def kill_selected(self, event=None):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um app")
            return

        index = sel[0]

        # ignora linha vazia
        if index % 2 == 1:
            return

        real_index = index // 2
        app = self.apps[real_index]

        try:
            os.kill(app["pid"], signal.SIGTERM)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # =========================
    # AUTO REFRESH
    # =========================
    def auto_refresh(self):
        self.refresh()
        self.root.after(5000, self.auto_refresh)


# =========================
# START
# =========================
if __name__ == "__main__":
    root = tk.Tk()
    app = AppKiller(root)
    root.mainloop()
