import os
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, ttk
import winreg

stop_flag = False  # Flag para parar a verificação

# ---------------- Funções Utilitárias ----------------
def insert_error_line(text, error=True):
    """Insere mensagens no ScrolledText com cores"""
    if error:
        output.insert(tk.END, text + "\n\n", 'error')
    else:
        output.insert(tk.END, text + "\n\n", 'success')
    output.see(tk.END)

# ---------------- Verificação de Logs do Sistema ----------------
def get_system_errors():
    logs = [
        r"C:\Windows\Logs\CBS\CBS.log",
        r"C:\Windows\Logs\DISM\dism.log"
    ]
    errors = []
    for log_path in logs:
        if stop_flag:
            return errors
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if stop_flag:
                            return errors
                        line = line.strip()
                        if 'cannot repair' in line.lower() or 'corrupt' in line.lower() or 'error' in line.lower():
                            errors.append(f"{log_path}: {line}")
            except Exception as e:
                errors.append(f"{log_path}: Erro ao ler arquivo ({e})")
    return errors

# ---------------- Verificação de Arquivos em Pasta/Disco ----------------
def scan_folder(path, progress_var=None, max_files=None):
    errors = []
    files_scanned = 0
    for root_dir, dirs, files in os.walk(path):
        if stop_flag:
            return errors
        for file in files:
            if stop_flag:
                return errors
            file_path = os.path.join(root_dir, file)
            try:
                with open(file_path, "rb") as f:
                    f.read(1024)  # Apenas teste de leitura
            except Exception as e:
                errors.append(f"{file_path} --> Erro: {e}")
            files_scanned += 1
            if progress_var and max_files:
                progress_var.set(int((files_scanned / max_files) * 100))
                progress_bar.update()
    if progress_var:
        progress_var.set(100)
    return errors

# ---------------- Funções para Usuários e Pasta Personalizada ----------------
def get_local_users():
    users = []
    try:
        profile_list_path = r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList"
        reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        key = winreg.OpenKey(reg, profile_list_path)
        i = 0
        while True:
            try:
                sid = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, sid)
                profile_path, _ = winreg.QueryValueEx(subkey, "ProfileImagePath")
                user = os.path.basename(profile_path)
                users.append((user, profile_path))
                i += 1
            except OSError:
                break
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível acessar o registro: {e}")
    return users

def check_user_health(path):
    if not os.path.exists(path):
        return False, "Pasta inexistente"
    try:
        os.listdir(path)
        return True, "OK"
    except PermissionError:
        return False, "Sem permissão"
    except Exception as e:
        return False, str(e)

def check_custom_config(user_path, custom_folder):
    docs_path = os.path.join(user_path, "Documents", custom_folder)
    if not os.path.exists(docs_path):
        return "Configuração ausente"
    try:
        os.listdir(docs_path)
        return "OK"
    except PermissionError:
        return f"Sem permissão {custom_folder}"
    except Exception as e:
        return f"Erro {custom_folder}: {e}"

def get_corrupted_files():
    log_path = r"C:\Windows\Logs\CBS\CBS.log"
    corrupted = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if 'cannot repair' in line.lower() or 'corrupt' in line.lower():
                        corrupted.append(line)
        except Exception as e:
            corrupted.append(f"Erro ao ler CBS.log: {e}")
    else:
        corrupted.append("CBS.log não encontrado")
    return corrupted

# ---------------- Função Principal da Thread ----------------
def run_check_thread():
    global stop_flag
    stop_flag = False
    btn_stop.config(bg='red')

    folder_path = filedialog.askdirectory(title="Escolha a pasta ou disco para verificar")
    if not folder_path:
        output.delete(1.0, tk.END)
        return

    # Extrai o nome da pasta para verificações personalizadas (ex.: "Diablo3" do caminho)
    custom_folder = os.path.basename(folder_path)
    if not custom_folder:
        custom_folder = "PastaSelecionada"  # Nome padrão se o nome da pasta estiver vazio

    output.delete(1.0, tk.END)
    progress_var.set(0)
    progress_bar.update()

    # Usuários
    users = get_local_users()
    header = f"{'Usuário':<20}{'Pasta':<50}{'Status Perfil':<20}{'Status ' + custom_folder:<20}\n"
    output.insert(tk.END, header, 'success')  # Cabeçalho em verde
    output.insert(tk.END, "-"*110 + "\n\n", 'success')

    for user, path in users:
        ok, status = check_user_health(path)
        custom_status = check_custom_config(path, custom_folder) if ok else "-"
        line = f"{user:<20}{path:<50}{status:<20}{custom_status:<20}\n\n"
        output.insert(tk.END, line, 'success')  # Conteúdo em verde

    # Arquivos Corrompidos
    output.insert(tk.END, "\nArquivos corrompidos detectados (somente leitura)\n")
    output.insert(tk.END, "-"*70 + "\n")
    corrupted = get_corrupted_files()
    for c in corrupted:
        insert_error_line(c)
        if stop_flag:
            return

    # Logs do Sistema
    system_errors = get_system_errors()
    output.insert(tk.END, "\nErros do sistema (CBS/DISM)\n")
    output.insert(tk.END, "-"*70 + "\n")
    for line in system_errors:
        insert_error_line(line)
        if stop_flag:
            return

    # Verificação de Arquivos na Pasta/Disco
    total_files = sum(len(files) for _, _, files in os.walk(folder_path))
    folder_errors = scan_folder(folder_path, progress_var, total_files)
    if folder_errors:
        output.insert(tk.END, f"\nErros de arquivos na pasta/disco ({folder_path})\n")
        output.insert(tk.END, "-"*70 + "\n")
    for line in folder_errors:
        insert_error_line(line)
        if stop_flag:
            return

    if not stop_flag:
        messagebox.showinfo("Concluído", "Verificação concluída!")

# ---------------- Controle de Threads ----------------
def run_check():
    t = threading.Thread(target=run_check_thread)
    t.start()

def stop_check():
    global stop_flag
    stop_flag = True
    btn_stop.config(bg='orange')

def save_results():
    content = output.get(1.0, tk.END)
    if not content.strip():
        messagebox.showwarning("Aviso", "Nenhum resultado para salvar.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo de texto", "*.txt")])
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Sucesso", f"Resultados salvos em: {file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo: {e}")

# ---------------- Interface Gráfica ----------------
root = tk.Tk()
root.title("Verificador de Usuários do Sistema")
root.geometry("1280x800")
root.state('zoomed')

frame = tk.Frame(root)
frame.pack(pady=10)

btn_check = tk.Button(frame, text="Verificar Pasta/Disco", bg="#03fc24", fg="black", command=run_check, font=("Consolas", 10))
btn_check.pack(pady=5)

btn_stop = tk.Button(frame, text="Parar Verificação", command=stop_check, font=("Consolas", 10), bg='red', fg='black')
btn_stop.pack(pady=5)

btn_save = tk.Button(frame, text="Salvar Resultados", bg="#07f5f5", fg="black", command=save_results, font=("Consolas", 10))
btn_save.pack(pady=5)

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=500)
progress_bar.pack(pady=10)

output = scrolledtext.ScrolledText(root, width=132, height=38, font=("Consolas", 12))
output.pack(pady=10)

output.tag_config('error', foreground='red')
output.tag_config('success', foreground='green')

root.mainloop()
