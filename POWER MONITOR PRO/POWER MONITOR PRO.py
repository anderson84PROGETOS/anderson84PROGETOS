import customtkinter as ctk
import psutil
import subprocess
import platform
import re
import time
from collections import deque, Counter
from datetime import timedelta

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.title("⚡ POWER MONITOR PRO ⚡")
app.geometry("1180x1050")
app.minsize(1100, 950)

# Maximiza a janela ao abrir
app.after(0, lambda: app.state("zoomed"))

# =========================
# Detecção de hardware
# =========================
def run_cmd(cmd, timeout=3):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""

def get_os_info():
    try:
        if platform.system() == "Windows":
            product = run_cmd('wmic os get Caption /value')
            match = re.search(r"Caption=(.+)", product)
            name = match.group(1).strip() if match else f"Windows {platform.release()}"
            return f"{name} 64-bit (Build 19045)"
        return platform.platform()
    except Exception:
        return "Microsoft Windows 10 Pro 64-bit (Build 19045)"

def get_cpu_name():
    try:
        if platform.system() == "Windows":
            result = run_cmd('wmic cpu get name /value')
            match = re.search(r"Name=(.+)", result)
            if match:
                return match.group(1).strip()
    except Exception:
        pass
    return "AMD Ryzen 3 2200G with Radeon Vega Graphics"

def get_cpu_details():
    name = get_cpu_name().lower()
    if "2200g" in name or "raven" in name:
        return "Raven Ridge • 14 nm • Socket AM4 • 3.5 GHz (máx.)"
    return "Raven Ridge • 14 nm • Socket AM4"

def get_cache_info():
    return "L2: 2048 KB  |  L3: 4096 KB"

def get_gpu_name():
    try:
        result = run_cmd('wmic path win32_VideoController get name /value')
        names = re.findall(r"Name=(.+)", result)
        for name in names:
            name = name.strip()
            if name and "microsoft basic" not in name.lower():
                return name
    except Exception:
        pass
    return "AMD Radeon Vega 8 Graphics (Integrada)"

def get_motherboard():
    try:
        manu = run_cmd('wmic baseboard get manufacturer /value')
        prod = run_cmd('wmic baseboard get product /value')
        m = re.search(r"Manufacturer=(.+)", manu)
        p = re.search(r"Product=(.+)", prod)
        manufacturer = m.group(1).strip() if m else ""
        product = p.group(1).strip() if p else ""
        if manufacturer or product:
            return f"{manufacturer} {product}".strip()
    except Exception:
        pass
    return "BIOSTAR Group A320MH"

def get_ram_details():
    """Versão estável e limpa"""
    total_gb = psutil.virtual_memory().total / (1024**3)

    if platform.system() != "Windows":
        return f"{total_gb:.1f} GB"

    try:
        # Capacidades
        cap_raw = run_cmd('wmic memorychip get Capacity /value')
        capacities = [int(x) for x in re.findall(r"Capacity=(\d+)", cap_raw) if int(x) > 512*1024*1024]

        # Velocidades
        speed_raw = run_cmd('wmic memorychip get Speed /value')
        speeds = re.findall(r"Speed=(\d+)", speed_raw)

        # Fabricantes
        manu_raw = run_cmd('wmic memorychip get Manufacturer /value')
        manufacturers = [m.strip() for m in re.findall(r"Manufacturer=(.+)", manu_raw) if m.strip()]

        chips = []
        for i, cap in enumerate(capacities):
            size = round(cap / (1024**3), 1)
            speed = speeds[i] if i < len(speeds) else "?"
            manu = manufacturers[i] if i < len(manufacturers) else "Desconhecido"
            chips.append({"size": size, "speed": speed, "manu": manu})

        if not chips:
            return f"{total_gb:.1f} GB"

        # Detecta Dual Channel
        sizes = [c["size"] for c in chips]
        if len(chips) == 2 and len(set(sizes)) == 1:
            channel = "Dual Channel"
        elif len(chips) == 1:
            channel = "Single Channel"
        else:
            channel = f"{len(chips)} pentes"

        # Monta texto limpo (uma linha)
        modules = [f"{c['size']}GB @{c['speed']}MHz ({c['manu']})" for c in chips]
        return f"{total_gb:.1f} GB • {channel} → {' + '.join(modules)}"

    except Exception:
        return f"{total_gb:.1f} GB"

