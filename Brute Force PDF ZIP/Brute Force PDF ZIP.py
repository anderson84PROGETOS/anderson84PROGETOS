import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import zipfile
import pyzipper
import pikepdf
import os
import threading

def inspect_file(path):
    """
    Retorna: (is_encrypted: bool, info_str: str, file_type: 'zip'|'pdf'|'unknown', is_aes: bool)
    """
    info = ""
    is_encrypted = False
    is_aes = False
    file_type = "unknown"
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".zip":
            file_type = "zip"
            with zipfile.ZipFile(path) as zf:
                info += "Arquivo: ZIP\n\n"
                entries = zf.infolist()
                info += f"Entradas no ZIP: {len(entries)}\n\n"
                # detecta criptografia: flag_bits & 0x1 indica que a entrada é criptografada
                encrypted_flags = any(e.flag_bits & 0x1 for e in entries)
                is_encrypted = encrypted_flags
                # detectar possível AES (algumas libs usam compress_type 99)
                is_aes = any(e.compress_type == 99 for e in entries)
                info += f"ZIP criptografado: {'Sim' if is_encrypted else 'Não detectado'}\n\n"
                info += f"Possível AES (requere pyzipper): {'Sim' if is_aes else 'Não'}\n\n"

        elif ext == ".pdf":
            file_type = "pdf"
            info += "Arquivo: PDF\n"
            try:
                # tenta abrir sem senha — se falhar e a mensagem indicar senha, tratamos como protegido
                pikepdf.Pdf.open(path)
                is_encrypted = False
                info += "\nPDF protegido por senha: Não\n\n"
            except Exception as e:
                msg = str(e).lower()
                # se a mensagem indicar senha/encryption → está protegido
                if ("password" in msg) or ("encrypted" in msg) or ("permission denied" in msg) or ("need a password" in msg) or ("needs a password" in msg):
                    is_encrypted = True
                    info += "\nPDF protegido por senha: Sim\n\n"
                else:
                    # outro erro (arquivo corrompido, inválido, etc.)
                    info += f"\nErro ao ler PDF (pode estar corrompido ou inválido): {e}\n\n"
                    # Se quiser tratar como inválido em vez de protegido, deixamos is_encrypted False.
                    # Mantemos is_encrypted False para não entrar em tentativa de cracking em PDFs corrompidos.
        else:
            info += "\nTipo de arquivo não suportado. Selecione ZIP ou PDF.\n\n"
    except Exception as e:
        return False, f"Erro ao inspecionar arquivo: {e}\n", "unknown", False

    return is_encrypted, info, file_type, is_aes

def load_wordlist(wordlist_path):
    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip()]
        return passwords, None
    except Exception as e:
        return None, f"\nErro ao carregar wordlist: {e}\n"

