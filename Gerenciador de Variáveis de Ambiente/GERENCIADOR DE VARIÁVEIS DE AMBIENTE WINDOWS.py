import os
import ctypes
import threading
import winreg
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO

# ==================== CORES ====================
BG        = "#1e1e1e"
FG        = "#ffffff"
CINZA     = "#0ce6ee"
VERDE     = "#00ff88"
AMARELO   = "#ffcc00"
VERMELHO  = "#ff5555"
AZUL      = "#0078D7"
LARANJA   = "#e79b0d"

# ==================== ESTADO GLOBAL ====================
current_var = None          # nome da variável atual (ex: PATH)
current_entries = []        # lista de entradas da variável atual

# ==================== FUNÇÕES AUXILIARES ====================
def log(msg, tag="info"):
    console.insert(tk.END, msg + "\n", tag)
    console.see(tk.END)

def em_thread(fn):
    threading.Thread(target=fn, daemon=True).start()

def ler_var(nome):
    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
    try:
        try:
            v, _ = winreg.QueryValueEx(k, nome)
            return v
        except FileNotFoundError:
            return None
    finally:
        winreg.CloseKey(k)

def gravar_var(nome, valor):
    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(k, nome, 0, winreg.REG_EXPAND_SZ, valor)
    finally:
        winreg.CloseKey(k)
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0, 5000, 0)

def listar_vars():
    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
    out, i = [], 0
    while True:
        try:
            n, v, _ = winreg.EnumValue(k, i)
            out.append((n, v))
            i += 1
        except OSError:
            break
    winreg.CloseKey(k)
    return out

def nome_var():
    n = combo.get().strip()
    if n == "Personalizada":
        n = entry_nome.get().strip()
    if not n:
        raise ValueError("Escolha o nome da variável.")
    return n.upper()

def caminho_alvo():
    p = var_prog.get().strip()
    if not p:
        raise ValueError("Escolha um programa ou pasta primeiro.")
    if not os.path.exists(p):
        raise ValueError("Caminho não encontrado.")
    
    if modo.get() == "pasta":
        return os.path.dirname(p) if os.path.isfile(p) else p
    else:
        return p

def extrair_caminho_da_linha(texto):
    """Extrai o caminho de uma linha do tipo '  11. C:\\pasta\\arquivo'"""
    texto = texto.strip()
    if not texto:
        return None
    # Remove o número da frente (ex: "11. " ou "  3. ")
    if ". " in texto:
        partes = texto.split(". ", 1)
        if len(partes) == 2 and partes[0].strip().isdigit():
            return partes[1].strip()
    return texto.strip()

def obter_selecao_console():
    """Retorna o caminho selecionado no console (se houver)"""
    try:
        if console.tag_ranges(tk.SEL):
            texto = console.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
            return extrair_caminho_da_linha(texto)
    except tk.TclError:
        pass
    return None

def abrir_local(caminho):
    """Abre a pasta no Explorer e seleciona o item"""
    if not caminho:
        return
    caminho = caminho.replace("/", "\\")
    try:
        if os.path.isfile(caminho):
            subprocess.run(["explorer", "/select,", caminho], check=False)
        elif os.path.isdir(caminho):
            os.startfile(caminho)
        else:
            # Tenta abrir a pasta pai
            pasta = os.path.dirname(caminho)
            if os.path.isdir(pasta):
                os.startfile(pasta)
            else:
                messagebox.showwarning("Aviso", f"Caminho não encontrado:\n{caminho}")
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir:\n{e}")

# ==================== AÇÕES ====================
def escolher_prog():
    p = filedialog.askopenfilename(
        title="Escolha o programa",
        filetypes=[("Executáveis", "*.exe *.bat *.cmd *.com"), ("Todos", "*.*")]
    )
    if p:
        var_prog.set(p)
        log(f"[+] Programa selecionado: {p}", "ok")

def escolher_pasta():
    p = filedialog.askdirectory(title="Escolha a pasta para adicionar no PATH")
    if p:
        var_prog.set(p)
        modo.set("pasta")
        log(f"\n[+] Pasta selecionada: {p}", "ok")

