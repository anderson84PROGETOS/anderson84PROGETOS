import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import pikepdf
import os
import pyzipper
import time
import base64
import re

# Global variable for scan speed (in seconds)
scan_speed = 0.05  # Default: Rápido (0.05s)

def set_scan_speed(speed):
    global scan_speed
    if speed == "Rápido":
        scan_speed = 0.05
    elif speed == "Médio":
        scan_speed = 0.2
    elif speed == "Lento":
        scan_speed = 0.5

def load_wordlist(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        messagebox.showerror("Erro", "Erro ao abrir o wordlist.")
        return []

def detectar_tipo_hash(hash_str):
    tamanho = len(hash_str)
    if tamanho == 32:
        return 'md5'
    elif tamanho == 40:
        return 'sha1'
    elif tamanho == 64:
        return 'sha256'
    elif tamanho == 128:
        return 'sha512'
    else:
        return None

def update_label_testando(index, pwd):
    label_testando.config(text=f"Wordlist atual: Testando:       Número: {index:<20}    Senha: {pwd}")
    root.update_idletasks()
    time.sleep(scan_speed)  # Use global scan_speed variable

def try_crack_hash(target_hash, hash_func_name, passwords):
    for index, pwd in enumerate(passwords, start=1):
        update_label_testando(index, pwd)
        h = getattr(hashlib, hash_func_name)(pwd.encode()).hexdigest()
        if h == target_hash.lower():
            label_testando.config(text=f"Senha Encontrada: {pwd}")
            return pwd
    return None

def try_crack_pdf(pdf_path, passwords):
    for index, pwd in enumerate(passwords, start=1):
        update_label_testando(index, pwd)
        try:
            with pikepdf.open(pdf_path, password=pwd):
                label_testando.config(text=f"Senha Encontrada: {pwd}")
                return pwd
        except pikepdf._qpdf.PasswordError:
            continue
        except Exception:
            break
    return None

def try_crack_zip(zip_path, passwords):
    try:
        with pyzipper.AESZipFile(zip_path) as zf:
            for index, pwd in enumerate(passwords, start=1):
                update_label_testando(index, pwd)
                try:
                    zf.pwd = pwd.encode('utf-8')
                    zf.namelist()
                    with zf.open(zf.namelist()[0]) as f:
                        f.read(1)
                    label_testando.config(text=f"Senha Encontrada: {pwd}")
                    return pwd
                except Exception:
                    continue
    except Exception as e:
        print(f"Erro ao abrir ZIP: {e}")
    return None

def iniciar():
    wordlist_path = entry_wordlist.get()
    entradas = input_text.get("1.0", tk.END).strip().splitlines()
    if not wordlist_path or not entradas:
        messagebox.showwarning("Aviso", "Preencha todos os campos.")
        return
    passwords = load_wordlist(wordlist_path)
    label_palavras.config(text=f"Total de palavras na wordlist: {len(passwords)}")
    resultado_text.delete("1.0", tk.END)
    total_entradas = len(entradas)
    progress_bar["value"] = 0
    progress_bar["maximum"] = total_entradas
    resultado_text.insert(tk.END, f"[INFO] Total de entradas: {total_entradas}\n\n")
    resultado_text.insert(tk.END, "[INFO] Análise das Entradas\n\n")
    for idx, entrada in enumerate(entradas, start=1):
        entrada = entrada.strip()
        pwd = None
        info = f"[{idx}] Entrada: {entrada}\n"
        if os.path.isfile(entrada):
            lower = entrada.lower()
            if lower.endswith(".pdf"):
                info += " [*] Arquivo PDF Detectado\n"
                resultado_text.insert(tk.END, info)
                resultado_text.see(tk.END)
                root.update_idletasks()
                pwd = try_crack_pdf(entrada, passwords)
            elif lower.endswith(".zip"):
                info += " [*] Arquivo ZIP Detectado\n"
                resultado_text.insert(tk.END, info)
                resultado_text.see(tk.END)
                root.update_idletasks()
                pwd = try_crack_zip(entrada, passwords)
            else:
                info += " [*] Arquivo desconhecido\n"
                resultado_text.insert(tk.END, info)
                resultado_text.see(tk.END)
                root.update_idletasks()
        else:
            tipo = detectar_tipo_hash(entrada)
            if tipo:
                info += f" [*] Hash Detectado: {tipo.upper()}\n"
                resultado_text.insert(tk.END, info)
                resultado_text.see(tk.END)
                root.update_idletasks()
                pwd = try_crack_hash(entrada, tipo, passwords)
            else:
                info += " [*] Tipo de entrada não reconhecido\n"
                resultado_text.insert(tk.END, info)
                resultado_text.see(tk.END)
                root.update_idletasks()
        if pwd:
            resultado_text.insert(tk.END, f" [+] Senha Encontrada: {pwd}\n\n")
        else:
            resultado_text.insert(tk.END, f" [-] Senha Não Encontrada\n\n")
        resultado_text.see(tk.END)
        root.update_idletasks()
        progress_bar["value"] = idx
    label_testando.config(text="Wordlist atual: Finalizado.")

def iniciar_thread():
    btn_iniciar.config(bg="#03fc30", state=tk.DISABLED)
    threading.Thread(target=run_bruteforce_thread, daemon=True).start()

def run_bruteforce_thread():
    try:
        iniciar()
    finally:
        btn_iniciar.config(state=tk.NORMAL, bg="#059e07")

def selecionar_wordlist():
    file_path = filedialog.askopenfilename(filetypes=[("Arquivos TXT", "*.txt")])
    if file_path:
        entry_wordlist.delete(0, tk.END)
        entry_wordlist.insert(0, file_path)
        passwords = load_wordlist(file_path)
        label_palavras.config(text=f"Total de palavras na wordlist: {len(passwords)}")

def selecionar_arquivo_hashes():
    file_path = filedialog.askopenfilename(filetypes=[("Arquivos TXT", "*.txt")])
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                conteudo = f.read()
                input_text.delete("1.0", tk.END)
                input_text.insert(tk.END, conteudo)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler o arquivo de hashes:\n{e}")

def adicionar_arquivo():
    path = filedialog.askopenfilename(filetypes=[("Arquivos Suportados", "*.pdf *.zip")])
    if path:
        input_text.insert(tk.END, path + "\n")

def salvar_resultados():
    conteudo = resultado_text.get("1.0", tk.END)
    if "[+] Senha Encontrada:" not in conteudo:
        messagebox.showinfo("Info", "Nenhuma senha encontrada para salvar.")
        return
    caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texto", "*.txt")])
    if caminho:
        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            messagebox.showinfo("Sucesso", "Resultados salvos com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{e}")

def gerar_hash(algoritmo):
    entrada = entrada_gerar_hash.get()
    if not entrada.strip():
        messagebox.showwarning("Aviso", "Digite uma senha para gerar hash.")
        return
    h = getattr(hashlib, algoritmo)(entrada.encode()).hexdigest()
    saida_hash.delete("1.0", tk.END)
    saida_hash.insert(tk.END, f"{algoritmo.upper()}\n\n{h}")

def hex_para_bytes(hex_str):
    hex_str = hex_str.replace(":", "").replace("\n", "").replace(" ", "")
    try:
        return bytes.fromhex(hex_str)
    except ValueError:
        return None

def analisar_hex():
    entrada = caixa_hex.get("1.0", tk.END).strip()
    dados = hex_para_bytes(entrada)
    if not dados:
        messagebox.showerror("Erro", "Hexadecimal inválido!")
        return
    base64_str = base64.b64encode(dados).decode()
    ascii_legivel = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in dados)
    caixa_base64.config(state=tk.NORMAL)
    caixa_base64.delete("1.0", tk.END)
    caixa_base64.insert(tk.END, base64_str)
    caixa_base64.config(state=tk.DISABLED)
    caixa_ascii.config(state=tk.NORMAL)
    caixa_ascii.delete("1.0", tk.END)
    caixa_ascii.insert(tk.END, ascii_legivel)
    caixa_ascii.config(state=tk.DISABLED)
    botao_salvar_hex["state"] = tk.NORMAL

