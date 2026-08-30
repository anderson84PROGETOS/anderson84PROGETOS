import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import platform
import socket
import uuid
import os
import subprocess
import sys
from datetime import datetime


# ============================================================
# CONFIGURAÇÃO GLOBAL PARA OCULTAR JANELAS DE CONSOLE (CMD)
# ============================================================
CREATE_NO_WINDOW = 0x08000000  # Flag do Windows para não criar janela

def _get_subprocess_kwargs():
    """Retorna kwargs para subprocess que ocultam a janela do CMD no Windows."""
    kwargs = {}
    if platform.system() == "Windows":
        # Configura startupinfo para ocultar janela
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs['startupinfo'] = startupinfo
        kwargs['creationflags'] = CREATE_NO_WINDOW
    return kwargs


def run_hidden(cmd, **kwargs):
    """Executa subprocess sem mostrar janela do CMD."""
    hidden_kwargs = _get_subprocess_kwargs()
    hidden_kwargs.update(kwargs)
    return subprocess.run(cmd, **hidden_kwargs)


# Instalar dependências automaticamente (SEM abrir CMD)
def install_package(package):
    hidden_kwargs = _get_subprocess_kwargs()
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", package],
        **hidden_kwargs
    )

try:
    import psutil
except ImportError:
    install_package("psutil")
    import psutil

try:
    import GPUtil
except ImportError:
    install_package("GPUtil")
    import GPUtil

try:
    from screeninfo import get_monitors
except ImportError:
    install_package("screeninfo")
    from screeninfo import get_monitors

try:
    import winreg
except ImportError:
    winreg = None


