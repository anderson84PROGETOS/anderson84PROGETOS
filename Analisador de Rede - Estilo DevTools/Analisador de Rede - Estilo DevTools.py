import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import requests
import threading
import time
import random
import re
import os
from datetime import datetime

# ================== USER-AGENTS PADRÃO ==================
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
]

# ================== VARIÁVEL GLOBAL DE USER-AGENTS ==================
user_agents_list = DEFAULT_USER_AGENTS.copy()
user_agents_file_path = ""

# ================== SESSION GLOBAL ==================
session = requests.Session()

def get_headers():
    return {
        "User-Agent": random.choice(user_agents_list),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5,pt-BR;q=0.3",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

# ================== PLATAFORMAS ==================
PLATFORMS = [    
    {"name":"linkpota.to",   "url":"https://linkpota.to/{}"},
    {"name": "PyPI",         "url": "https://pypi.org/user/{}/"},
    {"name": "Reddit",       "url": "https://www.reddit.com/user/{}"},
    {"name": "GitLab",       "url": "https://gitlab.com/{}"},
    {"name": "Replit",       "url": "https://replit.com/@{}"},
    {"name": "GitHub",       "url": "https://github.com/{}"},
    {"name": "Medium",       "url": "https://medium.com/@{}"},
    {"name": "Tumblr",       "url": "https://{}.tumblr.com"},
    {"name": "Spotify",      "url": "https://open.spotify.com/user/{}"},
    {"name": "SoundCloud",   "url": "https://soundcloud.com/{}"},
    {"name": "Codecademy",   "url": "https://www.codecademy.com/profiles/{}"},
    {"name": "Duolingo",     "url": "https://www.duolingo.com/profile/{}"},
    {"name": "Pinterest",    "url": "https://www.pinterest.com/{}"},
    {"name": "HackerEarth",  "url": "https://www.hackerearth.com/@{}"},
    {"name": "Pastebin",     "url": "https://pastebin.com/u/{}"},
    {"name": "Twitch",       "url": "https://www.twitch.tv/{}"},
    {"name": "TryHackMe",    "url": "https://tryhackme.com/p/{}"},
    {"name": "Kaggle",       "url": "https://www.kaggle.com/{}"},
    {"name": "Twitter/X",    "url": "https://twitter.com/{}"},
    {"name": "Scribd",       "url": "https://www.scribd.com/{}"},
    {"name": "HackTheBox",   "url": "https://app.hackthebox.com/profile/{}"},
    {"name": "About.me",     "url": "https://about.me/{}"},
    {"name": "Chess.com",    "url": "https://www.chess.com/member/{}"},
    {"name": "Wordpress",    "url": "https://{}.wordpress.com"},
    {"name": "Dev.to",       "url": "https://dev.to/{}"},
    {"name": "npm",          "url": "https://www.npmjs.com/~{}"},
    {"name": "Instagram",    "url": "https://www.instagram.com/{}/"},
    {"name": "Facebook",     "url": "https://www.facebook.com/{}"},
    {"name": "TikTok",       "url": "https://www.tiktok.com/@{}"},
    {"name": "YouTube",      "url": "https://www.youtube.com/@{}"},
    {"name": "LinkedIn",     "url": "https://www.linkedin.com/in/{}"},
    {"name": "Snapchat",     "url": "https://www.snapchat.com/add/{}"},
    {"name": "Behance",      "url": "https://www.behance.net/{}"},
    {"name": "Dribbble",     "url": "https://dribbble.com/{}"},
    {"name": "Flickr",       "url": "https://www.flickr.com/people/{}"},
    {"name": "DeviantArt",   "url": "https://www.deviantart.com/{}"},
    {"name": "Vimeo",        "url": "https://vimeo.com/{}"},
    {"name": "Steam",        "url": "https://steamcommunity.com/id/{}"},
    {"name": "Telegram",     "url": "https://t.me/{}"},
    {"name": "OnlyFans",     "url": "https://onlyfans.com/{}"},
    {"name": "Patreon",      "url": "https://www.patreon.com/{}"},
    {"name": "Kickstarter",  "url": "https://www.kickstarter.com/profile/{}"},
    {"name": "Bitbucket",    "url": "https://bitbucket.org/{}/"},
    {"name": "StackOverflow","url": "https://stackoverflow.com/users/{}"},
    {"name": "HackerRank",   "url": "https://www.hackerrank.com/{}"},
    {"name": "LeetCode",     "url": "https://leetcode.com/{}"},
    {"name": "Codeforces",   "url": "https://codeforces.com/profile/{}"},
    {"name": "Gravatar",     "url": "https://en.gravatar.com/{}"},
    {"name": "Keybase",      "url": "https://keybase.io/{}"},
    {"name": "Roblox",       "url": "https://www.roblox.com/search/users?keyword={}"},
    {"name": "Minecraft",    "url": "https://namemc.com/profile/{}"},
    {"name": "Epic Games",   "url": "https://store.epicgames.com/u/{}"},
    {"name": "Xbox",         "url": "https://account.xbox.com/en-us/profile?gamertag={}"},
    {"name": "PlayStation",  "url": "https://psnprofiles.com/{}"},
    {"name": "EA",           "url": "https://www.ea.com/games/library/pc-download/{}"},
    {"name": "Ubisoft",      "url": "https://ubisoftconnect.com/en-US/profile/{}"},
    {"name": "Battle.net",   "url": "https://starcraft2.blizzard.com/en-us/profile/{}/"},
    {"name": "RuneScape",    "url": "https://secure.runescape.com/m=hiscore_oldschool/hiscorepersonal?user1={}"},
    {"name": "Faceit",       "url": "https://www.faceit.com/en/players/{}"},
    {"name": "Tracker.gg",   "url": "https://tracker.gg/valorant/profile/riot/{}/overview"},
    {"name": "Guilded",      "url": "https://www.guilded.gg/profile/{}"},
    {"name": "Speedrun.com", "url": "https://www.speedrun.com/user/{}"},
    {"name": "osu!",         "url": "https://osu.ppy.sh/users/{}"},
    {"name": "Lichess",      "url": "https://lichess.org/@/{}"},
    {"name": "Modrinth",     "url": "https://modrinth.com/user/{}"},
    {"name": "CurseForge",   "url": "https://www.curseforge.com/members/{}"},
    {"name": "Planet Minecraft", "url": "https://www.planetminecraft.com/member/{}/"},
    {"name": "GOG",          "url": "https://www.gog.com/u/{}"},
    {"name": "Speedrun.com Forums", "url": "https://www.speedrun.com/user/{}"},
    {"name": "Nexus Mods",   "url": "https://next.nexusmods.com/profile/{}"},
    {"name": "BoardGameGeek","url": "https://boardgamegeek.com/user/{}"},
    {"name": "x.com",        "url": "https://x.com/{}"},
]


class OSINTTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EMAIL OSINT - Username Recon")
        self.root.geometry("1200x820")
        self.root.state("zoomed")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(True, True)

        # Estado
        self.found_accounts = []  # Cada item: (name, url, status_code)
        self._scanning = False
        self._last_username = ""
        self._scan_complete = False

        self.create_widgets()
        self.setup_tags()

    def create_widgets(self):
        # ============ HEADER ============
        header = tk.Frame(self.root, bg="#0a0a0a", height=140)
        header.pack(fill="x", pady=(10, 0))

        title_frame = tk.Frame(header, bg="#0a0a0a")
        title_frame.pack()

        self.title_label = tk.Label(
            title_frame, text="EMAIL", font=("Consolas", 54, "bold"),
            fg="#00ff41", bg="#0a0a0a"
        )
        self.title_label.pack()

        subtitle = tk.Label(
            header, text="OSINT // Username Intelligence Reconnaissance",
            font=("Consolas", 11), fg="#00b3ff", bg="#0a0a0a"
        )
        subtitle.pack()

        separador = tk.Frame(header, height=2, bg="#00ff41")
        separador.pack(fill="x", padx=50, pady=5)

        # ============ INPUT FRAME ============
        input_frame = tk.Frame(self.root, bg="#0a0a0a")
        input_frame.pack(pady=(5, 2))

        tk.Label(
            input_frame, text="USERNAME :", font=("Consolas", 14, "bold"),
            fg="#00ff41", bg="#0a0a0a"
        ).pack(side="left", padx=(0, 5))

        self.username_entry = tk.Entry(
            input_frame, font=("Consolas", 13), width=32,
            bg="#1a1a1a", fg="#00ff41", insertbackground="#00ff41",
            relief="flat", bd=0, highlightthickness=1, highlightbackground="#00ff41"
        )
        self.username_entry.pack(side="left", padx=5, ipady=4)
        self.username_entry.bind("<Return>", lambda e: self.start_scan())

        self.scan_button = tk.Button(
            input_frame, text="▶  SCAN PLATFORMS", font=("Consolas", 11, "bold"),
            bg="#00bf3f", fg="#000000", activebackground="#00ff41",
            activeforeground="#000000", command=self.start_scan,
            relief="flat", padx=15, pady=5, cursor="hand2"
        )
        self.scan_button.pack(side="left", padx=(15, 0))

        self.save_button = tk.Button(
            input_frame, text="💾  SAVE .TXT", font=("Consolas", 10, "bold"),
            bg="#1a2a3a", fg="#00b3ff", activebackground="#2a4a6a",
            activeforeground="#00ffff", command=self.save_results,
            relief="flat", padx=12, pady=5, cursor="hand2", state="disabled"
        )
        self.save_button.pack(side="left", padx=8)

        self.clear_button = tk.Button(
            input_frame, text="✕  CLEAR", font=("Consolas", 10, "bold"),
            bg="#3a1a1a", fg="#ff4444", activebackground="#5a2a2a",
            activeforeground="#ff6666", command=self.clear_results,
            relief="flat", padx=10, pady=5, cursor="hand2"
        )
        self.clear_button.pack(side="left", padx=5)

        # ============ USER-AGENT FRAME ============
        ua_frame = tk.Frame(self.root, bg="#0a0a0a")
        ua_frame.pack(pady=(2, 5), padx=30, fill="x")

        self.ua_status_label = tk.Label(
            ua_frame, text="🔄  User-Agents: 6 loaded (default)",
            font=("Consolas", 9), fg="#888888", bg="#0a0a0a", anchor="w"
        )
        self.ua_status_label.pack(side="left")

        self.ua_button = tk.Button(
            ua_frame, text="📂  LOAD UA FILE", font=("Consolas", 9, "bold"),
            bg="#2a2a2a", fg="#ffaa00", activebackground="#3a3a3a",
            activeforeground="#ffcc00", command=self.load_user_agents,
            relief="flat", padx=10, pady=2, cursor="hand2"
        )
        self.ua_button.pack(side="right")

        # ============ PROGRESS BAR ============
        progress_frame = tk.Frame(self.root, bg="#0a0a0a")
        progress_frame.pack(pady=(3, 5), padx=30, fill="x")

        self.progress = ttk.Progressbar(
            progress_frame, mode='determinate', length=0
        )
        self.progress.pack(fill="x")

        self.status_label = tk.Label(
            progress_frame, text="ready · 0 platforms", font=("Consolas", 8),
            fg="#555555", bg="#0a0a0a", anchor="w"
        )
        self.status_label.pack(fill="x")

        # ============ RESULTS ============
        result_frame = tk.Frame(self.root, bg="#0a0a0a")
        result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        result_header = tk.Frame(result_frame, bg="#0a0a0a")
        result_header.pack(fill="x")

        tk.Label(
            result_header, text="═══ PLATFORM FOOTPRINT ═══",
            font=("Consolas", 13, "bold"), fg="#00b3ff", bg="#0a0a0a"
        ).pack(side="left")

        self.counter_label = tk.Label(
            result_header, text="", font=("Consolas", 10, "bold"),
            fg="#00ff41", bg="#0a0a0a"
        )
        self.counter_label.pack(side="right")

        # Text area
        text_frame = tk.Frame(result_frame, bg="#0a0a0a")
        text_frame.pack(fill="both", expand=True, pady=(5, 0))

        self.result_text = scrolledtext.ScrolledText(
            text_frame, font=("Consolas", 10),
            bg="#0d0d0d", fg="#c0c0c0",
            insertbackground="#00ff41", relief="flat",
            highlightthickness=1, highlightbackground="#1a1a1a",
            borderwidth=0, padx=8, pady=8,
            wrap=tk.WORD
        )
        self.result_text.pack(fill="both", expand=True)

        # Bind de clique para abrir URLs
        self.result_text.tag_bind("url", "<Button-1>", self.open_url_callback)
        self.result_text.tag_bind("url_found", "<Button-1>", self.open_url_callback)
        self.result_text.config(cursor="arrow")

        # ============ FOOTER ============
        footer_frame = tk.Frame(self.root, bg="#0a0a0a")
        footer_frame.pack(side="bottom", fill="x", pady=(0, 5))

        footer = tk.Label(
            footer_frame,
            text="•  EMAIL OSINT •  Username Recon •",
            font=("Consolas", 8), fg="#3a3a3a", bg="#0a0a0a"
        )
        footer.pack()

    def setup_tags(self):
        """Configura todas as tags de cor do text widget."""
        tags = {
            "platform_header": {"foreground": "#00b3ff", "font": ("Consolas", 11, "bold")},
            "status_200":      {"foreground": "#00ff41"},  # verde - encontrado
            "status_403":      {"foreground": "#ff4444"},  # vermelho - não encontrado
            "status_404":      {"foreground": "#ff4444"},  # vermelho - não encontrado
            "status_other":    {"foreground": "#ffaa00"},  # laranja - outros códigos
            "error":           {"foreground": "#ff3333"},
            "url":             {"foreground": "#00ffff", "underline": True},
            "url_found":       {"foreground": "#00ffff", "underline": True},
            "summary_found":   {"foreground": "#00ff41", "font": ("Consolas", 11, "bold")},
            "summary_none":    {"foreground": "#ff4444", "font": ("Consolas", 11, "bold")},
            "separator":       {"foreground": "#1a3a1a"},
            "timestamp":       {"foreground": "#555555"},
        }
        for tag, cfg in tags.items():
            self.result_text.tag_config(tag, **cfg)

    # ============ CARREGAR USER-AGENTS DE ARQUIVO ============
    def load_user_agents(self):
        """Abre diálogo para selecionar um arquivo .txt com User-Agents."""
        global user_agents_list, user_agents_file_path

        filepath = filedialog.askopenfilename(
            title="Select User-Agents File (.txt)",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_agents = []
            for line in lines:
                line = line.strip()
                if line and len(line) > 30 and not line.startswith("#") and not line.startswith("//"):
                    new_agents.append(line)

            if not new_agents:
                messagebox.showwarning(
                    "No Valid Agents",
                    "No valid User-Agents found in the file.\nKeeping current User-Agents."
                )
                return

            user_agents_list = new_agents
            user_agents_file_path = filepath

            filename = os.path.basename(filepath)
            self.ua_status_label.config(
                text=f"🔄  User-Agents: {len(new_agents)} loaded from {filename}",
                fg="#ffaa00"
            )
            self.status_label.config(
                text=f"loaded {len(new_agents)} UAs from {filename}",
                fg="#ffaa00"
            )

            messagebox.showinfo(
                "User-Agents Loaded",
                f"Successfully loaded {len(new_agents)} User-Agents from:\n{filepath}"
            )

        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load file:\n{str(e)}")

    # ============ LÓGICA PRINCIPAL ============
    def check_platform(self, platform, username):
        """Verifica uma plataforma e retorna True se encontrou."""
        try:
            url = platform["url"].format(username)
            resp = session.get(url, headers=get_headers(), timeout=12, allow_redirects=True)
            
            status = resp.status_code
            
            if status == 200:
                self.found_accounts.append((platform["name"], url, status))
                self.root.after(0, self._insert_status, platform["name"], url, status, True)
                return True
            else:
                self.root.after(0, self._insert_status, platform["name"], url, status, False)
                return False
                
        except requests.exceptions.Timeout:
            self.root.after(0, self._insert_error, platform["name"], "timeout")
            return False
        except requests.exceptions.ConnectionError:
            self.root.after(0, self._insert_error, platform["name"], "conn err")
            return False
        except Exception as e:
            self.root.after(0, self._insert_error, platform["name"], str(e)[:20])
            return False

    def _get_status_tag(self, status):
        """Retorna a tag de cor baseada no status code."""
        if status == 200:
            return "status_200"
        elif status in (403, 401):
            return "status_403"
        elif status == 404:
            return "status_404"
        else:
            return "status_other"

    def _format_status(self, status):
        """Formata o status code para exibição."""
        if status == 200:
            return f"200 ✓"
        elif status == 403:
            return f"403 ✗"
        elif status == 404:
            return f"404 ✗"
        else:
            return f"{status}"

    def _insert_status(self, name, url, status, is_found):
        """Insere uma linha formatada com status code."""
        tag = self._get_status_tag(status)
        status_str = self._format_status(status)
        
        self.result_text.insert(tk.END, f"  {status_str:<7}", tag)
        self.result_text.insert(tk.END, f"{name:<18}", tag)
        
        if is_found:
            self.result_text.insert(tk.END, f"  {url}\n", "url")
        else:
            self.result_text.insert(tk.END, f"  —\n", tag)

    def _insert_error(self, name, reason):
        self.result_text.insert(tk.END, f"  ERR     ", "error")
        self.result_text.insert(tk.END, f"{name:<18}", "error")
        self.result_text.insert(tk.END, f"  {reason}\n", "error")

    def scan_thread(self):
        """Executa o scan em uma thread separada."""
        username = self.username_entry.get().strip()

        if not username or not re.match(r'^[\w.\-@+_]+$', username):
            self.root.after(0, lambda: messagebox.showerror(
                "Invalid Input",
                "Enter a valid username (letters, numbers, dots, hyphens, underscores)."
            ))
            self.root.after(0, self._finish_scan)
            return

        self._last_username = username
        self._scan_complete = False
        self.found_accounts.clear()
        self.root.after(0, self._clear_text)
        self.root.after(0, lambda: self._append_text(
            f"SCANNING: {username}\n\n", "platform_header"
        ))
        self.root.after(0, lambda: self._append_text(
            f"  {'STATUS':<7} {'PLATFORM':<18} URL\n", "platform_header"
        ))
        self.root.after(0, lambda: self._append_text(
            f"  {'─'*7} {'─'*18} {'─'*40}\n", "separator"
        ))

        total = len(PLATFORMS)
        found_count = 0

        for i, platform in enumerate(PLATFORMS):
            if not self._scanning:
                break

            if self.check_platform(platform, username):
                found_count += 1

            progress = int(((i + 1) / total) * 100)
            self.root.after(0, lambda p=progress, c=i+1: self._update_progress(p, c, total, found_count))
            time.sleep(0.15)

        self.root.after(0, self._show_summary, username, found_count, total)

    def _clear_text(self):
        self.result_text.delete(1.0, tk.END)

    def _append_text(self, text, tag=None):
        if tag:
            self.result_text.insert(tk.END, text, tag)
        else:
            self.result_text.insert(tk.END, text)
        self.result_text.see(tk.END)

    def _update_progress(self, value, current, total, found):
        self.progress['value'] = value
        self.status_label.config(
            text=f"scanning · {current}/{total} platforms · {found} found",
            fg="#00b3ff"
        )
        self.root.update_idletasks()

    def _show_summary(self, username, found, total):
        if not self._scanning:
            self._append_text("\n  [!] Scan cancelled by user.\n", "error")
            self._finish_scan()
            return

        self._append_text(f"\n  {'═' * 65}\n", "separator")
        
        if found > 0:
            self._append_text(
                f"  [✔]  {found} profile{'s' if found != 1 else ''} found  |  {total} platforms checked\n\n",
                "summary_found"
            )
            self._append_text("  📍  DISCOVERED PROFILES (HTTP 200):\n\n", "platform_header")

            # CORRIGIDO: usando name, url, status e exibindo o status também
            for name, url, status in self.found_accounts:
                # Status code em verde
                self._append_text(f"       →  200 ✓  ", "status_200")
                # Nome da plataforma em verde
                self._append_text(f"{name:<15}", "status_200")
                # URL em ciano (link)
                self._append_text(f"  {url}\n", "url_found")

            self.counter_label.config(
                text=f"{found} profiles found",
                fg="#00ff41"
            )
        else:
            self._append_text(
                f"  [✗]  No profiles found  |  {total} platforms checked\n",
                "summary_none"
            )
            self.counter_label.config(text="no results", fg="#ff4444")

        self._append_text(f"\n  {'═' * 65}\n", "separator")
        self._scan_complete = True
        self._finish_scan()

    def _finish_scan(self):
        self._scanning = False
        self.scan_button.config(text="▶  SCAN PLATFORMS", bg="#00bf3f", state="normal")
        
        if self._scan_complete and self.found_accounts:
            self.save_button.config(state="normal", bg="#1a3a3a", fg="#00ff41")
            self.status_label.config(text="scan complete · results ready to save", fg="#00ff41")
        elif self._scan_complete:
            self.save_button.config(state="disabled", bg="#1a2a3a", fg="#00b3ff")
            self.status_label.config(text="scan complete · no results found", fg="#ff4444")
        else:
            self.status_label.config(text="scan cancelled", fg="#ff4444")

        self.root.update_idletasks()

    # ============ SALVAR RESULTADOS EM .TXT ============
    def save_results(self):
        if not self._scan_complete or not self.found_accounts:
            messagebox.showinfo("Save Results", "No results to save. Run a scan first.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"osint_{self._last_username}_{timestamp}.txt"

        filepath = filedialog.asksaveasfilename(
            title="Save OSINT Results",
            defaultextension=".txt",
            initialfile=default_filename,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("=" * 65 + "\n")
                f.write("  EMAIL OSINT v3.0  -  Username Reconnaissance Report\n")
                f.write("=" * 65 + "\n\n")
                f.write(f"  Target Username : {self._last_username}\n")
                f.write(f"  Scan Date       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"  Platforms Checked: {len(PLATFORMS)}\n")
                f.write(f"  Profiles Found  : {len(self.found_accounts)}\n")
                f.write(f"  User-Agents     : {len(user_agents_list)} loaded\n")
                if user_agents_file_path:
                    f.write(f"  UA File         : {user_agents_file_path}\n")
                f.write("\n" + "=" * 65 + "\n\n")

                if self.found_accounts:
                    f.write("  📍  DISCOVERED PROFILES (HTTP 200):\n\n")
                    for name, url, status in self.found_accounts:
                        f.write(f"     [200] {name:<18}  {url}\n")
                    f.write("\n")

                f.write("  ─" * 22 + "\n")
                f.write("  FULL PLATFORM SCAN REPORT:\n\n")
                full_text = self.result_text.get(1.0, tk.END)
                f.write(full_text)
                
                f.write("\n" + "=" * 65 + "\n")
                f.write("  Report generated by EMAIL OSINT v3.0\n")
                f.write("  Educational & Research Use Only\n")
                f.write("=" * 65 + "\n")

            self.status_label.config(text=f"saved → {os.path.basename(filepath)}", fg="#00ff41")
            messagebox.showinfo("Saved Successfully", f"Results saved to:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file:\n{str(e)}")
            self.status_label.config(text="save error", fg="#ff4444")

    # ============ CONTROLES DA GUI ============
    def start_scan(self):
        if self._scanning:
            self._scanning = False
            self.scan_button.config(text="⏹  STOPPING...", bg="#ff4444", state="disabled")
            self.save_button.config(state="disabled", bg="#1a2a3a", fg="#00b3ff")
            return

        self._scanning = True
        self._scan_complete = False
        self.scan_button.config(text="⏹  STOP SCAN", bg="#ff4444", state="normal")
        self.save_button.config(state="disabled", bg="#1a2a3a", fg="#00b3ff")
        self.counter_label.config(text="scanning...", fg="#ffff00")
        self.status_label.config(text="starting scan...", fg="#ffff00")
        self.progress['value'] = 0

        t = threading.Thread(target=self.scan_thread, daemon=True)
        t.start()

    def clear_results(self):
        if self._scanning:
            return
        self.result_text.delete(1.0, tk.END)
        self.found_accounts.clear()
        self.counter_label.config(text="", fg="#00ff41")
        self.progress['value'] = 0
        self.status_label.config(text="cleared · ready", fg="#555555")
        self.save_button.config(state="disabled", bg="#1a2a3a", fg="#00b3ff")
        self._scan_complete = False
        self._last_username = ""

    def open_url_callback(self, event):
        try:
            index = self.result_text.index(f"@{event.x},{event.y}")
            tags = self.result_text.tag_names(index)
            for tag in tags:
                if tag in ("url", "url_found"):
                    line_start = f"{index.split('.')[0]}.0"
                    line_end = f"{index.split('.')[0]}.end"
                    line_text = self.result_text.get(line_start, line_end)
                    urls = re.findall(r'https?://[^\s]+', line_text)
                    if urls:
                        import webbrowser
                        webbrowser.open(urls[0])
                        self.status_label.config(text=f"opened: {urls[0][:60]}...", fg="#00b3ff")
                    break
        except Exception:
            pass

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":    
    app = OSINTTool()
    app.run()