def salvar_txt():
    base64_str = caixa_base64.get("1.0", tk.END).strip()
    ascii_str = caixa_ascii.get("1.0", tk.END).strip()
    conteudo = (
        "=== Assinatura Digital (Base64) ===\n\n" +
        base64_str + "\n\n" +
        "\n=== ASCII Legível ===\n\n" +
        ascii_str + "\n"
    )
    caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo Texto", "*.txt")])
    if caminho:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        messagebox.showinfo("Salvo", f"\nArquivo salvo em: {caminho}")

def abrir_arquivo_hex_analisador():
    caminho = filedialog.askopenfilename(filetypes=[("Arquivos Texto", "*.txt")])
    if not caminho:
        return
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
            caixa_hex.delete("1.0", tk.END)
            caixa_hex.insert(tk.END, conteudo.strip())
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao abrir arquivo:\n{str(e)}")

def decode_base64_content(content):
    try:
        cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', content)
        remainder = len(cleaned) % 4
        if remainder == 1:
            cleaned = cleaned[:-1]
        elif remainder > 0:
            cleaned += '=' * (4 - remainder)
        decoded_bytes = base64.b64decode(cleaned)
        return decoded_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        return f"❌ Erro na decodificação: {str(e)}"

def decode_base64():
    text = input_text_base64.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Aviso", "Digite ou cole algum texto Base64.")
        return
    linhas = text.splitlines()
    resultados = []
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        resultado = decode_base64_content(linha)
        resultados.append(resultado)
    output_text_base64.delete("1.0", tk.END)
    output_text_base64.insert(tk.END, "\n\n".join(resultados))