class HardwareDetector:
    """Classe responsável por detectar todo o hardware do sistema."""

    def __init__(self):
        self.info = {}

    def detectar_tudo(self, progress_callback=None):
        etapas = [
            ("Sistema Operacional", self.detectar_sistema),
            ("Processador (CPU)", self.detectar_cpu),
            ("Memória RAM", self.detectar_memoria),
            ("Discos / Armazenamento", self.detectar_discos),
            ("Placa de Vídeo (GPU)", self.detectar_gpu),
            ("Rede", self.detectar_rede),
            ("Placa-Mãe / BIOS", self.detectar_placa_mae),
            ("Monitor / Tela", self.detectar_monitor),
            ("Bateria", self.detectar_bateria),
            ("Dispositivos USB", self.detectar_usb),
            ("Áudio", self.detectar_audio),
            ("Processos Ativos", self.detectar_processos),
            ("Variáveis de Ambiente", self.detectar_variaveis_ambiente),
            ("Programas Instalados", self.detectar_programas),
            ("Serviços do Windows", self.detectar_servicos),
            ("Drivers", self.detectar_drivers),
        ]

        total = len(etapas)
        for i, (nome, func) in enumerate(etapas):
            try:
                func()
            except Exception as e:
                self.info[nome] = {"Erro": str(e)}
            if progress_callback:
                progress_callback(i + 1, total, nome)

        return self.info

    def detectar_sistema(self):
        uname = platform.uname()
        self.info["Sistema Operacional"] = {
            "Sistema": uname.system,
            "Nome do Computador": uname.node,
            "Release": uname.release,
            "Versão": uname.version,
            "Arquitetura": uname.machine,
            "Processador (platform)": uname.processor,
            "Plataforma": platform.platform(),
            "Edição do Windows": platform.win32_edition() if hasattr(platform, 'win32_edition') else "N/A",
            "Versão do Windows": '.'.join(str(x) for x in platform.win32_ver()) if hasattr(platform, 'win32_ver') else "N/A",
            "Usuário Atual": os.getlogin(),
            "Diretório Home": os.path.expanduser("~"),
            "Boot Time": datetime.fromtimestamp(psutil.boot_time()).strftime("%d/%m/%Y %H:%M:%S"),
            "Tempo Ligado": self._uptime(),
        }

    def _uptime(self):
        seconds = (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours}h {minutes}m {secs}s"

    def detectar_cpu(self):
        freq = psutil.cpu_freq()
        cpu_info = {
            "Processador": platform.processor(),
            "Núcleos Físicos": psutil.cpu_count(logical=False),
            "Núcleos Lógicos (Threads)": psutil.cpu_count(logical=True),
            "Uso Atual da CPU (%)": f"{psutil.cpu_percent(interval=1)}%",
            "Frequência Atual (MHz)": f"{freq.current:.0f} MHz" if freq else "N/A",
            "Frequência Mínima (MHz)": f"{freq.min:.0f} MHz" if freq and freq.min else "N/A",
            "Frequência Máxima (MHz)": f"{freq.max:.0f} MHz" if freq and freq.max else "N/A",
        }

        per_cpu = psutil.cpu_percent(interval=0.5, percpu=True)
        for i, percent in enumerate(per_cpu):
            cpu_info[f"Núcleo {i} Uso (%)"] = f"{percent}%"

        try:
            if winreg:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                     r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                cpu_info["Nome Completo da CPU"] = cpu_name.strip()
                winreg.CloseKey(key)
        except:
            pass

        self.info["Processador (CPU)"] = cpu_info

    def _obter_detalhes_ram_windows(self):
        """Consulta o hardware via PowerShell/JSON e extrai APENAS as informações que realmente existem com quebra de linha."""
        try:
            cmd = 'powershell -NoProfile -Command "Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity, DeviceLocator, Manufacturer, PartNumber, Speed | ConvertTo-Json"'
            result = run_hidden(
                cmd, capture_output=True, text=True, timeout=10, shell=True
            )

            if result.returncode != 0 or not result.stdout.strip():
                return "Não foi possível ler os pentes", "Desconhecido"

            import json

            dados = json.loads(result.stdout)

            if isinstance(dados, dict):
                dados = [dados]

            pentes_detalhados = []
            modelos_resumidos = []

            for i, p in enumerate(dados):
                info_pente = []

                # 1. Capacidade em GB
                cap = p.get("Capacity")
                if cap and str(cap).isdigit() and int(cap) > 0:
                    gb = int(cap) / (1024**3)
                    info_pente.append(
                        f"{gb:.0f} GB" if gb.is_integer() else f"{gb:.1f} GB"
                    )

                # 2. Fabricante
                fab = str(p.get("Manufacturer") or "").strip()
                if fab and fab.lower() not in [
                    "unknown",
                    "none",
                    "n/a",
                    "undefined",
                ]:
                    if not (len(fab) > 12 and fab.isalnum()):
                        info_pente.append(fab)
                else:
                    fab = ""

                # 3. Part Number / Modelo
                part = str(p.get("PartNumber") or "").strip()
                if part and part.lower() not in [
                    "unknown",
                    "none",
                    "n/a",
                    "undefined",
                ]:
                    info_pente.append(f"({part})")
                else:
                    part = ""

                # 4. Velocidade / Frequência
                speed = p.get("Speed")
                if speed and str(speed).isdigit() and int(speed) > 0:
                    info_pente.append(f"@{speed}MHz")

                # 5. Slot físico
                slot = str(p.get("DeviceLocator") or "").strip()
                if slot:
                    info_pente.append(f"[{slot}]")

                # Junta SOMENTE o que achou
                if info_pente:
                    pentes_detalhados.append(
                        f"• Pente {i+1}: " + " ".join(info_pente)
                    )

                    nome_pente = f"{fab} {part}".strip()
                    if not nome_pente:
                        nome_pente = (
                            f"{info_pente[0]}"
                            if info_pente
                            else f"Pente {i+1}"
                        )
                    modelos_resumidos.append(f"• {nome_pente}")

            if not pentes_detalhados:
                return "Nenhum pente físico detectado", "Desconhecido"

            detalhado = "\n".join(pentes_detalhados)

            total = len(modelos_resumidos)
            if total == 1:
                simplificado = modelos_resumidos[0].replace("• ", "")
            elif total > 1:
                if len(set(modelos_resumidos)) == 1:
                    simplificado = f"{total}x " + modelos_resumidos[0].replace("• ", "")
                else:
                    simplificado = "\n".join(modelos_resumidos)
            else:
                simplificado = "Memória Instalada"

            return detalhado, simplificado

        except Exception as e:
            return f"Erro ao detectar: {str(e)}", "Desconhecido"

    def detectar_memoria(self):
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        detalhe_pentes, modelo_simplificado = "N/A", "N/A"
        if platform.system() == "Windows":
            detalhe_pentes, modelo_simplificado = self._obter_detalhes_ram_windows()

        self.info["Memória RAM"] = {
            "RAM Total": self._formatar_bytes(mem.total),
            "RAM Disponível": self._formatar_bytes(mem.available),
            "RAM Usada": self._formatar_bytes(mem.used),
            "Percentual de Uso": f"{mem.percent}%",
            "Modelo (Simplificado)": modelo_simplificado,
            "Especificação Física (Pentes)": detalhe_pentes,
            "SWAP Total": self._formatar_bytes(swap.total),
            "SWAP Usada": self._formatar_bytes(swap.used),
            "SWAP Livre": self._formatar_bytes(swap.free),
            "SWAP Percentual": f"{swap.percent}%",
        }

    def detectar_discos(self):
        discos = {}
        partitions = psutil.disk_partitions()
        for i, p in enumerate(partitions):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                discos[f"Disco {i + 1} ({p.device})"] = {
                    "Ponto de Montagem": p.mountpoint,
                    "Sistema de Arquivos": p.fstype,
                    "Opções": p.opts,
                    "Tamanho Total": self._formatar_bytes(usage.total),
                    "Usado": self._formatar_bytes(usage.used),
                    "Livre": self._formatar_bytes(usage.free),
                    "Uso (%)": f"{usage.percent}%",
                }
            except PermissionError:
                discos[f"Disco {i + 1} ({p.device})"] = {
                    "Ponto de Montagem": p.mountpoint,
                    "Erro": "Sem permissão de acesso",
                }

        try:
            disk_io = psutil.disk_io_counters()
            discos["I/O Global dos Discos"] = {
                "Bytes Lidos": self._formatar_bytes(disk_io.read_bytes),
                "Bytes Escritos": self._formatar_bytes(disk_io.write_bytes),
                "Leituras": f"{disk_io.read_count:,}",
                "Escritas": f"{disk_io.write_count:,}",
            }
        except:
            pass

        self.info["Discos / Armazenamento"] = discos

    def detectar_gpu(self):
        gpus_info = {}
        try:
            gpus = GPUtil.getGPUs()
            for i, gpu in enumerate(gpus):
                gpus_info[f"GPU {i + 1}: {gpu.name}"] = {
                    "ID": gpu.id,
                    "Nome": gpu.name,
                    "Driver": gpu.driver,
                    "Memória Total (MB)": f"{gpu.memoryTotal:.0f} MB",
                    "Memória Usada (MB)": f"{gpu.memoryUsed:.0f} MB",
                    "Memória Livre (MB)": f"{gpu.memoryFree:.0f} MB",
                    "Uso da GPU (%)": f"{gpu.load * 100:.1f}%",
                    "Temperatura (°C)": f"{gpu.temperature}°C" if gpu.temperature else "N/A",
                    "UUID": gpu.uuid,
                }
        except:
            pass

        if not gpus_info:
            try:
                result = run_hidden(
                    ["wmic", "path", "win32_videocontroller", "get",
                     "Name,AdapterRAM,DriverVersion,VideoProcessor,CurrentRefreshRate,VideoModeDescription",
                     "/format:list"],
                    capture_output=True, text=True, timeout=10
                )
                entries = result.stdout.strip().split("\n\n")
                gpu_count = 0
                for entry in entries:
                    lines = [l.strip() for l in entry.strip().split("\n") if "=" in l]
                    if lines:
                        gpu_count += 1
                        gpu_data = {}
                        for line in lines:
                            key, _, value = line.partition("=")
                            if value.strip():
                                if key.strip() == "AdapterRAM":
                                    try:
                                        gpu_data["Memória do Adaptador"] = self._formatar_bytes(int(value.strip()))
                                    except:
                                        gpu_data[key.strip()] = value.strip()
                                else:
                                    gpu_data[key.strip()] = value.strip()
                        if gpu_data:
                            nome = gpu_data.get("Name", f"GPU {gpu_count}")
                            gpus_info[f"GPU {gpu_count}: {nome}"] = gpu_data
            except:
                gpus_info["Info"] = {"Status": "Nenhuma GPU detectada ou erro na detecção"}

        self.info["Placa de Vídeo (GPU)"] = gpus_info

    def detectar_rede(self):
        rede_info = {}
        hostname = socket.gethostname()
        try:
            get_ip = socket.gethostbyname(hostname)
        except:
            get_ip = "N/A"

        rede_info["Informações Gerais"] = {
            "Hostname": hostname,
            "IP Local": get_ip,
            "MAC Address": ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                                     for ele in range(0, 8 * 6, 8)][::-1]),
            "FQDN": socket.getfqdn(),
        }

        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        for iface, addr_list in addrs.items():
            iface_info = {}
            for addr in addr_list:
                if addr.family == socket.AF_INET:
                    iface_info["IPv4"] = addr.address
                    iface_info["Máscara IPv4"] = addr.netmask
                elif addr.family == socket.AF_INET6:
                    iface_info["IPv6"] = addr.address
                elif addr.family == psutil.AF_LINK:
                    iface_info["MAC"] = addr.address

            if iface in stats:
                s = stats[iface]
                iface_info["Ativa"] = "Sim" if s.isup else "Não"
                iface_info["Velocidade (Mbps)"] = str(s.speed) if s.speed else "N/A"
                iface_info["MTU"] = str(s.mtu)

            rede_info[f"Interface: {iface}"] = iface_info

        try:
            net_io = psutil.net_io_counters()
            rede_info["I/O de Rede Global"] = {
                "Bytes Enviados": self._formatar_bytes(net_io.bytes_sent),
                "Bytes Recebidos": self._formatar_bytes(net_io.bytes_recv),
                "Pacotes Enviados": f"{net_io.packets_sent:,}",
                "Pacotes Recebidos": f"{net_io.packets_recv:,}",
                "Erros de Entrada": str(net_io.errin),
                "Erros de Saída": str(net_io.errout),
            }
        except:
            pass

        self.info["Rede"] = rede_info

    def detectar_placa_mae(self):
        mb_info = {}
        comandos = {
            "Placa-Mãe": "wmic baseboard get Manufacturer,Product,SerialNumber,Version /format:list",
            "BIOS": "wmic bios get Manufacturer,Name,Version,ReleaseDate,SMBIOSBIOSVersion /format:list",
            "Sistema": "wmic computersystem get Manufacturer,Model,SystemType,TotalPhysicalMemory /format:list",
        }

        for secao, cmd in comandos.items():
            try:
                result = run_hidden(cmd.split(), capture_output=True, text=True, timeout=10)
                dados = {}
                for line in result.stdout.strip().split("\n"):
                    line = line.strip()
                    if "=" in line:
                        key, _, value = line.partition("=")
                        if value.strip():
                            dados[key.strip()] = value.strip()
                if dados:
                    mb_info[secao] = dados
            except:
                mb_info[secao] = {"Erro": "Não foi possível detectar"}

        self.info["Placa-Mãe / BIOS"] = mb_info

    def detectar_monitor(self):
        monitor_info = {}
        try:
            monitors = get_monitors()
            for i, m in enumerate(monitors):
                monitor_info[f"Monitor {i + 1}"] = {
                    "Nome": m.name if m.name else "N/A",
                    "Resolução": f"{m.width} x {m.height}",
                    "Posição (x, y)": f"({m.x}, {m.y})",
                    "Largura (mm)": f"{m.width_mm} mm" if m.width_mm else "N/A",
                    "Altura (mm)": f"{m.height_mm} mm" if m.height_mm else "N/A",
                    "Principal": "Sim" if m.is_primary else "Não",
                }
        except:
            monitor_info["Info"] = {"Status": "Não foi possível detectar monitores"}

        self.info["Monitor / Tela"] = monitor_info

    def detectar_bateria(self):
        bat_info = {}
        battery = psutil.sensors_battery()
        if battery:
            bat_info = {
                "Percentual": f"{battery.percent}%",
                "Conectado na Tomada": "Sim" if battery.power_plugged else "Não",
                "Tempo Restante": self._formatar_tempo_bateria(battery.secsleft),
            }
        else:
            bat_info = {"Status": "Sem bateria detectada (provavelmente desktop)"}

        self.info["Bateria"] = bat_info

    def _formatar_tempo_bateria(self, seconds):
        if seconds == psutil.POWER_TIME_UNLIMITED:
            return "Carregando / Ilimitado"
        elif seconds == psutil.POWER_TIME_UNKNOWN:
            return "Desconhecido"
        else:
            hours, remainder = divmod(int(seconds), 3600)
            minutes, secs = divmod(remainder, 60)
            return f"{hours}h {minutes}m {secs}s"

    def detectar_usb(self):
        usb_info = {}
        try:
            result = run_hidden(
                ["wmic", "path", "Win32_USBControllerDevice", "get", "Dependent", "/format:list"],
                capture_output=True, text=True, timeout=15
            )
            devices = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if "Dependent=" in line:
                    dev = line.split("=", 1)[1].strip('"')
                    devices.append(dev)

            if devices:
                for i, dev in enumerate(devices[:30]):
                    usb_info[f"Dispositivo {i + 1}"] = dev
            else:
                usb_info["Status"] = "Nenhum dispositivo USB detectado"
        except:
            usb_info["Status"] = "Erro ao detectar dispositivos USB"

        try:
            result = run_hidden(
                ["wmic", "path", "Win32_PnPEntity", "where",
                 "PNPClass='USB'", "get", "Name,Manufacturer,DeviceID", "/format:list"],
                capture_output=True, text=True, timeout=15
            )
            entries = result.stdout.strip().split("\n\n")
            usb_devices = {}
            count = 0
            for entry in entries:
                lines = [l.strip() for l in entry.strip().split("\n") if "=" in l]
                if lines:
                    count += 1
                    dev_data = {}
                    for line in lines:
                        key, _, value = line.partition("=")
                        if value.strip():
                            dev_data[key.strip()] = value.strip()
                    if dev_data:
                        nome = dev_data.get("Name", f"USB {count}")
                        usb_devices[f"USB PnP {count}: {nome}"] = dev_data
            if usb_devices:
                usb_info["Dispositivos PnP USB"] = usb_devices
        except:
            pass

        self.info["Dispositivos USB"] = usb_info

    def detectar_audio(self):
        audio_info = {}
        try:
            result = run_hidden(
                ["wmic", "sounddev", "get", "Name,Manufacturer,Status,StatusInfo", "/format:list"],
                capture_output=True, text=True, timeout=10
            )
            entries = result.stdout.strip().split("\n\n")
            count = 0
            for entry in entries:
                lines = [l.strip() for l in entry.strip().split("\n") if "=" in l]
                if lines:
                    count += 1
                    dev_data = {}
                    for line in lines:
                        key, _, value = line.partition("=")
                        if value.strip():
                            dev_data[key.strip()] = value.strip()
                    if dev_data:
                        nome = dev_data.get("Name", f"Áudio {count}")
                        audio_info[f"Dispositivo {count}: {nome}"] = dev_data
        except:
            audio_info["Status"] = "Erro ao detectar dispositivos de áudio"

        if not audio_info:
            audio_info["Status"] = "Nenhum dispositivo de áudio detectado"

        self.info["Áudio"] = audio_info

    def detectar_processos(self):
        proc_info = {}
        proc_list = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                info = proc.info
                proc_list.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        proc_list.sort(key=lambda x: x.get('memory_percent', 0) or 0, reverse=True)
        top_procs = proc_list[:20]

        for i, p in enumerate(top_procs):
            proc_info[f"#{i + 1} - {p.get('name', 'N/A')}"] = {
                "PID": str(p.get('pid', 'N/A')),
                "CPU (%)": f"{p.get('cpu_percent', 0):.1f}%",
                "Memória (%)": f"{p.get('memory_percent', 0):.2f}%",
                "Status": p.get('status', 'N/A'),
            }

        proc_info["_total"] = {"Total de Processos": str(len(proc_list))}
        self.info["Processos Ativos"] = proc_info

    def detectar_variaveis_ambiente(self):
        env_vars = {}
        important_vars = [
            'COMPUTERNAME', 'USERNAME', 'USERDOMAIN', 'OS', 'PROCESSOR_ARCHITECTURE',
            'PROCESSOR_IDENTIFIER', 'PROCESSOR_LEVEL', 'NUMBER_OF_PROCESSORS',
            'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PROGRAMFILES', 'PROGRAMFILES(X86)',
            'APPDATA', 'LOCALAPPDATA', 'USERPROFILE', 'HOMEPATH', 'HOMEDRIVE',
            'PATHEXT', 'COMSPEC', 'SYSTEMDRIVE',
        ]
        for var in important_vars:
            value = os.environ.get(var, "N/A")
            if value != "N/A":
                env_vars[var] = value

        self.info["Variáveis de Ambiente"] = env_vars

    def detectar_programas(self):
        programas = {}
        if winreg:
            paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            ]
            count = 0
            seen = set()
            for hive, path in paths:
                try:
                    key = winreg.OpenKey(hive, path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            try:
                                name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                if name and name not in seen:
                                    seen.add(name)
                                    count += 1
                                    prog_data = {"Nome": name}
                                    try:
                                        version, _ = winreg.QueryValueEx(subkey, "DisplayVersion")
                                        prog_data["Versão"] = version
                                    except:
                                        pass
                                    try:
                                        publisher, _ = winreg.QueryValueEx(subkey, "Publisher")
                                        prog_data["Fabricante"] = publisher
                                    except:
                                        pass
                                    programas[f"{count}. {name}"] = prog_data
                            except:
                                pass
                            winreg.CloseKey(subkey)
                        except:
                            pass
                    winreg.CloseKey(key)
                except:
                    pass

        if not programas:
            programas["Status"] = "Não foi possível listar programas instalados"
        else:
            programas["_total"] = {"Total de Programas": str(len(programas))}

        self.info["Programas Instalados"] = programas

    def detectar_servicos(self):
        servicos = {}
        try:
            services = list(psutil.win_service_iter())
            running = [s for s in services if s.status() == 'running']
            stopped = [s for s in services if s.status() == 'stopped']

            servicos["Resumo"] = {
                "Total de Serviços": str(len(services)),
                "Em Execução": str(len(running)),
                "Parados": str(len(stopped)),
            }

            for i, s in enumerate(running[:30]):
                try:
                    servicos[f"Ativo {i + 1}: {s.name()}"] = {
                        "Nome": s.display_name(),
                        "Status": s.status(),
                        "PID": str(s.pid()) if s.pid() else "N/A",
                    }
                except:
                    pass
        except:
            servicos["Status"] = "Não foi possível listar serviços"

        self.info["Serviços do Windows"] = servicos

    def detectar_drivers(self):
        drivers = {}
        try:
            result = run_hidden(
                ["driverquery", "/FO", "CSV", "/V"],
                capture_output=True, text=True, timeout=30
            )
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                count = 0
                for line in lines[1:51]:
                    values = [v.strip('"') for v in line.split('","')]
                    if len(values) >= 4:
                        count += 1
                        drivers[f"Driver {count}: {values[0]}"] = {
                            "Nome": values[0],
                            "Tipo": values[3] if len(values) > 3 else "N/A",
                            "Status": values[2] if len(values) > 2 else "N/A",
                        }
                drivers["_total"] = {"Total de Drivers Listados": str(len(lines) - 1)}
        except:
            drivers["Status"] = "Não foi possível listar drivers"

        self.info["Drivers"] = drivers

    def _formatar_bytes(self, bytes_val):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.2f} PB"


