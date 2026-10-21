#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
import struct
import threading
import tempfile
from datetime import datetime
from pathlib import Path
import hashlib
import webbrowser

# ═══════════════════════════════════════════════════════════════
# BASE DE CONHECIMENTO - API DO WINDOWS
# ═══════════════════════════════════════════════════════════════
API_KNOWLEDGE_BASE = {
    "CreateProcessA": {"desc": "Cria um novo processo (ANSI)", "cat": "Execução", "risk": "ALTO", "icon": "⚙️"},
    "CreateProcessW": {"desc": "Cria um novo processo (Unicode)", "cat": "Execução", "risk": "ALTO", "icon": "⚙️"},
    "ShellExecuteA": {"desc": "Executa comando/arquivo via Shell (ANSI)", "cat": "Execução", "risk": "ALTO", "icon": "🚀"},
    "ShellExecuteW": {"desc": "Executa comando/arquivo via Shell (Unicode)", "cat": "Execução", "risk": "ALTO", "icon": "🚀"},
    "ShellExecuteExA": {"desc": "Executa comando com opções avançadas", "cat": "Execução", "risk": "ALTO", "icon": "🚀"},
    "ShellExecuteExW": {"desc": "Executa comando com opções avançadas (Unicode)", "cat": "Execução", "risk": "ALTO", "icon": "🚀"},
    "WinExec": {"desc": "Executa aplicação (API antiga/legada)", "cat": "Execução", "risk": "ALTO", "icon": "⚡"},
    "system": {"desc": "Executa comando do sistema (CRT)", "cat": "Execução", "risk": "ALTO", "icon": "💻"},
    "CommandLineToArgvW": {"desc": "Converte string de linha de comando em array de argumentos", "cat": "Execução", "risk": "MÉDIO", "icon": "📝"},
    "GetCommandLineA": {"desc": "Obtém a linha de comando do processo (ANSI)", "cat": "Execução", "risk": "MÉDIO", "icon": "📋"},
    "GetCommandLineW": {"desc": "Obtém a linha de comando do processo (Unicode)", "cat": "Execução", "risk": "MÉDIO", "icon": "📋"},
    "GetAsyncKeyState": {"desc": "Verifica estado de tecla (keylogger)", "cat": "Evasão", "risk": "ALTO", "icon": "⌨️"},
    "GetKeyState": {"desc": "Obtém estado de tecla", "cat": "Evasão", "risk": "ALTO", "icon": "⌨️"},
    "RegOpenKeyA": {"desc": "Abre uma chave do registro (ANSI)", "cat": "Registro", "risk": "MÉDIO", "icon": "🔑"},
    "RegOpenKeyW": {"desc": "Abre uma chave do registro (Unicode)", "cat": "Registro", "risk": "MÉDIO", "icon": "🔑"},
    "RegOpenKeyExA": {"desc": "Abre chave do registro com opções (ANSI)", "cat": "Registro", "risk": "MÉDIO", "icon": "🔑"},
    "RegOpenKeyExW": {"desc": "Abre chave do registro com opções (Unicode)", "cat": "Registro", "risk": "MÉDIO", "icon": "🔑"},
    "RegCreateKeyA": {"desc": "Cria/abre uma chave do registro", "cat": "Registro", "risk": "ALTO", "icon": "🗝️"},
    "RegCreateKeyW": {"desc": "Cria/abre uma chave do registro (Unicode)", "cat": "Registro", "risk": "ALTO", "icon": "🗝️"},
    "RegCreateKeyExA": {"desc": "Cria chave do registro com opções", "cat": "Registro", "risk": "ALTO", "icon": "🗝️"},
    "RegCreateKeyExW": {"desc": "Cria chave do registro com opções (Unicode)", "cat": "Registro", "risk": "ALTO", "icon": "🗝️"},
    "RegSetValueA": {"desc": "Define valor em chave do registro", "cat": "Registro", "risk": "ALTO", "icon": "✏️"},
    "RegSetValueW": {"desc": "Define valor em chave do registro (Unicode)", "cat": "Registro", "risk": "ALTO", "icon": "✏️"},
    "RegSetValueExA": {"desc": "Define valor com opções no registro", "cat": "Registro", "risk": "ALTO", "icon": "✏️"},
    "RegSetValueExW": {"desc": "Define valor com opções no registro (Unicode)", "cat": "Registro", "risk": "ALTO", "icon": "✏️"},
    "RegGetValueA": {"desc": "Lê valor do registro (ANSI)", "cat": "Registro", "risk": "BAIXO", "icon": "👁️"},
    "RegGetValueW": {"desc": "Lê valor do registro (Unicode)", "cat": "Registro", "risk": "BAIXO", "icon": "👁️"},
    "RegQueryValueExA": {"desc": "Consulta valor do registro", "cat": "Registro", "risk": "BAIXO", "icon": "🔍"},
    "RegQueryValueExW": {"desc": "Consulta valor do registro (Unicode)", "cat": "Registro", "risk": "BAIXO", "icon": "🔍"},
    "RegDeleteKeyA": {"desc": "Deleta chave do registro", "cat": "Registro", "risk": "ALTO", "icon": "🗑️"},
    "RegDeleteKeyW": {"desc": "Deleta chave do registro (Unicode)", "cat": "Registro", "risk": "ALTO", "icon": "🗑️"},
    "RegDeleteValueA": {"desc": "Deleta valor do registro", "cat": "Registro", "risk": "ALTO", "icon": "🗑️"},
    "RegDeleteValueW": {"desc": "Deleta valor do registro (Unicode)", "cat": "Registro", "risk": "ALTO", "icon": "🗑️"},
    "RegCloseKey": {"desc": "Fecha handle de chave do registro", "cat": "Registro", "risk": "BAIXO", "icon": "🔒"},
    "InternetOpenA": {"desc": "Inicializa WinINet para conexões HTTP", "cat": "Rede", "risk": "ALTO", "icon": "🌐"},
    "InternetOpenW": {"desc": "Inicializa WinINet (Unicode)", "cat": "Rede", "risk": "ALTO", "icon": "🌐"},
    "InternetOpenUrlA": {"desc": "Abre uma URL (ANSI)", "cat": "Rede", "risk": "ALTO", "icon": "🔗"},
    "InternetOpenUrlW": {"desc": "Abre uma URL (Unicode)", "cat": "Rede", "risk": "ALTO", "icon": "🔗"},
    "InternetConnectA": {"desc": "Conecta a servidor HTTP/FTP", "cat": "Rede", "risk": "ALTO", "icon": "🔌"},
    "InternetConnectW": {"desc": "Conecta a servidor (Unicode)", "cat": "Rede", "risk": "ALTO", "icon": "🔌"},
    "InternetReadFile": {"desc": "Lê dados de conexão HTTP", "cat": "Rede", "risk": "ALTO", "icon": "📥"},
    "InternetWriteFile": {"desc": "Envia dados via HTTP", "cat": "Rede", "risk": "ALTO", "icon": "📤"},
    "HttpOpenRequestA": {"desc": "Cria request HTTP", "cat": "Rede", "risk": "ALTO", "icon": "📡"},
    "HttpOpenRequestW": {"desc": "Cria request HTTP (Unicode)", "cat": "Rede", "risk": "ALTO", "icon": "📡"},
    "HttpSendRequestA": {"desc": "Envia request HTTP", "cat": "Rede", "risk": "ALTO", "icon": "📨"},
    "HttpSendRequestW": {"desc": "Envia request HTTP (Unicode)", "cat": "Rede", "risk": "ALTO", "icon": "📨"},
    "URLDownloadToFileA": {"desc": "⚠️ Baixa arquivo de URL (ANSI)", "cat": "Rede", "risk": "CRÍTICO", "icon": "⬇️"},
    "URLDownloadToFileW": {"desc": "⚠️ Baixa arquivo de URL (Unicode)", "cat": "Rede", "risk": "CRÍTICO", "icon": "⬇️"},
    "WinHttpOpen": {"desc": "Inicializa WinHTTP", "cat": "Rede", "risk": "ALTO", "icon": "🌐"},
    "WinHttpConnect": {"desc": "Conecta via WinHTTP", "cat": "Rede", "risk": "ALTO", "icon": "🔌"},
    "WinHttpSendRequest": {"desc": "Envia request via WinHTTP", "cat": "Rede", "risk": "ALTO", "icon": "📨"},
    "socket": {"desc": "Cria socket de rede", "cat": "Rede", "risk": "ALTO", "icon": "🔌"},
    "connect": {"desc": "Conecta socket a endpoint", "cat": "Rede", "risk": "ALTO", "icon": "🔗"},
    "send": {"desc": "Envia dados via socket", "cat": "Rede", "risk": "ALTO", "icon": "📤"},
    "recv": {"desc": "Recebe dados via socket", "cat": "Rede", "risk": "ALTO", "icon": "📥"},
    "WSAStartup": {"desc": "Inicializa Winsock", "cat": "Rede", "risk": "MÉDIO", "icon": "🌐"},
    "CreateFileA": {"desc": "Cria/abre arquivo (ANSI)", "cat": "Arquivos", "risk": "MÉDIO", "icon": "📄"},
    "CreateFileW": {"desc": "Cria/abre arquivo (Unicode)", "cat": "Arquivos", "risk": "MÉDIO", "icon": "📄"},
    "ReadFile": {"desc": "Lê dados de arquivo", "cat": "Arquivos", "risk": "BAIXO", "icon": "📖"},
    "WriteFile": {"desc": "Escreve dados em arquivo", "cat": "Arquivos", "risk": "MÉDIO", "icon": "✍️"},
    "DeleteFileA": {"desc": "Deleta arquivo", "cat": "Arquivos", "risk": "ALTO", "icon": "🗑️"},
    "DeleteFileW": {"desc": "Deleta arquivo (Unicode)", "cat": "Arquivos", "risk": "ALTO", "icon": "🗑️"},
    "CopyFileA": {"desc": "Copia arquivo", "cat": "Arquivos", "risk": "MÉDIO", "icon": "📋"},
    "CopyFileW": {"desc": "Copia arquivo (Unicode)", "cat": "Arquivos", "risk": "MÉDIO", "icon": "📋"},
    "MoveFileA": {"desc": "Move/renomeia arquivo", "cat": "Arquivos", "risk": "MÉDIO", "icon": "➡️"},
    "MoveFileW": {"desc": "Move/renomeia arquivo (Unicode)", "cat": "Arquivos", "risk": "MÉDIO", "icon": "➡️"},
    "GetFileAttributesA": {"desc": "Obtém atributos de arquivo", "cat": "Arquivos", "risk": "BAIXO", "icon": "📊"},
    "GetFileAttributesW": {"desc": "Obtém atributos de arquivo (Unicode)", "cat": "Arquivos", "risk": "BAIXO", "icon": "📊"},
    "SetFileAttributesA": {"desc": "Define atributos de arquivo", "cat": "Arquivos", "risk": "MÉDIO", "icon": "🏷️"},
    "SetFileAttributesW": {"desc": "Define atributos de arquivo (Unicode)", "cat": "Arquivos", "risk": "MÉDIO", "icon": "🏷️"},
    "GetFullPathNameA": {"desc": "Resolve caminho completo de arquivo", "cat": "Arquivos", "risk": "BAIXO", "icon": "📁"},
    "GetFullPathNameW": {"desc": "Resolve caminho completo (Unicode)", "cat": "Arquivos", "risk": "BAIXO", "icon": "📁"},
    "FindFirstFileA": {"desc": "Inicia busca por arquivos", "cat": "Arquivos", "risk": "BAIXO", "icon": "🔎"},
    "FindFirstFileW": {"desc": "Inicia busca por arquivos (Unicode)", "cat": "Arquivos", "risk": "BAIXO", "icon": "🔎"},
    "FindNextFileA": {"desc": "Continua busca por arquivos", "cat": "Arquivos", "risk": "BAIXO", "icon": "🔎"},
    "FindNextFileW": {"desc": "Continua busca por arquivos (Unicode)", "cat": "Arquivos", "risk": "BAIXO", "icon": "🔎"},
    "SetCurrentDirectoryA": {"desc": "Altera diretório atual", "cat": "Arquivos", "risk": "BAIXO", "icon": "📂"},
    "SetCurrentDirectoryW": {"desc": "Altera diretório atual (Unicode)", "cat": "Arquivos", "risk": "BAIXO", "icon": "📂"},
    "GetCurrentDirectoryA": {"desc": "Obtém diretório atual", "cat": "Arquivos", "risk": "BAIXO", "icon": "📂"},
    "GetCurrentDirectoryW": {"desc": "Obtém diretório atual (Unicode)", "cat": "Arquivos", "risk": "BAIXO", "icon": "📂"},
    "VirtualAlloc": {"desc": "⚠️ Aloca memória (comum em injeção)", "cat": "Memória", "risk": "ALTO", "icon": "💾"},
    "VirtualAllocEx": {"desc": "🚨 Aloca memória em OUTRO processo", "cat": "Memória", "risk": "CRÍTICO", "icon": "💉"},
    "VirtualProtect": {"desc": "⚠️ Altera proteção de memória (shellcode)", "cat": "Memória", "risk": "ALTO", "icon": "🛡️"},
    "VirtualProtectEx": {"desc": "🚨 Altera proteção em outro processo", "cat": "Memória", "risk": "CRÍTICO", "icon": "🛡️"},
    "WriteProcessMemory": {"desc": "🚨 Escreve em memória de outro processo (INJEÇÃO)", "cat": "Memória", "risk": "CRÍTICO", "icon": "💉"},
    "ReadProcessMemory": {"desc": "⚠️ Lê memória de outro processo", "cat": "Memória", "risk": "ALTO", "icon": "👁️"},
    "CreateRemoteThread": {"desc": "🚨 Cria thread em processo remoto (INJEÇÃO)", "cat": "Memória", "risk": "CRÍTICO", "icon": "🧵"},
    "NtCreateThreadEx": {"desc": "🚨 Cria thread (API nativa, evasão)", "cat": "Memória", "risk": "CRÍTICO", "icon": "🧵"},
    "QueueUserAPC": {"desc": "⚠️ Enfileira APC (técnica de injeção)", "cat": "Memória", "risk": "ALTO", "icon": "📬"},
    "SetWindowsHookExA": {"desc": "⚠️ Instala hook global (keylogger)", "cat": "Memória", "risk": "ALTO", "icon": "🪝"},
    "SetWindowsHookExW": {"desc": "⚠️ Instala hook global (Unicode)", "cat": "Memória", "risk": "ALTO", "icon": "🪝"},
    "OpenProcess": {"desc": "Abre handle para outro processo", "cat": "Processos", "risk": "ALTO", "icon": "🎯"},
    "TerminateProcess": {"desc": "⚠️ Finaliza processo", "cat": "Processos", "risk": "ALTO", "icon": "💀"},
    "CreateThread": {"desc": "Cria nova thread", "cat": "Processos", "risk": "MÉDIO", "icon": "🧵"},
    "SuspendThread": {"desc": "Suspende thread", "cat": "Processos", "risk": "MÉDIO", "icon": "⏸️"},
    "ResumeThread": {"desc": "Retoma thread", "cat": "Processos", "risk": "MÉDIO", "icon": "▶️"},
    "GetThreadContext": {"desc": "⚠️ Obtém contexto de thread (hollowing)", "cat": "Processos", "risk": "ALTO", "icon": "🔍"},
    "SetThreadContext": {"desc": "🚨 Define contexto de thread (hollowing)", "cat": "Processos", "risk": "CRÍTICO", "icon": "⚙️"},
    "CreateToolhelp32Snapshot": {"desc": "Snapshot de processos/threads", "cat": "Processos", "risk": "MÉDIO", "icon": "📸"},
    "Process32FirstW": {"desc": "Enumera processos", "cat": "Processos", "risk": "MÉDIO", "icon": "📋"},
    "Process32NextW": {"desc": "Enumera processos (próximo)", "cat": "Processos", "risk": "MÉDIO", "icon": "📋"},
    "GetCurrentProcess": {"desc": "Obtém handle do processo atual", "cat": "Processos", "risk": "BAIXO", "icon": "🎯"},
    "GetCurrentProcessId": {"desc": "Obtém PID atual", "cat": "Processos", "risk": "BAIXO", "icon": "🆔"},
    "LoadLibraryA": {"desc": "⚠️ Carrega DLL dinamicamente", "cat": "DLL", "risk": "ALTO", "icon": "📚"},
    "LoadLibraryW": {"desc": "⚠️ Carrega DLL (Unicode)", "cat": "DLL", "risk": "ALTO", "icon": "📚"},
    "LoadLibraryExA": {"desc": "⚠️ Carrega DLL com flags", "cat": "DLL", "risk": "ALTO", "icon": "📚"},
    "LoadLibraryExW": {"desc": "⚠️ Carrega DLL com flags (Unicode)", "cat": "DLL", "risk": "ALTO", "icon": "📚"},
    "GetProcAddress": {"desc": "⚠️ Resolve endereço de função (API hiding)", "cat": "DLL", "risk": "ALTO", "icon": "📍"},
    "GetModuleHandleA": {"desc": "Obtém handle de módulo carregado", "cat": "DLL", "risk": "BAIXO", "icon": "📦"},
    "GetModuleHandleW": {"desc": "Obtém handle de módulo (Unicode)", "cat": "DLL", "risk": "BAIXO", "icon": "📦"},
    "GetModuleFileNameA": {"desc": "Obtém caminho do módulo", "cat": "DLL", "risk": "BAIXO", "icon": "📄"},
    "GetModuleFileNameW": {"desc": "Obtém caminho do módulo (Unicode)", "cat": "DLL", "risk": "BAIXO", "icon": "📄"},
    "FreeLibrary": {"desc": "Descarrega DLL", "cat": "DLL", "risk": "BAIXO", "icon": "🗑️"},
    "CryptAcquireContextA": {"desc": "Inicializa provider de criptografia", "cat": "Crypto", "risk": "MÉDIO", "icon": "🔐"},
    "CryptAcquireContextW": {"desc": "Inicializa provider (Unicode)", "cat": "Crypto", "risk": "MÉDIO", "icon": "🔐"},
    "CryptEncrypt": {"desc": "⚠️ Criptografa dados (ransomware?)", "cat": "Crypto", "risk": "ALTO", "icon": "🔒"},
    "CryptDecrypt": {"desc": "Descriptografa dados", "cat": "Crypto", "risk": "MÉDIO", "icon": "🔓"},
    "CryptGenKey": {"desc": "Gera chave criptográfica", "cat": "Crypto", "risk": "MÉDIO", "icon": "🗝️"},
    "CryptHashData": {"desc": "Calcula hash de dados", "cat": "Crypto", "risk": "BAIXO", "icon": "#️⃣"},
    "IsDebuggerPresent": {"desc": "🚨 Detecta debugger (anti-análise)", "cat": "Evasão", "risk": "CRÍTICO", "icon": "🕵️"},
    "CheckRemoteDebuggerPresent": {"desc": "🚨 Verifica debugger remoto", "cat": "Evasão", "risk": "CRÍTICO", "icon": "🕵️"},
    "NtQueryInformationProcess": {"desc": "⚠️ Query de info (anti-debug)", "cat": "Evasão", "risk": "ALTO", "icon": "🕵️"},
    "OutputDebugStringA": {"desc": "Detecta debugger via output", "cat": "Evasão", "risk": "MÉDIO", "icon": "🐛"},
    "GetTickCount": {"desc": "Usado para detecção de VM/sandbox", "cat": "Evasão", "risk": "BAIXO", "icon": "⏱️"},
    "Sleep": {"desc": "Delay (pode burlar sandbox)", "cat": "Evasão", "risk": "BAIXO", "icon": "😴"},
    "GetSystemInfo": {"desc": "Obtém informações do sistema", "cat": "Sistema", "risk": "BAIXO", "icon": "💻"},
    "GetComputerNameA": {"desc": "Obtém nome do computador", "cat": "Sistema", "risk": "BAIXO", "icon": "🖥️"},
    "GetComputerNameW": {"desc": "Obtém nome do computador (Unicode)", "cat": "Sistema", "risk": "BAIXO", "icon": "🖥️"},
    "GetUserNameA": {"desc": "Obtém nome do usuário", "cat": "Sistema", "risk": "BAIXO", "icon": "👤"},
    "GetUserNameW": {"desc": "Obtém nome do usuário (Unicode)", "cat": "Sistema", "risk": "BAIXO", "icon": "👤"},
    "GetVersionExA": {"desc": "Obtém versão do Windows", "cat": "Sistema", "risk": "BAIXO", "icon": "ℹ️"},
    "GetVersionExW": {"desc": "Obtém versão do Windows (Unicode)", "cat": "Sistema", "risk": "BAIXO", "icon": "ℹ️"},
    "OpenSCManagerA": {"desc": "Abre gerenciador de serviços", "cat": "Serviços", "risk": "MÉDIO", "icon": "⚙️"},
    "OpenSCManagerW": {"desc": "Abre gerenciador de serviços (Unicode)", "cat": "Serviços", "risk": "MÉDIO", "icon": "⚙️"},
    "CreateServiceA": {"desc": "⚠️ Cria serviço (persistência)", "cat": "Serviços", "risk": "ALTO", "icon": "🔧"},
    "CreateServiceW": {"desc": "⚠️ Cria serviço (persistência)", "cat": "Serviços", "risk": "ALTO", "icon": "🔧"},
    "StartServiceA": {"desc": "Inicia serviço", "cat": "Serviços", "risk": "MÉDIO", "icon": "▶️"},
    "StartServiceW": {"desc": "Inicia serviço (Unicode)", "cat": "Serviços", "risk": "MÉDIO", "icon": "▶️"},
}


