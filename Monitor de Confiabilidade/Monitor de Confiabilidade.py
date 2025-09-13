import subprocess
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from datetime import datetime

def abrir_monitor():
    try:
        subprocess.Popen(
            ["perfmon", "/rel"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir o Monitor: {e}")

def formatar_data_hora_iso(iso_str):
    """
    Converte timestamp ISO do Windows (ex: 2024-11-25T14:53:07.5350000Z)
    para o formato: Data: dd/mm/yyyy    Horas: HH:MM
    """
    try:
        iso_str = iso_str.rstrip("Z")
        dt = datetime.fromisoformat(iso_str.split('.')[0])
        return f"Data: {dt.strftime('%d/%m/%Y')}    Horas: {dt.strftime('%H:%M')}"
    except Exception:
        return iso_str

def processar_eventos(saida):
    """
    Processa a saída do wevtutil, substituindo a linha Date: pelo formato desejado
    """
    linhas = saida.splitlines()
    novas_linhas = []
    for linha in linhas:
        if linha.strip().startswith("Date:"):
            iso_ts = linha.split("Date:")[1].strip()
            linha = formatar_data_hora_iso(iso_ts)
        novas_linhas.append(linha)
    return "\n".join(novas_linhas)

def carregar_eventos():
    cmd_system = ["wevtutil", "qe", "System", "/c:40", "/f:text", "/q:*[System[(Level=2 or Level=3)]]"]
    cmd_app    = ["wevtutil", "qe", "Application", "/c:40", "/f:text", "/q:*[System[(Level=2 or Level=3)]]"]

    try:
        saida_sys = subprocess.check_output(cmd_system, text=True, stderr=subprocess.DEVNULL)
        saida_app = subprocess.check_output(cmd_app, text=True, stderr=subprocess.DEVNULL)

        eventos_sys = processar_eventos(saida_sys)
        eventos_app = processar_eventos(saida_app)

        texto_final = "=== LOG SYSTEM ===\n\n" + eventos_sys + "\n\n=== LOG APPLICATION ===\n" + eventos_app

        text_area.delete("1.0", tk.END)
        text_area.insert(tk.END, texto_final)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Erro", f"Falha ao ler eventos (código {e.returncode}).")

def salvar_log():
    """
    Salva o conteúdo do text_area em arquivo .txt
    """
    conteudo = text_area.get("1.0", tk.END).strip()
    if not conteudo:
        messagebox.showwarning("Aviso", "Não há conteúdo para salvar.")
        return

    arquivo = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt")],
        title="Salvar Log Como"
    )
    if arquivo:
        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write(conteudo)
            messagebox.showinfo("Sucesso", f"Log salvo em\n\n{arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")

# ----- Interface gráfica -----
root = tk.Tk()
root.title("Monitor de Confiabilidade")
root.wm_state('zoomed')

frame_btn = tk.Frame(root)
frame_btn.pack(pady=5)

btn_abrir = tk.Button(frame_btn, text="Abrir Monitor Gráfico", bg="#03fc24", fg="black", command=abrir_monitor)
btn_abrir.pack(side=tk.LEFT, padx=5)

btn_carregar = tk.Button(frame_btn, text="Carregar Últimos Eventos", bg="#03f0fc", fg="black", command=carregar_eventos)
btn_carregar.pack(side=tk.LEFT, padx=5)

btn_salvar = tk.Button(frame_btn, text="Salvar Log", bg="#fcd103", fg="black", command=salvar_log)
btn_salvar.pack(side=tk.LEFT, padx=5)

text_area = scrolledtext.ScrolledText(root, width=145, height=53)
text_area.pack(pady=10)

root.mainloop()
