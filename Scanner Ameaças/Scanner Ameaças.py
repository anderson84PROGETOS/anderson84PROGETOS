import os
import psutil
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import winsound
import hashlib
import webbrowser

suspicious_keywords = ['keylogger', 'rat', 'stealer', 'backdoor', 'botnet', 'hacker', 'exploit']
suspeitos_detectados = []
scan_active = threading.Event()

def is_suspicious(name):
    name = name.lower()
    return any(keyword in name for keyword in suspicious_keywords)

def calcular_hash_sha256(filepath):
    try:
        with open(filepath, 'rb') as f:
            hash_sha256 = hashlib.sha256()
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
    except Exception:
        return None

def open_virustotal_link(hash_sha256):
    if hash_sha256:
        url = f"https://www.virustotal.com/gui/file/{hash_sha256}/detection"
        webbrowser.open(url)
    else:
        messagebox.showwarning("Erro", "Hash não disponível para este arquivo.")

def open_selected_virustotal():
    input_text = entry_virustotal.get().strip()
    if not input_text:
        messagebox.showwarning("Erro", "Por favor, insira um número, lista (ex: 1,2,3) ou intervalo (ex: 1-10).")
        return

    try:
        indices = set()  # Use set to avoid duplicates
        # Split input by commas or spaces
        parts = re.split(r'[,\s]+', input_text)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Check for range (e.g., 1-10)
            if '-' in part:
                start, end = part.split('-')
                start = int(start.strip())
                end = int(end.strip())
                if start < 1 or end > len(suspeitos_detectados) or start > end:
                    messagebox.showwarning("Erro", f"Intervalo inválido: {part}. Use 1-{len(suspeitos_detectados)}.")
                    continue
                indices.update(range(start, end + 1))
            else:
                # Single number
                index = int(part)
                if 1 <= index <= len(suspeitos_detectados):
                    indices.add(index)
                else:
                    messagebox.showwarning("Erro", f"Índice {index} fora do intervalo (1-{len(suspeitos_detectados)}).")

        if not indices:
            messagebox.showwarning("Erro", "Nenhum índice válido fornecido.")
            return

        for index in sorted(indices):
            _, hash_sha256 = suspeitos_detectados[index - 1]
            open_virustotal_link(hash_sha256)

    except ValueError:
        messagebox.showwarning("Erro", "Entrada inválida. Use números como 1,2,3 ou intervalos como 1-10.")

def verificar_processos(output_box):
    output_box.insert(tk.END, "[*] Verificando processos em execução\n")
    output_box.see(tk.END)
    alerta = False
    suspeito_index = len(suspeitos_detectados) + 1
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            pname = proc.info['name'] or ''
            pexe = proc.info['exe'] or ''
            if is_suspicious(pname) or is_suspicious(pexe):
                hash_sha256 = calcular_hash_sha256(pexe)
                linha = f"[!] [{suspeito_index}] Processo suspeito: {pname} ({pexe}) \nSHA-256: "
                output_box.insert(tk.END, linha, "alert")
                if hash_sha256:
                    tag_name = f"hash_{hash_sha256}"
                    output_box.insert(tk.END, hash_sha256, ("alert", tag_name))
                    output_box.tag_configure(tag_name, foreground="blue", underline=1)
                    output_box.tag_bind(tag_name, "<Button-1>", lambda event, h=hash_sha256: open_virustotal_link(h))
                    output_box.tag_bind(tag_name, "<Enter>", lambda event: output_box.config(cursor="hand2"))
                    output_box.tag_bind(tag_name, "<Leave>", lambda event: output_box.config(cursor=""))
                else:
                    output_box.insert(tk.END, "N/A", "alert")
                output_box.insert(tk.END, "\n\n")
                output_box.see(tk.END)
                alerta = True
                if pexe:
                    suspeitos_detectados.append((pexe, hash_sha256))
                    suspeito_index += 1
        except (psutil.NoSuchProcess, psutil.ErrorAccessDenied):
            continue
    return alerta

