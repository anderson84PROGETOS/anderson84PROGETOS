import os
import sys
import hashlib
import threading
import time
import platform
import subprocess
import webbrowser
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import requests
import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog

# ═════════════════════════════════════════════════════════════
# CONFIGURAÇÕES (ajustado para chave gratuita do VirusTotal)
# ═════════════════════════════════════════════════════════════
VIRUSTOTAL_API_KEY = ""

VIRUSTOTAL_API_URL = "https://www.virustotal.com/api/v3/files/{hash}"
VIRUSTOTAL_WEB_URL = "https://www.virustotal.com/gui/file/{hash}/detection"
AUTO_REFRESH_INTERVAL = 3000   # ms
VT_RATE_LIMIT_DELAY = 16       # 16s entre chamadas (cota gratuita: 4/min)
VT_TIMEOUT = 30
MAX_WORKERS = 1                # apenas 1 worker


# ═════════════════════════════════════════════════════════════
# CACHE LOCAL
# ═════════════════════════════════════════════════════════════
VT_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd(),
    '.vt_cache.json'
)

class VTCache:
    def __init__(self, cache_file=VT_CACHE_FILE):
        self.cache_file = cache_file
        self.cache = self._load()
    
    def _load(self):
        try:
            if os.path.isfile(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                now = time.time()
                valid = {k: v for k, v in data.items() if (now - v.get('timestamp', 0)) < 86400}
                return valid
        except Exception:
            pass
        return {}
    
    def _save(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except Exception:
            pass
    
    def get(self, file_hash):
        entry = self.cache.get(file_hash)
        if entry and entry.get('result'):
            return entry['result']
        return None
    
    def set(self, file_hash, result):
        self.cache[file_hash] = {'result': result, 'timestamp': time.time()}
        self._save()
    
    def size(self):
        return len(self.cache)


# ═════════════════════════════════════════════════════════════
# FUNÇÕES CORE
# ═════════════════════════════════════════════════════════════
def get_file_hash(filepath):
    if not filepath or not os.path.isfile(filepath):
        return None
    try:
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (PermissionError, OSError):
        return None


def query_virustotal_api(file_hash, api_key):
    if not api_key or not file_hash:
        return None
    url = VIRUSTOTAL_API_URL.format(hash=file_hash)
    headers = {"x-apikey": api_key}
    try:
        resp = requests.get(url, headers=headers, timeout=VT_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            attrs = data.get("data", {}).get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            return {
                'malicious': stats.get('malicious', 0),
                'suspicious': stats.get('suspicious', 0),
                'undetected': stats.get('undetected', 0),
                'harmless': stats.get('harmless', 0),
                'timeout': stats.get('timeout', 0),
                'total': sum(stats.values()) if stats else 0
            }
        elif resp.status_code == 404:
            return {'malicious': 0, 'suspicious': 0, 'undetected': 0,
                    'harmless': 0, 'timeout': 0, 'total': 0, 'not_found': True}
        elif resp.status_code == 429:
            return {'rate_limited': True}
        else:
            return None
    except requests.exceptions.Timeout:
        return {'timeout_error': True}
    except Exception:
        return None


def format_vt_result(stats):
    if not stats:
        return ("...", False, False)
    if stats.get('rate_limited'):
        return ("⏳", False, False)
    if stats.get('timeout_error'):
        return ("⌛", False, False)
    malicious = stats.get('malicious', 0)
    suspicious = stats.get('suspicious', 0)
    total = stats.get('total', 0)
    if stats.get('not_found'):
        return ("N/A", False, True)
    if total == 0:
        return ("?", False, False)
    display = f"{malicious}/{total}"
    if malicious > 0 or suspicious > 0:
        return (display, True, False)
    else:
        return (display, False, True)


def open_virustotal_web(file_hash):
    if file_hash:
        webbrowser.open(VIRUSTOTAL_WEB_URL.format(hash=file_hash))


def agora_br():
    return datetime.now().strftime('%d/%m/%Y %H:%M:%S')


# ═════════════════════════════════════════════════════════════
# COLLECTOR DE PROCESSOS
# ═════════════════════════════════════════════════════════════
class ProcessCollector:
    @staticmethod
    def collect():
        timestamp_coleta = agora_br()
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent',
                                          'memory_percent', 'memory_info',
                                          'username', 'create_time', 'status']):
            try:
                pinfo = proc.info
                if pinfo['exe'] and os.path.isfile(pinfo['exe']):
                    file_hash = get_file_hash(pinfo['exe'])
                else:
                    file_hash = None

                cpu = pinfo['cpu_percent'] if pinfo['cpu_percent'] else 0.0
                mem_info = pinfo['memory_info']
                mem_mb = mem_info.rss / (1024 * 1024) if mem_info else 0
                ctime = pinfo['create_time']
                ctime_str = datetime.fromtimestamp(ctime).strftime('%H:%M:%S') if ctime else "N/A"

                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'] or "Unknown",
                    'exe': pinfo['exe'] or "",
                    'cpu': f"{cpu:.1f}",
                    'cpu_raw': cpu,
                    'mem': f"{mem_mb:.1f} MB",
                    'mem_raw': mem_mb,
                    'user': pinfo['username'] or "N/A",
                    'started': ctime_str,
                    'status': pinfo['status'] or "N/A",
                    'hash': file_hash or "",
                    'coleta': timestamp_coleta,
                    'vt_display': "",
                    'vt_malicious': False,
                    'vt_clean': False,
                    'vt_stats': None,
                    'has_hash': bool(file_hash),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                continue

        processes.sort(key=lambda p: p['mem_raw'], reverse=True)
        return processes


# ═════════════════════════════════════════════════════════════
# SCANNER VIRUSTOTAL
# ═════════════════════════════════════════════════════════════
class VTScanner:
    def __init__(self, api_key, cache=None):
        self.api_key = api_key
        self.cache = cache or VTCache()
        self._stop_flag = threading.Event()
        self._scan_lock = threading.Lock()
        self._scanning = False
    
    @property
    def is_scanning(self):
        return self._scanning
    
    def update_api_key(self, new_key):
        self.api_key = new_key
    
    def stop(self):
        self._stop_flag.set()
    
    def scan_processes(self, processes, progress_callback=None, done_callback=None):
        if not self._scan_lock.acquire(blocking=False):
            return
        
        try:
            self._scanning = True
            self._stop_flag.clear()
            
            if not self.api_key or not processes:
                return
            
            to_scan = []
            for p in processes:
                if p['hash'] and (not p['vt_display'] or p['vt_display'] in ("...", "🔍")):
                    cached = self.cache.get(p['hash'])
                    if cached:
                        display, malicious, clean = format_vt_result(cached)
                        p['vt_display'] = display
                        p['vt_malicious'] = malicious
                        p['vt_clean'] = clean
                        p['vt_stats'] = cached
                    else:
                        to_scan.append(p)
            
            if not to_scan:
                return
            
            total = len(to_scan)
            completed = [0]
            
            executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
            futures = {}
            
            try:
                for p in to_scan:
                    if self._stop_flag.is_set():
                        break
                    future = executor.submit(self._scan_single, p)
                    futures[future] = p
                    time.sleep(VT_RATE_LIMIT_DELAY)
                
                for future in as_completed(futures):
                    if self._stop_flag.is_set():
                        break
                    p = futures[future]
                    completed[0] += 1
                    
                    try:
                        result = future.result(timeout=VT_TIMEOUT + 5)
                        if result:
                            display, malicious, clean = format_vt_result(result)
                            p['vt_display'] = display
                            p['vt_malicious'] = malicious
                            p['vt_clean'] = clean
                            p['vt_stats'] = result
                            self.cache.set(p['hash'], result)
                    except Exception:
                        pass
                    
                    if progress_callback:
                        try:
                            progress_callback(completed[0], total)
                        except Exception:
                            pass
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
        finally:
            self._scanning = False
            self._scan_lock.release()
            if done_callback:
                try:
                    done_callback()
                except Exception:
                    pass
    
    def _scan_single(self, proc):
        if not proc or not proc.get('hash'):
            return None
        try:
            return query_virustotal_api(proc['hash'], self.api_key)
        except Exception:
            return None


# ═════════════════════════════════════════════════════════════
# INTERFACE GRÁFICA
# ═════════════════════════════════════════════════════════════
class ProcessExplorerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Process Explorer")
        self.root.geometry("1400x680")
        self.root.state('zoomed')
        self.root.minsize(1200, 500)

        self.colors = {
            'bg_dark': '#1e1e1e',
            'bg_medium': '#2d2d2d',
            'bg_light': '#3c3c3c',
            'fg': '#ffffff',
            'fg_dim': '#aaaaaa',
            'accent': '#00bcd4',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'success': '#2ecc71',
            'info': '#3498db',
            'row_even': '#252526',
            'row_odd': '#2d2d30',
            'header_bg': '#333333',
        }

        style = ttk.Style(root)
        style.theme_use('clam')

        # ── ESTILO DO CHECKBOX VT (ttk) ──
        style.configure('VT.TCheckbutton',
            foreground=self.colors['warning'],
            background=self.colors['bg_medium'],
            font=('Segoe UI', 9))
        style.map('VT.TCheckbutton',
            foreground=[('disabled', self.colors['fg_dim']), ('!disabled', self.colors['warning'])],
            background=[('disabled', self.colors['bg_medium']), ('!disabled', self.colors['bg_medium'])])

        self.mono_font = font.Font(family="Consolas", size=9)
        self.mono_bold = font.Font(family="Consolas", size=9, weight="bold")
        self.header_font = font.Font(family="Segoe UI", size=10, weight="bold")

        self._setup_dark_theme(style)

        main_frame = tk.Frame(root, bg=self.colors['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.processes = []
        self.auto_refresh = tk.BooleanVar(value=True)
        self.vt_enabled = tk.BooleanVar(value=False)
        
        self.api_key_loaded = False
        self.vt_scanner = None
        self.vt_cache = None
        self.lbl_cache = None
        
        api_key = self._try_load_api_key_from_file()
        self._init_vt_system(api_key)

        self._build_toolbar(main_frame, style)
        self._build_treeview(main_frame)
        self._build_statusbar(main_frame)
        self._build_context_menu()
        self._bind_events()

        self.refresh_processes()
        self._schedule_auto_refresh()
        self._update_clock_loop()

    # ═══════════════════════════════════════════════════════
    # NOVA JANELA PERSONALIZADA (maior, redimensionável)
    # ═══════════════════════════════════════════════════════
    def custom_askyesno(self, title, message):
        """Janela Toplevel personalizada que substitui messagebox.askyesno.
        Retorna True (Sim) ou False (Não)."""
        result = [False]  # mutable para capturar dentro dos callbacks

        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("660x500")
        win.minsize(500, 300)
        win.configure(bg=self.colors['bg_dark'])
        win.transient(self.root)  # mantém sobre a janela principal
        win.grab_set()            # modal
        win.focus_set()

        # Centraliza em relação à janela principal
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 325
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 200
        win.geometry(f"+{x}+{y}")

        # Frame principal com padding
        frame = tk.Frame(win, bg=self.colors['bg_dark'], padx=20, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # Área de texto com scrollbar
        text_frame = tk.Frame(frame, bg=self.colors['bg_dark'])
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        txt = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg=self.colors['bg_medium'],
            fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            relief=tk.FLAT,
            borderwidth=0,
            padx=12,
            pady=10,
            highlightthickness=1,
            highlightbackground=self.colors['bg_light'],
            highlightcolor=self.colors['accent']
        )
        txt.insert('1.0', message)
        txt.config(state=tk.DISABLED)  # somente leitura

        scrollbar = tk.Scrollbar(text_frame, command=txt.yview, bg=self.colors['bg_light'])
        txt.config(yscrollcommand=scrollbar.set)

        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Frame dos botões
        btn_frame = tk.Frame(frame, bg=self.colors['bg_dark'])
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        def on_sim():
            result[0] = True
            win.destroy()

        def on_nao():
            result[0] = False
            win.destroy()

        btn_nao = tk.Button(
            btn_frame,
            text="❌  Não",
            bg=self.colors['bg_light'],
            fg=self.colors['fg'],
            relief=tk.FLAT,
            padx=20,
            pady=6,
            font=('Segoe UI', 10),
            activebackground=self.colors['danger'],
            activeforeground='#ffffff',
            cursor='hand2',
            command=on_nao
        )
        btn_nao.pack(side=tk.RIGHT, padx=(8, 0))

        btn_sim = tk.Button(
            btn_frame,
            text="✅  Sim",
            bg=self.colors['success'],
            fg='#000000',
            relief=tk.FLAT,
            padx=20,
            pady=6,
            font=('Segoe UI', 10, 'bold'),
            activebackground='#27ae60',
            activeforeground='#000000',
            cursor='hand2',
            command=on_sim
        )
        btn_sim.pack(side=tk.RIGHT)

        # Tecla Enter = Sim, Esc = Não
        win.bind('<Return>', lambda e: on_sim())
        win.bind('<Escape>', lambda e: on_nao())

        # Fecha com X também como Não
        win.protocol("WM_DELETE_WINDOW", on_nao)

        win.wait_window()
        return result[0]

    def _try_load_api_key_from_file(self, filepath=None):
        if filepath is None:
            script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
            candidates = [
                os.path.join(script_dir, 'API.txt'),
                os.path.join(script_dir, 'api.txt'),
                os.path.join(script_dir, 'apikey.txt'),
                os.path.join(script_dir, '.vt_api_key'),
            ]
            for c in candidates:
                if os.path.isfile(c):
                    filepath = c
                    break
        
        if filepath and os.path.isfile(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    key = f.read().strip().strip('"').strip("'").strip()
                if key and len(key) > 10 and not key.startswith('#'):
                    return key
            except Exception:
                pass
        return None

    def _init_vt_system(self, api_key):
        if api_key:
            self.vt_cache = VTCache()
            self.vt_scanner = VTScanner(api_key, self.vt_cache)
            self.api_key_loaded = True
            self.vt_enabled.set(True)
        else:
            self.vt_scanner = None
            self.vt_cache = None
            self.api_key_loaded = False
            self.vt_enabled.set(False)

    def _load_api_key_from_dialog(self):
        filepath = filedialog.askopenfilename(
            title="Selecionar arquivo com a API Key do VirusTotal",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
            initialfile="API.txt"
        )
        if not filepath:
            return
        
        api_key = self._try_load_api_key_from_file(filepath)
        
        if not api_key:
            messagebox.showerror(
                "Erro",
                f"Não foi possível ler uma chave de API válida de:\n{filepath}\n\n"
                "O arquivo deve conter apenas a chave (ex: abcdef123456...)"
            )
            return
        
        self._init_vt_system(api_key)
        
        if self.processes:
            for p in self.processes:
                p['vt_display'] = ""
                p['vt_malicious'] = False
                p['vt_clean'] = False
                p['vt_stats'] = None
            self._run_vt_scan()
        
        self.chk_vt.state(['!disabled'])
        self.chk_vt.configure(style='VT.TCheckbutton')
        
        if self.lbl_cache is not None:
            self.lbl_cache.config(text=f"Cache: {self.vt_cache.size()}" if self.vt_cache else "Cache: 0")
        
        if hasattr(self, 'lbl_api_status'):
            self.lbl_api_status.config(
                text=f"🔑 API: {api_key[:12]}...{api_key[-4:]}",
                fg=self.colors['success']
            )
        
        self.status_bar.config(
            text=f"✅ API Key carregada de {os.path.basename(filepath)} | 🔬 VT Auto Scan ativado"
        )

    def _setup_dark_theme(self, style):
        style.configure('TFrame', background=self.colors['bg_dark'])
        style.configure('TLabel', background=self.colors['bg_dark'], foreground=self.colors['fg'])
        style.configure('TButton', background=self.colors['bg_medium'], foreground=self.colors['fg'],
                         borderwidth=0, focuscolor='none')
        style.map('TButton', background=[('active', self.colors['accent']), ('pressed', self.colors['bg_light'])])
        style.configure('TCheckbutton', background=self.colors['bg_dark'], foreground=self.colors['fg'])
        style.map('TCheckbutton', background=[('active', self.colors['bg_dark'])])
        style.configure('Treeview', background=self.colors['row_odd'], foreground=self.colors['fg'],
                         fieldbackground=self.colors['row_odd'], borderwidth=0)
        style.map('Treeview', background=[('selected', self.colors['accent'])], foreground=[('selected', '#000000')])
        style.configure('Treeview.Heading', background=self.colors['header_bg'], foreground=self.colors['fg'], relief='flat')
        style.map('Treeview.Heading', background=[('active', self.colors['bg_light'])])
        style.configure('TEntry', fieldbackground=self.colors['bg_medium'], foreground=self.colors['fg'], borderwidth=0)
        style.configure('TSeparator', background=self.colors['bg_light'])

    # ── TOOLBAR ──────────────────────────────────────────────
    def _build_toolbar(self, parent, style):
        toolbar_bg = self.colors['bg_medium']
        toolbar = tk.Frame(parent, bg=toolbar_bg, height=44)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        toolbar.pack_propagate(False)

        self.lbl_datetime = tk.Label(toolbar, text=agora_br(), bg=toolbar_bg, fg=self.colors['accent'],
                                      font=font.Font(family="Consolas", size=10, weight="bold"))
        self.lbl_datetime.pack(side=tk.LEFT, padx=(12, 18))

        tk.Frame(toolbar, bg=self.colors['bg_light'], width=1, height=26).pack(side=tk.LEFT, padx=4, fill=tk.Y)

        self.btn_refresh = tk.Button(toolbar, text="⟳ Refresh", bg=self.colors['bg_light'], fg=self.colors['fg'],
                                      relief=tk.FLAT, padx=10, pady=2, activebackground=self.colors['accent'],
                                      activeforeground='#000000', cursor='hand2', command=self.refresh_processes)
        self.btn_refresh.pack(side=tk.LEFT, padx=(10, 6))

        self.chk_auto = tk.Checkbutton(toolbar, text="Auto (3s)", variable=self.auto_refresh, bg=toolbar_bg,
                                        fg=self.colors['fg'], selectcolor=self.colors['bg_medium'],
                                        activebackground=toolbar_bg, activeforeground=self.colors['fg'])
        self.chk_auto.pack(side=tk.LEFT, padx=6)

        self.btn_load_api = tk.Button(
            toolbar,
            text="📂 Carregar API",
            bg=self.colors['info'],
            fg='#ffffff',
            relief=tk.FLAT,
            padx=10,
            pady=2,
            activebackground=self.colors['accent'],
            activeforeground='#000000',
            cursor='hand2',
            font=('Segoe UI', 9, 'bold'),
            command=self._load_api_key_from_dialog
        )
        self.btn_load_api.pack(side=tk.LEFT, padx=6)

        if self.api_key_loaded:
            key_snippet = self.vt_scanner.api_key[:12] + "..." + self.vt_scanner.api_key[-4:] if self.vt_scanner and self.vt_scanner.api_key else ""
            self.lbl_api_status = tk.Label(
                toolbar,
                text=f"🔑 API: {key_snippet}",
                bg=toolbar_bg,
                fg=self.colors['success'],
                font=('Segoe UI', 8, 'italic')
            )
        else:
            self.lbl_api_status = tk.Label(
                toolbar,
                text="🔑 API: Não carregada",
                bg=toolbar_bg,
                fg=self.colors['fg_dim'],
                font=('Segoe UI', 8, 'italic')
            )
        self.lbl_api_status.pack(side=tk.LEFT, padx=6)

        self.chk_vt = ttk.Checkbutton(
            toolbar,
            text="🔬 VT Auto",
            variable=self.vt_enabled,
            style='VT.TCheckbutton',
            command=self._toggle_vt_scan
        )
        if not self.api_key_loaded:
            self.chk_vt.state(['disabled'])
        self.chk_vt.pack(side=tk.LEFT, padx=6)

        cache_text = f"Cache: {self.vt_cache.size()}" if self.vt_cache else "Cache: 0"
        self.lbl_cache = tk.Label(
            toolbar,
            text=cache_text,
            bg=toolbar_bg,
            fg=self.colors['fg_dim'],
            font=('Segoe UI', 8)
        )
        self.lbl_cache.pack(side=tk.LEFT, padx=2)

        tk.Frame(toolbar, bg=self.colors['bg_light'], width=1, height=26).pack(side=tk.LEFT, padx=4, fill=tk.Y)

        tk.Label(toolbar, text="🔍", bg=toolbar_bg, fg=self.colors['fg'], font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(6, 2))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *a: self._filter_processes())
        self.entry_search = tk.Entry(toolbar, textvariable=self.search_var, bg=self.colors['bg_dark'], fg=self.colors['fg'],
                                      insertbackground=self.colors['fg'], relief=tk.FLAT, width=22, bd=4, font=('Segoe UI', 9))
        self.entry_search.pack(side=tk.LEFT, padx=(0, 4), ipady=2)

        tk.Button(toolbar, text="✕", bg=self.colors['bg_light'], fg=self.colors['fg_dim'], relief=tk.FLAT,
                  width=2, activebackground=self.colors['danger'], activeforeground='#ffffff',
                  command=lambda: self.search_var.set("")).pack(side=tk.LEFT)

        tk.Frame(toolbar, bg=self.colors['bg_light'], width=1, height=26).pack(side=tk.LEFT, padx=8, fill=tk.Y)

        self.btn_save = tk.Button(toolbar, text="💾 Salvar (.txt)", bg=self.colors['success'], fg='#000000',
                                   relief=tk.FLAT, padx=2, pady=1, activebackground='#27ae60', activeforeground='#000000',
                                   cursor='hand2', font=('Segoe UI', 9, 'bold'), command=self.save_results_txt)
        self.btn_save.pack(side=tk.LEFT, padx=(0, 1))

        tk.Label(toolbar, bg=toolbar_bg, text="").pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_total = tk.Label(toolbar, text="Processos: 0", bg=toolbar_bg, fg=self.colors['fg'], font=('Segoe UI', 9))
        self.lbl_total.pack(side=tk.RIGHT, padx=25)

    # ── TREEVIEW ────────────────────────────────────────────
    def _build_treeview(self, parent):
        container = tk.Frame(parent, bg=self.colors['bg_dark'])
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        columns = ('pid', 'name', 'cpu', 'mem', 'user', 'started', 'status', 'coleta', 'sha256', 'exe', 'vt')
        self.tree = ttk.Treeview(container, columns=columns, show='headings', selectmode='browse', style='Treeview')

        col_defs = [
            ('pid',     'PID',             70,  tk.CENTER),
            ('name',    'Process Name',    300, tk.W),
            ('cpu',     'CPU %',           65,  tk.CENTER),
            ('mem',     'Memory',          95,  tk.E),
            ('user',    'User',           250,  tk.W),
            ('started', 'Started',         75,  tk.CENTER),
            ('status',  'Status',          85,  tk.CENTER),
            ('coleta',  'Hora Coleta',    180, tk.CENTER),
            ('sha256',  'SHA-256',        500, tk.W),
            ('exe',     'Path',           850, tk.W),
            ('vt',      '🔬 VT',           70,  tk.CENTER),
        ]

        for col_id, heading, width, anchor in col_defs:
            self.tree.heading(col_id, text=heading, command=lambda c=col_id: self._sort_by_column(c))
            self.tree.column(col_id, width=width, anchor=anchor, minwidth=50)

        vsb = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure('cpu_high', foreground='#e74c3c', font=self.mono_bold)
        self.tree.tag_configure('cpu_med', foreground='#f39c12')
        self.tree.tag_configure('cpu_low', foreground='#2ecc71')
        self.tree.tag_configure('mem_high', foreground='#e74c3c')
        self.tree.tag_configure('mem_med', foreground='#f39c12')
        self.tree.tag_configure('suspended', foreground='#95a5a6', font=('Consolas', 9, 'italic'))
        self.tree.tag_configure('zombie', foreground='#7f8c8d', background='#2c1a1a')
        self.tree.tag_configure('vt_malicious', background='#3d1a1a', foreground='#ff6b6b')
        self.tree.tag_configure('vt_clean', background='#1a3d1a', foreground='#6bff6b')
        self.tree.tag_configure('vt_manual', foreground='#3498db')
        self.tree.tag_configure('hash_mono', font=self.mono_font)
        self.tree.tag_configure('row_even', background=self.colors['row_even'])
        self.tree.tag_configure('row_odd', background=self.colors['row_odd'])
        self.tree.tag_configure('system', foreground='#4fc3f7')

    # ── STATUS BAR ──────────────────────────────────────────
    def _build_statusbar(self, parent):
        status_frame = tk.Frame(parent, bg=self.colors['bg_medium'], height=26)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        status_frame.pack_propagate(False)

        self.status_bar = tk.Label(status_frame,
                                    text="Pronto | 📂 Clique em 'Carregar API Key' para ativar VT Auto ou use duplo clique na coluna VT para abrir no navegador",
                                    bg=self.colors['bg_medium'], fg=self.colors['fg_dim'],
                                    anchor=tk.W, padx=10, font=('Segoe UI', 8))
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        modo = "VT Auto" if self.api_key_loaded else "VT Manual"
        tk.Label(status_frame, text=f"Process Explorer • {modo} • SHA-256 visível",
                 bg=self.colors['bg_medium'], fg=self.colors['fg_dim'],
                 font=('Segoe UI', 7), padx=10).pack(side=tk.RIGHT)

    # ── CONTEXT MENU ────────────────────────────────────────
    def _build_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0, bg=self.colors['bg_medium'], fg=self.colors['fg'],
                                     activebackground=self.colors['accent'], activeforeground='#000000')
        self.context_menu.add_command(label="🔬 Abrir no VirusTotal (Web)", command=self.open_vt_selected)
        self.context_menu.add_command(label="📂 Abrir pasta do arquivo", command=self.open_path_folder)
        self.context_menu.add_command(label="📋 Copiar PID", command=self.copy_pid_selected)
        self.context_menu.add_command(label="📋 Copiar SHA-256", command=self.copy_hash_selected)
        self.context_menu.add_command(label="📋 Copiar Path", command=self.copy_path_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="⟳ Refresh", command=self.refresh_processes)
        self.context_menu.add_command(label="💾 Salvar Resultados", command=self.save_results_txt)

    # ── EVENTOS ─────────────────────────────────────────────
    def _bind_events(self):
        self.tree.bind('<Double-1>', self.on_double_click_vt)
        self.tree.bind('<Button-3>', self.on_right_click)

    # ── TOGGLE VT ───────────────────────────────────────────
    def _toggle_vt_scan(self):
        if self.vt_enabled.get() and self.vt_scanner and self.vt_scanner.api_key:
            self._run_vt_scan()
        else:
            for p in self.processes:
                p['vt_display'] = ""
                p['vt_malicious'] = False
                p['vt_clean'] = False
                p['vt_stats'] = None
            self._filter_processes()
            self.status_bar.config(text="🔬 VT Auto Scan desligado. Usando modo manual 🔍")

    # ── REFRESH ─────────────────────────────────────────────
    def refresh_processes(self):
        self.status_bar.config(text="🔄 Coletando processos...")
        threading.Thread(target=self._collect_and_update, daemon=True).start()

    def _collect_and_update(self):
        try:
            processes = ProcessCollector.collect()
        except Exception as e:
            self.root.after(0, lambda: self.status_bar.config(text=f"❌ Erro na coleta: {e}"))
            return
        self.root.after(0, self._update_tree, processes)

    def _update_tree(self, processes):
        self.processes = processes
        
        vt_auto = self.vt_enabled.get() and self.vt_scanner is not None and self.vt_scanner.api_key
        
        for p in self.processes:
            if vt_auto:
                if not p['vt_display']:
                    p['vt_display'] = "..."
            else:
                p['vt_display'] = "🔍" if p['has_hash'] else " - "
                p['vt_malicious'] = False
                p['vt_clean'] = False
                p['vt_stats'] = None
        
        if vt_auto:
            self._run_vt_scan()
        
        self._filter_processes()

    # ── VT SCAN ─────────────────────────────────────────────
    def _run_vt_scan(self):
        if not self.vt_scanner or not self.vt_enabled.get() or not self.vt_scanner.api_key:
            return
        
        if self.vt_scanner.is_scanning:
            self.status_bar.config(text="⏳ Scan VT já em andamento...")
            return
        
        pendentes = sum(1 for p in self.processes if p['hash'] and p['vt_display'] in ("...", ""))
        if pendentes == 0:
            cache_size = self.vt_cache.size() if self.vt_cache else 0
            self.status_bar.config(text=f"✅ Todos os processos já escaneados. Cache: {cache_size}")
            return
        
        self.status_bar.config(text=f"🔬 Escaneando {pendentes} processos no VirusTotal...")
        
        def progress_callback(completed, total):
            try:
                self.root.after(0, lambda: self.status_bar.config(
                    text=f"🔬 VT Scan: {completed}/{total} concluídos | Cache: {self.vt_cache.size() if self.vt_cache else 0}"))
                if completed % 5 == 0 or completed == total:
                    self.root.after(0, self._filter_processes)
            except Exception:
                pass
        
        def done_callback():
            try:
                self.root.after(0, lambda: self._finalize_vt_scan(pendentes))
            except Exception:
                pass
        
        threading.Thread(target=self.vt_scanner.scan_processes,
                         args=(self.processes, progress_callback, done_callback),
                         daemon=True).start()

    def _finalize_vt_scan(self, total_scan):
        mal_count = sum(1 for p in self.processes if p['vt_malicious'])
        self._filter_processes()
        if self.lbl_cache is not None and self.vt_cache is not None:
            self.lbl_cache.config(text=f"Cache: {self.vt_cache.size()}")
        self.status_bar.config(text=f"✅ VT Scan concluído! ⚠️ {mal_count} suspeitos | Cache: {self.vt_cache.size() if self.vt_cache else 0}")

    # ── FILTER ──────────────────────────────────────────────
    def _filter_processes(self):
        query = self.search_var.get().strip().lower()
        filtered = self.processes
        if query:
            filtered = [p for p in self.processes
                        if query in p['name'].lower()
                        or query in str(p['pid'])
                        or query in p['exe'].lower()
                        or query in p['user'].lower()
                        or query in p['hash'].lower()
                        or query in p['vt_display'].lower()]

        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, p in enumerate(filtered):
            tags = []
            tags.append('row_even' if idx % 2 == 0 else 'row_odd')

            try:
                cpu_val = float(p['cpu'])
                if cpu_val > 50: tags.append('cpu_high')
                elif cpu_val > 20: tags.append('cpu_med')
                elif cpu_val > 0: tags.append('cpu_low')
            except ValueError:
                pass

            if p['mem_raw'] > 500: tags.append('mem_high')
            elif p['mem_raw'] > 100: tags.append('mem_med')

            sl = p['status'].lower()
            if 'suspend' in sl: tags.append('suspended')
            elif 'zombie' in sl: tags.append('zombie')

            if p['pid'] in (0, 4) or p['name'].lower() in ('system', 'system idle process'):
                tags.append('system')

            if p['vt_malicious']:
                tags.append('vt_malicious')
            elif p['vt_clean']:
                tags.append('vt_clean')
            elif p['vt_display'] == "🔍":
                tags.append('vt_manual')

            tags.append('hash_mono')

            vt_val = p['vt_display'] if p['vt_display'] else ("🔍" if p['has_hash'] else " - ")
            hash_val = p['hash'] if p['hash'] else " - "

            self.tree.insert('', tk.END,
                             values=(p['pid'], p['name'], p['cpu'], p['mem'],
                                     p['user'], p['started'], p['status'],
                                     p['coleta'], hash_val, p['exe'], vt_val),
                             tags=tuple(tags))

        self.lbl_total.config(text=f"Processos: {len(filtered)}/{len(self.processes)}")

    # ── AUTO REFRESH / CLOCK ────────────────────────────────
    def _schedule_auto_refresh(self):
        if self.auto_refresh.get():
            self.refresh_processes()
        self.root.after(AUTO_REFRESH_INTERVAL, self._schedule_auto_refresh)

    def _update_clock_loop(self):
        self.lbl_datetime.config(text=agora_br())
        self.root.after(1000, self._update_clock_loop)

    # ── SAVE ────────────────────────────────────────────────
    def save_results_txt(self):
        if not self.processes:
            messagebox.showwarning("Aviso", "Nenhum processo carregado para salvar.")
            return

        query = self.search_var.get().strip().lower()
        to_save = self.processes
        if query:
            to_save = [p for p in self.processes
                       if query in p['name'].lower() or query in str(p['pid'])
                       or query in p['exe'].lower() or query in p['user'].lower()
                       or query in p['hash'].lower()]

        filepath = filedialog.asksaveasfilename(defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt")],
            title="Salvar resultados dos processos",
            initialfile=f"processos_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt")

        if not filepath:
            return

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 300 + "\n")
                f.write("PROCESS EXPLORER - Pentest Tool\n\n")
                f.write(f"Data/Hora do relatório: {agora_br()}\n\n")
                f.write(f"Hostname: {platform.node()}\n\n")
                f.write(f"Sistema: {platform.system()} {platform.release()}\n\n")
                f.write(f"Total de processos listados: {len(to_save)}\n\n")
                modo_vt = "Automático (API)" if (self.vt_scanner and self.vt_scanner.api_key) else "Manual (navegador)\n"
                f.write(f"Modo VirusTotal: {modo_vt}\n\n")
                if query:
                    f.write(f"Filtro aplicado: \"{query}\"\n")
                f.write("=" * 300 + "\n\n")

                cabecalho = (f"{'PID':>7}  {'Nome':<35}  {'CPU%':>6}  {'Memória':>10}  "
                             f"{'Usuário':<38}  {'Início':>8}  {'Status':<10}  "
                             f"{'SHA-256':<72}  {'Path':<80}  {'VT':<10}")
                f.write(cabecalho + "\n" + "-" * 300 + "\n")

                for p in to_save:
                    vt_display = p['vt_display'] if p['vt_display'] else ("🔍 Manual" if p['has_hash'] else " - ")
                    hash_str = p['hash'] if p['hash'] else "Sem hash (arquivo inacessível)"
                    linha = (f"{p['pid']:>7}  {p['name'][:35]:<35}  {p['cpu']:>6}  "
                             f"{p['mem']:>10}  {p['user'][:38]:<38}  {p['started']:>8}  "
                             f"{p['status'][:10]:<10}  {hash_str:<72}  "
                             f"{p['exe']:<80}  {vt_display:<10}")
                    f.write(linha + "\n")

                if self.vt_scanner and self.vt_scanner.api_key:
                    f.write("\n" + "=" * 160 + "\nRESUMO VIRUSTOTAL:\n" + "-" * 160 + "\n")
                    mal = [p for p in to_save if p['vt_malicious']]
                    clean = [p for p in to_save if p['vt_clean']]
                    f.write(f"⚠️  Suspeitos: {len(mal)}\n✅ Limpos: {len(clean)}\n")
                    if mal:
                        f.write("\n--- SUSPEITOS ---\n")
                        for p in mal:
                            f.write(f"PID {p['pid']:>7} | {p['vt_display']:>8} | {p['name'][:40]:<40} | "
                                    f"Hash: {p['hash'][:20]}... | {p['exe']}\n")

                f.write("\n" + "=" * 300 + "\n")
                f.write(f"Relatório gerado por Process Explorer em {agora_br()}\n")
                f.write("=" * 300 + "\n")

            self.status_bar.config(text=f"💾 Resultados salvos em: {filepath}")
            messagebox.showinfo("Sucesso", f"Resultados salvos com sucesso!\n\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", f"Não foi possível salvar o arquivo:\n{e}")

    # ── AÇÕES ───────────────────────────────────────────────
    def get_selected_process(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Aviso", "Nenhum processo selecionado.")
            return None
        item = selection[0]
        values = self.tree.item(item, 'values')
        if not values:
            return None
        pid = int(values[0])
        for p in self.processes:
            if p['pid'] == pid:
                return p
        return None

    def on_double_click_vt(self, event):
        region = self.tree.identify_region(event.x, event.y)
        col = self.tree.identify_column(event.x)
        if region == "cell" and col == "#11":
            self.open_vt_selected()

    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def open_vt_selected(self):
        proc = self.get_selected_process()
        if not proc:
            return
        if not proc['hash']:
            messagebox.showwarning("Hash não disponível", f"Não foi possível calcular o hash de:\n{proc['exe']}")
            return
        
        if proc['vt_stats'] and not proc['vt_stats'].get('not_found') and not proc['vt_stats'].get('rate_limited'):
            stats = proc['vt_stats']
            msg = (f"Processo: {proc['name']} (PID: {proc['pid']})\n"
                   f"SHA-256: {proc['hash'][:64]}\n\n"
                   f"🔬 Resultados VirusTotal:\n"
                   f"  ⚠️  Maliciosos:    {stats.get('malicious', 0)}\n"
                   f"  ✅  Limpos:        {stats.get('harmless', 0)}\n"
                   f"  ❓  Não detectados: {stats.get('undetected', 0)}\n"
                   f"  📊  Total engines: {stats.get('total', 0)}\n\n"
                   f"Abrir página web do VirusTotal para detalhes completos?")
            if not self.custom_askyesno("VirusTotal - Resultados", msg):  # ← JANELA GRANDE
                return
        else:
            msgbox = self.custom_askyesno("VirusTotal",
                f"Abrir página web do VirusTotal\n\n\n\n"
                f"Processo: {proc['name']}    PID: {proc['pid']}\n\n\n"
                f"SHA-256: {proc['hash'][:64]}\n\n"
                f"\n\n\n\n🔍 Você será direcionado ao navegador")                # ← JANELA GRANDE
            if not msgbox:
                return
        
        open_virustotal_web(proc['hash'])
        self.status_bar.config(text=f"🔬 VirusTotal: {proc['name']} (PID: {proc['pid']})")

    def open_path_folder(self):
        proc = self.get_selected_process()
        if not proc or not proc.get('exe') or not os.path.isfile(proc['exe']):
            messagebox.showwarning("Arquivo não encontrado", "Caminho inválido ou inacessível.")
            return
        try:
            subprocess.Popen(['explorer', '/select,', proc['exe']])
            self.status_bar.config(text=f"📂 Pasta aberta: {os.path.dirname(proc['exe'])}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

    def copy_pid_selected(self):
        proc = self.get_selected_process()
        if proc:
            self.root.clipboard_clear()
            self.root.clipboard_append(str(proc['pid']))
            self.status_bar.config(text=f"📋 PID {proc['pid']} copiado.")

    def copy_hash_selected(self):
        proc = self.get_selected_process()
        if proc and proc['hash']:
            self.root.clipboard_clear()
            self.root.clipboard_append(proc['hash'])
            self.status_bar.config(text=f"📋 SHA-256 copiado: {proc['hash'][:20]}...")
        elif proc:
            self.status_bar.config(text="❌ Nenhum hash disponível para copiar.")

    def copy_path_selected(self):
        proc = self.get_selected_process()
        if proc:
            self.root.clipboard_clear()
            self.root.clipboard_append(proc['exe'])
            self.status_bar.config(text=f"📋 Path copiado.")

    # ── SORT ────────────────────────────────────────────────
    def _sort_by_column(self, col):
        items = self.tree.get_children('')
        if not items:
            return

        data = [(item, self.tree.item(item, 'values')) for item in items]

        col_idx = {'pid': 0, 'name': 1, 'cpu': 2, 'mem': 3, 'user': 4,
                   'started': 5, 'status': 6, 'coleta': 7, 'sha256': 8,
                   'exe': 9, 'vt': 10}.get(col, 1)

        def sort_key(x):
            val = x[1][col_idx]
            if col_idx == 0:
                try: return int(val)
                except: return 0
            if col_idx == 3:
                try: return float(val.replace(' MB', ''))
                except: return 0.0
            if col_idx == 2:
                try: return float(val)
                except: return 0.0
            if col_idx == 10:
                try:
                    parts = str(val).split('/')
                    return int(parts[0]) if parts[0].isdigit() else (0 if val == "🔍" else -1)
                except: return 0
            return val.lower()

        if not hasattr(self, '_sort_reverse'):
            self._sort_reverse = {}
        current_rev = self._sort_reverse.get(col, False)
        data.sort(key=sort_key, reverse=current_rev)
        self._sort_reverse[col] = not current_rev

        for idx, (item, vals) in enumerate(data):
            self.tree.move(item, '', idx)
            arrow = " ▲" if current_rev else " ▼"
            for c in ('pid', 'name', 'cpu', 'mem', 'user', 'started', 'status',
                       'coleta', 'sha256', 'exe', 'vt'):
                self.tree.heading(c, text=self.tree.heading(c)['text'].replace(' ▲', '').replace(' ▼', ''))
            cur_text = self.tree.heading(col)['text']
            self.tree.heading(col, text=cur_text.replace(' ▲', '').replace(' ▼', '') + arrow)


# ═════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════
def main():
    root = tk.Tk()
    app = ProcessExplorerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