def try_crack(path, passwords, result_text, progress_bar, status_label):
    is_encrypted, inspect_result, file_type, is_aes = inspect_file(path)
    result_text.insert(tk.END, inspect_result)
    result_text.see(tk.END)
    root.update_idletasks()

    if not is_encrypted:
        result_text.insert(tk.END, "[-] Arquivo não parece estar criptografado ou é inválido para teste.\n", "error")
        status_label.config(text="Arquivo inválido ou não criptografado")
        return None

    result_text.insert(tk.END, f"[*] Tipo de arquivo Detectado: {file_type.upper()}\n\n")
    if file_type == "zip":
        result_text.insert(tk.END, f"\n[*] Usando {'AES (pyzipper)' if is_aes else 'ZipCrypto (zipfile)'} para tentativa.\n\n")
    result_text.see(tk.END)
    root.update_idletasks()

    total_passwords = len(passwords)
    progress_bar["maximum"] = total_passwords

    for index, pwd in enumerate(passwords, start=1):
        status_label.config(text=f"Testando senha {index}/{total_passwords}: {pwd}")
        result_text.insert(tk.END, f"Testando senha: {pwd}\n")
        result_text.see(tk.END)
        root.update_idletasks()

        try:
            if file_type == "zip":
                # Zip: se is_aes -> pyzipper.AESZipFile, caso contrário zipfile.ZipFile com pwd ao abrir cada arquivo
                try:
                    if is_aes:
                        with pyzipper.AESZipFile(path) as zf:
                            # define a senha (bytes)
                            zf.pwd = pwd.encode('utf-8')
                            names = zf.namelist()
                            if not names:
                                continue
                            # tentar abrir cada arquivo (valida conteúdo)
                            success = True
                            for name in names:
                                try:
                                    with zf.open(name) as f:
                                        while f.read(1024 * 64):
                                            pass
                                except RuntimeError:
                                    success = False
                                    break
                            if success:
                                result_text.insert(tk.END, f"\n[+] Senha Encontrada para ZIP (AES): {pwd}\n", "success")
                                progress_bar["value"] = total_passwords
                                status_label.config(text=f"Senha Encontrada: {pwd}")
                                return pwd
                    else:
                        # ZipCrypto (zipfile)
                        with zipfile.ZipFile(path) as zf:
                            names = zf.namelist()
                            if not names:
                                continue
                            success = True
                            for name in names:
                                try:
                                    # ao abrir, passamos pwd em bytes
                                    with zf.open(name, pwd=pwd.encode('utf-8')) as f:
                                        while f.read(1024 * 64):
                                            pass
                                except RuntimeError:
                                    # senha errada possivelmente
                                    success = False
                                    break
                                except zipfile.BadZipFile:
                                    success = False
                                    break
                                except Exception:
                                    # pode lançar RuntimeError ou outros; tratamos como falha de senha
                                    success = False
                                    break
                            if success:
                                result_text.insert(tk.END, f"\n[+] Senha encontrada para ZIP (ZipCrypto): {pwd}\n", "success")
                                progress_bar["value"] = total_passwords
                                status_label.config(text=f"Senha encontrada: {pwd}")
                                return pwd
                except Exception:
                    # ignora e continua com a próxima senha
                    pass

            elif file_type == "pdf":
                try:
                    # tenta abrir com senha; se abrir -> senha correta
                    # pikepdf levanta exceção quando a senha é inválida
                    pdf = pikepdf.Pdf.open(path, password=pwd)
                    pdf.close()
                    result_text.insert(tk.END, f"\n[+] Senha Encontrada para PDF: {pwd}\n", "success")
                    progress_bar["value"] = total_passwords
                    status_label.config(text=f"Senha Encontrada: {pwd}")
                    return pwd
                except Exception:
                    # senha errada ou outro problema -> continuar
                    pass

            else:
                result_text.insert(tk.END, "Tipo de arquivo não suportado para cracking.\n", "error")
                return None

        finally:
            progress_bar["value"] = index

    result_text.insert(tk.END, "\n[-] Nenhuma Senha Encontrada na wordlist\n", "error")
    status_label.config(text="Nenhuma senha encontrada")
    return None

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("ZIP ou PDF", "*.zip *.pdf")])
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)
        result_text.delete(1.0, tk.END)
        status_label.config(text="Arquivo selecionado. Aguardando wordlist e início.")

def select_wordlist():
    wordlist_path = filedialog.askopenfilename(filetypes=[("Arquivos TXT", "*.txt")])
    if wordlist_path:
        entry_wordlist.delete(0, tk.END)
        entry_wordlist.insert(0, wordlist_path)
        passwords, error = load_wordlist(wordlist_path)
        if error:
            messagebox.showerror("Erro", error)
            result_text.insert(tk.END, error, "error")
        else:
            wordlist_count.config(text=f"Total de senhas na wordlist: {len(passwords)}")
            result_text.delete(1.0, tk.END)
            status_label.config(text="Wordlist selecionada. Clique em: Iniciar Cracking")

def start_cracking():
    path = entry_file.get()
    wordlist_path = entry_wordlist.get()
    if not path or not os.path.isfile(path):
        messagebox.showwarning("Aviso", "Selecione um arquivo (ZIP ou PDF) válido.")
        return
    if not wordlist_path or not os.path.isfile(wordlist_path):
        messagebox.showwarning("Aviso", "Selecione um arquivo de wordlist válido.")
        return

    passwords, error = load_wordlist(wordlist_path)
    if error:
        messagebox.showerror("Erro", error)
        result_text.insert(tk.END, error, "error")
        return

    btn_start.config(state=tk.DISABLED, bg="#cccccc")
    result_text.delete(1.0, tk.END)
    progress_bar["value"] = 0
    threading.Thread(target=run_cracking_thread, args=(path, passwords), daemon=True).start()

def run_cracking_thread(path, passwords):
    try:
        try_crack(path, passwords, result_text, progress_bar, status_label)
    finally:
        btn_start.config(state=tk.NORMAL, bg="#03fc30")

found_password = None  # variável global para armazenar a senha encontrada

