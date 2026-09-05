#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════╗
║   🔒 Scanner de Vulnerabilidades do PC           ║
║   Interface Gráfica + Relatório HTML             ║
║   >>> COM ATIVIDADE EM TEMPO REAL DETALHADA <<<  ║
╚══════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import platform
import socket
import os
import sys
import json
import datetime
import threading
import webbrowser
import ctypes
import re
import shutil

try:
    import psutil
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil


class ScanAbortedException(Exception):
    """Exceção levantada para interromper o scan na hora."""
    pass


# ══════════════════════════════════════════════════════════════
# CLASSES DE VERIFICAÇÃO
# ══════════════════════════════════════════════════════════════

class VulnerabilityScanner:
    """Motor principal de scan com cancelamento instantâneo."""

    def __init__(self, callback=None, result_callback=None):
        self.results = {
            "system_info": {},
            "vulnerabilities": [],
            "warnings": [],
            "info": [],
            "scores": {
                "overall": 100,
                "categories": {},
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "total_vulns": 0,
                "total_warnings": 0,
                "total_info": 0
            },
            "scan_date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "scan_duration": 0,
            "interrupted": False
        }
        self.callback = callback
        self.result_callback = result_callback
        self.total_checks = 20
        self.current_check = 0
        self._stop_event = threading.Event()
        self.current_proc = None

    def stop(self):
        """Para o scan NA HORA matando processos pendentes."""
        self._stop_event.set()
        if self.current_proc:
            try:
                self.current_proc.kill()
            except Exception:
                pass

    def is_stopped(self):
        return self._stop_event.is_set()

    def check_abort(self):
        """Se o usuário clicou em stop, interrompe imediatamente."""
        if self.is_stopped():
            raise ScanAbortedException("Scan interrompido pelo usuário.")

    def log(self, msg):
        if self.callback:
            self.callback(msg)

    def emit_result(self, result_type, data):
        if self.result_callback:
            self.result_callback(result_type, data)

    def add_vulnerability(self, vuln):
        self.check_abort()
        self.results["vulnerabilities"].append(vuln)
        self.emit_result("vulnerability", vuln)

    def add_warning(self, warn):
        self.check_abort()
        self.results["warnings"].append(warn)
        self.emit_result("warning", warn)

    def add_info(self, info):
        self.check_abort()
        self.results["info"].append(info)
        self.emit_result("info", info)

    def update_progress(self):
        self.current_check += 1
        progress = (self.current_check / self.total_checks) * 100
        if self.callback:
            self.callback(f"__PROGRESS__{progress}")

    def run_command(self, cmd, shell=True):
        """Executa comando monitorando stop para matar na hora se necessário."""
        if self.is_stopped():
            raise ScanAbortedException()
        try:
            self.current_proc = subprocess.Popen(
                cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8', errors='replace'
            )

            while True:
                if self.is_stopped():
                    try:
                        self.current_proc.kill()
                    except Exception:
                        pass
                    raise ScanAbortedException()

                try:
                    stdout, _ = self.current_proc.communicate(timeout=0.1)
                    return stdout.strip() if stdout else ""
                except subprocess.TimeoutExpired:
                    continue
        except ScanAbortedException:
            raise
        except Exception:
            return ""
        finally:
            self.current_proc = None

    def run_full_scan(self):
        """Executa verificações com interrupção instantânea."""
        import time
        start_time = time.time()
        self.results["scan_date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        self.log("🚀 Iniciando scan completo do sistema\n")
        self.log("=" * 60)

        checks = [
            ("📋 Coletando informações do sistema\n", self.check_system_info),
            ("🔄 Verificando atualizações do Windows\n", self.check_windows_update),
            ("🧱 Verificando Firewall\n", self.check_firewall),
            ("🛡️ Verificando Antivírus\n", self.check_antivirus),
            ("🔐 Verificando UAC\n", self.check_uac),
            ("🌐 Verificando portas abertas\n", self.check_open_ports),
            ("⚙️ Verificando serviços perigosos\n", self.check_dangerous_services),
            ("📂 Verificando compartilhamentos de rede\n", self.check_network_shares),
            ("🔑 Verificando política de senhas\n", self.check_password_policy),
            ("🖥️ Verificando Remote Desktop\n", self.check_rdp),
            ("📡 Verificando SMBv1\n", self.check_smbv1),
            ("👤 Verificando contas de usuário\n", self.check_user_accounts),
            ("▶️ Verificando AutoRun\n", self.check_autorun),
            ("📦 Verificando programas instalados\n", self.check_installed_programs),
            ("💾 Verificando espaço em disco\n", self.check_disk_space),
            ("🔍 Verificando processos em execução\n", self.check_suspicious_processes),
            ("🌍 Verificando configuração DNS\n", self.check_dns_config),
            ("🔒 Verificando Secure Boot / BitLocker\n", self.check_secure_boot),
            ("⚡ Verificando PowerShell\n", self.check_powershell_policy),
            ("📊 Calculando scores de segurança\n", self.calculate_scores),
        ]

        try:
            for i, (msg, func) in enumerate(checks, 1):
                self.check_abort()
                self.log(f"\n[{i}/{len(checks)}] {msg}")
                self.emit_result("check_start", {"step": i, "total": len(checks), "name": msg})
                try:
                    func()
                except ScanAbortedException:
                    raise
                except Exception as e:
                    self.log(f"   ⚠️ Erro na verificação: {str(e)}")
                self.update_progress()

        except ScanAbortedException:
            self.results["interrupted"] = True
            self.results["scan_duration"] = round(time.time() - start_time, 2)
            self.log("\n" + "=" * 60)
            self.log(f"⏹️ SCAN INTERROMPIDO INSTANTANEAMENTE EM {self.results['scan_duration']}s!")
            try:
                self.calculate_scores()
            except Exception:
                pass
            self.emit_result("scan_stopped", self.results)
            return self.results

        self.results["scan_duration"] = round(time.time() - start_time, 2)
        self.log("\n" + "=" * 60)
        self.log(f"✅ Scan completo em {self.results['scan_duration']}s")
        self.log(f"   🔴 Vulnerabilidades: {len(self.results['vulnerabilities'])}")
        self.log(f"   🟡 Avisos: {len(self.results['warnings'])}")
        self.log(f"   🟢 Informações: {len(self.results['info'])}")

        self.emit_result("scan_complete", self.results)
        return self.results

    def check_system_info(self):
        self.emit_result("activity", {"message": "📋 Coletando informações do sistema\n"})
        uname = platform.uname()
        self.results["system_info"] = {
            "hostname": uname.node,
            "os": f"{uname.system} {uname.release}",
            "os_version": uname.version,
            "architecture": uname.machine,
            "processor": uname.processor or platform.processor(),
            "ram_total": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
            "ram_used_pct": psutil.virtual_memory().percent,
            "cpu_count": psutil.cpu_count(),
            "cpu_usage": psutil.cpu_percent(interval=0.3),
            "boot_time": datetime.datetime.fromtimestamp(
                psutil.boot_time()).strftime("%d/%m/%Y %H:%M"),
            "ip_address": self._get_ip(),
            "mac_address": self._get_mac(),
            "username": os.getenv("USERNAME", "N/A"),
            "is_admin": self._is_admin()
        }
        self.emit_result("system_info", self.results["system_info"])

    def _get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "N/A"

    def _get_mac(self):
        try:
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == psutil.AF_LINK:
                        if addr.address and addr.address != "00:00:00:00:00:00":
                            return addr.address
        except Exception:
            pass
        return "N/A"

    def _is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def check_windows_update(self):
        if platform.system() != "Windows":
            self.add_info({
                "title": "Windows Update",
                "detail": "Verificação disponível apenas no Windows",
                "category": "updates"
            })
            return

        self.emit_result("activity", {"message": "🔄 Consultando serviço Windows Update\n"})
        output = self.run_command('sc query wuauserv')
        if "RUNNING" in output:
            self.add_info({
                "title": "Windows Update Ativo",
                "detail": "O serviço Windows Update está em execução",
                "category": "updates"
            })
        elif "STOPPED" in output:
            self.add_vulnerability({
                "title": "Windows Update Parado",
                "detail": "O serviço Windows Update está parado.",
                "severity": "alta",
                "category": "updates",
                "fix": "Execute 'services.msc' e inicie o serviço 'Windows Update'"
            })
        else:
            self.add_warning({
                "title": "Windows Update - Status Desconhecido",
                "detail": "Não foi possível determinar o status do serviço Windows Update",
                "category": "updates"
            })

        self.check_abort()
        self.emit_result("activity", {"message": "🔄 Verificando data da última atualização\n"})

        ps_cmd = (
            'powershell -Command "'
            'try { $s = New-Object -ComObject Microsoft.Update.Session; '
            '$u = $s.CreateUpdateSearcher(); '
            '$h = $u.GetTotalHistoryCount(); '
            'if($h -gt 0){ $r = $u.QueryHistory(0,1); '
            '$r | ForEach-Object { $_.Date.ToString(\'yyyy-MM-dd\') } } '
            'else { Write-Output \'SemHistorico\' } } '
            'catch { Write-Output \'Erro\' }"'
        )
        last_update = self.run_command(ps_cmd)
        if last_update and last_update not in ["Erro", "SemHistorico", ""]:
            try:
                last_date = datetime.datetime.strptime(last_update.strip(), "%Y-%m-%d")
                days_ago = (datetime.datetime.now() - last_date).days
                if days_ago > 30:
                    self.add_vulnerability({
                        "title": f"Sistema sem atualização há {days_ago} dias",
                        "detail": f"Última atualização: {last_update}.",
                        "severity": "alta" if days_ago > 90 else "media",
                        "category": "updates",
                        "fix": "Abra Configurações > Atualização e Segurança > Windows Update"
                    })
                else:
                    self.add_info({
                        "title": f"Sistema atualizado ({days_ago} dias atrás)",
                        "detail": f"Última atualização: {last_update}",
                        "category": "updates"
                    })
            except Exception:
                pass

    def check_firewall(self):
        if platform.system() != "Windows":
            return

        profiles = {
            "Domain": "domainprofile",
            "Private": "privateprofile",
            "Public": "publicprofile"
        }

        for name, profile in profiles.items():
            self.check_abort()
            self.emit_result("activity", {"message": f"🧱 Verificando firewall perfil {name}\n"})
            output = self.run_command(f'netsh advfirewall show {profile} state')
            if "ON" in output.upper():
                self.add_info({
                    "title": f"Firewall {name} - Ativo ✅",
                    "detail": f"O perfil {name} do firewall está habilitado",
                    "category": "firewall"
                })
            else:
                self.add_vulnerability({
                    "title": f"Firewall {name} - DESATIVADO",
                    "detail": f"O perfil {name} do firewall está desabilitado.",
                    "severity": "critica",
                    "category": "firewall",
                    "fix": f"Execute: netsh advfirewall set {profile} state on"
                })

    def check_antivirus(self):
        if platform.system() != "Windows":
            return

        self.emit_result("activity", {"message": "🛡️ Consultando antivírus instalados\n"})
        ps_cmd = (
            'powershell -Command "'
            'Get-CimInstance -Namespace root/SecurityCenter2 '
            '-ClassName AntiVirusProduct | '
            'Select-Object displayName, productState | '
            'ConvertTo-Json"'
        )
        output = self.run_command(ps_cmd)

        if output:
            try:
                av_data = json.loads(output)
                if not isinstance(av_data, list):
                    av_data = [av_data]

                for av in av_data:
                    self.check_abort()
                    name = av.get("displayName", "Desconhecido")
                    state = av.get("productState", 0)
                    hex_state = hex(state)
                    enabled = (state >> 12) & 0xF

                    self.emit_result("activity", {"message": f"🛡️ Analisando: {name}"})

                    if enabled in [1, 3]:
                        self.add_info({
                            "title": f"Antivírus Ativo: {name}",
                            "detail": f"Estado: {hex_state}",
                            "category": "antivirus"
                        })
                    else:
                        self.add_warning({
                            "title": f"Antivírus possivelmente inativo: {name}",
                            "detail": f"Estado: {hex_state}",
                            "category": "antivirus"
                        })
            except json.JSONDecodeError:
                if "Windows Defender" in output or "displayName" in output:
                    self.add_info({
                        "title": "Antivírus Detectado",
                        "detail": "Foi detectado antivírus no sistema",
                        "category": "antivirus"
                    })
        else:
            self.add_vulnerability({
                "title": "Nenhum Antivírus Detectado",
                "detail": "Não foi possível detectar um antivírus ativo.",
                "severity": "critica",
                "category": "antivirus",
                "fix": "Instale e ative o Windows Defender ou outro antivírus"
            })

    def check_uac(self):
        if platform.system() != "Windows":
            return

        self.emit_result("activity", {"message": "🔐 Lendo registro UAC\n"})
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
            )
            consent_admin, _ = winreg.QueryValueEx(key, "ConsentPromptBehaviorAdmin")
            lua_enabled, _ = winreg.QueryValueEx(key, "EnableLUA")
            winreg.CloseKey(key)

            if lua_enabled == 0:
                self.add_vulnerability({
                    "title": "UAC Desativado",
                    "detail": "O Controle de Conta de Usuário está desativado.",
                    "severity": "critica",
                    "category": "uac",
                    "fix": "Ative o UAC em Painel de Controle > Contas de Usuário"
                })
            elif consent_admin == 0:
                self.add_vulnerability({
                    "title": "UAC - Nível Muito Baixo",
                    "detail": "UAC configurado para nunca notificar.",
                    "severity": "alta",
                    "category": "uac",
                    "fix": "Aumente o nível do UAC"
                })
            elif consent_admin == 5:
                self.add_info({
                    "title": "UAC - Nível Padrão ✅",
                    "detail": "UAC configurado no nível padrão",
                    "category": "uac"
                })
            else:
                self.add_info({
                    "title": f"UAC Ativo (nível: {consent_admin})",
                    "detail": "UAC está habilitado",
                    "category": "uac"
                })
        except Exception:
            self.add_warning({
                "title": "UAC - Não verificado",
                "detail": "Não foi possível verificar o status do UAC",
                "category": "uac"
            })

    def check_open_ports(self):
        dangerous_ports = {
            21: ("FTP", "alta"), 23: ("Telnet", "critica"),
            25: ("SMTP", "media"), 135: ("RPC", "media"),
            139: ("NetBIOS", "alta"), 445: ("SMB", "alta"),
            1433: ("SQL Server", "alta"), 1434: ("SQL Browser", "alta"),
            3306: ("MySQL", "alta"), 3389: ("RDP", "alta"),
            5432: ("PostgreSQL", "alta"), 5900: ("VNC", "critica"),
            5985: ("WinRM HTTP", "alta"), 5986: ("WinRM HTTPS", "media"),
            8080: ("HTTP Alt", "media"), 27017: ("MongoDB", "alta"),
        }

        self.emit_result("activity", {"message": "🌐 Enumerando conexões de rede\n"})
        open_ports = []
        try:
            connections = psutil.net_connections(kind='inet')
            listening = [c for c in connections if c.status == 'LISTEN']
            
            self.emit_result("activity", {"message": f"🌐 Analisando {len(listening)} portas em escuta\n"})

            for conn in listening:
                self.check_abort()
                port = conn.laddr.port
                addr = conn.laddr.ip

                try:
                    proc = psutil.Process(conn.pid) if conn.pid else None
                    proc_name = proc.name() if proc else "N/A"
                except Exception:
                    proc_name = "N/A"

                open_ports.append({
                    "port": port, "address": addr,
                    "pid": conn.pid, "process": proc_name
                })

                self.emit_result("activity", {"message": f"🌐 Porta {port} → {proc_name}"})

                if port in dangerous_ports:
                    service, severity = dangerous_ports[port]
                    self.add_vulnerability({
                        "title": f"Porta {port} ({service}) aberta",
                        "detail": f"Serviço {service} na porta {port} ({addr}) - PID: {conn.pid}",
                        "severity": severity,
                        "category": "network",
                        "fix": f"Feche a porta {port} se não estiver em uso"
                    })

        except ScanAbortedException:
            raise
        except Exception as e:
            self.add_warning({
                "title": "Verificação de portas parcial",
                "detail": f"Erro: {str(e)}",
                "category": "network"
            })

        self.results["system_info"]["open_ports"] = len(open_ports)
        self.results["system_info"]["open_ports_list"] = open_ports[:50]

    def check_dangerous_services(self):
        dangerous = {
            "RemoteRegistry": "Registro Remoto",
            "TermService": "Área de Trabalho Remota",
            "TlntSvr": "Servidor Telnet",
            "SNMP": "SNMP",
            "SSDPSRV": "Descoberta SSDP",
            "upnphost": "Host UPnP",
            "W3SVC": "IIS Web Server",
            "FTPSVC": "FTP Server",
            "SMTPSVC": "SMTP Server",
        }

        for svc_name, description in dangerous.items():
            self.check_abort()
            self.emit_result("activity", {"message": f"⚙️ Verificando serviço: {description}"})
            output = self.run_command(f'sc query {svc_name}')
            if "RUNNING" in output:
                self.add_warning({
                    "title": f"Serviço Ativo: {description}",
                    "detail": f"Serviço '{svc_name}' em execução.",
                    "category": "services"
                })

    def check_network_shares(self):
        """Verifica compartilhamentos e mostra cada item em tempo real."""

        self.log("   🔎 Consultando compartilhamentos do Windows\n")
        self.emit_result("activity", {
            "message": "📂 Consultando compartilhamentos de rede\n"
        })

        output = self.run_command("net share")

        self.check_abort()

        if not output:
            self.log("   ⚠️ Nenhum resultado recebido do comando NET SHARE.")
            self.emit_result("activity", {
                "message": "⚠️ Não foi possível obter a lista de compartilhamentos."
            })
            return

        self.log("   📋 Analisando compartilhamentos encontrados\n")

        shares = []
        administrative = []

        for line in output.splitlines():

            # Permite STOP durante a análise
            self.check_abort()

            line = line.strip()

            if not line:
                continue

            if "----" in line:
                continue

            lower = line.lower()

            if "share name" in lower:
                continue

            if "nome do compartilhamento" in lower:
                continue

            if "resource" in lower:
                continue

            if "recurso" in lower:
                continue

            if "remark" in lower:
                continue

            if "comentário" in lower:
                continue

            if "command completed" in lower:
                continue

            if "comando foi concluído" in lower:
                continue

            parts = line.split()

            if not parts:
                continue

            share_name = parts[0]

            # Ignorar textos que não sejam compartilhamentos
            if share_name.lower() in [
                "server",
                "servidor",
                "share",
                "nome",
                "the",
                "o"
            ]:
                continue

            # MOSTRAR IMEDIATAMENTE NA TELA
            if share_name.endswith("$"):

                administrative.append(share_name)

                message = (
                    f"📂 Compartilhamento administrativo encontrado: "
                    f"{share_name}"
                )

                self.log(f"   🔵 {message}")

                self.emit_result("activity", {
                    "message": message
                })

            else:

                shares.append(share_name)

                message = (
                    f"📂 Compartilhamento de rede encontrado: "
                    f"{share_name}"
                )

                self.log(f"   🟡 {message}")

                self.emit_result("activity", {
                    "message": message
                })

        # Salvar também no resultado
        self.results["system_info"]["network_shares"] = shares
        self.results["system_info"]["administrative_shares"] = administrative

        # Compartilhamentos normais
        if shares:

            for share in shares:

                self.check_abort()

                self.add_warning({
                    "title": f"Compartilhamento de Rede: {share}",
                    "detail": (
                        f"O compartilhamento '{share}' está disponível "
                        f"na rede. Verifique usuários e permissões."
                    ),
                    "category": "network"
                })

        else:

            self.add_info({
                "title": "Nenhum compartilhamento comum detectado ✅",
                "detail": (
                    "Não foram encontrados compartilhamentos "
                    "não administrativos."
                ),
                "category": "network"
            })

        # Mostrar resumo imediatamente
        self.log(
            f"   ✅ Compartilhamentos analisados: "
            f"{len(shares)} comuns / "
            f"{len(administrative)} administrativos"
        )

        self.emit_result("activity", {
            "message": (
                f"✅ Compartilhamentos finalizados: "
                f"{len(shares)} comuns / "
                f"{len(administrative)} administrativos"
            )
        })

    def check_password_policy(self):
        self.emit_result("activity", {"message": "🔑 Consultando política de senhas (net accounts)\n"})
        output = self.run_command("net accounts")
        if output:
            min_pwd_len = 0
            lockout = 0

            for line in output.split('\n'):
                self.check_abort()
                if "Minimum password length" in line or "Tamanho mínimo da senha" in line:
                    nums = re.findall(r'\d+', line)
                    if nums:
                        min_pwd_len = int(nums[0])
                elif "Lockout threshold" in line or "Limite de bloqueio" in line:
                    nums = re.findall(r'\d+', line)
                    if nums:
                        lockout = int(nums[0])

            self.emit_result("activity", {"message": f"🔑 Tamanho mínimo: {min_pwd_len} | Lockout: {lockout}"})

            if min_pwd_len < 8:
                self.add_vulnerability({
                    "title": f"Senha mínima muito curta ({min_pwd_len} caracteres)",
                    "detail": "Política permite senhas menores que 8 caracteres.",
                    "severity": "alta",
                    "category": "passwords",
                    "fix": "Execute: net accounts /minpwlen:8"
                })
            else:
                self.add_info({
                    "title": f"Tamanho mínimo de senha: {min_pwd_len} ✅",
                    "detail": "Política de senha adequada",
                    "category": "passwords"
                })

            if lockout == 0:
                self.add_vulnerability({
                    "title": "Sem limite de tentativas de login",
                    "detail": "Vulnerável a força bruta.",
                    "severity": "media",
                    "category": "passwords",
                    "fix": "Execute: net accounts /lockoutthreshold:5"
                })

    def check_rdp(self):
        if platform.system() != "Windows":
            return

        self.emit_result("activity", {"message": "🖥️ Lendo registro do Remote Desktop\n"})
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Terminal Server"
            )
            deny_connections, _ = winreg.QueryValueEx(key, "fDenyTSConnections")
            winreg.CloseKey(key)

            if deny_connections == 0:
                self.add_vulnerability({
                    "title": "Remote Desktop (RDP) Habilitado",
                    "detail": "Acesso remoto via RDP está habilitado.",
                    "severity": "media",
                    "category": "remote_access",
                    "fix": "Desative em Configurações > Sistema > Área de Trabalho Remota"
                })
            else:
                self.add_info({
                    "title": "RDP Desabilitado ✅",
                    "detail": "O Remote Desktop está desativado",
                    "category": "remote_access"
                })
        except Exception:
            pass

    def check_smbv1(self):
        self.emit_result("activity", {"message": "📡 Consultando configuração SMB\n"})
        output = self.run_command(
            'powershell -Command "Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol | ConvertTo-Json"'
        )
        if output:
            try:
                data = json.loads(output)
                if data.get("EnableSMB1Protocol", False):
                    self.add_vulnerability({
                        "title": "SMBv1 Habilitado (Vulnerável a WannaCry!)",
                        "detail": "Protocolo SMBv1 está ativo.",
                        "severity": "critica",
                        "category": "network",
                        "fix": "Execute: Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol"
                    })
                else:
                    self.add_info({
                        "title": "SMBv1 Desabilitado ✅",
                        "detail": "Protegido contra WannaCry/EternalBlue",
                        "category": "network"
                    })
            except Exception:
                pass

    def check_user_accounts(self):
        self.emit_result("activity", {"message": "👤 Listando contas de usuário\n"})
        output = self.run_command("net user")
        if output:
            lines = output.split('\n')
            users = []
            for line in lines:
                self.check_abort()
                if line.strip() and '---' not in line and 'command' not in line.lower() \
                        and 'User accounts' not in line and 'Contas de' not in line \
                        and '\\\\' not in line and 'concluído' not in line.lower() \
                        and 'completed' not in line.lower():
                    users.extend(line.split())

            self.results["system_info"]["user_accounts"] = users
            
            for user in users[:20]:
                self.emit_result("activity", {"message": f"👤 Usuário encontrado: {user}"})

            for user in ["Guest", "Convidado"]:
                self.check_abort()
                self.emit_result("activity", {"message": f"👤 Verificando conta: {user}"})
                user_info = self.run_command(f"net user {user}")
                if "active" in user_info.lower() or "ativa" in user_info.lower():
                    if "Yes" in user_info or "Sim" in user_info:
                        self.add_vulnerability({
                            "title": "Conta Convidado (Guest) Ativa",
                            "detail": "Conta de convidado está habilitada.",
                            "severity": "media",
                            "category": "accounts",
                            "fix": f"Execute: net user {user} /active:no"
                        })

            for admin in ["Administrator", "Administrador"]:
                self.check_abort()
                self.emit_result("activity", {"message": f"👤 Verificando conta admin: {admin}"})
                admin_info = self.run_command(f"net user {admin}")
                if "password required" in admin_info.lower() or "senha necessária" in admin_info.lower():
                    if "No" in admin_info or "Não" in admin_info:
                        self.add_vulnerability({
                            "title": "Conta Admin sem senha obrigatória",
                            "detail": "Conta de administrador não exige senha.",
                            "severity": "critica",
                            "category": "accounts",
                            "fix": "Defina uma senha forte para o administrador"
                        })

    def check_autorun(self):
        self.emit_result("activity", {"message": "▶️ Lendo registro AutoRun\n"})
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            )
            no_autorun, _ = winreg.QueryValueEx(key, "NoDriveTypeAutoRun")
            winreg.CloseKey(key)

            if no_autorun == 255:
                self.add_info({
                    "title": "AutoRun Desabilitado ✅",
                    "detail": "AutoRun desativado para todos os drives",
                    "category": "autorun"
                })
            else:
                self.add_warning({
                    "title": "AutoRun pode estar habilitado",
                    "detail": f"Valor: {no_autorun}. Recomendado: 255",
                    "category": "autorun"
                })
        except Exception:
            self.add_warning({
                "title": "AutoRun - Não configurado",
                "detail": "Não foi possível verificar",
                "category": "autorun"
            })

    def check_installed_programs(self):
        self.emit_result("activity", {"message": "📦 Enumerando programas instalados (pode demorar)\n"})
        output = self.run_command(
            'powershell -Command "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\'
            'CurrentVersion\\Uninstall\\* | Select-Object DisplayName, DisplayVersion, Publisher | '
            'ConvertTo-Json"'
        )
        programs = []
        if output:
            try:
                data = json.loads(output)
                if not isinstance(data, list):
                    data = [data]
                for prog in data:
                    self.check_abort()
                    name = prog.get("DisplayName", "")
                    if name:
                        programs.append({
                            "name": name,
                            "version": prog.get("DisplayVersion", "N/A"),
                            "publisher": prog.get("Publisher", "N/A")
                        })
            except Exception:
                pass

        self.emit_result("activity", {"message": f"📦 {len(programs)} programas encontrados. Analisando\n"})
        self.results["system_info"]["installed_programs_count"] = len(programs)

        risky_software = ["Java", "Flash", "Adobe Reader", "Silverlight", "QuickTime"]
        for prog in programs:
            self.check_abort()
            for risky in risky_software:
                if risky.lower() in prog["name"].lower():
                    self.emit_result("activity", {"message": f"📦 ⚠️ Software visado: {prog['name']}"})
                    self.add_warning({
                        "title": f"Software visado: {prog['name']}",
                        "detail": f"Versão: {prog['version']}. Mantenha atualizado.",
                        "category": "software"
                    })
                    break

    def check_disk_space(self):
        disks = []
        for part in psutil.disk_partitions():
            self.check_abort()
            try:
                self.emit_result("activity", {"message": f"💾 Analisando disco: {part.device}"})
                usage = psutil.disk_usage(part.mountpoint)
                disk_info = {
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "used_pct": usage.percent
                }
                disks.append(disk_info)

                self.emit_result("activity", {
                    "message": f"💾 {part.device} → {disk_info['free_gb']} GB livres ({usage.percent}% uso)"
                })

                if usage.percent > 95:
                    self.add_vulnerability({
                        "title": f"Disco {part.device} quase cheio ({usage.percent}%)",
                        "detail": f"Apenas {disk_info['free_gb']} GB livres.",
                        "severity": "media",
                        "category": "disk",
                        "fix": "Libere espaço removendo arquivos temporários"
                    })
                elif usage.percent > 85:
                    self.add_warning({
                        "title": f"Disco {part.device} com pouco espaço ({usage.percent}%)",
                        "detail": f"Restam {disk_info['free_gb']} GB livres",
                        "category": "disk"
                    })
            except Exception:
                continue

        self.results["system_info"]["disks"] = disks

    def check_suspicious_processes(self):
        suspicious_names = [
            "mimikatz", "pwdump", "procdump", "lazagne", "keylogger",
            "ratclient", "darkcomet", "njrat", "netcat", "nc.exe",
            "meterpreter", "cobalt", "beacon"
        ]

        self.emit_result("activity", {"message": "🔍 Enumerando processos ativos\n"})
        proc_count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            self.check_abort()
            try:
                pinfo = proc.info
                name = pinfo['name'].lower() if pinfo['name'] else ""
                proc_count += 1

                if proc_count % 50 == 0:
                    self.emit_result("activity", {"message": f"🔍 {proc_count} processos verificados\n"})

                for sus in suspicious_names:
                    if sus in name:
                        self.emit_result("activity", {"message": f"🔍 ⚠️ SUSPEITO: {pinfo['name']}"})
                        self.add_vulnerability({
                            "title": f"Processo Suspeito: {pinfo['name']}",
                            "detail": f"PID: {pinfo['pid']}",
                            "severity": "critica",
                            "category": "processes",
                            "fix": f"taskkill /PID {pinfo['pid']} /F"
                        })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        self.emit_result("activity", {"message": f"🔍 Total: {proc_count} processos analisados"})

        try:
            self.results["system_info"]["total_processes"] = len(list(psutil.process_iter()))
        except Exception:
            self.results["system_info"]["total_processes"] = 0

    def check_dns_config(self):
        self.emit_result("activity", {"message": "🌍 Obtendo configuração de rede (ipconfig)\n"})
        output = self.run_command("ipconfig /all")
        if output:
            dns_servers = re.findall(r'DNS Servers?[.\s]*:\s*([\d.]+)', output, re.IGNORECASE)
            if not dns_servers:
                dns_servers = re.findall(r'Servidores DNS[.\s]*:\s*([\d.]+)', output, re.IGNORECASE)

            if dns_servers:
                self.results["system_info"]["dns_servers"] = dns_servers
                for dns in dns_servers:
                    self.check_abort()
                    self.emit_result("activity", {"message": f"🌍 DNS encontrado: {dns}"})
                    if dns.startswith("192.168.") or dns.startswith("10.") or dns.startswith("172."):
                        self.add_info({
                            "title": f"DNS Local: {dns}",
                            "detail": "DNS configurado para servidor local",
                            "category": "network"
                        })

    def check_secure_boot(self):
        self.emit_result("activity", {"message": "🔒 Verificando Secure Boot (UEFI)\n"})
        output = self.run_command(
            'powershell -Command "try { Confirm-SecureBootUEFI } catch { Write-Output \'Error\' }"'
        )
        if "True" in output:
            self.add_info({
                "title": "Secure Boot Ativo ✅",
                "detail": "Secure Boot habilitado no UEFI",
                "category": "boot"
            })
        elif "False" in output:
            self.add_warning({
                "title": "Secure Boot Desativado",
                "detail": "Secure Boot desligado no BIOS/UEFI",
                "category": "boot"
            })

        self.emit_result("activity", {"message": "🔒 Verificando BitLocker no disco C:\n"})
        output = self.run_command("manage-bde -status C:")
        if output:
            if "Protection On" in output or "Proteção Ativada" in output:
                self.add_info({
                    "title": "BitLocker Ativo ✅",
                    "detail": "Disco C: criptografado",
                    "category": "encryption"
                })
            elif "Protection Off" in output or "Proteção Desativada" in output:
                self.add_warning({
                    "title": "BitLocker Desativado",
                    "detail": "Disco C: sem criptografia",
                    "category": "encryption"
                })

    def check_powershell_policy(self):
        self.emit_result("activity", {"message": "⚡ Consultando política PowerShell\n"})
        output = self.run_command("powershell -Command Get-ExecutionPolicy")
        if output:
            policy = output.strip()
            self.emit_result("activity", {"message": f"⚡ Política atual: {policy}"})
            if policy == "Unrestricted":
                self.add_vulnerability({
                    "title": "PowerShell - Política Irrestrita",
                    "detail": "Qualquer script pode ser executado.",
                    "severity": "alta",
                    "category": "powershell",
                    "fix": "Set-ExecutionPolicy RemoteSigned -Scope LocalMachine"
                })
            elif policy == "Bypass":
                self.add_vulnerability({
                    "title": "PowerShell - Política Bypass",
                    "detail": "Sem nenhuma restrição.",
                    "severity": "alta",
                    "category": "powershell",
                    "fix": "Set-ExecutionPolicy RemoteSigned -Scope LocalMachine"
                })
            elif policy in ["RemoteSigned", "AllSigned", "Restricted"]:
                self.add_info({
                    "title": f"PowerShell - Política: {policy} ✅",
                    "detail": "Política adequada",
                    "category": "powershell"
                })

    def calculate_scores(self):
        """Calcula scores com base em dados parciais ou completos."""
        self.emit_result("activity", {"message": "📊 Calculando score final de segurança\n"})
        categories = {}

        for vuln in self.results.get("vulnerabilities", []):
            cat = vuln.get("category", "other")
            if cat not in categories:
                categories[cat] = {"vulns": 0, "warnings": 0, "info": 0}
            severity = vuln.get("severity", "media")
            if severity == "critica":
                categories[cat]["vulns"] += 3
            elif severity == "alta":
                categories[cat]["vulns"] += 2
            else:
                categories[cat]["vulns"] += 1

        for warn in self.results.get("warnings", []):
            cat = warn.get("category", "other")
            if cat not in categories:
                categories[cat] = {"vulns": 0, "warnings": 0, "info": 0}
            categories[cat]["warnings"] += 1

        for info in self.results.get("info", []):
            cat = info.get("category", "other")
            if cat not in categories:
                categories[cat] = {"vulns": 0, "warnings": 0, "info": 0}
            categories[cat]["info"] += 1

        critical_count = sum(1 for v in self.results.get("vulnerabilities", []) if v.get("severity") == "critica")
        high_count = sum(1 for v in self.results.get("vulnerabilities", []) if v.get("severity") == "alta")
        medium_count = sum(1 for v in self.results.get("vulnerabilities", []) if v.get("severity") == "media")

        score = 100
        score -= critical_count * 15
        score -= high_count * 10
        score -= medium_count * 5
        score -= len(self.results.get("warnings", [])) * 2
        score = max(0, min(100, score))

        self.results["scores"] = {
            "overall": score,
            "categories": categories,
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "total_vulns": len(self.results.get("vulnerabilities", [])),
            "total_warnings": len(self.results.get("warnings", [])),
            "total_info": len(self.results.get("info", []))
        }

        self.emit_result("scores_updated", self.results["scores"])


