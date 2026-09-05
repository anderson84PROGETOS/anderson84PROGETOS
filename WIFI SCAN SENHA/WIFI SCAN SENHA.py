import html
import os
import subprocess
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox, ttk


class WifiViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WIFI SCAN SENHA")
        self.root.geometry("900x620")
        self.root.minsize(750, 480)
        self.root.configure(bg="#0a0a0a")

        self.wifi_data = []

        # ==================================================
        # ESTILOS
        # ==================================================
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure(
            "Treeview",
            background="#000000",
            foreground="#00ff41",
            fieldbackground="#000000",
            rowheight=28,
            font=("Consolas", 10),
            borderwidth=0,
        )
        self.style.configure(
            "Treeview.Heading",
            background="#063d12",
            foreground="#00ff41",
            font=("Consolas", 10, "bold"),
            relief="flat",
            borderwidth=0,
        )
        self.style.map(
            "Treeview",
            background=[("selected", "#0d5c1b")],
            foreground=[("selected", "#ffffff")],
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", "#0a5c1a")],
        )
        self.style.configure(
            "Vertical.TScrollbar",
            background="#00a52a",
            troughcolor="#000000",
            bordercolor="#000000",
            arrowcolor="#000000",
        )
        self.style.configure(
            "Horizontal.TScrollbar",
            background="#00a52a",
            troughcolor="#000000",
            bordercolor="#000000",
            arrowcolor="#000000",
        )

        # ==================================================
        # TÍTULO
        # ==================================================
        tk.Label(
            root,
            text="📶  WIFI SCAN SENHA 📶",
            font=("Consolas", 28, "bold"),
            fg="#00ff41",
            bg="#0a0a0a",
        ).pack(pady=(18, 2))

        tk.Label(
            root,
            text="PERFIS E SENHAS DE REDES WI-FI SALVAS",
            font=("Consolas", 10, "bold"),
            fg="#008f25",
            bg="#0a0a0a",
        ).pack(pady=(0, 16))

        # ==================================================
        # BOTÕES
        # ==================================================
        btn_frame = tk.Frame(root, bg="#0a0a0a")
        btn_frame.pack(pady=(0, 12))

        self.btn_scan = tk.Button(
            btn_frame,
            text="▶  INICIAR SCAN",
            command=self.load_wifi_profiles,
            width=18,
            font=("Segoe UI", 10, "bold"),
            bg="#28A745",
            fg="black",
            activebackground="#49d968",
            activeforeground="black",
            cursor="hand2",
            bd=0,
            pady=8,
        )
        self.btn_scan.grid(row=0, column=0, padx=6)

        tk.Button(
            btn_frame,
            text="🌐  SALVAR HTML",
            command=self.save_to_html,
            width=18,
            font=("Segoe UI", 10, "bold"),
            bg="#00bcd4",
            fg="black",
            activebackground="#55dff0",
            activeforeground="black",
            cursor="hand2",
            bd=0,
            pady=8,
        ).grid(row=0, column=1, padx=6)

        tk.Button(
            btn_frame,
            text="🗑  LIMPAR",
            command=self.clear_table,
            width=14,
            font=("Segoe UI", 10, "bold"),
            bg="#dc3545",
            fg="white",
            activebackground="#f04b5a",
            activeforeground="white",
            cursor="hand2",
            bd=0,
            pady=8,
        ).grid(row=0, column=2, padx=6)

        # ==================================================
        # TABELA  (tudo à esquerda, como na imagem)
        # ==================================================
        table_frame = tk.Frame(
            root,
            bg="#000000",
            highlightbackground="#00a52a",
            highlightthickness=1,
        )
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

        columns = ("numero", "ssid", "password")

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        # Cabeçalhos à esquerda
        self.tree.heading("numero", text="#", anchor="w")
        self.tree.heading("ssid", text="REDE WI-FI (SSID)", anchor="w")
        self.tree.heading("password", text="🔑  SENHA", anchor="w")

        # Dados à esquerda + larguras parecidas com a imagem
        self.tree.column("numero", width=50, anchor="w", stretch=False)
        self.tree.column("ssid", width=250, anchor="w", stretch=False)
        self.tree.column("password", width=540, anchor="w", stretch=False)

        scrollbar_y = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        scrollbar_x = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # ==================================================
        # STATUS
        # ==================================================
        self.status_var = tk.StringVar()
        self.status_var.set("Sistema iniciado. Clique em INICIAR SCAN.")

        tk.Label(
            root,
            textvariable=self.status_var,
            font=("Consolas", 10),
            fg="#00a52a",
            bg="#0a0a0a",
            anchor="w",
        ).pack(fill="x", padx=22, pady=(4, 2))

        tk.Label(
            root,
            text="Consulta local de perfis Wi-Fi  •  Senhas via key=clear  •  Exportação HTML",
            font=("Consolas", 9),
            fg="#006d1c",
            bg="#0a0a0a",
        ).pack(pady=(2, 12))

    # ==================================================
    # NETSH
    # ==================================================
    def run_netsh(self, command):
        try:
            return subprocess.check_output(
                command,
                shell=True,
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            )
        except Exception as e:
            raise RuntimeError(f"Erro ao executar netsh: {e}")

    def get_value(self, lines, keywords):
        for line in lines:
            line = line.strip()
            if ":" not in line:
                continue
            for keyword in keywords:
                if keyword.lower() in line.lower():
                    return line.split(":", 1)[1].strip()
        return "Não identificado"

    # ==================================================
    # BUSCAR PERFIS E SENHAS
    # ==================================================
    def get_wifi_profiles(self):
        results = []

        try:
            profiles_output = self.run_netsh("netsh wlan show profiles")
        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Não foi possível consultar as redes Wi-Fi:\n\n{e}",
            )
            return results

        names = []
        seen = set()

        for line in profiles_output.split("\n"):
            line = line.strip()
            if any(
                k in line
                for k in [
                    "Todos os Perfis de Usu",
                    "All User Profile",
                    "Perfil de Todos os Usuários",
                    "Perfil de todos os usuários",
                ]
            ):
                try:
                    name = line.split(":", 1)[1].strip()
                    if name and name not in seen:
                        seen.add(name)
                        names.append(name)
                except Exception:
                    pass

        for number, ssid in enumerate(names, start=1):
            password = "Não identificada"
            

            try:
                details = self.run_netsh(f'netsh wlan show profile name="{ssid}"')
                lines = details.split("\n")
                pass
            except Exception:
                pass

            try:
                output = subprocess.check_output(
                    f'netsh wlan show profile name="{ssid}" key=clear',
                    shell=True,
                    universal_newlines=True,
                    stderr=subprocess.STDOUT,
                )
                for line in output.split("\n"):
                    if any(
                        k in line
                        for k in [
                            "Conteúdo da Chave",
                            "Conte£do da Chave",
                            "Key Content",
                        ]
                    ):
                        password = line.split(":", 1)[1].strip()
                        break
            except Exception:
                password = "Erro ao obter"

            results.append(
                {
                    "numero": number,
                    "ssid": ssid,
                    "password": password,
                    
                }
            )

        return results

    # ==================================================
    # LIMPAR
    # ==================================================
    def clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.wifi_data = []
        self.status_var.set("Tabela limpa.")

    # ==================================================
    # CARREGAR NA INTERFACE  (só 3 colunas, à esquerda)
    # ==================================================
    def load_wifi_profiles(self):
        self.btn_scan.config(state="disabled", text="⏳  ESCANEANDO...")
        self.root.update()

        self.clear_table()
        self.status_var.set("Buscando perfis e senhas Wi-Fi...")

        self.wifi_data = self.get_wifi_profiles()

        if not self.wifi_data:
            self.status_var.set("Nenhuma rede Wi-Fi salva foi encontrada.")
            self.btn_scan.config(state="normal", text="▶  INICIAR SCAN")
            messagebox.showinfo("Aviso", "Nenhum perfil Wi-Fi salvo foi encontrado.")
            return

        for item in self.wifi_data:
            # Apenas as 3 colunas visíveis — alinhadas à esquerda
            self.tree.insert(
                "",
                tk.END,
                values=(
                    item["numero"],
                    item["ssid"],
                    item["password"],
                ),
            )

        total = len(self.wifi_data)
        com_senha = sum(
            1
            for i in self.wifi_data
            if i["password"]
            and "não" not in i["password"].lower()
            and "erro" not in i["password"].lower()
        )

        self.status_var.set(
            f"✔  Scan concluído: "
            f"{total} Redes Encontradas  •  "
            f"{com_senha} com senha  •  "
            f"{total - com_senha} sem senha"
        )
        self.btn_scan.config(state="normal", text="▶  INICIAR SCAN")

    # ==================================================
    # EXPORTAR HTML
    # ==================================================
    def save_to_html(self):
        if not self.wifi_data:
            messagebox.showwarning(
                "Aviso",
                "Execute o scan antes de salvar o relatório.",
            )
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = filedialog.asksaveasfilename(
            title="Salvar relatório HTML",
            defaultextension=".html",
            initialfile=f"relatorio_wifi_{timestamp}.html",
            filetypes=[
                ("Arquivo HTML", "*.html"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if not file_path:
            return

        rows_html = ""
        for item in self.wifi_data:
            ssid_safe = html.escape(str(item["ssid"]))
            pwd_safe = html.escape(str(item["password"]))
            

            pwd = str(item["password"])
            if "não identificada" in pwd.lower() or "erro" in pwd.lower():
                cor_senha = "#ff6b6b"
            elif "sem senha" in pwd.lower() or "aberta" in pwd.lower():
                cor_senha = "#ffa500"
            else:
                cor_senha = "#00ff41"

            rows_html += f"""
            <tr>
                <td>{item["numero"]}</td>
                <td><strong>{ssid_safe}</strong></td>
                <td class="pwd" style="color:{cor_senha}">{pwd_safe}</td>
            </tr>"""

        total = len(self.wifi_data)
        com_senha = sum(
            1
            for i in self.wifi_data
            if i["password"]
            and "não" not in i["password"].lower()
            and "erro" not in i["password"].lower()
        )

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WIFI Relatório</title>
<style>
    * {{ box-sizing: border-box; }}
    body {{
        margin: 0; padding: 30px;
        background: #080808; color: #d7ffd7;
        font-family: Consolas, "Courier New", monospace;
    }}
    .container {{ width: 100%; max-width: 1100px; margin: auto; }}
    h1 {{
        color: #00ff41; text-align: center; font-size: 34px; margin: 0 0 8px;
        text-shadow: 0 0 15px rgba(0,255,65,0.45);
    }}
    .subtitle {{ text-align: center; color: #008f25; margin-bottom: 20px; }}
    .stats {{ display: flex; justify-content: center; gap: 20px; margin-bottom: 25px; }}
    .stat-box {{
        background: #0a1a0c; border: 1px solid #00a52a; border-radius: 8px;
        padding: 16px 28px; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }}
    .stat-box .number {{ font-size: 28px; font-weight: bold; color: #00ff41; }}
    .stat-box .label {{
        font-size: 11px; color: #aaa; margin-top: 4px;
        text-transform: uppercase; letter-spacing: 1px;
    }}
    .panel {{
        border: 1px solid #00a52a; background: #000;
        box-shadow: 0 0 25px rgba(0,255,65,0.12); overflow-x: auto;
    }}
    table {{ width: 100%; border-collapse: collapse; min-width: 900px; }}
    th {{
        background: #063d12; color: #00ff41; padding: 14px;
        text-align: left; font-size: 12px; border-bottom: 1px solid #00a52a;
    }}
    td {{
        padding: 12px 14px; border-bottom: 1px solid #173b1e;
        color: #d7ffd7; text-align: left;
    }}
    tr:hover {{ background: #08250d; }}
    .pwd {{ font-weight: 700; font-size: 14px; }}
    .footer {{ text-align: center; color: #007b20; margin-top: 20px; font-size: 12px; }}
    .footer span {{ color: #00ff41; }}
</style>
</head>
<body>
<div class="container">
    <h1>📶 WIFI Relatório</h1>
    <div class="subtitle">PERFIS E SENHAS DE REDES WI-FI SALVAS</div>
    <div class="stats">
        <div class="stat-box">
            <div class="number">{total}</div>
            <div class="label">Total de Redes</div>
        </div>
        <div class="stat-box">
            <div class="number" style="color:#00ff41">{com_senha}</div>
            <div class="label">Com Senha</div>
        </div>
        <div class="stat-box">
            <div class="number" style="color:#ff6b6b">{total - com_senha}</div>
            <div class="label">Sem Senha</div>
        </div>
    </div>
    <div class="panel">
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>REDE WI-FI (SSID)</th>
                    <th>🔑 SENHA</th>
                    
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    <div class="footer">
        <p>Relatório gerado por <span>WIFI SCAN SENHA</span></p>
        <p>{datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}</p>
    </div>
</div>
</body>
</html>"""

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(html_content)
            if messagebox.askyesno(
                "Sucesso",
                "Relatório HTML salvo com sucesso.\n\nDeseja abrir no navegador?",
            ):
                webbrowser.open("file://" + os.path.realpath(file_path))
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o HTML:\n\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = WifiViewerApp(root)
    root.mainloop()
