import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import winreg, threading, subprocess, os, hashlib, webbrowser
from datetime import datetime

programas = []
janelas_hash_abertas = {}  # Controla janelas de hash abertas

def converter_tamanho(size_mb):
    try:
        size_mb = float(size_mb)
        return f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.2f} MB"
    except:
        return "Desconhecido"

def formatar_data(data):
    try:
        data = str(data)
        return datetime.strptime(data, "%Y%m%d").strftime("%d/%m/%Y") if len(data) == 8 and data.isdigit() else data
    except:
        return "Desconhecida"

def pegar_data_pasta(caminho):
    try:
        if caminho and os.path.exists(caminho):
            return datetime.fromtimestamp(os.path.getctime(caminho)).strftime("%d/%m/%Y")
    except:
        pass
    return "Desconhecida"

def calcular_hash_arquivo(caminho, algoritmo="sha256"):
    if not caminho or not os.path.isfile(caminho): return ""
    try:
        h = hashlib.new(algoritmo)
        with open(caminho, "rb", buffering=0) as f:
            for bloco in iter(lambda: f.read(65536), b""): h.update(bloco)
        return h.hexdigest()
    except:
        return ""

def abrir_pasta_programa(event):
    selecionado = tree.selection()
    if not selecionado: return
    item = tree.item(selecionado)
    nome = item["values"][0]
    for prog in programas:
        if prog["nome"] == nome:
            pasta = prog["local"]
            if pasta and os.path.exists(pasta): subprocess.Popen(f'explorer "{pasta}"')
            else: messagebox.showwarning("Aviso", "Pasta do programa não encontrada.")
            return

def abrir_virustotal():
    selecionado = tree.selection()
    if not selecionado: messagebox.showwarning("Aviso", "Selecione um programa primeiro."); return
    item = tree.item(selecionado)
    nome = item["values"][0]
    for prog in programas:
        if prog["nome"] == nome:
            caminho_exe = prog.get("caminho_exe", "")
            if not caminho_exe or not os.path.isfile(caminho_exe):
                messagebox.showwarning("Aviso", f"Executável não encontrado para: {nome}"); return
            hash_sha256 = calcular_hash_arquivo(caminho_exe, "sha256")
            if not hash_sha256: messagebox.showerror("Erro", "Não foi possível calcular o hash do arquivo."); return
            webbrowser.open(f"https://www.virustotal.com/gui/file/{hash_sha256}")
            status_var.set(f"Abrindo VirusTotal: {hash_sha256[:16]}..."); return

def abrir_virustotal_por_hash(hash_valor):
    if not hash_valor:
        messagebox.showwarning("Aviso", "Hash não disponível para este programa.")
        return
    webbrowser.open(f"https://www.virustotal.com/gui/file/{hash_valor}")
    status_var.set(f"Abrindo VirusTotal: {hash_valor[:16]}...")

def menu_contexto(event):
    item_id = tree.identify_row(event.y)
    coluna = tree.identify_column(event.x)
    if not item_id or not coluna: return
    tree.selection_set(item_id)
    indice_coluna = int(coluna.replace("#", "")) - 1
    item = tree.item(item_id)
    valores = item["values"]
    if indice_coluna != 5: return
    hash_completo = ""
    nome = valores[0] if valores else ""
    for prog in programas:
        if prog["nome"] == nome:
            hash_completo = prog.get("hash_sha256", "")
            break
    if not hash_completo: return
    menu = tk.Menu(janela, tearoff=0, bg="#222222", fg="white", font=("Consolas", 10))
    menu.add_command(label=f"🔍 Abrir no VirusTotal", command=lambda: abrir_virustotal_por_hash(hash_completo))
    menu.add_command(label=f"📋 Copiar SHA256", command=lambda: (
        janela.clipboard_clear(), janela.clipboard_append(hash_completo), janela.update(),
        status_var.set(f"Copiado: {hash_completo[:16]}..."), messagebox.showinfo("Copiado", "SHA256 copiado.")))
    try: menu.tk_popup(event.x_root, event.y_root)
    finally: menu.grab_release()