def mostrar_var():
    def task():
        global current_var, current_entries
        try:
            nome = nome_var()
            valor = ler_var(nome)
            log(f"\n[+] Variável: {nome}", "ok")
            log("-" * 70)

            current_var = nome
            current_entries = []

            if valor is None:
                log(f"[-] {nome} ainda não existe.", "erro")
                result.config(text="Variável não existe", fg=AMARELO)
                return

            if ";" in valor or nome == "PATH":
                entradas = [p for p in valor.split(";") if p.strip()]
                current_entries = entradas
                for i, item in enumerate(entradas, 1):
                    log(f"  {i:2}. {item}")
                log(f"\n[OK] Total: {len(entradas)} Entradas", "ok")
                result.config(text=f"{nome} → {len(entradas)} Entradas", fg=VERDE)
            else:
                log(valor)
                current_entries = [valor]
                result.config(text=f"{nome} = {valor}", fg=VERDE)

        except Exception as e:
            log(f"[ERRO] {e}", "erro")
            result.config(text=str(e), fg=VERMELHO)

    em_thread(task)

def adicionar():
    def task():
        try:
            nome = nome_var()
            novo = caminho_alvo()
            atual = ler_var(nome)

            if anexar.get() and atual:
                partes = [p for p in atual.split(";") if p.strip()]
                if any(novo.lower() == p.lower() for p in partes):
                    log(f"[-] '{novo}' já está em {nome}.", "aviso")
                    result.config(text="Já existe no PATH", fg=AMARELO)
                    return
                partes.append(novo)
                novo_valor = ";".join(partes)
            else:
                novo_valor = novo

            gravar_var(nome, novo_valor)
            log(f"\n[OK] {nome} atualizada com sucesso!", "ok")
            log(f"\nAdicionado: {novo}")
            result.config(text=f"{nome} atualizada", fg=VERDE)
            messagebox.showinfo("Sucesso", f"{nome} atualizada!\n\nReinicie o terminal/programa para aplicar.")

        except Exception as e:
            log(f"[ERRO] {e}", "erro")
            result.config(text=str(e), fg=VERMELHO)

    em_thread(task)

def remover_entrada(caminho_forcado=None, confirmar=True):
    def task():
        global current_entries
        try:
            nome = nome_var()
            
            # 1º tenta usar a seleção do console
            alvo = caminho_forcado or obter_selecao_console()
            
            # 2º se não tiver seleção, usa o caminho do programa/pasta escolhido
            if not alvo:
                alvo = caminho_alvo()

            # Confirmação antes de remover (mostra o nome/caminho)
            if confirmar:
                resposta = messagebox.askyesno(
                    "Confirmar remoção",
                    f"Deseja remover esta entrada de {nome}?\n\n"
                    f"{alvo}\n\n"
                    "Esta ação não pode ser desfeita facilmente."
                )
                if not resposta:
                    log(f"\n[-] Remoção cancelada pelo usuário.", "aviso")
                    return

            atual = ler_var(nome)

            if not atual:
                log(f"[-] {nome} está vazia ou não existe.", "aviso")
                return

            partes = [p for p in atual.split(";") if p.strip()]
            novas = [p for p in partes if p.lower() != alvo.lower()]

            if len(novas) == len(partes):
                log(f"[-] '{alvo}' não foi encontrado em {nome}.", "aviso")
                result.config(text="Entrada não encontrada", fg=AMARELO)
                return

            novo_valor = ";".join(novas)
            gravar_var(nome, novo_valor)
            
            # Atualiza a lista em memória
            current_entries = novas
            
            log(f"\n[OK] Removido de {nome}: {alvo}\n", "ok")
            result.config(text=f"\nRemovido de {nome}", fg=VERDE)
            messagebox.showinfo("Sucesso", f"Entrada removida de {nome}!\n\nReinicie o terminal para aplicar.")

        except Exception as e:
            log(f"[ERRO] {e}", "erro")
            result.config(text=str(e), fg=VERMELHO)

    em_thread(task)

def listar():
    def task():
        try:
            vars_ = listar_vars()
            log(f"\n[+] {len(vars_)} variáveis de ambiente do usuário", "ok")
            log("=" * 70)

            for nome, valor in sorted(vars_):
                log(f"\n■ {nome}", "ok")
                log("-" * 70)

                if ";" in valor:
                    itens = [i.strip() for i in valor.split(";") if i.strip()]
                    for i, item in enumerate(itens, 1):
                        log(f"  {i:2}. {item}")
                    log(f"\n[OK] {len(itens)} Entradas", "ok")
                else:
                    log(f"  {valor}")

            log("\n" + "=" * 70)

        except Exception as e:
            log(f"[ERRO] {e}", "erro")

    em_thread(task)

def limpar_console():
    console.delete("1.0", tk.END)
    result.config(text="", fg=CINZA)

