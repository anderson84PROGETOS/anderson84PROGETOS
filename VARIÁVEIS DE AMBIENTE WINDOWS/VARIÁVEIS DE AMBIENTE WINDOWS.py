import os
import ctypes
import threading
import winreg
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# ==================== CORES ====================
BG        = "#1e1e1e"
FG        = "#ffffff"
CINZA     = "#0ce6ee"
VERDE     = "#00ff88"
AMARELO   = "#ffcc00"
VERMELHO  = "#ff5555"
AZUL      = "#0078D7"
LARANJA   = "#e79b0d"
CINZA_ESCURO = "#2d2d2d"
ABOBORA   = "#FF8C00"

# ==================== ESTADO GLOBAL ====================
current_var = None
current_entries = []

# ==================== FUNÇÕES AUXILIARES ====================
def log(msg, tag="info"):
    console.insert(tk.END, msg + "\n", tag)
    console.see(tk.END)

def em_thread(fn):
    threading.Thread(target=fn, daemon=True).start()

def get_registry_key(scope, writable=False):
    """Retorna a chave do registro de acordo com o escopo"""
    if scope == "sistema":
        root = winreg.HKEY_LOCAL_MACHINE
        path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    else:
        root = winreg.HKEY_CURRENT_USER
        path = "Environment"

    access = winreg.KEY_READ | winreg.KEY_SET_VALUE if writable else winreg.KEY_READ
    return winreg.OpenKey(root, path, 0, access)

def ler_var(nome, scope=None):
    if scope is None:
        scope = escopo.get()
        if scope == "ambos":
            try:
                return ler_var(nome, "usuario")
            except:
                return ler_var(nome, "sistema")

    try:
        k = get_registry_key(scope, writable=False)
        try:
            v, _ = winreg.QueryValueEx(k, nome)
            return v
        except FileNotFoundError:
            return None
        finally:
            winreg.CloseKey(k)
    except Exception as e:
        raise Exception(f"Erro ao ler variável ({scope}): {e}")

def gravar_var(nome, valor, scope=None):
    if scope is None:
        scope = escopo.get()
        if scope == "ambos":
            raise Exception("Selecione Usuário ou Sistema para alterar variáveis.")

    try:
        k = get_registry_key(scope, writable=True)
        try:
            winreg.SetValueEx(k, nome, 0, winreg.REG_EXPAND_SZ, valor)
        finally:
            winreg.CloseKey(k)
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0, 5000, 0)
    except PermissionError:
        raise Exception("Permissão negada! Execute o programa como Administrador para alterar variáveis do Sistema.")
    except Exception as e:
        raise Exception(f"Erro ao gravar variável: {e}")

def listar_vars(scope=None):
    if scope is None:
        scope = escopo.get()

    if scope == "ambos":
        resultado = []
        for s, tipo in [("usuario", "Usuário"), ("sistema", "Sistema")]:
            try:
                vars_ = listar_vars(s)
                for nome, valor in vars_:
                    resultado.append((nome, valor, tipo))
            except:
                pass
        return resultado

    try:
        k = get_registry_key(scope, writable=False)
        out = []
        i = 0
        while True:
            try:
                n, v, _ = winreg.EnumValue(k, i)
                out.append((n, v))
                i += 1
            except OSError:
                break
        winreg.CloseKey(k)
        return out
    except Exception as e:
        raise Exception(f"Erro ao listar variáveis: {e}")

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
    texto = texto.strip()
    if not texto:
        return None
    if ". " in texto:
        partes = texto.split(". ", 1)
        if len(partes) == 2 and partes[0].strip().isdigit():
            return partes[1].strip()
    return texto.strip()

def obter_selecao_console():
    try:
        if console.tag_ranges(tk.SEL):
            texto = console.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
            return extrair_caminho_da_linha(texto)
    except tk.TclError:
        pass
    return None