def decode_file():
    file_path = filedialog.askopenfilename(
        title="Abrir arquivo .txt com Base64",
        filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
    )
    if not file_path:
        return
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        resultados = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            resultado = decode_base64_content(line)
            resultados.append(resultado)
        output_text_base64.delete("1.0", tk.END)
        output_text_base64.insert(tk.END, "\n\n".join(resultados))
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir ou ler o arquivo:\n{e}")

def encode_file():
    file_path = filedialog.askopenfilename(
        title="Abrir arquivo para codificar em Base64",
        filetypes=[("Todos os arquivos", "*.*")]
    )
    if not file_path:
        return
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        encoded = base64.b64encode(file_bytes).decode('utf-8')
        output_text_base64.delete("1.0", tk.END)
        output_text_base64.insert(tk.END, encoded)
        messagebox.showinfo("Sucesso", "Arquivo codificado em Base64 com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir ou codificar o arquivo:\n{e}")

def encode_base64():
    text = input_text_base64.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Aviso", "Digite um texto para codificar.")
        return
    try:
        encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        output_text_base64.delete("1.0", tk.END)
        output_text_base64.insert(tk.END, encoded)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao codificar o texto:\n{e}")

def save_encoded_base64():
    text = input_text_base64.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Aviso", "Digite um texto para codificar.")
        return
    try:
        encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt")],
            title="Salvar como"
        )
        if not file_path:
            return
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(encoded)
        messagebox.showinfo("Sucesso", f"Texto codificado salvo em:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{e}")

def mostrar_erro_personalizado(titulo, mensagem):
    erro_win = tk.Toplevel(root)
    erro_win.title(titulo)
    erro_win.geometry("400x200")
    erro_win.configure(bg="white")
    erro_win.resizable(False, False)
    label_titulo = tk.Label(erro_win, text=titulo, font=("Arial", 14, "bold"), fg="red", bg="white")
    label_titulo.pack(pady=10)
    label_mensagem = tk.Label(erro_win, text=mensagem, font=("Arial", 12), wraplength=360, bg="white")
    label_mensagem.pack(pady=10)
    botao_ok = tk.Button(erro_win, text="OK", command=erro_win.destroy, font=("Arial", 11), bg="#05fc32", fg="black")
    botao_ok.pack(pady=10)
    erro_win.transient(root)
    erro_win.grab_set()
    root.wait_window(erro_win)

def converter_para_hex():
    texto = entrada_texto_hex.get("1.0", tk.END).rstrip('\n')
    if not texto.strip():
        messagebox.showwarning("Aviso", "Digite algum texto.")
        return
    resultado_hex = ' '.join(f"{b:02X}" for b in texto.encode("utf-8"))
    texto_resultado_hex.delete("1.0", tk.END)
    texto_resultado_hex.insert(tk.END, resultado_hex)

def abrir_arquivo_hex_thread():
    threading.Thread(target=abrir_arquivo_hex, daemon=True).start()