# ==================== MENU DE CONTEXTO (BOTÃO DIREITO) ====================
def mostrar_menu_contexto(event):
    # Pega a linha clicada
    index = console.index(f"@{event.x},{event.y}")
    linha = console.get(f"{index} linestart", f"{index} lineend").strip()
    
    caminho = extrair_caminho_da_linha(linha)
    
    if not caminho or caminho.startswith("[") or caminho.startswith("-") or caminho.startswith("■"):
        return  # Não é uma entrada de caminho

    menu = tk.Menu(janela, tearoff=0, bg="#2d2d2d", fg=FG, 
                   activebackground=AZUL, activeforeground="white",
                   font=("Arial", 10))
    
    menu.add_command(
        label="🔍  Abrir local",
        command=lambda: abrir_local(caminho)
    )
    menu.add_separator()
    menu.add_command(
        label="🗑️  Remover Esta Entrada",
        command=lambda: remover_entrada(caminho_forcado=caminho, confirmar=True)
    )
    
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()

# ==================== INTERFACE ====================
def lbl(parent, t, fg=FG, f=("Arial", 10), **kw):
    return tk.Label(parent, text=t, bg=BG, fg=fg, font=f, **kw)

def btn(parent, texto, comando, cor, largura=18):
    return tk.Button(
        parent,
        text=texto,
        command=comando,
        bg=cor,
        fg="black",
        font=("Arial", 10, "bold"),
        width=largura,
        relief="raised",
        bd=2,
        cursor="hand2",
        activebackground=cor,
        activeforeground="black"
    )

janela = tk.Tk()
janela.title("GERENCIADOR DE VARIÁVEIS DE AMBIENTE - WINDOWS")
janela.geometry("1020x900")
janela.configure(bg=BG)
janela.minsize(800, 700)

var_prog = tk.StringVar()
modo = tk.StringVar(value="pasta")
anexar = tk.BooleanVar(value=True)


# ==================== ÍCONE E TÍTULO ====================

URL = "https://i.postimg.cc/Y0zVt9ZD/windows-7-logo-6718525-1280.png"

try:
    resposta = requests.get(URL, timeout=10)
    resposta.raise_for_status()

    img = Image.open(BytesIO(resposta.content))
    img = img.resize((64, 64), Image.LANCZOS)

    logo_windows = ImageTk.PhotoImage(img)

    # Ícone da janela
    janela.iconphoto(True, logo_windows)

    # Mantém referência para não desaparecer
    janela.logo_windows = logo_windows

except Exception as e:
    print("Erro ao carregar ícone:", e)


# Frame do título
frame_titulo = tk.Frame(janela, bg=BG)
frame_titulo.pack(pady=(12, 2))


# Logo esquerdo
tk.Label(
    frame_titulo,
    image=logo_windows,
    bg=BG
).pack(side="left", padx=(0, 8))


# Título
tk.Label(
    frame_titulo,
    text="GERENCIADOR DE VARIÁVEIS DE AMBIENTE - WINDOWS",
    fg=VERDE,
    bg=BG,
    font=("Arial", 16, "bold")
).pack(side="left")


# Logo direito
tk.Label(
    frame_titulo,
    image=logo_windows,
    bg=BG
).pack(side="left", padx=(8, 0))


lbl(janela, "Escolha a variável → escolha o programa/pasta → adicione ou remova", CINZA).pack()


# === Seleção de variável ===
lbl(janela, "VARIÁVEL", VERDE, ("Arial", 10, "bold")).pack(pady=(10, 0))
frame_var = tk.Frame(janela, bg=BG)
frame_var.pack(pady=4)

combo = ttk.Combobox(
    frame_var,
    values=["PATH", "SSLKEYLOGFILE", "Personalizada"],
    state="readonly",
    width=18,
    font=("Arial", 10)
)
combo.current(0)
combo.pack(side="left", padx=4)

entry_nome = tk.Entry(
    frame_var,
    width=28,
    bg="#2d2d2d",
    fg=FG,
    insertbackground=FG,
    font=("Arial", 10),
    state="disabled"
)
entry_nome.pack(side="left", padx=4)

def ao_mudar(_=None):
    if combo.get() == "Personalizada":
        entry_nome.config(state="normal")
    else:
        entry_nome.config(state="disabled")
    if combo.get() == "SSLKEYLOGFILE":
        modo.set("arquivo")

combo.bind("<<ComboboxSelected>>", ao_mudar)

# === Escolher programa / pasta ===
frame_escolha = tk.Frame(janela, bg=BG)
frame_escolha.pack(pady=10)

btn(frame_escolha, "👨‍💻 ESCOLHER PROGRAMA", escolher_prog, AZUL, 23).pack(side="left", padx=6)
btn(frame_escolha, "📁 ESCOLHER PASTA", escolher_pasta, "#eff31f", 18).pack(side="left", padx=6)

