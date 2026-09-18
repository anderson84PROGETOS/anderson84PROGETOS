import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import threading
import os
import re
import webbrowser
from datetime import datetime
import platform


class WebScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🕷️ Web Scraper Pro")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1a1a2e")
        self.root.minsize(1000, 650)

        try:
            if platform.system() == "Windows":
                self.root.after(100, lambda: self.root.state("zoomed"))
            else:
                self.root.after(200, lambda: self.root.attributes("-zoomed", True))
        except Exception:
            pass        

        self.resultados = {}
        self.scraping = False
        self.ultimo_arquivo = None

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configurar_estilos()
        self.criar_interface()

    # ─── ESTILOS ─────────────────────────────────────────────
    def configurar_estilos(self):
        self.style.configure("Main.TFrame", background="#1a1a2e")
        self.style.configure("Card.TFrame", background="#16213e")
        self.style.configure("Header.TLabel", background="#1a1a2e", foreground="#e94560",
                             font=("Segoe UI", 22, "bold"))
        self.style.configure("SubHeader.TLabel", background="#1a1a2e", foreground="#a8a8b3",
                             font=("Segoe UI", 10))
        self.style.configure("Green.Horizontal.TProgressbar", troughcolor="#16213e",
                             background="#53c28b")
        self.style.configure("TNotebook", background="#1a1a2e")
        self.style.configure("TNotebook.Tab", background="#16213e", foreground="#a8a8b3",
                             padding=[14, 6], font=("Segoe UI", 9, "bold"))
        self.style.map("TNotebook.Tab",
                       background=[("selected", "#0f3460")],
                       foreground=[("selected", "#e8e8e8")])

    # ─── INTERFACE ───────────────────────────────────────────
    def criar_interface(self):
        main = ttk.Frame(self.root, style="Main.TFrame")
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # ── header ──
        hdr = ttk.Frame(main, style="Main.TFrame")
        hdr.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(hdr, text="🕷️ Web Scraper Pro", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(hdr, text="Extraia dados de qualquer website • Preview em tempo real",
                  style="SubHeader.TLabel").pack(side=tk.LEFT, padx=(15, 0), pady=(8, 0))

        # ── url bar ──
        url_card = tk.Frame(main, bg="#16213e", highlightbackground="#0f3460", highlightthickness=1)
        url_card.pack(fill=tk.X, pady=(0, 8), ipady=6)
        url_in = tk.Frame(url_card, bg="#16213e")
        url_in.pack(fill=tk.X, padx=15, pady=8)

        tk.Label(url_in, text="🔗 URL:", bg="#16213e", fg="#e8e8e8",
                 font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self.url_entry = tk.Entry(url_in, font=("Segoe UI", 12), bg="#0a0a1a", fg="#e8e8e8",
                                  insertbackground="#e94560", relief="flat", highlightthickness=1,
                                  highlightcolor="#e94560", highlightbackground="#0f3460")
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10), ipady=5)
        self.url_entry.insert(0, "https://")
        self.url_entry.bind("<Return>", lambda e: self.iniciar_scraping())

        self.btn_scrape = tk.Button(url_in, text="🚀 SCRAPE", font=("Segoe UI", 11, "bold"),
                                    bg="#e94560", fg="white", activebackground="#c73652",
                                    relief="flat", cursor="hand2", padx=20, pady=5,
                                    command=self.iniciar_scraping)
        self.btn_scrape.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_parar = tk.Button(url_in, text="⏹ PARAR", font=("Segoe UI", 11, "bold"),
                                   bg="#ff6b35", fg="white", activebackground="#e55a2b",
                                   relief="flat", cursor="hand2", padx=15, pady=5,
                                   state=tk.DISABLED, command=self.parar_scraping)
        self.btn_parar.pack(side=tk.LEFT)

        # ── opções ──
        opt_card = tk.Frame(main, bg="#16213e", highlightbackground="#0f3460", highlightthickness=1)
        opt_card.pack(fill=tk.X, pady=(0, 8), ipady=4)
        opt_in = tk.Frame(opt_card, bg="#16213e")
        opt_in.pack(fill=tk.X, padx=15, pady=6)

        tk.Label(opt_in, text="⚙️ Extrair:", bg="#16213e", fg="#a8a8b3",
                 font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        self.var_titulos = tk.BooleanVar(value=True)
        self.var_paragrafos = tk.BooleanVar(value=True)
        self.var_links = tk.BooleanVar(value=True)
        self.var_imagens = tk.BooleanVar(value=True)
        self.var_tabelas = tk.BooleanVar(value=True)
        self.var_listas = tk.BooleanVar(value=True)
        self.var_meta = tk.BooleanVar(value=True)

        for txt, var in [("📑 Títulos", self.var_titulos),
                         ("📝 Parágrafos", self.var_paragrafos),
                         ("🔗 Links", self.var_links),
                         ("🖼️ Imagens", self.var_imagens),
                         ("📊 Tabelas", self.var_tabelas),
                         ("📋 Listas", self.var_listas),
                         ("🏷️ Meta Tags", self.var_meta)]:
            tk.Checkbutton(opt_in, text=txt, variable=var, bg="#16213e", fg="#e8e8e8",
                           selectcolor="#0a0a1a", activebackground="#16213e",
                           activeforeground="#e8e8e8", font=("Segoe UI", 9),
                           cursor="hand2").pack(side=tk.LEFT, padx=(0, 10))

        # user-agent
        ua_f = tk.Frame(opt_card, bg="#16213e")
        ua_f.pack(fill=tk.X, padx=15, pady=(0, 6))
        tk.Label(ua_f, text="🌐 User-Agent:", bg="#16213e", fg="#a8a8b3",
                 font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.ua_var = tk.StringVar(
            value="Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 "
                  "(KHTML, like Gecko) Version/7.0 Mobile/11D201 Safari/9537.53")
        tk.Entry(ua_f, textvariable=self.ua_var, font=("Segoe UI", 9), bg="#0a0a1a",
                 fg="#a8a8b3", insertbackground="#e94560", relief="flat", highlightthickness=1,
                 highlightcolor="#0f3460", highlightbackground="#0f3460").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0), ipady=3)

        # ── PAINEL PRINCIPAL ──
        paned = tk.PanedWindow(main, orient=tk.HORIZONTAL, bg="#1a1a2e", sashwidth=6,
                               sashrelief="flat", sashpad=2)
        paned.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # ── LADO ESQUERDO: Console + Dados + Código Fonte ──
        left_frame = tk.Frame(paned, bg="#1a1a2e")
        paned.add(left_frame, minsize=350, width=500)
        self.notebook_left = ttk.Notebook(left_frame)
        self.notebook_left.pack(fill=tk.BOTH, expand=True)

        # Aba Console
        tab_console = tk.Frame(self.notebook_left, bg="#0a0a1a")
        self.notebook_left.add(tab_console, text="  📋 Console  ")
        self.console = scrolledtext.ScrolledText(tab_console, font=("Consolas", 10),
                                                 bg="#0a0a1a", fg="#53c28b",
                                                 insertbackground="#53c28b", relief="flat",
                                                 wrap=tk.WORD, state=tk.DISABLED)
        self.console.pack(fill=tk.BOTH, expand=True)
        for tag, cor in [("info", "#53c28b"), ("warning", "#ffb347"), ("error", "#e94560"),
                         ("highlight", "#64b5f6"), ("header", "#e94560")]:
            self.console.tag_configure(tag, foreground=cor,
                                       font=("Consolas", 10, "bold") if tag == "header" else None)

        # Aba Dados
        tab_dados = tk.Frame(self.notebook_left, bg="#0a0a1a")
        self.notebook_left.add(tab_dados, text="  📊 Dados  ")
        self.dados_text = scrolledtext.ScrolledText(tab_dados, font=("Consolas", 10),
                                                    bg="#0a0a1a", fg="#e8e8e8",
                                                    insertbackground="#e8e8e8", relief="flat",
                                                    wrap=tk.WORD, state=tk.DISABLED)
        self.dados_text.pack(fill=tk.BOTH, expand=True)
        self.dados_text.tag_configure("title", foreground="#e94560",
                                      font=("Consolas", 11, "bold"))
        self.dados_text.tag_configure("data", foreground="#64b5f6")
        self.dados_text.tag_configure("onion", foreground="#a78bfa",
                                      font=("Consolas", 10, "bold"))
        self.dados_text.tag_configure("count", foreground="#53c28b")

        # Aba Código Fonte (index.html)
        tab_fonte = tk.Frame(self.notebook_left, bg="#0a0a1a")
        self.notebook_left.add(tab_fonte, text="  📄 Código Fonte  ")
        self.fonte_text = scrolledtext.ScrolledText(tab_fonte, font=("Consolas", 9),
                                                    bg="#0a0a1a", fg="#a8a8b3",
                                                    insertbackground="#a8a8b3", relief="flat",
                                                    wrap=tk.NONE, state=tk.DISABLED)
        x_scroll = tk.Scrollbar(tab_fonte, orient=tk.HORIZONTAL, command=self.fonte_text.xview)
        self.fonte_text.configure(xscrollcommand=x_scroll.set)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.fonte_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # ── LADO DIREITO: Preview HTML ──
        right_frame = tk.Frame(paned, bg="#1a1a2e")
        paned.add(right_frame, minsize=350, width=550)

        pv_header = tk.Frame(right_frame, bg="#0f3460")
        pv_header.pack(fill=tk.X)
        tk.Label(pv_header, text="  🌐 PREVIEW HTML — Tempo Real", bg="#0f3460", fg="#e8e8e8",
                 font=("Segoe UI", 10, "bold"), pady=8).pack(side=tk.LEFT, padx=8)
        self.preview_status = tk.Label(pv_header, text="⏳ Aguardando...", bg="#0f3460",
                                       fg="#ffb347", font=("Segoe UI", 9))
        self.preview_status.pack(side=tk.RIGHT, padx=12)

        self.counter_frame = tk.Frame(right_frame, bg="#16213e")
        self.counter_frame.pack(fill=tk.X)
        self.counters = {}
        for emoji, key, label in [("📑", "titulos", "Títulos"), ("📝", "paragrafos", "Parágr."),
                                  ("🔗", "links", "Links"), ("🖼️", "imagens", "Imgs"),
                                  ("📊", "tabelas", "Tabelas"), ("📋", "listas", "Listas"),
                                  ("🏷️", "meta", "Meta")]:
            f = tk.Frame(self.counter_frame, bg="#16213e", padx=6, pady=4)
            f.pack(side=tk.LEFT, expand=True)
            lbl = tk.Label(f, text=f"{emoji} 0", bg="#16213e", fg="#53c28b",
                           font=("Consolas", 11, "bold"))
            lbl.pack()
            tk.Label(f, text=label, bg="#16213e", fg="#888",
                     font=("Segoe UI", 7)).pack()
            self.counters[key] = lbl

        self.preview_text = scrolledtext.ScrolledText(right_frame, font=("Consolas", 9),
                                                      bg="#0a0a1a", fg="#e8e8e8",
                                                      insertbackground="#e8e8e8", relief="flat",
                                                      wrap=tk.WORD, state=tk.DISABLED)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        for tag_name, color in [("tag", "#e94560"), ("attr", "#ffd93d"), ("value", "#53c28b"),
                                ("comment", "#555577"), ("text_content", "#c8c8d8"),
                                ("onion_value", "#a78bfa")]:
            self.preview_text.tag_configure(tag_name, foreground=color)
        self.preview_text.tag_configure("section_marker", foreground="#64b5f6",
                                        font=("Consolas", 9, "bold"))

        # ── BARRA INFERIOR ──
        bottom = tk.Frame(main, bg="#1a1a2e")
        bottom.pack(fill=tk.X)

        self.progress = ttk.Progressbar(bottom, style="Green.Horizontal.TProgressbar",
                                        mode="determinate", length=300)
        self.progress.pack(side=tk.LEFT, padx=(0, 12))

        self.status_label = tk.Label(bottom, text="✅ Pronto", bg="#1a1a2e", fg="#53c28b",
                                     font=("Segoe UI", 9))
        self.status_label.pack(side=tk.LEFT)

        btn_f = tk.Frame(bottom, bg="#1a1a2e")
        btn_f.pack(side=tk.RIGHT)
        self.btn_abrir = tk.Button(btn_f, text="🌐 Abrir Browser", font=("Segoe UI", 9, "bold"),
                                   bg="#0f3460", fg="white", relief="flat", cursor="hand2",
                                   padx=12, pady=4, state=tk.DISABLED,
                                   command=self.abrir_browser)
        self.btn_abrir.pack(side=tk.LEFT, padx=(0, 5))
        self.btn_salvar = tk.Button(btn_f, text="💾 Salvar HTML", font=("Segoe UI", 9, "bold"),
                                    bg="#53c28b", fg="white", relief="flat", cursor="hand2",
                                    padx=12, pady=4, state=tk.DISABLED,
                                    command=self.salvar_html)
        self.btn_salvar.pack(side=tk.LEFT, padx=(0, 5))
        self.btn_limpar = tk.Button(btn_f, text="🗑️ Limpar", font=("Segoe UI", 9, "bold"),
                                    bg="#333355", fg="white", relief="flat", cursor="hand2",
                                    padx=12, pady=4, command=self.limpar_tudo)
        self.btn_limpar.pack(side=tk.LEFT)

        self.log("═" * 55, "header")
        self.log("  🕷️  Web Scraper Pro — Prontinho!", "header")
        self.log("═" * 55, "header")
        self.log("")

    # ─── HELPERS DE UI E PREVIEW ─────────────────────────────
    def log(self, msg, tag="info"):
        self.console.configure(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{ts}] {msg}\n" if msg.strip() else "\n", tag)
        self.console.see(tk.END)
        self.console.configure(state=tk.DISABLED)

    def status(self, txt, cor="#53c28b"):
        self.status_label.config(text=txt, fg=cor)

    def atualizar_progresso(self, valor):
        self.progress['value'] = valor

    def atualizar_counter(self, key, valor):
        emojis = {"titulos": "📑", "paragrafos": "📝", "links": "🔗", "imagens": "🖼️",
                  "tabelas": "📊", "listas": "📋", "meta": "🏷️"}
        if key in self.counters:
            self.counters[key].config(text=f"{emojis.get(key, '')} {valor}")

    def resetar_counters(self):
        for key in self.counters:
            self.atualizar_counter(key, 0)

    def preview_clear(self):
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.configure(state=tk.DISABLED)

    def preview_append(self, text, tag="text_content"):
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.insert(tk.END, text, tag)
        self.preview_text.see(tk.END)
        self.preview_text.configure(state=tk.DISABLED)

    def preview_section(self, titulo):
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.insert(tk.END, "\n" + "─" * 50 + "\n", "comment")
        self.preview_text.insert(tk.END, f"  ▶ {titulo}\n", "section_marker")
        self.preview_text.insert(tk.END, "─" * 50 + "\n\n", "comment")
        self.preview_text.see(tk.END)
        self.preview_text.configure(state=tk.DISABLED)

    def preview_tag_line(self, tag_name, content):
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.insert(tk.END, "<", "tag")
        self.preview_text.insert(tk.END, tag_name, "tag")
        self.preview_text.insert(tk.END, ">", "tag")
        self.preview_text.insert(tk.END, content[:120], "text_content")
        self.preview_text.insert(tk.END, "</", "tag")
        self.preview_text.insert(tk.END, tag_name, "tag")
        self.preview_text.insert(tk.END, ">\n", "tag")
        self.preview_text.see(tk.END)
        self.preview_text.configure(state=tk.DISABLED)

    def preview_link_line(self, text, url, is_onion=False):
        self.preview_text.configure(state=tk.NORMAL)
        icon = "  🧅 " if is_onion else "  🔗 "
        tag_color = "onion_value" if is_onion else "value"

        self.preview_text.insert(tk.END, icon, "comment")
        self.preview_text.insert(tk.END, text[:50], "text_content")
        self.preview_text.insert(tk.END, "  →  ", "comment")
        self.preview_text.insert(tk.END, url + "\n", tag_color)
        self.preview_text.see(tk.END)
        self.preview_text.configure(state=tk.DISABLED)

    def preview_image_line(self, alt, src):
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.insert(tk.END, "  🖼️ ", "comment")
        self.preview_text.insert(tk.END, f"[{alt[:40] or 'sem alt'}]", "attr")
        self.preview_text.insert(tk.END, "  ", "comment")
        self.preview_text.insert(tk.END, src + "\n", "value")
        self.preview_text.see(tk.END)
        self.preview_text.configure(state=tk.DISABLED)

    def preview_meta_line(self, name, content):
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.insert(tk.END, "  🏷️ ", "comment")
        self.preview_text.insert(tk.END, name[:30], "attr")
        self.preview_text.insert(tk.END, " = ", "comment")
        self.preview_text.insert(tk.END, content[:100] + "\n", "value")
        self.preview_text.see(tk.END)
        self.preview_text.configure(state=tk.DISABLED)

    # ─── SCRAPING (COM BARRA PROGRESSIVA) ────────────────────
    def iniciar_scraping(self):
        url = self.url_entry.get().strip()
        if not url or url == "https://":
            messagebox.showwarning("⚠️", "Insira uma URL válida!")
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)

        self.scraping = True
        self.btn_scrape.config(state=tk.DISABLED)
        self.btn_parar.config(state=tk.NORMAL)
        self.btn_salvar.config(state=tk.DISABLED)
        self.btn_abrir.config(state=tk.DISABLED)

        self.progress.config(mode="determinate")
        self.progress['value'] = 0

        self.status("🔄 Scraping em andamento...", "#ffb347")
        self.preview_status.config(text="🔴 LIVE — Recebendo dados...", fg="#e94560")
        self.resetar_counters()
        self.preview_clear()

        # Limpar abas
        self.fonte_text.configure(state=tk.NORMAL)
        self.fonte_text.delete(1.0, tk.END)
        self.fonte_text.configure(state=tk.DISABLED)
        self.dados_text.configure(state=tk.NORMAL)
        self.dados_text.delete(1.0, tk.END)
        self.dados_text.configure(state=tk.DISABLED)

        threading.Thread(target=self.executar_scraping, args=(url,), daemon=True).start()

    def parar_scraping(self):
        self.scraping = False
        self.log("⏹ Scraping interrompido!", "warning")

    def finalizar_ui(self, sucesso=False):
        self.btn_scrape.config(state=tk.NORMAL)
        self.btn_parar.config(state=tk.DISABLED)
        if sucesso:
            self.progress['value'] = 100
        else:
            self.progress['value'] = 0

    def executar_scraping(self, url):
        try:
            self.log(f"🌐 Conectando a: {url}", "highlight")

            opcoes_ativas = sum([self.var_meta.get(), self.var_titulos.get(),
                                 self.var_paragrafos.get(), self.var_links.get(),
                                 self.var_imagens.get(), self.var_tabelas.get(),
                                 self.var_listas.get()])
            incremento_etapa = 90 / (opcoes_ativas if opcoes_ativas > 0 else 1)
            progresso_atual = 0

            self.root.after(0, lambda: self.preview_append(
                "╔══════════════════════════════════════════════════╗\n"
                "║        🕷️  WEB SCRAPER PRO — LIVE PREVIEW      ║\n"
                "╚══════════════════════════════════════════════════╝\n\n",
                "section_marker"))

            headers = {
                "User-Agent": self.ua_var.get(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # ════════ CAPTURA DO CÓDIGO FONTE COMPLETO ════════
            # Força encoding correto para não corromper acentos
            if response.encoding is None or response.encoding.lower() == "iso-8859-1":
                response.encoding = response.apparent_encoding or "utf-8"

            html_bruto = response.text  # HTML completo e bruto, como o servidor entregou

            soup = BeautifulSoup(html_bruto, "lxml")

            self.resultados = {
                "url": url,
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "codigo_fonte": html_bruto,                 # bruto, completo (vai para o Save HTML)
                "codigo_fonte_formatado": soup.prettify(),  # versão indentada/bonita
                "tamanho_bytes": len(response.content),
            }

            progresso_atual = 10
            self.root.after(0, lambda: self.atualizar_progresso(progresso_atual))
            self.log(f"✅ Status {response.status_code} | {len(response.content):,} bytes", "info")

            if not self.scraping:
                return

            title_tag = soup.find("title")
            self.resultados["titulo_pagina"] = (title_tag.get_text(strip=True)
                                                if title_tag else "Sem título")
            self.log(f"📄 Página: {self.resultados['titulo_pagina']}", "highlight")

            # ════════ META TAGS ════════
            if self.var_meta.get():
                if not self.scraping:
                    return
                self.log("🏷️ Extraindo meta tags...", "info")
                self.root.after(0, lambda: self.preview_section("🏷️ META TAGS"))
                metas = []
                for meta in soup.find_all("meta"):
                    info = {}
                    if meta.get("name"):
                        info["name"] = meta["name"]
                        info["content"] = meta.get("content", "")
                    elif meta.get("property"):
                        info["property"] = meta["property"]
                        info["content"] = meta.get("content", "")
                    elif meta.get("charset"):
                        info["charset"] = meta["charset"]
                    if info:
                        metas.append(info)
                        self.root.after(0, lambda n=info.get("name") or info.get("property")
                                        or info.get("charset", ""),
                                        c=info.get("content", ""): self.preview_meta_line(n, c))
                self.resultados["meta_tags"] = metas
                self.root.after(0, lambda: self.atualizar_counter("meta", len(metas)))

                progresso_atual += incremento_etapa
                self.root.after(0, lambda: self.atualizar_progresso(progresso_atual))

            # ════════ TÍTULOS ════════
            if self.var_titulos.get():
                if not self.scraping:
                    return
                self.log("📑 Extraindo títulos...", "info")
                self.root.after(0, lambda: self.preview_section("📑 TÍTULOS (H1-H6)"))
                titulos = {}
                total_t = 0
                for i in range(1, 7):
                    tags = soup.find_all(f"h{i}")
                    if tags:
                        titulos[f"h{i}"] = []
                        for tag in tags:
                            txt = tag.get_text(strip=True)
                            if txt:
                                titulos[f"h{i}"].append(txt)
                                total_t += 1
                                self.root.after(0, lambda n=f"h{i}", t=txt:
                                                self.preview_tag_line(n, t))
                                self.root.after(0, lambda v=total_t:
                                                self.atualizar_counter("titulos", v))
                self.resultados["titulos"] = titulos

                progresso_atual += incremento_etapa
                self.root.after(0, lambda: self.atualizar_progresso(progresso_atual))

            # ════════ PARÁGRAFOS ════════
            if self.var_paragrafos.get():
                if not self.scraping:
                    return
                self.log("📝 Extraindo parágrafos...", "info")
                self.root.after(0, lambda: self.preview_section("📝 PARÁGRAFOS"))
                paragrafos = []
                for p in soup.find_all("p"):
                    txt = p.get_text(strip=True)
                    if txt and len(txt) > 10:
                        paragrafos.append(txt)
                        self.root.after(0, lambda t=txt: self.preview_tag_line("p", t))
                        self.root.after(0, lambda v=len(paragrafos):
                                        self.atualizar_counter("paragrafos", v))
                self.resultados["paragrafos"] = paragrafos

                progresso_atual += incremento_etapa
                self.root.after(0, lambda: self.atualizar_progresso(progresso_atual))

            # ════════ LINKS (MÉTODO DUPLO: TAGS <A> + REGEX UNIVERSAL) ════════
            if self.var_links.get():
                if not self.scraping:
                    return
                self.log("🔗 Extraindo todos os links (HTML, Meta, Scripts e .onion)...", "info")
                self.root.after(0, lambda: self.preview_section("🔗 LINKS (HTTP / HTTPS / .ONION)"))
                links = []
                seen = set()

                # 1. Extração via Tags <a href="...">
                for a in soup.find_all("a", href=True):
                    href_abs = urljoin(url, a["href"])
                    if href_abs.startswith(("http://", "https://")) and href_abs not in seen:
                        seen.add(href_abs)
                        texto = a.get_text(strip=True) or "(Link Âncora)"
                        is_onion = ".onion" in href_abs
                        links.append({"texto": texto, "url": href_abs, "is_onion": is_onion})
                        self.root.after(0, lambda t=texto, u=href_abs, o=is_onion:
                                        self.preview_link_line(t, u, o))
                        self.root.after(0, lambda v=len(links):
                                        self.atualizar_counter("links", v))

                # 2. Extração via REGEX por qualquer URL no Código Fonte
                url_regex = re.compile(r'https?://[a-zA-Z0-9.\-_~:/?#\[\]@!$&\'()*+,;=%]+')
                for match in url_regex.findall(html_bruto):
                    clean_url = match.rstrip(".,;:\"'>)]}")
                    if clean_url.startswith(("http://", "https://")) and clean_url not in seen:
                        seen.add(clean_url)
                        is_onion = ".onion" in clean_url
                        texto = "(Atributo / Meta Tag / Código Fonte)"
                        links.append({"texto": texto, "url": clean_url, "is_onion": is_onion})
                        self.root.after(0, lambda t=texto, u=clean_url, o=is_onion:
                                        self.preview_link_line(t, u, o))
                        self.root.after(0, lambda v=len(links):
                                        self.atualizar_counter("links", v))

                self.resultados["links"] = links
                progresso_atual += incremento_etapa
                self.root.after(0, lambda: self.atualizar_progresso(progresso_atual))

            # ════════ IMAGENS ════════
            if self.var_imagens.get():
                if not self.scraping:
                    return
                self.log("🖼️ Extraindo imagens...", "info")
                self.root.after(0, lambda: self.preview_section("🖼️ IMAGENS"))
                imagens = []
                for img in soup.find_all("img"):
                    src = img.get("src", "")
                    if src:
                        src_abs = urljoin(url, src)
                        alt = img.get("alt", "")
                        imagens.append({"src": src_abs, "alt": alt})
                        self.root.after(0, lambda a=alt, s=src_abs:
                                        self.preview_image_line(a, s))
                        self.root.after(0, lambda v=len(imagens):
                                        self.atualizar_counter("imagens", v))
                self.resultados["imagens"] = imagens

                progresso_atual += incremento_etapa
                self.root.after(0, lambda: self.atualizar_progresso(progresso_atual))

            # ════════ TABELAS ════════
            if self.var_tabelas.get():
                if not self.scraping:
                    return
                self.log("📊 Extraindo tabelas...", "info")
                self.root.after(0, lambda: self.preview_section("📊 TABELAS"))
                tabelas = []
                for table in soup.find_all("table"):
                    dados = []
                    for row in table.find_all("tr"):
                        row_data = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                        if any(row_data):
                            dados.append(row_data)
                    if dados:
                        tabelas.append(dados)
                        self.root.after(0, lambda v=len(tabelas):
                                        self.atualizar_counter("tabelas", v))
                self.resultados["tabelas"] = tabelas

                progresso_atual += incremento_etapa
                self.root.after(0, lambda: self.atualizar_progresso(progresso_atual))

            # ════════ LISTAS ════════
            if self.var_listas.get():
                if not self.scraping:
                    return
                self.log("📋 Extraindo listas...", "info")
                self.root.after(0, lambda: self.preview_section("📋 LISTAS"))
                listas = []
                for lista in soup.find_all(["ul", "ol"]):
                    items = [li.get_text(strip=True)
                             for li in lista.find_all("li", recursive=False)
                             if li.get_text(strip=True)]
                    if items:
                        listas.append({"tipo": "ordenada" if lista.name == "ol"
                                       else "não-ordenada", "items": items})
                        self.root.after(0, lambda v=len(listas):
                                        self.atualizar_counter("listas", v))
                self.resultados["listas"] = listas

                progresso_atual += incremento_etapa
                self.root.after(0, lambda: self.atualizar_progresso(progresso_atual))

            # ── concluído com SUCESSO ──
            self.root.after(0, lambda: self.preview_append(
                "\n\n╔══════════════════════════════════════════════════╗\n"
                "║           ✅  SCRAPING CONCLUÍDO!                ║\n"
                "╚══════════════════════════════════════════════════╝\n",
                "section_marker"))
            self.log("\n" + "═" * 55, "header")
            self.log("  ✅  SCRAPING CONCLUÍDO COM SUCESSO!", "header")
            self.log("═" * 55 + "\n", "header")

            self.root.after(0, self.mostrar_dados_tabs)
            self.root.after(0, lambda: self.btn_salvar.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_abrir.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status("✅ Scraping concluído!", "#53c28b"))
            self.root.after(0, lambda: self.preview_status.config(text="✅ Concluído!",
                                                                  fg="#53c28b"))
            self.root.after(0, lambda: self.finalizar_ui(sucesso=True))

        except Exception as e:
            self.log(f"❌ Erro: {e}", "error")
            self.root.after(0, lambda: self.status("❌ Erro no Scraping", "#e94560"))
            self.root.after(0, lambda: self.finalizar_ui(sucesso=False))
        finally:
            self.scraping = False

    def mostrar_dados_tabs(self):
        r = self.resultados

        # Preencher Aba de Dados
        self.dados_text.configure(state=tk.NORMAL)
        self.dados_text.delete(1.0, tk.END)
        self.dados_text.insert(tk.END,
                               f"\n  📄 {r.get('titulo_pagina', 'N/A')}\n"
                               f"  🔗 {r.get('url', 'N/A')}\n"
                               f"  🕐 {r.get('timestamp', 'N/A')}\n\n", "data")

        if "links" in r:
            self.dados_text.insert(tk.END, f"  🔗 LINKS EXTRAÍDOS ({len(r['links'])})\n", "title")
            self.dados_text.insert(tk.END, "  " + "─" * 50 + "\n")
            for l in r["links"]:
                icone = "🧅" if l.get("is_onion") else "•"
                tag_cor = "onion" if l.get("is_onion") else "data"
                self.dados_text.insert(tk.END, f"    {icone} {l['texto']} → {l['url']}\n", tag_cor)
            self.dados_text.insert(tk.END, "\n")

        self.dados_text.configure(state=tk.DISABLED)

        # ════════ Preencher Aba de Código Fonte (COMPLETO) ════════
        self.fonte_text.configure(state=tk.NORMAL)
        self.fonte_text.delete(1.0, tk.END)

        tamanho = r.get("tamanho_bytes", 0)
        self.fonte_text.insert(tk.END,
                               f"<!-- Código Fonte completo: {r.get('url', 'N/A')} | "
                               f"{tamanho:,} bytes | capturado em {r.get('timestamp', 'N/A')} -->"
                               f"\n\n")
        self.fonte_text.insert(tk.END, r.get("codigo_fonte_formatado")
                               or r.get("codigo_fonte", "Sem código fonte disponível."))
        self.fonte_text.configure(state=tk.DISABLED)
        self.log(f"📄 Código fonte carregado na aba ({tamanho:,} bytes)", "info")

    # ─── GERAR HTML (CARDS CLICÁVEIS + SCROLL SUAVE) ─────────
    def _esc(self, text):
        if not isinstance(text, str):
            text = str(text)
        return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))

    def gerar_html(self):
        r = self.resultados
        domain = urlparse(r.get("url", "")).netloc

        stats_html = ""
        mapeamento_cards = [
            ("📑", "titulos", "Títulos", "sec-titulos"),
            ("📝", "paragrafos", "Parágrafos", "sec-paragrafos"),
            ("🔗", "links", "Links", "sec-links"),
            ("🖼️", "imagens", "Imagens", "sec-imagens"),
            ("📊", "tabelas", "Tabelas", "sec-tabelas"),
            ("📋", "listas", "Listas", "sec-listas"),
            ("🏷️", "meta_tags", "Meta Tags", "sec-meta"),
            ("📄", "codigo_fonte", "Código", "sec-fonte")
        ]

        for icon, key, label, anchor in mapeamento_cards:
            if key in r:
                if key == "titulos":
                    num = sum(len(v) for v in r[key].values())
                elif key == "codigo_fonte":
                    num = f"{r.get('tamanho_bytes', 0) // 1024} KB"
                else:
                    num = len(r[key])
                stats_html += (f'<a href="#{anchor}" class="stat-card">'
                               f'<div style="font-size:1.5em;margin-bottom:8px">{icon}</div>'
                               f'<div class="number">{num}</div>'
                               f'<div class="label">{label}</div></a>')

        sections_html = ""

        if "titulos" in r and r["titulos"]:
            items_list = []
            for nv, lst in r["titulos"].items():
                for t in lst:
                    items_list.append(f'<div class="hi {nv}"><span class="ht">{nv}</span>'
                                      f'{self._esc(t)}</div>')
            items = "".join(items_list)
            sections_html += (f'<div id="sec-titulos" class="section"><div class="sh">'
                              f'<span class="icon">📑</span><h2>Títulos</h2></div>'
                              f'<div class="sc">{items}</div></div>')

        if "paragrafos" in r and r["paragrafos"]:
            items = "".join(f'<div class="para">{self._esc(p)}</div>' for p in r["paragrafos"])
            sections_html += (f'<div id="sec-paragrafos" class="section"><div class="sh">'
                              f'<span class="icon">📝</span><h2>Parágrafos</h2></div>'
                              f'<div class="sc">{items}</div></div>')

        if "links" in r and r["links"]:
            items_list = []
            for l in r["links"]:
                txt = self._esc(l["texto"])
                url_esc = self._esc(l["url"])

                if l.get("is_onion"):
                    cls = "li onion-link"
                    icon = "🧅"
                else:
                    cls = "li"
                    icon = "🔗"

                items_list.append(f'<a href="{url_esc}" target="_blank" class="{cls}">'
                                  f'<span class="lt">{icon} {txt}</span>'
                                  f'<span class="lu">{url_esc}</span></a>')
            items = "".join(items_list)
            sections_html += (f'<div id="sec-links" class="section"><div class="sh">'
                              f'<span class="icon">🔗</span>'
                              f'<h2>Links Extraídos ({len(r["links"])})</h2></div>'
                              f'<div class="sc">{items}</div></div>')

        if "imagens" in r and r["imagens"]:
            items_list = []
            for img in r["imagens"]:
                src_esc = self._esc(img["src"])
                alt_esc = self._esc(img["alt"])
                alt_disp = self._esc(img["alt"] or "Sem descrição")
                src_disp = self._esc(img["src"])
                items_list.append(
                    f'<div class="ic">'
                    f'<img src="{src_esc}" alt="{alt_esc}" loading="lazy" '
                    f'onerror="this.style.display=\'none\'" onclick="openLightbox(this.src)">'
                    f'<div class="ii"><div class="ia">{alt_disp}</div>'
                    f'<div class="is">{src_disp}</div></div>'
                    f'</div>')
            items = "".join(items_list)
            sections_html += (f'<div id="sec-imagens" class="section"><div class="sh">'
                              f'<span class="icon">🖼️</span><h2>Imagens</h2>'
                              f'<span class="badge">{len(r["imagens"])}</span></div>'
                              f'<div class="sc"><div class="ig">{items}</div></div></div>')

        if "tabelas" in r and r["tabelas"]:
            items = ""
            for i, tab in enumerate(r["tabelas"]):
                rows_list = []
                for j, row in enumerate(tab):
                    tag_name = "th" if j == 0 else "td"
                    cells_html = "".join(["<" + tag_name + ">" + self._esc(c) +
                                          "</" + tag_name + ">" for c in row])
                    rows_list.append("<tr>" + cells_html + "</tr>")
                rows = "".join(rows_list)
                items += (f'<h3 style="color:#64b5f6;margin:20px 0 10px">Tabela {i + 1} '
                          f'({len(tab)} linhas)</h3>'
                          f'<div style="overflow-x:auto"><table class="dt">{rows}</table></div>')
            sections_html += (f'<div id="sec-tabelas" class="section"><div class="sh">'
                              f'<span class="icon">📊</span><h2>Tabelas</h2>'
                              f'<span class="badge">{len(r["tabelas"])}</span></div>'
                              f'<div class="sc">{items}</div></div>')

        if "listas" in r and r["listas"]:
            items_list = []
            for i, lst in enumerate(r["listas"]):
                tag_name = "ol" if lst["tipo"] == "ordenada" else "ul"
                lis = "".join(["<li>" + self._esc(it) + "</li>" for it in lst["items"]])
                items_list.append('<div class="ls"><div class="lstt">Lista ' + str(i + 1) +
                                  ' (' + lst["tipo"] + ')</div><' + tag_name + '>' + lis +
                                  '</' + tag_name + '></div>')
            items = "".join(items_list)
            sections_html += (f'<div id="sec-listas" class="section"><div class="sh">'
                              f'<span class="icon">📋</span><h2>Listas</h2>'
                              f'<span class="badge">{len(r["listas"])}</span></div>'
                              f'<div class="sc">{items}</div></div>')

        if "meta_tags" in r and r["meta_tags"]:
            items_list = []
            for m in r["meta_tags"]:
                name = self._esc(m.get("name") or m.get("property") or m.get("charset", ""))
                content = self._esc(m.get("content", m.get("name", "")))
                items_list.append(f'<div class="meta-tag-item"><span class="mn">{name}</span>'
                                  f'<span class="mc">{content}</span></div>')
            items = "".join(items_list)
            sections_html += (f'<div id="sec-meta" class="section"><div class="sh">'
                              f'<span class="icon">🏷️</span><h2>Meta Tags</h2>'
                              f'<span class="badge">{len(r["meta_tags"])}</span></div>'
                              f'<div class="sc"><div style="display:flex;flex-wrap:wrap;gap:6px">'
                              f'{items}</div></div></div>')

        # ════════ CÓDIGO FONTE COMPLETO NO RELATÓRIO SALVO ════════
        # Usa o HTML BRUTO completo (codigo_fonte), sem cortes, escapado para exibição
        if "codigo_fonte" in r and r["codigo_fonte"]:
            fonte_esc = self._esc(r["codigo_fonte"])
            tamanho = r.get("tamanho_bytes", len(r["codigo_fonte"]))
            sections_html += (f'<div id="sec-fonte" class="section"><div class="sh">'
                              f'<span class="icon">📄</span>'
                              f'<h2>Código Fonte HTML COMPLETO (index.html)</h2>'
                              f'<span class="badge">{tamanho:,} bytes</span>'
                              f'</div><div class="sc"><details open>'
                              f'<summary style="cursor:pointer; color:#64b5f6; font-weight:bold;">'
                              f'👉 Código Fonte inteiro da página ({tamanho:,} bytes) — '
                              f'clique para recolher/expandir</summary>'
                              f'<pre style="background:#0a0a1a; padding:15px; border-radius:8px; '
                              f'overflow-x:auto; white-space:pre-wrap; word-break:break-all; '
                              f'margin-top:15px; font-size:0.85em; color:#a8a8b3; '
                              f'border: 1px solid #16213e;">'
                              f'<code>{fonte_esc}</code></pre>'
                              f'</details></div></div>')

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Scraping: {self._esc(r.get('titulo_pagina','Resultado'))}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}