def abrir_local(caminho):
    if not caminho:
        return
    caminho = caminho.replace("/", "\\")
    try:
        if os.path.isfile(caminho):
            subprocess.run(["explorer", "/select,", caminho], check=False)
        elif os.path.isdir(caminho):
            os.startfile(caminho)
        else:
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
            scope = escopo.get()
            if scope == "ambos":
                valor_u = ler_var(nome, "usuario")
                valor_s = ler_var(nome, "sistema")
                
                log(f"\n[+] Variável: {nome}", "ok")
                log("-" * 70)
                
                if valor_u is not None:
                    log("■ Usuário:", "ok")
                    if ";" in valor_u or nome.upper() == "PATH":
                        for i, item in enumerate([p for p in valor_u.split(";") if p.strip()], 1):
                            log(f"  {i:2}. {item}")
                    else:
                        log(f"  {valor_u}")
                else:
                    log("■ Usuário: (não existe)", "aviso")
                
                if valor_s is not None:
                    log("\n■ Sistema:", "ok")
                    if ";" in valor_s or nome.upper() == "PATH":
                        for i, item in enumerate([p for p in valor_s.split(";") if p.strip()], 1):
                            log(f"  {i:2}. {item}")
                    else:
                        log(f"  {valor_s}")
                else:
                    log("\n■ Sistema: (não existe)", "aviso")
                
                result.config(text=f"{nome} (Usuário + Sistema)", fg=VERDE)
                return

            valor = ler_var(nome, scope)
            tipo = "Sistema" if scope == "sistema" else "Usuário"
            log(f"\n[+] Variável ({tipo}): {nome}", "ok")
            log("-" * 70)

            current_var = nome
            current_entries = []

            if valor is None:
                log(f"[-] {nome} ainda não existe.", "erro")
                result.config(text="Variável não existe", fg=AMARELO)
                return

            if ";" in valor or nome.upper() == "PATH":
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
            if escopo.get() == "ambos":
                messagebox.showwarning("Aviso", "Selecione Usuário ou Sistema para adicionar variáveis.")
                return

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
            tipo = "Sistema" if escopo.get() == "sistema" else "Usuário"
            log(f"\n[OK] {nome} ({tipo}) atualizada com sucesso!", "ok")
            log(f"\nAdicionado: {novo}")
            result.config(text=f"{nome} atualizada", fg=VERDE)
            messagebox.showinfo("Sucesso", f"{nome} atualizada!\n\nReinicie o terminal/programa para aplicar.")
            atualizar_tabela()

        except Exception as e:
            log(f"[ERRO] {e}", "erro")
            result.config(text=str(e), fg=VERMELHO)

    em_thread(task)

def remover_entrada(caminho_forcado=None, confirmar=True):
    def task():
        global current_entries
        try:
            if escopo.get() == "ambos":
                messagebox.showwarning("Aviso", "Selecione Usuário ou Sistema para remover entradas.")
                return

            nome = nome_var()
            
            alvo = caminho_forcado or obter_selecao_console()
            
            if not alvo:
                alvo = caminho_alvo()

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
            
            current_entries = novas
            
            # Atualiza a tabela primeiro
            atualizar_tabela()
            
            # Mensagem com cor de abóbora no console e no result
            log(f"\n[OK] Removido de {nome}: {alvo}\n", "abobora")            
            result.config(text=f"Removido de {nome}", fg=ABOBORA)
            messagebox.showinfo("Sucesso", f"Entrada removida de {nome}!\n\nReinicie o terminal para aplicar.")

        except Exception as e:
            log(f"[ERRO] {e}", "erro")
            result.config(text=str(e), fg=VERMELHO)

    em_thread(task)

def atualizar_tabela():
    """Atualiza a tabela visual"""
    for item in tree.get_children():
        tree.delete(item)
    
    try:
        scope = escopo.get()
        vars_ = listar_vars(scope)

        if scope == "ambos":
            for nome, valor, tipo in sorted(vars_, key=lambda x: (x[2], x[0].upper())):
                tree.insert("", "end", values=(tipo, nome, valor))
            result.config(text=f"{len(vars_)} variáveis (Usuário + Sistema)", fg=VERDE)
            lbl_tabela.config(text="Variáveis de ambiente (Usuário + Sistema)")
        else:
            tipo = "Sistema" if scope == "sistema" else "Usuário"
            for nome, valor in sorted(vars_, key=lambda x: x[0].upper()):
                tree.insert("", "end", values=(tipo, nome, valor))
            result.config(text=f"{len(vars_)} variáveis de ambiente do {tipo}", fg=VERDE)
            lbl_tabela.config(text=f"Variáveis de ambiente do {tipo} (igual ao Windows)")

    except Exception as e:
        result.config(text=str(e), fg=VERMELHO)
        log(f"[ERRO] {e}", "erro")

