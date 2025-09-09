import tkinter as tk
from tkinter import filedialog, scrolledtext
import re
import os
from tkinter import messagebox  # adicione no topo do código

# ---------------- Funções principais ----------------
def extrair_strings(caminho, min_len=4):
    resultado = []
    url_regex = re.compile(r"https?://[^\s\"'<>]+")  # captura http:// ou https://

    with open(caminho, "rb") as f:
        dados = f.read()
        texto = re.findall(rb"[ -~]{%d,}" % min_len, dados)
        for s in texto:
            s_dec = s.decode(errors="ignore").strip()
            if not s_dec:
                continue

            urls = url_regex.findall(s_dec)
            if urls:
                resultado.extend(urls)
                continue

            if re.fullmatch(r"[0-9A-Fa-f\s]+", s_dec):
                continue
            if re.fullmatch(r"[A-Za-z0-9+/=]+", s_dec):
                continue
            if not re.search(r"[A-Za-z]", s_dec):
                continue
            if len(s_dec) > 300:
                continue

            resultado.append(s_dec)

    resultado = list(dict.fromkeys(resultado))
    return resultado

# ---------------- Conteúdos globais ----------------
conteudo_strings = []
conteudo_hex = []
conteudo_ip = []
conteudo_porta = []

# ---------------- Funções de visualização ----------------
def abrir_arquivo():
    arquivo = filedialog.askopenfilename(
        title="Selecione um arquivo",
        filetypes=(("Todos os arquivos", "*.*"),)
    )
    if arquivo:
        caminho_var.set(arquivo)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, f"Arquivo selecionado\n\n{arquivo}\n")
        lbl_modo.config(text="Modo atual: Nenhum")
        saida_atual.set("")
        limpar_conteudos()

def limpar_conteudos():
    global conteudo_strings, conteudo_hex, conteudo_ip, conteudo_porta
    conteudo_strings = []
    conteudo_hex = []
    conteudo_ip = []
    conteudo_porta = []

def mostrar_todas_strings():
    global conteudo_strings
    limpar_conteudos()
    arquivo = caminho_var.get()
    if arquivo and os.path.isfile(arquivo):
        try:
            conteudo_strings = extrair_strings(arquivo)
            saida_atual.set("strings")
            text_area.delete(1.0, tk.END)
            for linha in conteudo_strings:
                text_area.insert(tk.END, linha + "\n", "strings")
            lbl_modo.config(text="Modo atual: Strings")
        except Exception as e:
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, f"Erro ao extrair strings: {e}")

def mostrar_ip_porta():
    global conteudo_ip, conteudo_porta
    limpar_conteudos()
    arquivo = caminho_var.get()
    if arquivo and os.path.isfile(arquivo):
        try:
            strings_texto = extrair_strings(arquivo)
            texto_unido = "\n".join(strings_texto)
            
            conteudo_ip = sorted(set(re.findall(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}', texto_unido)))
            conteudo_porta = sorted(set([p for p in re.findall(r'\b([0-9]{2,5})\b', texto_unido) if 0 < int(p) < 65536]))

            saida_atual.set("ip_porta")

            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, "IP Encontrados\n\n", "titulo")
            for ip in conteudo_ip:
                text_area.insert(tk.END, ip + "\n", "ip")
            text_area.insert(tk.END, "\nPortas Encontradas\n\n", "titulo")
            for porta in conteudo_porta:
                text_area.insert(tk.END, porta + "\n", "porta")

            lbl_modo.config(text="Modo atual: IP/Porta")
        except Exception as e:
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, f"Erro ao buscar IPs/Portas: {e}")

def mostrar_strings_hex():
    global conteudo_hex
    limpar_conteudos()
    arquivo = caminho_var.get()
    if arquivo and os.path.isfile(arquivo):
        try:
            strings_texto = extrair_strings(arquivo)
            conteudo_hex = []

            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, "Strings em HEX + ASCII\n\n", "titulo")

            for linha in strings_texto:
                hex_line = " ".join(f"{ord(c):02X}" for c in linha)
                combinado = f"{hex_line:<100}   {linha}"
                conteudo_hex.append(combinado)

                text_area.insert(tk.END, f"{hex_line:<100}", "hex")
                text_area.insert(tk.END, "   " + linha + "\n", "ascii")

            saida_atual.set("hex")
            lbl_modo.config(text="Modo atual: HEX + ASCII")
        except Exception as e:
            text_area.delete(1.0, tk.END)
            text_area.insert(tk.END, f"Erro ao converter: {e}")