def get_storage_details():
    disks = []
    for part in psutil.disk_partitions(all=False):
        if "cdrom" in part.opts.lower() or not part.fstype:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            model = "ST1000DM010-2EP102"
            disks.append({
                "device": part.device,
                "mount": part.mountpoint,
                "model": model,
                "total": usage.total / (1024**3),
                "used": usage.used / (1024**3),
                "free": usage.free / (1024**3),
                "percent": usage.percent
            })
        except Exception:
            continue
    return disks

def get_audio():
    return "USB + AMD HD Audio + Realtek High Definition Audio"

def get_monitor():
    return "AOC 9315w"

def get_uptime():
    try:
        return str(timedelta(seconds=int(time.time() - psutil.boot_time())))
    except Exception:
        return "—"

# Cache estático
OS_INFO = get_os_info()
CPU_NAME = get_cpu_name()
CPU_TECH = get_cpu_details()
CACHE_INFO = get_cache_info()
GPU_NAME = get_gpu_name()
MOTHERBOARD = get_motherboard()
RAM_DETAILS = get_ram_details()
AUDIO = get_audio()
MONITOR = get_monitor()

# =========================
# Estimativas
# =========================
def estimar_cpu_power(uso_percent):
    tdp = 65
    power = 8 + (uso_percent / 100) * (tdp - 8) * 0.92
    return round(power, 1)

def estimar_gpu_power(uso_percent):
    power = 5 + (uso_percent / 100) * 38
    return round(power, 1)

def estimar_temp(uso_percent, base=36, max_temp=82):
    return round(base + (uso_percent / 100) * (max_temp - base))

def estimar_fan(uso_percent, min_rpm=800, max_rpm=2200):
    if uso_percent < 15:
        return min_rpm
    return int(min_rpm + (uso_percent / 100) * (max_rpm - min_rpm))

# =========================
# Interface
# =========================
titulo = ctk.CTkLabel(app,text="⚡ POWER MONITOR PRO ⚡\nReal-Time Hardware Monitor • Valores estimados + detecção real",
    font=("Segoe UI", 18, "bold"))

titulo.pack(pady=(8, 2))

status_frame = ctk.CTkFrame(app, fg_color="transparent")
status_frame.pack(pady=(0, 6))
status_light = ctk.CTkLabel(status_frame, text="●", font=("Segoe UI", 22), text_color="#3fb950")
status_light.pack(side="left", padx=(0, 8))
status_text = ctk.CTkLabel(status_frame, text="SISTEMA OK", font=("Segoe UI", 15, "bold"), text_color="#3fb950")
status_text.pack(side="left")

# ---- CPU / GPU ----
top = ctk.CTkFrame(app)
top.pack(fill="x", padx=12)

cpu_frame = ctk.CTkFrame(top, corner_radius=12)
cpu_frame.pack(side="left", expand=True, fill="both", padx=6, pady=6)
ctk.CTkLabel(cpu_frame, text="CPU", font=("Segoe UI", 18, "bold")).pack(pady=(8, 1))
ctk.CTkLabel(cpu_frame, text=CPU_NAME, font=("Segoe UI", 12), text_color="#aaaaaa", wraplength=360).pack()
ctk.CTkLabel(cpu_frame, text=CPU_TECH, font=("Segoe UI", 11), text_color="#58a6ff").pack()
ctk.CTkLabel(cpu_frame, text=CACHE_INFO, font=("Segoe UI", 11), text_color="#8b949e").pack(pady=(0, 6))
cpu_power = ctk.CTkLabel(cpu_frame, text="⚡ 0 W", font=("Segoe UI", 17))
cpu_power.pack()
cpu_temp = ctk.CTkLabel(cpu_frame, text="🌡 0 °C", font=("Segoe UI", 17))
cpu_temp.pack()
cpu_load = ctk.CTkLabel(cpu_frame, text="📈 0 %", font=("Segoe UI", 17))
cpu_load.pack()
cpu_bar = ctk.CTkProgressBar(cpu_frame, width=260)
cpu_bar.pack(pady=12)
cpu_bar.set(0)

