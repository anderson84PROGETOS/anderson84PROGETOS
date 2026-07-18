import os
import psutil
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import winsound
import hashlib
import webbrowser
import ctypes
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict

# ==================== CONSTANTES ====================
SUSPECT_EXTENSIONS = {'.exe', '.dll', '.scr', '.vbs', '.ps1', '.bat', '.cmd', '.jar', '.vbe', '.js', '.jse', '.wsf', '.wsh'}
SUSPECT_DIRS = [r'C:\Windows\Temp', os.environ.get('TEMP', ''), os.environ.get('APPDATA', ''), 
                os.environ.get('LOCALAPPDATA', ''), os.environ.get('PUBLIC', ''),
                os.path.join(os.environ.get('PROGRAMDATA', ''), 'Microsoft\Windows\Start Menu')]

SUSPICIOUS_PORTS_RANGE = [(4444, 4445), (1337, 1338), (31337, 31338), (5555, 5556), (6660, 6670), (8888, 8889)]

# ==================== CLASSIFICAÇÃO ====================
suspeitos_detectados = []  # (target, hash, score)
scan_active = threading.Event()

class ThreatScore:
    """Sistema de pontuação para classificar ameaças"""
    def __init__(self):
        self.scores = defaultdict(float)
        self.evidences = defaultdict(list)
    
    def add(self, category, score, evidence):
        self.scores[category] += score
        if evidence not in self.evidences[category]:
            self.evidences[category].append(evidence)
    
    @property
    def total(self):
        return sum(self.scores.values())
    
    @property
    def classification(self):
        t = self.total
        if t >= 70: return "🔥 CRÍTICO", "#ff0000"
        if t >= 40: return "⚠️ ALTO", "#ff6600"
        if t >= 20: return "⚡ MÉDIO", "#ffaa00"
        if t >= 10: return "🔵 BAIXO", "#4488ff"
        return "⚪ INOFENSIVO", "#00ff00"

# ==================== FUNÇÕES SEGURAS DE THREAD (CORRIGIDAS) ====================
def safe_insert(output_box, text, tag=None):
    """Inserir texto na GUI de forma thread-safe - SEM recursão"""
    output_box.after(0, lambda tb=output_box, t=text, tg=tag: tb.insert(tk.END, t, tg) if tb.winfo_exists() else None)

def safe_update_progress(progress_bar, value):
    """Atualizar barra de progresso de forma thread-safe - SEM recursão"""
    progress_bar.after(0, lambda pb=progress_bar, v=value: pb.configure(value=v) if pb.winfo_exists() else None)

def safe_messagebox(title, message, icon='warning'):
    """Mostrar messagebox na thread principal"""
    janela.after(0, lambda: messagebox.showwarning(title, message) if icon == 'warning' else (
        messagebox.showinfo(title, message) if icon == 'info' else messagebox.showerror(title, message)))

# ==================== DETECTORES ====================

def check_process_behavior():
    """Analisa comportamento de processos em execução"""
    threats = []
    
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'connections', 'create_time', 'username']):
        try:
            pinfo = proc.info
            ts = ThreatScore()
            pname = (pinfo['name'] or '').lower()
            pexe = (pinfo['exe'] or '').lower()
            
            # 1. Processo rodando de diretório suspeito
            for sus_dir in SUSPECT_DIRS:
                if sus_dir and sus_dir.lower() in pexe:
                    ts.add('local', 15, f'Executando de: {pexe}')
                    break
            
            # 2. Processo não-assinado rodando em AppData/Temp
            if any(d in pexe for d in ['appdata', 'temp', '\\temp\\', '\\tmp\\']):
                ext = os.path.splitext(pexe)[1]
                if ext in SUSPECT_EXTENSIONS:
                    ts.add('local', 10, f'Executável não-assinado em diretório suspeito')
            
            # 3. Conexões para portas suspeitas (RAT/reverse shell)
            try:
                conns = proc.connections()
                for conn in conns:
                    if conn.raddr:
                        ip = conn.raddr.ip
                        port = conn.raddr.port
                        for low, high in SUSPICIOUS_PORTS_RANGE:
                            if low <= port <= high:
                                ts.add('network', 25, f'Conexão porta suspeita {ip}:{port}')
                                break
                        if 'temp' in pexe and not ip.startswith(('127.', '192.168.', '10.', '172.16.')):
                            ts.add('network', 20, f'Conexão externa de processo em Temp: {ip}:{port}')
            except:
                pass
            
            # 4. Processo filho suspeito
            try:
                children = proc.children()
                for child in children:
                    cname = child.name().lower()
                    if cname in ('cmd.exe', 'powershell.exe', 'wscript.exe', 'cscript.exe'):
                        ts.add('process', 15, f'Processo filho suspeito: {cname}')
            except:
                pass
            
            # 5. Tempo de execução recente em local suspeito
            try:
                create_time = datetime.fromtimestamp(pinfo['create_time'])
                if create_time > datetime.now() - timedelta(hours=24):
                    if any(d in pexe for d in ['temp', 'appdata', '\\users\\']):
                        ts.add('local', 5, f'Criado recentemente (<24h) em local suspeito')
            except:
                pass
            
            # 6. Nomes de processos mascarados (typosquatting)
            legit_names = ['svchost.exe', 'lsass.exe', 'explorer.exe', 'winlogon.exe', 'services.exe',
                          'csrss.exe', 'smss.exe', 'spoolsv.exe', 'taskhost.exe', 'conhost.exe']
            for legit in legit_names:
                if pname != legit and pname.replace('i', 'l').replace('o', '0') == legit:
                    ts.add('deception', 30, f'Typosquatting: {pname} (parece {legit})')
                    break
                if pname and legit and len(pname) == len(legit):
                    if sum(1 for a, b in zip(pname, legit) if a != b) <= 2 and pname != legit:
                        ts.add('deception', 25, f'Possível homógrafo: {pname}')
                        break
            
            if ts.total >= 20:
                threats.append((proc, ts))
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    name_counts = defaultdict(int)
    for proc, ts in threats:
        name_counts[proc.info['name']] += 1
    
    final_threats = []
    for proc, ts in threats:
        if name_counts[proc.info['name']] >= 3:
            ts.add('process', 15, f'Múltiplas instâncias ({name_counts[proc.info["name"]]}) do mesmo processo')
        final_threats.append((proc, ts))
    
    return final_threats