def ler_programas_registro(root_key, path):
    lista = []
    try:
        registro = winreg.OpenKey(root_key, path)
        total_subchaves = winreg.QueryInfoKey(registro)[0]
        for i in range(total_subchaves):
            try:
                subkey_name = winreg.EnumKey(registro, i)
                subkey = winreg.OpenKey(root_key, path + "\\" + subkey_name)
                try: nome = winreg.QueryValueEx(subkey, "DisplayName")[0]
                except: nome = ""
                if not nome: continue
                try: versao = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                except: versao = "Desconhecida"
                try: fabricante = winreg.QueryValueEx(subkey, "Publisher")[0]
                except: fabricante = "Desconhecido"
                local = ""; caminho_exe = ""
                try: local = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                except: pass
                if not local:
                    try:
                        icone = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                        if icone:
                            icone_limpo = icone.split(",")[0]
                            local = os.path.dirname(icone_limpo); caminho_exe = icone_limpo
                    except: pass
                if not local:
                    try:
                        uninstall = winreg.QueryValueEx(subkey, "UninstallString")[0]
                        if uninstall: local = os.path.dirname(uninstall.split(".exe")[0])
                    except: pass
                if not caminho_exe and local and os.path.isdir(local):
                    try:
                        for arquivo in os.listdir(local):
                            if arquivo.lower().endswith(".exe"): caminho_exe = os.path.join(local, arquivo); break
                    except: pass
                data = "Desconhecida"
                try:
                    data_registro = winreg.QueryValueEx(subkey, "InstallDate")[0]
                    data = formatar_data(data_registro)
                except: pass
                if data == "Desconhecida": data = pegar_data_pasta(local)
                try: tamanho = converter_tamanho(float(winreg.QueryValueEx(subkey, "EstimatedSize")[0]) / 1024)
                except: tamanho = "Desconhecido"
                lista.append({"nome": nome, "versao": versao, "fabricante": fabricante, "data": data,
                              "tamanho": tamanho, "local": local, "caminho_exe": caminho_exe,
                              "hash_md5": "", "hash_sha1": "", "hash_sha256": ""})
            except: pass
    except: pass
    return lista

def calcular_hashes_programas(programas_lista):
    for i, prog in enumerate(programas_lista):
        caminho_exe = prog.get("caminho_exe", "")
        if caminho_exe and os.path.isfile(caminho_exe):
            programas_lista[i]["hash_md5"] = calcular_hash_arquivo(caminho_exe, "md5")
            programas_lista[i]["hash_sha1"] = calcular_hash_arquivo(caminho_exe, "sha1")
            programas_lista[i]["hash_sha256"] = calcular_hash_arquivo(caminho_exe, "sha256")
    return programas_lista

def atualizar_tabela(lista):
    tree.delete(*tree.get_children())
    for prog in lista:
        hash_exibicao = prog.get('hash_sha256', "")
        if not hash_exibicao: hash_exibicao = ""
        item_id = tree.insert("", "end", values=(
            prog['nome'], prog['versao'], prog['fabricante'], prog['data'],
            prog['tamanho'], hash_exibicao, prog['local']))
        if hash_exibicao: tree.tag_configure("hash_row", foreground="#00bfff"); tree.item(item_id, tags=("hash_row",))

def escanear_programas():
    global programas
    botao_scan.config(state="disabled"); botao_vt.config(state="disabled"); botao_hash_detalhe.config(state="disabled")
    tree.delete(*tree.get_children()); status_var.set("Escaneando programas instalados...")
    programas = []
    caminhos = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")]
    for root, path in caminhos: programas.extend(ler_programas_registro(root, path))
    vistos = set(); programas_unicos = []
    for prog in programas:
        chave = prog["nome"]
        if chave not in vistos: vistos.add(chave); programas_unicos.append(prog)
    status_var.set("Calculando hashes dos executáveis...")
    programas_unicos = calcular_hashes_programas(programas_unicos)
    programas = sorted(programas_unicos, key=lambda x: x['nome'].lower())
    atualizar_tabela(programas)
    status_var.set(f"Programas Encontrados: {len(programas)}")
    botao_scan.config(state="normal"); botao_vt.config(state="normal"); botao_hash_detalhe.config(state="normal")