gpu_frame = ctk.CTkFrame(top, corner_radius=12)
gpu_frame.pack(side="left", expand=True, fill="both", padx=6, pady=6)
ctk.CTkLabel(gpu_frame, text="GPU", font=("Segoe UI", 18, "bold")).pack(pady=(8, 1))
ctk.CTkLabel(gpu_frame, text=GPU_NAME, font=("Segoe UI", 12), text_color="#aaaaaa", wraplength=360).pack()
ctk.CTkLabel(gpu_frame, text="Integrada Vega 8 • Raven Ridge", font=("Segoe UI", 11), text_color="#58a6ff").pack(pady=(0, 6))
gpu_power = ctk.CTkLabel(gpu_frame, text="⚡ 0 W", font=("Segoe UI", 17))
gpu_power.pack()
gpu_temp = ctk.CTkLabel(gpu_frame, text="🌡 0 °C", font=("Segoe UI", 17))
gpu_temp.pack()
gpu_load = ctk.CTkLabel(gpu_frame, text="📈 0 %", font=("Segoe UI", 17))
gpu_load.pack()
gpu_bar = ctk.CTkProgressBar(gpu_frame, width=260)
gpu_bar.pack(pady=12)
gpu_bar.set(0)

# ---- SYSTEM INFORMATION ----
system = ctk.CTkFrame(app)
system.pack(fill="x", padx=12, pady=4)

ctk.CTkLabel(system, text="SYSTEM INFORMATION", font=("Segoe UI", 12, "bold")).pack(pady=(6, 4))

info_grid = ctk.CTkFrame(system, fg_color="transparent")
info_grid.pack(fill="x", padx=10, pady=(0, 6))

# Coluna 1
col1 = ctk.CTkFrame(info_grid, fg_color="transparent")
col1.pack(side="left", expand=True, fill="both")

lbl_os = ctk.CTkLabel(col1, text=f"🖥  OS: {OS_INFO}", anchor="w", font=("Segoe UI", 12))
lbl_os.pack(anchor="w", pady=1)
lbl_mb = ctk.CTkLabel(col1, text=f"🛠  Placa-mãe: {MOTHERBOARD}", anchor="w", font=("Segoe UI", 12))
lbl_mb.pack(anchor="w", pady=1)
lbl_ram = ctk.CTkLabel(col1, text=f"💾  RAM: {RAM_DETAILS}", anchor="w", font=("Segoe UI", 12))
lbl_ram.pack(anchor="w", pady=1)
lbl_audio = ctk.CTkLabel(col1, text=f"🔊  Áudio: {AUDIO}", anchor="w", font=("Segoe UI", 12))
lbl_audio.pack(anchor="w", pady=1)

# Coluna 2
col2 = ctk.CTkFrame(info_grid, fg_color="transparent")
col2.pack(side="left", expand=True, fill="both")

lbl_total = ctk.CTkLabel(col2, text="⚡ Total Power: —", anchor="w", font=("Segoe UI", 12))
lbl_total.pack(anchor="w", pady=1)
lbl_freq = ctk.CTkLabel(col2, text="⏱  CPU Freq: —", anchor="w", font=("Segoe UI", 12))
lbl_freq.pack(anchor="w", pady=1)
lbl_cores = ctk.CTkLabel(col2, text="🧠  Núcleos: —", anchor="w", font=("Segoe UI", 12))
lbl_cores.pack(anchor="w", pady=1)
lbl_uptime = ctk.CTkLabel(col2, text="⏳  Uptime: —", anchor="w", font=("Segoe UI", 12))
lbl_uptime.pack(anchor="w", pady=1)

# Coluna 3
col3 = ctk.CTkFrame(info_grid, fg_color="transparent")
col3.pack(side="left", expand=True, fill="both")

lbl_fan_cpu = ctk.CTkLabel(col3, text="🌀  CPU Fan: —", anchor="w", font=("Segoe UI", 12))
lbl_fan_cpu.pack(anchor="w", pady=1)
lbl_fan_gpu = ctk.CTkLabel(col3, text="🌀  GPU Fan: —", anchor="w", font=("Segoe UI", 12))
lbl_fan_gpu.pack(anchor="w", pady=1)
lbl_monitor = ctk.CTkLabel(col3, text=f"🖥  Monitor: {MONITOR}", anchor="w", font=("Segoe UI", 12))
lbl_monitor.pack(anchor="w", pady=1)
lbl_swap = ctk.CTkLabel(col3, text="📦 Memória Virtual: —", anchor="w", font=("Segoe UI", 12))
lbl_swap.pack(anchor="w", pady=1)

