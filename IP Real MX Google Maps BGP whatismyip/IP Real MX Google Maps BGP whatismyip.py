import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import socket
import subprocess
import webbrowser
from datetime import datetime
import threading
import re

# ===================== VARIÁVEIS GLOBAIS =====================
last_entrada = ""

# ===================== FUNÇÕES =====================

def get_ip_info(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10)
        response.raise_for_status()
        data = response.json()

        org = data.get("org", "")
        if org.startswith("AS"):
            partes = org.split(" ", 1)
            data["asn"] = partes[0]
            data["asn_name"] = partes[1] if len(partes) > 1 else "N/D"
        return data
    except:
        return None


def get_mx_and_real_ips(domain):
    result = f"🔍 ANÁLISE MX - {domain}\n"
    result += "=" * 60 + "\n\n"
    geo_entries = []

    try:
        mx_output = subprocess.run(['nslookup', '-type=MX', domain], 
                                 capture_output=True, text=True, timeout=10)
        
        result += "📧 REGISTROS MX ENCONTRADOS\n\n"
        for line in mx_output.stdout.splitlines():
            if "mail exchanger" in line.lower() or "MX" in line.upper():
                result += f"   {line.strip()}\n\n"
                if "mail exchanger" in line.lower():
                    mx_name = line.split()[-1].rstrip('.')
                    geo_entries.append(mx_name)
    except Exception as e:
        result += f"Erro ao consultar MX: {e}\n"

    result += "\n🌐 IP REAIS DOS SERVIDORES MX\n"
    result += "-" * 50 + "\n"

    mx_ips = []
    for mx in geo_entries:
        try:
            ip = socket.gethostbyname(mx)
            mx_ips.append(ip)
            result += f"📍 {mx} → {ip}\n"
            
            # Apenas verifica se o ping executou, sem exibir a saída
            subprocess.run(
                ['ping', '-4', '-n', '2', ip], capture_output=True, text=True, timeout=8)
            
            data = get_ip_info(ip)
            if data and data.get('loc'):
                lat, lon = data['loc'].split(',')
            
                maps_url = f"https://www.google.com/maps/place/{lat},{lon}\n"
                result += f"\n🔗 Google Maps: {maps_url}\n\n"

                # Whatismyip Map
                whatismyip_url = f"https://whatismyip.com.br/map.php?query={ip}"
                result += f"WhatIsMyIP: {whatismyip_url}\n\n"
                
                # Link BGP para MX (laranja)
                asn = data.get('asn')
                if asn and asn.startswith("AS"):
                    asn_num = asn[2:]
                    bgp_url = f"https://bgp.he.net/AS{asn_num}"
                    result += f"🌐 🔗 BGP.he.net : {bgp_url}\n\n"
                else:
                    result += "\n"
            else:
                result += "\n"
        except:
            result += "\n"
    
    return result, mx_ips