lbl(janela, "", CINZA, ("Consolas", 9), textvariable=var_prog, wraplength=850).pack(pady=2)

# === Modo e opções ===
frame_m = tk.Frame(janela, bg=BG)
frame_m.pack(pady=4)

tk.Radiobutton(
    frame_m, text="Pasta do programa", variable=modo, value="pasta",
    bg=BG, fg=FG, selectcolor="#2d2d2d", font=("Arial", 9)
).pack(side="left")

tk.Radiobutton(
    frame_m, text="Caminho completo do .exe", variable=modo, value="arquivo",
    bg=BG, fg=FG, selectcolor="#2d2d2d", font=("Arial", 9)
).pack(side="left", padx=12)

tk.Checkbutton(
    janela,
    text="Adicionar ao valor atual (não substituir)",
    variable=anexar,
    bg=BG, fg=FG, selectcolor="#2d2d2d",
    font=("Arial", 9)
).pack(pady=3)

# === Botões principais ===
frame_b = tk.Frame(janela, bg=BG)
frame_b.pack(pady=10)

tk.Button(
    frame_b,
    text="👨‍💻 ADICIONAR VARIAVEL",
    command=adicionar,
    bg="#00a86b",
    fg="black",
    font=("Arial", 10, "bold"),
    width=22,
    relief="raised",
    bd=2,
    cursor="hand2",
    activebackground="#00a86b",
    activeforeground="black"
).pack(side="left", padx=4)

tk.Button(
    frame_b,
    text="🔎 MOSTRAR VALOR",
    command=mostrar_var,
    bg="#e79b0d",
    fg="black",
    font=("Arial", 10, "bold"),
    width=19,
    relief="raised",
    bd=2,
    cursor="hand2",
    activebackground="#e79b0d",
    activeforeground="black"
).pack(side="left", padx=4)

tk.Button(
    frame_b,
    text="🔎 LISTAR TODAS 🔍",
    command=listar,
    bg=CINZA,
    fg="black",
    font=("Arial", 10, "bold"),
    width=18,
    relief="raised",
    bd=2,
    cursor="hand2",
    activebackground=CINZA,
    activeforeground="black"
).pack(side="left", padx=4)

tk.Button(
    frame_b,
    text="🗑 REMOVER ENTRADA",
    command=lambda: remover_entrada(),
    bg="#d32f2f",
    fg="black",
    font=("Arial", 10, "bold"),
    width=22,
    relief="raised",
    bd=2,
    cursor="hand2",
    activebackground="#d32f2f",
    activeforeground="white"
).pack(side="left", padx=4)

tk.Button(
    frame_b,
    text="🧹 LIMPAR CONSOLE",
    command=limpar_console,
    bg="#555555",
    fg="white",
    font=("Arial", 10, "bold"),
    width=18,
    relief="raised",
    bd=2,
    cursor="hand2",
    activebackground="#555555",
    activeforeground="white"
).pack(side="left", padx=4)

# Resultado
result = lbl(janela, "", CINZA, ("Consolas", 9), wraplength=850)
result.pack(pady=6)

# Console
frame_c = tk.Frame(janela, bg=BG)
frame_c.pack(fill="both", expand=True, padx=12, pady=8)

lbl(frame_c, "Console  (selecione uma linha ou clique com botão direito)", VERDE, ("Consolas", 10, "bold")).pack(anchor="w")

console = scrolledtext.ScrolledText(
    frame_c,
    bg="black",
    fg="#dcdcdc",
    font=("Consolas", 11),
    insertbackground=FG,
    height=25,
    selectbackground="#264f78",
    selectforeground="white"
)
console.pack(fill="both", expand=True)

# Tags de cor
console.tag_config("ok", foreground=VERDE)
console.tag_config("erro", foreground=VERMELHO)
console.tag_config("aviso", foreground=AMARELO)
console.tag_config("info", foreground="#dcdcdc")

# Menu de contexto (botão direito)
console.bind("<Button-3>", mostrar_menu_contexto)

# Mensagem inicial
frame_rodape = tk.Frame(janela, bg=BG)
frame_rodape.pack(side="bottom", fill="x", pady=(2, 2))

lbl_rodape = tk.Label(
    frame_rodape,
    text=(
        "Pronto. Escolha um programa ou pasta e use os botões acima  |  "
        "Dica: Selecione uma linha e clique em REMOVER ENTRADA   |   "
        "Botão direito em uma entrada para abrir o local (🔍)"
    ),
    bg=BG,
    fg="#4BFC05",
    font=("Arial", 8, "bold"),
    justify="left",
    anchor="w"
)

lbl_rodape.pack(fill="x", padx=8, pady=5)

janela.mainloop()