def check_file_behavior(filepath):
    """Analisa comportamento de um arquivo"""
    ts = ThreatScore()
    filename = os.path.basename(filepath).lower()
    ext = os.path.splitext(filename)[1].lower()
    
    if not os.path.exists(filepath):
        return None
    
    if ext in SUSPECT_EXTENSIONS:
        ts.add('local', 5, f'Extensão executável: {ext}')
    
    for sus_dir in SUSPECT_DIRS:
        if sus_dir and sus_dir.lower() in filepath.lower():
            ts.add('local', 15, f'Localizado em diretório suspeito: {sus_dir}')
            break
    
    try:
        size = os.path.getsize(filepath)
        if ext == '.exe' and size < 10240:
            ts.add('local', 5, f'Executável anormalmente pequeno: {size} bytes')
        if ext == '.dll' and size > 50 * 1024 * 1024:
            ts.add('local', 5, f'DLL anormalmente grande: {size/1024/1024:.1f}MB')
    except:
        pass
    
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
        if mtime > datetime.now() - timedelta(days=7):
            if any(d in filepath.lower() for d in ['temp', 'appdata', '\\users\\']):
                ts.add('local', 10, f'Modificado recentemente (<7 dias)')
    except:
        pass
    
    suspicious_name_patterns = [
        (r'keylog', 'keylogger', 25), (r'rat\.', 'RAT', 25), 
        (r'backdoor', 'backdoor', 25), (r'steal', 'stealer', 20),
        (r'dump.*(pass|cred)', 'credential dumper', 25),
        (r'(miner|monero|xmrig)', 'cryptominer', 25),
        (r'reverse.*shell', 'reverse shell', 30),
        (r'payload', 'payload', 15), (r'exploit', 'exploit', 15),
    ]
    
    for pattern, desc, score in suspicious_name_patterns:
        if re.search(pattern, filename):
            ts.add('naming', score, f'Nome sugestivo de {desc}: {filename}')
            break
    
    double_ext = re.search(r'\.\w+\.\w+$', filename)
    if double_ext and ext in SUSPECT_EXTENSIONS:
        ts.add('deception', 20, f'Extensão dupla detectada: {filename}')
    
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(filepath)
        if attrs != -1 and attrs & 2:
            ts.add('deception', 10, 'Arquivo oculto')
    except:
        pass
    
    if ts.total >= 5 and ext in {'.exe', '.dll', '.scr', '.ps1', '.vbs', '.bat'}:
        try:
            with open(filepath, 'rb') as f:
                content = f.read(1024 * 1024)
            text_content = content.decode('latin-1', errors='replace').lower()
            yara_hits = []
            if re.search(r'getasynckeystate|setwindowshookex', text_content):
                yara_hits.append(('Keylogger API', 30))
            if re.search(r'socket.*connect|connect.*socket', text_content):
                if re.search(r'/bin/bash|cmd\.exe|powershell', text_content):
                    yara_hits.append(('Reverse Shell', 35))
            if re.search(r'stratum.*pool|pool.*stratum|xmrig|monero|cryptonight', text_content):
                yara_hits.append(('Cryptominer', 30))
            if re.search(r'password.*(chrome|firefox)|credential.*dump|secrets\b', text_content):
                yara_hits.append(('Credential Stealer', 30))
            for yara_name, yara_score in yara_hits:
                ts.add('yara', yara_score, f'Regra YARA: {yara_name}')
        except:
            pass
    
    return ts if ts.total > 0 else None

