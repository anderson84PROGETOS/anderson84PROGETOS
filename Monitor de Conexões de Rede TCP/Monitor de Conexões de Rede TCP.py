import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import psutil
import subprocess
import re
import time
import webbrowser
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class NetworkMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Conexões de Rede TCP")
        self.root.geometry("1600x750")
        self.root.state("zoomed")
        self.root.configure(bg="#000000")

        self.root.option_add('*Menu*background', '#000000')
        self.root.option_add('*Menu*foreground', '#00ff9d')
        self.root.option_add('*Menu*activeBackground', '#00aa66')
        self.root.option_add('*Menu*activeForeground', "#000000")

        self.auto_refresh = tk.BooleanVar(value=False)
        self.countdown_var = tk.StringVar(value="5")
        self.refresh_job = None
        self.countdown_job = None

        self.setup_style()
        self.setup_ui()
        self.create_context_menu()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        bg_color = "#000000"
        fg_color = "#00ff9d"
        accent = "#00cc7a"
        table_bg = "#000000"
        selected_bg = "#00aa66"
        button_bg = "#111111"

        style.configure(".", background=bg_color, foreground=fg_color, fieldbackground=table_bg)
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("TFrame", background=bg_color)
        style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color, font=("Arial", 10, "bold"))

        style.configure("Treeview",
                       background=table_bg,
                       foreground=fg_color,
                       fieldbackground=table_bg,
                       font=("Consolas", 10))
        style.configure("Treeview.Heading",
                       background=accent,
                       foreground="#000000",
                       font=("Arial", 10, "bold"))
        style.map("Treeview",
                 background=[('selected', selected_bg)],
                 foreground=[('selected', '#000000')])

        style.configure("TButton",
                       background=button_bg,
                       foreground=fg_color,
                       font=("Arial", 10, "bold"),
                       padding=6)
        style.map("TButton",
                 background=[('active', '#00cc7a')],
                 foreground=[('active', '#000000')])

        style.configure("TCheckbutton",
                       background=bg_color,
                       foreground=fg_color,
                       font=("Arial", 10))
        style.map("TCheckbutton",
                 background=[('active', bg_color)],
                 foreground=[('active', '#00ff9d')])

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        title = ttk.Label(main_frame, text="Monitor de Conexões TCP",
                         font=("Arial", 18, "bold"), foreground="#00ff9d")
        title.pack(pady=12)

        table_frame = ttk.LabelFrame(main_frame, text="Conexões Ativas")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=8)

        self.columns = [
            ("#", 12), ("Processo", 130), ("PID", 60),
            ("Endereço Local", 270), ("Porta Local", 80),
            ("Endereço Remoto", 230), ("Porta Remota", 100),
            ("Status", 80), ("Perca de Pacote %", 130),
            ("Latência (ms)", 110)
        ]

        col_names = [col[0] for col in self.columns]
        self.tree = ttk.Treeview(table_frame, columns=col_names, show="headings", height=23)

        for col, width in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Button-3>", self.show_context_menu)

        # ==================== BOTÕES ====================
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=6)

        ttk.Button(btn_frame, text="🔄 Atualizar Agora", command=self.manual_update).pack(side=tk.LEFT, padx=8)

        self.auto_check = ttk.Checkbutton(
            btn_frame,
            text="Atualizar a cada 5 segundos",
            variable=self.auto_refresh,
            command=self.toggle_auto_refresh
        )
        self.auto_check.pack(side=tk.LEFT, padx=15)

        self.countdown_label = tk.Label(
            btn_frame,
            textvariable=self.countdown_var,
            font=("Arial", 14, "bold"),
            fg="#00ff9d",
            bg="#000000",
            width=3,
            anchor="center"
        )
        self.countdown_label.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="💾 Salvar Resultados", command=self.save_results).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Fechar", command=self.root.quit).pack(side=tk.LEFT, padx=8)

        # ==================== STATUS ====================
        self.status_label = ttk.Label(main_frame,
                                     text="Clique em 'Atualizar Agora' para carregar as conexões",
                                     foreground="#00cc7a")
        self.status_label.pack(pady=6)

        # ==================== RODAPÉ ====================
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)

        footer_text = (
            "Como usar: • Clique com o botão direito em um IP (Local ou Remoto) → '🔍 Abrir no VirusTotal' • "
            "Marque 'Atualizar a cada 5 segundos' para monitoramento automático\n\n"
            "💾 Salvar Resultados para exportar em .txt      🔎 Ou Pesquise no Windows Por resmon"
        )

        footer_label = ttk.Label(
            footer_frame,
            text=footer_text,
            font=("Arial", 9),
            foreground="#558866",
            wraplength=1380,
            justify="center"
        )
        footer_label.pack(pady=5)

    def create_context_menu(self):
        self.context_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg="#000000",
            fg="#00ff9d",
            activebackground="#00aa66",
            activeforeground="#000000",
            font=("Arial", 10),
            relief="solid",
            borderwidth=1
        )
        self.context_menu.add_command(
            label="🔍 Abrir no VirusTotal",
            command=self.open_in_virustotal
        )

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if not item:
            return

        values = self.tree.item(item, "values")
        if not values:
            return

        try:
            col_index = int(column.replace("#", "")) - 1
        except:
            return

        if col_index in [3, 5]:  # Endereço Local ou Remoto
            cell_value = values[col_index]
            if cell_value and cell_value != "-" and not cell_value.startswith("Porta"):
                self.selected_ip = cell_value
                self.context_menu.post(event.x_root, event.y_root)

    def open_in_virustotal(self):
        if hasattr(self, 'selected_ip') and self.selected_ip:
            url = f"https://www.virustotal.com/gui/ip-address/{self.selected_ip}"
            try:
                webbrowser.open(url)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível abrir o navegador:\n{e}")

    def toggle_auto_refresh(self):
        if self.auto_refresh.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()

    def start_auto_refresh(self):
        self.stop_auto_refresh()
        self.countdown_var.set("5")
        self.update_countdown()

    def stop_auto_refresh(self):
        if self.refresh_job:
            self.root.after_cancel(self.refresh_job)
            self.refresh_job = None
        if self.countdown_job:
            self.root.after_cancel(self.countdown_job)
            self.countdown_job = None
        self.countdown_var.set("")

    def update_countdown(self):
        try:
            current = int(self.countdown_var.get())
        except:
            current = 5

        if current > 0:
            self.countdown_var.set(str(current - 1))
            self.countdown_job = self.root.after(1000, self.update_countdown)
        else:
            self.manual_update()
            self.countdown_var.set("5")
            self.update_countdown()

    def manual_update(self):
        self.update_connections()
        if self.auto_refresh.get() and not self.countdown_job:
            self.countdown_var.set("5")
            self.update_countdown()

    # ==================== SALVAR RESULTADOS ====================
    def save_results(self):
        children = self.tree.get_children()
        if not children:
            messagebox.showwarning("Aviso", "Nenhum dado para salvar.\nAtualize a tabela primeiro.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
            title="Salvar resultados das conexões"
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("MONITOR DE CONEXÕES TCP\n")
                f.write("=" * 50 + "\n")
                f.write(f"Exportado em: {time.strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                f.write(f"Total de conexões: {len(children)}\n")
                f.write("=" * 50 + "\n\n")

                for i, item in enumerate(children, 1):
                    values = self.tree.item(item, "values")
                    f.write(f"Conexão: {i}\n")
                    f.write(f"Processo: {values[1]}\n")
                    f.write(f"PID: {values[2]}\n")
                    f.write(f"Endereço Local: {values[3]}\n")
                    f.write(f"Porta Local: {values[4]}\n")
                    f.write(f"Endereço Remoto: {values[5]}\n")
                    f.write(f"Porta Remota: {values[6]}\n")
                    f.write(f"Status: {values[7]}\n")
                    f.write(f"Perca de Pacote %: {values[8]}\n")
                    f.write(f"Latência (ms): {values[9]}\n")
                    f.write("-" * 40 + "\n\n")

            self.status_label.config(text=f"Salvo em: {filepath}", foreground="#00ff9d")
            messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso!\n\n{filepath}")

        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")

    # ==================== PING SEM JANELA DO CMD ====================
    def ping_host(self, ip, timeout=1, count=4):
        """Ping sem mostrar janela do CMD (Windows)"""
        try:
            # Configuração para esconder a janela do console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            output = subprocess.check_output(
                ["ping", "-n", str(count), "-w", str(int(timeout * 1000)), ip],
                stderr=subprocess.STDOUT,
                timeout=(timeout * count) + 2,
                startupinfo=startupinfo   # ← Aqui está o segredo
            ).decode('utf-8', errors='ignore')

            latencies = re.findall(r"tempo[=<](\d+)", output, re.IGNORECASE)

            loss_match = re.search(r"Perdidos\s*=\s*(\d+)", output, re.IGNORECASE)
            if loss_match:
                lost = int(loss_match.group(1))
            else:
                pct_match = re.search(r"(\d+)%[%\s]*(perda|loss)", output, re.IGNORECASE)
                if pct_match:
                    lost = int(count * int(pct_match.group(1)) / 100)
                else:
                    lost = count - len(latencies) if latencies else count

            loss_pct = round((lost / count) * 100, 1)

            if latencies:
                avg_latency = round(sum(int(l) for l in latencies) / len(latencies))
            else:
                avg_latency = "-"

            return ip, avg_latency, loss_pct

        except Exception:
            return ip, "-", 100.0

    def update_connections_thread(self):
        try:
            connections = psutil.net_connections(kind='tcp')
            seen = set()
            ping_tasks = []
            row_num = 1

            for conn in connections:
                if not conn.raddr or conn.raddr.ip in seen:
                    continue
                if conn.raddr.ip.startswith(("127.", "::", "0.")):
                    continue

                seen.add(conn.raddr.ip)

                proc_name = "Unknown"
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        proc_name = proc.name()
                    except:
                        pass

                ping_tasks.append((
                    conn.raddr.ip,
                    proc_name,
                    conn.pid or "-",
                    conn.laddr.ip if conn.laddr else "-",
                    conn.laddr.port if conn.laddr else "-",
                    conn.raddr.port,
                    conn.status,
                    row_num
                ))
                row_num += 1
                if row_num > 100:
                    break

            if not ping_tasks:
                self.root.after(0, self._update_ui, [])
                return

            max_workers = min(30, len(ping_tasks))
            results = {}
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(self.ping_host, ip, 0.5, 4): ip
                    for ip, *_ in ping_tasks
                }
                for future in as_completed(future_map):
                    ip, latency, loss_pct = future.result()
                    results[ip] = (latency, loss_pct)

            rows = []
            for ip, proc_name, pid, laddr_ip, laddr_port, raddr_port, status, rn in ping_tasks:
                latency, loss_pct = results.get(ip, ("-", 100.0))
                rows.append((
                    rn, proc_name, pid,
                    laddr_ip, laddr_port,
                    ip, raddr_port,
                    status,
                    f"{loss_pct}%",
                    latency
                ))

            self.root.after(0, self._update_ui, rows)

        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(
                text=f"Erro: {e}", foreground="#ff5555"
            ))

    def _update_ui(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            self.tree.insert("", tk.END, values=row)

        self.status_label.config(
            text=f"Atualizado com {len(rows)} conexões • {time.strftime('%H:%M:%S')}",
            foreground="#00ff9d"
        )

    def update_connections(self):
        self.status_label.config(text="Atualizando... (pings em paralelo)", foreground="#00ff9d")
        threading.Thread(target=self.update_connections_thread, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkMonitor(root)
    root.mainloop()
