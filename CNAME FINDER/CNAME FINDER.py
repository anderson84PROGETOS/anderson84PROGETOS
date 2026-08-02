import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import dns.resolver
import threading
import datetime
import re
import platform
import html as html_lib
import webbrowser
import os

# ================= TEMA =================
BG          = "#050505"          # fundo geral
VERDE       = "#00FF00"          # verde padrão
VERDE_FORTE = "#33FF66"          # verde do [LIVE] / destaques
VERDE_ESCURO= "#003300"
VERDE_OPACO = "#006600"
ABOBORA     = "#FF8C00"          # laranja abóbora do CNAME
AZUL        = "#0CD5F8"          # azul botão wordlist
VERMELHO    = "#FF7E33"          # vermelho botão salvar
FONTE       = ("Consolas", 11)
FONTE_TITLE = ("Consolas", 16, "bold")

# ============ RESOLUÇÃO DNS ============
def resolver_ip(host):
    try:
        for resp in dns.resolver.resolve(host, 'A', lifetime=10):
            return resp.to_text()
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return None
    except dns.exception.DNSException:
        return None

def obter_cname(host):
    try:
        for resp in dns.resolver.resolve(host, 'CNAME', lifetime=10):
            return resp.to_text().rstrip('.')
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return None
    except dns.exception.DNSException:
        return None

def verificar_subdominio(subdominio, resultados, resultados_detalhados):
    """
    Resolve A + CNAME e retorna uma lista de (texto, tag)
    para inserção colorida na GUI. None = subdomínio inexistente.
    Também guarda dados estruturados para o relatório HTML.
    """
    ip = resolver_ip(subdominio)
    if ip is None:
        return None

    cname = obter_cname(subdominio)
    ip_cname = None
    if cname:
        ip_cname = resolver_ip(cname)

    # ---- dados estruturados (usados no relatório HTML) ----
    resultados_detalhados.append({
        "host": subdominio,
        "ip": ip,
        "cname": cname,
        "ip_cname": ip_cname,
    })

    partes = [
        ("[LIVE] ", "live"),                          # verde forte
        (f"{subdominio:<75} -> {ip}", None),          # cor padrão (verde)
    ]
    texto_plano = f"[LIVE] {subdominio:<75} -> {ip}"

    if cname:
        destino = cname if not ip_cname else f"{cname:<75} -> {ip_cname}"
        partes.append((f"\n\nCNAME: {destino}", "cname"))   # laranja abóbora
        texto_plano += f"\n\nCNAME: {destino}"

    resultados.append(texto_plano)  # versão sem tags (para console/terminal)
    return partes

# ============ VARREDURA (THREAD) ============
def inserir_resultado(partes):
    """Insere o resultado aplicando as tags de cor."""
    for texto, tag in partes:
        if tag:
            resultados_text.insert(tk.END, texto, tag)
        else:
            resultados_text.insert(tk.END, texto)
    resultados_text.insert(tk.END, "\n\n")

def varredura(subdominios, site, resultados, resultados_detalhados, status_var, progress_var):
    total = len(subdominios)
    encontrados = 0

    for idx, sub in enumerate(subdominios):
        subdominio = f"{sub}.{site}"
        root.after(0, lambda s=subdominio: status_var.set(f"[*] Verificando: {s}"))
        root.after(0, lambda v=(idx + 1) / total * 100: progress_var.set(v))

        partes = verificar_subdominio(subdominio, resultados, resultados_detalhados)
        if partes:
            encontrados += 1
            root.after(0, lambda p=partes: inserir_resultado(p))  # tempo real + thread-safe

    root.after(0, lambda: status_var.set(
        f"[+] Varredura concluída: {encontrados} Subdomínios Ativos de {total} Testados"
    ))

# ============ AÇÕES DA INTERFACE ============
def escolher_wordlist():
    caminho = filedialog.askopenfilename(
        title="Selecionar wordlist",
        filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
    )
    if not caminho:
        return
    try:
        with open(caminho, 'r', encoding='utf-8', errors='ignore') as f:
            subs = sorted({l.strip() for l in f if l.strip()})
        if subs:
            wordlist_data.clear()
            wordlist_data.extend(subs)
            status_var.set(f"[+] Wordlist carregada: {len(subs)} subdomínios")
            messagebox.showinfo("Wordlist", f"{len(subs)} subdomínios carregados.")
        else:
            messagebox.showerror("Erro", "Wordlist vazia.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao ler arquivo:\n{e}")

