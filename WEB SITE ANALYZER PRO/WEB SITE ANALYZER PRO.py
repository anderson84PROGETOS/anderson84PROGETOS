#!/usr/bin/env python3
"""
◉ WEB SITE ANALYZER PRO
Aplicativo completo de análise de sites com interface gráfica
Suporte a arquivo useragent.txt com 10.000+ user agents
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import random
import os
import re
import webbrowser
import tempfile
from datetime import datetime
from collections import Counter
from urllib.parse import urljoin, urlparse
import ssl
import socket
import subprocess
import sys

# ============================================================
# INSTALAÇÃO AUTOMÁTICA DE DEPENDÊNCIAS
# ============================================================
def instalar_dependencias():
    """Instala dependências necessárias automaticamente"""
    deps = {"requests": "requests", "bs4": "beautifulsoup4"}
    for modulo, pacote in deps.items():
        try:
            __import__(modulo)
        except ImportError:
            print(f"Instalando {pacote}...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pacote],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

instalar_dependencias()

import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================
# CONSTANTES DE CORES
# ============================================================
BG = "#030603"
PANEL = "#071007"
GREEN = "#00ff41"
CYAN = "#00e5ff"
WHITE = "#b8ffb8"
RED = "#ff3333"
ORANGE = "#ff9900"
GRAY = "#668866"
YELLOW = "#ffff00"
PURPLE = "#cc66ff"
BLUE = "#3399ff"
DARK_BORDER = "#1a3a1a"
ENTRY_BG = "#020502"
SELECTED_BG = "#124512"


# ============================================================
# USER AGENTS PADRÃO (caso não carregue arquivo)
# ============================================================
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
]


# ============================================================
# GERADOR DE USERAGENTS.TXT
# ============================================================
def gerar_useragents_txt(caminho="useragent.txt", quantidade=10000):
    """Gera arquivo useragent.txt com milhares de user agents"""

    bases_chrome = [
        "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53",
        "Mozilla/5.0 (Windows NT {winver}; {arch}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X {macver}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Safari/537.36",
    ]

    bases_firefox = [
        "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53",
        "Mozilla/5.0 (Windows NT {winver}; {arch}; rv:{ffver}) Gecko/20100101 Firefox/{ffver}",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X {macver}; rv:{ffver}) Gecko/20100101 Firefox/{ffver}",
        "Mozilla/5.0 (X11; Linux x86_64; rv:{ffver}) Gecko/20100101 Firefox/{ffver}",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:{ffver}) Gecko/20100101 Firefox/{ffver}",
    ]

    bases_safari = [
        "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X {macver}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safver} Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS {iosver} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safver} Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS {iosver} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safver} Mobile/15E148 Safari/604.1",
    ]

    bases_edge = [
        "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53",
        "Mozilla/5.0 (Windows NT {winver}; {arch}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Safari/537.36 Edg/{edgever}",
    ]

    bases_mobile = [
        "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53",
        "Mozilla/5.0 (Linux; Android {andver}; {device}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android {andver}; {device}) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/{sambver} Chrome/{chrome} Mobile Safari/537.36",
    ]

    bases_opera = [
        "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53",
        "Mozilla/5.0 (Windows NT {winver}; {arch}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Safari/537.36 OPR/{opver}",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X {macver}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Safari/537.36 OPR/{opver}",
    ]

    bases_bots = [
        "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
        "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
        "DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)",
        "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
        "Twitterbot/1.0",
        "LinkedInBot/1.0 (compatible; Mozilla/5.0; Apache-HttpClient +http://www.linkedin.com)",
        "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
        "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)",
        "WhatsApp/2.23.20.0",
        "TelegramBot (like TwitterBot)",
        "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.0; +https://openai.com/gptbot)",
    ]

    winvers = ["10.0", "11.0", "6.3", "6.1"]
    archs = ["Win64; x64", "WOW64", "Win32; x86"]
    macvers = ["10_15_7", "11_0", "12_0", "13_0", "14_0", "14_5", "15_0"]
    iosvers = ["16_0", "16_5", "17_0", "17_5", "18_0", "18_1"]
    andvers = ["11", "12", "13", "14", "15"]
    devices = [
        "SM-S928B", "SM-S918B", "SM-A546B", "SM-A155F", "SM-G998B",
        "Pixel 8 Pro", "Pixel 7a", "Pixel 9", "Pixel 8",
        "SAMSUNG SM-G991B", "Redmi Note 13 Pro",
        "M2101K6G", "22101316G", "2201116SG",
        "RMX3630", "CPH2577", "V2307", "I2205",
        "moto g84 5G", "motorola edge 40 neo",
        "Nokia G42 5G", "Nokia X30",
    ]

    uas = set()

    for _ in range(quantidade):
        chrome_major = random.randint(90, 133)
        chrome_minor = random.randint(0, 9)
        chrome_build = random.randint(1000, 6999)
        chrome_patch = random.randint(0, 299)
        chrome = f"{chrome_major}.{chrome_minor}.{chrome_build}.{chrome_patch}"

        ffver = str(random.randint(80, 135)) + ".0"
        safver = f"{random.randint(14, 18)}.{random.randint(0, 3)}"
        edgever = f"{chrome_major}.0.{random.randint(1000, 3000)}.{random.randint(0, 99)}"
        opver = f"{random.randint(80, 115)}.0.{random.randint(1000, 5000)}.{random.randint(0, 99)}"
        sambver = f"{random.randint(18, 25)}.{random.randint(0, 5)}"

        winver = random.choice(winvers)
        arch = random.choice(archs)
        macver = random.choice(macvers)
        iosver = random.choice(iosvers)
        andver = random.choice(andvers)
        device = random.choice(devices)

        tipo = random.random()

        try:
            if tipo < 0.30:
                t = random.choice(bases_chrome)
                ua = t.format(winver=winver, arch=arch, macver=macver, chrome=chrome)
            elif tipo < 0.50:
                t = random.choice(bases_firefox)
                ua = t.format(winver=winver, arch=arch, macver=macver, ffver=ffver)
            elif tipo < 0.62:
                t = random.choice(bases_safari)
                ua = t.format(macver=macver, iosver=iosver, safver=safver)
            elif tipo < 0.75:
                t = random.choice(bases_edge)
                ua = t.format(winver=winver, arch=arch, chrome=chrome, edgever=edgever)
            elif tipo < 0.88:
                t = random.choice(bases_mobile)
                ua = t.format(andver=andver, device=device, chrome=chrome, sambver=sambver)
            elif tipo < 0.95:
                t = random.choice(bases_opera)
                ua = t.format(winver=winver, arch=arch, macver=macver, chrome=chrome, opver=opver)
            else:
                ua = random.choice(bases_bots)

            uas.add(ua)
        except (KeyError, IndexError):
            continue

    uas_list = sorted(list(uas))

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(f"# User Agents - Gerado automaticamente\n")
        f.write(f"# Total: {len(uas_list)} user agents\n")
        f.write(f"# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Fonte: WEB SITE ANALYZER PRO\n\n")
        for ua in uas_list:
            f.write(ua + "\n")

    return uas_list


# ============================================================
# CLASSE PRINCIPAL
# ============================================================
class SiteAnalyzerPro:

    def __init__(self, root):
        self.root = root
        self.root.title("◉ WEB SITE ANALYZER PRO")
        self.root.geometry("1400x900")
        self.root.minsize(1100, 700)
        self.root.configure(bg=BG)

        try:
            self.root.state("zoomed")
        except Exception:
            try:
                self.root.attributes("-zoomed", True)
            except Exception:
                pass

        self.dados_analise = None
        self.user_agents = list(DEFAULT_USER_AGENTS)
        self.ua_file_path = None
        self.ua_mode = tk.StringVar(value="random")
        self.current_ua = tk.StringVar(value=self.user_agents[0])
        self.is_analyzing = False

        self.criar_estilo()
        self.criar_interface()
        self.carregar_ua_padrao()

    # ========================================================
    # ESTILOS
    # ========================================================
    def criar_estilo(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Treeview",
            background=ENTRY_BG,
            foreground=GREEN,
            fieldbackground=ENTRY_BG,
            rowheight=24,
            font=("Consolas", 9)
        )
        style.configure(
            "Treeview.Heading",
            background="#0b210b",
            foreground=GREEN,
            font=("Consolas", 9, "bold")
        )
        style.map(
            "Treeview",
            background=[("selected", SELECTED_BG)],
            foreground=[("selected", "white")]
        )
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#0b210b",
            foreground=GREEN,
            padding=[10, 5],
            font=("Consolas", 8, "bold")
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#1a3a1a")],
            foreground=[("selected", CYAN)]
        )
        style.configure(
            "green.Horizontal.TProgressbar",
            background=GREEN,
            troughcolor=ENTRY_BG
        )

    # ========================================================
    # INTERFACE
    # ========================================================
    def criar_interface(self):
        # --- HEADER ---
        header = tk.Frame(self.root, bg=BG, height=55)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="◉ WEB SITE ANALYZER PRO",
            bg=BG, fg=GREEN,
            font=("Consolas", 18, "bold")
        ).pack(side="left", padx=15)

        self.relogio = tk.Label(
            header, bg=BG, fg=GRAY,
            font=("Consolas", 9)
        )
        self.relogio.pack(side="right", padx=10)

        self.status_label = tk.Label(
            header,
            text="● AGUARDANDO",
            bg=BG, fg=GRAY,
            font=("Consolas", 9, "bold")
        )
        self.status_label.pack(side="right", padx=15)
        self.atualizar_relogio()

        # --- USER AGENT FRAME ---
        ua_frame = tk.Frame(
            self.root, bg="#0a1a0a",
            highlightbackground=DARK_BORDER,
            highlightthickness=1
        )
        ua_frame.pack(fill="x", padx=12, pady=(8, 4))

        tk.Label(
            ua_frame, text="USER AGENT:",
            bg="#0a1a0a", fg=CYAN,
            font=("Consolas", 9, "bold")
        ).pack(side="left", padx=8, pady=6)

        # Modo
        mode_frame = tk.Frame(ua_frame, bg="#0a1a0a")
        mode_frame.pack(side="left", padx=5)

        modos = [
            ("Aleatorio", "random"),
            ("Selecionar", "select"),
            ("Manual", "manual")
        ]
        for txt, val in modos:
            tk.Radiobutton(
                mode_frame, text=txt,
                variable=self.ua_mode, value=val,
                bg="#0a1a0a", fg=GREEN,
                selectcolor=ENTRY_BG,
                activebackground="#0a1a0a",
                activeforeground=GREEN,
                font=("Consolas", 8),
                command=self.ua_mode_changed
            ).pack(side="left", padx=3)

        # Botões UA
        self.btn_load_ua = tk.Button(
            ua_frame, text="Carregar TXT",
            bg="#1a1a2a", fg=BLUE,
            font=("Consolas", 8, "bold"),
            relief="flat", cursor="hand2",
            command=self.carregar_ua_arquivo
        )
        self.btn_load_ua.pack(side="left", padx=5)

        self.btn_gerar_ua = tk.Button(
            ua_frame, text="Gerar 10000",
            bg="#1a2a1a", fg=GREEN,
            font=("Consolas", 8, "bold"),
            relief="flat", cursor="hand2",
            command=self.gerar_ua_arquivo
        )
        self.btn_gerar_ua.pack(side="left", padx=5)

        self.ua_count_label = tk.Label(
            ua_frame, text="UAs: 10",
            bg="#0a1a0a", fg=GRAY,
            font=("Consolas", 8)
        )
        self.ua_count_label.pack(side="right", padx=8)

        self.ua_file_label = tk.Label(
            ua_frame, text="Arquivo: (padrao)",
            bg="#0a1a0a", fg=GRAY,
            font=("Consolas", 8)
        )
        self.ua_file_label.pack(side="right", padx=5)

        # --- UA SELECT FRAME ---
        self.ua_select_frame = tk.Frame(self.root, bg=PANEL)

        tk.Label(
            self.ua_select_frame, text="UA:",
            bg=PANEL, fg=CYAN,
            font=("Consolas", 9, "bold")
        ).pack(side="left", padx=5, pady=4)

        self.ua_combo = ttk.Combobox(
            self.ua_select_frame,
            textvariable=self.current_ua,
            font=("Consolas", 8), width=120
        )
        self.ua_combo['values'] = self.user_agents[:200]
        self.ua_combo.pack(side="left", fill="x", expand=True, padx=5, pady=4)

        # --- UA MANUAL FRAME ---
        self.ua_manual_frame = tk.Frame(self.root, bg=PANEL)

        tk.Label(
            self.ua_manual_frame, text="UA:",
            bg=PANEL, fg=CYAN,
            font=("Consolas", 9, "bold")
        ).pack(side="left", padx=5, pady=4)

        self.ua_manual_entry = tk.Entry(
            self.ua_manual_frame,
            bg=ENTRY_BG, fg=GREEN,
            insertbackground=GREEN,
            font=("Consolas", 8),
            relief="flat"
        )
        self.ua_manual_entry.pack(
            side="left", fill="x", expand=True,
            padx=5, pady=4, ipady=3
        )

        # --- URL BAR ---
        url_frame = tk.Frame(self.root, bg=PANEL, padx=12, pady=10)
        url_frame.pack(fill="x", padx=12, pady=4)

        tk.Label(
            url_frame, text="DIGITE A URL:",
            bg=PANEL, fg=CYAN,
            font=("Consolas", 10, "bold")
        ).pack(side="left")

        self.url_entry = tk.Entry(
            url_frame, bg=ENTRY_BG, fg=GREEN,
            insertbackground=GREEN, relief="flat",
            font=("Consolas", 11),
            selectbackground=SELECTED_BG,
            selectforeground=WHITE
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=10, ipady=6)
        self.url_entry.bind("<Return>", lambda e: self.iniciar_analise())

        # Botões de ação
        self.btn_pdf = tk.Button(
            url_frame, text="PDF",
            bg="#2a1a2a", fg=PURPLE,
            font=("Consolas", 9, "bold"),
            relief="flat", cursor="hand2",
            command=self.exportar_pdf,
            state="disabled"
        )
        self.btn_pdf.pack(side="right", padx=3, ipadx=8, ipady=4)

        self.btn_salvar = tk.Button(
            url_frame, text="SALVAR",
            bg="#1a1a3a", fg=CYAN,
            font=("Consolas", 9, "bold"),
            relief="flat", cursor="hand2",
            command=self.salvar_html,
            state="disabled"
        )
        self.btn_salvar.pack(side="right", padx=3, ipadx=8, ipady=4)

        self.btn_limpar = tk.Button(
            url_frame, text="LIMPAR",
            bg="#2a1a0a", fg=ORANGE,
            font=("Consolas", 9, "bold"),
            relief="flat", cursor="hand2",
            command=self.limpar_tudo
        )
        self.btn_limpar.pack(side="right", padx=3, ipadx=8, ipady=4)

        self.btn_analisar = tk.Button(
            url_frame, text="ANALISAR",
            bg=GREEN, fg="black",
            font=("Consolas", 9, "bold"),
            relief="flat", cursor="hand2",
            command=self.iniciar_analise
        )
        self.btn_analisar.pack(side="right", padx=3, ipadx=8, ipady=4)

        # --- PROGRESS ---
        prog_frame = tk.Frame(self.root, bg=BG)
        prog_frame.pack(fill="x", padx=12)

        self.prog_label = tk.Label(
            prog_frame, text="", bg=BG, fg=GREEN,
            font=("Consolas", 8)
        )
        self.prog_label.pack(side="left")

        self.prog_bar = ttk.Progressbar(
            prog_frame,
            style="green.Horizontal.TProgressbar",
            mode="determinate", maximum=100
        )
        self.prog_bar.pack(fill="x", expand=True, padx=(8, 0), ipady=1)

        # --- CARDS ---
        cards_frame = tk.Frame(self.root, bg=BG)
        cards_frame.pack(fill="x", padx=12, pady=6)

        self.cards = {}
        card_defs = [
            ("STATUS", "--", GREEN),
            ("TAMANHO", "--", CYAN),
            ("LINKS", "0", ORANGE),
            ("SCRIPTS", "0", WHITE),
            ("IMAGENS", "0", GREEN),
            ("FORMS", "0", RED),
            ("TEMPO", "--", PURPLE),
            ("CSS", "0", BLUE),
        ]

        for titulo, valor, cor in card_defs:
            f = tk.Frame(cards_frame, bg=PANEL, bd=1, relief="solid", height=72)
            f.pack(side="left", fill="both", expand=True, padx=2)
            f.pack_propagate(False)
            tk.Label(
                f, text=titulo, bg=PANEL, fg=GRAY,
                font=("Consolas", 7, "bold")
            ).pack(pady=(8, 2))
            lbl = tk.Label(
                f, text=valor, bg=PANEL, fg=cor,
                font=("Consolas", 15, "bold")
            )
            lbl.pack()
            self.cards[titulo] = lbl

        # --- NOTEBOOK ---
        nb_frame = tk.Frame(self.root, bg=BG)
        nb_frame.pack(fill="both", expand=True, padx=12, pady=6)

        self.notebook = ttk.Notebook(nb_frame)
        self.notebook.pack(fill="both", expand=True)

        self.tabs = {}

        # Abas de texto
        text_tabs = [
            ("  GERAL  ", "geral"),
            ("  CONFIAVEL?  ", "trust"),
            ("  TECNOLOGIAS  ", "tech"),
            ("  SEGURANCA  ", "seg"),
            ("  SEO  ", "seo"),
            ("  COOKIES  ", "cookies"),
            ("  UA ATUAL  ", "ua_info"),
        ]

        # Abas de treeview
        tree_tabs = [
            ("  HEADERS  ", "headers", ("chave", "valor"), ("HEADER", "VALOR"), (280, 600)),
            ("  LINKS  ", "links", ("tipo", "dominio", "url"), ("TIPO", "DOMINIO", "URL"), (90, 180, 550)),
            ("  SCRIPTS  ", "scripts", ("tipo", "fonte"), ("TIPO", "FONTE"), (100, 750)),
            ("  IMAGENS  ", "imgs", ("alt", "url"), ("ALT TEXT", "URL"), (250, 600)),
        ]

        # Criar abas na ordem desejada
        ordem = [
            ("geral", "text"),
            ("trust", "text"),
            ("headers", "tree"),
            ("links", "tree"),
            ("tech", "text"),
            ("seg", "text"),
            ("seo", "text"),
            ("scripts", "tree"),
            ("imgs", "tree"),
            ("cookies", "text"),
            ("ua_info", "text"),
        ]

        nomes_abas = {
            "geral": "  GERAL  ",
            "trust": "  CONFIAVEL?  ",
            "headers": "  HEADERS  ",
            "links": "  LINKS  ",
            "tech": "  TECNOLOGIAS  ",
            "seg": "  SEGURANCA  ",
            "seo": "  SEO  ",
            "scripts": "  SCRIPTS  ",
            "imgs": "  IMAGENS  ",
            "cookies": "  COOKIES  ",
            "ua_info": "  UA ATUAL  ",
        }

        tree_configs = {
            "headers": (("chave", "valor"), ("HEADER", "VALOR"), (280, 600)),
            "links": (("tipo", "dominio", "url"), ("TIPO", "DOMINIO", "URL"), (90, 180, 550)),
            "scripts": (("tipo", "fonte"), ("TIPO", "FONTE"), (100, 750)),
            "imgs": (("alt", "url"), ("ALT TEXT", "URL"), (250, 600)),
        }

        for key, tipo in ordem:
            frame = tk.Frame(self.notebook, bg=PANEL)
            self.notebook.add(frame, text=nomes_abas[key])

            if tipo == "text":
                widget = self.criar_textbox(frame)
            else:
                cols, heads, widths = tree_configs[key]
                widget = self.criar_tree(frame, cols, heads, widths)

            self.tabs[key] = widget

        # --- RODAPÉ ---
        rod_frame = tk.Frame(self.root, bg=BG)
        rod_frame.pack(fill="x", padx=12, pady=(0, 6))

        self.rodape = tk.Label(
            rod_frame,
            text="Pronto para analisar.",
            bg=BG, fg=GRAY,
            font=("Consolas", 8), anchor="w"
        )
        self.rodape.pack(side="left")

        tk.Label(
            rod_frame,
            text="WEB ANALYZER PRO",
            bg=BG, fg="#334433",
            font=("Consolas", 7)
        ).pack(side="right")

    # ========================================================
    # WIDGETS AUXILIARES
    # ========================================================
    def criar_textbox(self, parent):
        container = tk.Frame(parent, bg=ENTRY_BG)
        container.pack(fill="both", expand=True)

        sy = tk.Scrollbar(container, orient="vertical")
        sy.pack(side="right", fill="y")

        sx = tk.Scrollbar(container, orient="horizontal")
        sx.pack(side="bottom", fill="x")

        text = tk.Text(
            container, bg=ENTRY_BG, fg=GREEN,
            insertbackground=GREEN,
            font=("Consolas", 9), relief="flat",
            wrap="none",
            yscrollcommand=sy.set,
            xscrollcommand=sx.set,
            selectbackground=SELECTED_BG,
            selectforeground=WHITE,
            padx=10, pady=10
        )
        text.pack(side="left", fill="both", expand=True)
        sy.config(command=text.yview)
        sx.config(command=text.xview)
        return text

    def criar_tree(self, parent, columns, headings, widths):
        container = tk.Frame(parent, bg=ENTRY_BG)
        container.pack(fill="both", expand=True)

        sy = tk.Scrollbar(container, orient="vertical")
        sy.pack(side="right", fill="y")

        sx = tk.Scrollbar(container, orient="horizontal")
        sx.pack(side="bottom", fill="x")

        tree = ttk.Treeview(
            container, columns=columns,
            show="headings",
            yscrollcommand=sy.set,
            xscrollcommand=sx.set
        )

        for col, head, w in zip(columns, headings, widths):
            tree.heading(col, text=head)
            tree.column(col, width=w, anchor="w")

        tree.pack(side="left", fill="both", expand=True)
        sy.config(command=tree.yview)
        sx.config(command=tree.xview)
        return tree

    def atualizar_relogio(self):
        try:
            self.relogio.config(
                text=datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
            )
            self.root.after(1000, self.atualizar_relogio)
        except Exception:
            pass

    # ========================================================
    # USER AGENT MANAGEMENT
    # ========================================================
    def carregar_ua_padrao(self):
        if os.path.exists("useragent.txt"):
            self.carregar_ua_de_arquivo("useragent.txt")
        else:
            self.ua_count_label.config(text=f"UAs: {len(self.user_agents)}")

    def carregar_ua_arquivo(self):
        path = filedialog.askopenfilename(
            title="Selecionar arquivo de User Agents",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            self.carregar_ua_de_arquivo(path)

    def carregar_ua_de_arquivo(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            uas = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    uas.append(line)

            if uas:
                self.user_agents = uas
                self.ua_file_path = path
                nome = os.path.basename(path)
                self.ua_file_label.config(text=f"Arquivo: {nome}")
                self.ua_count_label.config(text=f"UAs: {len(uas):,}")
                self.ua_combo['values'] = uas[:500]
                self.current_ua.set(uas[0])
                self.rodape.config(
                    text=f"{len(uas):,} user agents carregados de {nome}"
                )
            else:
                messagebox.showwarning("Aviso", "Arquivo vazio ou sem UAs validos.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler arquivo:\n{e}")

    def gerar_ua_arquivo(self):
        path = filedialog.asksaveasfilename(
            title="Salvar arquivo de User Agents",
            defaultextension=".txt",
            initialfile="useragent.txt",
            filetypes=[("Text Files", "*.txt")]
        )

        if not path:
            return

        self.rodape.config(text="Gerando 10.000+ user agents...")
        self.root.update()

        def gerar():
            try:
                uas = gerar_useragents_txt(path, 10500)
                self.root.after(0, lambda u=uas, p=path: self._on_ua_gerado(p, u))
            except Exception as e:
                erro_msg = str(e)
                self.root.after(0, lambda m=erro_msg: messagebox.showerror("Erro", f"Erro ao gerar: {m}"))

        threading.Thread(target=gerar, daemon=True).start()

    def _on_ua_gerado(self, path, uas):
        self.user_agents = uas
        self.ua_file_path = path
        nome = os.path.basename(path)
        self.ua_file_label.config(text=f"Arquivo: {nome}")
        self.ua_count_label.config(text=f"UAs: {len(uas):,}")
        self.ua_combo['values'] = uas[:500]
        if uas:
            self.current_ua.set(uas[0])
        self.rodape.config(text=f"{len(uas):,} user agents gerados em {nome}")
        messagebox.showinfo("Sucesso", f"{len(uas):,} user agents gerados!\n{path}")

    def ua_mode_changed(self):
        # Esconder ambos primeiro
        try:
            self.ua_select_frame.pack_forget()
        except Exception:
            pass
        try:
            self.ua_manual_frame.pack_forget()
        except Exception:
            pass

        mode = self.ua_mode.get()
        if mode == "select":
            self.ua_select_frame.pack(fill="x", padx=12, pady=2)
        elif mode == "manual":
            self.ua_manual_frame.pack(fill="x", padx=12, pady=2)

    def get_user_agent(self):
        mode = self.ua_mode.get()
        if mode == "random":
            ua = random.choice(self.user_agents)
        elif mode == "select":
            ua = self.current_ua.get()
        elif mode == "manual":
            ua = self.ua_manual_entry.get().strip()
            if not ua:
                ua = random.choice(self.user_agents)
        else:
            ua = random.choice(self.user_agents)
        return ua

    # ========================================================
    # PROGRESSO / STATUS
    # ========================================================
    def set_progress(self, pct, txt=""):
        try:
            self.prog_bar['value'] = pct
            self.prog_label.config(text=txt)
        except Exception:
            pass

    def set_status(self, text, color):
        try:
            self.status_label.config(text=text, fg=color)
        except Exception:
            pass

    # ========================================================
    # LIMPAR
    # ========================================================
    def limpar_tudo(self):
        for key, widget in self.tabs.items():
            try:
                if isinstance(widget, tk.Text):
                    widget.delete("1.0", tk.END)
                elif isinstance(widget, ttk.Treeview):
                    for item in widget.get_children():
                        widget.delete(item)
            except Exception:
                pass

        for titulo, lbl in self.cards.items():
            try:
                if titulo in ("STATUS", "TAMANHO", "TEMPO"):
                    lbl.config(text="--")
                else:
                    lbl.config(text="0")
            except Exception:
                pass

        self.set_status("● AGUARDANDO", GRAY)
        self.rodape.config(text="Pronto para analisar.")
        self.set_progress(0, "")
        self.btn_salvar.config(state="disabled")
        self.btn_pdf.config(state="disabled")
        self.dados_analise = None

    # ========================================================
    # INICIAR ANÁLISE
    # ========================================================
    def iniciar_analise(self):
        if self.is_analyzing:
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("URL", "Digite uma URL valida.")
            return

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
        self.limpar_tudo()

        self.is_analyzing = True
        self.btn_analisar.config(state="disabled", text="ANALISANDO...")
        self.set_status("● ANALISANDO", ORANGE)
        self.set_progress(5, "Iniciando...")

        threading.Thread(target=self.analisar, args=(url,), daemon=True).start()

    # ========================================================
    # ANÁLISE PRINCIPAL
    # ========================================================
    def analisar(self, url):
        try:
            inicio = time.time()
            user_agent = self.get_user_agent()

            ua_preview = user_agent[:50]
            self.root.after(0, lambda: self.set_progress(8, f"Conectando... UA: {ua_preview}..."))

            headers_req = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            self.root.after(0, lambda: self.set_progress(12, "Requisicao HTTP..."))

            resp = None
            try:
                resp = requests.get(
                    url, headers=headers_req,
                    timeout=30, allow_redirects=True,
                    verify=True
                )
            except requests.exceptions.SSLError:
                resp = requests.get(
                    url, headers=headers_req,
                    timeout=30, allow_redirects=True,
                    verify=False
                )

            tempo_resp = time.time() - inicio

            self.root.after(0, lambda: self.set_progress(25, "Parseando HTML..."))

            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            titulo = ""
            if soup.title and soup.title.string:
                titulo = soup.title.get_text(strip=True)

            servidor = resp.headers.get("Server", "Nao informado")
            content_type = resp.headers.get("Content-Type", "Nao informado")
            tamanho = len(resp.content)

            self.root.after(0, lambda: self.set_progress(40, "Extraindo elementos..."))

            all_links = soup.find_all("a")
            all_imgs = soup.find_all("img")
            all_scripts = soup.find_all("script")
            all_forms = soup.find_all("form")
            all_css = soup.find_all("link", rel=lambda x: x and "stylesheet" in x)
            all_iframes = soup.find_all("iframe")
            all_inputs = soup.find_all("input")

            parsed_base = urlparse(resp.url)
            dominio_base = parsed_base.netloc

            lista_links = []
            links_int = 0
            links_ext = 0

            for link in all_links:
                href = link.get("href")
                if not href:
                    continue
                try:
                    absoluto = urljoin(resp.url, href)
                    parsed = urlparse(absoluto)
                    dominio = parsed.netloc
                    if dominio == dominio_base:
                        tipo_link = "INTERNO"
                        links_int += 1
                    else:
                        tipo_link = "EXTERNO"
                        links_ext += 1
                    lista_links.append((tipo_link, dominio, absoluto))
                except Exception:
                    continue

            lista_scripts = []
            for script in all_scripts:
                src = script.get("src")
                if src:
                    try:
                        abs_src = urljoin(resp.url, src)
                        lista_scripts.append(("EXTERNO", abs_src))
                    except Exception:
                        lista_scripts.append(("EXTERNO", src))
                elif script.string:
                    preview = script.string.strip()[:80]
                    lista_scripts.append(("INLINE", preview + "..."))

            lista_imgs = []
            for img in all_imgs:
                src = img.get("src")
                alt = img.get("alt", "")
                if src:
                    try:
                        abs_src = urljoin(resp.url, src)
                    except Exception:
                        abs_src = src
                    lista_imgs.append((alt if alt else "(sem alt)", abs_src))

            self.root.after(0, lambda: self.set_progress(55, "Detectando tecnologias..."))

            tecnologias = self.detectar_tecnologias(html, resp.headers, soup)

            self.root.after(0, lambda: self.set_progress(65, "Analisando seguranca..."))

            seguranca = self.analisar_seguranca(resp, url)
            seo_result = self.analisar_seo(soup)

            self.root.after(0, lambda: self.set_progress(75, "Verificando confiabilidade..."))

            trust = self.analisar_confiabilidade(
                url, html, resp.headers, soup,
                seguranca, seo_result, tecnologias
            )

            self.root.after(0, lambda: self.set_progress(82, "Processando meta tags..."))

            metas = []
            for meta in soup.find_all("meta"):
                nome = meta.get("name") or meta.get("property") or meta.get("http-equiv")
                valor = meta.get("content")
                if nome and valor:
                    metas.append({"nome": str(nome), "valor": str(valor)})

            lista_forms = []
            for form in all_forms:
                action = form.get("action", "N/A")
                method = form.get("method", "GET").upper()
                campos = []
                for inp in form.find_all("input"):
                    tipo_inp = inp.get("type", "text")
                    nome_inp = inp.get("name", "")
                    campos.append(f"{nome_inp} ({tipo_inp})")
                lista_forms.append({
                    "action": action,
                    "method": method,
                    "campos": campos
                })

            dominios_ext = Counter()
            for _, dominio, _ in lista_links:
                if dominio != dominio_base:
                    dominios_ext[dominio] += 1

            self.root.after(0, lambda: self.set_progress(88, "Analisando cookies..."))

            cookies_data = self.analisar_cookies(html, resp)

            self.root.after(0, lambda: self.set_progress(95, "Compilando resultados..."))

            tempo_total = time.time() - inicio

            dados = {
                "url": resp.url,
                "url_original": url,
                "status": resp.status_code,
                "titulo": titulo,
                "servidor": servidor,
                "tipo": content_type,
                "tamanho": tamanho,
                "tempo": tempo_resp,
                "tempo_total": tempo_total,
                "data_analise": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "links_total": len(all_links),
                "links_internos": links_int,
                "links_externos": links_ext,
                "imagens": len(all_imgs),
                "scripts": len(all_scripts),
                "forms": len(all_forms),
                "css": len(all_css),
                "iframes": len(all_iframes),
                "inputs": len(all_inputs),
                "tecnologias": tecnologias,
                "seguranca": seguranca,
                "seo": seo_result,
                "trust": trust,
                "metas": metas,
                "lista_links": lista_links,
                "lista_scripts": lista_scripts,
                "lista_imgs": lista_imgs,
                "lista_forms": lista_forms,
                "headers": dict(resp.headers),
                "dominios_ext": dict(dominios_ext),
                "encoding": resp.encoding,
                "history": [r.url for r in resp.history],
                "dominio": dominio_base,
                "cookies": cookies_data,
                "user_agent": user_agent,
            }

            self.root.after(0, lambda d=dados: self.mostrar_resultados(d))

        except requests.exceptions.Timeout:
            self.root.after(0, lambda: self.erro("Tempo limite excedido (30s)."))
        except requests.exceptions.ConnectionError:
            self.root.after(0, lambda: self.erro(
                "Nao foi possivel conectar.\nVerifique a URL e sua conexao."
            ))
        except Exception as e:
            erro_msg = str(e)
            self.root.after(0, lambda m=erro_msg: self.erro(f"Erro inesperado:\n{m}"))

    # ========================================================
    # DETECTAR TECNOLOGIAS
    # ========================================================
    def detectar_tecnologias(self, html, headers, soup):
        techs = []
        html_lower = html.lower()
        headers_str = str(headers).lower()
        busca = html_lower + " " + headers_str

        mapeamento = {
            "WordPress": ["wp-content", "wp-includes", "wordpress"],
            "React": ["react", "__react", "react-dom", "_reactroot"],
            "Next.js": ["__next", "next.js", "_next/static"],
            "Vue.js": ["vue.js", "vuejs", "__vue__"],
            "Angular": ["ng-version", "angular", "ng-app"],
            "Nuxt.js": ["__nuxt", "nuxt.js"],
            "Svelte": ["svelte", "__svelte"],
            "Bootstrap": ["bootstrap.min.css", "bootstrap.min.js"],
            "Tailwind CSS": ["tailwindcss", "tailwind.min.css"],
            "jQuery": ["jquery.min.js", "jquery.js", "jquery-"],
            "Google Analytics": ["google-analytics.com", "googletagmanager.com/gtag"],
            "Google Tag Manager": ["googletagmanager.com/gtm"],
            "Font Awesome": ["font-awesome", "fontawesome"],
            "Google Fonts": ["fonts.googleapis.com"],
            "Cloudflare": ["cloudflare", "cf-ray"],
            "Nginx": ["nginx"],
            "Apache": ["apache"],
            "PHP": ["x-powered-by: php", ".php"],
            "ASP.NET": ["asp.net", "__viewstate"],
            "Node.js/Express": ["x-powered-by: express"],
            "Wix": ["wix.com", "wixsite"],
            "Shopify": ["shopify", "cdn.shopify.com"],
            "Squarespace": ["squarespace"],
            "Joomla": ["joomla"],
            "Drupal": ["drupal"],
            "Laravel": ["laravel_session", "laravel"],
            "HTMX": ["htmx.org", "hx-get", "hx-post"],
            "Alpine.js": ["alpine.js", "x-data"],
            "Vite": ["vite", "@vite"],
            "Webpack": ["webpack", "webpackchunk"],
            "Recaptcha": ["recaptcha", "g-recaptcha"],
            "Hotjar": ["hotjar", "hjid"],
            "Facebook Pixel": ["fbq(", "facebook.net/en_us/fbevents"],
            "Gatsby": ["gatsby", "___gatsby"],
            "Material UI": ["mui", "material-ui"],
        }

        for tech, keywords in mapeamento.items():
            for kw in keywords:
                if kw in busca:
                    techs.append(tech)
                    break

        for meta in soup.find_all("meta", attrs={"name": "generator"}):
            content = meta.get("content", "")
            if content:
                techs.append(f"Generator: {content}")

        # Remover duplicatas mantendo ordem
        seen = set()
        unique_techs = []
        for t in techs:
            if t not in seen:
                seen.add(t)
                unique_techs.append(t)

        return unique_techs if unique_techs else ["Nenhuma tecnologia detectada"]

    # ========================================================
    # SEGURANÇA
    # ========================================================
    def analisar_seguranca(self, resp, url):
        resultados = []
        score = 0
        total = 0
        hdrs = resp.headers
        hdrs_lower = {k.lower() for k in hdrs.keys()}

        checks = [
            (
                "HTTPS",
                url.startswith("https://"),
                "Conexao segura via HTTPS",
                "Site nao usa HTTPS - CRITICO"
            ),
            (
                "HSTS",
                "strict-transport-security" in hdrs_lower,
                "HSTS habilitado",
                "HSTS ausente"
            ),
            (
                "CSP",
                "content-security-policy" in hdrs_lower,
                "CSP definido",
                "CSP ausente"
            ),
            (
                "X-Content-Type-Options",
                "x-content-type-options" in hdrs_lower,
                "Protecao MIME sniffing",
                "X-Content-Type-Options ausente"
            ),
            (
                "X-Frame-Options",
                "x-frame-options" in hdrs_lower,
                "Protecao clickjacking",
                "X-Frame-Options ausente"
            ),
            (
                "X-XSS-Protection",
                "x-xss-protection" in hdrs_lower,
                "Protecao XSS",
                "X-XSS-Protection ausente"
            ),
            (
                "Referrer-Policy",
                "referrer-policy" in hdrs_lower,
                "Politica referrer definida",
                "Referrer-Policy ausente"
            ),
            (
                "Permissions-Policy",
                "permissions-policy" in hdrs_lower,
                "Politica permissoes definida",
                "Permissions-Policy ausente"
            ),
            (
                "Server Oculto",
                "server" not in hdrs_lower,
                "Header Server nao exposto",
                f"Server exposto: {hdrs.get('Server', 'N/A')}"
            ),
            (
                "X-Powered-By Oculto",
                "x-powered-by" not in hdrs_lower,
                "X-Powered-By nao exposto",
                f"Exposto: {hdrs.get('X-Powered-By', 'N/A')}"
            ),
        ]

        for nome, ok, msg_ok, msg_fail in checks:
            total += 1
            if ok:
                score += 1
                resultados.append(("✅", nome, msg_ok))
            else:
                resultados.append(("⚠️", nome, msg_fail))

        nota = int(score / total * 100) if total else 0
        if nota >= 80:
            cls = "EXCELENTE"
        elif nota >= 60:
            cls = "BOM"
        elif nota >= 40:
            cls = "REGULAR"
        else:
            cls = "FRACO"

        return {
            "checks": resultados,
            "score": score,
            "total": total,
            "nota": nota,
            "classificacao": cls
        }

    # ========================================================
    # SEO
    # ========================================================
    def analisar_seo(self, soup):
        resultados = []
        score = 0
        total = 0

        # Titulo
        total += 1
        if soup.title and soup.title.string:
            t = soup.title.get_text(strip=True)
            l = len(t)
            if 30 <= l <= 60:
                score += 1
                resultados.append(("✅", "Titulo", f"Presente ({l} chars)"))
            else:
                resultados.append(("⚠️", "Titulo", f"Tamanho nao ideal ({l})"))
        else:
            resultados.append(("❌", "Titulo", "Ausente"))

        # Description
        total += 1
        desc = soup.find("meta", attrs={"name": "description"})
        if desc and desc.get("content"):
            l = len(desc["content"])
            if 120 <= l <= 160:
                score += 1
                resultados.append(("✅", "Meta Description", f"OK ({l} chars)"))
            else:
                resultados.append(("⚠️", "Meta Description", f"Nao ideal ({l})"))
        else:
            resultados.append(("❌", "Meta Description", "Ausente"))

        # H1
        total += 1
        h1s = soup.find_all("h1")
        if len(h1s) == 1:
            score += 1
            resultados.append(("✅", "H1", "1 tag H1"))
        elif len(h1s) > 1:
            resultados.append(("⚠️", "H1", f"{len(h1s)} tags H1"))
        else:
            resultados.append(("❌", "H1", "Nenhuma H1"))

        # H2
        total += 1
        h2s = soup.find_all("h2")
        if h2s:
            score += 1
            resultados.append(("✅", "Headings", f"H2: {len(h2s)}"))
        else:
            resultados.append(("⚠️", "Headings", "Sem H2"))

        # Alt
        total += 1
        imgs = soup.find_all("img")
        sem_alt = sum(1 for i in imgs if not i.get("alt"))
        if imgs:
            if sem_alt == 0:
                score += 1
                resultados.append(("✅", "Alt Imagens", "Todas com alt"))
            else:
                resultados.append(("⚠️", "Alt Imagens", f"{sem_alt}/{len(imgs)} sem alt"))
        else:
            score += 1
            resultados.append(("ℹ️", "Alt Imagens", "Sem imagens"))

        # Viewport
        total += 1
        if soup.find("meta", attrs={"name": "viewport"}):
            score += 1
            resultados.append(("✅", "Viewport", "Presente"))
        else:
            resultados.append(("❌", "Viewport", "Ausente"))

        # Canonical
        total += 1
        if soup.find("link", rel="canonical"):
            score += 1
            resultados.append(("✅", "Canonical", "Presente"))
        else:
            resultados.append(("⚠️", "Canonical", "Ausente"))

        # Lang
        total += 1
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            score += 1
            resultados.append(("✅", "Idioma", f'lang="{html_tag["lang"]}"'))
        else:
            resultados.append(("⚠️", "Idioma", "Ausente"))

        # Open Graph
        total += 1
        if soup.find("meta", property="og:title"):
            score += 1
            resultados.append(("✅", "Open Graph", "Presente"))
        else:
            resultados.append(("⚠️", "Open Graph", "Ausente"))

        nota = int(score / total * 100) if total else 0
        if nota >= 80:
            cls = "EXCELENTE"
        elif nota >= 60:
            cls = "BOM"
        elif nota >= 40:
            cls = "REGULAR"
        else:
            cls = "FRACO"

        return {
            "checks": resultados,
            "score": score,
            "total": total,
            "nota": nota,
            "classificacao": cls
        }

    # ========================================================
    # CONFIABILIDADE
    # ========================================================
    def analisar_confiabilidade(self, url, html, headers, soup, seg, seo, techs):
        checks = []
        score = 0
        total = 0
        html_lower = html.lower()
        dominio = ""
        try:
            dominio = urlparse(url).netloc
        except Exception:
            pass

        # 1. HTTPS (15 pts)
        total += 15
        if url.startswith("https://"):
            score += 15
            checks.append({
                "ok": True,
                "titulo": "Conexao HTTPS",
                "desc": "Conexao criptografada SSL/TLS"
            })
        else:
            checks.append({
                "ok": False,
                "titulo": "Sem HTTPS",
                "desc": "CRITICO: Sem conexao segura"
            })

        # 2. Conteudo (10 pts)
        total += 10
        elems = len(soup.find_all(["p", "article", "section", "main"]))
        if elems > 5:
            score += 10
            checks.append({
                "ok": True,
                "titulo": "Conteudo Substancial",
                "desc": f"{elems} elementos"
            })
        elif elems > 0:
            score += 5
            checks.append({
                "ok": "warn",
                "titulo": "Pouco Conteudo",
                "desc": f"Apenas {elems} elementos"
            })
        else:
            checks.append({
                "ok": False,
                "titulo": "Sem Conteudo",
                "desc": "Nenhum conteudo visivel"
            })

        # 3. Privacidade (10 pts)
        total += 10
        priv_found = False
        for a in soup.find_all("a"):
            texto = a.get_text("", True).lower()
            href = (a.get("href") or "").lower()
            combined = texto + " " + href
            if "privacidade" in combined or "privacy" in combined:
                priv_found = True
                break

        if priv_found:
            score += 10
            checks.append({
                "ok": True,
                "titulo": "Politica de Privacidade",
                "desc": "Link encontrado"
            })
        else:
            checks.append({
                "ok": False,
                "titulo": "Sem Politica de Privacidade",
                "desc": "Nenhum link encontrado"
            })

        # 4. Termos (8 pts)
        total += 8
        termos_found = False
        for a in soup.find_all("a"):
            texto = a.get_text("", True).lower()
            href = (a.get("href") or "").lower()
            combined = texto + " " + href
            if "termos" in combined or "terms" in combined:
                termos_found = True
                break

        if termos_found:
            score += 8
            checks.append({
                "ok": True,
                "titulo": "Termos de Uso",
                "desc": "Link encontrado"
            })
        else:
            checks.append({
                "ok": False,
                "titulo": "Sem Termos de Uso",
                "desc": "Nenhum link"
            })

        # 5. Contato (8 pts)
        total += 8
        contato_count = 0
        for a in soup.find_all("a"):
            texto = a.get_text("", True).lower()
            href = (a.get("href") or "").lower()
            combined = texto + " " + href
            if any(w in combined for w in ["contato", "contact", "mailto:", "tel:"]):
                contato_count += 1

        if contato_count > 0:
            score += 8
            checks.append({
                "ok": True,
                "titulo": "Contato",
                "desc": f"{contato_count} link"
            })
        else:
            checks.append({
                "ok": False,
                "titulo": "Sem Contato",
                "desc": "Nenhum contato visivel"
            })

        # 6. Seguranca (12 pts)
        total += 12
        seg_nota = seg.get("nota", 0)
        if seg_nota >= 60:
            score += 12
            checks.append({
                "ok": True,
                "titulo": "Headers Seguros",
                "desc": f"Score: {seg_nota}%"
            })
        elif seg_nota >= 30:
            score += 6
            checks.append({
                "ok": "warn",
                "titulo": "Headers Parciais",
                "desc": f"Score: {seg_nota}%"
            })
        else:
            checks.append({
                "ok": False,
                "titulo": "Headers Fracos",
                "desc": f"Score: {seg_nota}%"
            })

        # 7. Senhas (10 pts)
        total += 10
        pass_inputs = soup.find_all("input", {"type": "password"})
        if not pass_inputs:
            score += 10
            checks.append({
                "ok": True,
                "titulo": "Sem Coleta de Senhas",
                "desc": "Nenhum campo de senha"
            })
        elif url.startswith("https://"):
            score += 5
            checks.append({
                "ok": "warn",
                "titulo": "Coleta de Senhas",
                "desc": f"{len(pass_inputs)} campo"
            })
        else:
            checks.append({
                "ok": False,
                "titulo": "Senhas sem HTTPS",
                "desc": "PERIGO!"
            })

        # 8. Links suspeitos (8 pts)
        total += 8
        susp_domains = ["bit.ly", "tinyurl", "goo.gl", "adf.ly", "shorte.st"]
        susp_count = 0
        for a in soup.find_all("a"):
            href = (a.get("href") or "").lower()
            if any(d in href for d in susp_domains):
                susp_count += 1

        if susp_count == 0:
            score += 8
            checks.append({
                "ok": True,
                "titulo": "Links Limpos",
                "desc": "Sem encurtadores suspeitos"
            })
        else:
            checks.append({
                "ok": False,
                "titulo": "Links Suspeitos",
                "desc": f"{susp_count} encurtadores"
            })

        # 9. Conteudo suspeito (7 pts)
        total += 7
        spam_words = [
            "ganhe dinheiro rapido",
            "bitcoin gratis",
            "premio exclusivo",
            "100% gratis"
        ]
        found_spam = [w for w in spam_words if w in html_lower]
        if not found_spam:
            score += 7
            checks.append({
                "ok": True,
                "titulo": "Conteudo Legitimo",
                "desc": "Sem padroes de spam"
            })
        else:
            checks.append({
                "ok": False,
                "titulo": "Conteudo Suspeito",
                "desc": f"Padroes: {', '.join(found_spam)}"
            })

        # 10. Favicon (3 pts)
        total += 3
        favicon = soup.find("link", rel=re.compile("icon", re.I))
        if favicon:
            score += 3
            checks.append({
                "ok": True,
                "titulo": "Favicon",
                "desc": "Presente"
            })
        else:
            checks.append({
                "ok": "warn",
                "titulo": "Sem Favicon",
                "desc": "Nao encontrado"
            })

        # 11. Meta tags (5 pts)
        total += 5
        has_desc = soup.find("meta", attrs={"name": "description"})
        has_og = soup.find("meta", property="og:title")
        if has_desc and has_og:
            score += 5
            checks.append({
                "ok": True,
                "titulo": "Meta Tags Completas",
                "desc": "Description + OG"
            })
        elif has_desc or has_og:
            score += 2
            checks.append({
                "ok": "warn",
                "titulo": "Meta Tags Parciais",
                "desc": "Algumas ausentes"
            })
        else:
            checks.append({
                "ok": False,
                "titulo": "Sem Meta Tags",
                "desc": "Ausentes"
            })

        nota = round(score / total * 100) if total else 0

        if nota >= 80:
            verdict = "SITE CONFIAVEL"
            cor = GREEN
        elif nota >= 60:
            verdict = "PROVAVELMENTE SEGURO"
            cor = CYAN
        elif nota >= 40:
            verdict = "SITE SUSPEITO - CUIDADO"
            cor = ORANGE
        else:
            verdict = "POTENCIALMENTE PERIGOSO"
            cor = RED

        return {
            "checks": checks,
            "score": score,
            "total": total,
            "nota": nota,
            "verdict": verdict,
            "verdictColor": cor,
            "dominio": dominio
        }

    # ========================================================
    # COOKIES
    # ========================================================
    def analisar_cookies(self, html, resp):
        cookies_list = []
        html_lower = html.lower()

        # Cookies da resposta
        for cookie in resp.cookies:
            cookies_list.append({
                "nome": cookie.name,
                "valor": (cookie.value or "")[:50],
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
                "httponly": cookie.has_nonstandard_attr("httponly"),
                "expires": str(cookie.expires) if cookie.expires else "Sessao"
            })

        # Rastreadores
        trackers = []
        tracker_patterns = {
            "Google Analytics": ["_ga", "_gid", "_gat", "google-analytics.com"],
            "Facebook": ["_fbp", "_fbc", "facebook.net"],
            "Hotjar": ["_hj", "_hjid", "hotjar"],
            "Cloudflare": ["__cf_bm", "__cfduid", "cloudflare"],
            "Google Ads": ["_gcl_au", "_gcl_aw"],
            "LinkedIn": ["bcookie", "li_sugr"],
            "Twitter": ["guest_id", "personalization_id"],
        }

        for tracker, patterns in tracker_patterns.items():
            for p in patterns:
                if p.lower() in html_lower:
                    trackers.append(tracker)
                    break

        # Banner cookies
        has_banner = False
        if "cookie" in html_lower:
            consent_words = ["consent", "aceitar", "accept", "lgpd", "gdpr"]
            has_banner = any(w in html_lower for w in consent_words)

        return {
            "cookies": cookies_list,
            "trackers": list(set(trackers)),
            "hasCookieBanner": has_banner
        }

    # ========================================================
    # MOSTRAR RESULTADOS
    # ========================================================
    def mostrar_resultados(self, d):
        self.dados_analise = d
        self.is_analyzing = False
        self.set_progress(100, "Concluido!")

        # Cards
        sc = d["status"]
        cor_st = GREEN if sc < 300 else ORANGE if sc < 400 else RED
        self.cards["STATUS"].config(text=str(sc), fg=cor_st)
        self.cards["TAMANHO"].config(text=self.fmt_size(d["tamanho"]))
        self.cards["LINKS"].config(text=str(d["links_total"]))
        self.cards["SCRIPTS"].config(text=str(d["scripts"]))
        self.cards["IMAGENS"].config(text=str(d["imagens"]))
        self.cards["FORMS"].config(text=str(d["forms"]))
        self.cards["TEMPO"].config(text=f"{d['tempo']:.2f}s")
        self.cards["CSS"].config(text=str(d["css"]))

        SEP = "=" * 70 + "\n"
        SUB = "-" * 70 + "\n"

        # --- ABA GERAL ---
        g = ""
        g += SEP
        g += "        RELATORIO DE ANALISE\n"
        g += SEP + "\n"
        g += f"  Data:          {d['data_analise']}\n"
        g += f"  URL:           {d['url']}\n"
        g += f"  Dominio:       {d['dominio']}\n"
        g += f"  Status:        {d['status']}\n"
        g += f"  Titulo:        {d['titulo']}\n"
        g += f"  Servidor:      {d['servidor']}\n"
        g += f"  Tamanho:       {self.fmt_size(d['tamanho'])}\n"
        g += f"  Tempo:         {d['tempo']:.3f}s\n"
        g += f"  User-Agent:    {d['user_agent'][:80]}...\n\n"
        g += SEP
        g += "        ELEMENTOS\n"
        g += SEP
        g += f"  Links: {d['links_total']} "
        g += f"(int:{d['links_internos']} ext:{d['links_externos']})\n"
        g += f"  Imagens: {d['imagens']}  Scripts: {d['scripts']}  "
        g += f"Forms: {d['forms']}  CSS: {d['css']}\n"
        g += f"  Iframes: {d['iframes']}  Inputs: {d['inputs']}\n"

        domsExt = sorted(d["dominios_ext"].items(), key=lambda x: -x[1])[:15]
        if domsExt:
            g += "\n" + SEP
            g += "        DOMINIOS EXTERNOS\n"
            g += SEP
            for dm, cnt in domsExt:
                g += f"  {dm}: {cnt}\n"

        if d["metas"]:
            g += "\n" + SEP
            g += "        META TAGS\n"
            g += SEP
            for m in d["metas"]:
                g += f"  {m['nome']}: {m['valor']}\n"

        g += "\n" + SEP
        g += "        CONFIABILIDADE\n"
        g += SEP
        g += f"  Nota: {d['trust']['nota']}% - {d['trust']['verdict']}\n"

        self.tabs["geral"].delete("1.0", tk.END)
        self.tabs["geral"].insert("1.0", g)

        # --- ABA CONFIABILIDADE ---
        tr = d["trust"]
        t = ""
        t += SEP
        t += "        ANALISE DE CONFIABILIDADE\n"
        t += f"        Dominio: {tr['dominio']}\n"
        t += SEP + "\n"

        nota_bars = tr["nota"] // 5
        barra = "#" * nota_bars
        vazio = "-" * (20 - nota_bars)
        t += f"  NOTA: {tr['nota']}% [{barra}{vazio}]\n"
        t += f"  VEREDICTO: {tr['verdict']}\n"
        t += f"  Score: {tr['score']}/{tr['total']} pontos\n\n"
        t += SEP + "\n"

        for c in tr["checks"]:
            if c["ok"] is True:
                icon = "[OK]"
            elif c["ok"] == "warn":
                icon = "[!!]"
            else:
                icon = "[XX]"
            t += f"  {icon}  {c['titulo']}\n"
            t += f"       {c['desc']}\n"
            t += SUB

        t += "\n  Analise automatica baseada em heuristicas.\n"

        self.tabs["trust"].delete("1.0", tk.END)
        self.tabs["trust"].insert("1.0", t)

        # --- ABA HEADERS ---
        tree_headers = self.tabs["headers"]
        for item in tree_headers.get_children():
            tree_headers.delete(item)
        for k, v in d["headers"].items():
            tree_headers.insert("", "end", values=(k, str(v)))

        # --- ABA LINKS ---
        tree_links = self.tabs["links"]
        for item in tree_links.get_children():
            tree_links.delete(item)
        for tipo_l, dom, link in d["lista_links"]:
            tree_links.insert("", "end", values=(tipo_l, dom, link))

        # --- ABA TECNOLOGIAS ---
        tt = ""
        tt += SEP
        tt += "        TECNOLOGIAS DETECTADAS\n"
        tt += SEP + "\n"
        for i, tech in enumerate(d["tecnologias"], 1):
            tt += f"  [{i:02d}]  *  {tech}\n"
        tt += f"\n  Total: {len(d['tecnologias'])}\n"

        self.tabs["tech"].delete("1.0", tk.END)
        self.tabs["tech"].insert("1.0", tt)

        # --- ABA SEGURANÇA ---
        seg = d["seguranca"]
        ss = ""
        ss += SEP
        ss += "        ANALISE DE SEGURANCA\n"
        ss += SEP + "\n"
        seg_bars = seg["nota"] // 5
        barra = "#" * seg_bars
        vazio = "-" * (20 - seg_bars)
        ss += f"  NOTA: {seg['nota']}% [{barra}{vazio}] {seg['classificacao']}\n"
        ss += f"  {seg['score']}/{seg['total']} passaram\n\n"
        ss += SEP + "\n"
        for ic, n, m in seg["checks"]:
            ss += f"  {ic}  {n}\n       {m}\n"
            ss += SUB

        self.tabs["seg"].delete("1.0", tk.END)
        self.tabs["seg"].insert("1.0", ss)

        # --- ABA SEO ---
        seo = d["seo"]
        os_txt = ""
        os_txt += SEP
        os_txt += "        ANALISE DE SEO\n"
        os_txt += SEP + "\n"
        seo_bars = seo["nota"] // 5
        barra = "#" * seo_bars
        vazio = "-" * (20 - seo_bars)
        os_txt += f"  NOTA: {seo['nota']}% [{barra}{vazio}] {seo['classificacao']}\n"
        os_txt += f"  {seo['score']}/{seo['total']} passaram\n\n"
        os_txt += SEP + "\n"
        for ic, n, m in seo["checks"]:
            os_txt += f"  {ic}  {n}\n       {m}\n"
            os_txt += SUB

        self.tabs["seo"].delete("1.0", tk.END)
        self.tabs["seo"].insert("1.0", os_txt)

        # --- ABA SCRIPTS ---
        tree_scripts = self.tabs["scripts"]
        for item in tree_scripts.get_children():
            tree_scripts.delete(item)
        for tipo_s, src in d["lista_scripts"]:
            tree_scripts.insert("", "end", values=(tipo_s, src))

        # --- ABA IMAGENS ---
        tree_imgs = self.tabs["imgs"]
        for item in tree_imgs.get_children():
            tree_imgs.delete(item)
        for alt, src in d["lista_imgs"]:
            tree_imgs.insert("", "end", values=(alt, src))

        # --- ABA COOKIES ---
        ck = d["cookies"]
        ct = ""
        ct += SEP
        ct += "        COOKIES & RASTREAMENTO\n"
        ct += SEP + "\n"

        if ck["hasCookieBanner"]:
            ct += "  Banner Cookies: [OK] Detectado\n"
        else:
            ct += "  Banner Cookies: [!!] Nao detectado\n"

        ct += f"\n  Cookies recebidos: {len(ck['cookies'])}\n"

        if ck["cookies"]:
            ct += "\n" + SEP
            ct += "        COOKIES HTTP\n"
            ct += SEP + "\n"
            for i, c in enumerate(ck["cookies"], 1):
                ct += f"  Cookie #{i}\n"
                ct += SUB
                ct += f"    Nome:    {c['nome']}\n"
                ct += f"    Valor:   {c['valor']}...\n"
                ct += f"    Domain:  {c['domain']}\n"
                ct += f"    Path:    {c['path']}\n"
                ct += f"    Secure:  {c['secure']}\n"
                ct += f"    Expires: {c['expires']}\n\n"

        if ck["trackers"]:
            ct += SEP
            ct += "        RASTREADORES\n"
            ct += SEP + "\n"
            for i, tracker in enumerate(ck["trackers"], 1):
                ct += f"  [{i:02d}]  >>  {tracker}\n"

        self.tabs["cookies"].delete("1.0", tk.END)
        self.tabs["cookies"].insert("1.0", ct)

        # --- ABA USER AGENT ---
        ua_txt = ""
        ua_txt += SEP
        ua_txt += "        USER AGENT UTILIZADO\n"
        ua_txt += SEP + "\n"
        ua_txt += f"  {d['user_agent']}\n\n"
        ua_txt += SEP
        ua_txt += "        DETALHES\n"
        ua_txt += SEP + "\n"
        ua_txt += f"  Modo:         {self.ua_mode.get()}\n"
        ua_txt += f"  Arquivo:      {self.ua_file_path or '(padrao)'}\n"
        ua_txt += f"  Total UAs:    {len(self.user_agents):,}\n"

        self.tabs["ua_info"].delete("1.0", tk.END)
        self.tabs["ua_info"].insert("1.0", ua_txt)

        # --- FINALIZAR ---
        self.set_status("● CONCLUIDO", GREEN)
        self.rodape.config(
            text=(
                f"HTTP {d['status']} | {d['tempo']:.2f}s | "
                f"{self.fmt_size(d['tamanho'])} | "
                f"{len(d['tecnologias'])} techs | "
                f"Seg:{seg['nota']}% | SEO:{seo['nota']}% | "
                f"Confianca:{tr['nota']}%"
            )
        )

        self.btn_analisar.config(state="normal", text="ANALISAR")
        self.btn_salvar.config(state="normal")
        self.btn_pdf.config(state="normal")

    # ========================================================
    # UTILITÁRIOS
    # ========================================================
    def fmt_size(self, t):
        if t < 1024:
            return f"{t} B"
        if t < 1024 * 1024:
            return f"{t / 1024:.1f} KB"
        return f"{t / (1024 * 1024):.2f} MB"

    def erro(self, msg):
        self.is_analyzing = False
        self.set_status("● ERRO", RED)
        self.rodape.config(text="Erro na analise.")
        self.btn_analisar.config(state="normal", text="ANALISAR")
        self.set_progress(0, "Erro!")
        messagebox.showerror("Erro", msg)

    # ========================================================
    # SALVAR HTML
    # ========================================================
    def salvar_html(self):
        if not self.dados_analise:
            messagebox.showwarning("Salvar", "Nenhuma analise.")
            return

        arquivo = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html")],
            initialfile=f"analise_{self.dados_analise['dominio']}.html"
        )

        if not arquivo:
            return

        try:
            html = self.gerar_relatorio_html(self.dados_analise)
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write(html)
            messagebox.showinfo("Salvo!", f"Relatorio salvo:\n{arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar:\n{e}")

    # ========================================================
    # EXPORTAR PDF (via browser print)
    # ========================================================
    def exportar_pdf(self):
        if not self.dados_analise:
            messagebox.showwarning("PDF", "Nenhuma analise.")
            return

        try:
            html = self.gerar_relatorio_html(self.dados_analise)

            tmp = tempfile.NamedTemporaryFile(
                suffix=".html", delete=False, mode="w",
                encoding="utf-8"
            )
            tmp.write(html)
            tmp_name = tmp.name
            tmp.close()

            webbrowser.open("file://" + os.path.abspath(tmp_name))
            messagebox.showinfo(
                "PDF",
                "O relatorio foi aberto no navegador.\n"
                "Use Ctrl+P para salvar como PDF."
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar:\n{e}")

    
    # ========================================================
    # GERAR RELATÓRIO HTML COMPLETO - PROFISSIONAL COM GRÁFICOS
    # ========================================================
    def gerar_relatorio_html(self, d):
        seg = d["seguranca"]
        seo = d["seo"]
        tr = d["trust"]
        ck = d["cookies"]

        def esc(s):
            return (str(s)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&#39;"))

        def score_cor(n):
            if n >= 80:
                return "#00ff41"
            if n >= 60:
                return "#00e5ff"
            if n >= 40:
                return "#ff9900"
            return "#ff3333"

        sc = d["status"]
        st_cor = "#00ff41" if sc < 300 else "#ff9900" if sc < 400 else "#ff3333"

        # ========== TECNOLOGIAS ==========
        techs_html = ""
        for i, t in enumerate(d["tecnologias"], 1):
            techs_html += (
                f'<span class="tech-badge">'
                f'{i:02d}. {esc(t)}</span>'
            )

        # ========== CHECKS SEGURANCA/SEO ==========
        def mk_checks(checks):
            result = ""
            for ic, n, m in checks:
                is_ok = "✅" in str(ic)
                is_fail = "❌" in str(ic)
                cls = "check-ok" if is_ok else "check-fail" if is_fail else "check-warn"
                result += (
                    f'<div class="check-item {cls} searchable">'
                    f'<span class="check-icon">{esc(ic)}</span>'
                    f'<div class="check-content">'
                    f'<strong>{esc(n)}</strong>'
                    f'<p>{esc(m)}</p></div></div>'
                )
            return result

        # ========== CONFIABILIDADE ==========
        trust_checks_html = ""
        for c in tr["checks"]:
            ok = c["ok"]
            cls = "check-ok" if ok is True else "check-warn" if ok == "warn" else "check-fail"
            ic = "✅" if ok is True else "⚠️" if ok == "warn" else "❌"
            trust_checks_html += (
                f'<div class="check-item {cls} searchable">'
                f'<span class="check-icon">{ic}</span>'
                f'<div class="check-content">'
                f'<strong>{esc(c["titulo"])}</strong>'
                f'<p>{esc(c["desc"])}</p></div></div>'
            )

        # ========== HEADERS ==========
        hdr_rows = ""
        for k, v in d["headers"].items():
            hdr_rows += (
                f'<tr class="searchable"><td class="td-key">'
                f'{esc(k)}</td><td>{esc(v)}</td></tr>'
            )

        # ========== LINKS ==========
        link_rows = ""
        for tipo_l, dm, u in d["lista_links"]:
            cls_tipo = "tipo-int" if tipo_l == "INTERNO" else "tipo-ext"
            link_rows += (
                f'<tr class="searchable"><td class="{cls_tipo}">{esc(tipo_l)}</td>'
                f'<td class="td-domain">{esc(dm)}</td>'
                f'<td><a href="{esc(u)}" target="_blank">{esc(u)}</a></td></tr>'
            )

        # ========== IMAGENS ==========
        img_rows = ""
        for a, s in d["lista_imgs"]:
            img_rows += (
                f'<tr class="searchable"><td class="td-alt">{esc(a)}</td>'
                f'<td><a href="{esc(s)}" target="_blank">{esc(s)}</a></td></tr>'
            )

        # ========== SCRIPTS ==========
        script_rows = ""
        for tipo_s, src in d["lista_scripts"]:
            cls_tipo = "tipo-ext" if tipo_s == "EXTERNO" else "tipo-inline"
            script_rows += (
                f'<tr class="searchable"><td class="{cls_tipo}">'
                f'{esc(tipo_s)}</td>'
                f'<td class="td-mono">{esc(src)}</td></tr>'
            )

        # ========== META TAGS ==========
        meta_rows = ""
        for m in d["metas"]:
            meta_rows += (
                f'<tr class="searchable"><td class="td-key">'
                f'{esc(m["nome"])}</td><td>{esc(m["valor"])}</td></tr>'
            )

        # ========== DOMÍNIOS EXTERNOS ==========
        dom_ext_sorted = sorted(d["dominios_ext"].items(), key=lambda x: -x[1])
        dom_ext_rows = ""
        max_dom = dom_ext_sorted[0][1] if dom_ext_sorted else 1
        for dm, cnt in dom_ext_sorted:
            pct = int(cnt / max_dom * 100)
            dom_ext_rows += (
                f'<tr class="searchable"><td class="td-domain">{esc(dm)}</td>'
                f'<td class="td-count">{cnt}</td>'
                f'<td><div class="mini-bar"><div class="mini-bar-fill" '
                f'style="width:{pct}%"></div></div></td></tr>'
            )

        # ========== FORMULÁRIOS ==========
        forms_html = ""
        if d.get("lista_forms"):
            for i, fm in enumerate(d["lista_forms"], 1):
                campos_items = ""
                for c in fm.get("campos", []):
                    campos_items += f'<span class="campo-badge">{esc(c)}</span>'
                if not campos_items:
                    campos_items = '<em class="empty-text">Nenhum campo</em>'
                method_cls = "method-post" if fm.get("method", "GET") == "POST" else "method-get"
                forms_html += (
                    f'<div class="form-card searchable">'
                    f'<div class="form-header">Formulario #{i} '
                    f'<span class="{method_cls}">{esc(fm.get("method", "GET"))}</span></div>'
                    f'<div class="form-body">'
                    f'<div class="form-row"><span class="form-label">Action:</span>'
                    f'<span class="form-value">{esc(fm.get("action", "N/A"))}</span></div>'
                    f'<div class="form-row"><span class="form-label">Campos:</span>'
                    f'<div class="campos-list">{campos_items}</div></div>'
                    f'</div></div>'
                )
        else:
            forms_html = '<p class="empty-text">Nenhum formulario encontrado.</p>'

        # ========== COOKIES ==========
        cookies_html = ""
        if ck["cookies"]:
            for i, c in enumerate(ck["cookies"], 1):
                secure_cls = "badge-ok" if c["secure"] else "badge-fail"
                secure_txt = "Sim" if c["secure"] else "Nao"
                http_cls = "badge-ok" if c.get("httponly", False) else "badge-fail"
                http_txt = "Sim" if c.get("httponly", False) else "Nao"
                cookies_html += (
                    f'<div class="cookie-card searchable">'
                    f'<div class="cookie-header">'
                    f'<span class="cookie-num">#{i}</span>'
                    f'<span class="cookie-name">{esc(c["nome"])}</span></div>'
                    f'<table class="cookie-table">'
                    f'<tr><td class="ck-label">Valor</td><td>{esc(c["valor"])}...</td></tr>'
                    f'<tr><td class="ck-label">Domain</td><td>{esc(c["domain"])}</td></tr>'
                    f'<tr><td class="ck-label">Path</td><td>{esc(c["path"])}</td></tr>'
                    f'<tr><td class="ck-label">Secure</td><td><span class="{secure_cls}">{secure_txt}</span></td></tr>'
                    f'<tr><td class="ck-label">HttpOnly</td><td><span class="{http_cls}">{http_txt}</span></td></tr>'
                    f'<tr><td class="ck-label">Expires</td><td>{esc(c["expires"])}</td></tr>'
                    f'</table></div>'
                )
        else:
            cookies_html = '<p class="empty-text">Nenhum cookie recebido.</p>'

        # ========== RASTREADORES ==========
        trackers_html = ""
        if ck["trackers"]:
            for t in ck["trackers"]:
                trackers_html += f'<span class="tracker-badge">{esc(t)}</span>'
        else:
            trackers_html = '<p class="empty-text">Nenhum rastreador detectado.</p>'

        cookie_banner_icon = "✅" if ck["hasCookieBanner"] else "⚠️"
        cookie_banner_txt = "Detectado" if ck["hasCookieBanner"] else "Nao detectado"
        cookie_banner_cls = "badge-ok" if ck["hasCookieBanner"] else "badge-warn"

        # ========== REDIRECIONAMENTOS ==========
        history_html = ""
        if d.get("history"):
            for i, h in enumerate(d["history"], 1):
                history_html += (
                    f'<div class="redirect-item searchable">'
                    f'<span class="redirect-num">#{i}</span>'
                    f'<a href="{esc(h)}" target="_blank">{esc(h)}</a></div>'
                )
        else:
            history_html = '<p class="empty-text">Sem redirecionamentos.</p>'

        # ========== DADOS DOS GRAFICOS ==========
        # Grafico Donut - Scores
        trust_nota = tr["nota"]
        seg_nota = seg["nota"]
        seo_nota = seo["nota"]

        # Grafico de elementos
        elem_links = d["links_total"]
        elem_imgs = d["imagens"]
        elem_scripts = d["scripts"]
        elem_forms = d["forms"]
        elem_css = d["css"]
        elem_iframes = d["iframes"]
        elem_total = max(elem_links + elem_imgs + elem_scripts + elem_forms + elem_css + elem_iframes, 1)

        # Grafico links int/ext
        links_int = d["links_internos"]
        links_ext = d["links_externos"]
        links_total = max(links_int + links_ext, 1)

        # ========== MENU DE NAVEGACAO ==========
        menu_items = [
            ("sec-info", "📋", "Info Geral"),
            ("sec-cards", "📊", "Dashboard"),
            ("sec-graficos", "📈", "Graficos"),
            ("sec-trust", "🛡", "Confiabilidade"),
            ("sec-seg", "🔒", "Seguranca"),
            ("sec-seo", "🔍", "SEO"),
            ("sec-tech", "🛠", "Tecnologias"),
            ("sec-headers", "📋", "Headers"),
            ("sec-meta", "🏷", "Meta Tags"),
            ("sec-links", "🔗", "Links"),
            ("sec-domext", "🌐", "Dom. Externos"),
            ("sec-scripts", "📜", "Scripts"),
            ("sec-imgs", "🖼", "Imagens"),
            ("sec-forms", "📝", "Formularios"),
            ("sec-cookies", "🍪", "Cookies"),
            ("sec-redir", "↪", "Redirecionamentos"),
            ("sec-ua", "🌐", "User Agent"),
            ("sec-resumo", "📊", "Resumo Final"),
        ]

        nav_items_html = ""
        for sec_id, icon, label in menu_items:
            nav_items_html += (
                f'<a href="#{sec_id}" class="nav-item" '
                f'onclick="scrollToSection(\'{sec_id}\')">'
                f'<span class="nav-icon">{icon}</span>'
                f'<span class="nav-label">{label}</span></a>'
            )

        # ========== HTML COMPLETO ==========
        html_output = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Analise: {esc(d['dominio'])} - WEB ANALYZER PRO</title>
<style>
/* ===== RESET & BASE ===== */
*{{margin:0;padding:0;box-sizing:border-box}}
html{{scroll-behavior:smooth;scroll-padding-top:90px}}
body{{
    background:#050505;
    color:#c0c0c0;
    font-family:'Segoe UI',Consolas,monospace;
    line-height:1.6;
    overflow-x:hidden
}}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar{{width:8px;height:8px}}
::-webkit-scrollbar-track{{background:#0a0a0a}}
::-webkit-scrollbar-thumb{{background:#1a3a1a;border-radius:4px}}
::-webkit-scrollbar-thumb:hover{{background:#2a5a2a}}

/* ===== SIDEBAR NAV ===== */
.sidebar{{
    position:fixed;
    left:0;top:0;bottom:0;
    width:56px;
    background:#080808;
    border-right:1px solid #1a3a1a;
    z-index:1000;
    overflow-y:auto;
    overflow-x:hidden;
    transition:width .3s;
    padding-top:10px
}}
.sidebar:hover{{width:200px}}
.sidebar:hover .nav-label{{opacity:1;width:auto}}
.nav-item{{
    display:flex;
    align-items:center;
    gap:10px;
    padding:10px 16px;
    color:#668866;
    text-decoration:none;
    font-size:12px;
    white-space:nowrap;
    transition:all .2s;
    border-left:3px solid transparent
}}
.nav-item:hover{{
    background:#0d1f0d;
    color:#00ff41;
    border-left-color:#00ff41
}}
.nav-item.active{{
    color:#00ff41;
    border-left-color:#00ff41;
    background:#0a1a0a
}}
.nav-icon{{font-size:16px;min-width:20px;text-align:center}}
.nav-label{{opacity:0;transition:opacity .3s;font-size:11px}}

/* ===== MAIN CONTENT ===== */
.main{{margin-left:56px;padding:20px 30px;min-width:0}}

/* ===== SEARCH BAR ===== */
.search-container{{
    position:sticky;
    top:0;
    z-index:500;
    background:rgba(5,5,5,.95);
    backdrop-filter:blur(10px);
    padding:12px 0;
    border-bottom:1px solid #1a3a1a;
    margin-bottom:20px;
    display:flex;
    gap:10px;
    align-items:center
}}
.search-input{{
    flex:1;
    background:#0a0a0a;
    border:1px solid #1a3a1a;
    color:#00ff41;
    padding:10px 16px;
    border-radius:25px;
    font-size:13px;
    font-family:Consolas,monospace;
    outline:none;
    transition:border-color .3s
}}
.search-input:focus{{border-color:#00ff41;box-shadow:0 0 10px rgba(0,255,65,.15)}}
.search-input::placeholder{{color:#334433}}
.search-count{{
    color:#668866;
    font-size:11px;
    min-width:100px;
    text-align:right
}}
.search-btn{{
    background:#00ff41;
    color:#000;
    border:none;
    padding:10px 20px;
    border-radius:25px;
    font-weight:bold;
    font-size:12px;
    cursor:pointer;
    font-family:Consolas,monospace;
    transition:all .2s
}}
.search-btn:hover{{background:#00cc33;transform:scale(1.05)}}
.clear-btn{{
    background:#2a1a0a;
    color:#ff9900;
    border:1px solid #4a2a0a;
    padding:10px 16px;
    border-radius:25px;
    font-size:12px;
    cursor:pointer;
    font-family:Consolas,monospace;
    transition:all .2s
}}
.clear-btn:hover{{background:#3a2a1a}}
.highlight{{background:#4a4a00;color:#ffff00;padding:1px 2px;border-radius:2px}}

/* ===== HEADER ===== */
.page-header{{
    text-align:center;
    padding:30px 0 20px;
    border-bottom:2px solid #1a3a1a;
    margin-bottom:25px
}}
.page-header h1{{
    color:#00ff41;
    font-size:28px;
    text-shadow:0 0 20px rgba(0,255,65,.3);
    letter-spacing:2px
}}
.page-header .subtitle{{color:#668866;margin-top:8px;font-size:13px}}
.page-header .date{{color:#444;font-size:11px;margin-top:4px}}

/* ===== SECTIONS ===== */
.section{{
    background:#0c0c0c;
    border:1px solid #1a3a1a;
    border-radius:10px;
    margin-bottom:20px;
    overflow:visible;
    scroll-margin-top:90px;
    min-width:0;
    transition:all .3s
}}
.section:hover{{border-color:#2a4a2a;box-shadow:0 4px 15px rgba(0,255,65,.05)}}
.section-header{{
    display:flex;
    align-items:center;
    justify-content:space-between;
    flex-wrap:wrap;
    gap:10px;
    padding:16px 20px;
    background:#0a0a0a;
    border-bottom:1px solid #1a3a1a;
    cursor:pointer;
    user-select:none;
    transition:background .2s
}}
.section-header:hover{{background:#0d1f0d}}
.section-header h2{{
    color:#00ff41;
    font-size:15px;
    display:flex;
    align-items:center;
    gap:10px
}}
.section-header .toggle-icon{{
    color:#668866;
    font-size:18px;
    transition:transform .3s
}}
.section-header .toggle-icon.collapsed{{transform:rotate(-90deg)}}
.section-body{{padding:20px;min-width:0;max-width:100%;overflow-x:auto;transition:all .3s}}
.section-body.collapsed{{display:none}}
.section-count{{
    background:#1a3a1a;
    color:#00ff41;
    padding:3px 10px;
    border-radius:12px;
    font-size:11px;
    font-weight:bold
}}

/* ===== CARDS DASHBOARD ===== */
.cards-grid{{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
    gap:10px;
    margin:15px 0
}}
.dash-card{{
    background:linear-gradient(135deg,#0a0a0a,#111);
    border:1px solid #1a3a1a;
    padding:16px;
    border-radius:10px;
    text-align:center;
    transition:all .3s
}}
.dash-card:hover{{transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,255,65,.1);border-color:#2a5a2a}}
.dash-card .card-title{{color:#668866;font-size:9px;text-transform:uppercase;letter-spacing:2px}}
.dash-card .card-value{{font-size:26px;font-weight:900;margin-top:6px}}

/* ===== GRAFICOS ===== */
.charts-grid{{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
    gap:20px;
    margin:15px 0;
    min-width:0
}}
.chart-box{{
    background:#0a0a0a;
    border:1px solid #1a3a1a;
    border-radius:10px;
    padding:20px;
    text-align:center;
    min-width:0
}}
.chart-box h3{{color:#00e5ff;font-size:13px;margin-bottom:15px;text-transform:uppercase;letter-spacing:1px}}

/* Donut Chart CSS */
.donut-container{{display:flex;justify-content:center;align-items:center;gap:20px;flex-wrap:wrap}}
.donut{{position:relative;width:120px;height:120px}}
.donut svg{{transform:rotate(-90deg)}}
.donut-center{{
    position:absolute;
    top:50%;left:50%;
    transform:translate(-50%,-50%);
    text-align:center
}}
.donut-value{{font-size:22px;font-weight:900}}
.donut-label{{font-size:9px;color:#668866;text-transform:uppercase}}

/* Bar Chart CSS */
.bar-chart{{width:100%}}
.bar-item{{display:flex;align-items:center;gap:10px;margin:8px 0}}
.bar-label{{width:80px;font-size:11px;color:#668866;text-align:right}}
.bar-track{{flex:1;height:22px;background:#111;border-radius:11px;overflow:hidden;border:1px solid #1a1a1a}}
.bar-fill{{height:100%;border-radius:11px;transition:width 1s ease;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;font-size:10px;font-weight:bold;color:#000}}
.bar-count{{width:40px;font-size:12px;font-weight:bold;text-align:left}}

/* ===== INFO ROWS ===== */
.info-grid{{display:grid;gap:1px;background:#1a1a1a;border-radius:8px;overflow:hidden}}
.info-row{{
    display:flex;
    flex-wrap:wrap;
    gap:6px 12px;
    padding:10px 16px;
    background:#0a0a0a;
    transition:background .2s
}}
.info-row:hover{{background:#0d1f0d}}
.info-label{{color:#668866;width:180px;max-width:100%;font-weight:bold;font-size:12px;flex-shrink:0}}
.info-val{{color:#00ff41;flex:1;min-width:0;overflow-wrap:anywhere;word-break:break-word;font-size:12px}}

/* ===== TABLES ===== */
table{{width:100%;border-collapse:collapse;background:#0a0a0a;border-radius:8px;overflow:hidden}}
thead{{position:static}}
th{{
    background:#0d1f0d;
    color:#00ff41;
    padding:12px;
    text-align:left;
    font-size:11px;
    text-transform:uppercase;
    letter-spacing:1px;
    border-bottom:2px solid #1a3a1a
}}
td{{
    padding:9px 12px;
    border-bottom:1px solid #111;
    font-size:11px;
    word-break:break-all;
    vertical-align:top;
    overflow-wrap:anywhere
}}
tr:hover td{{background:#0d1f0d}}
.td-key{{color:#00e5ff;font-weight:bold;width:250px}}
.td-domain{{color:#b8ffb8}}
.td-alt{{color:#b8ffb8;width:250px}}
.td-mono{{font-family:Consolas,monospace;color:#c0c0c0}}
.td-count{{color:#ff9900;font-weight:bold;text-align:center;width:80px}}
.tipo-int{{color:#00ff41;font-weight:bold}}
.tipo-ext{{color:#ff9900;font-weight:bold}}
.tipo-inline{{color:#cc66ff;font-weight:bold}}
a{{color:#00e5ff;text-decoration:none;transition:color .2s}}
a:hover{{color:#00ff41;text-decoration:underline}}

/* ===== MINI BAR ===== */
.mini-bar{{height:14px;background:#111;border-radius:7px;overflow:hidden;min-width:100px}}
.mini-bar-fill{{height:100%;background:linear-gradient(90deg,#00ff41,#00e5ff);border-radius:7px}}

/* ===== PROGRESS BAR ===== */
.progress-wrap{{margin:12px 0}}
.progress-bar{{height:28px;background:#0a0a0a;border-radius:14px;overflow:hidden;border:1px solid #1a3a1a}}
.progress-fill{{
    height:100%;border-radius:14px;
    display:flex;align-items:center;justify-content:center;
    font-size:12px;font-weight:bold;color:#000;
    transition:width 1.5s ease
}}
.score-big{{font-size:38px;font-weight:900;text-align:center;padding:10px 0}}
.score-sub{{color:#668866;text-align:center;font-size:13px;margin:5px 0 15px}}

/* ===== BADGES ===== */
.tech-badge{{
    display:inline-block;
    background:#1a3a1a;
    color:#00ff41;
    padding:7px 15px;
    border-radius:20px;
    margin:4px;
    font-size:12px;
    border:1px solid #2a5a2a;
    transition:all .2s
}}
.tech-badge:hover{{background:#2a5a2a;transform:scale(1.05)}}
.tracker-badge{{
    display:inline-block;
    background:#2a1a0a;
    color:#ff9900;
    padding:7px 15px;
    border-radius:20px;
    margin:4px;
    font-size:12px;
    border:1px solid #4a2a0a
}}
.badge-ok{{
    display:inline-block;
    background:rgba(0,255,65,.1);
    color:#00ff41;
    padding:2px 10px;
    border-radius:10px;
    font-size:11px;
    font-weight:bold
}}
.badge-fail{{
    display:inline-block;
    background:rgba(255,51,51,.1);
    color:#ff3333;
    padding:2px 10px;
    border-radius:10px;
    font-size:11px;
    font-weight:bold
}}
.badge-warn{{
    display:inline-block;
    background:rgba(255,153,0,.1);
    color:#ff9900;
    padding:2px 10px;
    border-radius:10px;
    font-size:11px;
    font-weight:bold
}}
.campo-badge{{
    display:inline-block;
    background:#111;
    color:#b8ffb8;
    padding:3px 10px;
    border-radius:8px;
    margin:2px;
    font-size:11px;
    border:1px solid #1a3a1a
}}
.method-post{{
    background:#ff3333;color:#fff;
    padding:2px 8px;border-radius:4px;font-size:10px;font-weight:bold
}}
.method-get{{
    background:#00e5ff;color:#000;
    padding:2px 8px;border-radius:4px;font-size:10px;font-weight:bold
}}

/* ===== CHECK ITEMS ===== */
.check-item{{
    display:flex;
    gap:12px;
    padding:12px;
    margin:6px 0;
    border-radius:8px;
    border-left:4px solid;
    transition:all .2s
}}
.check-item:hover{{transform:translateX(4px)}}
.check-ok{{background:rgba(0,255,65,.04);border-color:#00ff41}}
.check-fail{{background:rgba(255,51,51,.04);border-color:#ff3333}}
.check-warn{{background:rgba(255,153,0,.04);border-color:#ff9900}}
.check-icon{{font-size:16px;min-width:24px}}
.check-content strong{{color:#e0e0e0;font-size:13px}}
.check-content p{{color:#888;font-size:11px;margin-top:3px}}

/* ===== FORM/COOKIE CARDS ===== */
.form-card,.cookie-card{{
    background:#0a0a0a;
    border:1px solid #1a3a1a;
    border-radius:8px;
    margin:10px 0;
    overflow:hidden;
    transition:all .2s
}}
.form-card:hover,.cookie-card:hover{{border-color:#2a5a2a}}
.form-header,.cookie-header{{
    padding:12px 16px;
    background:#0d0d0d;
    border-bottom:1px solid #1a3a1a;
    color:#00ff41;
    font-weight:bold;
    font-size:13px;
    display:flex;
    align-items:center;
    gap:10px
}}
.form-body{{padding:14px 16px}}
.form-row{{margin:6px 0;display:flex;gap:10px;align-items:flex-start}}
.form-label{{color:#00e5ff;font-weight:bold;width:80px;font-size:12px}}
.form-value{{color:#c0c0c0;font-size:12px}}
.campos-list{{display:flex;flex-wrap:wrap;gap:4px}}
.cookie-num{{
    background:#1a3a1a;
    color:#00ff41;
    padding:2px 8px;
    border-radius:4px;
    font-size:11px
}}
.cookie-name{{color:#00e5ff}}
.cookie-table{{margin:0}}
.cookie-table td{{padding:6px 12px;font-size:11px}}
.ck-label{{color:#668866;width:100px;font-weight:bold}}

/* ===== REDIRECT ===== */
.redirect-item{{
    padding:8px 14px;
    background:#0a0a0a;
    border-left:3px solid #ff9900;
    margin:5px 0;
    border-radius:0 6px 6px 0;
    display:flex;
    gap:10px;
    align-items:center
}}
.redirect-num{{color:#ff9900;font-weight:bold}}

/* ===== SUMMARY ===== */
.summary-grid{{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
    gap:12px;
    margin:15px 0
}}
.sm-card{{
    background:#0a0a0a;
    border-left:4px solid #00ff41;
    padding:14px;
    border-radius:0 8px 8px 0;
    transition:all .2s
}}
.sm-card:hover{{transform:translateX(4px)}}
.sm-title{{color:#668866;font-size:10px;text-transform:uppercase;letter-spacing:1px}}
.sm-value{{font-size:22px;font-weight:900;margin-top:4px}}

/* ===== EMPTY TEXT ===== */
.empty-text{{color:#444;font-style:italic;padding:15px;text-align:center}}

/* ===== UA BOX ===== */
.ua-box{{
    background:#0a0a0a;
    padding:16px;
    border-radius:8px;
    border:1px solid #1a3a1a;
    font-family:Consolas,monospace;
    color:#00ff41;
    word-break:break-all;
    font-size:12px;
    line-height:1.8
}}

/* ===== VERDICT BANNER ===== */
.verdict-banner{{
    text-align:center;
    padding:20px;
    border-radius:10px;
    margin:15px 0;
    font-size:20px;
    font-weight:900;
    letter-spacing:2px
}}

/* ===== BTN TOP ===== */
.btn-top{{
    position:fixed;
    bottom:30px;right:30px;
    width:48px;height:48px;
    background:#00ff41;
    color:#000;
    border:none;
    border-radius:50%;
    font-size:20px;
    cursor:pointer;
    z-index:999;
    box-shadow:0 4px 15px rgba(0,255,65,.3);
    transition:all .3s;
    display:none
}}
.btn-top:hover{{transform:scale(1.1);background:#00cc33}}
.btn-top.visible{{display:block}}

/* ===== RESPONSIVIDADE / ANTI-SOBREPOSICAO ===== */
@media (max-width: 900px){{
    .main{{padding:16px 14px;margin-left:56px}}
    .charts-grid{{grid-template-columns:minmax(0,1fr)}}
    .cards-grid{{grid-template-columns:repeat(auto-fit,minmax(110px,1fr))}}
}}
@media (max-width: 600px){{
    .main{{padding:12px 10px;margin-left:48px}}
    .sidebar{{width:48px}}
    .sidebar:hover{{width:190px}}
    .page-header h1{{font-size:20px;letter-spacing:1px}}
    .section-body{{padding:12px}}
    .info-row{{display:block}}
    .info-label{{display:block;width:auto;margin-bottom:4px}}
    .info-val{{display:block;width:100%}}
    .charts-grid{{grid-template-columns:minmax(0,1fr)}}
    .chart-box{{padding:12px}}
    table{{min-width:520px}}
    .section-body:has(> table){{overflow-x:auto}}
    .search-container{{flex-wrap:wrap}}
    .search-input{{min-width:100%;}}
    .search-count{{min-width:0}}
}}
/* ===== PRINT ===== */
.no-print{{}}
@media print{{
    .sidebar,.search-container,.btn-top,.no-print{{display:none !important}}
    .main{{margin-left:0 !important}}
    body{{background:#fff;color:#333}}
    .section{{border-color:#ddd;break-inside:avoid}}
    .section-header{{background:#f5f5f5}}
    .section-header h2{{color:#111}}
    h1{{color:#111;text-shadow:none}}
    .dash-card,.chart-box,.sm-card,.form-card,.cookie-card{{background:#f9f9f9;border-color:#ddd}}
    .check-ok{{background:#e8f5e9}}
    .check-fail{{background:#ffebee}}
    .check-warn{{background:#fff3e0}}
    th{{background:#e0e0e0;color:#000}}
    a{{color:#0066cc}}
}}
</style>
</head>
<body>

<!-- SIDEBAR -->
<nav class="sidebar no-print">
{nav_items_html}
</nav>

<!-- MAIN -->
<div class="main">

<!-- SEARCH BAR -->
<div class="search-container no-print">
    <input type="text" class="search-input" id="searchInput"
        placeholder="Pesquisar em todo o relatorio..."
        onkeyup="doSearch()" onkeydown="if(event.key==='Enter')doSearch()">
    <button class="search-btn" onclick="doSearch()">PESQUISAR</button>
    <button class="clear-btn" onclick="clearSearch()">LIMPAR</button>
    <span class="search-count" id="searchCount"></span>
</div>

<!-- HEADER -->
<div class="page-header" id="sec-top">
    <h1>◉ WEB SITE ANALYZER PRO</h1>
    <p class="subtitle">Relatorio Completo de Analise</p>
    <p class="date">{d['data_analise']} |
    <a href="{esc(d['url'])}" target="_blank">{esc(d['url'])}</a></p>
</div>

<!-- ==================== INFO GERAL ==================== -->
<div class="section" id="sec-info">
<div class="section-header" onclick="toggleSection(this)">
    <h2>📋 INFORMACOES GERAIS</h2>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<div class="info-grid">
    <div class="info-row searchable"><span class="info-label">URL Analisada</span>
    <span class="info-val"><a href="{esc(d['url'])}" target="_blank">{esc(d['url'])}</a></span></div>
    <div class="info-row searchable"><span class="info-label">URL Original</span>
    <span class="info-val">{esc(d['url_original'])}</span></div>
    <div class="info-row searchable"><span class="info-label">Dominio</span>
    <span class="info-val">{esc(d['dominio'])}</span></div>
    <div class="info-row searchable"><span class="info-label">Status HTTP</span>
    <span class="info-val" style="color:{st_cor};font-weight:bold;font-size:16px">{d['status']}</span></div>
    <div class="info-row searchable"><span class="info-label">Titulo</span>
    <span class="info-val">{esc(d['titulo'])}</span></div>
    <div class="info-row searchable"><span class="info-label">Servidor</span>
    <span class="info-val">{esc(d['servidor'])}</span></div>
    <div class="info-row searchable"><span class="info-label">Content-Type</span>
    <span class="info-val">{esc(d['tipo'])}</span></div>
    <div class="info-row searchable"><span class="info-label">Encoding</span>
    <span class="info-val">{esc(d.get('encoding', 'N/A'))}</span></div>
    <div class="info-row searchable"><span class="info-label">Tamanho</span>
    <span class="info-val">{self.fmt_size(d['tamanho'])} ({d['tamanho']:,} bytes)</span></div>
    <div class="info-row searchable"><span class="info-label">Tempo Resposta</span>
    <span class="info-val">{d['tempo']:.3f}s</span></div>
    <div class="info-row searchable"><span class="info-label">Tempo Total</span>
    <span class="info-val">{d['tempo_total']:.3f}s</span></div>
    <div class="info-row searchable"><span class="info-label">Data Analise</span>
    <span class="info-val">{d['data_analise']}</span></div>
</div>
</div></div>

<!-- ==================== DASHBOARD ==================== -->
<div class="section" id="sec-cards">
<div class="section-header" onclick="toggleSection(this)">
    <h2>📊 DASHBOARD</h2>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<div class="cards-grid">
    <div class="dash-card"><div class="card-title">STATUS</div>
    <div class="card-value" style="color:{st_cor}">{d['status']}</div></div>
    <div class="dash-card"><div class="card-title">TAMANHO</div>
    <div class="card-value" style="color:#00e5ff">{self.fmt_size(d['tamanho'])}</div></div>
    <div class="dash-card"><div class="card-title">LINKS</div>
    <div class="card-value" style="color:#ff9900">{d['links_total']}</div></div>
    <div class="dash-card"><div class="card-title">SCRIPTS</div>
    <div class="card-value" style="color:#b8ffb8">{d['scripts']}</div></div>
    <div class="dash-card"><div class="card-title">IMAGENS</div>
    <div class="card-value" style="color:#00ff41">{d['imagens']}</div></div>
    <div class="dash-card"><div class="card-title">FORMULARIOS</div>
    <div class="card-value" style="color:#ff3333">{d['forms']}</div></div>
    <div class="dash-card"><div class="card-title">TEMPO</div>
    <div class="card-value" style="color:#cc66ff">{d['tempo']:.2f}s</div></div>
    <div class="dash-card"><div class="card-title">CSS</div>
    <div class="card-value" style="color:#3399ff">{d['css']}</div></div>
    <div class="dash-card"><div class="card-title">IFRAMES</div>
    <div class="card-value" style="color:#ff9900">{d['iframes']}</div></div>
    <div class="dash-card"><div class="card-title">INPUTS</div>
    <div class="card-value" style="color:#b8ffb8">{d['inputs']}</div></div>
    <div class="dash-card"><div class="card-title">CONFIANCA</div>
    <div class="card-value" style="color:{tr['verdictColor']}">{tr['nota']}%</div></div>
    <div class="dash-card"><div class="card-title">SEGURANCA</div>
    <div class="card-value" style="color:{score_cor(seg['nota'])}">{seg['nota']}%</div></div>
</div>
</div></div>

<!-- ==================== GRAFICOS ==================== -->
<div class="section" id="sec-graficos">
<div class="section-header" onclick="toggleSection(this)">
    <h2>📈 GRAFICOS & ESTATISTICAS</h2>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<div class="charts-grid">

    <!-- Donut: Scores -->
    <div class="chart-box">
        <h3>Scores Gerais</h3>
        <div class="donut-container">
            <div class="donut">
                <svg width="120" height="120" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="50" fill="none" stroke="#1a1a1a" stroke-width="12"/>
                    <circle cx="60" cy="60" r="50" fill="none" stroke="{tr['verdictColor']}" stroke-width="12"
                        stroke-dasharray="{trust_nota * 3.14} {314 - trust_nota * 3.14}" stroke-linecap="round"/>
                </svg>
                <div class="donut-center">
                    <div class="donut-value" style="color:{tr['verdictColor']}">{trust_nota}%</div>
                    <div class="donut-label">Confianca</div>
                </div>
            </div>
            <div class="donut">
                <svg width="120" height="120" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="50" fill="none" stroke="#1a1a1a" stroke-width="12"/>
                    <circle cx="60" cy="60" r="50" fill="none" stroke="{score_cor(seg_nota)}" stroke-width="12"
                        stroke-dasharray="{seg_nota * 3.14} {314 - seg_nota * 3.14}" stroke-linecap="round"/>
                </svg>
                <div class="donut-center">
                    <div class="donut-value" style="color:{score_cor(seg_nota)}">{seg_nota}%</div>
                    <div class="donut-label">Seguranca</div>
                </div>
            </div>
            <div class="donut">
                <svg width="120" height="120" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="50" fill="none" stroke="#1a1a1a" stroke-width="12"/>
                    <circle cx="60" cy="60" r="50" fill="none" stroke="{score_cor(seo_nota)}" stroke-width="12"
                        stroke-dasharray="{seo_nota * 3.14} {314 - seo_nota * 3.14}" stroke-linecap="round"/>
                </svg>
                <div class="donut-center">
                    <div class="donut-value" style="color:{score_cor(seo_nota)}">{seo_nota}%</div>
                    <div class="donut-label">SEO</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Barras: Elementos -->
    <div class="chart-box">
        <h3>Distribuicao de Elementos</h3>
        <div class="bar-chart">
            <div class="bar-item"><span class="bar-label">Links</span>
            <div class="bar-track"><div class="bar-fill" style="width:{int(elem_links/elem_total*100)}%;background:#ff9900">{elem_links}</div></div></div>
            <div class="bar-item"><span class="bar-label">Imagens</span>
            <div class="bar-track"><div class="bar-fill" style="width:{int(elem_imgs/elem_total*100)}%;background:#00ff41">{elem_imgs}</div></div></div>
            <div class="bar-item"><span class="bar-label">Scripts</span>
            <div class="bar-track"><div class="bar-fill" style="width:{int(elem_scripts/elem_total*100)}%;background:#00e5ff">{elem_scripts}</div></div></div>
            <div class="bar-item"><span class="bar-label">Forms</span>
            <div class="bar-track"><div class="bar-fill" style="width:{int(elem_forms/elem_total*100)}%;background:#ff3333">{elem_forms}</div></div></div>
            <div class="bar-item"><span class="bar-label">CSS</span>
            <div class="bar-track"><div class="bar-fill" style="width:{int(elem_css/elem_total*100)}%;background:#3399ff">{elem_css}</div></div></div>
            <div class="bar-item"><span class="bar-label">Iframes</span>
            <div class="bar-track"><div class="bar-fill" style="width:{int(elem_iframes/elem_total*100)}%;background:#cc66ff">{elem_iframes}</div></div></div>
        </div>
    </div>

    <!-- Barras: Links Int/Ext -->
    <div class="chart-box">
        <h3>Links Internos vs Externos</h3>
        <div class="bar-chart">
            <div class="bar-item"><span class="bar-label">Internos</span>
            <div class="bar-track"><div class="bar-fill" style="width:{int(links_int/links_total*100)}%;background:#00ff41">{links_int}</div></div>
            <span class="bar-count" style="color:#00ff41">{int(links_int/links_total*100)}%</span></div>
            <div class="bar-item"><span class="bar-label">Externos</span>
            <div class="bar-track"><div class="bar-fill" style="width:{int(links_ext/links_total*100)}%;background:#ff9900">{links_ext}</div></div>
            <span class="bar-count" style="color:#ff9900">{int(links_ext/links_total*100)}%</span></div>
        </div>
        <div style="margin-top:15px;padding:10px;background:#111;border-radius:8px;text-align:center">
            <span style="color:#668866">Total: </span>
            <span style="color:#00ff41;font-weight:bold;font-size:18px">{d['links_total']}</span>
            <span style="color:#668866"> links</span>
        </div>
    </div>

    <!-- Cookies/Trackers -->
    <div class="chart-box">
        <h3>Cookies & Rastreamento</h3>
        <div style="display:flex;justify-content:center;gap:30px;margin:15px 0">
            <div style="text-align:center">
                <div style="font-size:36px;font-weight:900;color:#00e5ff">{len(ck['cookies'])}</div>
                <div style="color:#668866;font-size:10px">COOKIES</div>
            </div>
            <div style="text-align:center">
                <div style="font-size:36px;font-weight:900;color:#ff9900">{len(ck['trackers'])}</div>
                <div style="color:#668866;font-size:10px">TRACKERS</div>
            </div>
        </div>
        <div style="text-align:center;margin-top:10px">
            <span class="{cookie_banner_cls}">{cookie_banner_icon} Banner: {cookie_banner_txt}</span>
        </div>
    </div>

</div>
</div></div>

<!-- ==================== CONFIABILIDADE ==================== -->
<div class="section" id="sec-trust">
<div class="section-header" onclick="toggleSection(this)">
    <h2>🛡 ANALISE DE CONFIABILIDADE</h2>
    <span class="section-count">{tr['nota']}%</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<div class="score-big" style="color:{tr['verdictColor']}">{tr['nota']}%</div>
<div class="verdict-banner" style="background:rgba({('0,255,65' if tr['nota']>=80 else '0,229,255' if tr['nota']>=60 else '255,153,0' if tr['nota']>=40 else '255,51,51')},.08);color:{tr['verdictColor']};border:2px solid {tr['verdictColor']}">
{tr['verdict']}
</div>
<div class="progress-wrap">
    <div class="progress-bar"><div class="progress-fill" style="width:{tr['nota']}%;background:{tr['verdictColor']}">{tr['nota']}%</div></div>
</div>
<div class="score-sub">{tr['score']}/{tr['total']} pontos</div>
{trust_checks_html}
</div></div>

<!-- ==================== SEGURANCA ==================== -->
<div class="section" id="sec-seg">
<div class="section-header" onclick="toggleSection(this)">
    <h2>🔒 ANALISE DE SEGURANCA</h2>
    <span class="section-count">{seg['nota']}% - {seg['classificacao']}</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<div class="score-big" style="color:{score_cor(seg['nota'])}">{seg['nota']}%</div>
<div class="score-sub">{seg['classificacao']} - {seg['score']}/{seg['total']} verificacoes</div>
<div class="progress-wrap">
    <div class="progress-bar"><div class="progress-fill" style="width:{seg['nota']}%;background:{score_cor(seg['nota'])}">{seg['nota']}%</div></div>
</div>
{mk_checks(seg['checks'])}
</div></div>

<!-- ==================== SEO ==================== -->
<div class="section" id="sec-seo">
<div class="section-header" onclick="toggleSection(this)">
    <h2>🔍 ANALISE DE SEO</h2>
    <span class="section-count">{seo['nota']}% - {seo['classificacao']}</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<div class="score-big" style="color:{score_cor(seo['nota'])}">{seo['nota']}%</div>
<div class="score-sub">{seo['classificacao']} - {seo['score']}/{seo['total']} verificacoes</div>
<div class="progress-wrap">
    <div class="progress-bar"><div class="progress-fill" style="width:{seo['nota']}%;background:{score_cor(seo['nota'])}">{seo['nota']}%</div></div>
</div>
{mk_checks(seo['checks'])}
</div></div>

<!-- ==================== TECNOLOGIAS ==================== -->
<div class="section" id="sec-tech">
<div class="section-header" onclick="toggleSection(this)">
    <h2>🛠 TECNOLOGIAS DETECTADAS</h2>
    <span class="section-count">{len(d['tecnologias'])}</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<div style="padding:10px 0">{techs_html}</div>
</div></div>

<!-- ==================== HEADERS ==================== -->
<div class="section" id="sec-headers">
<div class="section-header" onclick="toggleSection(this)">
    <h2>📋 HEADERS HTTP</h2>
    <span class="section-count">{len(d['headers'])}</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<table><thead><tr><th>Header</th><th>Valor</th></tr></thead>
<tbody>{hdr_rows}</tbody></table>
</div></div>

<!-- ==================== META TAGS ==================== -->
<div class="section" id="sec-meta">
<div class="section-header" onclick="toggleSection(this)">
    <h2>🏷 META TAGS</h2>
    <span class="section-count">{len(d['metas'])}</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<table><thead><tr><th>Nome / Property</th><th>Conteudo</th></tr></thead>
<tbody>{meta_rows if meta_rows else '<tr><td colspan="2" class="empty-text">Nenhuma meta tag</td></tr>'}</tbody></table>
</div></div>

<!-- ==================== LINKS ==================== -->
<div class="section" id="sec-links">
<div class="section-header" onclick="toggleSection(this)">
    <h2>🔗 LINKS ENCONTRADOS</h2>
    <span class="section-count">{d['links_total']} (Int:{d['links_internos']} Ext:{d['links_externos']})</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<table><thead><tr><th style="width:90px">Tipo</th><th style="width:200px">Dominio</th><th>URL</th></tr></thead>
<tbody>{link_rows if link_rows else '<tr><td colspan="3" class="empty-text">Nenhum link</td></tr>'}</tbody></table>
</div></div>

<!-- ==================== DOMINIOS EXTERNOS ==================== -->
<div class="section" id="sec-domext">
<div class="section-header" onclick="toggleSection(this)">
    <h2>🌐 DOMINIOS EXTERNOS</h2>
    <span class="section-count">{len(d['dominios_ext'])}</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<table><thead><tr><th>Dominio</th><th style="width:80px;text-align:center">Qtd</th><th>Distribuicao</th></tr></thead>
<tbody>{dom_ext_rows if dom_ext_rows else '<tr><td colspan="3" class="empty-text">Nenhum</td></tr>'}</tbody></table>
</div></div>

<!-- ==================== SCRIPTS ==================== -->
<div class="section" id="sec-scripts">
<div class="section-header" onclick="toggleSection(this)">
    <h2>📜 SCRIPTS</h2>
    <span class="section-count">{d['scripts']}</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<table><thead><tr><th style="width:100px">Tipo</th><th>Fonte / Conteudo</th></tr></thead>
<tbody>{script_rows if script_rows else '<tr><td colspan="2" class="empty-text">Nenhum script</td></tr>'}</tbody></table>
</div></div>

<!-- ==================== IMAGENS ==================== -->
<div class="section" id="sec-imgs">
<div class="section-header" onclick="toggleSection(this)">
    <h2>🖼 IMAGENS</h2>
    <span class="section-count">{d['imagens']}</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<table><thead><tr><th style="width:250px">Alt Text</th><th>URL</th></tr></thead>
<tbody>{img_rows if img_rows else '<tr><td colspan="2" class="empty-text">Nenhuma imagem</td></tr>'}</tbody></table>
</div></div>

<!-- ==================== FORMULARIOS ==================== -->
<div class="section" id="sec-forms">
<div class="section-header" onclick="toggleSection(this)">
    <h2>📝 FORMULARIOS</h2>
    <span class="section-count">{d['forms']}</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
{forms_html}
</div></div>

<!-- ==================== COOKIES ==================== -->
<div class="section" id="sec-cookies">
<div class="section-header" onclick="toggleSection(this)">
    <h2>🍪 COOKIES & RASTREAMENTO</h2>
    <span class="section-count">{len(ck['cookies'])} cookies / {len(ck['trackers'])} trackers</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<div class="info-grid" style="margin-bottom:20px">
    <div class="info-row"><span class="info-label">Banner Cookies</span>
    <span class="info-val"><span class="{cookie_banner_cls}">{cookie_banner_icon} {cookie_banner_txt}</span></span></div>
    <div class="info-row"><span class="info-label">Total Cookies</span>
    <span class="info-val">{len(ck['cookies'])}</span></div>
    <div class="info-row"><span class="info-label">Rastreadores</span>
    <span class="info-val">{len(ck['trackers'])}</span></div>
</div>
<h3 style="color:#00e5ff;margin:15px 0 10px">Rastreadores Detectados</h3>
<div style="padding:5px 0">{trackers_html}</div>
<h3 style="color:#00e5ff;margin:20px 0 10px">Cookies HTTP Detalhados</h3>
{cookies_html}
</div></div>

<!-- ==================== REDIRECIONAMENTOS ==================== -->
<div class="section" id="sec-redir">
<div class="section-header" onclick="toggleSection(this)">
    <h2>↪ REDIRECIONAMENTOS</h2>
    <span class="section-count">{len(d.get('history', []))}</span>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
{history_html}
</div></div>

<!-- ==================== USER AGENT ==================== -->
<div class="section" id="sec-ua">
<div class="section-header" onclick="toggleSection(this)">
    <h2>🌐 USER AGENT</h2>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body">
<div class="ua-box">{esc(d['user_agent'])}</div>
<div class="info-grid" style="margin-top:15px">
    <div class="info-row"><span class="info-label">Modo</span>
    <span class="info-val">{self.ua_mode.get()}</span></div>
    <div class="info-row"><span class="info-label">Arquivo UA</span>
    <span class="info-val">{esc(self.ua_file_path or '(padrao)')}</span></div>
    <div class="info-row"><span class="info-label">Total de UAs</span>
    <span class="info-val">{len(self.user_agents):,}</span></div>
</div>
</div></div>

<!-- ==================== RESUMO FINAL ==================== -->
<div class="section" id="sec-resumo" style="border:2px solid #00ff41">
<div class="section-header" onclick="toggleSection(this)" style="background:linear-gradient(135deg,#0a1a0a,#0a0a1a)">
    <h2>📊 RESUMO FINAL</h2>
    <span class="toggle-icon">▼</span>
</div>
<div class="section-body" style="background:linear-gradient(135deg,#080808,#0a0a12)">
<div class="summary-grid">
    <div class="sm-card"><div class="sm-title">Status HTTP</div>
    <div class="sm-value" style="color:{st_cor}">{d['status']}</div></div>
    <div class="sm-card" style="border-color:{tr['verdictColor']}"><div class="sm-title">Confiabilidade</div>
    <div class="sm-value" style="color:{tr['verdictColor']}">{tr['nota']}%</div></div>
    <div class="sm-card" style="border-color:{score_cor(seg['nota'])}"><div class="sm-title">Seguranca</div>
    <div class="sm-value" style="color:{score_cor(seg['nota'])}">{seg['nota']}%</div></div>
    <div class="sm-card" style="border-color:{score_cor(seo['nota'])}"><div class="sm-title">SEO</div>
    <div class="sm-value" style="color:{score_cor(seo['nota'])}">{seo['nota']}%</div></div>
    <div class="sm-card"><div class="sm-title">Tecnologias</div>
    <div class="sm-value">{len(d['tecnologias'])}</div></div>
    <div class="sm-card"><div class="sm-title">Headers</div>
    <div class="sm-value">{len(d['headers'])}</div></div>
    <div class="sm-card"><div class="sm-title">Meta Tags</div>
    <div class="sm-value">{len(d['metas'])}</div></div>
    <div class="sm-card"><div class="sm-title">Links</div>
    <div class="sm-value" style="color:#ff9900">{d['links_total']}</div></div>
    <div class="sm-card"><div class="sm-title">Imagens</div>
    <div class="sm-value" style="color:#00ff41">{d['imagens']}</div></div>
    <div class="sm-card"><div class="sm-title">Scripts</div>
    <div class="sm-value" style="color:#00e5ff">{d['scripts']}</div></div>
    <div class="sm-card"><div class="sm-title">Cookies</div>
    <div class="sm-value">{len(ck['cookies'])}</div></div>
    <div class="sm-card"><div class="sm-title">Trackers</div>
    <div class="sm-value" style="color:#ff9900">{len(ck['trackers'])}</div></div>
</div>
<div class="verdict-banner" style="margin-top:20px;background:rgba({('0,255,65' if tr['nota']>=80 else '0,229,255' if tr['nota']>=60 else '255,153,0' if tr['nota']>=40 else '255,51,51')},.08);color:{tr['verdictColor']};border:2px solid {tr['verdictColor']}">
{tr['verdict']}
</div>
</div></div>

<!-- RODAPE -->
<div style="text-align:center;color:#334433;padding:30px;border-top:2px solid #1a3a1a;margin-top:25px;font-size:11px">
    <p>◉ WEB SITE ANALYZER PRO</p>
    <p style="color:#00ff41;margin-top:5px">Relatorio gerado em {d['data_analise']}</p>
    <p style="margin-top:3px">Analise completa de <strong style="color:#00e5ff">{esc(d['dominio'])}</strong></p>
</div>

</div><!-- /main -->

<!-- BTN TOP -->
<button class="btn-top" id="btnTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>

<!-- ===== JAVASCRIPT ===== -->
<script>
// Toggle section
function toggleSection(header) {{
    var body = header.nextElementSibling;
    var icon = header.querySelector('.toggle-icon');
    if (body.classList.contains('collapsed')) {{
        body.classList.remove('collapsed');
        icon.classList.remove('collapsed');
    }} else {{
        body.classList.add('collapsed');
        icon.classList.add('collapsed');
    }}
}}

// Scroll to section
function scrollToSection(id) {{
    var el = document.getElementById(id);
    if (el) {{
        // Ensure section is expanded
        var body = el.querySelector('.section-body');
        var icon = el.querySelector('.toggle-icon');
        if (body && body.classList.contains('collapsed')) {{
            body.classList.remove('collapsed');
            if (icon) icon.classList.remove('collapsed');
        }}
        el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        // Highlight
        el.style.boxShadow = '0 0 20px rgba(0,255,65,.3)';
        setTimeout(function() {{ el.style.boxShadow = ''; }}, 2000);
    }}
}}

// Active nav on scroll
var sections = document.querySelectorAll('.section');
var navItems = document.querySelectorAll('.nav-item');
window.addEventListener('scroll', function() {{
    var scrollPos = window.scrollY + 100;
    sections.forEach(function(sec, i) {{
        if (sec.offsetTop <= scrollPos && sec.offsetTop + sec.offsetHeight > scrollPos) {{
            navItems.forEach(function(n) {{ n.classList.remove('active'); }});
            if (navItems[i]) navItems[i].classList.add('active');
        }}
    }});
    // Show/hide top button
    var btn = document.getElementById('btnTop');
    if (window.scrollY > 400) {{
        btn.classList.add('visible');
    }} else {{
        btn.classList.remove('visible');
    }}
}});

// Search
function doSearch() {{
    var query = document.getElementById('searchInput').value.toLowerCase().trim();
    var countEl = document.getElementById('searchCount');

    // Remove old highlights
    document.querySelectorAll('.highlight').forEach(function(el) {{
        var parent = el.parentNode;
        parent.replaceChild(document.createTextNode(el.textContent), el);
        parent.normalize();
    }});

    if (!query) {{
        // Show all
        document.querySelectorAll('.searchable').forEach(function(el) {{
            el.style.display = '';
        }});
        countEl.textContent = '';
        return;
    }}

    var found = 0;
    var items = document.querySelectorAll('.searchable');
    items.forEach(function(el) {{
        var text = el.textContent.toLowerCase();
        if (text.indexOf(query) !== -1) {{
            el.style.display = '';
            found++;
            // Highlight text
            highlightText(el, query);
        }} else {{
            el.style.display = 'none';
        }}
    }});

    countEl.textContent = found + ' resultado';

    // Expand sections with results
    document.querySelectorAll('.section').forEach(function(sec) {{
        var visibles = sec.querySelectorAll('.searchable:not([style*="display: none"])');
        if (visibles.length > 0) {{
            var body = sec.querySelector('.section-body');
            var icon = sec.querySelector('.toggle-icon');
            if (body) body.classList.remove('collapsed');
            if (icon) icon.classList.remove('collapsed');
        }}
    }});

    // Scroll to first result
    var first = document.querySelector('.searchable:not([style*="display: none"]) .highlight');
    if (first) {{
        first.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    }}
}}

function highlightText(element, query) {{
    var walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach(function(node) {{
        var text = node.textContent;
        var lower = text.toLowerCase();
        var idx = lower.indexOf(query);
        if (idx !== -1) {{
            var span = document.createElement('span');
            span.className = 'highlight';
            span.textContent = text.substring(idx, idx + query.length);

            var after = document.createTextNode(text.substring(idx + query.length));
            var before = document.createTextNode(text.substring(0, idx));

            var parent = node.parentNode;
            parent.insertBefore(before, node);
            parent.insertBefore(span, node);
            parent.insertBefore(after, node);
            parent.removeChild(node);
        }}
    }});
}}

function clearSearch() {{
    document.getElementById('searchInput').value = '';
    document.getElementById('searchCount').textContent = '';
    document.querySelectorAll('.highlight').forEach(function(el) {{
        var parent = el.parentNode;
        parent.replaceChild(document.createTextNode(el.textContent), el);
        parent.normalize();
    }});
    document.querySelectorAll('.searchable').forEach(function(el) {{
        el.style.display = '';
    }});
}}

// Keyboard shortcut: Ctrl+F focus search
document.addEventListener('keydown', function(e) {{
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {{
        e.preventDefault();
        document.getElementById('searchInput').focus();
    }}
}});
</script>

</body>
</html>"""

        return html_output


# ============================================================
# EXECUTAR
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = SiteAnalyzerPro(root)
    root.mainloop()