html {{ scroll-behavior: smooth; }}

body{{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);min-height:100vh;color:#e8e8e8;line-height:1.6}}
.container{{max-width:1200px;margin:0 auto;padding:40px 20px}}
.hero{{text-align:center;padding:60px 40px;background:linear-gradient(135deg,rgba(233,69,96,.1),rgba(15,52,96,.2));border-radius:24px;border:1px solid rgba(233,69,96,.2);margin-bottom:40px;backdrop-filter:blur(10px)}}
.hero h1{{font-size:2.5em;font-weight:800;background:linear-gradient(135deg,#e94560,#ff6b6b,#ffd93d);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:15px}}
.hero .mi{{display:flex;justify-content:center;gap:30px;margin-top:25px;flex-wrap:wrap}}
.hero .mit{{display:flex;align-items:center;gap:8px;color:#8888a8;font-size:.9em}}
.sg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:16px;margin-bottom:40px}}

.stat-card{{background:rgba(22,33,62,.6);border:1px solid rgba(15,52,96,.4);border-radius:16px;padding:24px;text-align:center;backdrop-filter:blur(10px);transition:transform .3s,box-shadow .3s; text-decoration:none; color:inherit; display:block; cursor:pointer; outline:none;}}
.stat-card:hover{{transform:translateY(-4px);box-shadow:0 8px 32px rgba(233,69,96,.2); background:rgba(30,45,80,.8);}}

.number{{font-size:2.2em;font-weight:800;background:linear-gradient(135deg,#53c28b,#45d9a5);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.label{{color:#a8a8b3;font-size:.85em;margin-top:5px;text-transform:uppercase;letter-spacing:1px}}
.section{{background:rgba(22,33,62,.4);border:1px solid rgba(15,52,96,.3);border-radius:20px;margin-bottom:30px;overflow:hidden;backdrop-filter:blur(10px); scroll-margin-top: 20px;}}
.sh{{display:flex;align-items:center;gap:12px;padding:24px 30px;background:linear-gradient(135deg,rgba(15,52,96,.4),rgba(22,33,62,.6));border-bottom:1px solid rgba(15,52,96,.3)}}
.sh .icon{{font-size:1.5em}}
.sh h2{{font-size:1.3em;font-weight:700}}
.badge{{background:linear-gradient(135deg,#e94560,#ff6b6b);color:#fff;padding:4px 14px;border-radius:20px;font-size:.8em;font-weight:600;margin-left:auto}}
.sc{{padding:24px 30px}}
.hi{{padding:12px 20px;margin:8px 0;border-radius:10px;background:rgba(10,10,26,.4);border-left:4px solid;transition:transform .2s}}
.hi.h1{{border-color:#e94560;font-size:1.3em;font-weight:700}}.hi.h2{{border-color:#ff6b35;font-size:1.15em;font-weight:600}}
.hi.h3{{border-color:#ffd93d;font-size:1.05em}}.hi.h4{{border-color:#53c28b}}.hi.h5{{border-color:#64b5f6;font-size:.95em}}.hi.h6{{border-color:#a78bfa;font-size:.9em}}
.ht{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.7em;font-weight:600;margin-right:10px;text-transform:uppercase;background:rgba(233,69,96,.2);color:#e94560}}
.para{{padding:16px 20px;margin:10px 0;background:rgba(10,10,26,.3);border-radius:10px;color:#c8c8d8;line-height:1.8;border-left:3px solid rgba(83,194,139,.3)}}

.li{{display:flex;flex-direction:column;align-items:flex-start;padding:12px 20px;margin:8px 0;background:rgba(10,10,26,.3);border-radius:10px;transition:all .3s;text-decoration:none;gap:6px;word-break:break-all;}}
.li:hover{{background:rgba(15,52,96,.4);transform:translateX(5px)}}

.li.onion-link {{ background:rgba(138,43,226,.2); border-left: 4px solid #a78bfa; }}
.li.onion-link:hover {{ background:rgba(138,43,226,.35); transform:translateX(5px); }}

.lt{{color:#e8e8e8;font-weight:600;font-size:0.95em;word-break:break-all;}}
.lu{{color:#64b5f6;font-size:.85em;word-break:break-all;line-height:1.4;}}

.ig{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px}}
.ic{{background:rgba(10,10,26,.4);border-radius:14px;overflow:hidden;border:1px solid rgba(15,52,96,.3);transition:transform .3s}}
.ic img{{width:100%;height:200px;object-fit:cover;display:block;background:rgba(15,52,96,.3);cursor:zoom-in;}}
.ii{{padding:14px 16px}}.ia{{color:#e8e8e8;font-weight:500;font-size:.9em;margin-bottom:5px}}.is{{color:#8888a8;font-size:.75em;word-break:break-all}}
.dt{{width:100%;border-collapse:collapse;margin:10px 0}}
.dt th{{background:rgba(233,69,96,.15);color:#e94560;padding:14px 16px;text-align:left;font-weight:600;font-size:.9em;text-transform:uppercase;letter-spacing:.5px}}
.dt td{{padding:12px 16px;border-bottom:1px solid rgba(15,52,96,.2);color:#c8c8d8;font-size:.9em}}
.meta-tag-item{{display:inline-flex;align-items:center;gap:8px;padding:8px 16px;background:rgba(10,10,26,.4);border-radius:8px;border:1px solid rgba(15,52,96,.3);font-size:.85em;word-break:break-all;}}
.mn{{color:#e94560;font-weight:600}}.mc{{color:#a8a8b3}}
.ls{{margin:15px 0}}.lstt{{color:#64b5f6;font-weight:600;margin-bottom:10px;font-size:.9em}}
.ls ul,.ls ol{{padding-left:25px}}.ls li{{padding:6px 0;color:#c8c8d8}}
.footer{{text-align:center;padding:40px;color:#555577;font-size:.85em}}.footer a{{color:#e94560;text-decoration:none}}
.lightbox{{display:none;position:fixed;z-index:9999;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);align-items:center;justify-content:center;cursor:zoom-out;backdrop-filter:blur(5px)}}
.lightbox img{{max-width:90%;max-height:90vh;object-fit:contain;border-radius:8px;box-shadow:0 10px 40px rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.1)}}
@media(max-width:768px){{.hero h1{{font-size:1.8em}}.sg{{grid-template-columns:repeat(2,1fr)}}.ig{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="container">
    <div class="hero">
        <h1>🕷️ {self._esc(r.get('titulo_pagina','Resultado'))}</h1>
        <div class="mi">
            <div class="mit"><span>🔗</span><a href="{self._esc(r.get('url','#'))}" target="_blank" style="color:#64b5f6;text-decoration:none">{self._esc(domain)}</a></div>
        </div>
    </div>
    <div class="sg">{stats_html}</div>
    {sections_html}
    <div class="footer">
        <p>Gerado por <strong>🕷️ Web Scraper Pro</strong> em {r.get('timestamp','N/A')}</p>
    </div>
</div>

<div id="lightbox" class="lightbox" onclick="this.style.display='none'">
    <img id="lb-img" src="">
</div>
<script>
    function openLightbox(src) {{
        document.getElementById('lb-img').src = src;
        document.getElementById('lightbox').style.display = 'flex';
    }}
    document.addEventListener('keydown', function(e){{
        if(e.key === "Escape") document.getElementById('lightbox').style.display = 'none';
    }});
</script>
</body>
</html>"""

    # ─── SALVAR / ABRIR E LIMPAR ─────────────────────────────
    def salvar_html(self):
        if not self.resultados:
            return
        domain = urlparse(self.resultados.get("url", "")).netloc.replace(".", "_")
        nome = f"scrape_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fp = filedialog.asksaveasfilename(defaultextension=".html",
                                          filetypes=[("HTML", "*.html")],
                                          initialfile=nome, title="💾 Salvar HTML")

        if fp:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self.gerar_html())
            self.status(f"💾 {os.path.basename(fp)}", "#53c28b")
            if messagebox.askyesno("✅ Sucesso!", "Salvo com sucesso!\n\nAbrir no browser?"):
                webbrowser.open(f"file://{os.path.abspath(fp)}")

    def abrir_browser(self):
        tmp = os.path.join(os.path.expanduser("~"), ".scraper_preview.html")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(self.gerar_html())
        webbrowser.open(f"file://{os.path.abspath(tmp)}")

    def limpar_tudo(self):
        for widget in [self.console, self.dados_text, self.preview_text, self.fonte_text]:
            widget.configure(state=tk.NORMAL)
            widget.delete(1.0, tk.END)
            widget.configure(state=tk.DISABLED)
        self.resultados = {}
        self.btn_salvar.config(state=tk.DISABLED)
        self.btn_abrir.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.status("✅ Pronto", "#53c28b")
        self.preview_status.config(text="⏳ Aguardando...", fg="#ffb347")
        self.resetar_counters()


def main():
    root = tk.Tk()
    WebScraperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