def try_crack(path, passwords, result_text, progress_bar, status_label):
    global found_password
    found_password = None  # reset
    is_encrypted, inspect_result, file_type, is_aes = inspect_file(path)
    result_text.insert(tk.END, inspect_result)
    result_text.see(tk.END)
    root.update_idletasks()

    if not is_encrypted:
        result_text.insert(tk.END, "[-] Arquivo não parece estar criptografado ou é inválido para teste.\n", "error")
        status_label.config(text="Arquivo inválido ou não criptografado")
        return None

    total_passwords = len(passwords)
    progress_bar["maximum"] = total_passwords

    for index, pwd in enumerate(passwords, start=1):
        status_label.config(text=f"Testando senha {index}/{total_passwords}: {pwd}")
        result_text.insert(tk.END, f"Testando senha: {pwd}\n")
        result_text.see(tk.END)
        root.update_idletasks()

        try:
            if file_type == "zip":
                try:
                    with pyzipper.AESZipFile(path) if is_aes else zipfile.ZipFile(path) as zf:
                        names = zf.namelist()
                        if not names:
                            continue
                        success = True
                        for name in names:
                            try:
                                if is_aes:
                                    zf.pwd = pwd.encode('utf-8')
                                    with zf.open(name) as f:
                                        while f.read(1024 * 64):
                                            pass
                                else:
                                    with zf.open(name, pwd=pwd.encode('utf-8')) as f:
                                        while f.read(1024 * 64):
                                            pass
                            except Exception:
                                success = False
                                break
                        if success:
                            found_password = pwd
                            result_text.insert(tk.END, f"\n[+] Senha encontrada: {pwd}\n", "success")
                            status_label.config(text=f"Senha encontrada: {pwd}")
                            btn_save_password.config(state=tk.NORMAL)
                            progress_bar["value"] = total_passwords
                            return pwd
                except Exception:
                    pass

            elif file_type == "pdf":
                try:
                    pdf = pikepdf.Pdf.open(path, password=pwd)
                    n_pages = len(pdf.pages)  # força verificação
                    pdf.close()
                    found_password = pwd
                    result_text.insert(tk.END, f"\n[+] Senha encontrada para PDF: {pwd}\n", "success")
                    status_label.config(text=f"Senha encontrada: {pwd}")
                    btn_save_password.config(state=tk.NORMAL)
                    progress_bar["value"] = total_passwords
                    return pwd
                except Exception:
                    pass
        finally:
            progress_bar["value"] = index

    result_text.insert(tk.END, "\n[-] Nenhuma senha encontrada na wordlist\n", "error")
    status_label.config(text="Nenhuma senha encontrada")
    return None

# Função para salvar senha em .txt
def save_password():
    global found_password
    if not found_password:
        messagebox.showwarning("Aviso", "Nenhuma senha encontrada para salvar.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")], title="Salvar Senha")
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Senha: {found_password}")  # adiciona prefixo "Senha: "
            messagebox.showinfo("Sucesso", f"Senha salva em: {file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar senha: {e}")

# GUI Setup
root = tk.Tk()
root.title("Cracker de Senha - ZIP / PDF")
root.geometry("810x890")

# File Selection (ZIP/PDF)
frame_file = tk.Frame(root)
frame_file.pack(pady=10)
tk.Label(frame_file, text="Arquivo (ZIP ou PDF):", font=("Arial", 10)).pack(side=tk.LEFT)
entry_file = tk.Entry(frame_file, width=60)
entry_file.pack(side=tk.LEFT, padx=5)
tk.Button(frame_file, text="Selecionar Arquivo", command=select_file, bg="#03f4fc").pack(side=tk.LEFT)

# Wordlist Selection
frame_wordlist = tk.Frame(root)
frame_wordlist.pack(pady=10)
tk.Label(frame_wordlist, text="Wordlist (.txt):", font=("Arial", 10)).pack(side=tk.LEFT)
entry_wordlist = tk.Entry(frame_wordlist, width=67)
entry_wordlist.pack(side=tk.LEFT, padx=5)
tk.Button(frame_wordlist, text="Selecionar Wordlist", command=select_wordlist, bg="#f5f507").pack(side=tk.LEFT)

# Wordlist Count
wordlist_count = tk.Label(root, text="Total de senhas na wordlist: 0", font=("Arial", 10))
wordlist_count.pack(pady=5)

# Start Button
btn_start = tk.Button(root, text="Iniciar Cracking", command=start_cracking, bg="#03fc30", font=("Arial", 10))
btn_start.pack(pady=10)

# Botão para salvar senha (apenas habilitado após encontrar)
btn_save_password = tk.Button(root, text="Salvar Senha", command=save_password, bg="#f79e02", font=("Arial", 10), state=tk.DISABLED)
btn_save_password.pack(pady=10)

# Progress Bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(pady=10)

# Status Label
status_label = tk.Label(root, text="Aguardando ação...", font=("Arial", 10, "bold"), fg="blue")
status_label.pack(pady=5)

# Result Text Area
tk.Label(root, text="Resultados", font=("Arial", 10)).pack()
result_text = scrolledtext.ScrolledText(root, width=90, height=33, font=("Courier", 10))
result_text.pack(padx=10, pady=10)
result_text.tag_config("success", foreground="green", font=("Courier", 10, "bold"))
result_text.tag_config("error", foreground="red")

# Run the GUI
root.mainloop()