def iniciar_varredura():
    site = site_entry.get().strip().lower().replace("http://", "").replace("https://", "").replace("/", "")
    if not site:
        messagebox.showerror("Erro", "Digite o nome do website (ex: exemplo.com).")
        return
    if not wordlist_data:
        messagebox.showerror("Erro", "Carregue uma wordlist primeiro.")
        return

    resultados_text.delete("1.0", tk.END)
    resultados_text.insert(tk.END, f"{'='*60}\nTARGET: {site}\nTotal: {len(wordlist_data)} subdomínios\n{'='*60}\n\n")
    progress_var.set(0)
    resultados.clear()
    resultados_detalhados.clear()

    threading.Thread(
        target=varredura,
        args=(wordlist_data, site, resultados, resultados_detalhados, status_var, progress_var),
        daemon=True
    ).start()

# ================= RELATÓRIO HTML =================
CSS = """
*{
    margin:0;
    padding:0;
    box-sizing:border-box;
}

html,body{
    width:100%;
    height:100%;
}

body{
    background:#050505 radial-gradient(circle at top, rgba(0,255,0,.08), transparent 70%);
    color:#00FF00;
    font-family:"Consolas","Courier New",monospace;
    padding:20px;
    overflow-x:auto;
}

.container{
    width:99%;
    max-width:none;
    margin:auto;
}

header{
    text-align:center;
    margin-bottom:30px;
}

header h1{
    font-size:38px;
    color:#33FF66;
    letter-spacing:3px;
    text-shadow:0 0 20px #00FF00;
    border-bottom:2px solid #00FF00;
    padding-bottom:15px;
}

header .sub{
    color:#00FFFF;
    margin-top:12px;
    font-size:18px;
}

header .sub b{
    color:#33FF66;
}

.stats{
    display:flex;
    justify-content:center;
    flex-wrap:wrap;
    gap:20px;
    margin-bottom:35px;
}

.card{
    background:#001900;
    border:1px solid #00FF00;
    border-radius:10px;
    padding:20px 35px;
    min-width:220px;
    text-align:center;
    box-shadow:0 0 15px rgba(0,255,0,.20);
}

.numero{
    font-size:40px;
    font-weight:bold;
    color:#33FF66;
}

.rotulo{
    margin-top:8px;
    color:#66FF66;
    text-transform:uppercase;
    font-size:15px;
}

.table-wrapper{
    width:100%;
    overflow-x:auto;
    border:1px solid #00FF00;
    border-radius:10px;
    box-shadow:0 0 20px rgba(0,255,0,.20);
}

table{
    width:100%;
    min-width:1250px;    
    border-collapse:collapse;
    background:#001400;
}

thead th{
    background:#003300;
    color:#33FF66;
    padding:16px;
    border:1px solid #00FF00;
    font-size:16px;
    text-transform:uppercase;
    letter-spacing:1px;
    white-space:nowrap;
}

tbody td{
    padding:14px 18px;
    border:1px solid #0a4b0a;
    font-size:15px;
    white-space:nowrap;
    word-break:normal;
}

tbody tr:nth-child(even){
    background:#001800;
}

tbody tr:hover{
    background:#003300;
}

.live{
    color:#00FF00;
    font-weight:bold;
}

.cname{
    color:#FFAA00;
    font-weight:bold;
}

.muted{
    color:#7ACC7A;
}

.com-cname{
    border-left:5px solid #FF9900;
}

footer{
    text-align:center;
    color:#66FF66;
    margin-top:35px;
    font-size:15px;
    line-height:1.8;
}

.tool{
    color:#00FFFF;
}
"""