def iniciar_scan():
    threading.Thread(target=escanear_programas, daemon=True).start()

def pesquisar_programa(event=None):
    termo = entrada_pesquisa.get().lower().strip()
    if not termo: atualizar_tabela(programas); status_var.set(f"Mostrando todos os programas ({len(programas)})"); return
    filtrados = [prog for prog in programas if (
        termo in prog['nome'].lower() or termo in prog['data'].lower() or
        termo in prog['fabricante'].lower() or termo in prog['local'].lower() or
        termo in prog.get('hash_sha256', "").lower())]
    atualizar_tabela(filtrados); status_var.set(f"Resultados encontrados: {len(filtrados)}")

def mostrar_detalhes_hash():
    """Mostra janela com hashes completos - NÃO bloqueante, pode minimizar a principal."""
    selecionado = tree.selection()
    if not selecionado: messagebox.showwarning("Aviso", "Selecione um programa primeiro."); return
    item = tree.item(selecionado); nome = item["values"][0]
    
    # Se já existe uma janela aberta para este programa, traz para frente
    if nome in janelas_hash_abertas and janelas_hash_abertas[nome].winfo_exists():
        janelas_hash_abertas[nome].lift()
        janelas_hash_abertas[nome].focus()
        return
    
    for prog in programas:
        if prog["nome"] == nome:
            janela_hash = tk.Toplevel(janela)
            janela_hash.title(f"Hashes - {nome}")
            janela_hash.geometry("750x250")
            janela_hash.configure(bg="#111111")
            # NÃO usar transient() nem grab_set() - permite minimizar a principal
            # janela_hash.transient(janela)  <-- REMOVIDO
            # janela_hash.grab_set()         <-- REMOVIDO
            
            # Registra a janela para controle
            janelas_hash_abertas[nome] = janela_hash
            
            # Remove do dicionário quando fechar
            def on_close():
                if nome in janelas_hash_abertas: del janelas_hash_abertas[nome]
                janela_hash.destroy()
            janela_hash.protocol("WM_DELETE_WINDOW", on_close)
            
            frame = tk.Frame(janela_hash, bg="#111111"); frame.pack(fill="both", expand=True, padx=20, pady=20)
            dados = [("MD5", prog.get("hash_md5", "Não calculado")),
                     ("SHA1", prog.get("hash_sha1", "Não calculado")),
                     ("SHA256", prog.get("hash_sha256", "Não calculado")),
                     ("Arquivo", prog.get("caminho_exe", "Não encontrado"))]
            for i, (label, valor) in enumerate(dados):
                tk.Label(frame, text=f"{label}:", bg="#111111", fg="cyan",
                         font=("Consolas", 10, "bold"), anchor="w").grid(row=i, column=0, sticky="w", pady=5, padx=(0,10))
                entry = tk.Entry(frame, bg="#1e1e1e", fg="black", font=("Consolas", 9), width=85, relief="flat")
                entry.insert(0, valor); entry.config(state="readonly"); entry.grid(row=i, column=1, sticky="ew", pady=5)
            frame.columnconfigure(1, weight=1)
            btn_frame = tk.Frame(janela_hash, bg="#111111"); btn_frame.pack(fill="x", padx=20, pady=(0,20))
            tk.Button(btn_frame, text="COPIAR SHA256",
                      command=lambda: (janela_hash.clipboard_clear(), janela_hash.clipboard_append(prog.get("hash_sha256","")),
                                       janela_hash.update(), messagebox.showinfo("Copiado", "SHA256 copiado para a área de transferência.")),
                      bg="#aa5500", fg="white", font=("Consolas",10,"bold")).pack(side="left", padx=(0,10))
            tk.Button(btn_frame, text="ABRIR VIRUSTOTAL",
                      command=lambda: (webbrowser.open(f"https://www.virustotal.com/gui/file/{prog.get('hash_sha256','')}")),
                      bg="#0055aa", fg="white", font=("Consolas",10,"bold")).pack(side="left")
            return
        