def abrir_arquivo_hex():
    caminho = filedialog.askopenfilename(filetypes=[("Todos os arquivos", "*.*")])
    if not caminho:
        return
    try:
        tamanho_arquivo = os.path.getsize(caminho)
        if tamanho_arquivo == 0:
            messagebox.showinfo("Info", "Arquivo vazio.")
            return
        def reset_interface():
            hex_viewer.delete("1.0", tk.END)
            progresso_hex['value'] = 0
        root.after(0, reset_interface)
        with open(caminho, "rb") as f:
            bytes_lidos = 0
            bloco_tamanho = 4096
            while True:
                bloco = f.read(bloco_tamanho)
                if not bloco:
                    break
                linhas = []
                for i in range(0, len(bloco), 16):
                    segmento = bloco[i:i+16]
                    hex_part = ' '.join(f"{byte:02X}" for byte in segmento)
                    texto_legivel = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in segmento)
                    linha = f"{hex_part:<48}  {texto_legivel}\n"
                    linhas.append(linha)
                texto_para_inserir = ''.join(linhas)
                bytes_lidos += len(bloco)
                progresso_atual = (bytes_lidos / tamanho_arquivo) * 100
                def atualizar_interface():
                    hex_viewer.insert(tk.END, texto_para_inserir)
                    progresso_hex['value'] = progresso_atual
                root.after(0, atualizar_interface)
        def progresso_final():
            progresso_hex['value'] = 100
        root.after(0, progresso_final)
    except Exception as e:
        def mostra_erro():
            mostrar_erro_personalizado("Erro", f"Erro ao abrir arquivo:\n{e}")
        root.after(0, mostra_erro)

def abrir_arquivo_hex_texto_thread():
    threading.Thread(target=abrir_arquivo_hex_texto, daemon=True).start()

