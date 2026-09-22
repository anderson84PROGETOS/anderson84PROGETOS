import os
import sqlite3
import shutil
import tempfile
import html
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta


class UniversalBrowserInspector:
    def __init__(self, root):
        self.root = root
        self.root.title("Browser Scope")
        self.root.geometry("1250x750")
        self.root.configure(bg="#181825")

        self.db_conn = None
        self.temp_dir = None
        self.temp_db_path = None
        self.current_table = None
        self.current_columns = []
        self.current_rows = []
        self.all_tables_data = {}  # Guarda TODAS as tabelas para exportação completa
        self.source_file_name = ""

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        bg_dark = "#181825"
        bg_panel = "#313244"
        fg_text = "#cdd6f4"
        accent = "#ff7518"

        style.configure("TFrame", background=bg_dark)
        style.configure("TLabel", background=bg_dark, foreground=fg_text, font=("Segoe UI", 10))
        style.configure("TButton", background=bg_panel, foreground=fg_text,
                         borderwidth=0, font=("Segoe UI", 10, "bold"))
        style.map("TButton", background=[("active", "#45475a")])
        style.configure("TCombobox", fieldbackground=bg_panel, background=bg_panel, foreground="#ffffff")

        style.configure("Treeview",
                         background="#11111b",
                         foreground=fg_text,
                         fieldbackground="#11111b",
                         rowheight=28,
                         font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                         background=bg_panel,
                         foreground=accent,
                         font=("Segoe UI", 10, "bold"))
        style.map("Treeview",
                   background=[("selected", accent)],
                   foreground=[("selected", "#ffffff")])

        # Botão de destaque laranja
        style.configure("Accent.TButton", background="#ff7518", foreground="#ffffff",
                         borderwidth=0, font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#e0660f")])

    def create_widgets(self):
        # ── BARRA SUPERIOR ──
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        btn_open = ttk.Button(top_frame, text="📁 Abrir Arquivo",
                               command=self.open_file)
        btn_open.pack(side=tk.LEFT, padx=(0, 10))

        lbl_table = ttk.Label(top_frame, text="Tabela:")
        lbl_table.pack(side=tk.LEFT, padx=(5, 5))

        self.combo_tables = ttk.Combobox(top_frame, state="readonly", width=22)
        self.combo_tables.pack(side=tk.LEFT, padx=(0, 10))
        self.combo_tables.bind("<<ComboboxSelected>>", self.on_table_changed)

        # Botão exportar tabela atual
        btn_export_table = ttk.Button(top_frame, text="💾 Exportar Tabela → HTML",
                                       command=self.export_current_table_html)
        btn_export_table.pack(side=tk.LEFT, padx=(0, 5))

        # Botão exportar TUDO
        btn_export_all = ttk.Button(top_frame, text="📦 Exportar TUDO → HTML",
                                     command=self.export_all_tables_html,
                                     style="Accent.TButton")
        btn_export_all.pack(side=tk.LEFT, padx=(0, 15))

        lbl_search = ttk.Label(top_frame, text="🔎 Pesquisar:")
        lbl_search.pack(side=tk.LEFT, padx=(5, 5))

        self.entry_search = tk.Entry(top_frame, bg="#313244", fg="#ffffff",
                                      insertbackground="white", relief="flat",
                                      font=("Segoe UI", 10))
        self.entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_search.bind("<KeyRelease>", self.filter_data)

        self.lbl_count = ttk.Label(top_frame, text="Registros: 0")
        self.lbl_count.pack(side=tk.RIGHT, padx=10)

        # ── TABELA ──
        table_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        table_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(table_frame, show="headings")
        self.tree.bind("<Double-1>", self.copy_selected_row)

        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # ── BARRA DE STATUS ──
        self.lbl_status = ttk.Label(
            self.root,
            text="Selecione um arquivo de banco de dados do navegador. "
                 "(Dica: Clique duplo copia a linha)",
            font=("Segoe UI", 9)
        )
        self.lbl_status.pack(fill=tk.X, padx=10, pady=5)

    # ──────────────────────────────────────────────
    #   ABRIR / FECHAR BANCO
    # ──────────────────────────────────────────────
    def close_current_db(self):
        if self.db_conn:
            try:
                self.db_conn.close()
            except Exception:
                pass
            self.db_conn = None

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo de Banco de Dados",
            filetypes=[
                ("Arquivos do Navegador", "*History* *Cookies* *Web Data* *Login Data* *"),
                ("Todos os Arquivos", "*.*")
            ]
        )
        if not file_path:
            return

        self.close_current_db()
        self.all_tables_data.clear()

        try:
            self.temp_dir = tempfile.mkdtemp()
            base_name = os.path.basename(file_path)
            self.source_file_name = base_name
            self.temp_db_path = os.path.join(self.temp_dir, base_name)

            shutil.copy2(file_path, self.temp_db_path)

            # Copia WAL/SHM se existirem
            src_dir = os.path.dirname(file_path)
            for ext in ["-wal", "-shm", ".wal", ".shm"]:
                wal_src = os.path.join(src_dir, base_name + ext)
                if os.path.exists(wal_src):
                    shutil.copy2(wal_src, self.temp_db_path + ext)

            self.db_conn = sqlite3.connect(self.temp_db_path)
            self.db_conn.text_factory = bytes

            cursor = self.db_conn.cursor()

            try:
                cursor.execute("PRAGMA wal_checkpoint(FULL);")
            except Exception:
                pass

            cursor.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            )
            raw_tables = cursor.fetchall()
            tables = [t[0].decode('utf-8', errors='ignore') for t in raw_tables]

            if not tables:
                messagebox.showwarning("Aviso", "Arquivo aberto, mas sem tabelas legíveis.")
                return

            # Pré-carrega TODAS as tabelas para exportação
            self.preload_all_tables(tables)

            self.combo_tables['values'] = tables
            self.combo_tables.current(0)

            self.lbl_status.config(
                text=f"✅ Aberto: {base_name} | "
                     f"{len(tables)} tabelas encontradas | "
                     f"Duplo clique = copiar linha"
            )
            self.load_table_data(tables[0])

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir:\n\n{str(e)}")
            self.close_current_db()

    def preload_all_tables(self, tables):
        """Carrega dados de TODAS as tabelas para exportação completa."""
        cursor = self.db_conn.cursor()
        for table_name in tables:
            try:
                cursor.execute(f"PRAGMA table_info('{table_name}');")
                cols_info = cursor.fetchall()
                columns = [self.safe_format_cell(c[1]) for c in cols_info]

                cursor.execute(f"SELECT * FROM '{table_name}';")
                raw_rows = cursor.fetchall()

                rows = []
                for row in raw_rows:
                    processed = [
                        self.safe_format_cell(item, columns[idx] if idx < len(columns) else "")
                        for idx, item in enumerate(row)
                    ]
                    rows.append(processed)

                self.all_tables_data[table_name] = {
                    "columns": columns,
                    "rows": rows
                }
            except Exception:
                self.all_tables_data[table_name] = {
                    "columns": ["Erro"],
                    "rows": [["Não foi possível ler esta tabela"]]
                }

    # ──────────────────────────────────────────────
    #   FORMATAÇÃO DE DADOS
    # ──────────────────────────────────────────────
    def format_chrome_timestamp(self, microseconds_str):
        try:
            val = int(microseconds_str)
            if val > 11644473600000000:
                epoch = datetime(1601, 1, 1)
                dt = epoch + timedelta(microseconds=val)
                return dt.strftime("%d/%m/%Y %H:%M:%S")
            elif val > 1000000000 and val < 2000000000:
                # Unix timestamp em segundos
                dt = datetime.fromtimestamp(val)
                return dt.strftime("%d/%m/%Y %H:%M:%S")
            elif val > 1000000000000 and val < 2000000000000:
                # Unix timestamp em milissegundos
                dt = datetime.fromtimestamp(val / 1000)
                return dt.strftime("%d/%m/%Y %H:%M:%S")
        except (ValueError, TypeError, OverflowError, OSError):
            pass
        return microseconds_str

    def safe_format_cell(self, val, col_name=""):
        if val is None:
            return "NULL"

        text = ""
        if isinstance(val, bytes):
            try:
                decoded = val.decode('utf-8')
                if all(c.isprintable() or c in '\n\r\t' for c in decoded):
                    text = decoded
                else:
                    return f"[Binário - {len(val)} bytes]"
            except UnicodeDecodeError:
                decoded_raw = val.decode('utf-8', errors='replace')
                if decoded_raw.count('\ufffd') > len(decoded_raw) * 0.2:
                    return f"[Binário - {len(val)} bytes]"
                text = decoded_raw
        else:
            text = str(val)

        time_keywords = ["time", "date", "expires", "created", "last_visit", "accessed"]
        if any(t in col_name.lower() for t in time_keywords):
            text = self.format_chrome_timestamp(text)

        return text

    # ──────────────────────────────────────────────
    #   NAVEGAÇÃO / EXIBIÇÃO
    # ──────────────────────────────────────────────
    def on_table_changed(self, event):
        selected = self.combo_tables.get()
        if selected:
            self.load_table_data(selected)

    def load_table_data(self, table_name):
        if table_name in self.all_tables_data:
            data = self.all_tables_data[table_name]
            self.current_table = table_name
            self.current_columns = data["columns"]
            self.current_rows = data["rows"]
        else:
            if not self.db_conn:
                return
            self.current_table = table_name
            cursor = self.db_conn.cursor()

            cursor.execute(f"PRAGMA table_info('{table_name}');")
            cols_info = cursor.fetchall()
            self.current_columns = [self.safe_format_cell(c[1]) for c in cols_info]

            cursor.execute(f"SELECT * FROM '{table_name}';")
            raw_rows = cursor.fetchall()
            self.current_rows = []
            for row in raw_rows:
                processed = [
                    self.safe_format_cell(item, self.current_columns[idx])
                    for idx, item in enumerate(row)
                ]
                self.current_rows.append(processed)

        self.entry_search.delete(0, tk.END)
        self.render_tree(self.current_columns, self.current_rows)

    def render_tree(self, columns, rows):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = columns

        sample_rows = rows[:150]

        for idx, col in enumerate(columns):
            max_chars = len(col)
            for r in sample_rows:
                if idx < len(r):
                    max_chars = max(max_chars, len(str(r[idx])))

            calc_width = (max_chars * 9) + 30

            col_lower = col.lower()
            if col_lower in ['url', 'target_path', 'referrer', 'original_url', 'tab_url']:
                calc_width = max(calc_width, 400)
            elif col_lower in ['title', 'name', 'value', 'host_key', 'path']:
                calc_width = max(calc_width, 280)
            else:
                calc_width = max(calc_width, 90)

            calc_width = min(calc_width, 700)

            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, width=calc_width, minwidth=70, stretch=False)

        for row in rows:
            self.tree.insert("", tk.END, values=row)

        self.lbl_count.config(text=f"Registros: {len(rows)}")

    def filter_data(self, event=None):
        query = self.entry_search.get().lower().strip()
        if not query:
            self.render_tree(self.current_columns, self.current_rows)
            return

        filtered = [
            row for row in self.current_rows
            if any(query in str(cell).lower() for cell in row)
        ]
        self.render_tree(self.current_columns, filtered)

    def copy_selected_row(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        text = " | ".join(str(v) for v in vals)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.lbl_status.config(text="📋 Linha copiada para a área de transferência!")

    # ──────────────────────────────────────────────
    #   GERAÇÃO HTML
    # ──────────────────────────────────────────────
    def generate_html_css(self):
        """Retorna o CSS completo para o relatório HTML."""
        return """
        :root {
            --bg-body: #0f0f1a;
            --bg-card: #1a1a2e;
            --bg-table-header: #16213e;
            --bg-table-row: #1a1a2e;
            --bg-table-row-alt: #0f0f1a;
            --bg-table-hover: #e94560;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0b8;
            --accent: #ff7518;
            --accent-glow: rgba(255, 117, 24, 0.3);
            --border: #2a2a45;
            --success: #00d97e;
            --url-color: #64b5f6;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
            background: var(--bg-body);
            color: var(--text-primary);
            line-height: 1.6;
        }

        .hero {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            border-bottom: 3px solid var(--accent);
            padding: 40px 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .hero::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 30% 50%, var(--accent-glow), transparent 60%);
            animation: pulse 8s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 0.6; }
        }

        .hero h1 {
            font-size: 2.2em;
            font-weight: 800;
            color: var(--accent);
            position: relative;
            z-index: 1;
            text-shadow: 0 0 30px var(--accent-glow);
        }

        .hero .subtitle {
            font-size: 1.05em;
            color: var(--text-secondary);
            margin-top: 8px;
            position: relative;
            z-index: 1;
        }

        .hero .meta-info {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            position: relative;
            z-index: 1;
            flex-wrap: wrap;
        }

        .meta-badge {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 8px 18px;
            font-size: 0.9em;
        }

        .meta-badge strong {
            color: var(--accent);
        }

        /* Navegação por Tabelas */
        .nav-bar {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 15px 30px;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
        }

        .nav-bar h3 {
            color: var(--text-secondary);
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 10px;
        }

        .nav-links {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .nav-links a {
            color: var(--text-primary);
            text-decoration: none;
            background: var(--bg-body);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 0.85em;
            transition: all 0.2s;
        }

        .nav-links a:hover {
            background: var(--accent);
            color: #fff;
            border-color: var(--accent);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px var(--accent-glow);
        }

        /* Seção da Tabela */
        .table-section {
            margin: 30px;
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid var(--border);
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .table-header {
            background: linear-gradient(90deg, var(--bg-table-header), #1a1a3e);
            padding: 20px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--accent);
        }

        .table-header h2 {
            color: var(--accent);
            font-size: 1.3em;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .table-header h2::before {
            content: '📋';
        }

        .row-count {
            background: var(--accent);
            color: #fff;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 700;
        }

        .table-wrapper {
            overflow-x: auto;
            max-height: 70vh;
            overflow-y: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88em;
        }

        thead {
            position: sticky;
            top: 0;
            z-index: 10;
        }

        thead th {
            background: var(--bg-table-header);
            color: var(--accent);
            padding: 14px 16px;
            text-align: left;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 0.8px;
            border-bottom: 2px solid var(--accent);
            white-space: nowrap;
        }

        tbody tr {
            transition: background 0.15s;
        }

        tbody tr:nth-child(even) {
            background: var(--bg-table-row-alt);
        }

        tbody tr:nth-child(odd) {
            background: var(--bg-table-row);
        }

        tbody tr:hover {
            background: rgba(233, 69, 96, 0.15) !important;
        }

        tbody td {
            padding: 10px 16px;
            border-bottom: 1px solid var(--border);
            max-width: 500px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: var(--text-primary);
        }

        tbody td:hover {
            white-space: normal;
            word-break: break-all;
            overflow: visible;
            background: rgba(255, 255, 255, 0.03);
        }

        /* Destaque especial para URLs */
        td.cell-url {
            color: var(--url-color);
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            font-size: 0.85em;
        }

        td.cell-null {
            color: #555;
            font-style: italic;
        }

        td.cell-binary {
            color: #888;
            font-style: italic;
            background: rgba(255, 255, 255, 0.02);
        }

        td.cell-date {
            color: var(--success);
            font-weight: 500;
        }

        /* Tabela vazia */
        .empty-table {
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
            font-style: italic;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 30px;
            color: var(--text-secondary);
            font-size: 0.85em;
            border-top: 1px solid var(--border);
            margin-top: 40px;
        }

        .footer a {
            color: var(--accent);
            text-decoration: none;
        }

        /* Responsivo */
        @media (max-width: 768px) {
            .hero h1 { font-size: 1.5em; }
            .table-section { margin: 15px; }
            .meta-info { flex-direction: column; align-items: center; }
        }

        /* Scroll customizado */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-body);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent);
        }
        """

    def classify_cell(self, value, col_name=""):
        """Retorna classe CSS e valor formatado para a célula."""
        val_str = str(value)
        col_lower = col_name.lower()

        if val_str == "NULL":
            return "cell-null", val_str

        if val_str.startswith("[Binário"):
            return "cell-binary", val_str

        if any(k in col_lower for k in ["url", "referrer", "target_path", "original_url"]):
            return "cell-url", val_str

        time_keywords = ["time", "date", "expires", "created", "last_visit", "accessed"]
        if any(t in col_lower for t in time_keywords):
            # Verifica se parece com data formatada
            if "/" in val_str and ":" in val_str:
                return "cell-date", val_str

        return "", val_str

    def build_table_html(self, table_name, columns, rows):
        """Gera o HTML de UMA seção de tabela."""
        safe_id = html.escape(table_name.replace(" ", "_"))

        section = f'<div class="table-section" id="table-{safe_id}">\n'
        section += f'  <div class="table-header">\n'
        section += f'    <h2>{html.escape(table_name)}</h2>\n'
        section += f'    <span class="row-count">{len(rows)} registros</span>\n'
        section += f'  </div>\n'

        if not rows:
            section += '  <div class="empty-table">Nenhum registro encontrado nesta tabela.</div>\n'
            section += '</div>\n'
            return section

        section += '  <div class="table-wrapper">\n'
        section += '    <table>\n'

        # Cabeçalho
        section += '      <thead><tr>\n'
        for col in columns:
            section += f'        <th>{html.escape(str(col))}</th>\n'
        section += '      </tr></thead>\n'

        # Corpo
        section += '      <tbody>\n'
        for row in rows:
            section += '        <tr>\n'
            for idx, cell in enumerate(row):
                col_name = columns[idx] if idx < len(columns) else ""
                css_class, formatted_val = self.classify_cell(cell, col_name)
                cls_attr = f' class="{css_class}"' if css_class else ""

                escaped_val = html.escape(str(formatted_val))

                # Se for URL, torna clicável
                if css_class == "cell-url" and (
                    escaped_val.startswith("http://") or escaped_val.startswith("https://")
                ):
                    display_val = (
                        f'<a href="{escaped_val}" target="_blank" '
                        f'style="color:inherit;text-decoration:underline dotted">'
                        f'{escaped_val}</a>'
                    )
                else:
                    display_val = escaped_val

                section += f'          <td{cls_attr} title="{escaped_val}">{display_val}</td>\n'
            section += '        </tr>\n'
        section += '      </tbody>\n'
        section += '    </table>\n'
        section += '  </div>\n'
        section += '</div>\n'

        return section

    def generate_full_html(self, tables_dict, title="Relatório do Navegador"):
        """Gera o documento HTML completo com TODAS as tabelas."""
        now = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        total_records = sum(len(d["rows"]) for d in tables_dict.values())
        total_tables = len(tables_dict)

        doc = "<!DOCTYPE html>\n<html lang='pt-BR'>\n<head>\n"
        doc += "  <meta charset='UTF-8'>\n"
        doc += "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
        doc += f"  <title>{html.escape(title)}</title>\n"
        doc += f"  <style>{self.generate_html_css()}</style>\n"
        doc += "</head>\n<body>\n\n"

        # Hero
        doc += '<div class="hero">\n'
        doc += f'  <h1>🔍 {html.escape(title)}</h1>\n'
        doc += f'  <p class="subtitle">Relatório gerado pelo Inspetor Universal de Navegador</p>\n'
        doc += '  <div class="meta-info">\n'
        doc += f'    <span class="meta-badge">📄 Arquivo: <strong>{html.escape(self.source_file_name)}</strong></span>\n'
        doc += f'    <span class="meta-badge">📊 Tabelas: <strong>{total_tables}</strong></span>\n'
        doc += f'    <span class="meta-badge">🗃️ Registros: <strong>{total_records:,}</strong></span>\n'
        doc += f'    <span class="meta-badge">🕐 Gerado: <strong>{now}</strong></span>\n'
        doc += '  </div>\n'
        doc += '</div>\n\n'

        # Navegação
        doc += '<div class="nav-bar">\n'
        doc += '  <h3>⚡ Navegação Rápida</h3>\n'
        doc += '  <div class="nav-links">\n'
        for tname in tables_dict:
            safe_id = html.escape(tname.replace(" ", "_"))
            row_count = len(tables_dict[tname]["rows"])
            doc += f'    <a href="#table-{safe_id}">{html.escape(tname)} ({row_count})</a>\n'
        doc += '  </div>\n'
        doc += '</div>\n\n'

        # Tabelas
        for tname, tdata in tables_dict.items():
            doc += self.build_table_html(tname, tdata["columns"], tdata["rows"])
            doc += "\n"

        # Footer
        doc += '<div class="footer">\n'
        doc += f'  <p>Relatório gerado em {now}</p>\n'
        doc += '  <p>Inspetor Universal de Navegador v5 — '
        doc += 'Ferramenta de análise forense de bancos de dados de navegadores</p>\n'
        doc += '</div>\n\n'

        # JavaScript para busca no HTML
        doc += """
<script>
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'f') {
        // Permite busca nativa do navegador
    }
});

// Botão voltar ao topo
window.addEventListener('scroll', function() {
    let btn = document.getElementById('btn-top');
    if (!btn) {
        btn = document.createElement('button');
        btn.id = 'btn-top';
        btn.innerHTML = '⬆';
        btn.style.cssText = `
            position: fixed; bottom: 30px; right: 30px;
            width: 50px; height: 50px; border-radius: 50%;
            background: #ff7518; color: #fff; border: none;
            font-size: 1.5em; cursor: pointer; z-index: 999;
            box-shadow: 0 4px 15px rgba(255,117,24,0.4);
            transition: opacity 0.3s, transform 0.3s;
        `;
        btn.onclick = () => window.scrollTo({top: 0, behavior: 'smooth'});
        document.body.appendChild(btn);
    }
    btn.style.opacity = window.scrollY > 300 ? '1' : '0';
    btn.style.transform = window.scrollY > 300 ? 'scale(1)' : 'scale(0.5)';
});
</script>
"""

        doc += "</body>\n</html>"
        return doc

    # ──────────────────────────────────────────────
    #   EXPORTAÇÃO
    # ──────────────────────────────────────────────
    def export_current_table_html(self):
        """Exporta apenas a tabela atual (com filtro aplicado se houver)."""
        if not self.current_table or not self.current_columns:
            messagebox.showwarning("Aviso", "Nenhuma tabela carregada para exportar.")
            return

        # Pega as linhas atualmente visíveis (pode ter filtro)
        visible_rows = []
        for item_id in self.tree.get_children():
            vals = self.tree.item(item_id, "values")
            visible_rows.append(list(vals))

        save_path = filedialog.asksaveasfilename(
            title="Salvar Tabela como HTML",
            defaultextension=".html",
            initialfile=f"{self.source_file_name}_{self.current_table}.html",
            filetypes=[("HTML", "*.html"), ("Todos", "*.*")]
        )
        if not save_path:
            return

        single_table = {
            self.current_table: {
                "columns": self.current_columns,
                "rows": visible_rows
            }
        }

        title = f"{self.source_file_name} — {self.current_table}"
        full_html = self.generate_full_html(single_table, title=title)

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(full_html)

            size_kb = os.path.getsize(save_path) / 1024
            self.lbl_status.config(
                text=f"✅ Tabela '{self.current_table}' exportada! "
                     f"({len(visible_rows)} registros, {size_kb:.1f} KB) → {save_path}"
            )
            messagebox.showinfo(
                "Exportação Concluída",
                f"Tabela '{self.current_table}' salva com sucesso!\n\n"
                f"📊 {len(visible_rows)} registros\n"
                f"📄 {size_kb:.1f} KB\n"
                f"📁 {save_path}"
            )

            # Abre no navegador automaticamente
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(save_path)}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")

    def export_all_tables_html(self):
        """Exporta TODAS as tabelas em um único HTML completo."""
        if not self.all_tables_data:
            messagebox.showwarning("Aviso", "Nenhum banco de dados carregado.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Salvar TODAS as Tabelas como HTML",
            defaultextension=".html",
            initialfile=f"{self.source_file_name}_COMPLETO.html",
            filetypes=[("HTML", "*.html"), ("Todos", "*.*")]
        )
        if not save_path:
            return

        self.lbl_status.config(text="⏳ Gerando relatório completo... Aguarde...")
        self.root.update()

        title = f"Relatório Completo — {self.source_file_name}"
        full_html = self.generate_full_html(self.all_tables_data, title=title)

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(full_html)

            total_records = sum(len(d["rows"]) for d in self.all_tables_data.values())
            total_tables = len(self.all_tables_data)
            size_kb = os.path.getsize(save_path) / 1024
            size_display = (
                f"{size_kb:.1f} KB" if size_kb < 1024
                else f"{size_kb / 1024:.2f} MB"
            )

            self.lbl_status.config(
                text=f"✅ Relatório COMPLETO exportado! "
                     f"({total_tables} tabelas, {total_records} registros, "
                     f"{size_display}) → {save_path}"
            )
            messagebox.showinfo(
                "Exportação Completa!",
                f"Relatório completo salvo com sucesso!\n\n"
                f"📊 {total_tables} tabelas\n"
                f"🗃️ {total_records:,} registros totais\n"
                f"📄 {size_display}\n"
                f"📁 {save_path}"
            )

            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(save_path)}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")

    def __del__(self):
        self.close_current_db()


# ══════════════════════════════════════════════════
#   INICIALIZAÇÃO
# ══════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalBrowserInspector(root)
    root.mainloop()