def listar():
    def task():
        try:
            atualizar_tabela()
            scope = escopo.get()
            vars_ = listar_vars(scope)
            total = len(vars_)
            
            if scope == "ambos":
                log(f"\n[+] {total} variáveis (Usuário + Sistema)", "ok")
            else:
                tipo = "Sistema" if scope == "sistema" else "Usuário"
                log(f"\n[+] {total} variáveis de ambiente do {tipo}", "ok")
            
            log("=" * 70)

            if scope == "ambos":
                for nome, valor, tipo in sorted(vars_, key=lambda x: (x[2], x[0].upper())):
                    log(f"\n■ [{tipo}] {nome}", "ok")
                    log("-" * 70)
                    if ";" in valor or nome.upper() == "PATH":
                        itens = [i.strip() for i in valor.split(";") if i.strip()]
                        for i, item in enumerate(itens, 1):
                            log(f"  {i:2}. {item}")
                        log(f"\n[OK] {len(itens)} Entradas", "ok")
                    else:
                        log(f"  {valor}")
            else:
                for nome, valor in sorted(vars_, key=lambda x: x[0].upper()):
                    log(f"\n■ {nome}", "ok")
                    log("-" * 70)
                    if ";" in valor or nome.upper() == "PATH":
                        itens = [i.strip() for i in valor.split(";") if i.strip()]
                        for i, item in enumerate(itens, 1):
                            log(f"  {i:2}. {item}")
                        log(f"\n[OK] {len(itens)} Entradas", "ok")
                    else:
                        log(f"  {valor}")

            log("\n" + "=" * 70)
            log(f"[OK] Total de variáveis listadas: {total}", "ok")

        except Exception as e:
            log(f"[ERRO] {e}", "erro")

    em_thread(task)

def limpar_console():
    console.delete("1.0", tk.END)
    result.config(text="", fg=CINZA)

def ao_selecionar_tabela(event):
    selecionado = tree.selection()
    if selecionado:
        item = tree.item(selecionado[0])
        valores = item["values"]
        if len(valores) >= 2:
            nome = valores[1]
            combo.set(nome if nome in ["PATH", "SSLKEYLOGFILE"] else "Personalizada")
            if nome not in ["PATH", "SSLKEYLOGFILE"]:
                entry_nome.config(state="normal")
                entry_nome.delete(0, tk.END)
                entry_nome.insert(0, nome)
            ao_mudar()

def ao_mudar_escopo():
    atualizar_tabela()
    if escopo.get() == "sistema":
        result.config(text="⚠ Modo SISTEMA — precisa executar como Administrador para alterar", fg=AMARELO)
    elif escopo.get() == "ambos":
        result.config(text="Modo AMBOS (somente visualização + consulta)", fg=CINZA)
    else:
        result.config(text="", fg=CINZA)

# ==================== MENU DE CONTEXTO ====================
def mostrar_menu_contexto(event):
    index = console.index(f"@{event.x},{event.y}")
    linha = console.get(f"{index} linestart", f"{index} lineend").strip()
    
    caminho = extrair_caminho_da_linha(linha)
    
    if not caminho or caminho.startswith("[") or caminho.startswith("-") or caminho.startswith("■"):
        return

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

def mostrar_menu_contexto_tabela(event):
    item = tree.identify_row(event.y)
    if not item:
        return

    tree.selection_set(item)
    tree.focus(item)

    valores = tree.item(item, "values")
    if not valores or len(valores) < 3:
        return

    tipo, nome_var_tabela, valor = valores[0], valores[1], str(valores[2]).strip()

    if not valor:
        return

    if ";" in valor:
        caminho = valor.split(";")[0].strip()
    else:
        caminho = valor

    menu = tk.Menu(janela, tearoff=0, bg="#2d2d2d", fg=FG,
                   activebackground=AZUL, activeforeground="white",
                   font=("Arial", 10))

    menu.add_command(
        label="🔍  Abrir local",
        command=lambda: abrir_local(caminho)
    )

    menu.add_separator()
    menu.add_command(
        label=f"📌  Selecionar: {nome_var_tabela}",
        command=lambda: ao_selecionar_tabela(None)
    )

    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()

# ==================== INTERFACE ====================
def lbl(parent, t, fg=FG, f=("Arial", 10), **kw):
    return tk.Label(parent, text=t, bg=BG, fg=fg, font=f, **kw)

janela = tk.Tk()
janela.title("VARIÁVEIS DE AMBIENTE - WINDOWS")

janela.state("zoomed")
janela.geometry("1150x980")
janela.configure(bg=BG)
janela.minsize(950, 800)