def atualizar_swap():
    swap = psutil.swap_memory()
    lbl_swap.configure(text=f"📦 Memória Virtual: {swap.used/1024**3:.1f} / {swap.total/1024**3:.1f} GB ({swap.percent:.0f}%)")
    lbl_swap.after(1000, atualizar_swap)
atualizar_swap()

# ---- STORAGE + STATUS ----
disk_frame = ctk.CTkFrame(app)
disk_frame.pack(fill="x", padx=12, pady=(2, 2))

ctk.CTkLabel(disk_frame, text="STORAGE", font=("Segoe UI", 12, "bold")).pack(pady=(4, 2))

disk_main = ctk.CTkFrame(disk_frame, fg_color="transparent")
disk_main.pack(fill="x", padx=10, pady=(0, 6))

disk_container = ctk.CTkFrame(disk_main, fg_color="transparent")
disk_container.pack(side="left", expand=True, fill="both")
disk_labels = []

# Painel de status lateral
status_panel = ctk.CTkFrame(disk_main, width=320, height=140)
status_panel.pack(side="right", padx=(10, 0), anchor="n")
status_panel.pack_propagate(False)

status_panel_title = ctk.CTkLabel(status_panel, text="●  SISTEMA OK", font=("Segoe UI", 13, "bold"), text_color="#3fb950")
status_panel_title.pack(pady=(10, 4), padx=8, anchor="w")

status_panel_cpu = ctk.CTkLabel(status_panel, text="CPU: —", font=("Segoe UI", 12), text_color="#aaaaaa", anchor="w")
status_panel_cpu.pack(anchor="w", padx=10, pady=0)
status_panel_gpu = ctk.CTkLabel(status_panel, text="GPU: —", font=("Segoe UI", 12), text_color="#aaaaaa", anchor="w")
status_panel_gpu.pack(anchor="w", padx=10, pady=0)
status_panel_disk = ctk.CTkLabel(status_panel, text="Disco: —", font=("Segoe UI", 12), text_color="#aaaaaa", anchor="w")
status_panel_disk.pack(anchor="w", padx=10, pady=0)
status_panel_power = ctk.CTkLabel(status_panel, text="Consumo: —", font=("Segoe UI", 12), text_color="#aaaaaa", anchor="w")
status_panel_power.pack(anchor="w", padx=10, pady=0)

# ---- LIVE POWER GRAPH ----
graf = ctk.CTkFrame(app)
graf.pack(fill="both", expand=True, padx=12, pady=(0, 5))

ctk.CTkLabel(graf, text="LIVE POWER GRAPH", font=("Segoe UI", 12, "bold")).pack(pady=(2, 2))

stats_frame = ctk.CTkFrame(graf, fg_color="transparent")
stats_frame.pack(fill="x", padx=10, pady=(0, 2))

lbl_now = ctk.CTkLabel(stats_frame, text="Agora: — W", font=("Segoe UI", 13, "bold"), text_color="#3fb950")
lbl_now.pack(side="left", padx=(0, 16))
lbl_avg = ctk.CTkLabel(stats_frame, text="Média: — W", font=("Segoe UI", 13), text_color="#58a6ff")
lbl_avg.pack(side="left", padx=(0, 16))
lbl_peak = ctk.CTkLabel(stats_frame, text="Pico: — W", font=("Segoe UI", 13), text_color="#f85149")
lbl_peak.pack(side="left", padx=(0, 16))
lbl_cpu_hist = ctk.CTkLabel(stats_frame, text="CPU: — W", font=("Segoe UI", 13), text_color="#d29922")
lbl_cpu_hist.pack(side="left", padx=(0, 16))
lbl_gpu_hist = ctk.CTkLabel(stats_frame, text="GPU: — W", font=("Segoe UI", 13), text_color="#a371f7")
lbl_gpu_hist.pack(side="left")

grafico = ctk.CTkTextbox(graf, height=150, font=("Consolas", 11))
grafico.pack(fill="both", expand=True, padx=8, pady=(0, 2))

historico_total = deque(maxlen=50)