# ═══════════════════════════════════════════════════════════════
# PARSER DE PE
# ═══════════════════════════════════════════════════════════════
class PEParser:
    def __init__(self, filepath):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = f.read()
        self.is_pe = False
        self.is_64bit = False
        self.imports = {}
        self.exports = []
        self.sections = []
        self.pe_info = {}

    def parse(self):
        try:
            if len(self.data) < 0x40:
                return False
            if self.data[:2] != b'MZ':
                return False

            pe_offset = struct.unpack('<I', self.data[0x3C:0x40])[0]
            if pe_offset >= len(self.data) - 4:
                return False
            if self.data[pe_offset:pe_offset+4] != b'PE\x00\x00':
                return False

            self.is_pe = True
            coff_offset = pe_offset + 4
            machine = struct.unpack('<H', self.data[coff_offset:coff_offset+2])[0]
            num_sections = struct.unpack('<H', self.data[coff_offset+2:coff_offset+4])[0]
            timestamp = struct.unpack('<I', self.data[coff_offset+4:coff_offset+8])[0]
            size_opt_header = struct.unpack('<H', self.data[coff_offset+16:coff_offset+18])[0]
            characteristics = struct.unpack('<H', self.data[coff_offset+18:coff_offset+20])[0]

            self.is_64bit = (machine == 0x8664)
            machine_type = {0x14c: "x86 (32-bit)", 0x8664: "x64 (64-bit)",
                            0x1c0: "ARM", 0xaa64: "ARM64"}.get(machine, f"Unknown (0x{machine:X})")

            opt_offset = coff_offset + 20
            if opt_offset + 2 > len(self.data):
                return False
            magic = struct.unpack('<H', self.data[opt_offset:opt_offset+2])[0]

            is_dll = bool(characteristics & 0x2000)
            is_exe = bool(characteristics & 0x0002) and not is_dll

            self.pe_info = {
                "architecture": machine_type,
                "is_64bit": self.is_64bit,
                "is_dll": is_dll,
                "is_exe": is_exe,
                "file_type": "DLL" if is_dll else ("EXE" if is_exe else "Unknown"),
                "num_sections": num_sections,
                "timestamp": datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S") if timestamp else "N/A",
                "characteristics": f"0x{characteristics:04X}"
            }

            if magic == 0x10b:
                self.pe_info["entry_point"] = f"0x{struct.unpack('<I', self.data[opt_offset+16:opt_offset+20])[0]:08X}"
                self.pe_info["image_base"] = f"0x{struct.unpack('<I', self.data[opt_offset+28:opt_offset+32])[0]:08X}"
                data_dir_offset = opt_offset + 96
            elif magic == 0x20b:
                self.pe_info["entry_point"] = f"0x{struct.unpack('<I', self.data[opt_offset+16:opt_offset+20])[0]:08X}"
                self.pe_info["image_base"] = f"0x{struct.unpack('<Q', self.data[opt_offset+24:opt_offset+32])[0]:016X}"
                data_dir_offset = opt_offset + 112
            else:
                return False

            if data_dir_offset + 128 > len(self.data):
                return False

            sections_offset = opt_offset + size_opt_header
            for i in range(num_sections):
                sec_off = sections_offset + (i * 40)
                if sec_off + 40 > len(self.data):
                    break
                name = self.data[sec_off:sec_off+8].rstrip(b'\x00').decode('ascii', errors='ignore')
                virt_size = struct.unpack('<I', self.data[sec_off+8:sec_off+12])[0]
                virt_addr = struct.unpack('<I', self.data[sec_off+12:sec_off+16])[0]
                raw_size = struct.unpack('<I', self.data[sec_off+16:sec_off+20])[0]
                raw_ptr = struct.unpack('<I', self.data[sec_off+20:sec_off+24])[0]
                chars = struct.unpack('<I', self.data[sec_off+36:sec_off+40])[0]
                self.sections.append({
                    "name": name, "virtual_size": virt_size, "virtual_address": virt_addr,
                    "raw_size": raw_size, "raw_pointer": raw_ptr, "characteristics": chars
                })

            import_rva = struct.unpack('<I', self.data[data_dir_offset+8:data_dir_offset+12])[0]
            import_size = struct.unpack('<I', self.data[data_dir_offset+12:data_dir_offset+16])[0]
            if import_rva and import_size:
                self._parse_imports(import_rva)

            export_rva = struct.unpack('<I', self.data[data_dir_offset:data_dir_offset+4])[0]
            export_size = struct.unpack('<I', self.data[data_dir_offset+4:data_dir_offset+8])[0]
            if export_rva and export_size:
                self._parse_exports(export_rva)

            return True
        except Exception as e:
            print(f"Erro ao parsear PE: {e}")
            return False

    def _rva_to_offset(self, rva):
        for section in self.sections:
            start = section["virtual_address"]
            end = start + max(section["virtual_size"], section["raw_size"])
            if start <= rva < end:
                offset = section["raw_pointer"] + (rva - start)
                if 0 <= offset < len(self.data):
                    return offset
                return None
        return None

    def _read_string(self, offset):
        if offset is None or offset >= len(self.data):
            return ""
        end = self.data.find(b'\x00', offset)
        if end == -1:
            return ""
        return self.data[offset:end].decode('ascii', errors='ignore')

    def _parse_imports(self, import_rva):
        offset = self._rva_to_offset(import_rva)
        if offset is None:
            return
        ptr_size = 8 if self.is_64bit else 4
        ordinal_flag = 0x8000000000000000 if self.is_64bit else 0x80000000
        name_mask = ordinal_flag - 1

        while offset + 20 <= len(self.data):
            original_first_thunk = struct.unpack('<I', self.data[offset:offset+4])[0]
            name_rva = struct.unpack('<I', self.data[offset+12:offset+16])[0]
            first_thunk = struct.unpack('<I', self.data[offset+16:offset+20])[0]

            if original_first_thunk == 0 and name_rva == 0 and first_thunk == 0:
                break

            dll_name_offset = self._rva_to_offset(name_rva)
            dll_name = self._read_string(dll_name_offset).lower()

            if not dll_name:
                offset += 20
                continue

            functions = []
            thunk_rva = original_first_thunk if original_first_thunk else first_thunk
            thunk_offset = self._rva_to_offset(thunk_rva)

            if thunk_offset is not None:
                i = 0
                while True:
                    cur = thunk_offset + (i * ptr_size)
                    if cur + ptr_size > len(self.data):
                        break
                    if self.is_64bit:
                        thunk = struct.unpack('<Q', self.data[cur:cur+8])[0]
                    else:
                        thunk = struct.unpack('<I', self.data[cur:cur+4])[0]
                    if thunk == 0:
                        break
                    if thunk & ordinal_flag:
                        ordinal = thunk & 0xFFFF
                        functions.append(f"Ordinal#{ordinal}")
                    else:
                        name_off = self._rva_to_offset(thunk & name_mask)
                        if name_off is not None and name_off + 2 < len(self.data):
                            func_name = self._read_string(name_off + 2)
                            if func_name:
                                functions.append(func_name)
                    i += 1
                    if i > 10000:
                        break

            if dll_name:
                self.imports[dll_name] = functions
            offset += 20

    def _parse_exports(self, export_rva):
        try:
            offset = self._rva_to_offset(export_rva)
            if offset is None:
                return
            num_names = struct.unpack('<I', self.data[offset+24:offset+28])[0]
            names_rva = struct.unpack('<I', self.data[offset+32:offset+36])[0]
            names_off = self._rva_to_offset(names_rva)
            if names_off is None:
                return
            for i in range(min(num_names, 10000)):
                cur = names_off + (i * 4)
                if cur + 4 > len(self.data):
                    break
                name_rva = struct.unpack('<I', self.data[cur:cur+4])[0]
                name = self._read_string(self._rva_to_offset(name_rva))
                if name:
                    self.exports.append(name)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