var_prog = tk.StringVar()
modo = tk.StringVar(value="pasta")
anexar = tk.BooleanVar(value=True)
escopo = tk.StringVar(value="usuario")

# ==================== TÍTULO ====================
frame_titulo = tk.Frame(janela, bg=BG)
frame_titulo.pack(pady=(12, 2))

tk.Label(
    frame_titulo,
    text="VARIÁVEIS DE AMBIENTE WINDOWS",
    fg=VERDE,
    bg=BG,
    font=("Arial", 18, "bold")
).pack(side="left")

lbl(janela, "Escolha a variável → escolha o programa/pasta → adicione ou remova", CINZA).pack()

# === ESCOPO ===
frame_escopo = tk.Frame(janela, bg=BG)
frame_escopo.pack(pady=(8, 2))

lbl(frame_escopo, "ESCOPO:", VERDE, ("Arial", 10, "bold")).pack(side="left", padx=(0, 10))

tk.Radiobutton(frame_escopo, text="👤 Usuário", variable=escopo, value="usuario",
               command=ao_mudar_escopo, bg=BG, fg=FG, selectcolor="#2d2d2d",
               font=("Arial", 10, "bold"), activebackground=BG, activeforeground=VERDE).pack(side="left", padx=6)

tk.Radiobutton(frame_escopo, text="💻 Sistema", variable=escopo, value="sistema",
               command=ao_mudar_escopo, bg=BG, fg=FG, selectcolor="#2d2d2d",
               font=("Arial", 10, "bold"), activebackground=BG, activeforeground=AMARELO).pack(side="left", padx=6)

tk.Radiobutton(frame_escopo, text="🔀 Ambos", variable=escopo, value="ambos",
               command=ao_mudar_escopo, bg=BG, fg=FG, selectcolor="#2d2d2d",
               font=("Arial", 10, "bold"), activebackground=BG, activeforeground=CINZA).pack(side="left", padx=6)

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

tk.Button(frame_escolha, text="👨‍💻 ESCOLHER PROGRAMA", command=escolher_prog,
          bg=AZUL, fg="black", font=("Arial", 10, "bold"), width=23,
          relief="raised", bd=2, cursor="hand2").pack(side="left", padx=6)

tk.Button(frame_escolha, text="📁 ESCOLHER PASTA", command=escolher_pasta,
          bg="#eff31f", fg="black", font=("Arial", 10, "bold"), width=18,
          relief="raised", bd=2, cursor="hand2").pack(side="left", padx=6)

lbl(janela, "", CINZA, ("Consolas", 9), textvariable=var_prog, wraplength=900).pack(pady=2)

# === Modo e opções ===
frame_m = tk.Frame(janela, bg=BG)
frame_m.pack(pady=4)

tk.Radiobutton(frame_m, text="Pasta do programa", variable=modo, value="pasta",
               bg=BG, fg=FG, selectcolor="#2d2d2d", font=("Arial", 9)).pack(side="left")

tk.Radiobutton(frame_m, text="Caminho completo do .exe", variable=modo, value="arquivo",
               bg=BG, fg=FG, selectcolor="#2d2d2d", font=("Arial", 9)).pack(side="left", padx=12)

tk.Checkbutton(janela, text="Adicionar ao valor atual (não substituir)",
               variable=anexar, bg=BG, fg=FG, selectcolor="#2d2d2d",
               font=("Arial", 9)).pack(pady=3)

# === Botões principais ===
frame_b = tk.Frame(janela, bg=BG)
frame_b.pack(pady=10)

tk.Button(frame_b, text="👨‍💻 ADICIONAR VARIAVEL", command=adicionar,
          bg="#00a86b", fg="black", font=("Arial", 10, "bold"), width=22,
          relief="raised", bd=2, cursor="hand2").pack(side="left", padx=4)

tk.Button(frame_b, text="🔎 MOSTRAR VALOR", command=mostrar_var,
          bg="#e79b0d", fg="black", font=("Arial", 10, "bold"), width=19,
          relief="raised", bd=2, cursor="hand2").pack(side="left", padx=4)

tk.Button(frame_b, text="🔎 LISTAR TODAS 🔍", command=listar,
          bg=CINZA, fg="black", font=("Arial", 10, "bold"), width=18,
          relief="raised", bd=2, cursor="hand2").pack(side="left", padx=4)

tk.Button(frame_b, text="🗑 REMOVER ENTRADA", command=lambda: remover_entrada(),
          bg="#d32f2f", fg="black", font=("Arial", 10, "bold"), width=22,
          relief="raised", bd=2, cursor="hand2").pack(side="left", padx=4)