def mostrar_sobre():
    sobre_texto = """PROGRAMAS INSTALADOS WINDOWS - Scanner Completo

Funcionalidades:

• Escaneia programas instalados via Registro do Windows (HKLM + HKCU)

• Detecta programas de 32 e 64 bits

• Calcula hashes MD5, SHA1 e SHA256 dos executáveis principais

• Integração direta com VirusTotal (clique direito ou botão)

• Janelas de detalhes de hash não bloqueantes

• Pesquisa em tempo real

• Clique duplo abre a pasta do programa

• Clique direito na coluna SHA256 abre menu rápido

• Exportação completa para TXT

Requisitos:

• Windows 10/11

• Permissões de Administrador recomendadas

• Python 3.8+ com tkinter

Uso:
1. Execute o script

2. Clique em "ESCANEAR PROGRAMAS"

3. Use os botões e funcionalidades


Autor: [Anderson Moreira]

Versão: 1.0

Data: 13/07 Julho/2026"""
    
    messagebox.showinfo("Sobre este Script", sobre_texto)


def salvar_txt():
    if not programas: messagebox.showwarning("Aviso", "Nenhum dado encontrado."); return
    caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo TXT","*.txt")], title="Salvar relatório")
    if not caminho: return
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("="*90+"\nPROGRAMAS INSTALADOS WINDOWS\n"+"="*90+"\n\n")
            for prog in programas:
                f.write(f"NOME: {prog['nome']}\nVERSÃO: {prog['versao']}\nFABRICANTE: {prog['fabricante']}\n")
                f.write(f"DATA: {prog['data']}\nTAMANHO: {prog['tamanho']}\n")
                f.write(f"MD5: {prog.get('hash_md5','')}\nSHA1: {prog.get('hash_sha1','')}\nSHA256: {prog.get('hash_sha256','')}\n")
                f.write(f"CAMINHO: {prog['local']}\nEXECUTÁVEL: {prog.get('caminho_exe','')}\n"+"-"*90+"\n")
        messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso.")
    except Exception as e: messagebox.showerror("Erro", str(e))

valor_copiado = ""

def selecionar_celula(event):
    global valor_copiado
    item_id = tree.identify_row(event.y); coluna = tree.identify_column(event.x)
    if not item_id or not coluna: return
    valores = tree.item(item_id)["values"]; indice = int(coluna.replace("#","")) - 1
    if indice < len(valores): valor_copiado = str(valores[indice]); status_var.set(f"Selecionado para copiar: {valor_copiado}")

def copiar_valor():
    global valor_copiado
    if not valor_copiado: messagebox.showwarning("Aviso", "Clique em uma célula primeiro."); return
    janela.clipboard_clear(); janela.clipboard_append(valor_copiado); janela.update()
    status_var.set(f"Copiado: {valor_copiado}"); messagebox.showinfo("Copiado", valor_copiado)

# INTERFACE
janela = tk.Tk()
janela.title("VISUALIZADOR DE PROGRAMAS INSTALADOS WINDOWS")
janela.geometry("1700x800")
janela.state("zoomed"); janela.configure(bg="#111111")

style = ttk.Style(); style.theme_use("clam")
style.configure("Treeview", background="#1e1e1e", foreground="#ffffff", fieldbackground="#1e1e1e", rowheight=30, font=("Consolas",10))
style.configure("Treeview.Heading", background="#222222", foreground="cyan", font=("Consolas",10,"bold"))

