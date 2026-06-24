import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
from datetime import datetime
import re

# ===================== CORES NEON =====================
CORES = {
    "bg": "#0a0a0a",
    "fg": "#00ff9d",
    "accent": "#00ffff",
    "purple": "#ff00ff",
    "red": "#ff0055",
    "entry_bg": "#1a1a1a"
}

USER_AGENT = "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53"

def aplicar_estilo_hacker():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background=CORES["bg"])
    style.configure("TLabel", background=CORES["bg"], foreground=CORES["fg"], font=("Consolas", 11, "bold"))
    style.configure("TButton", background=CORES["accent"], foreground="black", font=("Consolas", 12, "bold"))
    style.map("TButton", background=[("active", CORES["purple"])])

# ===================== EXTRAIR URLS =====================
def extrair_urls(texto):
    # Regex para pegar http/https + domínios
    padrao = r'https?://[^\s;,\'"\)]+'
    urls = re.findall(padrao, texto)
    # Remover duplicatas mantendo ordem
    urls_unicas = []
    for url in urls:
        if url not in urls_unicas:
            urls_unicas.append(url)
    return urls_unicas

# ===================== BUSCAR CABEÇALHOS =====================
def buscar_cabecalho():
    url = entrada_url.get().strip()
    if not url:
        messagebox.showerror("ERRO", "Digite uma URL.")
        return

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    try:
        headers = {"User-Agent": USER_AGENT}
        resposta = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        resultado.delete(1.0, tk.END)
        
        # Cabeçalho do scan
        resultado.insert(tk.END, "═" * 75 + "\n", "titulo")
        resultado.insert(tk.END, "          HEADER PROBE // ANONYMOUS HEADER ANALYZER\n", "titulo")
        resultado.insert(tk.END, "═" * 75 + "\n\n", "titulo")

        resultado.insert(tk.END, "URL FINAL\n\n", "secao")
        resultado.insert(tk.END, f"{resposta.url}\n\n", "destaque")
        resultado.insert(tk.END, f"STATUS CODE: {resposta.status_code}\n\n", "destaque")

        # Cabeçalhos normais
        resultado.insert(tk.END, "═" * 75 + "\n", "secao")
        resultado.insert(tk.END, "          CABEÇALHOS HTTP\n", "secao")
        resultado.insert(tk.END, "═" * 75 + "\n\n", "secao")

        for chave, valor in resposta.headers.items():
            resultado.insert(tk.END, f"{chave:<30}", "chave")
            resultado.insert(tk.END, f": {valor}\n", "valor")

        # ===================== EXTRAÇÃO DE URLS =====================
        todas_urls = []
        for valor in resposta.headers.values():
            todas_urls.extend(extrair_urls(str(valor)))

        if todas_urls:
            resultado.insert(tk.END, "\n" + "═" * 75 + "\n", "secao")
            resultado.insert(tk.END, f"          URL EXTRAÍDAS: {len(todas_urls)} Encontradas\n", "secao")
            resultado.insert(tk.END, "═" * 75 + "\n\n", "secao")

            for i, u in enumerate(todas_urls, 1):
                resultado.insert(tk.END, f"{i:>3}. ", "chave")
                resultado.insert(tk.END, f"{u}\n", "valor")

        # Salva para botão de salvar
        global ultimo_resultado
        ultimo_resultado = resultado.get(1.0, tk.END)

    except Exception as e:
        messagebox.showerror("FALHA", str(e))

# ===================== SALVAR =====================
def salvar_resultados():
    if 'ultimo_resultado' not in globals() or not ultimo_resultado.strip():
        messagebox.showwarning("Aviso", "Faça uma consulta primeiro!")
        return

    arquivo = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt")],
        initialfile=f"Resultado_headers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    
    if arquivo:
        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write("HEADER PROBE - RELATÓRIO\n")
                f.write("=" * 70 + "\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                f.write(ultimo_resultado)
            messagebox.showinfo("Sucesso", f"Salvo\n\n{arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

# ===================== INTERFACE =====================
janela = tk.Tk()
janela.title("HEADER PROBE // ANONYMOUS")
janela.geometry("1100x760")
janela.state('zoomed')
janela.configure(bg=CORES["bg"])

aplicar_estilo_hacker()

# Topo
frame_top = ttk.Frame(janela)
frame_top.pack(fill="x", padx=15, pady=12)
tk.Label(frame_top, text="HEADER PROBE // ANONYMOUS", font=("Consolas", 18, "bold"), fg=CORES["accent"], bg=CORES["bg"]).pack(side="left")

# URL
frame_url = ttk.Frame(janela)
frame_url.pack(fill="x", padx=15, pady=8)
tk.Label(frame_url, text="DIGITE A URL:", font=("Consolas", 12, "bold"), fg=CORES["fg"], bg=CORES["bg"]).pack(side="left")
entrada_url = ttk.Entry(frame_url, width=50, font=("Consolas", 11))
entrada_url.pack(side="left", padx=10)

btn_scan = ttk.Button(frame_url, text="EXECUTE SCAN", command=buscar_cabecalho)
btn_scan.pack(side="left", padx=5)
btn_salvar = ttk.Button(frame_url, text="SALVAR .TXT", command=salvar_resultados)
btn_salvar.pack(side="left", padx=5)

# Resultado
resultado = scrolledtext.ScrolledText(
    janela, wrap=tk.WORD, font=("Consolas", 10),
    bg="#0f0f0f", fg=CORES["fg"], insertbackground=CORES["accent"]
)
resultado.pack(fill="both", expand=True, padx=15, pady=10)

# Tags
resultado.tag_config("titulo", foreground=CORES["accent"], font=("Consolas", 12, "bold"))
resultado.tag_config("destaque", foreground=CORES["purple"], font=("Consolas", 11, "bold"))
resultado.tag_config("secao", foreground=CORES["accent"], font=("Consolas", 11, "bold"))
resultado.tag_config("chave", foreground=CORES["fg"])
resultado.tag_config("valor", foreground=CORES["accent"])

ultimo_resultado = ""
janela.mainloop()
