import customtkinter as ctk
from tkinter import messagebox, filedialog, scrolledtext
import socket
import uuid
import getpass
import platform
import subprocess
import requests
import datetime
import psutil
import re
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ===================== FUNÇÕES DE REDE =====================

def obter_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "Desconhecido"


def obter_ip_local_ipv6():
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(
                "ipconfig", shell=True, text=True, encoding="cp850", errors="ignore"
            )
            for linha in output.splitlines():
                if "IPv6" in linha:
                    ipv6 = re.search(
                        r'([0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4}', linha
                    )
                    if ipv6:
                        return ipv6.group(0)
            for linha in output.splitlines():
                if "Link-local" in linha or "link-local" in linha.lower():
                    ipv6 = re.search(
                        r'([0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4}', linha
                    )
                    if ipv6:
                        return ipv6.group(0) + " (link-local)"
            return "Não encontrado"
        else:
            try:
                output = subprocess.check_output(
                    "ip -6 addr show scope global", shell=True, text=True, errors="ignore"
                )
                for linha in output.splitlines():
                    if "inet6" in linha:
                        ipv6 = re.search(
                            r'([0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4}', linha
                        )
                        if ipv6:
                            return ipv6.group(0)
            except:
                pass
            try:
                output = subprocess.check_output(
                    "ip -6 addr show scope link", shell=True, text=True, errors="ignore"
                )
                for linha in output.splitlines():
                    if "inet6" in linha:
                        ipv6 = re.search(
                            r'([0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4}', linha
                        )
                        if ipv6:
                            return ipv6.group(0) + " (link-local)"
            except:
                pass
            return "Não encontrado"
    except Exception as e:
        return f"Erro: {str(e)}"


def obter_gateway_ipv4_windows():
    try:
        output = subprocess.check_output(
            "route print -4 0.0.0.0", shell=True, text=True, encoding="cp850", errors="ignore"
        )
        for linha in output.splitlines():
            if linha.strip().startswith("0.0.0.0"):
                partes = linha.split()
                if len(partes) >= 3:
                    gateway = partes[2]
                    if re.match(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', gateway):
                        return gateway
        return None
    except:
        return None


def extrair_gateways_dns(info_rede):
    gateways_ipv4 = []
    gateways_ipv6 = []
    dns_servers = []

    linhas = info_rede.splitlines()

    for line in linhas:
        line_strip = line.strip()
        if re.search(r'(Default Gateway|Gateway|Gateway Padrão)', line_strip, re.IGNORECASE):
            if ":" in line_strip:
                partes = line_strip.split(":", 1)
                valor = partes[1].strip()
                ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', valor)
                for ip in ips:
                    if ip not in gateways_ipv4 and ip != "0.0.0.0":
                        gateways_ipv4.append(ip)
            full = re.search(r'([0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4}', line_strip)
            if full:
                g6 = full.group(0)
                if g6 != '::' and g6 not in gateways_ipv6:
                    gateways_ipv6.append(g6)

        if re.search(r'(DNS\s*Servers?|Servidor\s*DNS|DNS\s*Server)', line_strip, re.IGNORECASE):
            if ":" in line_strip:
                partes = line_strip.split(":", 1)
                valor = partes[1].strip()
                ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', valor)
                for d in ips:
                    if d not in dns_servers:
                        dns_servers.append(d)

    if not gateways_ipv4:
        for line in linhas:
            if 'gateway' in line.lower():
                ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line)
                for ip in ips:
                    if ip not in gateways_ipv4 and ip != "0.0.0.0":
                        gateways_ipv4.append(ip)

    if not gateways_ipv4:
        gw = obter_gateway_ipv4_windows()
        if gw:
            gateways_ipv4.append(gw)

    if not dns_servers:
        for line in linhas:
            if 'DNS' in line:
                ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line)
                for d in ips:
                    if d not in dns_servers:
                        dns_servers.append(d)

    if not gateways_ipv6:
        for line in linhas:
            if 'gateway' in line.lower() or 'padrão' in line.lower() or 'default' in line.lower():
                full = re.search(r'([0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4}', line)
                if full:
                    g6 = full.group(0)
                    if g6 != '::' and g6 not in gateways_ipv6:
                        gateways_ipv6.append(g6)

    gw_ipv4_str = ', '.join(gateways_ipv4) if gateways_ipv4 else "Não encontrado"
    gw_ipv6_str = ', '.join(gateways_ipv6) if gateways_ipv6 else "Não encontrado"
    dns_str = ', '.join(dns_servers) if dns_servers else "Não encontrado"

    return gw_ipv4_str, gw_ipv6_str, dns_str