def check_windows_persistence():
    """Verifica entradas de persistência no Windows"""
    threats = []
    
    try:
        import winreg
        run_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        ]
        for hkey, path in run_keys:
            try:
                with winreg.OpenKey(hkey, path) as key:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            value_lower = value.lower()
                            for sus_dir in SUSPECT_DIRS:
                                if sus_dir and sus_dir.lower() in value_lower:
                                    ts = ThreatScore()
                                    ts.add('persistence', 30, f'RunKey "{name}" -> {value}')
                                    threats.append((f'RunKey: {name}', ts))
                                    break
                            i += 1
                        except WindowsError:
                            break
            except:
                pass
    except:
        pass
    
    try:
        # CORREÇÃO: ocultar janela do CMD
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        result = subprocess.run(['schtasks', '/query', '/fo', 'LIST', '/v'], 
                              capture_output=True, timeout=15,
                              startupinfo=startupinfo,
                              creationflags=subprocess.CREATE_NO_WINDOW)
        stdout = result.stdout.decode('utf-8', errors='replace')
        lines = stdout.split('\n')
        current_task = {}
        for line in lines:
            if ':' in line:
                key, val = line.split(':', 1)
                current_task[key.strip()] = val.strip()
            if line.strip() == '' and current_task:
                task_name = current_task.get('TaskName', '')
                task_cmd = current_task.get('Task To Run', '')
                if task_cmd:
                    for sus_dir in SUSPECT_DIRS:
                        if sus_dir and sus_dir.lower() in task_cmd.lower():
                            ts = ThreatScore()
                            ts.add('persistence', 25, f'Scheduled Task: {task_name} -> {task_cmd}')
                            threats.append((f'Task: {task_name}', ts))
                            break
                current_task = {}
    except:
        pass
    
    startup_paths = [
        os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs\Startup'),
        os.path.join(os.environ.get('PROGRAMDATA', ''), r'Microsoft\Windows\Start Menu\Programs\Startup'),
    ]
    for sp in startup_paths:
        if os.path.exists(sp):
            for item in os.listdir(sp):
                item_path = os.path.join(sp, item)
                ts = check_file_behavior(item_path)
                if ts and ts.total >= 10:
                    ts.add('persistence', 15, f'Startup Folder: {item}')
                    threats.append((item_path, ts))
    
    return threats

def check_network_anomalies():
    """Verifica anomalias de rede além de conexões de processo"""
    threats = []
    connections_by_ip = defaultdict(list)
    
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            conns = proc.connections()
            for conn in conns:
                if conn.raddr:
                    ip = conn.raddr.ip
                    if not ip.startswith(('127.', '192.168.', '10.', '172.16.', '169.254.')):
                        connections_by_ip[(ip, conn.raddr.port)].append(proc.info)
        except:
            continue
    
    if len(connections_by_ip) > 10:
        ts = ThreatScore()
        ts.add('network', 20, f'Múltiplas conexões externas: {len(connections_by_ip)} IPs/portas')
        threats.append(('Múltiplas conexões externas', ts))
    
    return threats

# ==================== CALCULAR HASH ====================
def calcular_hash_sha256(filepath):
    try:
        with open(filepath, 'rb') as f:
            hash_sha256 = hashlib.sha256()
            for chunk in iter(lambda: f.read(65536), b""):
                hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
    except:
        return None

def open_virustotal_link(hash_sha256):
    if hash_sha256:
        webbrowser.open(f"https://www.virustotal.com/gui/file/{hash_sha256}/detection")

# ==================== BOTÃO VIRUSTOTAL ====================
def create_vt_button(output_box, hash_sha256):
    """Cria botão VirusTotal clicável para um hash"""
    tag_name = f"vt_{hash_sha256[:8]}"
    output_box.insert(tk.END, "  🔍 ", "vt_icon")
    output_box.insert(tk.END, "VirusTotal", ("vt_button", tag_name))
    
    def on_click(e):
        open_virustotal_link(hash_sha256)
    
    output_box.tag_bind(tag_name, "<Button-1>", on_click)
    output_box.tag_bind(tag_name, "<Button-3>", on_click)
    output_box.tag_bind(tag_name, "<Enter>", lambda e: output_box.config(cursor="hand2"))
    output_box.tag_bind(tag_name, "<Leave>", lambda e: output_box.config(cursor=""))