tk.Button(frame_b, text="🧹 LIMPAR CONSOLE", command=limpar_console,
          bg="#555555", fg="white", font=("Arial", 10, "bold"), width=18,
          relief="raised", bd=2, cursor="hand2").pack(side="left", padx=4)

# Resultado
result = lbl(janela, "", CINZA, ("Consolas", 9), wraplength=900)
result.pack(pady=6)

# ==================== TABELA ====================
frame_tabela = tk.Frame(janela, bg=BG)
frame_tabela.pack(fill="x", padx=12, pady=(5, 0), anchor="w")

lbl_tabela = lbl(frame_tabela, "Variáveis de ambiente do Usuário (igual ao Windows)", VERDE, ("Arial", 10, "bold"))
lbl_tabela.pack(anchor="w")

frame_tree = tk.Frame(frame_tabela, bg=BG)
frame_tree.pack(fill="x", anchor="w")

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background="#252526",
    foreground="#FFFFFF",
    fieldbackground="#252526",
    rowheight=25,
    font=("Consolas", 10),
    borderwidth=0
)

style.configure(
    "Treeview.Heading",
    background="#0078D7",
    foreground="#FFFFFF",
    font=("Arial", 10, "bold")
)

style.map(
    "Treeview",
    background=[("selected", "#094771")],
    foreground=[("selected", "#FFFFFF")]
)

tree = ttk.Treeview(frame_tree, columns=("Tipo", "Variável", "Valor"), show="headings", height=7)

tree.heading("Tipo", text="Tipo", anchor="w")
tree.heading("Variável", text="Variável", anchor="w")
tree.heading("Valor", text="Valor", anchor="w")

tree.column("Tipo", width=100, minwidth=100, anchor="w", stretch=False)
tree.column("Variável", width=400, minwidth=200, anchor="w", stretch=False)
tree.column("Valor", width=3000, minwidth=700, anchor="w", stretch=False)

scrollbar_t = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
scrollbar_h = ttk.Scrollbar(frame_tree, orient="horizontal", command=tree.xview)

tree.configure(yscrollcommand=scrollbar_t.set, xscrollcommand=scrollbar_h.set)

tree.grid(row=0, column=0, sticky="nsew")
scrollbar_t.grid(row=0, column=1, sticky="ns")
scrollbar_h.grid(row=1, column=0, sticky="ew")

frame_tree.grid_columnconfigure(0, weight=1)
tree.xview_moveto(0)

tree.bind("<<TreeviewSelect>>", ao_selecionar_tabela)
tree.bind("<Button-3>", mostrar_menu_contexto_tabela)

# ==================== CONSOLE ====================
frame_c = tk.Frame(janela, bg=BG)
frame_c.pack(fill="both", expand=True, padx=12, pady=8)

lbl(frame_c, "Console  (selecione uma linha ou clique com botão direito)", VERDE, ("Consolas", 10, "bold")).pack(anchor="w")

console = scrolledtext.ScrolledText(
    frame_c,
    bg="black",
    fg="#dcdcdc",
    font=("Consolas", 11),
    insertbackground=FG,
    height=11,
    selectbackground="#264f78",
    selectforeground="white"
)
console.pack(fill="both", expand=True)

console.tag_config("ok", foreground=VERDE)
console.tag_config("erro", foreground=VERMELHO)
console.tag_config("aviso", foreground=AMARELO)
console.tag_config("info", foreground="#dcdcdc")
console.tag_config("abobora", foreground=ABOBORA)   # ← COR DE ABÓBORA

console.bind("<Button-3>", mostrar_menu_contexto)

# Rodapé
frame_rodape = tk.Frame(janela, bg=BG)
frame_rodape.pack(side="bottom", fill="x", pady=(2, 2))

lbl_rodape = tk.Label(
    frame_rodape,
    text=(
        "Pronto  |  Usuário / Sistema / Ambos  |  "
        "Modo Sistema precisa de privilégios de Administrador  |  "
        "Botão direito na tabela ou console → Abrir local"
    ),
    bg=BG,
    fg="#4BFC05",
    font=("Arial", 8, "bold"),
    justify="left",
    anchor="w"
)
lbl_rodape.pack(fill="x", padx=8, pady=5)

# Carrega a tabela ao iniciar
atualizar_tabela()

janela.mainloop()
