import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import webbrowser
import subprocess
from deep_translator import GoogleTranslator


class CVEInfoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Consultar vulnerabilidades CVE")
        self.root.geometry("900x700")
        self.root.wm_state("zoomed")
        self.root.resizable(True, True)

        # Título
        titulo = tk.Label(
            root,
            text="Consultar vulnerabilidades CVE",
            font=("Arial", 20, "bold")
        )
        titulo.pack(pady=10)

        # Frame superior
        frame_top = tk.Frame(root)
        frame_top.pack(padx=10)

        tk.Label(
            frame_top,
            text="Digite a CVE (ex: 2006-3530):",
            font=("Arial", 11)
        ).pack(side="left")

        self.cve_entry = tk.Entry(frame_top, width=30, font=("Arial", 11))
        self.cve_entry.pack(side="left", padx=10)

        style = ttk.Style()

        style.configure(
            "Green.TButton",
            foreground="green"
        )

        consultar_btn = ttk.Button(
            frame_top,
            text="Consultar",
            command=self.buscar_cve,
            style="Green.TButton"
        )

        consultar_btn.pack(side="left")

        # Botão Salvar TXT    
        style = ttk.Style()

        style.configure(
            "Red.TButton",
            foreground="red"
        )

        salvar_btn = ttk.Button(
            frame_top,
            text="💾 Salvar em .txt",
            command=self.salvar_txt,
            style="Red.TButton"
        )

        salvar_btn.pack(side="left", padx=10)

        # Área de texto com scrollbar
        frame_texto = tk.Frame(root)
        frame_texto.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame_texto)
        self.texto = tk.Text(
            frame_texto,
            wrap="word",
            yscrollcommand=scrollbar.set,
            font=("Consolas", 10)
        )
        scrollbar.config(command=self.texto.yview)
        scrollbar.pack(side="right", fill="y")
        self.texto.pack(side="left", fill="both", expand=True)

        # Tags de formatação
        self.texto.tag_config("titulo", font=("Arial", 12, "bold"))
        self.texto.tag_config("verde", foreground="green")
        self.texto.tag_config("vermelho", foreground="red")
        self.texto.tag_config("azul", foreground="blue")
        self.texto.tag_config("laranja", foreground="orange")
        self.texto.tag_config("roxo", foreground="purple")
        self.texto.tag_config("link", foreground="blue", underline=True)

    def limpar_texto(self):
        self.texto.delete("1.0", tk.END)

    def inserir(self, texto, tag=None):
        if tag:
            self.texto.insert(tk.END, texto, tag)
        else:
            self.texto.insert(tk.END, texto)

    def abrir_link(self, url):
        """Abre o link no Google Chrome em modo anônimo (Incognito)"""
        try:
            # Tenta abrir no Chrome em modo anônimo
            subprocess.Popen(['google-chrome', '--incognito', url])
        except FileNotFoundError:
            try:
                # Alternativa para Windows
                subprocess.Popen(['start', 'chrome', '--incognito', url], shell=True)
            except:
                # Fallback para webbrowser padrão
                webbrowser.open_new(url)

    def salvar_txt(self):
        """Salva o conteúdo da área de texto em um arquivo .txt"""
        if not self.texto.get("1.0", tk.END).strip():
            messagebox.showwarning("Aviso", "Não há conteúdo para salvar.")
            return

        arquivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")],
            title="Salvar relatório CVE"
        )
        if arquivo:
            try:
                with open(arquivo, "w", encoding="utf-8") as f:
                    conteudo = self.texto.get("1.0", tk.END)
                    f.write(conteudo)
                messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso:\n{arquivo}")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{e}")

    def buscar_cve(self):
        self.limpar_texto()

        cve = self.cve_entry.get().strip().upper()

        if not cve:
            messagebox.showwarning("Aviso", "Digite uma CVE.")
            return

        if not cve.startswith("CVE-"):
            cve_api = f"CVE-{cve}"
        else:
            cve_api = cve

        url = f"https://cvedb.shodan.io/cve/{cve_api}"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            response = requests.get(url, headers=headers, timeout=15)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na conexão:\n{e}")
            return

        if response.status_code != 200:
            messagebox.showerror(
                "Erro",
                f"CVE não encontrada.\nStatus: {response.status_code}"
            )
            return

        try:
            data = response.json()
        except Exception:
            messagebox.showerror(
                "Erro",
                "Não foi possível interpretar a resposta."
            )
            return

        # ==================================================
        # Título
        # ==================================================

        self.inserir(f"Informações para: {cve_api}\n\n", "titulo")

        # ==================================================
        # Descrição original
        # ==================================================

        descricao = data.get("summary", "Descrição não disponível.")

        self.inserir(
            "Descrição Original (Inglês)\n",
            "titulo"
        )

        self.inserir(descricao + "\n\n")

        # ==================================================
        # Tradução
        # ==================================================

        try:
            descricao_pt = GoogleTranslator(
                source="auto",
                target="pt"
            ).translate(descricao)

        except Exception:
            descricao_pt = "Erro na tradução automática."

        self.inserir(
            "Descrição Traduzida (Português-BR)\n",
            "titulo"
        )

        self.inserir(
            descricao_pt + "\n\n",
            "verde"
        )

        # ==================================================
        # CVSS
        # ==================================================

        cvss = data.get("cvss", "Não disponível")

        self.inserir(
            f"Pontuação CVSS: {cvss}\n\n", "titulo")

        # ==================================================
        # Severidade
        # ==================================================

        try:
            score = float(cvss)

            if score == 0:
                nivel = "🔵 Sem impacto"
                tag = None

            elif score <= 3.9:
                nivel = "🔵 Baixo"
                tag = "azul"

            elif score <= 6.9:
                nivel = "🟠 Médio"
                tag = "laranja"

            elif score <= 8.9:
                nivel = "🔴 Alto"
                tag = "vermelho"

            else:
                nivel = "🟣 Crítico"
                tag = "roxo"

            self.inserir(
                f"Severidade: {nivel}\n\n", tag)

        except Exception:
            self.inserir(
                "Severidade: Indefinida\n\n", "vermelho")

        # ==================================================
        # Referências Externas
        # ==================================================

        referencias = sorted(
            set(data.get("references", []))
        )

        self.inserir("Referências Externas\n\n", "titulo")

        def open_in_browser(url):
            try:
                # Windows - Chrome anônimo
                subprocess.Popen(
                    ["cmd", "/c", "start", "chrome", "--incognito", url],
                    shell=True
                )

            except Exception:
                try:
                    webbrowser.open_new_tab(url)

                except Exception as e:
                    messagebox.showerror(
                        "Erro",
                        f"Não foi possível abrir o navegador.\n{e}"
                    )

        if referencias:

            for i, ref in enumerate(referencias, start=1):

                # Exibe o link
                self.inserir(f"{i}. {ref}\n", "link")

                # Botão correspondente ao link
                btn = tk.Button(self.texto, text="Abrir no Chrome", cursor="hand2", command=lambda r=ref: open_in_browser(r))

                self.texto.window_create(tk.END, window=btn)

                self.inserir("\n\n")

        else:
            self.inserir(
                "Nenhuma referência encontrada.\n", "vermelho")

if __name__ == "__main__":
    root = tk.Tk()
    app = CVEInfoGUI(root)
    root.mainloop()