def abrir_arquivo_hex_texto():
    caminho = filedialog.askopenfilename(filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")])
    if not caminho:
        return
    try:
        tamanho_arquivo = os.path.getsize(caminho)
        if tamanho_arquivo == 0:
            messagebox.showinfo("Info", "Arquivo vazio.")
            return
        def reset_interface():
            hex_texto_entrada.delete("1.0", tk.END)
            texto_decodificado.delete("1.0", tk.END)
            progresso_texto_hex['value'] = 0
        root.after(0, reset_interface)
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()
            if not conteudo:
                messagebox.showinfo("Info", "Arquivo vazio ou sem conteúdo válido.")
                return
            conteudo_limpo = conteudo.replace(" ", "").replace("\n", "").upper()
            if len(conteudo_limpo) % 2 != 0:
                raise ValueError("Hexadecimal incompleto (quantidade ímpar de caracteres).")
            conteudo_formatado = ' '.join(conteudo_limpo[i:i+2] for i in range(0, len(conteudo_limpo), 2))
            def atualizar_entrada():
                hex_texto_entrada.insert(tk.END, conteudo_formatado)
            root.after(0, atualizar_entrada)
            try:
                decoded_bytes = bytes.fromhex(conteudo_limpo)
                decoded_text = decoded_bytes.decode("utf-8")
                def atualizar_resultado():
                    texto_decodificado.delete("1.0", tk.END)
                    texto_decodificado.insert(tk.END, decoded_text)
                    progresso_texto_hex['value'] = 100
                root.after(0, atualizar_resultado)
            except ValueError:
                def erro_decodificacao():
                    mostrar_erro_personalizado("Erro", "O conteúdo do arquivo não é um hexadecimal válido.")
                root.after(0, erro_decodificacao)
            except UnicodeDecodeError:
                def erro_unicode():
                    mostrar_erro_personalizado("Erro", "Não foi possível decodificar o hexadecimal para texto UTF-8.")
                root.after(0, erro_unicode)
    except Exception as e:
        def mostra_erro():
            pass
        root.after(0, mostra_erro)

# GUI
root = tk.Tk()
root.title("Multi-Tool: Brute Force, Hash, Base64, Hex")
root.geometry("1280x950")
root.wm_state('zoomed')

# Notebook com abas
abas = ttk.Notebook(root)
abas.pack(fill="both", expand=True)

# Aba 1 - Brute Force
aba1 = tk.Frame(abas)
abas.add(aba1, text="Brute Force Hash/PDF/ZIP")

tk.Label(aba1, text="Hashes ou Arquivos").pack()
frame_hashes = tk.Frame(aba1)
frame_hashes.pack()
tk.Button(frame_hashes, text="Selecionar Arquivo de Hashes", command=selecionar_arquivo_hashes, bg="#c7ffb6").pack(side=tk.LEFT, padx=5, pady=10)
tk.Button(frame_hashes, text="Selecionar PDF/ZIP", command=adicionar_arquivo, bg="#fa5f9a").pack(side=tk.LEFT, padx=5, pady=10)
input_text = scrolledtext.ScrolledText(aba1, width=145, height=10)
input_text.pack()
tk.Label(aba1, text="Wordlist (.txt)").pack()
frame_wordlist = tk.Frame(aba1)
frame_wordlist.pack()
entry_wordlist = tk.Entry(frame_wordlist, width=96)
entry_wordlist.pack(side=tk.LEFT)
tk.Button(frame_wordlist, text="Selecionar", command=selecionar_wordlist, bg="#03f4fc").pack(side=tk.LEFT, padx=10)
label_palavras = tk.Label(aba1, text="Total de palavras na wordlist: 0")
label_palavras.pack(pady=5)
# Speed control dropdown
frame_speed = tk.Frame(aba1)
frame_speed.pack(pady=5)
tk.Label(frame_speed, text="Velocidade do Scan:").pack(side=tk.LEFT)
speed_var = tk.StringVar(value="Rápido")
speed_menu = ttk.Combobox(frame_speed, textvariable=speed_var, values=["Rápido", "Médio", "Lento"], state="readonly", width=10)
speed_menu.pack(side=tk.LEFT, padx=5)
speed_menu.bind("<<ComboboxSelected>>", lambda event: set_scan_speed(speed_var.get()))
btn_iniciar = tk.Button(aba1, text="Iniciar Brute Force", command=iniciar_thread, bg="#059e07", fg="black")
btn_iniciar.pack(pady=10)
btn_salvar = tk.Button(aba1, text="Salvar Senhas Encontradas", command=salvar_resultados, bg="#eda705", fg="black")
btn_salvar.pack(pady=5)
progress_bar = ttk.Progressbar(aba1, orient="horizontal", length=600, mode="determinate")
progress_bar.pack(pady=5)
label_testando = tk.Label(aba1, text="Wordlist atual: Aguardando...", fg="blue", font=("Arial", 10, "bold"))
label_testando.pack(pady=3)
tk.Label(aba1, text="Resultado").pack()
resultado_text = scrolledtext.ScrolledText(aba1, width=145, height=14)
resultado_text.pack()
tk.Label(aba1, text="Gerar Hash de uma Senha", font=("Arial", 12, "bold")).pack(pady=8)
frame_hash = tk.Frame(aba1)
frame_hash.pack()
entrada_gerar_hash = tk.Entry(frame_hash, width=60)
entrada_gerar_hash.pack(side=tk.LEFT, padx=5)
frame_botoes_hash = tk.Frame(aba1)
frame_botoes_hash.pack(pady=5)
tk.Button(frame_botoes_hash, text="Gerar MD5", command=lambda: gerar_hash("md5"), bg="#d0c4fc").pack(side=tk.LEFT, padx=5)
tk.Button(frame_botoes_hash, text="Gerar SHA1", command=lambda: gerar_hash("sha1"), bg="#c4fce8").pack(side=tk.LEFT, padx=5)
tk.Button(frame_botoes_hash, text="Gerar SHA256", command=lambda: gerar_hash("sha256"), bg="#fcd7c4").pack(side=tk.LEFT, padx=5)
tk.Button(frame_botoes_hash, text="Gerar SHA512", command=lambda: gerar_hash("sha512"), bg="#fbc4f7").pack(side=tk.LEFT, padx=5)
saida_hash = tk.Text(aba1, width=146, height=4, fg="blue")
saida_hash.pack(pady=5)

# Aba 2 - Analisador de Assinatura Digital
aba2 = tk.Frame(abas)
abas.add(aba2, text="Analisador de Assinatura Hex")

tk.Label(aba2, text="Cole ou abra a Assinatura Hexadecimal", font=("Arial", 12)).pack(pady=5)
frame_botoes_hex = tk.Frame(aba2)
frame_botoes_hex.pack(pady=5)
tk.Button(frame_botoes_hex, text="📂 Abrir Arquivo .txt", command=abrir_arquivo_hex_analisador, bg="#FF9800", fg="black", font=("Arial", 11)).pack(side=tk.LEFT, padx=10)
tk.Button(frame_botoes_hex, text="🔍 Analisar", command=analisar_hex, bg="#06c91a", fg="black", font=("Arial", 11, "bold")).pack(side=tk.LEFT)
botao_salvar_hex = tk.Button(frame_botoes_hex, text="💾 Salvar Resultado", command=salvar_txt, bg="#2196F3", fg="black", font=("Arial", 11, "bold"))
botao_salvar_hex.pack(side=tk.LEFT, padx=10, pady=10)
botao_salvar_hex["state"] = tk.DISABLED
tk.Label(aba2, text="Entrada Hexadecimal", font=("Arial", 11, "bold")).pack()
caixa_hex = scrolledtext.ScrolledText(aba2, height=15, font=("Courier", 10), bg="#ffffff", fg="#000000", wrap=tk.WORD)
caixa_hex.pack(fill="both", padx=10, pady=5, expand=False)
tk.Label(aba2, text="Assinatura em Base64", font=("Arial", 11, "bold")).pack()
caixa_base64 = scrolledtext.ScrolledText(aba2, height=15, font=("Courier", 10), bg="#eeeeee", fg="#000000", wrap=tk.WORD)
caixa_base64.pack(fill="both", padx=10, pady=5, expand=False)
caixa_base64.config(state=tk.DISABLED)
tk.Label(aba2, text="Texto ASCII legível", font=("Arial", 11, "bold")).pack()
caixa_ascii = scrolledtext.ScrolledText(aba2, height=12, font=("Courier", 10), bg="#eeeeee", fg="#000000", wrap=tk.WORD)
caixa_ascii.pack(fill="both", padx=10, pady=5, expand=False)
caixa_ascii.config(state=tk.DISABLED)

# Aba 3 - Codificador/Decodificador Base64
aba3 = tk.Frame(abas)
abas.add(aba3, text="Codificador/Decodificador Base64")

tk.Label(aba3, text="Texto Base64 ou Texto Normal").pack(pady=5)
input_text_base64 = tk.Text(aba3, width=120, height=23)
input_text_base64.pack()
frame_buttons_base64 = tk.Frame(aba3)
frame_buttons_base64.pack(pady=10)
tk.Button(frame_buttons_base64, text="Decodificar Base64", command=decode_base64, bg="#fccf05", fg="black").grid(row=0, column=0, padx=5)
tk.Button(frame_buttons_base64, text="Codificar Arquivo para Base64", command=encode_file, bg="#05c3fc", fg="black").grid(row=0, column=1, padx=5)
tk.Button(frame_buttons_base64, text="Codificar Texto para Base64", command=encode_base64, bg="#fc035e", fg="black").grid(row=0, column=2, padx=5)
tk.Button(frame_buttons_base64, text="Salvar Texto Codificado em .txt", command=save_encoded_base64, bg="#fc5895", fg="black").grid(row=0, column=3, padx=5)
tk.Button(frame_buttons_base64, text="Decodificar de Arquivo Base64 .txt", command=decode_file, bg="#05fc3f", fg="black").grid(row=0, column=4, padx=5, pady=5)
tk.Label(aba3, text="Resultado").pack()
output_text_base64 = tk.Text(aba3, width=120, height=23)
output_text_base64.pack()

# Aba 4 - Conversor de Texto e Hexadecimal
aba4 = tk.Frame(abas)
abas.add(aba4, text="Conversor de Texto e Hex")

label_texto_hex = tk.Label(aba4, text="Digite seu texto", font=("Arial", 12))
label_texto_hex.pack(pady=10)
frame_entrada_hex = tk.Frame(aba4)
frame_entrada_hex.pack()
entrada_texto_hex = tk.Text(frame_entrada_hex, width=115, height=6, font=("Arial", 12))
entrada_texto_hex.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scroll_entrada_hex = tk.Scrollbar(frame_entrada_hex, command=entrada_texto_hex.yview)
scroll_entrada_hex.pack(side=tk.RIGHT, fill=tk.Y)
entrada_texto_hex.config(yscrollcommand=scroll_entrada_hex.set)
botao_texto_hex = tk.Button(aba4, text="Converter", bg="#05fc32", fg="black", command=converter_para_hex, font=("Arial", 12))
botao_texto_hex.pack(pady=10)
label_resultado_hex = tk.Label(aba4, text="Texto em Hexadecimal", font=("Arial", 12, "bold"))
label_resultado_hex.pack()
frame_resultado_hex = tk.Frame(aba4)
frame_resultado_hex.pack()
scrollbar_hex = tk.Scrollbar(frame_resultado_hex)
scrollbar_hex.pack(side=tk.RIGHT, fill=tk.Y)
texto_resultado_hex = tk.Text(frame_resultado_hex, width=130, height=6, wrap=tk.WORD, yscrollcommand=scrollbar_hex.set, font=("Courier", 10), fg="green")
texto_resultado_hex.pack(side=tk.LEFT)
scrollbar_hex.config(command=texto_resultado_hex.yview)
frame_botao_hex = tk.Frame(aba4)
frame_botao_hex.pack(pady=5)
botao_abrir_hex = tk.Button(frame_botao_hex, text="Abrir Arquivo (qualquer tipo)", bg="#03fce3", fg="black", command=abrir_arquivo_hex_thread, font=("Arial", 12))
botao_abrir_hex.pack(pady=5)
progresso_hex = ttk.Progressbar(aba4, orient='horizontal', mode='determinate', length=500)
progresso_hex.pack(pady=5)
frame_hex_viewer = tk.Frame(aba4)
frame_hex_viewer.pack(padx=10, pady=5)
scroll_hex_viewer = tk.Scrollbar(frame_hex_viewer)
scroll_hex_viewer.pack(side=tk.RIGHT, fill=tk.Y)
hex_viewer = tk.Text(frame_hex_viewer, wrap=tk.NONE, width=130, height=6, font=("Courier", 10), yscrollcommand=scroll_hex_viewer.set)
hex_viewer.pack(pady=5)
scroll_hex_viewer.config(command=hex_viewer.yview)
label_hex_entrada = tk.Label(aba4, text="Conteúdo Hexadecimal do Arquivo", font=("Arial", 12))
label_hex_entrada.pack(pady=5)
frame_hex_texto = tk.Frame(aba4)
frame_hex_texto.pack(padx=10, pady=5)
scroll_hex_texto = tk.Scrollbar(frame_hex_texto)
scroll_hex_texto.pack(side=tk.RIGHT, fill=tk.Y)
hex_texto_entrada = tk.Text(frame_hex_texto, wrap=tk.WORD, width=130, height=6, font=("Courier", 10), yscrollcommand=scroll_hex_texto.set)
hex_texto_entrada.pack(pady=5)
scroll_hex_texto.config(command=hex_texto_entrada.yview)
label_texto_decodificado = tk.Label(aba4, text="Texto Decodificado", font=("Arial", 12, "bold"))
label_texto_decodificado.pack(pady=5)
frame_texto_decodificado = tk.Frame(aba4)
frame_texto_decodificado.pack(padx=10, pady=5)
scroll_texto_decodificado = tk.Scrollbar(frame_texto_decodificado)
scroll_texto_decodificado.pack(side=tk.RIGHT, fill=tk.Y)
texto_decodificado = tk.Text(frame_texto_decodificado, wrap=tk.WORD, width=130, height=6, font=("Courier", 10), fg="green", yscrollcommand=scroll_texto_decodificado.set)
texto_decodificado.pack(pady=5)
scroll_texto_decodificado.config(command=texto_decodificado.yview)
botao_abrir_texto_hex = tk.Button(frame_botao_hex, text="Abrir Arquivo de Texto em Hexadecimal (.txt)", bg="#fcca03", fg="black", command=abrir_arquivo_hex_texto_thread, font=("Arial", 12))
botao_abrir_texto_hex.pack()
progresso_texto_hex = ttk.Progressbar(aba4, orient='horizontal', mode='determinate', length=500)
progresso_texto_hex.pack(pady=10)

root.mainloop()