# ANALYZER
# ═══════════════════════════════════════════════════════════════
class DeepAnalyzer:
    STRING_PATTERNS = {
        "URLs HTTP/HTTPS": {
            "regex": r"https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]{4,}",
            "severity": "ALTO", "icon": "🌐"
        },
        "Endereços IP": {
            "regex": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
            "severity": "ALTO", "icon": "🔢"
        },
        "Chaves de Registro": {
            "regex": r"(?:HKEY_[A-Z_]+|HKLM|HKCU|HKCR)\\[A-Za-z0-9_\\\-\. ]+",
            "severity": "MÉDIO", "icon": "🔑"
        },
        "Caminhos de Arquivos": {
            "regex": r"[A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n\x00]+\\)*[^\\/:*?\"<>|\r\n\x00]*",
            "severity": "BAIXO", "icon": "📁"
        },
        "PowerShell/CMD": {
            "regex": r"(?i)(?:powershell(?:\.exe)?|cmd(?:\.exe)?|wscript|cscript|rundll32)",
            "severity": "CRÍTICO", "icon": "⚠️"
        },
        "Emails": {
            "regex": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
            "severity": "MÉDIO", "icon": "📧"
        },
        "User-Agents": {
            "regex": r"Mozilla/[0-9.]+ \([^)]{5,100}\)",
            "severity": "MÉDIO", "icon": "🤖"
        },
    }

    def __init__(self):
        self.filepath = None
        self.file_info = {}
        self.pe_parser = None
        self.imports_analysis = {}
        self.strings_analysis = {}
        self.all_strings = []
        self.behaviors = []

    @staticmethod
    def _format_size(size):
        size = float(size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def analyze(self, filepath, progress_cb=None):
        self.filepath = filepath
        if progress_cb: progress_cb(5, "Obtendo informações do arquivo...")
        self._get_file_info()
        if progress_cb: progress_cb(15, "Parseando estrutura PE...")
        self.pe_parser = PEParser(filepath)
        self.pe_parser.parse()
        if progress_cb: progress_cb(35, "Analisando imports (APIs)...")
        self._analyze_imports()
        if progress_cb: progress_cb(55, "Extraindo strings...")
        self._extract_strings()
        if progress_cb: progress_cb(75, "Identificando padrões suspeitos...")
        self._analyze_strings()
        if progress_cb: progress_cb(85, "Deduzindo comportamentos...")
        self._detect_behaviors()
        if progress_cb: progress_cb(95, "Finalizando...")

    def _get_file_info(self):
        if not self.filepath:
            raise RuntimeError("Nenhum arquivo definido.")
        if not os.path.isfile(self.filepath):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.filepath}")

        stat = os.stat(self.filepath)
        with open(self.filepath, 'rb') as f:
            content = f.read()

        magic_map = [
            (b'MZ', "Executável Windows (PE)"),
            (b'\x7fELF', "Executável Linux (ELF)"),
            (b'\xca\xfe\xba\xbe', "Java Class / Mach-O Fat"),
            (b'\xcf\xfa\xed\xfe', "Mach-O (macOS)"),
            (b'PK\x03\x04', "Arquivo ZIP / Office / APK"),
            (b'\x89PNG', "Imagem PNG"),
            (b'\xff\xd8\xff', "Imagem JPEG"),
            (b'GIF8', "Imagem GIF"),
            (b'%PDF', "Documento PDF"),
            (b'Rar!', "Arquivo RAR"),
            (b'7z\xbc\xaf', "Arquivo 7-Zip"),
            (b'ID3', "Arquivo MP3"),
        ]
        detected = "Desconhecido / Dados binários"
        for magic, desc in magic_map:
            if content[:len(magic)] == magic:
                detected = desc
                break

        self.file_info = {
            "nome": os.path.basename(self.filepath),
            "caminho": os.path.abspath(self.filepath),
            "tamanho": stat.st_size,
            "tamanho_fmt": self._format_size(stat.st_size),
            "modificado": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
            "criado": datetime.fromtimestamp(stat.st_ctime).strftime("%d/%m/%Y %H:%M:%S"),
            "md5": hashlib.md5(content).hexdigest(),
            "sha1": hashlib.sha1(content).hexdigest(),
            "sha256": hashlib.sha256(content).hexdigest(),
            "detected_type": detected,
        }

    def _analyze_imports(self):
        self.imports_analysis = {
            "by_dll": {}, "by_category": {}, "all_functions": [], "unknown_functions": [],
            "stats": {"total_dlls": 0, "total_functions": 0, "known": 0, "unknown": 0}
        }
        if self.pe_parser is None:
            if not self.filepath:
                raise RuntimeError("Nenhum arquivo carregado.")
            self.pe_parser = PEParser(self.filepath)
            self.pe_parser.parse()

        pe_imports = getattr(self.pe_parser, "imports", None)
        if not pe_imports:
            return

        for dll, funcs in pe_imports.items():
            self.imports_analysis["by_dll"][dll] = []
            for func in funcs:
                info = API_KNOWLEDGE_BASE.get(func, None)
                func_data = {
                    "name": func, "dll": dll, "known": info is not None,
                    "description": info["desc"] if info else "Função não catalogada",
                    "category": info["cat"] if info else "Outros",
                    "risk": info["risk"] if info else "DESCONHECIDO",
                    "icon": info["icon"] if info else "❓",
                }
                self.imports_analysis["by_dll"][dll].append(func_data)
                self.imports_analysis["all_functions"].append(func_data)
                if info:
                    cat = info["cat"]
                    if cat not in self.imports_analysis["by_category"]:
                        self.imports_analysis["by_category"][cat] = []
                    self.imports_analysis["by_category"][cat].append(func_data)
                    self.imports_analysis["stats"]["known"] += 1
                else:
                    self.imports_analysis["unknown_functions"].append(func_data)
                    self.imports_analysis["stats"]["unknown"] += 1

        self.imports_analysis["stats"]["total_dlls"] = len(pe_imports)
        self.imports_analysis["stats"]["total_functions"] = len(self.imports_analysis["all_functions"])

    def _extract_strings(self, min_len=5):
        if not self.filepath or not os.path.isfile(self.filepath):
            raise RuntimeError(f"Arquivo inválido: {self.filepath!r}")
        self.all_strings = []
        with open(self.filepath, 'rb') as f:
            content = f.read()
        for match in re.finditer(rb'[\x20-\x7E]{%d,}' % min_len, content):
            s = match.group().decode('ascii', errors='ignore')
            self.all_strings.append({
                "string": s, "offset": match.start(),
                "hex_offset": f"0x{match.start():08X}", "type": "ASCII"
            })
        for match in re.finditer(rb'(?:[\x20-\x7E]\x00){%d,}' % min_len, content):
            try:
                s = match.group().decode('utf-16-le', errors='ignore')
                if len(s) >= min_len:
                    self.all_strings.append({
                        "string": s, "offset": match.start(),
                        "hex_offset": f"0x{match.start():08X}", "type": "Unicode"
                    })
            except Exception:
                pass

    def _analyze_strings(self):
        self.strings_analysis = {}
        for cat, cfg in self.STRING_PATTERNS.items():
            self.strings_analysis[cat] = {
                "severity": cfg["severity"], "icon": cfg["icon"], "findings": []
            }
            regex = re.compile(cfg["regex"])
            seen = set()
            for s in self.all_strings:
                for match in regex.finditer(s["string"]):
                    val = match.group()
                    key = val.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    self.strings_analysis[cat]["findings"].append({
                        "value": val, "context": s["string"][:200],
                        "offset": s["hex_offset"], "type": s["type"]
                    })

    def _detect_behaviors(self):
        self.behaviors = []
        funcs = {f["name"] for f in self.imports_analysis.get("all_functions", [])}

        checks = [
            ("Execução de Comandos Externos",
             {"ShellExecuteA", "ShellExecuteW", "ShellExecuteExA", "ShellExecuteExW",
              "CreateProcessA", "CreateProcessW", "WinExec"},
             "🚀", "ALTO", "O binário pode executar comandos externos ou lançar outros programas."),
            ("Comunicação em Rede HTTP",
             {"InternetOpenA", "InternetOpenW", "HttpOpenRequestA", "HttpOpenRequestW",
              "WinHttpOpen", "URLDownloadToFileA", "URLDownloadToFileW"},
             "🌐", "ALTO", "O binário se conecta a servidores HTTP/HTTPS."),
            ("Download de Arquivos",
             {"URLDownloadToFileA", "URLDownloadToFileW", "InternetReadFile"},
             "⬇️", "CRÍTICO", "⚠️ Capacidade de baixar e executar arquivos remotos (dropper)."),
            ("Manipulação de Registro",
             {"RegCreateKeyA", "RegCreateKeyW", "RegSetValueA", "RegSetValueW",
              "RegSetValueExA", "RegSetValueExW"},
             "🔑", "MÉDIO", "Pode modificar o registro do Windows (persistência?)."),
            ("Injeção de Código",
             {"VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread", "NtCreateThreadEx"},
             "💉", "CRÍTICO", "🚨 PADRÃO CLÁSSICO DE INJEÇÃO DE CÓDIGO em outros processos!"),
            ("Process Hollowing",
             {"CreateProcessA", "CreateProcessW", "GetThreadContext", "SetThreadContext",
              "WriteProcessMemory"},
             "🕳️", "CRÍTICO", "🚨 Possível técnica de Process Hollowing (malware avançado)."),
            ("Keylogger/Hook",
             {"SetWindowsHookExA", "SetWindowsHookExW", "GetAsyncKeyState", "GetKeyState"},
             "⌨️", "ALTO", "⚠️ Capacidade de capturar teclas (possível keylogger)."),
            ("Anti-Debug/Anti-Análise",
             {"IsDebuggerPresent", "CheckRemoteDebuggerPresent", "NtQueryInformationProcess",
              "OutputDebugStringA"},
             "🕵️", "ALTO", "⚠️ Técnicas de evasão de debuggers e análise."),
            ("Criptografia",
             {"CryptEncrypt", "CryptDecrypt", "CryptGenKey", "CryptAcquireContextA"},
             "🔐", "MÉDIO", "Uso de APIs de criptografia (ransomware?)."),
            ("Enumeração de Processos",
             {"CreateToolhelp32Snapshot", "Process32FirstW", "Process32NextW"},
             "📋", "MÉDIO", "Enumera processos em execução no sistema."),
            ("Persistência via Serviço",
             {"CreateServiceA", "CreateServiceW", "OpenSCManagerA", "OpenSCManagerW"},
             "🔧", "ALTO", "⚠️ Pode criar serviços do Windows (persistência)."),
            ("Carregamento Dinâmico de DLL",
             {"LoadLibraryA", "LoadLibraryW", "GetProcAddress"},
             "📚", "MÉDIO", "Carrega DLLs e resolve funções em runtime (API hiding)."),
            ("Manipulação de Arquivos",
             {"CreateFileA", "CreateFileW", "WriteFile", "DeleteFileA", "DeleteFileW",
              "CopyFileA", "CopyFileW"},
             "📄", "BAIXO", "Lê/escreve/deleta arquivos no sistema."),
            ("Enumeração do Sistema",
             {"GetComputerNameA", "GetComputerNameW", "GetUserNameA", "GetUserNameW",
              "GetVersionExA", "GetVersionExW"},
             "💻", "BAIXO", "Coleta informações sobre o sistema e usuário (reconnaissance)."),
        ]

        for name, required, icon, risk, desc in checks:
            matched = funcs & required
            if matched:
                self.behaviors.append({
                    "name": name, "icon": icon, "risk": risk,
                    "description": desc, "evidence": sorted(matched)
                })

    def calculate_risk_score(self):
        score = 0
        weights = {"CRÍTICO": 25, "ALTO": 15, "MÉDIO": 7, "BAIXO": 2}
        for b in self.behaviors:
            score += weights.get(b["risk"], 0)
        for cat, data in self.strings_analysis.items():
            if data["findings"]:
                score += weights.get(data["severity"], 0) // 2
        return min(score, 100)