# ══════════════════════════════════════════════════════════════
# GERADOR DE RELATÓRIO HTML
# ══════════════════════════════════════════════════════════════

class HTMLReportGenerator:
    """Gera relatório HTML salvando dados parciais ou completos."""

    @staticmethod
    def generate(results, filepath):
        if not results:
            results = {}
        
        score = results.get("scores", {}).get("overall", 100)
        sinfo = results.get("system_info", {}) or {}
        vulns = results.get("vulnerabilities", []) or []
        warnings = results.get("warnings", []) or []
        infos = results.get("info", []) or []
        scores = results.get("scores", {}) or {}
        is_interrupted = results.get("interrupted", False)
        scan_date = results.get("scan_date", datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        scan_duration = results.get("scan_duration", 0)

        if score >= 80:
            score_color = "#27ae60"; score_label = "BOM"; score_emoji = "🟢"
        elif score >= 60:
            score_color = "#f39c12"; score_label = "MODERADO"; score_emoji = "🟡"
        elif score >= 40:
            score_color = "#e67e22"; score_label = "PREOCUPANTE"; score_emoji = "🟠"
        else:
            score_color = "#e74c3c"; score_label = "CRÍTICO"; score_emoji = "🔴"

        vuln_rows = ""
        for v in vulns:
            sev = v.get("severity", "media")
            sev_colors = {"critica": "#e74c3c", "alta": "#e67e22", "media": "#f39c12"}
            sev_labels = {"critica": "CRÍTICA", "alta": "ALTA", "media": "MÉDIA"}
            color = sev_colors.get(sev, "#f39c12")
            label = sev_labels.get(sev, "MÉDIA")
            fix = v.get("fix", "N/A")
            vuln_rows += f"""
            <tr>
                <td><span class="badge" style="background:{color}">{label}</span></td>
                <td><strong>{v.get('title','')}</strong></td>
                <td>{v.get('detail','')}</td>
                <td class="fix-cell">{fix}</td>
            </tr>"""

        warn_rows = ""
        for w in warnings:
            warn_rows += f"""<tr><td><strong>{w.get('title','')}</strong></td><td>{w.get('detail','')}</td></tr>"""

        info_rows = ""
        for i in infos:
            info_rows += f"""<tr><td><strong>{i.get('title','')}</strong></td><td>{i.get('detail','')}</td></tr>"""

        ports_rows = ""
        for p in sinfo.get("open_ports_list", []) or []:
            ports_rows += f"""<tr><td>{p.get('port','')}</td><td>{p.get('address','')}</td><td>{p.get('process','')}</td><td>{p.get('pid','')}</td></tr>"""

        disk_rows = ""
        for d in sinfo.get("disks", []) or []:
            used_pct = d.get('used_pct', 0)
            used_color = "#e74c3c" if used_pct > 90 else "#f39c12" if used_pct > 70 else "#27ae60"
            disk_rows += f"""
            <tr>
                <td>{d.get('device','')}</td>
                <td>{d.get('total_gb','')} GB</td>
                <td>{d.get('free_gb','')} GB</td>
                <td>
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width:{used_pct}%; background:{used_color}">
                            {used_pct}%
                        </div>
                    </div>
                </td>
            </tr>"""

        cat_names = list(scores.get("categories", {}).keys())
        cat_vulns = [scores.get("categories", {}).get(c, {}).get("vulns", 0) for c in cat_names]
        cat_warns = [scores.get("categories", {}).get(c, {}).get("warnings", 0) for c in cat_names]
        cat_infos = [scores.get("categories", {}).get(c, {}).get("info", 0) for c in cat_names]

        interrupted_banner = """
        <div style="background: rgba(231,76,60,0.25); border: 2px dashed #e74c3c; border-radius: 12px; padding: 18px; margin-bottom: 25px; text-align: center;">
            <h2 style="color: #ff6b6b; margin-bottom: 6px;">⏹️ RELATÓRIO PARCIAL (SCAN INTERROMPIDO)</h2>
            <p style="color: #eee; font-size: 1.05em;">O scan foi interrompido manualmente. Este relatório contém todos os dados registrados até o instante da parada.</p>
        </div>
        """ if is_interrupted else ""

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>🔒 Relatório - {sinfo.get('hostname', 'PC')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Segoe UI',sans-serif; background:linear-gradient(135deg,#0c0c1d,#1a1a3e,#0c0c1d); color:#e0e0e0; min-height:100vh; }}
        .container {{ max-width:1400px; margin:0 auto; padding:20px; }}
        .header {{ background:linear-gradient(135deg,#1e1e3f,#2d2d5e); border-radius:20px; padding:35px; text-align:center; margin-bottom:25px; border:1px solid rgba(255,255,255,0.1); }}
        .header h1 {{ font-size:2.3em; color:#fff; margin-bottom:10px; }}
        .header .subtitle {{ color:#8888cc; }}
        .score-section {{ display:flex; justify-content:center; gap:25px; margin-bottom:25px; flex-wrap:wrap; }}
        .score-card {{ background:linear-gradient(135deg,#1e1e3f,#2d2d5e); border-radius:20px; padding:25px; text-align:center; min-width:190px; }}
        .score-circle {{ width:140px; height:140px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 12px; font-size:2.8em; font-weight:bold; color:white; border:6px solid {score_color}; box-shadow:0 0 30px {score_color}40; }}
        .score-label {{ font-size:1.2em; font-weight:bold; color:{score_color}; }}
        .stats-card {{ display:flex; flex-direction:column; gap:12px; }}
        .stat-item {{ display:flex; align-items:center; gap:12px; font-size:1.1em; }}
        .stat-number {{ font-size:1.8em; font-weight:bold; min-width:45px; text-align:right; }}
        .card {{ background:linear-gradient(135deg,#1e1e3f,#252550); border-radius:15px; padding:22px; margin-bottom:22px; }}
        .card h2 {{ color:#7b7bff; margin-bottom:15px; font-size:1.4em; border-bottom:2px solid rgba(123,123,255,0.3); padding-bottom:8px; }}
        .info-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:12px; }}
        .info-item {{ background:rgba(255,255,255,0.05); padding:12px; border-radius:10px; border-left:4px solid #7b7bff; }}
        .info-item .label {{ color:#8888cc; font-size:0.8em; text-transform:uppercase; }}
        .info-item .value {{ color:#fff; font-size:1.1em; margin-top:4px; }}
        table {{ width:100%; border-collapse:collapse; }}
        th {{ background:rgba(123,123,255,0.2); color:#9999ff; padding:10px; text-align:left; text-transform:uppercase; font-size:0.85em; }}
        td {{ padding:10px; border-bottom:1px solid rgba(255,255,255,0.05); }}
        .badge {{ display:inline-block; padding:4px 10px; border-radius:20px; font-size:0.75em; font-weight:bold; color:white; }}
        .fix-cell {{ color:#7bff7b; font-family:'Consolas',monospace; font-size:0.9em; }}
        .progress-bar-container {{ background:rgba(255,255,255,0.1); border-radius:10px; height:22px; overflow:hidden; }}
        .progress-bar-fill {{ height:100%; display:flex; align-items:center; justify-content:center; color:white; font-weight:bold; font-size:0.8em; }}
        .charts-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(350px,1fr)); gap:20px; margin-bottom:20px; }}
        .chart-container {{ background:linear-gradient(135deg,#1e1e3f,#252550); border-radius:15px; padding:20px; }}
        .chart-container h3 {{ color:#7b7bff; margin-bottom:12px; text-align:center; }}
        .footer {{ text-align:center; padding:25px; color:#666; font-size:0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Relatório de Vulnerabilidades</h1>
            <p class="subtitle">Scan em {scan_date} | Duração: {scan_duration}s | Host: {sinfo.get('hostname', 'N/A')}</p>
        </div>

        {interrupted_banner}

        <div class="score-section">
            <div class="score-card">
                <div class="score-circle">{score}</div>
                <div class="score-label">{score_emoji} {score_label}</div>
                <p style="color:#888; margin-top:8px;">Score Parcial/Final</p>
            </div>
            <div class="score-card stats-card">
                <div class="stat-item"><span class="stat-number" style="color:#e74c3c">{scores.get('critical_count',0)}</span><span>Críticas</span></div>
                <div class="stat-item"><span class="stat-number" style="color:#e67e22">{scores.get('high_count',0)}</span><span>Altas</span></div>
                <div class="stat-item"><span class="stat-number" style="color:#f39c12">{scores.get('medium_count',0)}</span><span>Médias</span></div>
                <div class="stat-item"><span class="stat-number" style="color:#f1c40f">{scores.get('total_warnings',0)}</span><span>Avisos</span></div>
                <div class="stat-item"><span class="stat-number" style="color:#27ae60">{scores.get('total_info',0)}</span><span>OK</span></div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-container"><h3>📊 Severidade</h3><canvas id="severityChart"></canvas></div>
            <div class="chart-container"><h3>📈 Categorias</h3><canvas id="categoryChart"></canvas></div>
        </div>

        <div class="card">
            <h2>📋 Informações do Sistema</h2>
            <div class="info-grid">
                <div class="info-item"><div class="label">Hostname</div><div class="value">{sinfo.get('hostname','N/A')}</div></div>
                <div class="info-item"><div class="label">OS</div><div class="value">{sinfo.get('os','N/A')}</div></div>
                <div class="info-item"><div class="label">CPU</div><div class="value">{sinfo.get('cpu_count','N/A')} cores / {sinfo.get('cpu_usage','N/A')}%</div></div>
                <div class="info-item"><div class="label">RAM</div><div class="value">{sinfo.get('ram_total','N/A')} / {sinfo.get('ram_used_pct','N/A')}%</div></div>
                <div class="info-item"><div class="label">IP</div><div class="value">{sinfo.get('ip_address','N/A')}</div></div>
                <div class="info-item"><div class="label">MAC</div><div class="value">{sinfo.get('mac_address','N/A')}</div></div>
                <div class="info-item"><div class="label">Usuário</div><div class="value">{sinfo.get('username','N/A')} / Admin: {'Sim' if sinfo.get('is_admin') else 'Não'}</div></div>
                <div class="info-item"><div class="label">Portas Abertas</div><div class="value">{sinfo.get('open_ports','N/A')}</div></div>
            </div>
        </div>

        {'<div class="card"><h2>💾 Discos</h2><table><thead><tr><th>Drive</th><th>Total</th><th>Livre</th><th>Uso</th></tr></thead><tbody>' + disk_rows + '</tbody></table></div>' if disk_rows else ''}

        <div class="card">
            <h2>🔴 Vulnerabilidades ({len(vulns)})</h2>
            {f'<table><thead><tr><th>Severidade</th><th>Título</th><th>Detalhes</th><th>Correção</th></tr></thead><tbody>{vuln_rows}</tbody></table>' if vuln_rows else '<p>✅ Nenhuma vulnerabilidade registrada até o momento.</p>'}
        </div>

        <div class="card">
            <h2>🟡 Avisos ({len(warnings)})</h2>
            {f'<table><thead><tr><th>Título</th><th>Detalhes</th></tr></thead><tbody>{warn_rows}</tbody></table>' if warn_rows else '<p>Nenhum aviso registrado.</p>'}
        </div>

        <div class="card">
            <h2>🟢 Verificações OK ({len(infos)})</h2>
            {f'<table><thead><tr><th>Título</th><th>Detalhes</th></tr></thead><tbody>{info_rows}</tbody></table>' if info_rows else '<p>Nenhuma verificação OK registrada.</p>'}
        </div>

        {'<div class="card"><h2>🌐 Portas Abertas</h2><table><thead><tr><th>Porta</th><th>Endereço</th><th>Processo</th><th>PID</th></tr></thead><tbody>' + ports_rows + '</tbody></table></div>' if ports_rows else ''}

        <div class="footer"><p>Relatório gerado em {scan_date}</p></div>
    </div>
    <script>
        Chart.defaults.color = '#aaa';
        new Chart(document.getElementById('severityChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['Críticas','Altas','Médias','Avisos','OK'],
                datasets: [{{
                    data: [{scores.get('critical_count',0)},{scores.get('high_count',0)},{scores.get('medium_count',0)},{scores.get('total_warnings',0)},{scores.get('total_info',0)}],
                    backgroundColor: ['#e74c3c','#e67e22','#f39c12','#f1c40f','#27ae60']
                }}]
            }},
            options: {{ plugins: {{ legend: {{ position: 'bottom' }} }} }}
        }});
        new Chart(document.getElementById('categoryChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(cat_names)},
                datasets: [
                    {{ label:'Vulns', data:{json.dumps(cat_vulns)}, backgroundColor:'rgba(231,76,60,0.7)' }},
                    {{ label:'Avisos', data:{json.dumps(cat_warns)}, backgroundColor:'rgba(241,196,15,0.7)' }},
                    {{ label:'OK', data:{json.dumps(cat_infos)}, backgroundColor:'rgba(39,174,96,0.7)' }}
                ]
            }},
            options: {{ scales: {{ y: {{ beginAtZero:true }} }}, plugins: {{ legend: {{ position: 'bottom' }} }} }}
        }});
    </script>
</body>
</html>"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

        return filepath


# ══════════════════════════════════════════════════════════════
# INTERFACE GRÁFICA
# ══════════════════════════════════════════════════════════════

class ScannerGUI:
    """Interface gráfica com atividade em tempo real."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔒 Scanner de Vulnerabilidades")
        self.root.geometry("1200x820")
        self.root.minsize(1000, 700)
        self.root.configure(bg="#1a1a2e")

        try:
            if platform.system() == "Windows":
                self.root.after(100, lambda: self.root.state("zoomed"))
        except Exception:
            pass

        self.scanner = None
        self.results = None
        self.scanning = False
        self.last_report_path = None

        self.counter_vuln = 0
        self.counter_warn = 0
        self.counter_info = 0
        self.counter_critical = 0
        self.counter_high = 0
        self.counter_medium = 0

        self.setup_styles()
        self.create_widgets()
        self.center_window()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        bg = "#1a1a2e"
        fg = "#e0e0e0"
        accent = "#7b7bff"

        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=bg, foreground="#fff", font=("Segoe UI", 22, "bold"))
        style.configure("Subtitle.TLabel", background=bg, foreground="#8888cc", font=("Segoe UI", 10))
        style.configure("Status.TLabel", background=bg, foreground=accent, font=("Segoe UI", 10, "bold"))

        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background="#2d2d5e", foreground="#aaa",
                        padding=[18, 10], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#7b7bff")],
                  foreground=[("selected", "#fff")])

        style.configure("Custom.Horizontal.TProgressbar",
                        troughcolor="#2d2d5e", background=accent,
                        darkcolor=accent, lightcolor=accent,
                        bordercolor=bg, thickness=22)

    def create_widgets(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))

        ttk.Label(header_frame, text="🔒 Scanner de Vulnerabilidades",
                  style="Title.TLabel").pack()
        ttk.Label(header_frame, text="Análise em tempo real com atividade detalhada",
                  style="Subtitle.TLabel").pack()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 15))

        self.create_scanner_tab()
        self.create_realtime_tab()
        self.create_vulnerabilities_tab()
        self.create_warnings_tab()
        self.create_info_tab()
        self.create_help_tab()
        self.create_about_tab()

    def create_scanner_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  🔍 Scanner  ")

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=(12, 12), padx=15)

        self.scan_btn = tk.Button(
            btn_frame, text="🚀 Iniciar Scan",
            font=("Segoe UI", 11, "bold"),
            bg="#7b7bff", fg="white", activebackground="#5555dd",
            relief=tk.FLAT, cursor="hand2", padx=18, pady=8,
            command=self.start_scan
        )
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_btn = tk.Button(
            btn_frame, text="⏹️ STOP (Parar na Hora)",
            font=("Segoe UI", 11, "bold"),
            bg="#c0392b", fg="white", activebackground="#962d22",
            relief=tk.FLAT, cursor="hand2", padx=18, pady=8,
            command=self.stop_scan, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.report_btn = tk.Button(
            btn_frame, text="📄 Salvar Relatório HTML",
            font=("Segoe UI", 11, "bold"),
            bg="#27ae60", fg="white", activebackground="#1e8449",
            relief=tk.FLAT, cursor="hand2", padx=18, pady=8,
            command=self.save_report, state=tk.DISABLED
        )
        self.report_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.open_btn = tk.Button(
            btn_frame, text="🌐 Abrir Relatório",
            font=("Segoe UI", 11, "bold"),
            bg="#e67e22", fg="white", activebackground="#d35400",
            relief=tk.FLAT, cursor="hand2", padx=18, pady=8,
            command=self.open_report, state=tk.DISABLED
        )
        self.open_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.clear_btn = tk.Button(
            btn_frame, text="🗑️ Limpar",
            font=("Segoe UI", 11, "bold"),
            bg="#34495e", fg="white", activebackground="#2c3e50",
            relief=tk.FLAT, cursor="hand2", padx=18, pady=8,
            command=self.clear_all
        )
        self.clear_btn.pack(side=tk.LEFT)

        counters_frame = tk.Frame(tab, bg="#1a1a2e")
        counters_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        self.counter_labels = {}
        counters_info = [
            ("critical", "🔴 Críticas", "#e74c3c"),
            ("high", "🟠 Altas", "#e67e22"),
            ("medium", "🟡 Médias", "#f39c12"),
            ("warn", "⚠️ Avisos", "#f1c40f"),
            ("info", "✅ OK", "#27ae60"),
        ]

        for key, label, color in counters_info:
            frame = tk.Frame(counters_frame, bg="#2d2d5e", relief=tk.FLAT)
            frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)

            tk.Label(frame, text=label, bg="#2d2d5e", fg="#aaa",
                     font=("Segoe UI", 9)).pack(pady=(6, 0))

            val_label = tk.Label(frame, text="0", bg="#2d2d5e", fg=color,
                                  font=("Segoe UI", 18, "bold"))
            val_label.pack(pady=(0, 6))

            self.counter_labels[key] = val_label

        progress_frame = ttk.Frame(tab)
        progress_frame.pack(fill=tk.X, pady=(0, 8), padx=15)

        self.progress_var = tk.DoubleVar(value=0)
        self.progressbar = ttk.Progressbar(
            progress_frame, variable=self.progress_var,
            maximum=100, style="Custom.Horizontal.TProgressbar"
        )
        self.progressbar.pack(fill=tk.X)

        self.status_label = ttk.Label(progress_frame, text="⏸️ Pronto para iniciar",
                                       style="Status.TLabel")
        self.status_label.pack(anchor=tk.W, pady=(4, 0))

        log_frame = ttk.Frame(tab)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(4, 10))

        ttk.Label(log_frame, text="📋 Log em Tempo Real:", style="TLabel").pack(anchor=tk.W, pady=(0, 4))

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD,
            bg="#0d0d1a", fg="#00ff88",
            font=("Consolas", 10),
            insertbackground="#00ff88",
            relief=tk.FLAT, borderwidth=5,
            padx=10, pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # Tags de cores - TODAS INCLUINDO ACTIVITY
        self.log_text.tag_config("vuln_critical", foreground="#ff4444", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("vuln_high", foreground="#ff8844", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("vuln_medium", foreground="#ffcc44", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("warning", foreground="#ffff44")
        self.log_text.tag_config("info", foreground="#44ff88")
        self.log_text.tag_config("header", foreground="#7b7bff", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("separator", foreground="#555")
        self.log_text.tag_config("stop", foreground="#ff4d4d", font=("Consolas", 11, "bold"))
        self.log_text.tag_config("activity", foreground="#00c8ff", font=("Consolas", 10))

    def create_realtime_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  📊 Tempo Real  ")

        info_label = ttk.Label(tab,
            text="🔴 Resultados aparecem nos cards abaixo no instante da detecção:",
            style="Status.TLabel")
        info_label.pack(pady=10)

        canvas_frame = ttk.Frame(tab)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        self.realtime_canvas = tk.Canvas(canvas_frame, bg="#1a1a2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.realtime_canvas.yview)
        self.realtime_frame = tk.Frame(self.realtime_canvas, bg="#1a1a2e")

        self.realtime_frame.bind(
            "<Configure>",
            lambda e: self.realtime_canvas.configure(scrollregion=self.realtime_canvas.bbox("all"))
        )

        self.realtime_canvas.create_window((0, 0), window=self.realtime_frame, anchor="nw",
                                            width=self.root.winfo_screenwidth() - 100)
        self.realtime_canvas.configure(yscrollcommand=scrollbar.set)

        self.realtime_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            self.realtime_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.realtime_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.placeholder_label = tk.Label(
            self.realtime_frame,
            text="\n\n🔍 Clique em '🚀 Iniciar Scan' para começar\n\n"
                 "Os resultados aparecerão aqui em tempo real!\n\n",
            bg="#1a1a2e", fg="#666",
            font=("Segoe UI", 13)
        )
        self.placeholder_label.pack(pady=50)

    def create_vulnerabilities_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  🔴 Vulnerabilidades  ")

        ttk.Label(tab, text="🔴 Vulnerabilidades Detectadas",
                  style="Title.TLabel").pack(pady=(10, 2))

        self.vuln_count_label = ttk.Label(tab, text="Total: 0",
                                            style="Status.TLabel")
        self.vuln_count_label.pack(pady=(0, 8))

        vuln_frame = ttk.Frame(tab)
        vuln_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        self.vuln_text = scrolledtext.ScrolledText(
            vuln_frame, wrap=tk.WORD,
            bg="#0d0d1a", fg="#e0e0e0",
            font=("Segoe UI", 10),
            relief=tk.FLAT, borderwidth=5,
            padx=15, pady=15
        )
        self.vuln_text.pack(fill=tk.BOTH, expand=True)

        self.vuln_text.tag_config("critica", background="#5c1a1a", foreground="#ffaaaa",
                                   font=("Segoe UI", 11, "bold"), spacing3=5)
        self.vuln_text.tag_config("alta", background="#5c3a1a", foreground="#ffcc99",
                                   font=("Segoe UI", 11, "bold"), spacing3=5)
        self.vuln_text.tag_config("media", background="#5c4a1a", foreground="#ffe699",
                                   font=("Segoe UI", 11, "bold"), spacing3=5)
        self.vuln_text.tag_config("detail", foreground="#cccccc",
                                   font=("Segoe UI", 10), spacing3=3)
        self.vuln_text.tag_config("fix", foreground="#7bff7b",
                                   font=("Consolas", 10), spacing3=10)
        self.vuln_text.tag_config("separator", foreground="#444")

        self.vuln_text.config(state=tk.DISABLED)

    def create_warnings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  🟡 Avisos  ")

        ttk.Label(tab, text="🟡 Avisos e Recomendações",
                  style="Title.TLabel").pack(pady=(10, 2))

        self.warn_count_label = ttk.Label(tab, text="Total: 0",
                                            style="Status.TLabel")
        self.warn_count_label.pack(pady=(0, 8))

        warn_frame = ttk.Frame(tab)
        warn_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        self.warn_text = scrolledtext.ScrolledText(
            warn_frame, wrap=tk.WORD,
            bg="#0d0d1a", fg="#e0e0e0",
            font=("Segoe UI", 10),
            relief=tk.FLAT, borderwidth=5,
            padx=15, pady=15
        )
        self.warn_text.pack(fill=tk.BOTH, expand=True)

        self.warn_text.tag_config("title", background="#5c5a1a", foreground="#ffff99",
                                   font=("Segoe UI", 11, "bold"), spacing3=5)
        self.warn_text.tag_config("detail", foreground="#cccccc",
                                   font=("Segoe UI", 10), spacing3=10)
        self.warn_text.tag_config("separator", foreground="#444")

        self.warn_text.config(state=tk.DISABLED)

    def create_info_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  🟢 OK  ")

        ttk.Label(tab, text="🟢 Verificações OK (Configuração Correta)",
                  style="Title.TLabel").pack(pady=(10, 2))

        self.info_count_label = ttk.Label(tab, text="Total: 0",
                                            style="Status.TLabel")
        self.info_count_label.pack(pady=(0, 8))

        info_frame = ttk.Frame(tab)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        self.info_text = scrolledtext.ScrolledText(
            info_frame, wrap=tk.WORD,
            bg="#0d0d1a", fg="#e0e0e0",
            font=("Segoe UI", 10),
            relief=tk.FLAT, borderwidth=5,
            padx=15, pady=15
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)

        self.info_text.tag_config("title", background="#1a5c3a", foreground="#99ffcc",
                                   font=("Segoe UI", 11, "bold"), spacing3=5)
        self.info_text.tag_config("detail", foreground="#cccccc",
                                   font=("Segoe UI", 10), spacing3=10)

        self.info_text.config(state=tk.DISABLED)

    def create_help_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  ❓ Ajuda  ")

        content = """
╔══════════════════════════════════════════════════════════════╗
║              📖 GUIA RÁPIDO & ATIVIDADE EM TEMPO REAL        ║
╚══════════════════════════════════════════════════════════════╝

🚀 FUNCIONALIDADES:

  1️⃣ INICIAR SCAN: Inicia a varredura completa.
  2️⃣ STOP (PARAR NA HORA): Interrompe IMEDIATAMENTE.
  3️⃣ ATIVIDADE EM TEMPO REAL (azul claro): mostra CADA coisa
     que o scanner está fazendo naquele instante.
      • 📂 Compartilhamentos: mostra cada um encontrado
      • 🌐 Portas: mostra cada porta em escuta
      • 👤 Usuários: lista cada conta enumerada
      • 💾 Discos: mostra análise de cada partição
      • 🔍 Processos: contador ao vivo (a cada 50)
  4️⃣ SALVAR RELATÓRIO: gera HTML com todos os dados.

🎨 CORES DO LOG:
  🔵 Azul claro   → Atividade (o que está fazendo agora)
  🔴 Vermelho     → Vulnerabilidade crítica
  🟠 Laranja      → Vulnerabilidade alta
  🟡 Amarelo      → Vulnerabilidade média/aviso
  🟢 Verde        → Verificação OK

⚠️ Execute como Administrador para análises profundas.
"""
        text = scrolledtext.ScrolledText(
            tab, wrap=tk.WORD, bg="#0d0d1a", fg="#00ff88",
            font=("Consolas", 11), relief=tk.FLAT, padx=15, pady=15
        )
        text.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)

    def create_about_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  ℹ️ Sobre  ")

        content = """
╔══════════════════════════════════════════════════════════════╗
║   🔒 SCANNER DE VULNERABILIDADES - v2.4 (Activity Live)      ║
╚══════════════════════════════════════════════════════════════╝

  ✨ NOVIDADES v2.4:
     ▸ Atividade em tempo real DETALHADA
     ▸ Mostra cada item detectado durante a varredura
     ▸ Compartilhamentos exibidos um a um enquanto encontra
     ▸ Contadores dinâmicos de processos e portas
     ▸ Status label sempre mostra o que está rolando

  ✨ Cancelamento instantâneo via kill de subprocessos
  ✨ 100% Somente Leitura e Seguro
  ✨ Relatórios HTML parciais ou completos
"""
        text = scrolledtext.ScrolledText(
            tab, wrap=tk.WORD, bg="#0d0d1a", fg="#c8b6ff",
            font=("Consolas", 11), relief=tk.FLAT, padx=15, pady=15
        )
        text.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)

    def center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

    def append_log(self, text, tag=None):
        self.log_text.config(state=tk.NORMAL)
        if tag:
            self.log_text.insert(tk.END, text + "\n", tag)
        else:
            self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_counters(self):
        self.counter_labels["critical"].config(text=str(self.counter_critical))
        self.counter_labels["high"].config(text=str(self.counter_high))
        self.counter_labels["medium"].config(text=str(self.counter_medium))
        self.counter_labels["warn"].config(text=str(self.counter_warn))
        self.counter_labels["info"].config(text=str(self.counter_info))

    def add_realtime_card(self, result_type, data):
        if self.placeholder_label:
            try:
                self.placeholder_label.destroy()
            except Exception:
                pass
            self.placeholder_label = None

        if result_type == "vulnerability":
            sev = data.get("severity", "media")
            colors = {
                "critica": ("#5c1a1a", "#ff6666", "🔴 CRÍTICA"),
                "alta": ("#5c3a1a", "#ff9966", "🟠 ALTA"),
                "media": ("#5c4a1a", "#ffcc66", "🟡 MÉDIA"),
            }
            bg_color, fg_color, label = colors.get(sev, colors["media"])
        elif result_type == "warning":
            bg_color = "#5c5a1a"
            fg_color = "#ffff99"
            label = "⚠️ AVISO"
        else:
            bg_color = "#1a5c3a"
            fg_color = "#99ffcc"
            label = "✅ OK"

        card = tk.Frame(self.realtime_frame, bg=bg_color, relief=tk.FLAT, bd=2)
        card.pack(fill=tk.X, padx=10, pady=4)

        header = tk.Frame(card, bg=bg_color)
        header.pack(fill=tk.X, padx=12, pady=(8, 3))

        tk.Label(header, text=label, bg=bg_color, fg=fg_color,
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

        tk.Label(card, text=data.get("title", ""),
                 bg=bg_color, fg="#ffffff",
                 font=("Segoe UI", 11, "bold"),
                 anchor="w", justify=tk.LEFT,
                 wraplength=950).pack(fill=tk.X, padx=12, pady=(0, 4))

        tk.Label(card, text=data.get("detail", ""),
                 bg=bg_color, fg="#e0e0e0",
                 font=("Segoe UI", 9),
                 anchor="w", justify=tk.LEFT,
                 wraplength=950).pack(fill=tk.X, padx=12, pady=(0, 4))

        if "fix" in data:
            tk.Label(card, text=f"💡 Correção: {data['fix']}",
                     bg=bg_color, fg="#7bff7b",
                     font=("Consolas", 9),
                     anchor="w", justify=tk.LEFT,
                     wraplength=950).pack(fill=tk.X, padx=12, pady=(0, 8))
        else:
            tk.Label(card, text="", bg=bg_color).pack(pady=1)

        self.root.after(100, lambda: self.realtime_canvas.yview_moveto(1.0))

    def add_to_vuln_tab(self, data):
        self.vuln_text.config(state=tk.NORMAL)
        sev = data.get("severity", "media")
        sev_labels = {"critica": "🔴 CRÍTICA", "alta": "🟠 ALTA", "media": "🟡 MÉDIA"}
        label = sev_labels.get(sev, "🟡 MÉDIA")

        self.vuln_text.insert(tk.END, f"  {label}  {data.get('title', '')}  \n", sev)
        self.vuln_text.insert(tk.END, f"  📝 {data.get('detail', '')}\n", "detail")
        if "fix" in data:
            self.vuln_text.insert(tk.END, f"  💡 Correção: {data['fix']}\n", "fix")
        self.vuln_text.insert(tk.END, "  " + "─" * 80 + "\n\n", "separator")

        self.vuln_text.see(tk.END)
        self.vuln_text.config(state=tk.DISABLED)

        total = self.counter_critical + self.counter_high + self.counter_medium
        self.vuln_count_label.config(text=f"Total: {total} vulnerabilidades")

    def add_to_warn_tab(self, data):
        self.warn_text.config(state=tk.NORMAL)
        self.warn_text.insert(tk.END, f"  ⚠️  {data.get('title', '')}  \n", "title")
        self.warn_text.insert(tk.END, f"  📝 {data.get('detail', '')}\n", "detail")
        self.warn_text.insert(tk.END, "  " + "─" * 80 + "\n\n", "separator")

        self.warn_text.see(tk.END)
        self.warn_text.config(state=tk.DISABLED)

        self.warn_count_label.config(text=f"Total: {self.counter_warn} avisos")

    def add_to_info_tab(self, data):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, f"  ✅  {data.get('title', '')}  \n", "title")
        self.info_text.insert(tk.END, f"  📝 {data.get('detail', '')}\n\n", "detail")

        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)

        self.info_count_label.config(text=f"Total: {self.counter_info} verificações OK")

    def result_callback(self, result_type, data):
        if result_type == "vulnerability":
            sev = data.get("severity", "media")
            if sev == "critica":
                self.counter_critical += 1
                tag = "vuln_critical"
                emoji = "🔴"
            elif sev == "alta":
                self.counter_high += 1
                tag = "vuln_high"
                emoji = "🟠"
            else:
                self.counter_medium += 1
                tag = "vuln_medium"
                emoji = "🟡"

            self.root.after(0, lambda: self.append_log(
                f"   {emoji} VULN [{sev.upper()}]: {data.get('title', '')}", tag))
            self.root.after(0, lambda d=data: self.add_realtime_card("vulnerability", d))
            self.root.after(0, lambda d=data: self.add_to_vuln_tab(d))

        elif result_type == "warning":
            self.counter_warn += 1
            self.root.after(0, lambda: self.append_log(
                f"   ⚠️  AVISO: {data.get('title', '')}", "warning"))
            self.root.after(0, lambda d=data: self.add_realtime_card("warning", d))
            self.root.after(0, lambda d=data: self.add_to_warn_tab(d))

        elif result_type == "info":
            self.counter_info += 1
            self.root.after(0, lambda: self.append_log(
                f"   ✅ OK: {data.get('title', '')}", "info"))
            self.root.after(0, lambda d=data: self.add_realtime_card("info", d))
            self.root.after(0, lambda d=data: self.add_to_info_tab(d))

        elif result_type == "system_info":
            self.root.after(0, lambda d=data: self.append_log(
                f"\n   💻 Sistema: {d.get('hostname')} | {d.get('os')} | "
                f"IP: {d.get('ip_address')} | Admin: {'SIM' if d.get('is_admin') else 'NÃO'}",
                "header"))

        elif result_type == "check_start":
            step = data.get("step", 0)
            total = data.get("total", 0)
            self.root.after(0, lambda: self.status_label.config(
                text=f"🔄 [{step}/{total}] {data.get('name', '')}"))

        elif result_type == "activity":
            # NOVO: Atividade em tempo real (o que está fazendo agora)
            message = data.get("message", "")

            self.root.after(
                0,
                lambda m=message: self.append_log(
                    f"   {m}",
                    "activity"
                )
            )

            self.root.after(
                0,
                lambda m=message: self.status_label.config(
                    text=m
                )
            )

        elif result_type == "scan_stopped":
            self.results = data
            self.root.after(0, self._scan_interrupted_ui)

        self.root.after(0, self.update_counters)

    def scan_callback(self, msg):
        if msg.startswith("__PROGRESS__"):
            progress = float(msg.replace("__PROGRESS__", ""))
            self.root.after(0, lambda: self.progress_var.set(progress))
        else:
            tag = None
            if msg.startswith("\n["):
                tag = "header"
            elif "=" in msg and len(msg) > 20:
                tag = "separator"
            elif "INTERROMPIDO" in msg:
                tag = "stop"
            self.root.after(0, lambda m=msg, t=tag: self.append_log(m, t))

    def start_scan(self):
        if self.scanning:
            return

        if self.results:
            if not messagebox.askyesno("Novo Scan", "Já existe um scan gravado. Deseja limpar e reiniciar?"):
                return
            self.clear_all()

        self.notebook.select(0)

        self.scanner = VulnerabilityScanner(
            callback=self.scan_callback,
            result_callback=self.result_callback
        )
        self.results = self.scanner.results

        self.scanning = True
        self.scan_btn.config(state=tk.DISABLED, bg="#555")
        self.stop_btn.config(state=tk.NORMAL, bg="#c0392b")
        self.report_btn.config(state=tk.DISABLED)
        self.open_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)

        thread = threading.Thread(target=self._run_scan, daemon=True)
        thread.start()

    def stop_scan(self):
        if self.scanner and self.scanning:
            self.status_label.config(text="⏹️ Parando o scan na hora\n")
            self.stop_btn.config(state=tk.DISABLED, bg="#555")
            try:
                self.scanner.stop()
            except Exception as e:
                self.append_log(f"❌ Erro ao parar: {str(e)}")

    def _run_scan(self):
        try:
            results = self.scanner.run_full_scan()
            self.results = results
            if not results.get("interrupted"):
                self.root.after(0, self._scan_complete)
        except Exception as e:
            self.root.after(0, lambda: self.append_log(f"\n❌ Erro: {str(e)}"))
            self.root.after(0, self._scan_error)

    def _scan_complete(self):
        self.scanning = False
        self.scan_btn.config(state=tk.NORMAL, bg="#7b7bff")
        self.stop_btn.config(state=tk.DISABLED, bg="#c0392b")
        self.report_btn.config(state=tk.NORMAL)
        self.clear_btn.config(state=tk.NORMAL)
        self.progress_var.set(100)

        if not self.results:
            self.results = {"scores": {"overall": 0}}
        
        scores = self.results.get("scores", {}) or {}
        score = scores.get("overall", 0)

        self.status_label.config(
            text=f"✅ Scan completo! Score: {score}/100 | "
                 f"🔴 {self.counter_critical + self.counter_high + self.counter_medium} vulns | "
                 f"⚠️ {self.counter_warn} avisos"
        )

        msg = (
            f"Scan Completo! ✅\n\n"
            f"Score de Segurança: {score}/100\n\n"
            f"🔴 Críticas: {self.counter_critical}\n"
            f"🟠 Altas: {self.counter_high}\n"
            f"🟡 Médias: {self.counter_medium}\n"
            f"⚠️  Avisos: {self.counter_warn}\n"
            f"✅ OK: {self.counter_info}\n\n"
            f"Deseja salvar o relatório HTML?"
        )

        if messagebox.askyesno("Scan Completo", msg):
            self.save_report()

    def _scan_interrupted_ui(self):
        self.scanning = False
        self.scan_btn.config(state=tk.NORMAL, bg="#7b7bff")
        self.stop_btn.config(state=tk.DISABLED, bg="#c0392b")
        self.report_btn.config(state=tk.NORMAL)
        self.clear_btn.config(state=tk.NORMAL)

        if not self.results:
            self.results = {
                "scores": {"overall": 100, "critical_count": 0, "high_count": 0, 
                          "medium_count": 0, "total_warnings": 0, "total_info": 0},
                "interrupted": True,
                "scan_date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "scan_duration": 0,
                "vulnerabilities": [],
                "warnings": [],
                "info": [],
                "system_info": {}
            }
        
        if "scores" not in self.results or not self.results["scores"]:
            self.results["scores"] = {"overall": 100}
        
        scores = self.results.get("scores", {}) or {}
        score = scores.get("overall", 100)
        
        self.status_label.config(text=f"⏹️ Scan Parado! (Score parcial: {score}/100)")

        msg = (
            f"⏹️ Scan parado na hora com sucesso!\n\n"
            f"Itens coletados até a parada:\n"
            f"• Vulnerabilidades: {self.counter_critical + self.counter_high + self.counter_medium}\n"
            f"• Avisos: {self.counter_warn}\n"
            f"• Itens OK: {self.counter_info}\n"
            f"• Score Parcial: {score}/100\n\n"
            f"Deseja salvar o Relatório HTML com os dados de onde parou?"
        )
        if messagebox.askyesno("Scan Interrompido", msg):
            self.save_report()

    def _scan_error(self):
        self.scanning = False
        self.scan_btn.config(state=tk.NORMAL, bg="#7b7bff")
        self.stop_btn.config(state=tk.DISABLED, bg="#c0392b")
        self.clear_btn.config(state=tk.NORMAL)
        if self.results and (self.results.get("vulnerabilities") or self.results.get("warnings") or self.results.get("info")):
            self.report_btn.config(state=tk.NORMAL)
        self.status_label.config(text="❌ Erro durante o scan")

    def clear_all(self):
        self.counter_vuln = 0
        self.counter_warn = 0
        self.counter_info = 0
        self.counter_critical = 0
        self.counter_high = 0
        self.counter_medium = 0
        self.update_counters()

        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        self.vuln_text.config(state=tk.NORMAL)
        self.vuln_text.delete(1.0, tk.END)
        self.vuln_text.config(state=tk.DISABLED)
        self.vuln_count_label.config(text="Total: 0")

        self.warn_text.config(state=tk.NORMAL)
        self.warn_text.delete(1.0, tk.END)
        self.warn_text.config(state=tk.DISABLED)
        self.warn_count_label.config(text="Total: 0")

        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state=tk.DISABLED)
        self.info_count_label.config(text="Total: 0")

        for widget in self.realtime_frame.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

        self.placeholder_label = tk.Label(
            self.realtime_frame,
            text="\n\n🔍 Clique em '🚀 Iniciar Scan' para começar\n\n"
                 "Os resultados aparecerão aqui em tempo real!\n\n",
            bg="#1a1a2e", fg="#666",
            font=("Segoe UI", 13)
        )
        self.placeholder_label.pack(pady=50)

        self.progress_var.set(0)
        self.status_label.config(text="⏸️ Pronto para iniciar")
        self.report_btn.config(state=tk.DISABLED)
        self.open_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.results = None
        self.scanner = None
        self.last_report_path = None

    def save_report(self):
        if not self.results:
            messagebox.showwarning("Aviso", "Execute ou inicie o scan primeiro!")
            return

        is_partial = self.results.get("interrupted", False)
        prefix = "vulnerabilidades_parcial" if is_partial else "vulnerabilidades"
        default_name = f"{prefix}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        filepath = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=default_name,
            title="Salvar Relatório HTML (Parcial ou Completo)"
        )

        if filepath:
            try:
                HTMLReportGenerator.generate(self.results, filepath)
                self.last_report_path = filepath
                self.open_btn.config(state=tk.NORMAL)
                self.append_log(f"\n📄 Relatório salvo em: {filepath}", "header")
                messagebox.showinfo("Sucesso", f"Relatório salvo com sucesso!\n\n{filepath}")

                if messagebox.askyesno("Abrir", "Deseja abrir o relatório no navegador?"):
                    webbrowser.open(f"file://{os.path.abspath(filepath)}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")

    def open_report(self):
        if self.last_report_path and os.path.exists(self.last_report_path):
            webbrowser.open(f"file://{os.path.abspath(self.last_report_path)}")
        else:
            messagebox.showwarning("Aviso", "Nenhum relatório salvo ainda!")

    def run(self):
        self.root.mainloop()


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = ScannerGUI()
    app.run()