def gerar_html(site, total, encontrados, com_cname, lista, data_hora):
    """Monta o relatório HTML completo (tema hacker)."""
    linhas = []
    for r in lista:
        host = html_lib.escape(r["host"])
        ip   = html_lib.escape(r["ip"])
        if r["cname"]:
            cname = html_lib.escape(r["cname"])
            if r["ip_cname"]:
                cname += f" <span class='muted'>({html_lib.escape(r['ip_cname'])})</span>"
            linhas.append(
                f"        <tr class='com-cname'>\n"
                f"            <td><span class='live'>[LIVE]</span> {host}</td>\n"
                f"            <td>{ip}</td>\n"
                f"            <td><span class='cname'>CNAME</span> {cname}</td>\n"
                f"        </tr>"
            )
        else:
            linhas.append(
                f"        <tr>\n"
                f"            <td><span class='live'>[LIVE]</span> {host}</td>\n"
                f"            <td>{ip}</td>\n"
                f"            <td class='muted'>— sem CNAME —</td>\n"
                f"        </tr>"
            )
    linhas_html = "\n".join(linhas)
    site = html_lib.escape(site)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Relatório DNS — {site}</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="container">

<header>
    <h1>[+] CNAME FINDER — Relatório de Subdomínios</h1>
    <div class="sub">TARGET: <b>{site}</b> &nbsp;•&nbsp; Gerado em: {data_hora}</div>
</header>

<div class="stats">
    <div class="card"><div class="numero">{total}</div><div class="rotulo">Subdomínios testados</div></div>
    <div class="card"><div class="numero">{encontrados}</div><div class="rotulo">Ativos [LIVE]</div></div>
    <div class="card"><div class="numero">{com_cname}</div><div class="rotulo">Com CNAME</div></div>
</div>

<table>
<thead>
    <tr>
        <th style="width:38%">Host</th> 
        <th style="width:22%">Endereço IP (A)</th>
        <th style="width:40%">CNAME / Destino</th>
    </tr>
</thead>
<tbody>
{linhas_html}
</tbody>
</table>

<footer>
    Relatório gerado automaticamente pela ferramenta <span class="tool">CNAME FINDER — Subdomain Enumerator</span><br>
    Uso autorizado exclusivamente em alvos dentro do escopo do teste.
</footer>

</div>
</body>
</html>"""



def salvar_resultados():
    if not resultados_detalhados:
        messagebox.showerror(
            "Erro",
            "Nenhum resultado para salvar. Execute a varredura primeiro."
        )
        return

    site = site_entry.get().strip() or "desconhecido"
    sufixo = re.sub(r'[^a-zA-Z0-9._-]', '_', site)

    nome = filedialog.asksaveasfilename(
        title="Salvar relatório HTML",
        defaultextension=".html",
        initialfile=f"relatorio_{sufixo}.html",
        filetypes=[
            ("Arquivo HTML", "*.html"),
            ("Todos os arquivos", "*.*")
        ]
    )

    if not nome:
        return

    # Corrige extensão antiga
    if nome.lower().endswith(".txt"):
        nome = nome[:-4] + ".html"

    total = len(wordlist_data)
    encontrados = len(resultados_detalhados)
    com_cname = sum(1 for r in resultados_detalhados if r["cname"])
    lista = sorted(resultados_detalhados, key=lambda r: r["host"].lower())
    data_hora = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

    html_final = gerar_html(
        site,
        total,
        encontrados,
        com_cname,
        lista,
        data_hora
    )

    try:
        with open(nome, "w", encoding="utf-8") as f:
            f.write(html_final)

        # Pergunta se deseja abrir
        resposta = messagebox.askyesno(
            "Relatório salvo",
            f"Relatório HTML salvo com sucesso!\n\n"
            f"{nome}\n\n"
            "Deseja abrir o relatório agora ?"
        )

        if resposta:
            webbrowser.open("file://" + os.path.abspath(nome))

    except Exception as e:
        messagebox.showerror(
            "Erro",
            f"Falha ao salvar:\n{e}"
        )

# ============ INTERFACE GRÁFICA ============
root = tk.Tk()
root.title("CNAME FINDER")
root.configure(bg=BG)

if platform.system() == "Windows":
    root.state("zoomed")          # maximiza no Windows
else:
    try:
        root.attributes("-zoomed", True)   # tenta maximizar no Linux (Kali)
    except tk.TclError:
        root.geometry("1366x768")          # fallback

wordlist_data = []
resultados = []
resultados_detalhados = []       # dados estruturados para o relatório HTML
progress_var = tk.DoubleVar()
status_var = tk.StringVar(value="[>] Aguardando comando...")

# --- Banner ---
banner = tk.Label(
    root,
    text=r"""
 ██████╗███╗   ██╗ █████╗ ███╗   ███╗███████╗    ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗
██╔════╝████╗  ██║██╔══██╗████╗ ████║██╔════╝    ██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
██║     ██╔██╗ ██║███████║██╔████╔██║█████╗      █████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
██║     ██║╚██╗██║██╔══██║██║╚██╔╝██║██╔══╝      ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
╚██████╗██║ ╚████║██║  ██║██║ ╚═╝ ██║███████╗    ██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
 ╚═════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝    ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
""",
    bg=BG,
    fg=VERDE,
    font=("Courier New", 9, "bold"),
    justify="center"
)
banner.pack(pady=(10, 5))

# --- Alvo ---
frame_alvo = tk.Frame(root, bg=BG)
frame_alvo.pack(pady=5)
tk.Label(frame_alvo, text="[TARGET] Digite o domínio:", bg=BG, fg=VERDE_FORTE, font=FONTE).pack(side=tk.LEFT, padx=5)
site_entry = tk.Entry(
    frame_alvo, width=35, font=FONTE,
    bg=VERDE_ESCURO, fg=VERDE, insertbackground=VERDE,
    relief=tk.FLAT, highlightthickness=1, highlightbackground=VERDE, highlightcolor=VERDE
)
site_entry.pack(side=tk.LEFT, padx=5)

# --- Botões ---
frame_btn = tk.Frame(root, bg=BG)
frame_btn.pack(pady=8)

def criar_botao(master, texto, comando, cor=VERDE):
    return tk.Button(
        master, text=texto, command=comando, font=("Consolas", 11, "bold"),
        bg=BG, fg=cor, activebackground=VERDE_OPACO, activeforeground=BG,
        relief=tk.GROOVE, bd=2, padx=15, pady=4, cursor="hand2"
    )

criar_botao(frame_btn, "[1] INICIAR VARREDURA", iniciar_varredura, cor=VERDE).pack(side=tk.LEFT, padx=8)
criar_botao(frame_btn, "[2] CARREGAR WORDLIST", escolher_wordlist, cor=AZUL).pack(side=tk.LEFT, padx=8)
criar_botao(frame_btn, "[3] SALVAR RESULTADOS", salvar_resultados, cor=VERMELHO).pack(side=tk.LEFT, padx=8)

# --- Barra de progresso ---
style = ttk.Style()
try:
    style.theme_use("clam")
except tk.TclError:
    pass
style.configure(
    "Hacker.Horizontal.TProgressbar",
    background=VERDE, troughcolor=VERDE_ESCURO,
    bordercolor=VERDE, lightcolor=VERDE, darkcolor=VERDE
)
progress_bar = ttk.Progressbar(
    root, style="Hacker.Horizontal.TProgressbar",
    orient="horizontal", length=900, mode="determinate", variable=progress_var
)
progress_bar.pack(pady=(5, 0), padx=10)

status_label = tk.Label(root, textvariable=status_var, bg=BG, fg="#66FF66", font=("Consolas", 10, "italic"))
status_label.pack(pady=(2, 4))

# --- Área de resultados ---
frame_texto = tk.Frame(root, bg=BG)
frame_texto.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

scrollbar = tk.Scrollbar(frame_texto, bg=VERDE_ESCURO, activebackground=VERDE, troughcolor=BG)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

resultados_text = tk.Text(
    frame_texto, font=FONTE, wrap=tk.NONE,
    bg=BG, fg=VERDE, insertbackground=VERDE,
    selectbackground=VERDE, selectforeground=BG,
    relief=tk.FLAT, highlightthickness=1, highlightbackground=VERDE,
    yscrollcommand=scrollbar.set
)
resultados_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=resultados_text.yview)

# ---------- TAGS DE COR (aplicadas por trecho) ----------
resultados_text.tag_configure("live",  foreground=VERDE_FORTE, font=("Consolas", 11, "bold"))
resultados_text.tag_configure("cname", foreground=ABOBORA,     font=("Consolas", 11, "bold"))

root.mainloop()