def perform_lookup(entrada, progress_callback, result_callback):
    try:
        progress_callback(10)
        
        mx_analysis, mx_ips = get_mx_and_real_ips(entrada)
        progress_callback(45)

        mx_geo = "\n🌍 GEOLOCALIZAÇÃO DOS SERVIDORES MX\n"
        mx_geo += "=" * 50 + "\n\n"
        
        for ip in mx_ips:
            data = get_ip_info(ip)
            if data:
                mx_geo += f"IP: {ip}\n\n"
                mx_geo += f"País     : {data.get('country', 'N/D')}\n"
                mx_geo += f"Região   : {data.get('region', 'N/D')}\n"
                mx_geo += f"Cidade   : {data.get('city', 'N/D')}\n"
                mx_geo += f"Org      : {data.get('org', 'N/D')}\n"
                mx_geo += f"ASN      : {data.get('asn','N/D')}\n"
                mx_geo += f"Empresa  : {data.get('asn_name','N/D')}\n\n"

                if data.get('loc'):
                    lat, lon = data['loc'].split(',')
                    maps_url = f"https://www.google.com/maps/place/{lat},{lon}"                    
                    mx_geo += f"Latitude  : {lat}\n"
                    mx_geo += f"Longitude : {lon}\n\n"
                    mx_geo += f"🔗 Maps   : {maps_url}\n\n"

                # Whatismyip
                whatismyip_url = f"https://whatismyip.com.br/map.php?query={ip}"
                mx_geo += f"WhatIsMyIP: {whatismyip_url}\n\n"    
                
                # Link BGP para cada MX
                asn = data.get('asn')
                if asn and asn.startswith("AS"):
                    asn_num = asn[2:]
                    bgp_url = f"https://bgp.he.net/AS{asn_num}"
                    mx_geo += f"🌐 BGP    : {bgp_url}\n"
                mx_geo += "-" * 40 + "\n\n"
        progress_callback(75)

        # IP Principal
        main_geo = "\n🌐 GEOLOCALIZAÇÃO DO IP PRINCIPAL\n"
        main_geo += "=" * 50 + "\n\n"
        
        try:
            main_ip = socket.gethostbyname(entrada)
            main_data = get_ip_info(main_ip)

            if main_data:
                main_geo += f"IP        : {main_ip}\n\n"
                main_geo += f"País      : {main_data.get('country', 'N/D')}\n"
                main_geo += f"Região    : {main_data.get('region', 'N/D')}\n"
                main_geo += f"Cidade    : {main_data.get('city', 'N/D')}\n"
                main_geo += f"ASN       : {main_data.get('asn', 'N/D')}\n"
                main_geo += f"Empresa   : {main_data.get('asn_name', 'N/D')}\n"
                main_geo += f"Org       : {main_data.get('org', 'N/D')}\n\n"

                if main_data.get('loc'):
                    lat, lon = main_data['loc'].split(',')
                    maps_url = f"https://www.google.com/maps/place/{lat},{lon}"
                    main_geo += f"Latitude  : {lat}\n"
                    main_geo += f"Longitude : {lon}\n\n"
                    main_geo += f"🔗 Maps   : {maps_url}\n\n"

                # Whatismyip para IP Principal
                whatismyip_url = f"https://whatismyip.com.br/map.php?query={main_ip}"
                main_geo += f"WhatIsMyIP: {whatismyip_url}\n\n"    

                # Link BGP para IP Principal
                asn = main_data.get('asn')
                if asn and asn.startswith("AS"):
                    asn_num = asn[2:]
                    bgp_url = f"https://bgp.he.net/AS{asn_num}"
                    main_geo += f"\n🌐 🔗 BGP.he.net : {bgp_url}\n"
        except:
            main_geo += "Não foi possível resolver o IP principal.\n"

        progress_callback(100)
        full_text = mx_analysis + mx_geo + main_geo
        result_callback(full_text)
        
    except Exception as e:
        progress_callback(100)
        root.after(0, lambda: messagebox.showerror("Erro", str(e)))


def update_gui(full_text):
    result_text.delete("1.0", tk.END)
    result_text.insert("1.0", full_text)

    # =================== CONFIGURAÇÃO DAS TAGS ===================
    result_text.tag_configure("url", foreground="#00ccff", underline=True)
    result_text.tag_configure("whatismyip", foreground="#c026d3", underline=True)
    result_text.tag_configure("bgp", foreground="#ff8800", underline=True, 
                             font=("Consolas", 10, "bold"))
    
    texto = result_text.get("1.0", tk.END)

    # =================== MARCAÇÃO DOS LINKS ===================
    
    # Google Maps (azul)
    for m in re.finditer(r"https://www\.google\.com/maps/place/[-0-9.,]+", texto):
        inicio = f"1.0+{m.start()}c"
        fim = f"1.0+{m.end()}c"
        result_text.tag_add("url", inicio, fim)

    # WhatIsMyIP (roxo) ← CORRIGIDO
    for m in re.finditer(r"https://whatismyip\.com\.br/map\.php\?query=[0-9.]+", texto):
        inicio = f"1.0+{m.start()}c"
        fim = f"1.0+{m.end()}c"
        result_text.tag_add("whatismyip", inicio, fim)

    # BGP (laranja)
    for m in re.finditer(r"https://bgp\.he\.net/AS\d+", texto):
        inicio = f"1.0+{m.start()}c"
        fim = f"1.0+{m.end()}c"
        result_text.tag_add("bgp", inicio, fim)

    # =================== BINDINGS DO CLIQUE ===================
    result_text.tag_bind("url", "<Double-Button-1>", abrir_url)
    result_text.tag_bind("whatismyip", "<Double-Button-1>", abrir_url)
    result_text.tag_bind("bgp", "<Double-Button-1>", abrir_url)