class HTMLGenerator:
    """Gera um relatório HTML bonito com os dados do hardware."""

    @staticmethod
    def gerar(info: dict, filepath: str):
        data_hora = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

        icons = {
            "Sistema Operacional": "💻", "Processador (CPU)": "🔲",
            "Memória RAM": "🧠", "Discos / Armazenamento": "💾",
            "Placa de Vídeo (GPU)": "🎮", "Rede": "🌐",
            "Placa-Mãe / BIOS": "🔧", "Monitor / Tela": "🖥️",
            "Bateria": "🔋", "Dispositivos USB": "🔌",
            "Áudio": "🔊", "Processos Ativos": "⚙️",
            "Variáveis de Ambiente": "📋", "Programas Instalados": "📦",
            "Serviços do Windows": "🛠️", "Drivers": "📟",
        }

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Relatório de Hardware - {datetime.now().strftime("%d/%m/%Y")}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0c0c1d 0%, #1a1a3e 25%, #0d1b2a 50%, #1b2838 100%);
            color: #e0e0e0; min-height: 100vh; padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            text-align: center; padding: 50px 30px;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
            border-radius: 24px; margin-bottom: 40px;
            border: 1px solid rgba(102, 126, 234, 0.2);
        }}
        .header h1 {{
            font-size: 2.5em; font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .header .subtitle {{ color: #8892b0; font-size: 1.1em; }}
        .header .date {{ color: #667eea; font-size: 0.95em; margin-top: 12px; font-weight: 500; }}
        .nav-index {{
            background: rgba(26, 26, 62, 0.6); border-radius: 16px;
            padding: 25px 30px; margin-bottom: 40px;
            border: 1px solid rgba(102, 126, 234, 0.15);
        }}
        .nav-index h2 {{ font-size: 1.3em; color: #667eea; margin-bottom: 15px; }}
        .nav-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px; }}
        .nav-item {{
            display: flex; align-items: center; padding: 10px 15px;
            background: rgba(102, 126, 234, 0.08); border-radius: 10px;
            text-decoration: none; color: #b0b8d1; transition: all 0.3s;
        }}
        .nav-item:hover {{ background: rgba(102, 126, 234, 0.2); color: #fff; transform: translateX(5px); }}
        .nav-item .icon {{ margin-right: 10px; font-size: 1.2em; }}
        .section {{
            background: rgba(26, 26, 62, 0.5); border-radius: 20px;
            margin-bottom: 30px; overflow: hidden;
            border: 1px solid rgba(102, 126, 234, 0.1);
        }}
        .section-header {{
            padding: 22px 30px;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.12), rgba(118, 75, 162, 0.08));
            border-bottom: 1px solid rgba(102, 126, 234, 0.1);
            display: flex; align-items: center; gap: 12px;
        }}
        .section-header .icon {{ font-size: 1.6em; }}
        .section-header h2 {{ font-size: 1.35em; color: #ccd6f6; }}
        .section-content {{ padding: 20px 30px 25px; }}
        .subsection {{ margin-bottom: 20px; }}
        .subsection-title {{
            font-size: 1em; font-weight: 600; color: #667eea;
            margin-bottom: 12px; padding-bottom: 6px;
            border-bottom: 1px solid rgba(102, 126, 234, 0.15);
        }}
        table {{ width: 100%; border-collapse: collapse; }}
        tr:hover {{ background: rgba(102, 126, 234, 0.06); }}
        td {{ padding: 10px 15px; border-bottom: 1px solid rgba(255, 255, 255, 0.04); }}
        td:first-child {{ font-weight: 500; color: #8892b0; width: 40%; font-size: 0.9em; }}
        td:last-child {{ color: #ccd6f6; font-size: 0.9em; word-break: break-word; }}
        .footer {{ text-align: center; padding: 40px 20px; color: #4a5568; font-size: 0.85em; }}
        .badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }}
        .badge-green {{ background: rgba(72, 187, 120, 0.15); color: #68d391; }}
        .badge-red {{ background: rgba(245, 101, 101, 0.15); color: #fc8181; }}
        .progress-bar {{ width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; margin-top: 5px; overflow: hidden; }}
        .progress-fill {{ height: 100%; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ Relatório de Hardware</h1>
            <p class="subtitle">Análise completa do sistema</p>
            <p class="date">📅 Gerado em {data_hora}</p>
        </div>
        <div class="nav-index">
            <h2>📑 Índice</h2>
            <div class="nav-grid">
"""

        for secao in info.keys():
            icon = icons.get(secao, "📌")
            section_id = secao.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
            html += f'<a href="#{section_id}" class="nav-item"><span class="icon">{icon}</span>{secao}</a>\n'

        html += "</div></div>\n"

        for secao, dados in info.items():
            icon = icons.get(secao, "📌")
            section_id = secao.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")

            html += f"""<div class="section" id="{section_id}">
                <div class="section-header"><span class="icon">{icon}</span><h2>{secao}</h2></div>
                <div class="section-content">"""

            if isinstance(dados, dict):
                has_subsections = any(isinstance(v, dict) for v in dados.values())

                if has_subsections:
                    for sub_key, sub_val in dados.items():
                        if sub_key.startswith("_"):
                            if isinstance(sub_val, dict):
                                html += '<div class="subsection"><table>'
                                for k, v in sub_val.items():
                                    html += f"<tr><td><strong>{k}</strong></td><td><strong>{v}</strong></td></tr>"
                                html += "</table></div>"
                            continue

                        if isinstance(sub_val, dict):
                            html += f'<div class="subsection"><div class="subsection-title">{sub_key}</div><table>'
                            for k, v in sub_val.items():
                                if not k.startswith("_"):
                                    v_str = HTMLGenerator._colorir_valor(k, str(v))
                                    html += f"<tr><td>{k}</td><td>{v_str}</td></tr>"
                            html += "</table></div>"
                        else:
                            html += f'<div class="subsection"><table><tr><td>{sub_key}</td><td>{sub_val}</td></tr></table></div>'
                else:
                    html += "<table>"
                    for k, v in dados.items():
                        if not k.startswith("_"):
                            v_str = HTMLGenerator._colorir_valor(k, str(v))
                            html += f"<tr><td>{k}</td><td>{v_str}</td></tr>"
                    html += "</table>"

            html += "</div></div>\n"

        html += f"""<div class="footer">
            <p>Relatório gerado por <strong>Hardware Detector Pro</strong></p>
            <p>Python {platform.python_version()} • {platform.platform()}</p>
        </div></div></body></html>"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

    @staticmethod
    def _colorir_valor(key, value):
        key_lower = key.lower()
        val_lower = value.lower()

        if val_lower in ("sim", "yes", "running", "ativa", "ativo"):
            return f'<span class="badge badge-green">{value}</span>'
        elif val_lower in ("não", "no", "stopped", "inativa", "inativo"):
            return f'<span class="badge badge-red">{value}</span>'

        if "%" in value and ("uso" in key_lower or "percent" in key_lower):
            try:
                pct = float(value.replace("%", "").strip())
                if pct > 80:
                    color = "linear-gradient(90deg, #f56565, #e53e3e)"
                elif pct > 50:
                    color = "linear-gradient(90deg, #ecc94b, #d69e2e)"
                else:
                    color = "linear-gradient(90deg, #48bb78, #38a169)"
                return f'{value}<div class="progress-bar"><div class="progress-fill" style="width: {pct}%; background: {color};"></div></div>'
            except:
                pass

        return value.replace("\n", "<br>")


class App(tk.Tk):
    """Interface gráfica principal."""

    BG_DARK = "#0f0f1e"
    BG_MEDIUM = "#1a1a2e"
    BG_LIGHT = "#16213e"
    ACCENT = "#667eea"
    ACCENT_HOVER = "#764ba2"
    SUCCESS = "#48bb78"
    TEXT = "#ccd6f6"
    TEXT_DIM = "#8892b0"

    ICONS = {
        "Sistema Operacional": "💻", "Processador (CPU)": "🔲",
        "Memória RAM": "🧠", "Discos / Armazenamento": "💾",
        "Placa de Vídeo (GPU)": "🎮", "Rede": "🌐",
        "Placa-Mãe / BIOS": "🔧", "Monitor / Tela": "🖥️",
        "Bateria": "🔋", "Dispositivos USB": "🔌",
        "Áudio": "🔊", "Processos Ativos": "⚙️",
        "Variáveis de Ambiente": "📋", "Programas Instalados": "📦",
        "Serviços do Windows": "🛠️", "Drivers": "📟",
    }

    def __init__(self):
        super().__init__()

        # Oculta a janela imediatamente
        self.withdraw()

        self.title("🖥️ Hardware Detector Pro")

        # Abre maximizada
        try:
            self.state("zoomed")
        except:
            pass

        # Configurar tamanho e posição
        w = 1100
        h = 750
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(900, 600)
        self.configure(bg=self.BG_DARK)

        # Inicializa nível de zoom
        self.zoom_level = 0
        self.zoom_step = 1

        # Protocolo de fechamento personalizado
        self.protocol("WM_DELETE_WINDOW", self.ao_fechar)

        # Atalho de zoom (Ctrl + scroll do mouse)
        self.bind_all("<Control-MouseWheel>", self.zoom_interface)

        self.detector = HardwareDetector()
        self.info = None
        self.tree = None
        self.resumo_container = None

        self._configurar_estilos()
        self._criar_interface()

        # MOSTRA A JANELA APENAS QUANDO TUDO ESTIVER PRONTO
        self.deiconify()

    def ao_fechar(self):
        """Confirma antes de fechar."""
        if messagebox.askokcancel("Sair", "Deseja realmente fechar o Hardware Detector Pro?"):
            self.destroy()

    def zoom_interface(self, event):
        """Aumenta ou diminui o zoom da interface com Ctrl + Scroll."""
        if event.delta > 0:
            self.zoom_level += self.zoom_step
        else:
            self.zoom_level -= self.zoom_step

        # Limita o zoom
        self.zoom_level = max(-3, min(self.zoom_level, 10))

        # Recalcula tamanhos de fonte
        base_size = 9
        new_size = base_size + self.zoom_level

        try:
            style = ttk.Style()
            style.configure("Custom.Treeview", font=("Segoe UI", new_size), rowheight=28 + self.zoom_level * 2)
            style.configure("Custom.Treeview.Heading", font=("Segoe UI", new_size + 1, "bold"))
            self.status_var.set(f"🔍 Zoom: {self.zoom_level:+d}")
        except:
            pass

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"),
                        foreground=self.ACCENT, background=self.BG_DARK)
        style.configure("Sub.TLabel", font=("Segoe UI", 10),
                        foreground=self.TEXT_DIM, background=self.BG_DARK)
        style.configure("Status.TLabel", font=("Segoe UI", 10),
                        foreground=self.TEXT, background=self.BG_DARK)
        style.configure("Info.TLabel", font=("Segoe UI", 9),
                        foreground="#4a5568", background=self.BG_DARK)

        style.configure("Custom.Horizontal.TProgressbar",
                        troughcolor=self.BG_LIGHT, background=self.ACCENT,
                        thickness=15, borderwidth=0)

        style.configure("TNotebook", background=self.BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=self.BG_LIGHT, foreground=self.TEXT_DIM,
                        padding=[15, 8], font=("Segoe UI", 9, "bold"),
                        borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", self.ACCENT)],
                  foreground=[("selected", "white")])

        style.configure("Custom.Treeview",
                        background=self.BG_MEDIUM,
                        foreground=self.TEXT,
                        fieldbackground=self.BG_MEDIUM,
                        borderwidth=0,
                        font=("Segoe UI", 9),
                        rowheight=28)
        style.configure("Custom.Treeview.Heading",
                        background=self.ACCENT,
                        foreground="white",
                        font=("Segoe UI", 10, "bold"),
                        borderwidth=0,
                        relief="flat")
        style.map("Custom.Treeview",
                  background=[("selected", self.ACCENT_HOVER)],
                  foreground=[("selected", "white")])
        style.map("Custom.Treeview.Heading",
                  background=[("active", self.ACCENT_HOVER)])

        style.configure("Search.TEntry",
                        fieldbackground=self.BG_LIGHT,
                        foreground=self.TEXT,
                        borderwidth=1,
                        insertcolor=self.TEXT)

    def _criar_interface(self):
        # === TOPO ===
        top_frame = tk.Frame(self, bg=self.BG_DARK)
        top_frame.pack(fill=tk.X, padx=20, pady=(15, 5))

        title_frame = tk.Frame(top_frame, bg=self.BG_DARK)
        title_frame.pack(fill=tk.X)

        ttk.Label(title_frame, text="🖥️ Hardware Detector Pro",
                  style="Title.TLabel").pack(side=tk.LEFT)

        btn_top_frame = tk.Frame(title_frame, bg=self.BG_DARK)
        btn_top_frame.pack(side=tk.RIGHT)

        self.btn_detect = tk.Button(
            btn_top_frame, text="🔍  Detectar Hardware",
            font=("Segoe UI", 11, "bold"),
            bg=self.ACCENT, fg="white",
            activebackground=self.ACCENT_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2", padx=20, pady=10,
            command=self._iniciar_deteccao
        )
        self.btn_detect.pack(side=tk.LEFT, padx=5)

        self.btn_save = tk.Button(
            btn_top_frame, text="💾  Salvar HTML",
            font=("Segoe UI", 11, "bold"),
            bg=self.SUCCESS, fg="white",
            activebackground="#38a169", activeforeground="white",
            relief=tk.FLAT, cursor="hand2", padx=20, pady=10,
            command=self._salvar_html, state=tk.DISABLED
        )
        self.btn_save.pack(side=tk.LEFT, padx=5)

        ttk.Label(top_frame,
                  text="Detecta CPU, GPU, RAM, Discos, Rede e mais — Exibe resultados e gera relatório HTML",
                  style="Sub.TLabel").pack(anchor=tk.W, pady=(5, 0))

        sep = tk.Frame(self, height=2, bg=self.ACCENT)
        sep.pack(fill=tk.X, padx=20, pady=(10, 0))

        # === BARRA DE PROGRESSO ===
        progress_frame = tk.Frame(self, bg=self.BG_DARK)
        progress_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        self.progress = ttk.Progressbar(
            progress_frame, style="Custom.Horizontal.TProgressbar",
            orient=tk.HORIZONTAL, mode='determinate'
        )
        self.progress.pack(fill=tk.X)

        status_frame = tk.Frame(self, bg=self.BG_DARK)
        status_frame.pack(fill=tk.X, padx=20, pady=(5, 10))

        self.status_var = tk.StringVar(value="⏸ Pronto. Clique em 'Detectar Hardware' para iniciar.")
        ttk.Label(status_frame, textvariable=self.status_var,
                  style="Status.TLabel").pack(side=tk.LEFT)

        self.step_var = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.step_var,
                  style="Info.TLabel").pack(side=tk.RIGHT)

        # === ÁREA DE RESULTADOS ===
        results_frame = tk.Frame(self, bg=self.BG_DARK)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        search_frame = tk.Frame(results_frame, bg=self.BG_DARK)
        search_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(search_frame, text="🔎", font=("Segoe UI", 12),
                 bg=self.BG_DARK, fg=self.ACCENT).pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=("Segoe UI", 10), bg=self.BG_LIGHT, fg=self.TEXT,
            insertbackground=self.TEXT, relief=tk.FLAT, bd=5
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        tk.Button(search_frame, text="✖", font=("Segoe UI", 10, "bold"),
                  bg=self.BG_LIGHT, fg=self.TEXT_DIM, relief=tk.FLAT,
                  cursor="hand2", padx=10,
                  command=lambda: self.search_var.set("")).pack(side=tk.LEFT, padx=(5, 0))

        tk.Button(search_frame, text="⬇ Expandir Tudo", font=("Segoe UI", 9),
                  bg=self.BG_LIGHT, fg=self.TEXT, relief=tk.FLAT,
                  cursor="hand2", padx=10,
                  command=self._expandir_tudo).pack(side=tk.LEFT, padx=(10, 0))

        tk.Button(search_frame, text="⬆ Recolher Tudo", font=("Segoe UI", 9),
                  bg=self.BG_LIGHT, fg=self.TEXT, relief=tk.FLAT,
                  cursor="hand2", padx=10,
                  command=self._recolher_tudo).pack(side=tk.LEFT, padx=(5, 0))

        self.notebook = ttk.Notebook(results_frame)
        self._criar_aba_tree()
        self._criar_aba_resumo()

        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.search_var.trace_add("write", self._on_search)
        self._add_placeholder(self.search_entry, "Buscar em todos os resultados...")

        # === RODAPÉ ===
        footer_frame = tk.Frame(self, bg=self.BG_DARK)
        footer_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        ttk.Label(footer_frame,
                  text=f"Python {platform.python_version()} • {platform.system()} {platform.release()}",
                  style="Info.TLabel").pack(side=tk.LEFT)

        self.result_var = tk.StringVar(value="")
        ttk.Label(footer_frame, textvariable=self.result_var,
                  style="Sub.TLabel").pack(side=tk.RIGHT)

    def _add_placeholder(self, entry, text):
        entry.insert(0, text)
        entry.config(fg=self.TEXT_DIM)

        def on_focus_in(e):
            if entry.get() == text:
                entry.delete(0, tk.END)
                entry.config(fg=self.TEXT)

        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, text)
                entry.config(fg=self.TEXT_DIM)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def _criar_aba_tree(self):
        tree_frame = tk.Frame(self.notebook, bg=self.BG_MEDIUM)
        self.notebook.add(tree_frame, text="  📊 Dados Detalhados  ")

        container = tk.Frame(tree_frame, bg=self.BG_MEDIUM)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(container, style="Custom.Treeview",
                                  columns=("valor",), show="tree headings")
        self.tree.heading("#0", text="Categoria / Propriedade", anchor=tk.W)
        self.tree.heading("valor", text="Valor", anchor=tk.W)
        self.tree.column("#0", width=400, minwidth=250)
        self.tree.column("valor", width=500, minwidth=200)

        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure("categoria", background=self.BG_LIGHT,
                                foreground=self.ACCENT, font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("subcategoria", background="#20293c",
                                foreground="#f093fb", font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("item_par", background=self.BG_MEDIUM)
        self.tree.tag_configure("item_impar", background="#181828")

        self.tree.insert("", tk.END, text="⏸  Clique em 'Detectar Hardware' para começar...",
                         values=("",), tags=("categoria",))

    def _criar_aba_resumo(self):
        resumo_frame = tk.Frame(self.notebook, bg=self.BG_MEDIUM)
        self.notebook.add(resumo_frame, text="  ⭐ Resumo Rápido  ")

        canvas = tk.Canvas(resumo_frame, bg=self.BG_MEDIUM, highlightthickness=0)
        scrollbar = ttk.Scrollbar(resumo_frame, orient="vertical", command=canvas.yview)
        self.resumo_container = tk.Frame(canvas, bg=self.BG_MEDIUM)

        self.resumo_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.resumo_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        tk.Label(self.resumo_container,
                 text="\n\n⏸  Nenhum dado detectado ainda.\n\nClique em '🔍 Detectar Hardware' no topo.\n",
                 font=("Segoe UI", 12), bg=self.BG_MEDIUM, fg=self.TEXT_DIM).pack(pady=50)

    def _preencher_tree(self):
        if not self.tree:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.info:
            return

        for secao, dados in self.info.items():
            icon = self.ICONS.get(secao, "📌")
            categoria_id = self.tree.insert("", tk.END,
                                             text=f"{icon}  {secao}",
                                             values=("",),
                                             tags=("categoria",),
                                             open=False)

            if isinstance(dados, dict):
                has_subsections = any(isinstance(v, dict) for v in dados.values())

                if has_subsections:
                    for sub_key, sub_val in dados.items():
                        if isinstance(sub_val, dict):
                            display_key = sub_key.lstrip("_")
                            sub_id = self.tree.insert(categoria_id, tk.END,
                                                       text=f"📁  {display_key}",
                                                       values=("",),
                                                       tags=("subcategoria",),
                                                       open=True)
                            for i, (k, v) in enumerate(sub_val.items()):
                                if not k.startswith("_"):
                                    tag = "item_par" if i % 2 == 0 else "item_impar"
                                    self.tree.insert(sub_id, tk.END,
                                                     text=f"    • {k}",
                                                     values=(str(v),),
                                                     tags=(tag,))
                        else:
                            self.tree.insert(categoria_id, tk.END,
                                             text=f"    • {sub_key}",
                                             values=(str(sub_val),),
                                             tags=("item_par",))
                else:
                    for i, (k, v) in enumerate(dados.items()):
                        if not k.startswith("_"):
                            tag = "item_par" if i % 2 == 0 else "item_impar"
                            self.tree.insert(categoria_id, tk.END,
                                             text=f"    • {k}",
                                             values=(str(v),),
                                             tags=(tag,))

        children = self.tree.get_children()
        if children:
            self.tree.item(children[0], open=True)

    def _preencher_resumo(self):
        if not self.resumo_container:
            return

        for widget in self.resumo_container.winfo_children():
            widget.destroy()

        if not self.info:
            return

        tk.Label(self.resumo_container, text="⭐ Resumo do Sistema",
                 font=("Segoe UI", 18, "bold"),
                 bg=self.BG_MEDIUM, fg=self.ACCENT).pack(pady=(10, 20), anchor=tk.W, padx=15)

        cards_frame = tk.Frame(self.resumo_container, bg=self.BG_MEDIUM)
        cards_frame.pack(fill=tk.X, padx=15)

        so = self.info.get("Sistema Operacional", {})
        self._criar_card(cards_frame, "💻", "Sistema",
                         so.get("Sistema", "N/A"),
                         f"{so.get('Release', '')} - {so.get('Arquitetura', '')}",
                         0, 0)

        cpu = self.info.get("Processador (CPU)", {})
        cpu_nome = cpu.get("Nome Completo da CPU", cpu.get("Processador", "N/A"))
        if len(cpu_nome) > 40:
            cpu_nome = cpu_nome[:40] + "..."
        self._criar_card(cards_frame, "🔲", "Processador",
                         cpu_nome,
                         f"{cpu.get('Núcleos Físicos', 'N/A')} núcleos, {cpu.get('Núcleos Lógicos (Threads)', 'N/A')} threads",
                         0, 1)

        ram = self.info.get("Memória RAM", {})
        modelo_ram = ram.get("Modelo (Simplificado)", "Desconhecido")
        self._criar_card(cards_frame, "🧠", "Memória RAM",
                         ram.get("RAM Total", "N/A"),
                         f"{modelo_ram}\nUsado: {ram.get('RAM Usada', 'N/A')} ({ram.get('Percentual de Uso', 'N/A')})",
                         0, 2)

        gpu_info = self.info.get("Placa de Vídeo (GPU)", {})
        gpu_nome = "N/A"
        if gpu_info:
            primeira = next(iter(gpu_info.keys()))
            gpu_nome = primeira.split(": ", 1)[-1] if ": " in primeira else primeira
            if len(gpu_nome) > 40:
                gpu_nome = gpu_nome[:40] + "..."
        self._criar_card(cards_frame, "🎮", "Placa de Vídeo",
                         gpu_nome,
                         f"{len(gpu_info)} GPU Detectada",
                         1, 0)

        self._criar_card(cards_frame, "🏷️", "Computador",
                         so.get("Nome do Computador", "N/A"),
                         f"Usuário: {so.get('Usuário Atual', 'N/A')}",
                         1, 1)

        self._criar_card(cards_frame, "⏱️", "Tempo Ligado",
                         so.get("Tempo Ligado", "N/A"),
                         f"Boot: {so.get('Boot Time', 'N/A')}",
                         1, 2)

        rede = self.info.get("Rede", {})
        info_ger = rede.get("Informações Gerais", {})
        self._criar_card(cards_frame, "🌐", "Rede",
                         info_ger.get("IP Local", "N/A"),
                         f"MAC: {info_ger.get('MAC Address', 'N/A')}",
                         2, 0)

        discos = self.info.get("Discos / Armazenamento", {})
        num_discos = sum(1 for k in discos.keys() if k.startswith("Disco"))
        self._criar_card(cards_frame, "💾", "Armazenamento",
                         f"{num_discos} Partições",
                         "Ver detalhes na aba Dados",
                         2, 1)

        bat = self.info.get("Bateria", {})
        bat_pct = bat.get("Percentual", bat.get("Status", "N/A"))
        bat_sub = f"Tomada: {bat.get('Conectado na Tomada', 'N/A')}" if "Percentual" in bat else ""
        self._criar_card(cards_frame, "🔋", "Bateria",
                         bat_pct, bat_sub, 2, 2)

        for c in range(3):
            cards_frame.grid_columnconfigure(c, weight=1, uniform="col")

        stats_frame = tk.Frame(self.resumo_container, bg=self.BG_MEDIUM)
        stats_frame.pack(fill=tk.X, padx=15, pady=(20, 10))

        tk.Label(stats_frame, text="📊 Estatísticas Gerais",
                 font=("Segoe UI", 14, "bold"),
                 bg=self.BG_MEDIUM, fg=self.ACCENT).pack(anchor=tk.W, pady=(0, 10))

        stats_inner = tk.Frame(stats_frame, bg=self.BG_MEDIUM)
        stats_inner.pack(fill=tk.X)

        total_categorias = len(self.info)
        total_itens = sum(
            sum(len(v) if isinstance(v, dict) else 1 for v in cat.values()) if isinstance(cat, dict) else 1
            for cat in self.info.values()
        )

        proc = self.info.get("Processos Ativos", {})
        total_proc = proc.get("_total", {}).get("Total de Processos", "N/A")

        prog = self.info.get("Programas Instalados", {})
        total_prog = prog.get("_total", {}).get("Total de Programas", "N/A")

        serv = self.info.get("Serviços do Windows", {})
        total_serv = serv.get("Resumo", {}).get("Total de Serviços", "N/A")

        self._criar_stat(stats_inner, "📁", total_categorias, "Categorias", 0)
        self._criar_stat(stats_inner, "📌", total_itens, "Itens Detectados", 1)
        self._criar_stat(stats_inner, "⚙️", total_proc, "Processos", 2)
        self._criar_stat(stats_inner, "📦", total_prog, "Programas", 3)
        self._criar_stat(stats_inner, "🛠️", total_serv, "Serviços", 4)

        for c in range(5):
            stats_inner.grid_columnconfigure(c, weight=1, uniform="stat")

    def _criar_card(self, parent, icon, titulo, valor, subtitulo, row, col):
        card = tk.Frame(parent, bg=self.BG_LIGHT, highlightbackground=self.ACCENT,
                        highlightthickness=1)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        inner = tk.Frame(card, bg=self.BG_LIGHT)
        inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)

        top = tk.Frame(inner, bg=self.BG_LIGHT)
        top.pack(fill=tk.X)

        tk.Label(top, text=icon, font=("Segoe UI", 24),
                 bg=self.BG_LIGHT, fg=self.ACCENT).pack(side=tk.LEFT)

        tk.Label(top, text=titulo, font=("Segoe UI", 9, "bold"),
                 bg=self.BG_LIGHT, fg=self.TEXT_DIM).pack(side=tk.LEFT, padx=(10, 0))

        tk.Label(inner, text=str(valor), font=("Segoe UI", 13, "bold"),
                 bg=self.BG_LIGHT, fg=self.TEXT,
                 wraplength=250, justify=tk.LEFT).pack(anchor=tk.W, pady=(8, 4))

        if subtitulo:
            tk.Label(inner, text=str(subtitulo), font=("Segoe UI", 8),
                     bg=self.BG_LIGHT, fg=self.TEXT_DIM,
                     wraplength=250, justify=tk.LEFT).pack(anchor=tk.W)

    def _criar_stat(self, parent, icon, valor, label, col):
        stat = tk.Frame(parent, bg=self.BG_LIGHT)
        stat.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")

        tk.Label(stat, text=icon, font=("Segoe UI", 20),
                 bg=self.BG_LIGHT, fg=self.ACCENT).pack(pady=(10, 0))

        tk.Label(stat, text=str(valor), font=("Segoe UI", 16, "bold"),
                 bg=self.BG_LIGHT, fg=self.TEXT).pack()

        tk.Label(stat, text=label, font=("Segoe UI", 8),
                 bg=self.BG_LIGHT, fg=self.TEXT_DIM).pack(pady=(0, 10))

    def _on_search(self, *args):
        if not self.tree:
            return

        termo = self.search_var.get().lower().strip()
        if termo == "buscar em todos os resultados..." or not termo:
            self._preencher_tree()
            return

        if not self.info:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for secao, dados in self.info.items():
            icon = self.ICONS.get(secao, "📌")
            matches = []

            if isinstance(dados, dict):
                for k, v in dados.items():
                    if isinstance(v, dict):
                        for sk, sv in v.items():
                            if termo in str(k).lower() or termo in str(sk).lower() or termo in str(sv).lower():
                                matches.append((f"{k} → {sk}", sv))
                    else:
                        if termo in str(k).lower() or termo in str(v).lower():
                            matches.append((k, v))

            if matches or termo in secao.lower():
                cat_id = self.tree.insert("", tk.END,
                                           text=f"{icon}  {secao}",
                                           values=("",),
                                           tags=("categoria",),
                                           open=True)
                for i, (k, v) in enumerate(matches):
                    tag = "item_par" if i % 2 == 0 else "item_impar"
                    self.tree.insert(cat_id, tk.END,
                                     text=f"    • {k}",
                                     values=(str(v),),
                                     tags=(tag,))

    def _expandir_tudo(self):
        if not self.tree:
            return
        def expand(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expand(child)

        for item in self.tree.get_children():
            expand(item)

    def _recolher_tudo(self):
        if not self.tree:
            return
        def collapse(item):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                collapse(child)

        for item in self.tree.get_children():
            collapse(item)

    def _iniciar_deteccao(self):
        self.btn_detect.config(state=tk.DISABLED, bg="#4a5568")
        self.btn_save.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.result_var.set("")
        self.status_var.set("🔄 Detectando hardware... Aguarde.")

        if self.tree:
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.tree.insert("", tk.END, text="🔄  Detectando...",
                             values=("",), tags=("categoria",))

        import threading
        thread = threading.Thread(target=self._detectar, daemon=True)
        thread.start()

    def _detectar(self):
        def progress_callback(current, total, nome):
            pct = (current / total) * 100
            self.after(0, self._atualizar_progresso, pct, current, total, nome)

        self.info = self.detector.detectar_tudo(progress_callback)
        self.after(0, self._deteccao_concluida)

    def _atualizar_progresso(self, pct, current, total, nome):
        self.progress['value'] = pct
        self.status_var.set(f"🔄 Detectando: {nome}...")
        self.step_var.set(f"Etapa {current}/{total}")

    def _deteccao_concluida(self):
        self.progress['value'] = 100
        total_items = sum(
            sum(len(v) if isinstance(v, dict) else 1 for v in cat.values()) if isinstance(cat, dict) else 1
            for cat in self.info.values()
        )
        self.status_var.set(f"✅ Detecção concluída! {len(self.info)} categorias • {total_items} itens")
        self.step_var.set("Concluído")

        self.btn_detect.config(state=tk.NORMAL, bg=self.ACCENT)
        self.btn_save.config(state=tk.NORMAL)

        self._preencher_tree()
        self._preencher_resumo()

        self.notebook.select(1)

    def _salvar_html(self):
        if not self.info:
            messagebox.showwarning("Aviso", "Primeiro detecte o hardware!")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=f"relatorio_hardware_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            title="Salvar Relatório HTML"
        )

        if filepath:
            try:
                HTMLGenerator.gerar(self.info, filepath)
                self.result_var.set(f"✅ Salvo: {os.path.basename(filepath)}")

                resposta = messagebox.askyesno("Sucesso! 🎉",
                                                f"Relatório salvo com sucesso!\n\n{filepath}\n\nDeseja abrir agora?")
                if resposta:
                    import webbrowser
                    webbrowser.open(filepath)

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
