import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import urllib.parse
import json
import hashlib
import threading
import webbrowser

# ── Paleta ────────────────────────────────────────────────────────────────────
BG       = "#0f1117"
CARD     = "#1a1d27"
BORDER   = "#2a2d3a"
ACCENT   = "#6c63ff"
ACCENT2  = "#a78bfa"
VERDE    = "#22c55e"
VERMELHO = "#ef4444"
AMARELO  = "#f59e0b"
BRANCO   = "#f1f5f9"
CINZA    = "#94a3b8"
FONT_MAIN = ("Segoe UI", 10)
FONT_BIG  = ("Segoe UI", 13, "bold")
FONT_H    = ("Segoe UI", 18, "bold")


# ── Verificação de senha (sem API key) ───────────────────────────────────────

def verificar_senha(senha: str):
    """k-Anonymity: só os 5 primeiros chars do hash SHA-1 são enviados."""
    sha1 = hashlib.sha1(senha.encode()).hexdigest().upper()
    pref, suf = sha1[:5], sha1[5:]
    url = f"https://api.pwnedpasswords.com/range/{pref}"
    req = urllib.request.Request(url, headers={"User-Agent": "VerificadorVazamento-GUI/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            for linha in r.read().decode().splitlines():
                h, c = linha.split(":")
                if h == suf:
                    return int(c), None
        return 0, None
    except Exception as ex:
        return None, f"Erro de conexão: {ex}"


# ── Widget helpers ────────────────────────────────────────────────────────────

def make_card(parent, **kw):
    return tk.Frame(parent, bg=CARD, highlightbackground=BORDER,
                    highlightthickness=1, **kw)

def lbl(parent, text, font=FONT_MAIN, fg=BRANCO, bg=CARD, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)


# ── App ───────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Verificador de Vazamentos Email e Senhas")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._build()
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _build(self):
        root = tk.Frame(self, bg=BG, padx=50, pady=36)
        root.pack(fill="both", expand=True)

        # ── Cabeçalho ─────────────────────────────────────────────────────────
        hdr = tk.Frame(root, bg=BG)
        hdr.pack(fill="x", pady=(0, 22))
        tk.Label(hdr, text="🔍", font=("Segoe UI", 30), bg=BG, fg=ACCENT2).pack(side="left", padx=(0,12))
        sub = tk.Frame(hdr, bg=BG)
        sub.pack(side="left")
        tk.Label(sub, text="Verificador de Vazamentos Email e Senhas", font=FONT_H,
                 bg=BG, fg=BRANCO).pack(anchor="w")
        tk.Label(sub, text="100% gratuito  •  sem cadastro  •  sem API key",
                 font=("Segoe UI", 9), bg=BG, fg=CINZA).pack(anchor="w")

        # ── Card Email ────────────────────────────────────────────────────────
        c1 = make_card(root, padx=18, pady=16)
        c1.pack(fill="x", pady=(0, 14))
        tk.Frame(c1, bg=ACCENT, width=3).pack(side="left", fill="y", padx=(0,14))
        b1 = tk.Frame(c1, bg=CARD)
        b1.pack(fill="both", expand=True)

        lbl(b1, "📧  Email", font=FONT_BIG).pack(anchor="w")
        lbl(b1, "Abre o HaveIBeenPwned no seu navegador — sem cadastro nem API key.",
            fg=CINZA, font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 10))

        row_e = tk.Frame(b1, bg=CARD)
        row_e.pack(fill="x")
        self.email_var = tk.StringVar()
        self.email_entry = tk.Entry(
            row_e, textvariable=self.email_var,
            font=FONT_MAIN, bg="#252836", fg=BRANCO,
            insertbackground=BRANCO, relief="flat",
            highlightbackground=BORDER, highlightthickness=1, width=40)
        self.email_entry.pack(side="left", ipady=8, padx=(0, 8))
        self.email_entry.bind("<Return>", lambda e: self._abrir_email())

        tk.Button(row_e, text="Abrir no navegador →",
                  font=("Segoe UI", 9, "bold"),
                  bg=ACCENT, fg=BRANCO, relief="flat",
                  activebackground=ACCENT2, cursor="hand2",
                  padx=14, pady=6,
                  command=self._abrir_email).pack(side="left")

        # info box
        info = tk.Frame(b1, bg="#1e2133", padx=12, pady=10)
        info.pack(fill="x", pady=(12, 0))
        lbl(info, "ℹ️  Como funciona:", font=("Segoe UI", 9, "bold"),
            bg="#1e2133").pack(anchor="w")
        lbl(info,
            "1. Digite seu email acima e clique no botão.\n"
            "2. O site HaveIBeenPwned abre com seu email já preenchido.\n"
            "3. Clique em 'pwned?' para ver os resultados na página.",
            font=("Segoe UI", 9), fg=CINZA, bg="#1e2133",
            justify="left").pack(anchor="w", pady=(4, 0))

        # ── Card Senha ────────────────────────────────────────────────────────
        c2 = make_card(root, padx=18, pady=16)
        c2.pack(fill="x", pady=(0, 14))
        tk.Frame(c2, bg=AMARELO, width=3).pack(side="left", fill="y", padx=(0,14))
        b2 = tk.Frame(c2, bg=CARD)
        b2.pack(fill="both", expand=True)

        lbl(b2, "🔑  Senha", font=FONT_BIG).pack(anchor="w")
        lbl(b2, "Verificação anônima via k-Anonymity — sua senha NUNCA sai do computador.",
            fg=CINZA, font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 10))

        row_s = tk.Frame(b2, bg=CARD)
        row_s.pack(fill="x")
        self.senha_var = tk.StringVar()
        self.senha_entry = tk.Entry(
            row_s, textvariable=self.senha_var,
            font=FONT_MAIN, bg="#252836", fg=BRANCO,
            show="●", insertbackground=BRANCO, relief="flat",
            highlightbackground=BORDER, highlightthickness=1, width=40)
        self.senha_entry.pack(side="left", ipady=8, padx=(0, 8))
        self.senha_entry.bind("<Return>", lambda e: self._verificar_senha())

        self._olho = False
        tk.Button(row_s, text="👁", font=("Segoe UI", 11),
                  bg="#252836", fg=CINZA, relief="flat",
                  cursor="hand2", padx=6,
                  command=self._toggle_senha).pack(side="left", padx=(0, 8))

        self.btn_senha = tk.Button(
            row_s, text="Verificar agora",
            font=("Segoe UI", 9, "bold"),
            bg=AMARELO, fg=BG, relief="flat",
            activebackground="#fbbf24", cursor="hand2",
            padx=14, pady=6,
            command=self._verificar_senha)
        self.btn_senha.pack(side="left")

        self.res_senha = tk.Frame(b2, bg=CARD)
        self.res_senha.pack(fill="x", pady=(12, 0))

        # ── Dicas ─────────────────────────────────────────────────────────────
        dicas = make_card(root, padx=18, pady=14)
        dicas.pack(fill="x", pady=(0, 14))
        tk.Frame(dicas, bg=VERDE, width=3).pack(side="left", fill="y", padx=(0,14))
        bd = tk.Frame(dicas, bg=CARD)
        bd.pack(fill="both", expand=True)
        lbl(bd, "💡  Boas práticas de segurança", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tips = [
            "• Use senhas únicas e longas para cada serviço",
            "• Ative autenticação em dois fatores (2FA) sempre que possível",
            "• Gerencie senhas com Bitwarden (gratuito) ou KeePass",
            "• Se um site vazar, troque a senha imediatamente",
        ]
        for t in tips:
            lbl(bd, t, font=("Segoe UI", 9), fg=CINZA).pack(anchor="w")

        # ── Rodapé ────────────────────────────────────────────────────────────
        rod = tk.Frame(root, bg=BG)
        rod.pack(fill="x", pady=(4, 0))
        lbl(rod, "🔒 Nenhum dado seu é armazenado ou transmitido (exceto 5 chars do hash da senha).",
            font=("Segoe UI", 8), fg=CINZA, bg=BG).pack(side="left")

    # ── Ações ─────────────────────────────────────────────────────────────────

    def _abrir_email(self):
        email = self.email_var.get().strip()
        if not email or "@" not in email:
            messagebox.showwarning("Atenção", "Digite um email válido.")
            return
        url = f"https://haveibeenpwned.com/account/{urllib.parse.quote(email)}"
        webbrowser.open(url)

    def _toggle_senha(self):
        self._olho = not self._olho
        self.senha_entry.config(show="" if self._olho else "●")

    def _clear(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    def _verificar_senha(self):
        senha = self.senha_var.get()
        if not senha:
            messagebox.showwarning("Atenção", "Digite uma senha.")
            return
        self.btn_senha.config(state="disabled")
        self._clear(self.res_senha)
        lbl(self.res_senha, "⏳ Verificando de forma anônima…",
            fg=CINZA).pack(anchor="w")
        threading.Thread(target=self._senha_worker, args=(senha,), daemon=True).start()

    def _senha_worker(self, senha):
        contagem, erro = verificar_senha(senha)
        self.after(0, self._senha_resultado, contagem, erro)

    def _senha_resultado(self, contagem, erro):
        self.btn_senha.config(state="normal")
        self._clear(self.res_senha)
        f = self.res_senha

        if erro:
            lbl(f, f"⚠ {erro}", fg=AMARELO).pack(anchor="w")
            return

        if contagem == 0:
            row = tk.Frame(f, bg=CARD)
            row.pack(fill="x")
            lbl(row, "✅", font=("Segoe UI", 18), fg=VERDE).pack(side="left", padx=(0,8))
            lbl(row, "Senha não encontrada em nenhum vazamento!",
                font=("Segoe UI", 10, "bold"), fg=VERDE).pack(side="left")
        else:
            row = tk.Frame(f, bg=CARD)
            row.pack(fill="x")
            lbl(row, "🚨", font=("Segoe UI", 18), fg=VERMELHO).pack(side="left", padx=(0,8))
            lbl(row, f"Senha vazada {contagem:,}× — TROQUE IMEDIATAMENTE!",
                font=("Segoe UI", 10, "bold"), fg=VERMELHO,
                wraplength=440, justify="left").pack(side="left")
            lbl(f, "Nunca reutilize senhas. Use um gerenciador como o Bitwarden.",
                font=("Segoe UI", 9), fg=AMARELO).pack(anchor="w", pady=(6, 0))


if __name__ == "__main__":
    app = App()
    app.mainloop()