def obter_info_rede():
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(
                "ipconfig /all", shell=True, text=True, encoding="cp850", errors="ignore"
            )
            return output
        else:
            try:
                output = subprocess.check_output("ifconfig", shell=True, text=True, errors="ignore")
            except:
                output = subprocess.check_output("ip addr", shell=True, text=True, errors="ignore")
            return output
    except Exception as e:
        return f"Erro ao obter informações de rede: {str(e)}"


def obter_ip_publico():
    servicos = [
        "https://api.ipify.org",
        "https://icanhazip.com",
        "https://checkip.amazonaws.com",
    ]
    for url in servicos:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.text.strip()
        except:
            continue
    return "Não foi possível obter IP público"


def obter_mac():
    try:
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ':'.join([mac[i:i+2] for i in range(0, 12, 2)]).upper()
    except:
        return "Desconhecido"


def obter_interfaces_rede():
    interfaces = []
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(
                "wmic nic get Name,NetEnabled /format:list",
                shell=True, text=True, encoding="cp850", errors="ignore"
            )
            nomes = re.findall(r'Name=(.+?)\r?\n', output)
            enabled = re.findall(r'NetEnabled=(.+?)\r?\n', output)
            for nome, ativa in zip(nomes, enabled):
                status = "ATIVA" if 'TRUE' in ativa else "DESATIVADA"
                interfaces.append(f"   [{status:<11}] - {nome.strip()}")
        else:
            output = subprocess.check_output(
                "ip -o link show | awk -F': ' '{print $2}'",
                shell=True, text=True, errors="ignore"
            )
            interfaces = [f"   {i}" for i in output.strip().splitlines() if i.strip()]
    except:
        interfaces = ["   Não foi possível listar"]
    return interfaces

# ===================== FUNÇÕES DE HARDWARE/RECURSOS =====================

def obter_uso_recursos():
    try:
        cpu = psutil.cpu_percent(interval=0.8)
        ram = psutil.virtual_memory().percent
        disco = psutil.disk_usage('/').percent

        cpu_freq = psutil.cpu_freq()
        freq_str = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "Desconhecido"
        cpu_cores_fisicos = psutil.cpu_count(logical=False)
        cpu_cores_logicos = psutil.cpu_count(logical=True)

        ram_total = psutil.virtual_memory().total / (1024**3)
        ram_usada = psutil.virtual_memory().used / (1024**3)

        disco_total = psutil.disk_usage('/').total / (1024**3)
        disco_usado = psutil.disk_usage('/').used / (1024**3)
        disco_livre = psutil.disk_usage('/').free / (1024**3)

        return {
            "cpu_percent": round(cpu, 1),
            "cpu_freq": freq_str,
            "cpu_cores_fisicos": cpu_cores_fisicos,
            "cpu_cores_logicos": cpu_cores_logicos,
            "ram_percent": round(ram, 1),
            "ram_total": round(ram_total, 2),
            "ram_usada": round(ram_usada, 2),
            "disco_percent": round(disco, 1),
            "disco_total": round(disco_total, 2),
            "disco_usado": round(disco_usado, 2),
            "disco_livre": round(disco_livre, 2),
        }
    except:
        return {
            "cpu_percent": 0, "cpu_freq": "Erro", "cpu_cores_fisicos": 0,
            "cpu_cores_logicos": 0, "ram_percent": 0, "ram_total": 0,
            "ram_usada": 0, "disco_percent": 0, "disco_total": 0,
            "disco_usado": 0, "disco_livre": 0
        }


