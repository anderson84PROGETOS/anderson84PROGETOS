import psutil
import winsound
import time
import datetime
import os
import sys
from colorama import init, Fore, Style

# Inicializa colorama
init(autoreset=True)

# Cabeçalho artístico
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """ 
███╗   ███╗ ██████╗ ███╗   ██╗██╗████████╗ ██████╗ ██████╗  █████╗ ██████╗     ██████╗  ██████╗
████╗ ████║██╔═══██╗████╗  ██║██║╚══██╔══╝██╔═══██╗██╔══██╗██╔══██╗██╔══██╗    ██╔══██╗██╔════╝
██╔████╔██║██║   ██║██╔██╗ ██║██║   ██║   ██║   ██║██████╔╝███████║██████╔╝    ██████╔╝██║     
██║╚██╔╝██║██║   ██║██║╚██╗██║██║   ██║   ██║   ██║██╔══██╗██╔══██║██╔══██╗    ██╔═══╝ ██║     
██║ ╚═╝ ██║╚██████╔╝██║ ╚████║██║   ██║   ╚██████╔╝██║  ██║██║  ██║██║  ██║    ██║     ╚██████╗
╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝    ╚═╝      ╚═════╝
""")

# === Função para obter o diretório do script ou do executável (.exe) ===
def get_script_dir():
    if getattr(sys, 'frozen', False):  # Executável com PyInstaller
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# === Caminho absoluto do log.txt ===
log_path = os.path.join(get_script_dir(), "log.txt")


# === Configurações ===
processos_suspeitos = [
    # Ferramentas de rede/reversas
    "nc.exe", "ncat.exe", "netcat.exe", "msfvenom.exe", "meterpreter", "socat.exe",
    "plink.exe",  # PuTTY link - pode ser usado para túnel reverso
    "ssh.exe",

    # PowerShell e scripting
    "powershell.exe", "pwsh.exe", "wscript.exe", "cscript.exe",

    # RATs e keyloggers
    "keylogger.exe", "rat.exe", "remcos.exe", "spynote.exe", "nanocore.exe", "darkcomet.exe",

    # Ferramentas ofensivas
    "mimikatz.exe", "procdump.exe", "tasklist.exe", "tcpview.exe", "autoruns.exe",
    "processhacker.exe", "nmap.exe", "masscan.exe", "hydra.exe", "john.exe",

    # Execução remota/shells
    "cmd.exe", "bash.exe", "sh.exe", "python.exe", "perl.exe", "ruby.exe", "java.exe",

    # Suspicious downloaders
    "curl.exe", "wget.exe", "bitsadmin.exe", "certutil.exe",

    # Outras ferramentas suspeitas
    "ngrok.exe", "teamviewer.exe", "anydesk.exe", "vncserver.exe", "tightvnc.exe", "ultravnc.exe",
    "logmein.exe", "radmin.exe", "ammyy.exe", "dameware.exe",
]

portas_suspeitas = [
    21,    # FTP - frequentemente alvo de ataques
    22,    # SSH - muito usado para shells reversas
    23,    # Telnet - inseguro e visado por atacantes
    53,    # DNS - usado em tunneling (ex: iodine)
    80,    # HTTP - tráfego malicioso disfarçado
    135,   # RPC - usado em exploits Windows
    137, 138, 139, 445,  # NetBIOS/SMB - vulnerabilidades conhecidas
    1433,  # SQL Server - alvo comum
    3306,  # MySQL - também alvo de brute-force
    3389,  # RDP - muito visado por atacantes
    4444,  # Metasploit default reverse shell
    4711,  # Web shells
    5000, 5050,  # Ferramentas de desenvolvimento podem ser abusadas
    5432,  # PostgreSQL
    5800, 5900,  # VNC
    5985, 5986,  # WinRM
    666, 6666, 6667,  # Common em shells de IRC bots e RATs
    7000, 7001, 7002,  # Usadas por bots e backdoors
    8080, 8081, 8888,  # HTTP alternativo, tunneling, proxies
    9001, 9002, 9003,  # TOR relays, reverse shells
    12345,  # NetBus (backdoor clássico)
    27374,  # Sub7 RAT
    31337,  # Back Orifice / Elite (leet) port
    32764,  # Vulnerabilidade em roteadores
    44444,  # Usada por vários trojans
]

# === Controle de alertas ===
processos_alertados = set()
conexoes_alertadas = set()
power_shell_pids = set()
python_suspeito_count = 0

# === Funções ===
def emitir_alarme():
    print("[!!!] ALERTA SONORO!\n")
    winsound.Beep(1500, 1000)

def log(mensagem):
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{agora}] {mensagem}"
    print(linha)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(linha + "\n")

def verificar_processos_suspeitos():
    global python_suspeito_count
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            nome = proc.info['name'].lower()
            pid = proc.info['pid']
            cmdline_list = proc.info.get('cmdline') or []
            cmdline = ' '.join(cmdline_list).lower()

            try:
                caminho_exe = proc.exe()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                caminho_exe = "Caminho do executável indisponível"

            if nome in ["powershell.exe", "pwsh.exe"]:
                if pid not in power_shell_pids:
                    if len(power_shell_pids) > 0 and pid not in processos_alertados:
                        msg = f"[ALERTA] PowerShell suspeito Encontrado: PID {pid} - Caminho: {caminho_exe}\n"
                        log(msg)
                        emitir_alarme()
                        processos_alertados.add(pid)
                    power_shell_pids.add(pid)
                continue

            if nome == "python.exe":
                if ("keyboard" in cmdline or "python.exe" in cmdline) and pid not in processos_alertados:
                    python_suspeito_count += 1
                    if python_suspeito_count >= 2:
                        msg = f"[ALERTA] Script Python suspeito com 'python.exe' Detectado: PID {pid} - Caminho: {caminho_exe}\n"
                        log(msg)
                        emitir_alarme()
                    processos_alertados.add(pid)
                continue

            if nome in processos_suspeitos and pid not in processos_alertados:
                msg = f"[ALERTA] Processo suspeito Encontrado: {nome} (PID: {pid}) - Caminho: {caminho_exe}\n"
                log(msg)
                emitir_alarme()
                processos_alertados.add(pid)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

def verificar_conexoes():
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == 'ESTABLISHED' and conn.raddr:
            try:
                porta = conn.raddr.port
                chave = (conn.pid, porta)
                if porta in portas_suspeitas and chave not in conexoes_alertadas:
                    log(f"[ALERTA] Conexão suspeita Detectada: {conn.raddr} (PID: {conn.pid})")
                    emitir_alarme()
                    conexoes_alertadas.add(chave)
            except Exception:
                continue

# === Loop principal ===
try:
    while True:
        verificar_processos_suspeitos()
        verificar_conexoes()
        time.sleep(5)
except KeyboardInterrupt:
    print("\nMonitoramento Encerrado pelo usuário.\n")
    log("[INFO] Monitoramento Encerrado manualmente.\n")

# Caminho do log exibido ao final
print(f"\nArquivo de log salvo em: {Fore.YELLOW + Style.BRIGHT}{log_path}")

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