def create_stop_button(output_box, proc_pid):
    """Cria botão para encerrar processo"""
    tag_name = f"kill_{proc_pid}"
    output_box.insert(tk.END, "  🛑 ", "alert")
    output_box.insert(tk.END, "Encerrar Processo", ("kill_button", tag_name))
    
    def on_kill(e):
        try:
            p = psutil.Process(proc_pid)
            p.terminate()
            safe_insert(output_box, f"\n[✓] Processo {proc_pid} encerrado.\n", "success")
        except Exception as ex:
            safe_insert(output_box, f"\n[!] Erro ao encerrar: {ex}\n", "alert")
    
    output_box.tag_bind(tag_name, "<Button-1>", on_kill)
    output_box.tag_bind(tag_name, "<Button-3>", on_kill)
    output_box.tag_bind(tag_name, "<Enter>", lambda e: output_box.config(cursor="hand2"))
    output_box.tag_bind(tag_name, "<Leave>", lambda e: output_box.config(cursor=""))

def adicionar_item_com_botao_vt(output_box, titulo, caminho, hash_sha256, score, evidencias=None, pid=None):
    """Adiciona um item suspeito ao output com botão VirusTotal e cor conforme gravidade"""
    if score >= 70: tag = "alert"
    elif score >= 40: tag = "alert_high"
    elif score >= 20: tag = "alert_medium"
    else: tag = "alert_low"
    
    safe_insert(output_box, f"\n{titulo}\n", tag)
    safe_insert(output_box, f"    Caminho: {caminho}\n", "hash")
    safe_insert(output_box, f"    Score: {score:.0f}/100\n", tag)
    
    if evidencias:
        for cat, evs in evidencias:
            safe_insert(output_box, f"    ├─ {cat}\n", "info")
            for ev in evs:
                safe_insert(output_box, f"    │  └─ {ev}\n", "normal")
    
    safe_insert(output_box, f"    SHA-256: {hash_sha256 or 'N/A'} ", "hash")
    if hash_sha256:
        create_vt_button(output_box, hash_sha256)
    
    if pid:
        safe_insert(output_box, f"\n    ", "hash")
        create_stop_button(output_box, pid)
    
    safe_insert(output_box, f"\n")