frame_topo = tk.Frame(janela, bg="#111111"); frame_topo.pack(fill="x", pady=(10,5))

botao_scan = tk.Button(frame_topo, text="ESCANEAR PROGRAMAS", command=iniciar_scan, bg="#00aa00", fg="black", font=("Consolas",11,"bold"), width=20)
botao_scan.pack(side="left", padx=10)

botao_salvar = tk.Button(frame_topo, text="SALVAR TXT", command=salvar_txt, bg="#19d4ec", fg="black", font=("Consolas",11,"bold"), width=12)
botao_salvar.pack(side="left", padx=10)

botao_vt = tk.Button(frame_topo, text="ABRIR VIRUSTOTAL", command=abrir_virustotal, bg="#aa0000", fg="black", font=("Consolas",11,"bold"), width=18)
botao_vt.pack(side="left", padx=10)

botao_hash_detalhe = tk.Button(frame_topo, text="DETALHES HASH", command=mostrar_detalhes_hash, bg="#6600aa", fg="black", font=("Consolas",11,"bold"), width=15)
botao_hash_detalhe.pack(side="left", padx=10)

botao_copiar = tk.Button(frame_topo, text="COPIAR", command=copiar_valor, bg="#aa5500", fg="black", font=("Consolas",11,"bold"), width=8)
botao_copiar.pack(side="left", padx=10)

# Botão Sobre
botao_sobre = tk.Button(frame_topo, text="SOBRE ?", command=mostrar_sobre, 
                        bg="#555555", fg="white", font=("Consolas",11,"bold"), width=8)
botao_sobre.pack(side="left", padx=10)

tk.Label(frame_topo, text="PESQUISAR:", bg="#111111", fg="cyan", font=("Consolas",11,"bold")).pack(side="left", padx=(20,5))
entrada_pesquisa = tk.Entry(frame_topo, bg="#1e1e1e", fg="white", insertbackground="white", font=("Consolas", 11, "bold"), width=40)
entrada_pesquisa.pack(side="left", padx=5)
entrada_pesquisa.bind("<KeyRelease>", pesquisar_programa)

colunas = ("Nome","Versão","Fabricante","Data","Tamanho","SHA256","Caminho")
frame_tabela = tk.Frame(janela, bg="#111111"); frame_tabela.pack(fill="both", expand=True, padx=10, pady=(5,10))

style.configure("Vertical.TScrollbar", background="#00ff00", troughcolor="#111111", arrowcolor="black", bordercolor="#111111", darkcolor="#00aa00", lightcolor="#00ff00")
style.configure("Horizontal.TScrollbar", background="#00ff00", troughcolor="#111111", arrowcolor="black", bordercolor="#111111", darkcolor="#00aa00", lightcolor="#00ff00")

scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", style="Vertical.TScrollbar"); scroll_y.pack(side="right", fill="y")
scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", style="Horizontal.TScrollbar"); scroll_x.pack(side="bottom", fill="x")

tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
scroll_y.config(command=tree.yview); scroll_x.config(command=tree.xview)

for col in colunas: tree.heading(col, text=col)
tree.column("Nome", width=500); tree.column("Versão", width=200); tree.column("Fabricante", width=500)
tree.column("Data", width=130); tree.column("Tamanho", width=160)
tree.column("SHA256", width=500); tree.column("Caminho", width=700)

tree.pack(fill="both", expand=True)
tree.bind("<Button-1>", selecionar_celula)
tree.bind("<Button-3>", menu_contexto)
tree.bind("<Double-1>", abrir_pasta_programa)

status_var = tk.StringVar(); status_var.set("Pronto. Pressione ESCANEAR PROGRAMAS para iniciar. | Botão direito na coluna SHA256 para menu rápido.")
status = tk.Label(janela, textvariable=status_var, bg="#111111", fg="lime", anchor="w", font=("Consolas",10))
status.pack(fill="x", side="bottom")


janela.mainloop()
