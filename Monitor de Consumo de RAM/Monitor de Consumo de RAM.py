import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import os
from datetime import datetime
import webbrowser
import json
import platform

class MonitorRAM:
    def __init__(self, root):
        self.root = root
        self.root.title("🖥️ Monitor de Consumo de RAM")
        self.root.geometry("950x700")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)

        try:
            if platform.system() == "Windows":
                self.root.after(100, lambda: self.root.state("zoomed"))
            else:
                self.root.after(200, lambda: self.root.attributes("-zoomed", True))
        except Exception:
            pass        

        # Estilo
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure("Title.TLabel",
                             font=("Segoe UI", 18, "bold"),
                             foreground="#cdd6f4",
                             background="#1e1e2e")

        self.style.configure("Info.TLabel",
                             font=("Segoe UI", 11),
                             foreground="#a6adc8",
                             background="#1e1e2e")

        self.style.configure("Custom.Treeview",
                             background="#313244",
                             foreground="#cdd6f4",
                             fieldbackground="#313244",
                             font=("Segoe UI", 10),
                             rowheight=28)

        self.style.configure("Custom.Treeview.Heading",
                             background="#45475a",
                             foreground="#cdd6f4",
                             font=("Segoe UI", 11, "bold"))

        self.style.map("Custom.Treeview",
                       background=[("selected", "#585b70")])

        self.processos_data = []
        self.auto_refresh = False

        self.criar_interface()
        self.atualizar_dados()

    def criar_interface(self):
        main_frame = tk.Frame(self.root, bg="#1e1e2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Título
        titulo = ttk.Label(main_frame,
                           text="🖥️ Monitor de Consumo de RAM",
                           style="Title.TLabel")
        titulo.pack(pady=(5, 10))

        # Frame info RAM
        info_frame = tk.Frame(main_frame, bg="#313244",
                              highlightbackground="#585b70",
                              highlightthickness=1)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.label_ram_total = ttk.Label(info_frame, text="", style="Info.TLabel")
        self.label_ram_total.configure(background="#313244")
        self.label_ram_total.pack(side=tk.LEFT, padx=20, pady=10)

        self.label_ram_usada = ttk.Label(info_frame, text="", style="Info.TLabel")
        self.label_ram_usada.configure(background="#313244")
        self.label_ram_usada.pack(side=tk.LEFT, padx=20, pady=10)

        self.label_ram_livre = ttk.Label(info_frame, text="", style="Info.TLabel")
        self.label_ram_livre.configure(background="#313244")
        self.label_ram_livre.pack(side=tk.LEFT, padx=20, pady=10)

        self.label_ram_percent = ttk.Label(info_frame, text="", style="Info.TLabel")
        self.label_ram_percent.configure(background="#313244")
        self.label_ram_percent.pack(side=tk.LEFT, padx=20, pady=10)

        # Barra de progresso
        progress_frame = tk.Frame(main_frame, bg="#1e1e2e")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.style.configure("RAM.Horizontal.TProgressbar",
                             troughcolor="#313244",
                             background="#89b4fa",
                             thickness=25)

        self.barra_ram = ttk.Progressbar(progress_frame,
                                          style="RAM.Horizontal.TProgressbar",
                                          length=400, mode='determinate')
        self.barra_ram.pack(fill=tk.X)

        # Tabela
        tree_frame = tk.Frame(main_frame, bg="#1e1e2e")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        colunas = ("pos", "pid", "nome", "ram_mb", "ram_percent", "status", "usuario")
        self.tree = ttk.Treeview(tree_frame, columns=colunas,
                                  show="headings", style="Custom.Treeview",
                                  yscrollcommand=scrollbar_y.set,
                                  xscrollcommand=scrollbar_x.set)

        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        self.tree.heading("pos", text="#")
        self.tree.heading("pid", text="PID")
        self.tree.heading("nome", text="Nome do Processo")
        self.tree.heading("ram_mb", text="RAM (MB)")
        self.tree.heading("ram_percent", text="RAM (%)")
        self.tree.heading("status", text="Status")
        self.tree.heading("usuario", text="Usuário")

        self.tree.column("pos", width=50, anchor="center")
        self.tree.column("pid", width=70, anchor="center")
        self.tree.column("nome", width=250, anchor="w")
        self.tree.column("ram_mb", width=100, anchor="center")
        self.tree.column("ram_percent", width=90, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("usuario", width=150, anchor="w")

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Botões
        btn_frame = tk.Frame(main_frame, bg="#1e1e2e")
        btn_frame.pack(fill=tk.X, pady=(0, 5))

        btn_atualizar = tk.Button(btn_frame, text="🔄 Atualizar",
                                   font=("Segoe UI", 11, "bold"),
                                   bg="#89b4fa", fg="#1e1e2e",
                                   activebackground="#74c7ec",
                                   relief="flat", cursor="hand2",
                                   padx=20, pady=8,
                                   command=self.atualizar_dados)
        btn_atualizar.pack(side=tk.LEFT, padx=5)

        btn_salvar = tk.Button(btn_frame, text="💾 Salvar HTML com Gráficos",
                                font=("Segoe UI", 11, "bold"),
                                bg="#a6e3a1", fg="#1e1e2e",
                                activebackground="#94e2d5",
                                relief="flat", cursor="hand2",
                                padx=20, pady=8,
                                command=self.salvar_html)
        btn_salvar.pack(side=tk.LEFT, padx=5)

        btn_auto = tk.Button(btn_frame, text="⏱️ Auto Refresh (5s)",
                              font=("Segoe UI", 11, "bold"),
                              bg="#f9e2af", fg="#1e1e2e",
                              activebackground="#f5c2e7",
                              relief="flat", cursor="hand2",
                              padx=20, pady=8,
                              command=self.toggle_auto_refresh)
        btn_auto.pack(side=tk.LEFT, padx=5)

        self.label_status = ttk.Label(btn_frame, text="", style="Info.TLabel")
        self.label_status.pack(side=tk.RIGHT, padx=10)

        self.label_count = ttk.Label(main_frame, text="", style="Info.TLabel")
        self.label_count.pack(anchor="w")

    def obter_processos(self):
        processos = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info',
                                          'memory_percent', 'status', 'username']):
            try:
                info = proc.info
                ram_bytes = info['memory_info'].rss if info['memory_info'] else 0
                ram_mb = ram_bytes / (1024 * 1024)
                ram_percent = info['memory_percent'] if info['memory_percent'] else 0.0

                try:
                    usuario = info['username'] if info['username'] else "N/A"
                except (psutil.AccessDenied, KeyError):
                    usuario = "N/A"

                try:
                    status = info['status'] if info['status'] else "N/A"
                except (psutil.AccessDenied, KeyError):
                    status = "N/A"

                processos.append({
                    'pid': info['pid'],
                    'nome': info['name'] if info['name'] else "Desconhecido",
                    'ram_mb': round(ram_mb, 2),
                    'ram_percent': round(ram_percent, 2),
                    'status': status,
                    'usuario': usuario
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        processos.sort(key=lambda x: x['ram_mb'], reverse=True)
        return processos

    def atualizar_dados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        ram = psutil.virtual_memory()
        ram_total = ram.total / (1024 ** 3)
        ram_usada = ram.used / (1024 ** 3)
        ram_livre = ram.available / (1024 ** 3)
        ram_percent = ram.percent

        self.label_ram_total.config(text=f"📊 Total: {ram_total:.2f} GB")
        self.label_ram_usada.config(text=f"🔴 Usada: {ram_usada:.2f} GB")
        self.label_ram_livre.config(text=f"🟢 Livre: {ram_livre:.2f} GB")
        self.label_ram_percent.config(text=f"📈 Uso: {ram_percent}%")

        self.barra_ram['value'] = ram_percent

        if ram_percent > 80:
            self.style.configure("RAM.Horizontal.TProgressbar", background="#f38ba8")
        elif ram_percent > 60:
            self.style.configure("RAM.Horizontal.TProgressbar", background="#f9e2af")
        else:
            self.style.configure("RAM.Horizontal.TProgressbar", background="#a6e3a1")

        self.processos_data = self.obter_processos()

        for i, proc in enumerate(self.processos_data, 1):
            tag = ""
            if i <= 3:
                tag = "top3"
            elif proc['ram_mb'] < 1:
                tag = "baixo"

            self.tree.insert("", tk.END, values=(
                i, proc['pid'], proc['nome'],
                f"{proc['ram_mb']:.2f}", f"{proc['ram_percent']:.2f}%",
                proc['status'], proc['usuario']
            ), tags=(tag,))

        self.tree.tag_configure("top3", background="#45475a", foreground="#f38ba8")
        self.tree.tag_configure("baixo", foreground="#6c7086")

        self.label_count.config(
            text=f"📋 Total: {len(self.processos_data)} processos | "
                 f"Atualizado: {datetime.now().strftime('%H:%M:%S')}")
        self.label_status.config(text="✅ Atualizado!")

    def toggle_auto_refresh(self):
        self.auto_refresh = not self.auto_refresh
        if self.auto_refresh:
            self.label_status.config(text="⏱️ Auto refresh ATIVADO")
            self.auto_atualizar()
        else:
            self.label_status.config(text="⏱️ Auto refresh DESATIVADO")

    def auto_atualizar(self):
        if self.auto_refresh:
            self.atualizar_dados()
            self.root.after(5000, self.auto_atualizar)

    def salvar_html(self):
        if not self.processos_data:
            messagebox.showwarning("Aviso", "Nenhum dado. Atualize primeiro!")
            return

        arquivo = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("Todos", "*.*")],
            initialfile=f"monitor_ram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            title="Salvar Relatório HTML com Gráficos"
        )

        if not arquivo:
            return

        ram = psutil.virtual_memory()
        ram_total_gb = ram.total / (1024 ** 3)
        ram_usada_gb = ram.used / (1024 ** 3)
        ram_livre_gb = ram.available / (1024 ** 3)
        ram_percent = ram.percent

        try:
            nome_pc = os.environ.get('COMPUTERNAME', 'N/A')
            if nome_pc == 'N/A' and hasattr(os, 'uname'):
                nome_pc = os.uname().nodename
        except Exception:
            nome_pc = 'N/A'

        if ram_percent > 80:
            cor_barra = "#f38ba8"
        elif ram_percent > 60:
            cor_barra = "#f9e2af"
        else:
            cor_barra = "#a6e3a1"

        # Top 15 para gráfico de barras
        top15 = self.processos_data[:15]
        top15_nomes = json.dumps([p['nome'][:20] for p in top15])
        top15_ram = json.dumps([p['ram_mb'] for p in top15])
        top15_percent = json.dumps([p['ram_percent'] for p in top15])

        # Top 10 para gráfico de pizza
        top10 = self.processos_data[:10]
        top10_nomes = json.dumps([p['nome'][:25] for p in top10])
        top10_ram = json.dumps([p['ram_mb'] for p in top10])

        # Agrupar por status
        status_count = {}
        for p in self.processos_data:
            s = p['status']
            status_count[s] = status_count.get(s, 0) + 1
        status_labels = json.dumps(list(status_count.keys()))
        status_values = json.dumps(list(status_count.values()))

        # Distribuição de RAM por faixas
        faixas = {"0-1 MB": 0, "1-10 MB": 0, "10-50 MB": 0,
                  "50-100 MB": 0, "100-500 MB": 0, "500+ MB": 0}
        for p in self.processos_data:
            mb = p['ram_mb']
            if mb < 1:
                faixas["0-1 MB"] += 1
            elif mb < 10:
                faixas["1-10 MB"] += 1
            elif mb < 50:
                faixas["10-50 MB"] += 1
            elif mb < 100:
                faixas["50-100 MB"] += 1
            elif mb < 500:
                faixas["100-500 MB"] += 1
            else:
                faixas["500+ MB"] += 1

        faixas_labels = json.dumps(list(faixas.keys()))
        faixas_values = json.dumps(list(faixas.values()))

        # Top 20 para treemap/ranking
        top20 = self.processos_data[:20]
        top20_nomes = json.dumps([p['nome'][:25] for p in top20])
        top20_ram = json.dumps([p['ram_mb'] for p in top20])

        # Linhas da tabela
        linhas_html = ""
        for i, proc in enumerate(self.processos_data, 1):
            if i <= 3:
                classe = "top3"
                icone = "🥇" if i == 1 else ("🥈" if i == 2 else "🥉")
            elif proc['ram_mb'] < 1:
                classe = "baixo"
                icone = ""
            else:
                classe = ""
                icone = ""

            bar_width = min(proc['ram_percent'] * 10, 100)
            nome_s = str(proc['nome']).replace('<', '&lt;').replace('>', '&gt;')
            user_s = str(proc['usuario']).replace('<', '&lt;').replace('>', '&gt;')

            linhas_html += f"""
            <tr class="{classe}">
                <td class="center">{icone} {i}</td>
                <td class="center">{proc['pid']}</td>
                <td class="nome">{nome_s}</td>
                <td class="center">{proc['ram_mb']:.2f} MB</td>
                <td class="center">
                    <div class="bar-container">
                        <div class="bar" style="width: {bar_width}%"></div>
                        <span class="bar-text">{proc['ram_percent']:.2f}%</span>
                    </div>
                </td>
                <td class="center">{proc['status']}</td>
                <td>{user_s}</td>
            </tr>"""

        # Soma total RAM dos processos
        total_ram_procs = sum(p['ram_mb'] for p in self.processos_data)
        top5_ram_sum = sum(p['ram_mb'] for p in self.processos_data[:5])

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor de RAM - Relatório Completo com Gráficos</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #181825 100%);
            color: #cdd6f4;
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{ max-width: 1300px; margin: 0 auto; }}

        .header {{
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #313244 0%, #45475a 100%);
            border-radius: 16px;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}

        .header h1 {{
            font-size: 2.4em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #89b4fa, #cba6f7, #f38ba8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .header .subtitle {{ color: #a6adc8; font-size: 1.1em; margin-top: 5px; }}

        .ram-overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}

        .ram-card {{
            background: linear-gradient(135deg, #313244, #45475a);
            border-radius: 14px;
            padding: 22px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .ram-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        }}

        .ram-card .icon {{ font-size: 2.2em; margin-bottom: 8px; }}
        .ram-card .value {{ font-size: 1.9em; font-weight: bold; color: #89b4fa; }}
        .ram-card .label {{ color: #a6adc8; font-size: 0.9em; margin-top: 5px; }}
        .ram-card.usado .value {{ color: #f38ba8; }}
        .ram-card.livre .value {{ color: #a6e3a1; }}
        .ram-card.percent .value {{ color: {cor_barra}; }}
        .ram-card.procs .value {{ color: #cba6f7; }}

        .progress-section {{
            background: #313244;
            border-radius: 14px;
            padding: 22px;
            margin-bottom: 25px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        }}

        .progress-bar-bg {{
            background: #1e1e2e;
            border-radius: 15px;
            height: 40px;
            overflow: hidden;
            position: relative;
        }}

        .progress-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #a6e3a1, {cor_barra});
            border-radius: 15px;
            width: {ram_percent}%;
        }}

        .progress-text {{
            position: absolute;
            width: 100%;
            text-align: center;
            line-height: 40px;
            font-weight: bold;
            font-size: 1.15em;
            color: #cdd6f4;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.6);
            top: 0;
        }}

        /* GRÁFICOS */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }}

        .chart-card {{
            background: #313244;
            border-radius: 14px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        }}

        .chart-card h3 {{
            color: #cba6f7;
            margin-bottom: 15px;
            font-size: 1.2em;
            text-align: center;
        }}

        .chart-card canvas {{
            max-height: 400px;
        }}

        .chart-full {{
            grid-column: 1 / -1;
        }}

        /* TABELA */
        .table-section {{
            background: #313244;
            border-radius: 14px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            overflow-x: auto;
            margin-bottom: 25px;
        }}

        .table-section h2 {{
            margin-bottom: 15px;
            color: #cba6f7;
            font-size: 1.4em;
        }}

        table {{ width: 100%; border-collapse: collapse; }}

        thead th {{
            background: linear-gradient(135deg, #45475a, #585b70);
            color: #cdd6f4;
            padding: 14px 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #89b4fa;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        tbody tr {{
            border-bottom: 1px solid #45475a;
            transition: background 0.2s ease;
        }}

        tbody tr:hover {{ background: #45475a; }}
        tbody tr:nth-child(even) {{ background: rgba(69, 71, 90, 0.3); }}
        tbody td {{ padding: 10px 12px; font-size: 0.92em; }}
        .center {{ text-align: center; }}

        .nome {{
            font-weight: 500;
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .top3 {{ background: rgba(243, 139, 168, 0.12) !important; }}
        .top3 td {{ color: #f38ba8; font-weight: 600; }}
        .baixo td {{ color: #6c7086; }}

        .bar-container {{
            position: relative;
            background: #1e1e2e;
            border-radius: 8px;
            height: 22px;
            min-width: 100px;
            overflow: hidden;
        }}

        .bar {{
            height: 100%;
            background: linear-gradient(90deg, #89b4fa, #cba6f7);
            border-radius: 8px;
            min-width: 2px;
        }}

        .top3 .bar {{ background: linear-gradient(90deg, #f38ba8, #fab387); }}

        .bar-text {{
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.78em;
            font-weight: bold;
            color: #cdd6f4;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        }}

        .summary {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .badge {{
            background: #45475a;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85em;
            color: #a6adc8;
            display: inline-block;
            margin: 2px;
        }}

        .badge.highlight {{ background: #89b4fa; color: #1e1e2e; font-weight: bold; }}
        .badge.red {{ background: #f38ba8; color: #1e1e2e; font-weight: bold; }}
        .badge.green {{ background: #a6e3a1; color: #1e1e2e; font-weight: bold; }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #313244, #3b3d54);
            border-radius: 12px;
            padding: 18px;
            border-left: 4px solid #89b4fa;
        }}

        .stat-card h4 {{ color: #a6adc8; font-size: 0.9em; margin-bottom: 5px; }}
        .stat-card .stat-value {{ color: #cdd6f4; font-size: 1.4em; font-weight: bold; }}

        .footer {{
            text-align: center;
            padding: 25px;
            margin-top: 20px;
            color: #6c7086;
            font-size: 0.9em;
            background: #313244;
            border-radius: 14px;
        }}

        .footer strong {{ color: #89b4fa; }}

        /* Busca */
        .search-box {{
            background: #1e1e2e;
            border: 2px solid #45475a;
            color: #cdd6f4;
            padding: 10px 18px;
            border-radius: 10px;
            font-size: 1em;
            width: 300px;
            outline: none;
            transition: border-color 0.3s;
        }}

        .search-box:focus {{ border-color: #89b4fa; }}

        .btn-print {{
            background: #cba6f7;
            color: #1e1e2e;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: bold;
            cursor: pointer;
            font-size: 0.95em;
            transition: background 0.3s;
        }}

        .btn-print:hover {{ background: #f5c2e7; }}

        @media print {{
            body {{ background: white; color: #333; padding: 10px; }}
            .header {{ background: #f0f0f0; box-shadow: none; }}
            .header h1 {{ -webkit-text-fill-color: #333; color: #333; }}
            .ram-card, .chart-card, .table-section, .stat-card, .footer {{
                background: #f8f8f8; border: 1px solid #ddd; box-shadow: none;
            }}
            .ram-card .value, .stat-card .stat-value {{ color: #333; }}
            thead th {{ background: #e0e0e0; color: #333; }}
            .search-box, .btn-print {{ display: none; }}
        }}

        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.5em; }}
            .charts-grid {{ grid-template-columns: 1fr; }}
            .ram-overview {{ grid-template-columns: repeat(2, 1fr); }}
            .search-box {{ width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <h1>🖥️ Monitor de Consumo de RAM</h1>
            <p class="subtitle">Relatório Completo com Gráficos Interativos</p>
            <p class="subtitle">📅 {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')} | 💻 {nome_pc}</p>
        </div>

        <!-- CARDS DE RESUMO -->
        <div class="ram-overview">
            <div class="ram-card">
                <div class="icon">📊</div>
                <div class="value">{ram_total_gb:.2f} GB</div>
                <div class="label">RAM Total</div>
            </div>
            <div class="ram-card usado">
                <div class="icon">🔴</div>
                <div class="value">{ram_usada_gb:.2f} GB</div>
                <div class="label">RAM Usada</div>
            </div>
            <div class="ram-card livre">
                <div class="icon">🟢</div>
                <div class="value">{ram_livre_gb:.2f} GB</div>
                <div class="label">RAM Livre</div>
            </div>
            <div class="ram-card percent">
                <div class="icon">📈</div>
                <div class="value">{ram_percent}%</div>
                <div class="label">Uso Atual</div>
            </div>
            <div class="ram-card procs">
                <div class="icon">⚙️</div>
                <div class="value">{len(self.processos_data)}</div>
                <div class="label">Processos Ativos</div>
            </div>
        </div>

        <!-- BARRA DE PROGRESSO -->
        <div class="progress-section">
            <h3 style="margin-bottom: 12px; color: #cba6f7;">📊 Uso Geral da Memória RAM</h3>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill"></div>
                <div class="progress-text">
                    {ram_percent}% utilizado ({ram_usada_gb:.2f} GB de {ram_total_gb:.2f} GB)
                </div>
            </div>
        </div>

        <!-- ESTATÍSTICAS -->
        <div class="stats-grid">
            <div class="stat-card" style="border-left-color: #f38ba8;">
                <h4>🥇 Maior Consumidor</h4>
                <div class="stat-value">{self.processos_data[0]['nome'][:30] if self.processos_data else 'N/A'}</div>
                <div style="color: #f38ba8; margin-top: 4px;">{self.processos_data[0]['ram_mb']:.2f} MB</div>
            </div>
            <div class="stat-card" style="border-left-color: #a6e3a1;">
                <h4>🥄 Menor Consumidor</h4>
                <div class="stat-value">{self.processos_data[-1]['nome'][:30] if self.processos_data else 'N/A'}</div>
                <div style="color: #a6e3a1; margin-top: 4px;">{self.processos_data[-1]['ram_mb']:.2f} MB</div>
            </div>
            <div class="stat-card" style="border-left-color: #89b4fa;">
                <h4>📦 RAM Total dos Processos</h4>
                <div class="stat-value">{total_ram_procs:.2f} MB</div>
                <div style="color: #89b4fa; margin-top: 4px;">{total_ram_procs/1024:.2f} GB</div>
            </div>
            <div class="stat-card" style="border-left-color: #f9e2af;">
                <h4>🏆 Top 5 consomem</h4>
                <div class="stat-value">{top5_ram_sum:.2f} MB</div>
                <div style="color: #f9e2af; margin-top: 4px;">
                    {(top5_ram_sum/total_ram_procs*100) if total_ram_procs > 0 else 0:.1f}% do total
                </div>
            </div>
        </div>

        <!-- GRÁFICOS -->
        <div class="charts-grid">
            <!-- Gráfico 1: Gauge/Donut RAM Geral -->
            <div class="chart-card">
                <h3>🎯 Uso da RAM - Visão Geral</h3>
                <canvas id="chartGauge"></canvas>
            </div>

            <!-- Gráfico 2: Pizza Top 10 -->
            <div class="chart-card">
                <h3>🥧 Top 10 Processos - Distribuição</h3>
                <canvas id="chartPizza"></canvas>
            </div>

            <!-- Gráfico 3: Barras Horizontais Top 15 -->
            <div class="chart-card chart-full">
                <h3>📊 Top 15 Processos - Consumo de RAM (MB)</h3>
                <canvas id="chartBarras" style="max-height: 500px;"></canvas>
            </div>

            <!-- Gráfico 4: Distribuição por Faixas -->
            <div class="chart-card">
                <h3>📈 Distribuição por Faixas de Consumo</h3>
                <canvas id="chartFaixas"></canvas>
            </div>

            <!-- Gráfico 5: Status dos Processos -->
            <div class="chart-card">
                <h3>🔄 Status dos Processos</h3>
                <canvas id="chartStatus"></canvas>
            </div>

            <!-- Gráfico 6: Top 20 Barras Verticais % -->
            <div class="chart-card chart-full">
                <h3>📉 Top 20 Processos - Porcentagem da RAM (%)</h3>
                <canvas id="chartTop20" style="max-height: 450px;"></canvas>
            </div>
        </div>

        <!-- TABELA COMPLETA -->
        <div class="table-section">
            <div class="summary">
                <h2>📋 Todos os Processos (Maior → Menor)</h2>
                <div>
                    <input type="text" class="search-box" id="searchInput"
                           placeholder="🔍 Buscar processo..."
                           onkeyup="filtrarTabela()">
                    <button class="btn-print" onclick="window.print()">🖨️ Imprimir</button>
                </div>
            </div>
            <div>
                <span class="badge highlight">{len(self.processos_data)} processos</span>
                <span class="badge red">Top 3 em destaque</span>
                <span class="badge green">Ordenado por consumo</span>
            </div>
            <br>

            <div style="max-height: 600px; overflow-y: auto;">
                <table id="tabelaProcessos">
                    <thead>
                        <tr>
                            <th class="center">#</th>
                            <th class="center">PID</th>
                            <th>Nome do Processo</th>
                            <th class="center">RAM (MB)</th>
                            <th class="center">RAM (%)</th>
                            <th class="center">Status</th>
                            <th>Usuário</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas_html}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- FOOTER -->
        <div class="footer">
            <p>🖥️ <strong>Monitor de Consumo de RAM</strong> - Relatório gerado via Python + Chart.js</p>
            <p style="margin-top: 8px;">
                📊 <strong>{len(self.processos_data)}</strong> processos |
                🥇 Top: <strong>{self.processos_data[0]['nome'] if self.processos_data else 'N/A'}</strong>
                ({self.processos_data[0]['ram_mb']:.2f} MB) |
                📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            </p>
        </div>
    </div>

    <!-- SCRIPTS DOS GRÁFICOS -->
    <script>
        // Cores bonitas
        const cores = [
            '#f38ba8', '#fab387', '#f9e2af', '#a6e3a1', '#94e2d5',
            '#89dceb', '#74c7ec', '#89b4fa', '#b4befe', '#cba6f7',
            '#f5c2e7', '#eba0ac', '#f2cdcd', '#f5e0dc', '#cdd6f4'
        ];

        const coresTransp = cores.map(c => c + '99');

        // ===== GRÁFICO 1: Gauge/Donut RAM Geral =====
        new Chart(document.getElementById('chartGauge'), {{
            type: 'doughnut',
            data: {{
                labels: ['RAM Usada ({ram_usada_gb:.2f} GB)', 'RAM Livre ({ram_livre_gb:.2f} GB)'],
                datasets: [{{
                    data: [{ram_usada_gb:.2f}, {ram_livre_gb:.2f}],
                    backgroundColor: ['{cor_barra}', '#45475a'],
                    borderColor: ['#1e1e2e', '#1e1e2e'],
                    borderWidth: 3,
                    hoverOffset: 10
                }}]
            }},
            options: {{
                responsive: true,
                cutout: '65%',
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ color: '#cdd6f4', font: {{ size: 13 }}, padding: 20 }}
                    }},
                    tooltip: {{
                        backgroundColor: '#313244',
                        titleColor: '#cdd6f4',
                        bodyColor: '#a6adc8',
                        borderColor: '#585b70',
                        borderWidth: 1,
                        callbacks: {{
                            label: function(ctx) {{
                                return ctx.label + ' (' + ((ctx.parsed / {ram_total_gb:.2f}) * 100).toFixed(1) + '%)';
                            }}
                        }}
                    }}
                }}
            }},
            plugins: [{{
                id: 'centerText',
                afterDraw: function(chart) {{
                    const ctx = chart.ctx;
                    ctx.save();
                    const x = chart.getDatasetMeta(0).data[0].x;
                    const y = chart.getDatasetMeta(0).data[0].y;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.font = 'bold 36px Segoe UI';
                    ctx.fillStyle = '{cor_barra}';
                    ctx.fillText('{ram_percent}%', x, y - 8);
                    ctx.font = '14px Segoe UI';
                    ctx.fillStyle = '#a6adc8';
                    ctx.fillText('em uso', x, y + 22);
                    ctx.restore();
                }}
            }}]
        }});

        // ===== GRÁFICO 2: Pizza Top 10 =====
        new Chart(document.getElementById('chartPizza'), {{
            type: 'pie',
            data: {{
                labels: {top10_nomes},
                datasets: [{{
                    data: {top10_ram},
                    backgroundColor: cores.slice(0, 10),
                    borderColor: '#1e1e2e',
                    borderWidth: 2,
                    hoverOffset: 12
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{ color: '#cdd6f4', font: {{ size: 11 }}, padding: 8 }}
                    }},
                    tooltip: {{
                        backgroundColor: '#313244',
                        titleColor: '#cdd6f4',
                        bodyColor: '#a6adc8',
                        callbacks: {{
                            label: function(ctx) {{
                                return ctx.label + ': ' + ctx.parsed.toFixed(2) + ' MB';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // ===== GRÁFICO 3: Barras Horizontais Top 15 =====
        new Chart(document.getElementById('chartBarras'), {{
            type: 'bar',
            data: {{
                labels: {top15_nomes},
                datasets: [{{
                    label: 'RAM (MB)',
                    data: {top15_ram},
                    backgroundColor: cores.slice(0, 15).map(c => c + 'CC'),
                    borderColor: cores.slice(0, 15),
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        backgroundColor: '#313244',
                        titleColor: '#cdd6f4',
                        bodyColor: '#a6adc8',
                        callbacks: {{
                            label: function(ctx) {{
                                return ctx.parsed.x.toFixed(2) + ' MB';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        grid: {{ color: '#45475a44' }},
                        ticks: {{ color: '#a6adc8', font: {{ size: 11 }} }},
                        title: {{ display: true, text: 'Megabytes (MB)', color: '#89b4fa' }}
                    }},
                    y: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#cdd6f4', font: {{ size: 11 }} }}
                    }}
                }}
            }}
        }});

        // ===== GRÁFICO 4: Distribuição por Faixas =====
        new Chart(document.getElementById('chartFaixas'), {{
            type: 'bar',
            data: {{
                labels: {faixas_labels},
                datasets: [{{
                    label: 'Quantidade',
                    data: {faixas_values},
                    backgroundColor: ['#a6e3a1CC', '#89dcebCC', '#89b4faCC', '#cba6f7CC', '#f9e2afCC', '#f38ba8CC'],
                    borderColor: ['#a6e3a1', '#89dceb', '#89b4fa', '#cba6f7', '#f9e2af', '#f38ba8'],
                    borderWidth: 2,
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        backgroundColor: '#313244',
                        titleColor: '#cdd6f4',
                        bodyColor: '#a6adc8'
                    }}
                }},
                scales: {{
                    y: {{
                        grid: {{ color: '#45475a44' }},
                        ticks: {{ color: '#a6adc8', stepSize: 1 }},
                        title: {{ display: true, text: 'Nº de Processos', color: '#89b4fa' }}
                    }},
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#cdd6f4', font: {{ size: 11 }} }}
                    }}
                }}
            }}
        }});

        // ===== GRÁFICO 5: Status dos Processos =====
        new Chart(document.getElementById('chartStatus'), {{
            type: 'polarArea',
            data: {{
                labels: {status_labels},
                datasets: [{{
                    data: {status_values},
                    backgroundColor: cores.slice(0, {len(status_count)}).map(c => c + 'AA'),
                    borderColor: cores.slice(0, {len(status_count)}),
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ color: '#cdd6f4', font: {{ size: 12 }}, padding: 15 }}
                    }},
                    tooltip: {{
                        backgroundColor: '#313244',
                        titleColor: '#cdd6f4',
                        bodyColor: '#a6adc8'
                    }}
                }},
                scales: {{
                    r: {{
                        grid: {{ color: '#45475a44' }},
                        ticks: {{ color: '#a6adc8', backdropColor: 'transparent' }}
                    }}
                }}
            }}
        }});

        // ===== GRÁFICO 6: Top 20 Barras Verticais % =====
        new Chart(document.getElementById('chartTop20'), {{
            type: 'bar',
            data: {{
                labels: {top20_nomes},
                datasets: [
                    {{
                        label: 'RAM (MB)',
                        data: {top20_ram},
                        backgroundColor: '#89b4faAA',
                        borderColor: '#89b4fa',
                        borderWidth: 2,
                        borderRadius: 6,
                        yAxisID: 'y'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        labels: {{ color: '#cdd6f4', font: {{ size: 12 }} }}
                    }},
                    tooltip: {{
                        backgroundColor: '#313244',
                        titleColor: '#cdd6f4',
                        bodyColor: '#a6adc8'
                    }}
                }},
                scales: {{
                    y: {{
                        grid: {{ color: '#45475a44' }},
                        ticks: {{ color: '#a6adc8' }},
                        title: {{ display: true, text: 'MB', color: '#89b4fa' }}
                    }},
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{
                            color: '#cdd6f4',
                            font: {{ size: 10 }},
                            maxRotation: 45,
                            minRotation: 45
                        }}
                    }}
                }}
            }}
        }});

        // ===== FUNÇÃO DE BUSCA =====
        function filtrarTabela() {{
            const input = document.getElementById('searchInput').value.toLowerCase();
            const rows = document.querySelectorAll('#tabelaProcessos tbody tr');
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(input) ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>"""

        try:
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(html_content)

            resposta = messagebox.askyesno(
                "Sucesso! ✅",
                f"Relatório HTML com gráficos salvo!\n\n"
                f"📁 {arquivo}\n"
                f"📊 6 gráficos interativos\n"
                f"📋 {len(self.processos_data)} processos\n"
                f"🔍 Com busca e impressão\n\n"
                f"Abrir no navegador?"
            )

            if resposta:
                webbrowser.open('file://' + os.path.realpath(arquivo))

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar:\n{str(e)}")


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default='')
    except Exception:
        pass
    app = MonitorRAM(root)
    root.mainloop()


if __name__ == "__main__":
    main()