# ---------------- Função de pesquisa com destaque ----------------
def pesquisar_strings():
    termo = entrada_pesquisa.get().strip()
    if not termo:
        return

    modo = saida_atual.get()
    resultados = []    

    if modo == "strings":
        resultados = [linha for linha in conteudo_strings if termo in linha]
    elif modo == "hex":
        resultados = [linha for linha in conteudo_hex if termo in linha]
    elif modo == "ip_porta":
        resultados = [ip for ip in conteudo_ip if termo in ip]
        resultados += [p for p in conteudo_porta if termo in p]
    else:
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, "Nenhum modo ativo. Selecione um modo primeiro.\n")
        return

    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, f"Resultados da Pesquisa: {termo}\n\n", "titulo")
    if resultados:
        for item in resultados:
            text_area.insert(tk.END, item + "\n")
    else:
        text_area.insert(tk.END, "Nada encontrado\n")

    text_area.tag_remove("destaque", "1.0", tk.END)

    start = "1.0"
    while True:
        pos = text_area.search(termo, start, stopindex=tk.END)
        if not pos:
            break
        end = f"{pos}+{len(termo)}c"
        text_area.tag_add("destaque", pos, end)
        start = end

# ---------------- Função para salvar resultados ----------------
def salvar_resultados():
    conteudo = text_area.get(1.0, tk.END).strip()
    if not conteudo:
        return
    arquivo_salvar = filedialog.asksaveasfilename(
        title="Salvar resultados como",
        defaultextension=".txt",
        filetypes=(("Arquivos de texto", "*.txt"),)
    )
    if arquivo_salvar:
        with open(arquivo_salvar, "w", encoding="utf-8") as f:
            f.write(conteudo)
        # Mensagem de confirmação
        messagebox.showinfo("Arquivo salvo", f"O arquivo foi salvo em\n\n{arquivo_salvar}")

# ---------------- Interface Tkinter ----------------
root = tk.Tk()
root.title("Strings Hex")
root.state('zoomed')

caminho_var = tk.StringVar()
saida_atual = tk.StringVar(value="")

frame_top = tk.Frame(root)
frame_top.pack(pady=5)

btn_abrir = tk.Button(frame_top, text="Selecionar Arquivo", bg="#03fc24", fg="black", command=abrir_arquivo)
btn_abrir.pack(side=tk.LEFT, padx=5)

btn_strings = tk.Button(frame_top, text="Mostrar todas as strings", bg="#07f5f5", fg="black", command=mostrar_todas_strings)
btn_strings.pack(side=tk.LEFT, padx=5)

btn_ip_porta = tk.Button(frame_top, text="Mostrar IP e Porta", bg="#073ff5", fg="white", command=mostrar_ip_porta)
btn_ip_porta.pack(side=tk.LEFT, padx=5)

btn_hex = tk.Button(frame_top, text="Mostrar em HEX + ASCII", bg="#f5b507", fg="black", command=mostrar_strings_hex)
btn_hex.pack(side=tk.LEFT, padx=5)

btn_salvar = tk.Button(frame_top, text="Salvar Resultados", bg="#f50756", fg="black", command=salvar_resultados)
btn_salvar.pack(side=tk.LEFT, padx=5)

label = tk.Label(root, text="Pesquisar Letras Minúsculas e Letras Maiúsculas", font=("Arial", 10, "bold"))
label.pack(pady=5)

frame_pesquisa = tk.Frame(root)
frame_pesquisa.pack(pady=5)

entrada_pesquisa = tk.Entry(frame_pesquisa, width=40)
entrada_pesquisa.pack(side=tk.LEFT, padx=5)

btn_pesquisar = tk.Button(frame_pesquisa, text="Pesquisar", command=pesquisar_strings)
btn_pesquisar.pack(side=tk.LEFT)

lbl_modo = tk.Label(root, text="Modo atual: Nenhum", font=("Arial", 10, "bold"))
lbl_modo.pack(pady=5)

text_area = scrolledtext.ScrolledText(root, width=150, height=48)
text_area.pack(padx=10, pady=10)

# ---------------- Tags de cores ----------------
text_area.tag_config("strings", foreground="black")
text_area.tag_config("hex", foreground="blue")
text_area.tag_config("ascii", foreground="black")
text_area.tag_config("titulo", foreground="green", font=("Arial", 10, "bold"))
text_area.tag_config("ip", foreground="purple")
text_area.tag_config("porta", foreground="red")
text_area.tag_config("destaque", foreground="red", font=("Arial", 10, "bold"))

root.mainloop()