def obter_processador():
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(
                "wmic cpu get Name", shell=True, text=True, encoding="cp850", errors="ignore"
            )
            return output.strip().split('\n')[-1].strip()
        else:
            output = subprocess.check_output(
                "cat /proc/cpuinfo | grep 'model name' | head -1",
                shell=True, text=True, errors="ignore"
            )
            return output.split(':')[1].strip() if ':' in output else "Desconhecido"
    except:
        return "Desconhecido"


def obter_gpu():
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(
                "wmic path win32_VideoController get Name",
                shell=True, text=True, encoding="cp850", errors="ignore"
            )
            linhas = [l.strip() for l in output.splitlines() if l.strip() and l.strip() != "Name"]
            return linhas[0] if linhas else "Não detectada"
        else:
            output = subprocess.check_output(
                "lspci | grep -i vga", shell=True, text=True, errors="ignore"
            )
            return output.split(':')[2].strip() if ':' in output else "Não detectada"
    except:
        return "Não detectada"


def obter_tempo_atividade():
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(
                "wmic os get LastBootUpTime", shell=True, text=True,
                encoding="cp850", errors="ignore"
            )
            linha = [l.strip() for l in output.splitlines() if l.strip() and l != "LastBootUpTime"]
            if linha:
                boot = linha[0]
                try:
                    dt = datetime.datetime.strptime(boot[:14], "%Y%m%d%H%M%S")
                    agora = datetime.datetime.now()
                    diff = agora - dt
                    dias = diff.days
                    horas = diff.seconds // 3600
                    minutos = (diff.seconds % 3600) // 60
                    return f"{dias}d {horas}h {minutos}m"
                except:
                    return "Consultar task manager"
            return "Desconhecido"
        else:
            output = subprocess.check_output("uptime -p", shell=True, text=True, errors="ignore")
            return output.strip()
    except:
        return "Desconhecido"

# ===================== FUNÇÃO PRINCIPAL DE ATUALIZAÇÃO =====================

def atualizar_informacoes(text_widget):
    try:
        info_rede = obter_info_rede()
        gw_ipv4, gw_ipv6, dns = extrair_gateways_dns(info_rede)
        recursos = obter_uso_recursos()
        interfaces = obter_interfaces_rede()

        interfaces_str = '\n\n'.join(interfaces) if interfaces else "   Nenhuma"
        ip_local_v6 = obter_ip_local_ipv6()

        # Partições de disco
        discos = []
        for part in psutil.disk_partitions():
            try:
                uso = psutil.disk_usage(part.mountpoint)
                discos.append(
                    f" {part.device:<5} "
                    f"{uso.percent:>5.1f}% usado  {uso.free / (1024**3):>10.1f}GB livre"
                )
            except:
                discos.append(f" {part.device:<5}")
        discos_str = '\n\n'.join(discos) if discos else "   N/A"

        info = f"""╔══════════════════════════════════════════════════════════════╗
║           INFORMAÇÕES COMPLETAS DO SISTEMA                   ║
╚══════════════════════════════════════════════════════════════╝

📅 Data/Hora              {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

━━━━━━━━━━━━━━━━━━ HARDWARE ━━━━━━━━━━━━━━━━━━

🖥️  Computador             {platform.node()}

👤  Usuário                   {getpass.getuser()}

⚙️  Sistema                  {platform.system()} {platform.release()} ({platform.version()})

🏗️  Arquitetura             {platform.machine()}

🕒  Atividade                 {obter_tempo_atividade()}

💻  Processador               {obter_processador()}

🎮  GPU                       {obter_gpu()}

🧠  CPU Física                {recursos['cpu_cores_fisicos']} núcleos

    CPU Lógica                {recursos['cpu_cores_logicos']} threads

⚡  CPU Frequência           {recursos['cpu_freq']}

━━━━━━━━━━━━━━━━━━ DISCOS ━━━━━━━━━━━━━━━━━━

{discos_str}

━━━━━━━━━━━━━━━━━━ REDE ━━━━━━━━━━━━━━━━━━

🌐  IP Local (IPv4)        : {obter_ip_local():<30}

🌐  IP Local (IPv6)        : {ip_local_v6:<30}

🌍  IP Público             : {obter_ip_publico():<30}

🔗  MAC Address            : {obter_mac():<30}

📡  Gateway IPv4           : {gw_ipv4:<30}

📡  Gateway IPv6           : {gw_ipv6:<30}

🌐  DNS Servers            : {dns:<30}



━━━━━━━━━━━━━━━━━━ Interfaces ━━━━━━━━━━━━━━━━━━

{interfaces_str}


━━━━━━━━━━━━━━━━━━ RECURSOS ━━━ ATUAL ━━━ MÁXIMO ━━━ LIVRE ━━━━━━━━

🧠  CPU        : {recursos['cpu_percent']:>5}%

💾  RAM        : {recursos['ram_percent']:>5}%   ({recursos['ram_usada']:>6}GB / {recursos['ram_total']:>6}GB)

💿  Disco (/)  : {recursos['disco_percent']:>5}%   ({recursos['disco_usado']:>6}GB / {recursos['disco_total']:>6}GB)  Livre: {recursos['disco_livre']:>6}GB



{'='*70}
INFORMAÇÕES COMPLETAS DA REDE (ipconfig /all)
{'='*70}
{info_rede}
"""
        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", info)
        return info
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro:\n{str(e)}")
        import traceback
        traceback.print_exc()
        return ""

