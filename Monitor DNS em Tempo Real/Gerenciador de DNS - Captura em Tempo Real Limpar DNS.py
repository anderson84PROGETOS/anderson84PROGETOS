import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import subprocess
import threading
import webbrowser
import re
import time
import socket
import os

capture_process = None
stop_capture = False


def cleanup_etl():
    """Exclui o arquivo PktMon.etl com segurança"""
    try:
        if os.path.exists("PktMon.etl"):
            os.remove("PktMon.etl")
            # print("PktMon.etl excluído com sucesso.")  # descomente para debug
    except Exception as e:
        print(f"Erro ao excluir PktMon.etl: {e}")


def display_dns():
    try:
        result = subprocess.check_output(['ipconfig', '/displaydns'], shell=True)
        clear_screen()
        output.insert(tk.END, result.decode('latin-1', errors='ignore'))
    except:
        messagebox.showerror("Erro", "Erro ao exibir DNS")


def flush_dns():
    try:
        subprocess.check_output(['ipconfig', '/flushdns'], shell=True)
        clear_screen()
        output.insert(tk.END, "✅ DNS Flush executado com sucesso!\n")
        messagebox.showinfo("Sucesso", "DNS limpo!")
    except:
        messagebox.showerror("Erro", "Erro ao limpar DNS")


def clear_screen():
    cleanup_etl()                    # ← Exclui o .etl ao limpar tela
    output.delete(1.0, tk.END)


def save_to_txt():
    try:
        content = output.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Aviso", "Não há conteúdo para salvar!")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")],
            title="Salvar captura DNS como..."
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso!\n{file_path}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar arquivo:\n{e}")


def start_dns_capture():
    global capture_process, stop_capture
    stop_capture = False
    clear_screen()
    output.insert(tk.END, "🚀 Captura de DNS em Tempo Real Iniciada (pktmon)\n")
    output.insert(tk.END, "Acesse qualquer site no navegador agora...\n")
    output.insert(tk.END, "="*90 + "\n\n")

    def run_pktmon():
        global capture_process
        try:
            subprocess.run("pktmon filter remove", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run("pktmon filter add DNS -t UDP -p 53", shell=True, stdout=subprocess.DEVNULL)
            
            cleanup_etl()  # Remove arquivo antigo antes de iniciar

            capture_process = subprocess.Popen(
                "pktmon start -c -m real-time --pkt-size 0",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )

            while not stop_capture and capture_process.poll() is None:
                line = capture_process.stdout.readline()
                if line and ("DNS" in line or any(ext in line.lower() for ext in ['.com', '.net', '.org', '.br', '.io', '.app'])):
                    clean_line = re.sub(r'\s+', ' ', line.strip())
                    timestamp = time.strftime("%H:%M:%S")
                   
                    domain_match = re.search(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', clean_line)
                    ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', clean_line)
                    domain = domain_match.group(1) if domain_match else "N/A"
                    ip_from_pktmon = ip_match.group() if ip_match else "N/A"

                    website_ip = "Não resolvido"
                    if domain != "N/A":
                        try:
                            website_ip = socket.gethostbyname(domain)
                        except:
                            try:
                                if not domain.startswith("www."):
                                    website_ip = socket.gethostbyname("www." + domain)
                            except:
                                pass

                    formatted = (
                        f"\n{'='*80}\n"
                        f"🕒 Horário : {timestamp}\n\n"
                        f"📍 IP Capturado: {ip_from_pktmon}\n\n\n"
                        f"🌐 Domínio : {domain}\n\n"
                        f"📄 Linha : {clean_line}\n\n"
                        f"🌍 IP Website : {website_ip}\n"
                        f"{'='*80}\n"
                    )
                    output.insert(tk.END, formatted)
                    output.see(tk.END)
                time.sleep(0.01)
        except Exception as e:
            output.insert(tk.END, f"\nErro: {e}\nExecute o programa como Administrador!\n")

    threading.Thread(target=run_pktmon, daemon=True).start()


def stop_dns_capture():
    global stop_capture, capture_process
    stop_capture = True
    try:
        subprocess.run("pktmon stop", shell=True, stdout=subprocess.DEVNULL)
        if capture_process:
            capture_process.kill()
    except:
        pass
    
    cleanup_etl()                    # ← Exclui o .etl ao parar captura
    output.insert(tk.END, "\n⛔ Captura parada pelo usuário.\n")


def open_virustotal(event):
    try:
        index = output.index(f"@{event.x},{event.y}")
        line = output.get(f"{index} linestart", f"{index} lineend")
       
        domain_match = re.search(r'([a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', line)
        ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line)
       
        if domain_match:
            domain = domain_match.group(1)
            webbrowser.open(f"https://www.virustotal.com/gui/domain/{domain}")
        elif ip_match:
            ip = ip_match.group()
            webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")
    except:
        pass


# ===================== INTERFACE =====================
root = tk.Tk()
root.title("Gerenciador de DNS - Captura em Tempo Real e Limpar DNS")
root.geometry("1200x820")
root.state("zoomed")
root.configure(bg="#1e1e1e")


def on_closing():
    """Executado quando o usuário fecha a janela"""
    stop_dns_capture()
    cleanup_etl()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)   # ← Vincula fechamento da janela

tk.Label(root, text="Captura de DNS em Tempo Real",
         font=("Arial", 18, "bold"), bg="#1e1e1e", fg="#00ffcc").pack(pady=12)

frame = tk.Frame(root, bg="#1e1e1e")
frame.pack(pady=10)

btn_style = {"font": ("Arial", 10, "bold"), "width": 18, "bd": 0, "cursor": "hand2", "height": 2}

tk.Button(frame, text="Mostrar DNS", bg="#0078D7", fg="black", command=display_dns, **btn_style).grid(row=0, column=0, padx=4)
tk.Button(frame, text="Limpar DNS", bg="#28a745", fg="black", command=flush_dns, **btn_style).grid(row=0, column=1, padx=4)
tk.Button(frame, text="▶ Iniciar Captura", bg="#ff9800", fg="black", command=start_dns_capture, **btn_style).grid(row=0, column=2, padx=4)
tk.Button(frame, text="⛔ Parar Captura", bg="#f44336", fg="black", command=stop_dns_capture, **btn_style).grid(row=0, column=3, padx=4)
tk.Button(frame, text="Limpar Tela", bg="#555555", fg="black", command=clear_screen, **btn_style).grid(row=0, column=4, padx=4)
tk.Button(frame, text="💾 Salvar em TXT", bg="#9c27b0", fg="black", command=save_to_txt, **btn_style).grid(row=0, column=5, padx=4)

# Saída
output = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="#0d0d0d", fg="#00ffaa",
                                   font=("Consolas", 11), insertbackground="white")
output.pack(padx=12, pady=12, fill="both", expand=True)
output.bind("<Double-Button-1>", open_virustotal)

tk.Label(root, text="⚠️ Execute como Administrador | Duplo clique no domínio ou IP abre no VirusTotal",
         bg="#1e1e1e", fg="#ffaa00", font=("Arial", 9)).pack(pady=5)

root.mainloop()