# ==================== ESCANEAMENTO PRINCIPAL ====================
def scan_all(output_box, progress_bar):
    """Varredura completa: processos, persistência, rede, arquivos"""
    
    total_steps = 5
    current_step = 0
    
    def atualizar_contagem():
        lbl_suspeitos.after(0, lambda: lbl_suspeitos.config(text=f"Suspeitos Encontrados: {len(suspeitos_detectados)}"))
    
    # === FASE 1: Processos ===
    current_step += 1
    safe_insert(output_box, f"\n{'='*60}\n", "title")
    safe_insert(output_box, f"[▶] FASE 1/{total_steps}: Analisando processos em execução...\n", "info")
    safe_update_progress(progress_bar, (current_step / total_steps) * 100)
    
    process_threats = check_process_behavior()
    
    if not process_threats:
        safe_insert(output_box, "  ✓ Nenhum processo suspeito detectado.\n", "success")
    else:
        safe_insert(output_box, f"  [!] {len(process_threats)} Processos Suspeitos Encontrados\n", "alert")
        for proc, ts in process_threats:
            classification, color = ts.classification
            idx = len(suspeitos_detectados) + 1
            hash_sha256 = calcular_hash_sha256(proc.info['exe'] or '')
            
            evidencias = [(cat.upper(), evs) for cat, evs in ts.evidences.items()]
            
            adicionar_item_com_botao_vt(
                output_box,
                f"[{idx}] {classification} | PID: {proc.info['pid']} | {proc.info['name']}",
                proc.info['exe'] or 'N/A',
                hash_sha256,
                ts.total,
                evidencias,
                pid=proc.info['pid']
            )
            
            suspeitos_detectados.append((proc.info['exe'] or proc.info['name'] or 'unknown', hash_sha256, ts.total))
            atualizar_contagem()
            
            if not scan_active.is_set():
                return
    
    # === FASE 2: Persistência ===
    current_step += 1
    safe_insert(output_box, f"\n{'='*60}\n", "title")
    safe_insert(output_box, f"[▶] FASE 2/{total_steps}: Verificando persistência no Windows...\n", "info")
    safe_update_progress(progress_bar, (current_step / total_steps) * 100)
    
    persistence_threats = check_windows_persistence()
    
    if not persistence_threats:
        safe_insert(output_box, "  ✓ Nenhuma entrada de persistência suspeita.\n", "success")
    else:
        safe_insert(output_box, f"  [!] {len(persistence_threats)} Entradas de persistência suspeitas\n", "alert")
        for item, ts in persistence_threats:
            classification, color = ts.classification
            idx = len(suspeitos_detectados) + 1
            
            hash_sha256 = None
            if isinstance(item, str) and os.path.isfile(item):
                hash_sha256 = calcular_hash_sha256(item)
            
            evidencias = [(cat.upper(), evs) for cat, evs in ts.evidences.items()]
            
            adicionar_item_com_botao_vt(
                output_box,
                f"[{idx}] {classification} - Persistência",
                str(item),
                hash_sha256,
                ts.total,
                evidencias
            )
            
            suspeitos_detectados.append((item, hash_sha256, ts.total))
            atualizar_contagem()
            
            if not scan_active.is_set():
                return
    
    # === FASE 3: Rede ===
    current_step += 1
    safe_insert(output_box, f"\n{'='*60}\n", "title")
    safe_insert(output_box, f"[▶] FASE 3/{total_steps}: Analisando conexões de rede...\n", "info")
    safe_update_progress(progress_bar, (current_step / total_steps) * 100)
    
    network_threats = check_network_anomalies()
    
    if not network_threats:
        safe_insert(output_box, "  ✓ Nenhuma anomalia de rede detectada.\n", "success")
    else:
        safe_insert(output_box, f"  [!] {len(network_threats)} Anomalias de rede\n", "alert")
        for item, ts in network_threats:
            classification, color = ts.classification
            idx = len(suspeitos_detectados) + 1
            
            evidencias = [(cat.upper(), evs) for cat, evs in ts.evidences.items()]
            
            adicionar_item_com_botao_vt(
                output_box,
                f"[{idx}] {classification} - Rede",
                str(item),
                None,
                ts.total,
                evidencias
            )
            
            suspeitos_detectados.append((item, None, ts.total))
            atualizar_contagem()
            
            if not scan_active.is_set():
                return
    
    # === FASE 4: Arquivos no diretório selecionado ===
    current_step += 1
    dir_path = entry_dir.get().strip()
    if dir_path and os.path.exists(dir_path):
        safe_insert(output_box, f"\n{'='*60}\n", "title")
        safe_insert(output_box, f"[▶] FASE 4/{total_steps}: Escaneando arquivos em {dir_path}...\n", "info")
        safe_update_progress(progress_bar, (current_step / total_steps) * 100)
        
        total_files = sum(len(files) for _, _, files in os.walk(dir_path)) or 1
        scanned = 0
        file_threats = []
        
        for root, _, files in os.walk(dir_path):
            for file in files:
                if not scan_active.is_set():
                    safe_insert(output_box, "\n[!] Varredura interrompida.\n", "alert")
                    return
                
                filepath = os.path.join(root, file)
                try:
                    ts = check_file_behavior(filepath)
                    if ts and ts.total >= 10:
                        file_threats.append((filepath, ts))
                except:
                    pass
                
                scanned += 1
                safe_update_progress(progress_bar, (current_step / total_steps) * 100 + (scanned / total_files) * (100 / total_steps))
                
                if scanned % 50 == 0:
                    lbl_status.after(0, lambda s=scanned, t=total_files: lbl_status.config(text=f"Escaneando: {s}/{t} arquivos"))
        
        if file_threats:
            safe_insert(output_box, f"  [!] {len(file_threats)} Arquivos Suspeitos Encontrados\n", "alert")
            for filepath, ts in file_threats:
                classification, color = ts.classification
                idx = len(suspeitos_detectados) + 1
                hash_sha256 = calcular_hash_sha256(filepath)
                
                evidencias = [(cat.upper(), evs) for cat, evs in ts.evidences.items()]
                
                adicionar_item_com_botao_vt(
                    output_box,
                    f"[{idx}] {classification}",
                    filepath,
                    hash_sha256,
                    ts.total,
                    evidencias
                )
                
                suspeitos_detectados.append((filepath, hash_sha256, ts.total))
                atualizar_contagem()
        else:
            safe_insert(output_box, "  ✓ Nenhum arquivo suspeito detectado no diretório.\n", "success")
    else:
        current_step += 1
        safe_insert(output_box, f"\n[~] FASE 4/{total_steps}: Nenhum diretório selecionado, pulando...\n", "info")
    
    # === FASE 5: RESUMO FINAL COM TODOS OS ITENS E BOTÕES VT ===
    current_step = total_steps
    safe_update_progress(progress_bar, 100)
    
    safe_insert(output_box, f"\n{'='*60}\n", "title")
    safe_insert(output_box, f"[✓] VARREDURA CONCLUÍDA - RESUMO FINAL\n", "success")
    safe_insert(output_box, f"{'='*60}\n", "title")
    
    if not suspeitos_detectados:
        safe_insert(output_box, "\n✅ Nenhuma ameaça detectada. Sistema limpo.\n", "success")
    else:
        sorted_threats = sorted(enumerate(suspeitos_detectados), key=lambda x: x[1][2], reverse=True)
        
        safe_insert(output_box, f"\n⚠️  TOTAL: {len(suspeitos_detectados)} AMEAÇAS ENCONTRADAS\n\n", "alert")
        
        criticas = sum(1 for _, _, s in suspeitos_detectados if s >= 70)
        altas = sum(1 for _, _, s in suspeitos_detectados if 40 <= s < 70)
        medias = sum(1 for _, _, s in suspeitos_detectados if 20 <= s < 40)
        baixas = sum(1 for _, _, s in suspeitos_detectados if 10 <= s < 20)
        
        safe_insert(output_box, f"  🔥 Críticas: {criticas}  |  ⚠️ Altas: {altas}  |  ⚡ Médias: {medias}  |  🔵 Baixas: {baixas}\n\n", "alert")
        
        safe_insert(output_box, f"{'─'*60}\n", "title")
        safe_insert(output_box, f"  LISTA COMPLETA DE ITENS SUSPEITOS (VirusTotal)\n", "info")
        safe_insert(output_box, f"{'─'*60}\n", "title")
        
        for posicao, (orig_idx, (target, h, score)) in enumerate(sorted_threats, 1):
            idx_original = orig_idx + 1
            
            if score >= 70: 
                nivel = "🔥 CRÍTICO"
                tag_nivel = "alert"
            elif score >= 40: 
                nivel = "⚠️ ALTO"
                tag_nivel = "alert_high"
            elif score >= 20: 
                nivel = "⚡ MÉDIO"
                tag_nivel = "alert_medium"
            elif score >= 10: 
                nivel = "🔵 BAIXO"
                tag_nivel = "alert_low"
            else: 
                nivel = "⚪ INFO"
                tag_nivel = "normal"
            
            nome_curto = os.path.basename(target) if target else 'N/A'
            
            safe_insert(output_box, f"\n  {posicao}. [{idx_original}] {nivel} (Score: {score:.0f})\n", tag_nivel)
            safe_insert(output_box, f"     Arquivo: {nome_curto}\n", "hash")
            safe_insert(output_box, f"     Caminho: {target}\n", "hash")
            safe_insert(output_box, f"     Hash: {h or 'N/A'} ", "hash")
            if h:
                create_vt_button(output_box, h)
            safe_insert(output_box, f"\n")       
        
        if criticas > 0:
            safe_insert(output_box, f"\n🔥 ATENÇÃO: Existem ameaças CRÍTICAS! Ações recomendadas:\n", "alert")
            safe_insert(output_box, f"  1. Encerrar processos suspeitos (botão 🛑 ao lado do item)\n", "normal")
            safe_insert(output_box, f"  2. Verificar entradas de persistência no Registro e Tasks\n", "normal")
            safe_insert(output_box, f"  3. Executar scan completo com Windows Defender\n", "normal")
            safe_insert(output_box, f"  4. Desconectar da rede se suspeitar de C2\n", "normal")
    
    if suspeitos_detectados:
        winsound.MessageBeep(0x10)  # MB_ICONHAND = 0x10 (corrigido)
        criticas = sum(1 for _, _, s in suspeitos_detectados if s >= 70)
        altas = sum(1 for _, _, s in suspeitos_detectados if 40 <= s < 70)
        medias = sum(1 for _, _, s in suspeitos_detectados if 20 <= s < 40)
        
        safe_messagebox("ALERTA - SHADOW SCANNER", 
            f"{len(suspeitos_detectados)} Ameaças Encontradas\n\n"
            f"🔥 Críticas: {criticas}\n"
            f"⚠️ Altas: {altas}\n"
            f"⚡ Médias: {medias}\n\n"
            f"Verifique o resumo final para detalhes e links VirusTotal.",
            'warning')