extensoes_suspeitas = [
    '.exe', '.dll', '.scr', '.pif', '.com', '.bat', '.cmd', '.vbs', '.js',
    '.jse', '.wsf', '.wsh', '.ps1', '.psm1', '.tmp', '.lnk', '.apk', '.sys', '.cpl',
    '.hta', '.msc', '.msi', '.msp', '.reg'
]

def escanear_diretorio(diretorio, output_box, progress_bar):
    if not os.path.exists(diretorio):
        messagebox.showerror("Erro", "Diretório inválido!")
        return False

    output_box.insert(tk.END, f"\n[*] Escaneando: {diretorio}\n\n")
    output_box.see(tk.END)

    total_files = sum(len(files) for _, _, files in os.walk(diretorio))
    scanned = 0
    alerta = False
    suspeito_index = len(suspeitos_detectados) + 1

    if total_files == 0:
        progress_bar["maximum"] = 1
        progress_bar["value"] = 1

    for root, _, files in os.walk(diretorio):
        for file in files:
            if not scan_active.is_set():
                output_box.insert(tk.END, "\n[!] Varredura interrompida pelo usuário.\n", "alert")
                output_box.see(tk.END)
                return alerta

            filepath = os.path.join(root, file)
            filename = file.lower()

            output_box.insert(tk.END, f"Verificando: {filepath}\n\n")
            output_box.see(tk.END)

            _, ext = os.path.splitext(filename)

            hash_sha256 = calcular_hash_sha256(filepath)
            suspeito = False

            if re.search(r'\.txt\.exe$|\.jpg\.exe$|\.png\.scr$', filename):
                linha = f"[!] [{suspeito_index}] Extensão dupla suspeita: {filepath} \nSHA-256: "
                suspeito = True
            elif is_suspicious(filename):
                linha = f"[!] [{suspeito_index}] Nome suspeito detectado: {filepath} \nSHA-256: "
                suspeito = True
            elif ext in extensoes_suspeitas:
                linha = f"[!] [{suspeito_index}] Arquivo com extensão suspeita: {filepath} \nSHA-256: "
                suspeito = True

            if suspeito:
                output_box.insert(tk.END, linha, "alert")
                if hash_sha256:
                    tag_name = f"hash_{hash_sha256}"
                    output_box.insert(tk.END, hash_sha256, ("alert", tag_name))
                    output_box.tag_configure(tag_name, foreground="blue", underline=1)
                    output_box.tag_bind(tag_name, "<Button-1>", lambda event, h=hash_sha256: open_virustotal_link(h))
                    output_box.tag_bind(tag_name, "<Enter>", lambda event: output_box.config(cursor="hand2"))
                    output_box.tag_bind(tag_name, "<Leave>", lambda event: output_box.config(cursor=""))
                else:
                    output_box.insert(tk.END, "N/A", "alert")
                output_box.insert(tk.END, "\n\n")
                output_box.see(tk.END)
                alerta = True
                if hash_sha256:
                    suspeitos_detectados.append((filepath, hash_sha256))
                    suspeito_index += 1

            scanned += 1
            progress_bar["maximum"] = total_files
            progress_bar["value"] = scanned
            progress_bar.update()
            lbl_suspeitos.config(text=f"Suspeitos Encontrados: {len(suspeitos_detectados)}")

    output_box.insert(tk.END, "\n[✓] Varredura concluída.\n")
    output_box.see(tk.END)
    return alerta

def selecionar_pasta():
    pasta = filedialog.askdirectory()
    if pasta:
        entry_dir.delete(0, tk.END)
        entry_dir.insert(0, pasta)

def iniciar_varredura_thread():
    scan_active.set()
    thread = threading.Thread(target=iniciar_varredura)
    thread.start()

def parar_varredura():
    scan_active.clear()