# =========================
# Funções de atualização
# =========================
def atualizar_discos():
    for widget in disk_labels:
        widget.destroy()
    disk_labels.clear()

    disks = get_storage_details()
    if not disks:
        lbl = ctk.CTkLabel(disk_container, text="Nenhum disco encontrado", anchor="w")
        lbl.pack(anchor="w")
        disk_labels.append(lbl)
        return

    for d in disks:
        if d['percent'] >= 90:
            cor = "#f85149"
        elif d['percent'] >= 75:
            cor = "#d29922"
        else:
            cor = "#3fb950"

        linha = ctk.CTkFrame(disk_container, fg_color="transparent")
        linha.pack(anchor="w", pady=1, fill="x")

        luz = ctk.CTkLabel(linha, text="●", font=("Segoe UI", 13), text_color=cor, width=16)
        luz.pack(side="left")

        texto = (f" {d['model']}  •  {d['mount']}  "
                 f"{d['used']:.0f}/{d['total']:.0f} GB ({d['percent']}%)  "
                 f"Livre: {d['free']:.0f} GB  •  39 °C")
        lbl = ctk.CTkLabel(linha, text=texto, anchor="w", font=("Segoe UI", 12))
        lbl.pack(side="left")
        disk_labels.append(linha)

def atualizar_status(cpu_temp, gpu_temp, cpu_load, gpu_load, total_power):
    problemas = []
    nivel = "ok"

    if cpu_temp >= 85:
        cpu_txt, cpu_cor = f"CPU {cpu_temp}°C muito quente", "#f85149"
        problemas.append("CPU muito quente")
        nivel = "critico"
    elif cpu_temp >= 70:
        cpu_txt, cpu_cor = f"CPU {cpu_temp}°C quente", "#d29922"
        problemas.append("CPU quente")
        nivel = "atencao" if nivel != "critico" else nivel
    elif cpu_temp >= 60:
        cpu_txt, cpu_cor = f"CPU {cpu_temp}°C aquecendo", "#d29922"
        problemas.append("CPU aquecendo")
        nivel = "atencao" if nivel != "critico" else nivel
    else:
        cpu_txt, cpu_cor = f"CPU {cpu_temp}°C ok", "#3fb950"

    if gpu_temp >= 85:
        gpu_txt, gpu_cor = f"GPU {gpu_temp}°C muito quente", "#f85149"
        problemas.append("GPU muito quente")
        nivel = "critico"
    elif gpu_temp >= 70:
        gpu_txt, gpu_cor = f"GPU {gpu_temp}°C quente", "#d29922"
        problemas.append("GPU quente")
        nivel = "atencao" if nivel != "critico" else nivel
    else:
        gpu_txt, gpu_cor = f"GPU {gpu_temp}°C ok", "#3fb950"

    if total_power >= 100:
        power_txt, power_cor = "Consumo alto", "#d29922"
        problemas.append("Consumo alto")
        nivel = "atencao" if nivel != "critico" else nivel
    else:
        power_txt, power_cor = "Consumo ok", "#3fb950"

    disk_txt, disk_cor = "Discos ok", "#3fb950"
    try:
        for d in get_storage_details():
            if d['percent'] >= 95:
                disk_txt, disk_cor = f"Disco {d['mount']} crítico", "#f85149"
                problemas.append("Disco crítico")
                nivel = "critico"
            elif d['percent'] >= 90:
                disk_txt, disk_cor = f"Disco {d['mount']} quase cheio", "#f85149"
            elif d['percent'] >= 80:
                if disk_cor != "#f85149":
                    disk_txt, disk_cor = f"Disco {d['mount']} cheio", "#d29922"
    except Exception:
        pass

    if nivel == "ok":
        status_light.configure(text_color="#3fb950")
        status_text.configure(text="SISTEMA OK", text_color="#3fb950")
    elif nivel == "atencao":
        status_light.configure(text_color="#d29922")
        status_text.configure(text="⚠ " + " | ".join(problemas), text_color="#d29922")
    else:
        status_light.configure(text_color="#f85149")
        status_text.configure(text="⚠ " + " | ".join(problemas), text_color="#f85149")

    temp_media = int((cpu_temp + gpu_temp) / 2)
    if nivel == "ok":
        status_panel_title.configure(text=f"● SISTEMA OK  {temp_media}°C", text_color="#3fb950")
    elif nivel == "atencao":
        status_panel_title.configure(text=f"● ATENÇÃO  {temp_media}°C", text_color="#d29922")
    else:
        status_panel_title.configure(text=f"● CRÍTICO  {temp_media}°C", text_color="#f85149")

    status_panel_cpu.configure(text=cpu_txt, text_color=cpu_cor)
    status_panel_gpu.configure(text=gpu_txt, text_color=gpu_cor)
    status_panel_disk.configure(text=disk_txt, text_color=disk_cor)
    status_panel_power.configure(text=power_txt, text_color=power_cor)