# ==================== INTERFACE ====================
def selecionar_pasta():
    pasta = filedialog.askdirectory()
    if pasta:
        entry_dir.delete(0, tk.END)
        entry_dir.insert(0, pasta)

def iniciar_varredura_thread():
    if not scan_active.is_set():
        scan_active.set()
        threading.Thread(target=iniciar_varredura, daemon=True).start()

def parar_varredura():
    scan_active.clear()
    lbl_status.config(text="⚠️ Varredura interrompida pelo usuário")

def iniciar_varredura():
    try:
        output_box.after(0, lambda: output_box.delete(1.0, tk.END))
        output_box.after(0, lambda: progress_bar.configure(value=0))
        suspeitos_detectados.clear()
        lbl_suspeitos.after(0, lambda: lbl_suspeitos.config(text="Suspeitos Encontrados: 0"))
        lbl_status.after(0, lambda: lbl_status.config(text="▶ Executando varredura completa..."))
        btn_start.after(0, lambda: btn_start.config(state=tk.DISABLED))
        btn_stop.after(0, lambda: btn_stop.config(state=tk.NORMAL))
        
        scan_all(output_box, progress_bar)
        
        btn_start.after(0, lambda: btn_start.config(state=tk.NORMAL))
        btn_stop.after(0, lambda: btn_stop.config(state=tk.DISABLED))
        
        lbl_suspeitos.after(0, lambda: lbl_suspeitos.config(text=f"Suspeitos Encontrados: {len(suspeitos_detectados)}"))
        
        if not any(s >= 70 for _, _, s in suspeitos_detectados):
            lbl_status.after(0, lambda: lbl_status.config(text="✅ Varredura concluída"))
        else:
            lbl_status.after(0, lambda: lbl_status.config(text="⚠️ Ameaças detectadas!"))
    except Exception as e:
        print(f"Erro na varredura: {e}")
    finally:
        scan_active.clear()

