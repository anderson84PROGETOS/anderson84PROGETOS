import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import socket
import webbrowser
import threading
import time
import re

monitoring = False
seen = set()

def display_dns():
    try:
        result = subprocess.check_output(['ipconfig', '/displaydns'], shell=True)
        output.delete(1.0, tk.END)
        output.insert(tk.END, "=== CACHE DNS ATUAL ===\n\n")
        output.insert(tk.END, result.decode('latin-1', errors='ignore'))
    except:
        messagebox.showerror("Erro", "Erro ao exibir cache DNS")

def flush_dns():
    try:
        subprocess.check_output(['ipconfig', '/flushdns'], shell=True)
        clear_screen()
        output.insert(tk.END, "🧹 DNS limpo com sucesso!\n")
        messagebox.showinfo("Sucesso", "DNS limpo com sucesso!")
    except:
        messagebox.showerror("Erro", "Erro ao limpar DNS")

def clear_screen():
    output.delete(1.0, tk.END)

def open_virustotal(ip):
    webbrowser.open(f"https://www.virustotal.com/gui/ip-address/{ip}")

def get_process_name(pid):
    try:
        result = subprocess.check_output(f'tasklist /FI "PID eq {pid}" /FO CSV', shell=True)
        lines = result.decode('latin-1', errors='ignore').split('\n')
        if len(lines) > 1:
            return lines[1].split(',')[0].strip('"')
    except:
        pass
    return "Desconhecido"

def monitor_real_time():
    global monitoring
    last_cleanup = time.time()
   
    while monitoring:
        try:
            # Usa netstat com mais detalhes
            result = subprocess.check_output(['netstat', '-ano'], shell=True)
            text = result.decode('latin-1', errors='ignore')
            lines = text.split('\n')
           
            new_entries = []
            current_time = time.time()

            # Limpa o seen a cada 30 segundos para não perder conexões reutilizadas
            if current_time - last_cleanup > 30:
                seen.clear()
                last_cleanup = current_time

            for line in lines:
                if 'ESTABLISHED' not in line:
                    continue
               
                parts = re.split(r'\s+', line.strip())
                if len(parts) < 5:
                    continue
               
                remote = parts[2]
                pid = parts[-1]
               
                ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):\d+', remote)
                if not ip_match:
                    continue
                ip = ip_match.group(1)
               
                # Ignora IPs locais
                if ip.startswith(('10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.',
                                '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
                                '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.')):
                    continue
               
                key = f"{ip}-{pid}"
                if key in seen:
                    continue
                seen.add(key)
               
                try:
                    domain = socket.gethostbyaddr(ip)[0]
                except:
                    domain = ip
               
                process = get_process_name(pid)
               
                # Destaque para conexões de navegadores (útil para aba anônima)
                is_browser = any(b in process.lower() for b in ['chrome', 'firefox', 'msedge', 'brave', 'opera'])
                
                new_entries.append((domain, ip, process, pid, is_browser))
           
            if new_entries:
                for domain, ip, process, pid, is_browser in new_entries:
                    if is_browser:
                        output.insert(tk.END, "🔒 ", "browser")
                        output.insert(tk.END, f"{domain}\n", "browser")
                    else:
                        output.insert(tk.END, f"🌐 {domain}\n")
                    
                    output.insert(tk.END, f"   📍 IP: {ip}\n")
                    output.insert(tk.END, f"   📌 Processo: {process} (PID: {pid})\n")
                    
                    btn = tk.Button(output, text="🔍 VirusTotal", bg="#ff4444", fg="white",
                                  font=("Arial", 9, "bold"), command=lambda i=ip: open_virustotal(i))
                    output.window_create(tk.END, window=btn)
                    output.insert(tk.END, "\n" + "-"*80 + "\n\n")
               
                output.see(tk.END)
           
            time.sleep(1.5)  # mais responsivo
           
        except Exception as e:
            time.sleep(2)

def start_monitor():
    global monitoring
    if monitoring:
        messagebox.showinfo("Info", "Monitor já está ativo!")
        return
   
    monitoring = True
    seen.clear()  # limpa histórico ao iniciar
    clear_screen()
    
    output.insert(tk.END, "🔴 Monitoramento em Tempo Real INICIADO (Todas as Portas)\n", "title")
    output.insert(tk.END, "✅ Inclui abas normais e ABA ANÔNIMA / Incógnito\n\n", "success")
   
    threading.Thread(target=monitor_real_time, daemon=True).start()
    status_label.config(text="🔴 Monitorando todas as conexões (incluindo anônima)...", fg="#ff3333")

def stop_monitor():
    global monitoring
    monitoring = False
    status_label.config(text="⭕ Monitor parado", fg="gray")

# ==================== INTERFACE ====================
root = tk.Tk()
root.title("Monitor de Conexões em Tempo Real - Todas Portas + Aba Anônima")
root.geometry("1480x920")
root.state("zoomed")
root.configure(bg="#1e1e1e")

title = tk.Label(root, text="Monitor de Navegação em Tempo Real (Todas Portas + Incógnito)", 
                font=("Arial", 22, "bold"), bg="#1e1e1e", fg="#00ffcc")
title.pack(pady=15)

status_label = tk.Label(root, text="⭕ Monitor parado", font=("Arial", 12, "bold"),
                       bg="#1e1e1e", fg="gray")
status_label.pack(pady=5)

frame_buttons = tk.Frame(root, bg="#1e1e1e")
frame_buttons.pack(pady=10)

btn_style = {"font": ("Arial", 11, "bold"), "width": 26, "bd": 0, "cursor": "hand2", "height": 2}

tk.Button(frame_buttons, text="🔴 Iniciar Monitor", bg="#ff3333", fg="white",
          command=start_monitor, **btn_style).grid(row=0, column=0, padx=6)

tk.Button(frame_buttons, text="⭕ Parar Monitor", bg="#555555", fg="white",
          command=stop_monitor, **btn_style).grid(row=0, column=1, padx=6)

tk.Button(frame_buttons, text="Limpar Tela", bg="#666666", fg="white",
          command=clear_screen, **btn_style).grid(row=0, column=2, padx=6)

tk.Button(frame_buttons, text="📋 Mostrar Cache DNS", bg="#0078D7", fg="white",
          command=display_dns, **btn_style).grid(row=0, column=3, padx=6)

tk.Button(frame_buttons, text="🧹 Limpar DNS", bg="#28a745", fg="white",
          command=flush_dns, **btn_style).grid(row=0, column=4, padx=6)

# Área de saída com tags de cor
output = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="#0f0f0f", fg="#00ffaa",
                                  font=("Consolas", 11), insertbackground="white")
output.pack(padx=15, pady=10, fill="both", expand=True)

# Configurar tags de cor
output.tag_config("title", foreground="#00ffff", font=("Consolas", 12, "bold"))
output.tag_config("success", foreground="#00ff88")
output.tag_config("browser", foreground="#ffaa00", font=("Consolas", 11, "bold"))

root.mainloop()