def abrir_url(event):
    indice = result_text.index(f"@{event.x},{event.y}")
    inicio = result_text.search("https://", indice, backwards=True, regexp=False)
    fim = result_text.search(r"\s", indice, regexp=True) or "end"
    url = result_text.get(inicio, fim).strip()
    webbrowser.open(url)


def lookup():
    global last_entrada
    entrada = entry.get().strip()
    if not entrada:
        messagebox.showwarning("Aviso", "Digite um domínio ou IP!")
        return

    last_entrada = entrada

    result_text.delete(1.0, tk.END)

    result_text.tag_configure("analise", font=("Consolas", 12, "bold"))
    result_text.insert(tk.END, f"🔍 Analisando: {entrada}\n", "analise")
    
    progress_bar['value'] = 0

    thread = threading.Thread(target=perform_lookup, 
                             args=(entrada, update_progress, update_result), 
                             daemon=True)
    thread.start()


def update_progress(value):
    root.after(0, lambda v=value: progress_bar.configure(value=v))


def update_result(full_text):
    root.after(0, lambda: update_gui(full_text))


def save_to_txt():
    if not result_text.get(1.0, tk.END).strip():
        messagebox.showwarning("Aviso", "Faça uma busca primeiro!")
        return
    filename = f"analise_{last_entrada}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=filename)
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(result_text.get(1.0, tk.END))
        messagebox.showinfo("Sucesso", f"Arquivo salvo\n\n{file_path}")


# ===================== INTERFACE =====================
root = tk.Tk()
root.title("🔎 IP Real + MX + Google Maps + BGP + whatismyip 🔍")
root.geometry("1030x860")

tk.Label(root, text="🔎 IP Real + MX + Google Maps + BGP + whatismyip 🔍", 
         font=("Arial", 16, "bold")).pack(pady=12)

frame = ttk.Frame(root)
frame.pack(pady=8, padx=20, fill="x")

frame = ttk.Frame(root)
frame.pack(pady=8)

ttk.Label(frame, text="Domínio",  font=("Arial", 9, "bold")
).pack(side="left", padx=(5, 0))

entry = ttk.Entry(frame, width=40, font=("Arial", 11, "bold"))
entry.pack(side="left", padx=5)

tk.Button(frame, text="🔎 Analisar", command=lookup, bg="#00cc00", fg="black", activebackground="#00ff00",
    activeforeground="black",
    font=("Arial", 10, "bold"),
    relief="raised",
    bd=2,
    padx=14
).pack(side="left", padx=8)

progress_frame = ttk.Frame(root)
progress_frame.pack(pady=5)

ttk.Label(progress_frame, text="Progresso:", font=("Arial", 8, "bold")).pack(side="left", padx=(0, 8))

progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=428, mode="determinate")
progress_bar.pack(side="left")

frame_text = tk.Frame(root)
frame_text.pack(pady=10)

result_text = tk.Text(
    frame_text,
    width=120,          # largura em caracteres
    height=33,          # altura em linhas
    font=("Consolas", 11),
    bg="#0a0a0a",
    fg="#00ff99"
)

result_text.pack()

btn_frame = ttk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="💾 Salvar", command=save_to_txt, bg="#ff8c00", fg="black",
    activebackground="#ffa500",
    activeforeground="black",
    font=("Arial", 10, "bold"),
    width=12,
    relief="raised",
    bd=2
).pack(side="left", padx=8)

tk.Button(btn_frame, text="🚪 Sair", command=root.quit, bg="#1e90ff", fg="black",
    activebackground="#4169e1",
    activeforeground="black",
    font=("Arial", 10, "bold"),
    width=12,
    relief="raised",
    bd=2
).pack(side="left", padx=8)


# ===================== RODAPÉ =====================
frame_rodape = tk.Frame(root, bg="#1e1e1e")
frame_rodape.pack(side="bottom", fill="x")

label_versao = tk.Label(
    frame_rodape,
    text="📌 Funcionamento: Resolve DNS ► Consulta MX ► Descobre IPs ► Ping ► ASN ► Empresa ► Geolocalização ► Google Maps ► BGP.he.net  ►  whatismyip "
    "\nClique duplo no link do Maps para abrir a localização.",
    bg="#1e1e1e",
    fg="#1CE00B",
    font=("Segoe UI", 10),
    wraplength=920,
    justify="center"
)

label_versao.pack(pady=5)

root.mainloop()