# ═══════════════════════════════════════════════════════════════
# GERADOR DE RELATÓRIO HTML
# ═══════════════════════════════════════════════════════════════
class HTMLReportGenerator:

    @staticmethod
    def _esc(text):
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    @staticmethod
    def generate(analyzer, output_path):
        risk_score = analyzer.calculate_risk_score()
        scan_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        fi = analyzer.file_info
        pe = analyzer.pe_parser.pe_info if (analyzer.pe_parser and analyzer.pe_parser.is_pe) else {}

        if risk_score >= 70:
            risk_color, risk_level = "#ef4444", "ALTO RISCO"
        elif risk_score >= 40:
            risk_color, risk_level = "#f59e0b", "RISCO MODERADO"
        elif risk_score > 0:
            risk_color, risk_level = "#3b82f6", "BAIXO RISCO"
        else:
            risk_color, risk_level = "#10b981", "LIMPO"

        behaviors_html = ""
        if analyzer.behaviors:
            for b in analyzer.behaviors:
                badge = {"CRÍTICO": "critical", "ALTO": "high", "MÉDIO": "medium", "BAIXO": "low"}.get(b["risk"], "low")
                evidence = ", ".join([f'<code>{HTMLReportGenerator._esc(e)}</code>' for e in b["evidence"]])
                behaviors_html += f"""
                <div class="behavior-card behavior-{badge}">
                    <div class="behavior-header">
                        <div class="behavior-icon">{b['icon']}</div>
                        <div class="behavior-title-wrap">
                            <h3 class="behavior-title">{HTMLReportGenerator._esc(b['name'])}</h3>
                            <span class="badge badge-{badge}">{b['risk']}</span>
                        </div>
                    </div>
                    <p class="behavior-desc">{HTMLReportGenerator._esc(b['description'])}</p>
                    <div class="behavior-evidence">
                        <strong>Evidências (APIs):</strong> {evidence}
                    </div>
                </div>
                """
        else:
            behaviors_html = '<div class="empty-state">Nenhum comportamento suspeito identificado.</div>'

        imports_html = ""
        for dll, funcs in sorted(analyzer.pe_parser.imports.items()):
            rows = ""
            for i, f in enumerate(funcs, 1):
                info = API_KNOWLEDGE_BASE.get(f, None)
                if info:
                    badge = {"CRÍTICO": "critical", "ALTO": "high", "MÉDIO": "medium",
                             "BAIXO": "low", "DESCONHECIDO": "unknown"}.get(info["risk"], "low")
                    desc = info["desc"]; icon = info["icon"]; risk = info["risk"]; cat = info["cat"]
                else:
                    badge = "unknown"; desc = "Função não catalogada"
                    icon = "❓"; risk = "N/A"; cat = "Outros"

                rows += f"""
                <tr>
                    <td class="td-num">{i}</td>
                    <td><span class="icon-cell">{icon}</span></td>
                    <td><code class="func-name">{HTMLReportGenerator._esc(f)}</code></td>
                    <td>{HTMLReportGenerator._esc(cat)}</td>
                    <td><span class="badge badge-{badge}">{risk}</span></td>
                    <td class="desc-cell">{HTMLReportGenerator._esc(desc)}</td>
                </tr>
                """

            imports_html += f"""
            <div class="dll-section">
                <div class="dll-header" onclick="toggleSection(this)">
                    <div class="dll-title">
                        <span class="dll-icon">📚</span>
                        <h3>{HTMLReportGenerator._esc(dll)}</h3>
                        <span class="badge badge-info">{len(funcs)} funções</span>
                    </div>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="dll-content">
                    <table class="data-table">
                        <thead>
                            <tr><th width="40">#</th><th width="40"></th><th>Função</th>
                                <th width="130">Categoria</th><th width="110">Risco</th><th>Descrição</th></tr>
                        </thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
            </div>
            """

        if not imports_html:
            imports_html = '<div class="empty-state">Arquivo não possui tabela de imports (não é um PE válido ou está limpo).</div>'

        stats = analyzer.imports_analysis["stats"]

        strings_html = ""
        for cat, data in analyzer.strings_analysis.items():
            findings = data["findings"]
            badge = {"CRÍTICO": "critical", "ALTO": "high", "MÉDIO": "medium", "BAIXO": "low"}.get(data["severity"], "low")

            if findings:
                rows = ""
                for i, f in enumerate(findings[:50], 1):
                    rows += f"""
                    <tr>
                        <td class="td-num">{i}</td>
                        <td><code class="offset-cell">{HTMLReportGenerator._esc(f['offset'])}</code></td>
                        <td><span class="type-badge type-{f['type'].lower()}">{f['type']}</span></td>
                        <td class="string-cell"><code>{HTMLReportGenerator._esc(f['value'])}</code></td>
                    </tr>
                    """
                extra = f"<p class='more-info'>... e mais {len(findings) - 50} resultados</p>" if len(findings) > 50 else ""

                strings_html += f"""
                <div class="dll-section">
                    <div class="dll-header" onclick="toggleSection(this)">
                        <div class="dll-title">
                            <span class="dll-icon">{data['icon']}</span>
                            <h3>{HTMLReportGenerator._esc(cat)}</h3>
                            <span class="badge badge-{badge}">{len(findings)} encontrado(s)</span>
                        </div>
                        <span class="toggle-icon">▼</span>
                    </div>
                    <div class="dll-content">
                        <table class="data-table">
                            <thead>
                                <tr><th width="40">#</th><th width="120">Offset</th><th width="80">Tipo</th><th>Valor</th></tr>
                            </thead>
                            <tbody>{rows}</tbody>
                        </table>
                        {extra}
                    </div>
                </div>
                """

        # ========= TODAS AS STRINGS (CORRIGIDO + BUSCA) =========
        all_strings = getattr(analyzer, 'all_strings', []) or []
        total_all = len(all_strings)
        MAX_RENDER = 10000

        if total_all > 0:
            rendered = all_strings[:MAX_RENDER]
            rows_all = []
            for i, s in enumerate(rendered, 1):
                off = s.get('hex_offset', s.get('offset', ''))
                if isinstance(off, int):
                    off = f"0x{off:08X}"
                stype = s.get('type', 'ASCII')
                val = s.get('string', s.get('value', ''))

                rows_all.append(f"""
                    <tr class="string-row" data-search="{HTMLReportGenerator._esc(val).lower()}">
                        <td class="td-num">{i}</td>
                        <td><code class="offset-cell">{HTMLReportGenerator._esc(off)}</code></td>
                        <td><span class="type-badge type-{stype.lower()}">{HTMLReportGenerator._esc(stype)}</span></td>
                        <td class="string-cell"><code>{HTMLReportGenerator._esc(val)}</code></td>
                    </tr>
                """)
            extra_all = ""
            if total_all > MAX_RENDER:
                extra_all = (f"<p class='more-info'>⚠️ Exibindo apenas as primeiras "
                             f"{MAX_RENDER:,} de {total_all:,} strings "
                             f"(limite para performance do navegador).</p>")

            all_strings_html = f"""
            <div class="dll-section">
                <div class="dll-header" onclick="toggleSection(this)">
                    <div class="dll-title">
                        <span class="dll-icon">📜</span>
                        <h3>Todas as Strings Extraídas</h3>
                        <span class="badge badge-info">{total_all:,} total</span>
                    </div>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="dll-content">
                    <div class="search-box">
                        <input type="text" id="stringSearch" placeholder="🔍 Pesquisar nas strings... (ex: http, kernel32, admin)"
                               oninput="filterStrings()" />
                        <button onclick="clearSearch()" class="btn-clear">✖ Limpar</button>
                        <span id="searchResult" class="search-result">{total_all:,} strings</span>
                    </div>
                    <table class="data-table" id="stringsTable">
                        <thead>
                            <tr>
                                <th width="60">#</th>
                                <th width="120">Offset</th>
                                <th width="80">Tipo</th>
                                <th>Valor</th>
                            </tr>
                        </thead>
                        <tbody>{''.join(rows_all)}</tbody>
                    </table>
                    {extra_all}
                </div>
            </div>
            """
        else:
            all_strings_html = '<div class="empty-state">Nenhuma string extraída do arquivo.</div>'

        sections_html = ""
        for s in analyzer.pe_parser.sections:
            exec_flag = "✅" if s["characteristics"] & 0x20000000 else "❌"
            write_flag = "✅" if s["characteristics"] & 0x80000000 else "❌"
            read_flag = "✅" if s["characteristics"] & 0x40000000 else "❌"
            sections_html += f"""
            <tr>
                <td><code>{HTMLReportGenerator._esc(s['name'])}</code></td>
                <td><code>0x{s['virtual_address']:08X}</code></td>
                <td>{s['virtual_size']:,} bytes</td>
                <td>{s['raw_size']:,} bytes</td>
                <td style="text-align:center">{read_flag}</td>
                <td style="text-align:center">{write_flag}</td>
                <td style="text-align:center">{exec_flag}</td>
            </tr>
            """

        file_type_label = pe.get('file_type', fi.get('detected_type', 'N/A'))

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Análise Profunda - {HTMLReportGenerator._esc(fi['nome'])}</title>
<style>
:root {{
    --bg-primary: #0a0e17; --bg-secondary: #111827; --bg-card: #1a2332;
    --bg-card-hover: #1f2b3d; --border: #2a3a50; --text: #e2e8f0;
    --text-muted: #94a3b8; --text-dim: #64748b;
    --blue: #3b82f6; --cyan: #06b6d4; --green: #10b981;
    --red: #ef4444; --orange: #f59e0b; --purple: #8b5cf6; --pink: #ec4899;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: 'Segoe UI', 'Inter', sans-serif; background: var(--bg-primary);
    color: var(--text); line-height: 1.6; }}
.container {{ max-width:1500px; margin:0 auto; padding:20px; }}
.report-header {{ background: linear-gradient(135deg, #1a2332 0%, #0f1923 100%);
    border: 1px solid var(--border); border-radius: 16px; padding: 40px;
    margin-bottom: 30px; position: relative; overflow: hidden; }}
.report-header::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; background: linear-gradient(90deg, var(--blue), var(--cyan), var(--purple), var(--pink)); }}
.header-content {{ display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:20px; }}
.header-left h1 {{ font-size: 28px; font-weight: 700;
    background: linear-gradient(135deg, var(--blue), var(--cyan));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }}
.subtitle {{ color: var(--text-muted); font-size:14px; }}
.scan-time {{ color: var(--text-dim); font-size:13px; }}
.header-logo {{ font-size:40px; margin-bottom:10px; }}
.top-grid {{ display: grid; grid-template-columns: 300px 1fr; gap: 20px; margin-bottom: 30px; }}
@media (max-width: 900px) {{ .top-grid {{ grid-template-columns: 1fr; }} }}
.card {{ background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px; }}
.card h2 {{ font-size: 14px; color: var(--text-muted); margin-bottom: 16px;
    text-transform: uppercase; letter-spacing: 1px; display: flex; align-items: center; gap: 8px; }}
.risk-circle {{ width: 160px; height: 160px; border-radius: 50%;
    background: conic-gradient({risk_color} {risk_score * 3.6}deg, var(--bg-secondary) 0);
    margin: 0 auto 15px; display: flex; align-items: center; justify-content: center;
    box-shadow: 0 0 40px {risk_color}30; }}
.risk-inner {{ width: 120px; height: 120px; background: var(--bg-card); border-radius: 50%;
    display: flex; flex-direction: column; align-items: center; justify-content: center; }}
.risk-num {{ font-size: 42px; font-weight: 800; color: {risk_color}; }}
.risk-label {{ font-size: 11px; color: var(--text-dim); text-transform: uppercase; }}
.risk-level {{ font-size: 18px; font-weight: 700; color: {risk_color}; text-align: center; }}
.info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px; }}
.info-item {{ display: flex; gap: 10px; padding: 10px 14px; background: var(--bg-secondary);
    border-radius: 8px; border: 1px solid var(--border); align-items: center; }}
.info-label {{ color: var(--text-dim); font-size: 11px; text-transform: uppercase;
    font-weight: 700; min-width: 90px; }}