def iniciar_varredura():
    output_box.delete(1.0, tk.END)
    progress_bar["value"] = 0
    suspeitos_detectados.clear()
    lbl_suspeitos.config(text="Suspeitos encontrados: 0")

    suspeito1 = verificar_processos(output_box)
    suspeito2 = escanear_diretorio(entry_dir.get(), output_box, progress_bar)

    if scan_active.is_set() and (suspeito1 or suspeito2):
        winsound.MessageBeep(winsound.MB_ICONHAND)
        messagebox.showwarning("Alerta de Segurança", "⚠️ Itens suspeitos foram detectados durante a varredura!")
    scan_active.clear()

def salvar_resultado():
    conteudo = output_box.get("1.0", tk.END)
    linhas = conteudo.strip().splitlines()
    linhas_suspeitas = []
    i = 0
    while i < len(linhas):
        if '[!]' in linhas[i]:
            # Capture the suspicious line and the next line (SHA-256 or N/A)
            if i + 1 < len(linhas):
                linhas_suspeitas.append(linhas[i].strip() + "\n" + linhas[i + 1].strip())
                i += 2
            else:
                linhas_suspeitas.append(linhas[i].strip())
                i += 1
        else:
            i += 1
    total_suspeitos = len(linhas_suspeitas)

    if total_suspeitos > 0:
        caminho = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivos de texto", "*.txt")])
        if caminho:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(f"Total de resultados suspeitos Encontrados: {total_suspeitos}\n\n")
                f.write("\n\n".join(linhas_suspeitas))
            messagebox.showinfo("Salvo", f"Salvo com sucesso em: {caminho}")
    else:
        messagebox.showinfo("Nada para salvar", "Nenhum resultado suspeito foi encontrado para salvar.")

# Interface gráfica
janela = tk.Tk()
janela.title("Scanner de Ameaças")
janela.geometry("950x650")
janela.state("zoomed")

frame = tk.Frame(janela)
frame.pack(pady=10)

entry_dir = tk.Entry(frame, width=60)
entry_dir.pack(side=tk.LEFT, padx=5)

btn_browse = tk.Button(frame, text="Selecionar Pasta", command=selecionar_pasta)
btn_browse.pack(side=tk.LEFT)

btn_scan = tk.Button(janela, text="Iniciar Varredura", command=iniciar_varredura_thread, bg="#0af531", fg="black")
btn_scan.pack(pady=5)

btn_stop = tk.Button(janela, text="Parar Varredura", command=parar_varredura, bg="red", fg="white")
btn_stop.pack(pady=5)

frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=5)

btn_salvar = tk.Button(frame_botoes, text="Salvar Relatório", command=salvar_resultado, bg="lightblue")
btn_salvar.pack(side=tk.LEFT, padx=10)

# Frame para o campo de entrada e botão do VirusTotal
frame_virustotal = tk.Frame(janela)
frame_virustotal.pack(pady=5)

lbl_virustotal = tk.Label(frame_virustotal, text="Digite números ou intervalos para VirusTotal (ex: 1,2,3 ou 1-10):")
lbl_virustotal.pack(side=tk.LEFT, padx=5)

entry_virustotal = tk.Entry(frame_virustotal, width=75)
entry_virustotal.pack(side=tk.LEFT, padx=5)

btn_virustotal = tk.Button(frame_virustotal, text="Abrir no VirusTotal", command=open_selected_virustotal, bg="orange")
btn_virustotal.pack(side=tk.LEFT, padx=5)

progress_bar = ttk.Progressbar(janela, orient="horizontal", length=700, mode="determinate")
progress_bar.pack(pady=5)

lbl_suspeitos = tk.Label(janela, text="Suspeitos Encontrados: 0", font=("Arial", 10, "bold"))
lbl_suspeitos.pack()

output_box = scrolledtext.ScrolledText(janela, wrap=tk.WORD, width=160, height=40)
output_box.pack(padx=10, pady=10)
output_box.tag_config("alert", foreground="red")

janela.mainloop()