# ===================== FUNÇÕES AUXILIARES DA INTERFACE =====================

def copiar_tudo(text_widget):
    texto = text_widget.get("1.0", "end").strip()
    if texto:
        root.clipboard_clear()
        root.clipboard_append(texto)
        messagebox.showinfo("Copiado", "Todo o conteudo foi copiado!")


def salvar_txt(text_widget):
    texto = text_widget.get("1.0", "end").strip()
    if not texto:
        messagebox.showwarning("Aviso", "Nada para salvar.")
        return
    try:
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt")],
            title="Salvar Informacoes"
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(texto)
            messagebox.showinfo("Salvo", f"Arquivo salvo em:\n{filename}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")

# ===================== INTERFACE GRÁFICA =====================

root = ctk.CTk()
root.title("Informacoes do Sistema e Rede")
root.geometry("1100x850")

# Maximiza a janela depois que ela carrega
root.after(100, lambda: root.state("zoomed"))

ctk.CTkLabel(
    root, text="Informacoes Completas do Sistema",
    font=ctk.CTkFont(size=24, weight="bold")
).pack(pady=15)

text_frame = ctk.CTkFrame(root)
text_frame.pack(padx=30, pady=10, fill="both", expand=True)

text_widget = scrolledtext.ScrolledText(
    text_frame,
    wrap="word",
    font=("Consolas", 11, "bold"),
    bg="#161616",
    fg="#09bd18",
    insertbackground="white",
    padx=10,
    pady=10
)
text_widget.pack(padx=15, pady=15, fill="both", expand=True)

btn_frame = ctk.CTkFrame(root)
btn_frame.pack(pady=15)

ctk.CTkButton(
    btn_frame, text="Atualizar", width=160, height=45,
    command=lambda: atualizar_informacoes(text_widget)
).pack(side="left", padx=12)

ctk.CTkButton(
    btn_frame, text="Copiar Tudo", width=160, height=45,
    command=lambda: copiar_tudo(text_widget)
).pack(side="left", padx=12)

ctk.CTkButton(
    btn_frame, text="Salvar em TXT", width=160, height=45,
    command=lambda: salvar_txt(text_widget)
).pack(side="left", padx=12)

# Mensagem inicial
text_widget.insert("1.0", "Clique em 'Atualizar' para exibir as informações do sistema.\n\nA janela pode travar brevemente durante a coleta dos dados.")

root.mainloop()