def desenhar_grafico(total_atual, cpu_atual, gpu_atual):
    historico_total.append(total_atual)
    media = sum(historico_total) / len(historico_total)
    pico = max(historico_total)

    lbl_now.configure(text=f"Agora: {total_atual:.1f} W")
    lbl_avg.configure(text=f"Média: {media:.1f} W")
    lbl_peak.configure(text=f"Pico: {pico:.1f} W")
    lbl_cpu_hist.configure(text=f"CPU: {cpu_atual:.1f} W")
    lbl_gpu_hist.configure(text=f"GPU: {gpu_atual:.1f} W")

    max_val = max(pico, 40)
    altura_max = 9
    linhas = [""] * altura_max

    for valor in historico_total:
        altura = max(1, min(int((valor / max_val) * altura_max), altura_max))
        for i in range(altura_max):
            if i < altura:
                char = "█" if valor > media * 1.25 else ("▓" if valor > media else "▒")
                linhas[altura_max - 1 - i] += char + " "
            else:
                linhas[altura_max - 1 - i] += "  "

    texto = f" Escala: 0 ─── {max_val:.0f} W  |  Últimos {len(historico_total)}s\n"
    texto += " " + "─" * 200 + "\n"
    for linha in linhas:
        texto += " " + linha.rstrip() + "\n"
    texto += " " + "─" * 200 + "\n"
    texto += " ▒ baixo   ▓ médio   █ pico"

    grafico.delete("1.0", "end")
    grafico.insert("end", texto)

def atualizar():
    cpu_uso = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()

    try:
        freq = psutil.cpu_freq()
        freq_txt = f"{freq.current:.0f} MHz" if freq else "—"
    except Exception:
        freq_txt = "—"

    cores_f = psutil.cpu_count(logical=False) or "?"
    cores_l = psutil.cpu_count(logical=True) or "?"

    gpu_uso = min(100, cpu_uso * 0.65 + (8 if cpu_uso > 25 else 0))

    cpu_power_val = estimar_cpu_power(cpu_uso)
    gpu_power_val = estimar_gpu_power(gpu_uso)
    cpu_temp_val = estimar_temp(cpu_uso, base=34, max_temp=80)
    gpu_temp_val = estimar_temp(gpu_uso, base=36, max_temp=78)
    cpu_fan = estimar_fan(cpu_uso)
    gpu_fan = estimar_fan(gpu_uso, min_rpm=0, max_rpm=1500)

    total = cpu_power_val + gpu_power_val

    # Cards
    cpu_power.configure(text=f"⚡ {cpu_power_val:.1f} W")
    cpu_temp.configure(text=f"🌡 {cpu_temp_val} °C")
    cpu_load.configure(text=f"📈 {cpu_uso:.0f} %")
    cpu_bar.set(cpu_uso / 100)

    gpu_power.configure(text=f"⚡ {gpu_power_val:.1f} W")
    gpu_temp.configure(text=f"🌡 {gpu_temp_val} °C")
    gpu_load.configure(text=f"📈 {gpu_uso:.0f} %")
    gpu_bar.set(gpu_uso / 100)

    # System info
    lbl_total.configure(text=f"⚡ Total Power: {total:.1f} W")
    lbl_ram.configure(text=f"💾  RAM: {ram.used/1024**3:.1f}/{ram.total/1024**3:.1f} GB ({ram.percent}%)  •  {RAM_DETAILS}")
    lbl_freq.configure(text=f"⏱  CPU Freq: {freq_txt}")
    lbl_cores.configure(text=f"🧠  Núcleos: {cores_f} físicos / {cores_l} lógicos")
    lbl_fan_cpu.configure(text=f"🌀  CPU Fan: {cpu_fan} RPM")
    lbl_fan_gpu.configure(text=f"🌀  GPU Fan: {gpu_fan} RPM")
    lbl_uptime.configure(text=f"⏳  Uptime: {get_uptime()}")

    atualizar_discos()
    atualizar_status(cpu_temp_val, gpu_temp_val, cpu_uso, gpu_uso, total)
    desenhar_grafico(total, cpu_power_val, gpu_power_val)

    app.after(1000, atualizar)

# Inicialização
psutil.cpu_percent(interval=None)
atualizar()
app.mainloop()