.info-value {{ color: var(--text); font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px; word-break: break-all; }}
.hash-val {{ font-size: 11px; color: var(--cyan); }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px; margin-bottom: 30px; }}
.stat-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px;
    padding: 24px; text-align: center; position: relative; overflow: hidden; transition: all 0.3s; }}
.stat-card:hover {{ transform: translateY(-2px); border-color: var(--blue); }}
.stat-card::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; background: var(--blue); }}
.stat-icon {{ font-size: 32px; margin-bottom: 8px; }}
.stat-num {{ font-size: 36px; font-weight: 800; color: var(--text); line-height: 1; }}
.stat-label {{ font-size: 13px; color: var(--text-muted); margin-top: 6px; }}
.section-heading {{ font-size: 20px; color: var(--text); margin: 40px 0 20px;
    padding-bottom: 10px; border-bottom: 2px solid var(--border);
    display: flex; align-items: center; gap: 10px; }}
.behaviors-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 16px; margin-bottom: 30px; }}
.behavior-card {{ background: var(--bg-card); border: 1px solid var(--border);
    border-left: 4px solid var(--blue); border-radius: 10px; padding: 20px; transition: all 0.3s; }}
.behavior-card:hover {{ background: var(--bg-card-hover); }}
.behavior-critical {{ border-left-color: var(--red); }}
.behavior-high {{ border-left-color: var(--orange); }}
.behavior-medium {{ border-left-color: var(--blue); }}
.behavior-low {{ border-left-color: var(--green); }}
.behavior-header {{ display:flex; gap:14px; align-items:flex-start; margin-bottom:12px; }}
.behavior-icon {{ font-size: 32px; }}
.behavior-title-wrap {{ flex: 1; }}
.behavior-title {{ font-size: 16px; margin-bottom: 4px; }}
.behavior-desc {{ color: var(--text-muted); font-size: 13px; margin-bottom: 10px; }}
.behavior-evidence {{ font-size: 12px; color: var(--text-dim); padding-top: 10px;
    border-top: 1px solid var(--border); }}
.behavior-evidence code {{ background: var(--bg-secondary); padding: 2px 6px; border-radius: 4px;
    color: var(--cyan); font-size: 11px; margin: 2px; display: inline-block; }}
.badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
.badge-critical {{ background: #ef444420; color: var(--red); border: 1px solid #ef444440; }}
.badge-high {{ background: #f59e0b20; color: var(--orange); border: 1px solid #f59e0b40; }}
.badge-medium {{ background: #3b82f620; color: var(--blue); border: 1px solid #3b82f640; }}
.badge-low {{ background: #10b98120; color: var(--green); border: 1px solid #10b98140; }}
.badge-info {{ background: #06b6d420; color: var(--cyan); border: 1px solid #06b6d440; }}
.badge-unknown {{ background: #64748b20; color: var(--text-muted); border: 1px solid #64748b40; }}
.dll-section {{ background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 10px; margin-bottom: 12px; overflow: hidden; }}
.dll-header {{ padding: 16px 20px; display: flex; justify-content: space-between;
    align-items: center; cursor: pointer; transition: background 0.2s; user-select: none; }}
.dll-header:hover {{ background: var(--bg-card-hover); }}
.dll-title {{ display:flex; align-items:center; gap:12px; }}
.dll-icon {{ font-size: 20px; }}
.dll-title h3 {{ font-size: 15px; font-family: 'Consolas', monospace; color: var(--cyan); }}
.toggle-icon {{ color: var(--text-dim); transition: transform 0.3s; }}
.dll-content {{ border-top: 1px solid var(--border); overflow-x: auto; }}
.data-table {{ width: 100%; border-collapse: collapse; }}
.data-table th {{ background: var(--bg-secondary); color: var(--text-dim);
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;
    padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); }}
.data-table td {{ padding: 8px 14px; border-bottom: 1px solid #1a2332; font-size: 13px; }}
.data-table tr:hover {{ background: var(--bg-card-hover); }}
.td-num {{ color: var(--text-dim); text-align: center; }}
.icon-cell {{ font-size: 16px; }}
.func-name {{ color: var(--cyan); font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px; background: #06b6d410; padding: 2px 8px; border-radius: 4px; }}
.offset-cell {{ color: var(--purple); font-family: 'Consolas', monospace;
    font-size: 11px; background: #8b5cf610; padding: 2px 6px; border-radius: 3px; }}
.type-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 10px; font-weight: 700; }}
.type-ascii {{ background: #3b82f615; color: var(--blue); }}
.type-unicode {{ background: #8b5cf615; color: var(--purple); }}
.desc-cell {{ color: var(--text-muted); font-size: 12px; }}
.string-cell code {{ color: var(--text); font-family: 'Consolas', monospace;
    font-size: 11px; word-break: break-all; }}
.more-info {{ padding: 10px 20px; color: var(--text-dim); font-size: 12px; text-align: center; }}
.empty-state {{ text-align: center; padding: 40px; color: var(--text-dim);
    background: var(--bg-card); border-radius: 10px; border: 1px dashed var(--border); }}
.report-footer {{ text-align: center; padding: 30px; color: var(--text-dim);
    font-size: 12px; border-top: 1px solid var(--border); margin-top: 40px; }}
.collapsed {{ display: none !important; }}
.search-box {{ padding: 15px 20px; display: flex; gap: 10px; align-items: center;
    background: var(--bg-secondary); border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 10; }}
.search-box input {{ flex: 1; padding: 10px 14px; background: var(--bg-primary);
    border: 1px solid var(--border); border-radius: 6px; color: var(--text);
    font-size: 14px; font-family: 'Segoe UI', sans-serif; outline: none;
    transition: border-color 0.2s; }}
.search-box input:focus {{ border-color: var(--blue); box-shadow: 0 0 0 3px #3b82f630; }}
.btn-clear {{ padding: 10px 16px; background: var(--red); color: #fff; border: none;
    border-radius: 6px; cursor: pointer; font-weight: 700; font-size: 13px;
    transition: background 0.2s; }}
.btn-clear:hover {{ background: #dc2626; }}
.search-result {{ color: var(--cyan); font-weight: 700; font-size: 13px;
    padding: 8px 14px; background: #06b6d415; border-radius: 6px;
    white-space: nowrap; min-width: 120px; text-align: center; }}
.highlight {{ background: #fbbf24; color: #000; padding: 1px 3px; border-radius: 2px; }}
@media print {{ body {{ background: #fff; color: #000; }}
    .dll-header {{ cursor: default; }} .dll-content {{ display: block !important; }}
    .search-box {{ display: none; }} }}
</style>
</head>
<body>
<div class="container">
    <div class="report-header">
        <div class="header-content">
            <div class="header-left">
                <div class="header-logo">🔬</div>
                <h1>DLL Deep Analyzer Report</h1>
                <div class="subtitle">Análise Profunda de APIs, Imports e Comportamentos</div>
            </div>
            <div class="header-right">
                <div class="scan-time">📅 <strong>{scan_time}</strong></div>
            </div>
        </div>
    </div>
    <div class="top-grid">
        <div class="card" style="text-align:center;">
            <h2>🎯 Score de Risco</h2>
            <div class="risk-circle">
                <div class="risk-inner">
                    <div class="risk-num">{risk_score}</div>
                    <div class="risk-label">/ 100</div>
                </div>
            </div>
            <div class="risk-level">{risk_level}</div>
        </div>
        <div class="card">
            <h2>📄 Informações do Arquivo</h2>
            <div class="info-grid">
                <div class="info-item"><span class="info-label">Nome</span><span class="info-value">{HTMLReportGenerator._esc(fi['nome'])}</span></div>
                <div class="info-item"><span class="info-label">Tipo</span><span class="info-value">{HTMLReportGenerator._esc(file_type_label)}</span></div>
                <div class="info-item"><span class="info-label">Detecção</span><span class="info-value">{HTMLReportGenerator._esc(fi.get('detected_type','N/A'))}</span></div>
                <div class="info-item"><span class="info-label">Arquitetura</span><span class="info-value">{HTMLReportGenerator._esc(pe.get('architecture','N/A (não-PE)'))}</span></div>
                <div class="info-item"><span class="info-label">Tamanho</span><span class="info-value">{fi['tamanho_fmt']} ({fi['tamanho']:,} B)</span></div>
                <div class="info-item"><span class="info-label">Entry Point</span><span class="info-value">{HTMLReportGenerator._esc(pe.get('entry_point','N/A'))}</span></div>
                <div class="info-item"><span class="info-label">Image Base</span><span class="info-value">{HTMLReportGenerator._esc(pe.get('image_base','N/A'))}</span></div>
                <div class="info-item"><span class="info-label">Compilado</span><span class="info-value">{HTMLReportGenerator._esc(pe.get('timestamp','N/A'))}</span></div>
                <div class="info-item"><span class="info-label">Modificado</span><span class="info-value">{fi['modificado']}</span></div>
                <div class="info-item" style="grid-column:1/-1;"><span class="info-label">Caminho</span><span class="info-value" style="font-size:11px;">{HTMLReportGenerator._esc(fi['caminho'])}</span></div>
                <div class="info-item" style="grid-column:1/-1;"><span class="info-label">MD5</span><span class="info-value hash-val">{fi['md5']}</span></div>
                <div class="info-item" style="grid-column:1/-1;"><span class="info-label">SHA-1</span><span class="info-value hash-val">{fi['sha1']}</span></div>
                <div class="info-item" style="grid-column:1/-1;"><span class="info-label">SHA-256</span><span class="info-value hash-val">{fi['sha256']}</span></div>
            </div>
        </div>
    </div>
    <div class="stats-grid">
        <div class="stat-card"><div class="stat-icon">📚</div><div class="stat-num">{stats['total_dlls']}</div><div class="stat-label">DLLs Importadas</div></div>
        <div class="stat-card"><div class="stat-icon">⚙️</div><div class="stat-num">{stats['total_functions']}</div><div class="stat-label">Funções Totais</div></div>
        <div class="stat-card"><div class="stat-icon">✅</div><div class="stat-num">{stats['known']}</div><div class="stat-label">APIs Conhecidas</div></div>
        <div class="stat-card"><div class="stat-icon">⚡</div><div class="stat-num">{len(analyzer.behaviors)}</div><div class="stat-label">Comportamentos</div></div>
        <div class="stat-card"><div class="stat-icon">📜</div><div class="stat-num">{total_all:,}</div><div class="stat-label">Strings Extraídas</div></div>
    </div>
    <h2 class="section-heading">🎯 Comportamentos Identificados</h2>
    <div class="behaviors-grid">{behaviors_html}</div>
    <h2 class="section-heading">📦 Seções do PE</h2>
    {'<div class="dll-section"><div class="dll-content" style="display:block;"><table class="data-table"><thead><tr><th>Nome</th><th>V.Address</th><th>V.Size</th><th>Raw Size</th><th>R</th><th>W</th><th>X</th></tr></thead><tbody>' + sections_html + '</tbody></table></div></div>' if sections_html else '<div class="empty-state">Arquivo não é um PE — seções não disponíveis.</div>'}
    <h2 class="section-heading">📥 Imports (APIs por DLL)</h2>
    {imports_html}
    <h2 class="section-heading">🔍 Strings Suspeitas</h2>
    {strings_html if strings_html else '<div class="empty-state">Nenhuma string suspeita encontrada.</div>'}
    <h2 class="section-heading">📜 Todas as Strings</h2>
    {all_strings_html}
    <div class="report-footer">
        <p>🔬 <strong>DLL Deep Analyzer</strong> — Relatório Forense</p>
        <p>Gerado em {scan_time} | Análise manual pode ser necessária</p>
    </div>
</div>
<script>
function toggleSection(h) {{
    const c = h.nextElementSibling;
    const i = h.querySelector('.toggle-icon');
    if (c.classList.contains('collapsed')) {{
        c.classList.remove('collapsed');
        if (i) i.style.transform = 'rotate(0deg)';
    }} else {{
        c.classList.add('collapsed');
        if (i) i.style.transform = 'rotate(-90deg)';
    }}
}}

function filterStrings() {{
    const input = document.getElementById('stringSearch');
    const filter = input.value.toLowerCase().trim();
    const rows = document.querySelectorAll('#stringsTable tbody tr.string-row');
    const result = document.getElementById('searchResult');
    let visible = 0;

    rows.forEach(row => {{
        const text = row.getAttribute('data-search') || '';
        if (filter === '' || text.includes(filter)) {{
            row.style.display = '';
            visible++;
        }} else {{
            row.style.display = 'none';
        }}
    }});

    if (filter === '') {{
        result.textContent = rows.length.toLocaleString() + ' strings';
        result.style.background = '#06b6d415';
        result.style.color = '#06b6d4';
    }} else {{
        result.textContent = visible.toLocaleString() + ' / ' + rows.length.toLocaleString();
        if (visible === 0) {{
            result.style.background = '#ef444415';
            result.style.color = '#ef4444';
        }} else {{
            result.style.background = '#10b98115';
            result.style.color = '#10b981';
        }}
    }}
}}

function clearSearch() {{
    document.getElementById('stringSearch').value = '';
    filterStrings();
    document.getElementById('stringSearch').focus();
}}

// Atalho Ctrl+F para focar na busca de strings
document.addEventListener('keydown', function(e) {{
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {{
        const inp = document.getElementById('stringSearch');
        if (inp) {{
            e.preventDefault();
            inp.focus();
            inp.select();
        }}
    }}
}});
</script>
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path

    # ================= NOVO: Geração do HTML Apenas da Pesquisa =================
    @staticmethod
    def generate_search(analyzer, query, filtered_strings, output_path):
        fi = analyzer.file_info
        scan_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        rows = []
        for i, s in enumerate(filtered_strings[:10000], 1):
            off = s.get('hex_offset', s.get('offset', ''))
            if isinstance(off, int):
                off = f"0x{off:08X}"
            stype = s.get('type', 'ASCII')
            val = s.get('string', s.get('value', ''))
            
            rows.append(f"""
                <tr class="string-row" data-search="{HTMLReportGenerator._esc(val).lower()}">
                    <td class="td-num">{i}</td>
                    <td><code class="offset-cell">{HTMLReportGenerator._esc(off)}</code></td>
                    <td><span class="type-badge type-{stype.lower()}">{HTMLReportGenerator._esc(stype)}</span></td>
                    <td class="string-cell"><code>{HTMLReportGenerator._esc(val)}</code></td>
                </tr>
            """)
            
        extra = ""
        if len(filtered_strings) > 10000:
            extra = f"<p class='more-info'>⚠️ Exibindo apenas as primeiras 10.000 de {len(filtered_strings):,} strings limitadas para navegação.</p>"
            
        query_text = HTMLReportGenerator._esc(query) if query else "(Todas as strings)"
        
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resultado da Pesquisa - {HTMLReportGenerator._esc(fi['nome'])}</title>
<style>
:root {{
    --bg-primary: #0a0e17; --bg-secondary: #111827; --bg-card: #1a2332;
    --border: #2a3a50; --text: #e2e8f0; --text-muted: #94a3b8; --text-dim: #64748b;
    --blue: #3b82f6; --cyan: #06b6d4; --purple: #8b5cf6; --red: #ef4444;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg-primary); color: var(--text); padding: 20px; }}
.container {{ max-width: 1400px; margin: 0 auto; }}
.header {{ background: var(--bg-card); padding: 20px; border-radius: 10px; border: 1px solid var(--border); margin-bottom: 20px; }}
.header h1 {{ color: var(--cyan); font-size: 24px; margin-bottom: 10px; }}
.header p {{ color: var(--text-muted); font-size: 14px; margin-bottom: 5px; }}
.badge {{ background: #06b6d420; color: var(--cyan); border: 1px solid #06b6d440; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
.search-box {{ background: var(--bg-secondary); padding: 15px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 20px; position: sticky; top: 0; z-index: 10; display: flex; gap: 10px; }}
.search-box input {{ flex: 1; padding: 10px; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 6px; color: var(--text); outline: none; }}
.search-box input:focus {{ border-color: var(--blue); }}
table {{ width: 100%; border-collapse: collapse; background: var(--bg-card); border-radius: 8px; overflow: hidden; }}
th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); font-size: 13px; }}
th {{ background: var(--bg-secondary); color: var(--text-dim); text-transform: uppercase; font-size: 11px; }}
tr:hover {{ background: #1f2b3d; }}
.td-num {{ color: var(--text-dim); }}
.offset-cell {{ color: var(--purple); font-family: monospace; background: #8b5cf615; padding: 2px 6px; border-radius: 4px; }}
.type-badge {{ font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: bold; }}
.type-ascii {{ background: #3b82f615; color: var(--blue); }}
.type-unicode {{ background: #8b5cf615; color: var(--purple); }}
.string-cell code {{ font-family: monospace; word-break: break-all; color: var(--text); }}
.more-info {{ text-align: center; color: var(--text-dim); font-size: 12px; margin-top: 15px; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🔍 Relatório de Pesquisa de Strings</h1>
        <p><strong>Arquivo:</strong> {HTMLReportGenerator._esc(fi['nome'])}</p>
        <p><strong>MD5:</strong> {fi['md5']}</p>
        <div style="margin-top: 15px;">
            <span class="badge">Termo Analisado: "{query_text}"</span>
            <span class="badge" style="margin-left:10px; background: #3b82f620; color: var(--blue); border-color: #3b82f640;">{len(filtered_strings):,} resultados</span>
            <span style="margin-left:10px; font-size:12px; color:var(--text-dim);">{scan_time}</span>
        </div>
    </div>
    
    <div class="search-box">
        <input type="text" id="subSearch" placeholder="Refinar pesquisa dentro deste relatório..." oninput="filterSub()">
        <span id="subCount" style="color:var(--cyan); padding: 10px; font-weight:bold;">{len(filtered_strings):,} itens</span>
    </div>

    <table id="stringsTable">
        <thead>
            <tr><th width="50">#</th><th width="120">Offset</th><th width="80">Tipo</th><th>String Encontrada</th></tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    {extra}
</div>

<script>
function filterSub() {{
    const val = document.getElementById('subSearch').value.toLowerCase().trim();
    const trs = document.querySelectorAll('#stringsTable tbody tr');
    let count = 0;
    trs.forEach(tr => {{
        const txt = tr.getAttribute('data-search') || '';
        if(val === '' || txt.includes(val)) {{
            tr.style.display = '';
            count++;
        }} else {{
            tr.style.display = 'none';
        }}
    }});
    document.getElementById('subCount').innerText = count.toLocaleString() + ' itens visíveis';
}}
</script>
</body>
</html>"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path


# ═══════════════════════════════════════════════════════════════
# INTERFACE GRÁFICA
# ═══════════════════════════════════════════════════════════════
class AnalyzerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔬 DLL Análise Forense")
        self.root.geometry("1200x850")
        self.root.state("zoomed")
        self.root.minsize(980, 720)
        self.analyzer = DeepAnalyzer()
        self.selected_file = tk.StringVar()
        self.is_running = False
        self.last_report_path = None
        self.has_results = False
        self.search_var = tk.StringVar()  # busca de strings

        self.colors = {
            "bg_dark": "#0d1117", "bg_med": "#161b22", "bg_light": "#21262d",
            "bg_input": "#0d1117", "border": "#30363d", "text": "#e6edf3",
            "text_sec": "#8b949e", "blue": "#58a6ff", "green": "#3fb950",
            "red": "#f85149", "orange": "#d29922", "purple": "#bc8cff", "cyan": "#39d2c0"
        }
        self.root.configure(bg=self.colors["bg_dark"])
        self._setup_styles()
        self._build_ui()
        self._center()

    def _center(self):
        self.root.update_idletasks()
        w = self.root.winfo_width(); h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Main.TFrame", background=self.colors["bg_dark"])
        style.configure("Card.TFrame", background=self.colors["bg_med"])
        style.configure("Title.TLabel", background=self.colors["bg_dark"],
                        foreground=self.colors["cyan"], font=("Segoe UI", 22, "bold"))
        style.configure("Sub.TLabel", background=self.colors["bg_dark"],
                        foreground=self.colors["text_sec"], font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=self.colors["bg_med"],
                        foreground=self.colors["text"], font=("Segoe UI", 10))
        style.configure("Status.TLabel", background=self.colors["bg_dark"],
                        foreground=self.colors["text_sec"], font=("Segoe UI", 9))
        style.configure("Horizontal.TProgressbar", background=self.colors["blue"],
                        troughcolor=self.colors["bg_light"], bordercolor=self.colors["border"])
        style.configure("TNotebook", background=self.colors["bg_dark"], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.colors["bg_light"],
                        foreground=self.colors["text_sec"], font=("Segoe UI", 11, "bold"),
                        padding=[20, 8])
        style.map("TNotebook.Tab",
                  background=[("selected", self.colors["bg_med"])],
                  foreground=[("selected", self.colors["cyan"])])

    def _build_ui(self):
        container = ttk.Frame(self.root, style="Main.TFrame")
        container.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tab_analysis = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab_analysis, text="  🚀 Análise  ")
        self._build_analysis_tab(tab_analysis)

        tab_results = ttk.Frame(self.notebook, style="Main.TFrame")
        self.notebook.add(tab_results, text="  📊 Resultados  ")
        self._build_results_tab(tab_results)

    def _build_analysis_tab(self, main):
        main = ttk.Frame(main, style="Main.TFrame")
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        hdr = ttk.Frame(main, style="Main.TFrame")
        hdr.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(hdr, text="🔬 DLL Deep Analyzer", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(hdr, text="  Professional Forensics v4.4", style="Sub.TLabel").pack(side=tk.LEFT, pady=(8, 0))

        fc = self._card(main, "📂 Arquivo para Análise (DLL, EXE, PDF, ZIP, ou QUALQUER arquivo)")
        fr = tk.Frame(fc, bg=self.colors["bg_med"])
        fr.pack(fill=tk.X, pady=5)
        self.file_entry = tk.Entry(fr, textvariable=self.selected_file, font=("Consolas", 11),
                                    bg=self.colors["bg_input"], fg=self.colors["text"],
                                    insertbackground=self.colors["cyan"], relief="flat", bd=0,
                                    highlightthickness=1, highlightbackground=self.colors["border"],
                                    highlightcolor=self.colors["blue"])
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        tk.Button(fr, text="📁 Procurar", font=("Segoe UI", 10, "bold"),
                  bg=self.colors["blue"], fg="#fff", activebackground="#4a90d9",
                  relief="flat", cursor="hand2", padx=20, pady=6,
                  command=self.browse_file).pack(side=tk.RIGHT)
        self.file_info_lbl = ttk.Label(fc, text="Nenhum arquivo selecionado", style="Card.TLabel")
        self.file_info_lbl.pack(fill=tk.X, pady=(8, 0))

        info = self._card(main, "ℹ️ Recursos do Analisador")
        info_text = (
            "• Aceita QUALQUER tipo de arquivo (DLL, EXE, PDF, ZIP, imagens, etc.)\n"
            "• Parse completo de PE sem dependências externas (quando aplicável)\n"
            "• Extração de todas as DLLs importadas e suas funções (APIs)\n"
            "• Identificação de ~150+ APIs do Windows com descrição e risco\n"
            "• Dedução de comportamentos (injeção, keylogger, ransomware, etc.)\n"
            "• Extração de URLs, IPs, chaves de registro, caminhos, emails\n"
            "• 🔍 BUSCA em tempo real nas strings e botão de Exportação de Busca\n"
            "• Após analisar: use o botão '💾 Salvar HTML' na aba Resultados"
        )
        tk.Label(info, text=info_text, font=("Segoe UI", 10), bg=self.colors["bg_med"],
                 fg=self.colors["text_sec"], justify=tk.LEFT, anchor="w").pack(fill=tk.X)

        bf = ttk.Frame(main, style="Main.TFrame")
        bf.pack(fill=tk.X, pady=12)
        self.analyze_btn = tk.Button(bf, text="🚀  INICIAR ANÁLISE PROFUNDA",
                                      font=("Segoe UI", 13, "bold"),
                                      bg=self.colors["green"], fg="#fff",
                                      activebackground="#33a043", activeforeground="#fff",
                                      relief="flat", cursor="hand2", padx=40, pady=12,
                                      command=self.start)
        self.analyze_btn.pack(expand=True)

        pf = ttk.Frame(main, style="Main.TFrame")
        pf.pack(fill=tk.X, pady=(0, 10))
        self.progress = tk.DoubleVar(value=0)
        ttk.Progressbar(pf, variable=self.progress, maximum=100,
                        mode='determinate', style="Horizontal.TProgressbar").pack(fill=tk.X, ipady=3)
        self.progress_lbl = ttk.Label(pf, text="Aguardando...", style="Status.TLabel")
        self.progress_lbl.pack(fill=tk.X, pady=(5, 0))

        lc = self._card(main, "📋 Log de Execução")
        self.log = scrolledtext.ScrolledText(lc, height=10, font=("Consolas", 10),
                                              bg=self.colors["bg_input"], fg=self.colors["text"],
                                              insertbackground=self.colors["cyan"],
                                              relief="flat", bd=0, wrap=tk.WORD,
                                              highlightthickness=1,
                                              highlightbackground=self.colors["border"])
        self.log.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log.tag_config("info", foreground=self.colors["blue"])
        self.log.tag_config("ok", foreground=self.colors["green"])
        self.log.tag_config("warn", foreground=self.colors["orange"])
        self.log.tag_config("err", foreground=self.colors["red"])
        self.log.tag_config("hdr", foreground=self.colors["cyan"], font=("Consolas", 10, "bold"))
        self._log("Sistema pronto. Selecione um arquivo para análise.", "info")

    def _build_results_tab(self, parent):
        wrapper = ttk.Frame(parent, style="Main.TFrame")
        wrapper.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        top = ttk.Frame(wrapper, style="Main.TFrame")
        top.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(top, text="📊 Resultados da Análise", style="Title.TLabel").pack(side=tk.LEFT)

        right_frame = ttk.Frame(top, style="Main.TFrame")
        right_frame.pack(side=tk.RIGHT)

        self.save_html_btn = tk.Button(
            right_frame, text="💾  Salvar Relatório Completo",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["purple"], fg="#fff",
            activebackground="#9a6cd4", activeforeground="#fff",
            relief="flat", cursor="hand2", padx=22, pady=10,
            state=tk.DISABLED,
            command=self.save_html_as
        )
        self.save_html_btn.pack(side=tk.RIGHT, padx=(10, 0))

        self.res_score_lbl = tk.Label(right_frame, text="Score: —", font=("Segoe UI", 14, "bold"),
                                       bg=self.colors["bg_dark"], fg=self.colors["text_sec"])
        self.res_score_lbl.pack(side=tk.RIGHT, padx=(0, 15))

        self.res_notebook = ttk.Notebook(wrapper)
        self.res_notebook.pack(fill=tk.BOTH, expand=True)

        # Sub-aba: Info
        frame_info = ttk.Frame(self.res_notebook, style="Main.TFrame")
        self.res_notebook.add(frame_info, text="  📄 Arquivo  ")
        self.res_info = tk.Text(frame_info, font=("Consolas", 10), bg=self.colors["bg_input"],
                                 fg=self.colors["text"], relief="flat", bd=0, wrap=tk.WORD,
                                 highlightthickness=1, highlightbackground=self.colors["border"],
                                 state=tk.DISABLED)
        self.res_info.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        # Sub-aba: Comportamentos
        frame_beh = ttk.Frame(self.res_notebook, style="Main.TFrame")
        self.res_notebook.add(frame_beh, text="  🎯 Comportamentos  ")
        self.res_beh = tk.Text(frame_beh, font=("Consolas", 10), bg=self.colors["bg_input"],
                                fg=self.colors["text"], relief="flat", bd=0, wrap=tk.WORD,
                                highlightthickness=1, highlightbackground=self.colors["border"],
                                state=tk.DISABLED)
        self.res_beh.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.res_beh.tag_config("crit", foreground=self.colors["red"], font=("Consolas", 10, "bold"))
        self.res_beh.tag_config("high", foreground=self.colors["orange"], font=("Consolas", 10, "bold"))
        self.res_beh.tag_config("med", foreground=self.colors["blue"], font=("Consolas", 10, "bold"))
        self.res_beh.tag_config("low", foreground=self.colors["green"])
        self.res_beh.tag_config("ev", foreground=self.colors["cyan"])
        self.res_beh.tag_config("hdr", foreground=self.colors["purple"], font=("Consolas", 11, "bold"))

        # Sub-aba: Imports
        frame_imp = ttk.Frame(self.res_notebook, style="Main.TFrame")
        self.res_notebook.add(frame_imp, text="  📥 Imports  ")
        self.res_tree = ttk.Treeview(frame_imp, columns=("cat", "risk", "desc"),
                                      show="tree headings")
        self.res_tree.heading("#0", text="DLL / Função", anchor=tk.W)
        self.res_tree.heading("cat", text="Categoria", anchor=tk.W)
        self.res_tree.heading("risk", text="Risco", anchor=tk.W)
        self.res_tree.heading("desc", text="Descrição", anchor=tk.W)
        self.res_tree.column("#0", width=320)
        self.res_tree.column("cat", width=110)
        self.res_tree.column("risk", width=100)
        self.res_tree.column("desc", width=450)
        vsb = ttk.Scrollbar(frame_imp, orient=tk.VERTICAL, command=self.res_tree.yview)
        self.res_tree.configure(yscrollcommand=vsb.set)
        self.res_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(8, 0))
        vsb.pack(side=tk.RIGHT, fill=tk.Y, pady=(8, 0))
        self.res_tree.tag_configure("CRÍTICO", foreground=self.colors["red"])
        self.res_tree.tag_configure("ALTO", foreground=self.colors["orange"])
        self.res_tree.tag_configure("MÉDIO", foreground=self.colors["blue"])
        self.res_tree.tag_configure("BAIXO", foreground=self.colors["green"])
        self.res_tree.tag_configure("DESCONHECIDO", foreground=self.colors["text_sec"])

        # Sub-aba: Strings Suspeitas
        frame_str = ttk.Frame(self.res_notebook, style="Main.TFrame")
        self.res_notebook.add(frame_str, text="  🔍 Strings Suspeitas  ")
        self.res_strings = ttk.Treeview(frame_str, columns=("cat", "offset", "type", "value"),
                                         show="headings")
        self.res_strings.heading("cat", text="Categoria", anchor=tk.W)
        self.res_strings.heading("offset", text="Offset", anchor=tk.W)
        self.res_strings.heading("type", text="Tipo", anchor=tk.W)
        self.res_strings.heading("value", text="Valor", anchor=tk.W)
        self.res_strings.column("cat", width=150)
        self.res_strings.column("offset", width=110)
        self.res_strings.column("type", width=70)
        self.res_strings.column("value", width=650)
        vsb2 = ttk.Scrollbar(frame_str, orient=tk.VERTICAL, command=self.res_strings.yview)
        self.res_strings.configure(yscrollcommand=vsb2.set)
        self.res_strings.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(8, 0))
        vsb2.pack(side=tk.RIGHT, fill=tk.Y, pady=(8, 0))

        # ══════════════════════════════════════════════════════
        # Sub-aba: Todas as Strings (COM BUSCA E EXPORTAÇÃO)
        # ══════════════════════════════════════════════════════
        frame_all = ttk.Frame(self.res_notebook, style="Main.TFrame")
        self.res_notebook.add(frame_all, text=f"  📜 Todas as Strings  ")

        # Barra de busca
        search_frame = tk.Frame(frame_all, bg=self.colors["bg_med"])
        search_frame.pack(fill=tk.X, pady=(8, 5))

        tk.Label(search_frame, text="🔍", font=("Segoe UI", 14),
                 bg=self.colors["bg_med"], fg=self.colors["cyan"]).pack(side=tk.LEFT, padx=(10, 5))

        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                      font=("Segoe UI", 11),
                                      bg=self.colors["bg_input"], fg=self.colors["text"],
                                      insertbackground=self.colors["cyan"],
                                      relief="flat", bd=0,
                                      highlightthickness=1,
                                      highlightbackground=self.colors["border"],
                                      highlightcolor=self.colors["blue"])
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_strings())
        self.search_entry.bind("<Return>", lambda e: self._filter_strings())
        self.search_entry.insert(0, "")

        # Placeholder visual
        def _on_focus_in(e):
            if self.search_entry.get() == "Pesquisar (ex: http, admin, kernel32)...":
                self.search_entry.delete(0, tk.END)
                self.search_entry.config(fg=self.colors["text"])

        def _on_focus_out(e):
            if not self.search_entry.get():
                self.search_entry.insert(0, "Pesquisar (ex: http, admin, kernel32)...")
                self.search_entry.config(fg=self.colors["text_sec"])

        self.search_entry.insert(0, "Pesquisar (ex: http, admin, kernel32)...")
        self.search_entry.config(fg=self.colors["text_sec"])
        self.search_entry.bind("<FocusIn>", _on_focus_in)
        self.search_entry.bind("<FocusOut>", _on_focus_out)

        tk.Button(search_frame, text="✖ Limpar", font=("Segoe UI", 9, "bold"),
                  bg=self.colors["red"], fg="#fff", activebackground="#d13c3c",
                  relief="flat", cursor="hand2", padx=12, pady=4,
                  command=self._clear_search).pack(side=tk.LEFT, padx=(0, 5))

        # ============= NOVO BOTÃO DE SALVAR PESQUISA =============
        self.save_search_btn = tk.Button(
            search_frame, text="💾 Salvar Pesquisa HTML", font=("Segoe UI", 9, "bold"),
            bg=self.colors["cyan"], fg="#000", activebackground="#30b5a4",
            relief="flat", cursor="hand2", padx=12, pady=4, state=tk.DISABLED,
            command=self.save_search_html
        )
        self.save_search_btn.pack(side=tk.LEFT, padx=(5, 5))
        # =========================================================

        self.search_result_lbl = tk.Label(search_frame, text="— / —",
                                           font=("Segoe UI", 10, "bold"),
                                           bg=self.colors["bg_med"],
                                           fg=self.colors["cyan"],
                                           padx=12, pady=4)
        self.search_result_lbl.pack(side=tk.RIGHT, padx=(5, 10))

        # Treeview + scrollbars
        tree_frame = tk.Frame(frame_all, bg=self.colors["bg_dark"])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.res_all_strings = ttk.Treeview(tree_frame, columns=("offset", "type", "string"),
                                             show="headings")
        self.res_all_strings.heading("offset", text="Offset", anchor=tk.W)
        self.res_all_strings.heading("type", text="Tipo", anchor=tk.W)
        self.res_all_strings.heading("string", text="String", anchor=tk.W)
        self.res_all_strings.column("offset", width=110)
        self.res_all_strings.column("type", width=70)
        self.res_all_strings.column("string", width=780)

        vsb3 = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.res_all_strings.yview)
        hsb3 = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.res_all_strings.xview)
        self.res_all_strings.configure(yscrollcommand=vsb3.set, xscrollcommand=hsb3.set)

        self.res_all_strings.grid(row=0, column=0, sticky="nsew")
        vsb3.grid(row=0, column=1, sticky="ns")
        hsb3.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Guarda referência das strings (todas) p/ filtro
        self._all_strings_cache = []

    def _card(self, parent, title):
        outer = tk.Frame(parent, bg=self.colors["border"])
        outer.pack(fill=tk.X, pady=(0, 12))
        card = tk.Frame(outer, bg=self.colors["bg_med"])
        card.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        tk.Label(card, text=title, font=("Segoe UI", 11, "bold"),
                 bg=self.colors["bg_med"], fg=self.colors["blue"],
                 anchor="w").pack(fill=tk.X, padx=16, pady=(12, 4))
        inner = tk.Frame(card, bg=self.colors["bg_med"])
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
        return inner

    def _log(self, msg, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        pre = {"info": "ℹ️", "ok": "✅", "warn": "⚠️", "err": "❌", "hdr": "🔷"}.get(tag, "•")
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, f"[{ts}] {pre} {msg}\n", tag)
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def browse_file(self):
        p = filedialog.askopenfilename(
            title="Selecionar arquivo (qualquer tipo)",
            filetypes=[("Binários Windows", "*.dll;*.exe;*.sys;*.ocx"),
                        ("Documentos", "*.pdf;*.doc;*.docx;*.xls;*.xlsx"),
                        ("Arquivos Compactados", "*.zip;*.rar;*.7z"),
                        ("Imagens", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                        ("Todos os arquivos", "*.*")]
        )
        if p:
            self.selected_file.set(p)
            size = os.path.getsize(p)
            sz = DeepAnalyzer._format_size(size)
            self.file_info_lbl.config(text=f"📄 {os.path.basename(p)}  |  📏 {sz}  |  📁 {os.path.dirname(p)}")
            self._log(f"Arquivo selecionado: {os.path.basename(p)} ({sz})", "info")

    def update_prog(self, v, m):
        self.root.after(0, lambda: (self.progress.set(v), self.progress_lbl.config(text=m), self._log(m, "info")))

    def start(self):
        inp = self.selected_file.get().strip()
        if not inp or not os.path.isfile(inp):
            messagebox.showerror("Erro", "Selecione um arquivo válido!")
            return
        if self.is_running:
            return

        self.is_running = True
        self.analyze_btn.config(state=tk.DISABLED, text="⏳  ANALISANDO...", bg=self.colors["orange"])
        self.save_html_btn.config(state=tk.DISABLED)
        self.save_search_btn.config(state=tk.DISABLED)
        self.has_results = False

        self.log.config(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.config(state=tk.DISABLED)
        self._log("=" * 60, "hdr")
        self._log("INICIANDO ANÁLISE PROFUNDA", "hdr")
        self._log("=" * 60, "hdr")
        threading.Thread(target=self._run, args=(inp,), daemon=True).start()

    def save_html_as(self):
        if not self.has_results or self.analyzer is None or not self.analyzer.file_info:
            messagebox.showwarning("Aviso", "Execute uma análise primeiro!")
            return

        fi = self.analyzer.file_info
        base = os.path.splitext(fi['nome'])[0]
        suggested = f"analise_{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        path = filedialog.asksaveasfilename(
            title="Salvar Relatório HTML Completo",
            defaultextension=".html",
            filetypes=[("Arquivo HTML", "*.html"), ("Todos os arquivos", "*.*")],
            initialfile=suggested,
            initialdir=os.path.dirname(fi['caminho'])
        )

        if not path:
            return

        try:
            HTMLReportGenerator.generate(self.analyzer, path)
            self.last_report_path = path
            self._log(f"💾 HTML salvo em: {path}", "ok")

            if messagebox.askyesno(
                "✅ Sucesso",
                f"Relatório salvo com sucesso!\n\n"
                f"📁 Arquivo: {os.path.basename(path)}\n"
                f"📂 Local: {os.path.dirname(path)}\n\n"
                f"Deseja abrir no navegador agora?"
            ):
                webbrowser.open(Path(path).resolve().as_uri())
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar HTML:\n\n{str(e)}")
            self._log(f"❌ Erro ao salvar HTML: {e}", "err")

    # ================= NOVO: Método de Salvar Pesquisa =================
    def save_search_html(self):
        if not self.has_results or not self.analyzer or not self.analyzer.file_info:
            messagebox.showwarning("Aviso", "Nenhuma análise disponível.")
            return

        query = self.search_var.get().strip()
        if query == "Pesquisar (ex: http, admin, kernel32)...":
            query = ""

        if not query:
            if not messagebox.askyesno("Aviso", "A caixa de busca está vazia, isso exportará TODAS as strings encontradas. Deseja continuar?"):
                return

        # Filtrar o cache com base no termo
        q_lower = query.lower()
        filtered = []
        for s in self._all_strings_cache:
            text = (s.get("string", s.get("value", "")) or "").lower()
            if not q_lower or q_lower in text:
                filtered.append(s)

        if not filtered:
            messagebox.showwarning("Nenhum Resultado", f"Não há resultados para o termo '{query}'. Nenhum arquivo foi salvo.")
            return

        fi = self.analyzer.file_info
        base = os.path.splitext(fi['nome'])[0]
        q_safe = re.sub(r'[^\w\-]', '_', query) if query else "todas"
        suggested = f"pesquisa_{q_safe}_{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        path = filedialog.asksaveasfilename(
            title="Salvar Resultado da Pesquisa HTML",
            defaultextension=".html",
            filetypes=[("Arquivo HTML", "*.html"), ("Todos os arquivos", "*.*")],
            initialfile=suggested,
            initialdir=os.path.dirname(fi['caminho'])
        )

        if not path:
            return

        try:
            HTMLReportGenerator.generate_search(self.analyzer, query, filtered, path)
            self._log(f"💾 Relatório de pesquisa salvo em: {path} ({len(filtered)} itens)", "ok")

            if messagebox.askyesno("✅ Sucesso", f"Pesquisa HTML salva com sucesso!\n\nForam exportados {len(filtered)} resultados.\n\nDeseja abrir o arquivo agora?"):
                webbrowser.open(Path(path).resolve().as_uri())
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar pesquisa para HTML:\n\n{str(e)}")
            self._log(f"❌ Erro ao exportar pesquisa: {e}", "err")

    # ═════════════════════════════════════════════════════════
    # BUSCA / FILTRO DE STRINGS
    # ═════════════════════════════════════════════════════════
    def _filter_strings(self):
        """Filtra as strings exibidas na Treeview conforme o texto digitado."""
        q = self.search_var.get().strip().lower()
        if q == "pesquisar (ex: http, admin, kernel32)...":
            q = ""

        # Limpa a tree
        self.res_all_strings.delete(*self.res_all_strings.get_children())

        total = len(self._all_strings_cache)
        visible = 0

        for s in self._all_strings_cache:
            text = (s.get("string", "") or "").lower()
            if not q or q in text:
                self.res_all_strings.insert("", tk.END,
                                             values=(s["hex_offset"], s["type"], s["string"][:500]))
                visible += 1
                if visible >= 10000:  # limite p/ não travar GUI
                    break

        if q:
            if visible == 0:
                self.search_result_lbl.config(text=f"0 / {total:,}", fg=self.colors["red"])
            else:
                self.search_result_lbl.config(text=f"{visible:,} / {total:,}", fg=self.colors["cyan"])
        else:
            self.search_result_lbl.config(text=f"{visible:,} / {total:,}", fg=self.colors["cyan"])

    def _clear_search(self):
        """Limpa a busca e reexibe tudo."""
        self.search_entry.delete(0, tk.END)
        self.search_entry.config(fg=self.colors["text"])
        self.search_entry.focus()
        self._filter_strings()

    # ═════════════════════════════════════════════════════════
    # POPULA RESULTADOS
    # ═════════════════════════════════════════════════════════
    def _populate_results(self):
        an = self.analyzer
        fi = an.file_info
        pe = an.pe_parser.pe_info if (an.pe_parser and an.pe_parser.is_pe) else {}
        score = an.calculate_risk_score()

        color = (self.colors["red"] if score >= 70 else
                 self.colors["orange"] if score >= 40 else
                 self.colors["blue"] if score > 0 else self.colors["green"])
        self.res_score_lbl.config(text=f"Score: {score}/100", fg=color)

        info_txt = (
            f"{'═'*62}\n  📄 INFORMAÇÕES DO ARQUIVO\n{'═'*62}\n\n"
            f"  Nome ..........: {fi['nome']}\n"
            f"  Tipo (PE) .....: {pe.get('file_type', 'N/A (não-PE)')}\n"
            f"  Detecção ......: {fi.get('detected_type', 'N/A')}\n"
            f"  Arquitetura ...: {pe.get('architecture', 'N/A')}\n"
            f"  Tamanho .......: {fi['tamanho_fmt']} ({fi['tamanho']:,} bytes)\n"
            f"  Entry Point ...: {pe.get('entry_point', 'N/A')}\n"
            f"  Image Base ....: {pe.get('image_base', 'N/A')}\n"
            f"  Compilado .....: {pe.get('timestamp', 'N/A')}\n"
            f"  Criado ........: {fi['criado']}\n"
            f"  Modificado ....: {fi['modificado']}\n"
            f"  Caminho .......: {fi['caminho']}\n\n"
            f"  MD5 ...........: {fi['md5']}\n"
            f"  SHA-1 .........: {fi['sha1']}\n"
            f"  SHA-256 .......: {fi['sha256']}\n"
        )

        if an.pe_parser and an.pe_parser.sections:
            info_txt += f"\n{'═'*62}\n  📦 SEÇÕES DO PE\n{'═'*62}\n\n"
            info_txt += f"  {'Nome':<10} {'VAddr':<12} {'VSize':>12} {'RawSize':>12}  R W X\n"
            info_txt += f"  {'-'*10} {'-'*12} {'-'*12} {'-'*12}  -----\n"
            for s in an.pe_parser.sections:
                r = "R" if s["characteristics"] & 0x40000000 else "-"
                w = "W" if s["characteristics"] & 0x80000000 else "-"
                x = "X" if s["characteristics"] & 0x20000000 else "-"
                info_txt += (f"  {s['name']:<10} 0x{s['virtual_address']:08X} "
                             f"{s['virtual_size']:>12,} {s['raw_size']:>12,}  {r} {w} {x}\n")

        if an.pe_parser and an.pe_parser.exports:
            info_txt += f"\n{'═'*62}\n  📤 EXPORTS ({len(an.pe_parser.exports)})\n{'═'*62}\n\n"
            for i, e in enumerate(an.pe_parser.exports[:100], 1):
                info_txt += f"  {i:>4}. {e}\n"
            if len(an.pe_parser.exports) > 100:
                info_txt += f"  ... e mais {len(an.pe_parser.exports) - 100}\n"

        self.res_info.config(state=tk.NORMAL)
        self.res_info.delete("1.0", tk.END)
        self.res_info.insert(tk.END, info_txt)
        self.res_info.config(state=tk.DISABLED)

        self.res_beh.config(state=tk.NORMAL)
        self.res_beh.delete("1.0", tk.END)
        if an.behaviors:
            self.res_beh.insert(tk.END, f"🎯 {len(an.behaviors)} comportamento(s) identificado(s)\n\n", "hdr")
            tag_map = {"CRÍTICO": "crit", "ALTO": "high", "MÉDIO": "med", "BAIXO": "low"}
            for b in an.behaviors:
                t = tag_map.get(b["risk"], "med")
                self.res_beh.insert(tk.END, f"  {b['icon']} [{b['risk']}] {b['name']}\n", t)
                self.res_beh.insert(tk.END, f"      {b['description']}\n", "ev")
                self.res_beh.insert(tk.END, f"      Evidências: {', '.join(b['evidence'])}\n\n")
        else:
            self.res_beh.insert(tk.END, "✅ Nenhum comportamento suspeito identificado.", "low")
        self.res_beh.config(state=tk.DISABLED)

        self.res_tree.delete(*self.res_tree.get_children())
        if an.pe_parser and an.pe_parser.imports:
            for dll, funcs in sorted(an.pe_parser.imports.items()):
                dll_node = self.res_tree.insert("", tk.END, text=f"📚 {dll} ({len(funcs)})",
                                                 values=("", "", ""))
                for f in funcs:
                    info = API_KNOWLEDGE_BASE.get(f, None)
                    if info:
                        cat, risk, desc = info["cat"], info["risk"], info["desc"]
                    else:
                        cat, risk, desc = "Outros", "DESCONHECIDO", "Função não catalogada"
                    self.res_tree.insert(dll_node, tk.END, text=f"    {f}",
                                          values=(cat, risk, desc), tags=(risk,))
        else:
            self.res_tree.insert("", tk.END, text="⚠️ Nenhuma DLL importada (arquivo não-PE ou sem imports)",
                                  values=("", "", ""))

        self.res_strings.delete(*self.res_strings.get_children())
        total_susp = 0
        for cat, data in an.strings_analysis.items():
            for fnd in data["findings"]:
                total_susp += 1
                self.res_strings.insert("", tk.END,
                                         values=(cat, fnd["offset"], fnd["type"], fnd["value"]))
        self.res_notebook.tab(3, text=f"  🔍 Strings Suspeitas ({total_susp})  ")

        # Todas as Strings — cache + populate
        self._all_strings_cache = an.all_strings[:]
        self.res_all_strings.delete(*self.res_all_strings.get_children())
        for s in self._all_strings_cache[:10000]:
            self.res_all_strings.insert("", tk.END,
                                         values=(s["hex_offset"], s["type"], s["string"][:500]))
        self.res_notebook.tab(4, text=f"  📜 Todas as Strings ({len(an.all_strings)})  ")

        total = len(an.all_strings)
        shown = min(total, 10000)
        self.search_result_lbl.config(text=f"{shown:,} / {total:,}", fg=self.colors["cyan"])

        # Habilita botões
        self.has_results = True
        self.save_html_btn.config(state=tk.NORMAL)
        self.save_search_btn.config(state=tk.NORMAL)

    def _run(self, inp):
        try:
            self.analyzer.analyze(inp, progress_cb=self.update_prog)

            stats = self.analyzer.imports_analysis["stats"]
            fi = self.analyzer.file_info

            self.root.after(0, lambda: self._log(f"\n📄 ARQUIVO: {fi['nome']} ({fi['tamanho_fmt']})", "hdr"))
            self.root.after(0, lambda: self._log(f"  Tipo detectado: {fi.get('detected_type','N/A')}", "info"))

            self.root.after(0, lambda: self._log("\n📊 ESTATÍSTICAS:", "hdr"))
            self.root.after(0, lambda: self._log(f"  DLLs importadas: {stats['total_dlls']}", "info"))
            self.root.after(0, lambda: self._log(f"  Funções totais: {stats['total_functions']}", "info"))
            self.root.after(0, lambda: self._log(f"  APIs conhecidas: {stats['known']}", "ok"))
            self.root.after(0, lambda: self._log(f"  APIs desconhecidas: {stats['unknown']}", "warn"))
            self.root.after(0, lambda: self._log(f"  Strings extraídas: {len(self.analyzer.all_strings)}", "info"))

            self.root.after(0, lambda: self._log("\n🎯 COMPORTAMENTOS DETECTADOS:", "hdr"))
            for b in self.analyzer.behaviors:
                tag = "err" if b["risk"] == "CRÍTICO" else "warn" if b["risk"] == "ALTO" else "info"
                self.root.after(0, lambda bb=b, t=tag: self._log(f"  {bb['icon']} [{bb['risk']}] {bb['name']}", t))

            self.root.after(0, lambda: self._log("\n📚 DLLs IMPORTADAS:", "hdr"))
            pe_imports = {}
            if self.analyzer.pe_parser is not None:
                pe_imports = getattr(self.analyzer.pe_parser, "imports", {}) or {}
            if pe_imports:
                for dll, funcs in pe_imports.items():
                    self.root.after(0, lambda d=dll, n=len(funcs): self._log(f"  📦 {d} → {n} funções", "info"))
            else:
                self.root.after(0, lambda: self._log("  ⚠️ Nenhuma DLL importada — análise limitada a strings/padrões.", "warn"))

            total_susp = sum(len(d["findings"]) for d in self.analyzer.strings_analysis.values())
            if total_susp:
                self.root.after(0, lambda: self._log(f"\n🔍 STRINGS SUSPEITAS: {total_susp} encontrado(s)", "warn"))
                for cat, data in self.analyzer.strings_analysis.items():
                    if data["findings"]:
                        self.root.after(0, lambda c=cat, n=len(data["findings"]):
                                        self._log(f"  {c}: {n}", "warn"))

            score = self.analyzer.calculate_risk_score()
            tag = "err" if score >= 70 else "warn" if score >= 40 else "ok" if score == 0 else "info"
            self.root.after(0, lambda: self._log(f"\n🎯 SCORE DE RISCO: {score}/100", tag))

            self.root.after(0, self._populate_results)

            self.update_prog(100, "✅ Análise concluída!")
            self.root.after(0, lambda: self._log("\n✅ ANÁLISE CONCLUÍDA!", "ok"))
            self.root.after(0, lambda: self._log("📊 Veja a aba 'Resultados' para todos os detalhes.", "hdr"))
            self.root.after(0, lambda: self._log("🔍 Use o campo de busca em '📜 Todas as Strings' para pesquisar!", "info"))
            self.root.after(0, lambda: self._log("💾 Clique em 'Salvar HTML' na aba Resultados para gerar o relatório.", "info"))

            self.root.after(200, lambda: self._offer_save())

        except Exception as e:
            import traceback
            err = traceback.format_exc()
            self.root.after(0, lambda: self._log(f"ERRO: {str(e)}\n{err}", "err"))
            self.root.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.root.after(0, self._reset)

    def _offer_save(self):
        if messagebox.askyesno(
            "✅ Análise Concluída",
            "A análise foi concluída com sucesso!\n\n"
            "Veja os resultados na aba '📊 Resultados'.\n\n"
            "Deseja salvar o relatório HTML agora?"
        ):
            self.notebook.select(1)
            self.save_html_as()

    def _reset(self):
        self.is_running = False
        self.analyze_btn.config(state=tk.NORMAL, text="🚀  INICIAR ANÁLISE PROFUNDA", bg=self.colors["green"])

    def run(self):
        self.root.mainloop()


def main():
    AnalyzerGUI().run()


if __name__ == "__main__":
    main()