def open_selected_virustotal():
    input_text = entry_virustotal.get().strip()
    if not input_text:
        messagebox.showwarning("Erro", "Digite números ou intervalos (ex: 1,3-5)")
        return
    try:
        indices = set()
        for part in re.split(r'[,\s]+', input_text):
            if not part: continue
            if '-' in part:
                s, e = map(int, part.split('-'))
                indices.update(range(s, e+1))
            else:
                indices.add(int(part))
        opened = []
        for i in sorted(indices):
            if 1 <= i <= len(suspeitos_detectados):
                h = suspeitos_detectados[i-1][1]
                if h:
                    open_virustotal_link(h)
                    opened.append(i)
        if not opened:
            messagebox.showinfo("Info", "Nenhum hash disponível para os índices selecionados.")
    except Exception as e:
        messagebox.showwarning("Erro", f"Entrada inválida: {e}")

def salvar_resultado():
    conteudo = output_box.get("1.0", tk.END).strip()
    if "[!]" in conteudo or "CRÍTICO" in conteudo or "ALTO" in conteudo:
        caminho = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                 filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if caminho:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(f"SCANNER - Relatório de Varredura\n\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"{'='*60}\n\n")
                f.write(conteudo)
            messagebox.showinfo("Salvo", f"Relatório salvo\n\n{caminho}")

def limpar_resultados():
    if suspeitos_detectados:
        if messagebox.askyesno("Confirmar", "Limpar todos os resultados?"):
            output_box.delete(1.0, tk.END)
            suspeitos_detectados.clear()
            lbl_suspeitos.config(text="Suspeitos Encontrados: 0")
            progress_bar["value"] = 0
            lbl_status.config(text="Resultados limpos")
    else:
        output_box.delete(1.0, tk.END)
        lbl_status.config(text="Console limpo")

# ==================== JANELA PRINCIPAL ====================
janela = tk.Tk()
janela.title("SCANNER DETECÇAO COMPORTAMENTAL")
janela.configure(bg="#0a0a0a")

try:
    janela.state("zoomed")
except:
    janela.geometry("1400x900")

# === Título ===
title_frame = tk.Frame(janela, bg="#0a0a0a")
title_frame.pack(pady=10)

tk.Label(title_frame, text="SCANNER DETECÇAO COMPORTAMENTAL", font=("Courier", 28, "bold"), 
         fg="#00ff00", bg="#0a0a0a").pack()
tk.Label(title_frame, text="Detecção Comportamental de Ameaças", 
         font=("Courier", 10), fg="#00aa00", bg="#0a0a0a").pack()

# === Frame de diretório ===
dir_frame = tk.Frame(janela, bg="#0a0a0a")
dir_frame.pack(pady=8)

tk.Label(dir_frame, text="Diretório:", bg="#0a0a0a", fg="#00ff00", 
         font=("Courier", 10)).pack(side=tk.LEFT, padx=5)

entry_dir = tk.Entry(dir_frame, width=80, bg="#000000", fg="#00ff00", 
                      font=("Courier", 10), insertbackground="#00ff00")
entry_dir.pack(side=tk.LEFT, padx=5)
entry_dir.insert(0, os.environ.get('TEMP', 'C:\\'))

tk.Button(dir_frame, text="📁 SELECIONAR", command=selecionar_pasta, 
          bg="#002200", fg="#00ff00", font=("Courier", 9, "bold")).pack(side=tk.LEFT, padx=5)

# === Botões de controle ===
control_frame = tk.Frame(janela, bg="#0a0a0a")
control_frame.pack(pady=10)

btn_start = tk.Button(control_frame, text="▶ INICIAR VARREDURA COMPLETA", 
                      command=iniciar_varredura_thread, bg="#00ff00", fg="black", 
                      font=("Courier", 12, "bold"), height=2, width=30)
btn_start.pack(side=tk.LEFT, padx=10)

btn_stop = tk.Button(control_frame, text="⛔ PARAR", command=parar_varredura, 
                     bg="#880000", fg="white", font=("Courier", 10, "bold"), 
                     state=tk.DISABLED)
btn_stop.pack(side=tk.LEFT, padx=5)

tk.Button(control_frame, text="🗑️ LIMPAR", command=limpar_resultados, 
          bg="#333333", fg="#ffcc00", font=("Courier", 10, "bold")).pack(side=tk.LEFT, padx=5)

# === VirusTotal ===
vt_frame = tk.Frame(janela, bg="#0a0a0a")
vt_frame.pack(pady=5)

tk.Label(vt_frame, text="Abrir VirusTotal → Índices:", bg="#0a0a0a", 
         fg="#00ff00", font=("Courier", 10)).pack(side=tk.LEFT, padx=5)

entry_virustotal = tk.Entry(vt_frame, width=40, bg="#111111", fg="#00ff00", 
                             font=("Courier", 10), insertbackground="#00ff00")
entry_virustotal.pack(side=tk.LEFT, padx=5)
entry_virustotal.insert(0, "ex: 1,3-5")

tk.Button(vt_frame, text="🔍 ABRIR", command=open_selected_virustotal, 
          bg="#ff8800", fg="black", font=("Courier", 10, "bold")).pack(side=tk.LEFT, padx=5)

# === Barra de progresso ===
progress_bar = ttk.Progressbar(janela, length=1000, mode="determinate")
progress_bar.pack(pady=8)

# === Labels de status ===
status_frame = tk.Frame(janela, bg="#0a0a0a")
status_frame.pack(pady=3)

lbl_suspeitos = tk.Label(status_frame, text="Suspeitos Encontrados: 0", 
                          font=("Courier", 12, "bold"), fg="#ffff00", bg="#0a0a0a")
lbl_suspeitos.pack(side=tk.LEFT, padx=20)

lbl_status = tk.Label(status_frame, text="Pronto para varredura", 
                      font=("Courier", 10), fg="#00aa00", bg="#0a0a0a")
lbl_status.pack(side=tk.LEFT, padx=20)

# === Output box ===
output_box = scrolledtext.ScrolledText(janela, bg="#000000", fg="#00ff41", 
                                        font=("Courier", 10), height=25, wrap=tk.WORD)
output_box.pack(padx=15, pady=8, fill=tk.BOTH, expand=True)

# Configurar tags
output_box.tag_config("alert", foreground="#ff3333", font=("Courier", 10, "bold"))
output_box.tag_config("alert_high", foreground="#ff6600", font=("Courier", 10, "bold"))
output_box.tag_config("alert_medium", foreground="#ffaa00", font=("Courier", 10, "bold"))
output_box.tag_config("alert_low", foreground="#4488ff", font=("Courier", 10))
output_box.tag_config("info", foreground="#00aaff", font=("Courier", 10))
output_box.tag_config("success", foreground="#00ff00", font=("Courier", 10))
output_box.tag_config("hash", foreground="#00ccff", font=("Courier", 10))
output_box.tag_config("normal", foreground="#cccccc", font=("Courier", 10))
output_box.tag_config("title", foreground="#00ff00", font=("Courier", 10, "bold"))
output_box.tag_config("vt_icon", foreground="#00ddff")
output_box.tag_config("vt_button", foreground="#00ddff", background="#002244", 
                       font=("Courier", 9, "bold"))
output_box.tag_config("kill_button", foreground="#ff4444", background="#440000", 
                       font=("Courier", 9, "bold"))

# === Botão salvar ===
bottom_frame = tk.Frame(janela, bg="#0a0a0a")
bottom_frame.pack(pady=8)

tk.Button(bottom_frame, text="💾 SALVAR RELATÓRIO", command=salvar_resultado, 
          bg="#003366", fg="#00ff00", font=("Courier", 11, "bold")).pack(side=tk.LEFT, padx=10)

janela.mainloop()
