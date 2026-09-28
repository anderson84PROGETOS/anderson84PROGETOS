#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
 FileAnalyzer  -  GUI (estilo robotshell/FileAnalyzer)
=====================================================================
 Varre arquivos/pastas procurando palavras-chave sensiveis.
 - Wordlist EMBUTIDA no codigo (padrao)
 - Permite carregar/salvar uma wordlist .txt do seu PC
 - FIltro ao vivo + busca de um termo unico (so a palavra pesquisada)
 - Reporta: arquivo, palavra, linha e trecho
 - Exporta resultado em .TXT e em .HTML (relatorio profissional)
 - Barra de progresso VERDE de 0 a 100%
 - Scrollbar horizontal para navegar nos resultados
 - ABAS (Notebook): "Wordlist" e "Resultados" (area grande)
 - Janela de AJUDA integrada (botao "Ajuda")
 Requisitos: apenas Python 3 (Tkinter ja vem incluso)
=====================================================================
"""

import os
import re
import html
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox

# ------------------------------------------------------------------
#  WORDLIST EMBUTIDA (padrao)
# ------------------------------------------------------------------
DEFAULT_WORDLIST = [
    "confidential",
    "internal use only",
    "do not distribute",
    "restricted",
    "proprietary",
    "company confidential",
    "for internal use",
    "nda",
    "employee",
    "payroll",
    "invoice",
    "contract",
    "password",
    "api key",
    "secret",
    "token",
    "jira",
    "confluence",
    "slack",
    "vpn",
]

# Extensoes tratadas como texto na varredura de pastas
TEXT_EXT = {
    ".txt", ".log", ".md", ".csv", ".json", ".xml", ".yaml", ".yml",
    ".ini", ".cfg", ".conf", ".env", ".py", ".js", ".ts", ".java",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".rb", ".go", ".rs",
    ".sh", ".bat", ".ps1", ".sql", ".html", ".htm", ".css",
    ".properties", ".htaccess", ".htpasswd", ".pem", ".key", ".bak",
}

# ------------------------------------------------------------------
#  CATEGORIZACAO (usada para colorir os badges no HTML)
# ------------------------------------------------------------------
CATEGORY_MAP = {
    "password": "cred", "api key": "cred", "secret": "cred", "token": "cred",
    "confidential": "conf", "internal use only": "conf", "do not distribute": "conf",
    "restricted": "conf", "proprietary": "conf", "company confidential": "conf",
    "for internal use": "conf",
    "nda": "legal", "contract": "legal", "employee": "legal",
    "payroll": "legal", "invoice": "legal",
    "jira": "sys", "confluence": "sys", "slack": "sys", "vpn": "sys",
}
CATEGORY_LABEL = {
    "cred": "Credencial", "conf": "Confidencial", "legal": "Legal/RH",
    "sys": "Sistemas", "other": "Outro",
}

# ------------------------------------------------------------------
#  TEXTO DA JANELA DE AJUDA
# ------------------------------------------------------------------
HELP_TITLE = "Ajuda - FileAnalyzer"

HELP_TEXT = """\
========================================================
 FileAnalyzer - Keyword Scanner
========================================================

PARA QUE SERVE?
---------------
O FileAnalyzer varre arquivos e pastas procurando PALAVRAS-CHAVE
sensiveis (confidencial, senha, token, API key, NDA, folha de
pagamento, etc.). Ele mostra onde cada termo aparece, em qual
linha e o trecho da linha.

E util para:
  * Pentests e auditorias: achar documentos/secrets expostos.
  * Limpeza de dados: ver se ha informacao confidencial vazando.
  * Verificar repositorios ou backups antes de compartilhar.
  * Confirmar se termos marcados como internos estao fora do
    lugar.


COMO USAR - PASSO A PASSO
-------------------------
1) ESCOLHA O ALVO
   - "Arquivos..."  -> seleciona um ou varios arquivos.
   - "Pasta..."       -> seleciona uma pasta inteira.
   - "Limpar alvos"   -> zera a lista de alvos.
   Os alvos sao acumulados; veja o contador "Alvos: N".

2) AJUSTE A WORDLIST (aba "Wordlist")
   - A lista padrao ja vem embutida no codigo.
   - "Carregar Wordlist (.txt)"  -> importa um arquivo .txt do seu
     PC (uma palavra por linha). O programa pergunta se voce quer
     SUBSTITUIR a lista atual ou ADICIONAR as novas palavras.
   - "Salvar Wordlist (.txt)"    -> grava a lista atual num .txt.
   - "Resetar Wordlist"          -> volta a lista padrao embutida.
   - Campo "Nova palavra" adiciona (aceita varias separadas por ;).
   - Delete remove as palavras selecionadas

3) FILTRO E BUSCA DE UM TERMO SO (area "Opcoes")
   - Campo "Filtro": digite http, href, password, etc. e a tabela
     de resultados mostra SOMENTE as linhas que contem esse texto.
     O filtro age ao vivo, enquanto voce digita, sobre os
     resultados ja exibidos.
   - "Limpar filtro" -> remove o filtro e mostra tudo de novo.
   - "Buscar so este termo": faz uma NOVA varredura usando apenas
     o termo digitado no filtro. Assim os resultados trazem
     somente aquela palavra pesquisada.

4) DEFINA AS OUTRAS OPCOES
   - "Diferenciar maiusculas/minusculas"
   - "Palavra inteira (\\b...\\b)"
   - "Varrer QUALQUER extensao (pastas)"
   - "Tamanho maximo por arquivo (MB)"

5) INICIE A ANALISE
   - Clique em "ANALISAR" (ou Ctrl+A).
   - A barra de progresso VERDE mostra o andamento de 0 a 100%.
   - Ao iniciar, o programa troca automaticamente para a aba
     "Resultados".
   - Clique em "Parar" para interromper a qualquer momento.

6) VEJA OS RESULTADOS (aba "Resultados")
   - A tabela mostra: Arquivo | Palavra | Linha | Trecho.
   - Barra HORIZONTAL (embaixo) move para esquerda/direita.
   - Barra VERTICAL (na direita) sobe/desce.
   - Duplo-clique abre o arquivo correspondente.
   - "Copiar linha selecionada" copia para a area de transferencia.

7) EXPORTE O RELATORIO  (somente TXT e HTML)
   - "Exportar TXT"   -> relatorio em texto puro, alinhado e legivel.
   - "Exportar HTML"  -> relatorio profissional com CSS embutido.
       OBS: se um filtro estiver ativo, exporta apenas o que esta
       sendo exibido na tabela filtrada.


ATALHOS DE TECLADO
------------------
   Ctrl+1  -> aba "Wordlist"
   Ctrl+2  -> aba "Resultados"
   Ctrl+A  -> inicia a analise (ANALISAR)
   F1      -> abre esta Ajuda


DICAS
-----
* Termos como "password", "api key" e "token" costumam gerar
  falsos positivos; ligue "Palavra inteira" para maior precisao.
* Combine com "Diferenciar maiusculas" desligado para pegar
  variacoes como "CONFIDENTIAL" ou "Confidential".
* O filtro tambem procura no TRECHO, entao digitar "href" mostra
  linhas que contem href, mesmo que a palavra-chave seja outra.


REQUISITOS
----------
* Python 3 (o Tkinter ja vem incluso na instalacao padrao).
* Nenhuma biblioteca externa e necessaria.


OBSERVACAO / ETICA
------------------
Use esta ferramenta apenas em arquivos e sistemas que voce tem
autorizacao para analisar. Ela e destinada a testes autorizados,
auditorias internas e limpeza de dados proprios.
"""


# ==================================================================
#  TEMPLATES DO RELATORIO HTML
# ==================================================================
HTML_CSS = """
:root{
  --bg:#f4f6fb; --card:#ffffff; --ink:#1c2333; --muted:#6b7690;
  --line:#e3e8f2; --brand:#2f5bea; --brand2:#1b3fb0;
  --cred:#d92d20; --cred-bg:#fef3f2; --cred-bd:#fecdca;
  --conf:#b54708; --conf-bg:#fffaeb; --conf-bd:#fedf89;
  --legal:#5925dc; --legal-bg:#f4f3ff; --legal-bd:#d9d6fe;
  --sys:#027a48; --sys-bg:#ecfdf3; --sys-bd:#abefc6;
  --other:#475467; --other-bg:#f2f4f7; --other-bd:#d0d5dd;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Segoe UI",Roboto,Helvetica,Arial,sans-serif;font-size:14px}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px}
header{background:linear-gradient(135deg,var(--brand),var(--brand2));
  color:#fff;border-radius:14px;padding:26px 28px;box-shadow:0 6px 20px rgba(47,91,234,.25)}
header h1{margin:0;font-size:22px;letter-spacing:.4px}
header p{margin:6px 0 0;opacity:.88;font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
  gap:14px;margin:20px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:16px 18px;box-shadow:0 1px 2px rgba(16,24,40,.04)}
.card .lbl{color:var(--muted);font-size:12px;text-transform:uppercase;
  letter-spacing:.6px;margin-bottom:8px}
.card .val{font-size:26px;font-weight:700;line-height:1}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;
  overflow:hidden;box-shadow:0 1px 2px rgba(16,24,40,.04)}
.panel .ptop{display:flex;flex-wrap:wrap;gap:12px;align-items:center;
  justify-content:space-between;padding:14px 18px;border-bottom:1px solid var(--line)}
.panel h2{margin:0;font-size:15px;letter-spacing:.3px}
input[type=search]{width:280px;max-width:100%;padding:9px 12px;border:1px solid var(--line);
  border-radius:8px;font-size:13px;outline:none}
input[type=search]:focus{border-color:var(--brand);box-shadow:0 0 0 3px rgba(47,91,234,.12)}
table{width:100%;border-collapse:collapse}
thead th{position:sticky;top:0;background:#f8fafc;border-bottom:1px solid var(--line);
  text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.5px;
  color:var(--muted);padding:11px 14px;cursor:pointer;user-select:none;white-space:nowrap}
thead th:hover{color:var(--brand)}
tbody td{padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:hover{background:#fafbff}
td.file{font-family:Consolas,Menlo,monospace;font-size:12.5px;word-break:break-all}
td.line{text-align:center;color:var(--muted);font-variant-numeric:tabular-nums}
td.snip{font-family:Consolas,Menlo,monospace;font-size:12.5px;color:#384152;word-break:break-word}
mark{background:#fff3b0;color:inherit;border-radius:3px;padding:0 2px}
.badge{display:inline-block;padding:3px 9px;border-radius:999px;font-size:11.5px;
  font-weight:600;white-space:nowrap;border:1px solid transparent}
.b-cred{color:var(--cred);background:var(--cred-bg);border-color:var(--cred-bd)}
.b-conf{color:var(--conf);background:var(--conf-bg);border-color:var(--conf-bd)}
.b-legal{color:var(--legal);background:var(--legal-bg);border-color:var(--legal-bd)}
.b-sys{color:var(--sys);background:var(--sys-bg);border-color:var(--sys-bd)}
.b-other{color:var(--other);background:var(--other-bg);border-color:var(--other-bd)}
.empty{padding:34px;text-align:center;color:var(--muted)}
.legend{display:flex;flex-wrap:wrap;gap:14px;padding:12px 18px;color:var(--muted);font-size:12px}
footer{margin-top:22px;color:var(--muted);font-size:12px;text-align:center}
"""

HTML_JS = """
(function(){
  var q = document.getElementById('q');
  var rows = Array.prototype.slice.call(document.querySelectorAll('#tb tr'));
  q.addEventListener('input', function(){
    var v = this.value.toLowerCase();
    rows.forEach(function(r){
      r.style.display = r.innerText.toLowerCase().indexOf(v) !== -1 ? '' : 'none';
    });
  });
  document.querySelectorAll('#tb th').forEach(function(th, i){
    var asc = true;
    th.addEventListener('click', function(){
      var tb = document.getElementById('tb');
      rows.sort(function(a, b){
        var x = a.children[i].innerText.trim().toLowerCase();
        var y = b.children[i].innerText.trim().toLowerCase();
        if(i === 2){ x = parseInt(x,10)||0; y = parseInt(y,10)||0;
                     return asc ? x-y : y-x; }
        return asc ? x.localeCompare(y) : y.localeCompare(x);
      });
      asc = !asc;
      rows.forEach(function(r){ tb.appendChild(r); });
    });
  });
})();
"""


class FileAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FileAnalyzer Keyword Scanner")
        self.root.geometry("1280x780")
        self.root.minsize(980, 560)

        # Maximizar no Windows/Linux
        try:
            self.root.state("zoomed")
        except Exception:
            try:
                self.root.attributes("-zoomed", True)
            except Exception:
                pass        

        self.keywords = list(DEFAULT_WORDLIST)   # wordlist ativa
        self.targets = []                        # arquivos/pastas escolhidos
        self.results = []                        # TODAS as ocorrencias
        self.visible_results = []                # ocorrencias exibidas (apos filtro)
        self.scanning = False
        self.last_only_term = None               # termo unico da ultima busca

        # metadados para o relatorio
        self.started_at = None
        self.finished_at = None
        self.files_scanned = 0
        self.scan_targets = []
        self.used_options = {}

        self._build_style()
        self._build_ui()
        self._bind_shortcuts()
        self._refresh_keyword_list()
        self._update_targets_label()

    # ==============================================================
    #  ESTILO (barra de progresso verde)
    # ==============================================================
    def _build_style(self):
        try:
            style = ttk.Style()
            if "clam" in style.theme_names():
                style.theme_use("clam")

            style.configure(
                "Green.Horizontal.TProgressbar",
                troughcolor="#e3e8f2",
                background="#12b76a",
                darkcolor="#12b76a",
                lightcolor="#12b76a",
                bordercolor="#d0d5dd",
                thickness=18,
            )
            try:
                style.layout("Green.Horizontal.TProgressbar", [
                    ("Horizontal.Progressbar.trough",
                     {"sticky": "nswe", "children": [
                         ("Horizontal.Progressbar.pbar",
                          {"side": "left", "sticky": "ns"})]}),
                    ("Horizontal.Progressbar.label", {"sticky": ""}),
                ])
            except tk.TclError:
                pass

            style.configure("TNotebook.Tab", padding=(16, 8), font=("Segoe UI", 10))
        except tk.TclError:
            pass

    # ==============================================================
    #  CONSTRUCAO DA INTERFACE
    # ==============================================================
    def _build_ui(self):
        # ---------------- Toolbar superior ----------------
        top = ttk.Frame(self.root, padding=6)
        top.pack(fill="x")

        ttk.Button(top, text="Arquivos...", command=self.select_files).pack(side="left", padx=2)
        ttk.Button(top, text="Pasta...", command=self.select_folder).pack(side="left", padx=2)
        ttk.Button(top, text="Limpar alvos", command=self.clear_targets).pack(side="left", padx=2)
        ttk.Button(top, text="Carregar Wordlist (.txt)", command=self.load_wordlist).pack(side="left", padx=2)
        ttk.Button(top, text="Salvar Wordlist (.txt)", command=self.save_wordlist).pack(side="left", padx=2)

        ttk.Button(top, text="?  Ajuda (F1)", command=self.show_help).pack(side="left", padx=(12, 2))

        ttk.Button(top, text="ANALISAR", command=self.start_scan).pack(side="right", padx=2)
        ttk.Button(top, text="Parar", command=self.stop_scan).pack(side="right", padx=2)

        # ---------------- Opcoes ----------------
        opts = ttk.LabelFrame(self.root, text="Opções", padding=6)
        opts.pack(fill="x", padx=6, pady=(0, 4))

        # ---- linha 1: opcoes de varredura ----
        row1 = ttk.Frame(opts)
        row1.pack(fill="x")

        self.case_var = tk.BooleanVar(value=False)
        self.whole_var = tk.BooleanVar(value=False)
        self.all_ext_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(row1, text="Diferenciar maiúsculas/minúsculas",
                        variable=self.case_var).pack(side="left", padx=6)
        ttk.Checkbutton(row1, text="Palavra inteira (\\b...\\b)",
                        variable=self.whole_var).pack(side="left", padx=6)
        ttk.Checkbutton(row1, text="Varrer QUALQUER extensão (pastas)",
                        variable=self.all_ext_var).pack(side="left", padx=6)

        ttk.Label(row1, text="Tamanho máximo por arquivo (MB):").pack(side="left", padx=(20, 4))
        self.size_var = tk.IntVar(value=20)
        ttk.Spinbox(row1, from_=1, to=2048, width=6,
                    textvariable=self.size_var).pack(side="left")

        self.targets_lbl = ttk.Label(row1, text="", foreground="#0a5")
        self.targets_lbl.pack(side="right", padx=6)

        # ---- linha 2: FILTRO / BUSCA de um termo ----
        row2 = ttk.Frame(opts)
        row2.pack(fill="x", pady=(8, 0))

        ttk.Label(row2, text="Filtro (mostra só o que contém):",
                  font=("Segoe UI", 10, "bold")).pack(side="left", padx=(6, 4))

        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(row2, textvariable=self.filter_var, width=34)
        self.filter_entry.pack(side="left")
        self.filter_var.trace_add("write", lambda *a: self._apply_filter())

        ttk.Button(row2, text="Limpar filtro",
                   command=self._clear_filter).pack(side="left", padx=(6, 0))

        ttk.Button(row2, text="Buscar só este termo",
                   command=self._scan_only_term).pack(side="left", padx=(10, 0))

        ttk.Label(row2, text="ex.: http, href, password, token...",
                  foreground="#6b7690").pack(side="left", padx=10)

        self.filter_info = ttk.Label(row2, text="", foreground="#0a5")
        self.filter_info.pack(side="right", padx=6)

        # ==========================================================
        #  NOTEBOOK (ABAS): "Wordlist" e "Resultados"
        # ==========================================================
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=6, pady=4)

        self.tab_words = ttk.Frame(self.nb, padding=10)
        self.tab_res = ttk.Frame(self.nb, padding=10)
        self.nb.add(self.tab_words, text="   Wordlist   ")
        self.nb.add(self.tab_res, text="   Resultados   ")

        self._build_tab_wordlist()
        self._build_tab_results()

        # ---------------- Rodape ----------------
        bottom = ttk.Frame(self.root, padding=6)
        bottom.pack(fill="x")

        self.progress = ttk.Progressbar(
            bottom, mode="determinate", maximum=100,
            style="Green.Horizontal.TProgressbar", length=200)
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ttk.Button(bottom, text="Exportar HTML",
                   command=self.export_html).pack(side="right", padx=(4, 0))
        ttk.Button(bottom, text="Exportar TXT",
                   command=self.export_txt).pack(side="right", padx=(4, 0))
        self.status = ttk.Label(bottom, text="Pronto. 0%", width=48, anchor="w")
        self.status.pack(side="right", padx=6)

    # --------------------------------------------------------------
    #  ABA 1 - WORDLIST
    # --------------------------------------------------------------
    def _build_tab_wordlist(self):
        f = self.tab_words
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)

        holder = ttk.Frame(f)
        holder.grid(row=0, column=0, sticky="nsew")
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)

        self.kw_list = tk.Listbox(
            holder, activestyle="dotbox", selectmode="extended",
            font=("Consolas", 11), height=14)
        vsb = ttk.Scrollbar(holder, orient="vertical", command=self.kw_list.yview)
        hsb = ttk.Scrollbar(holder, orient="horizontal", command=self.kw_list.xview)
        self.kw_list.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.kw_list.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.kw_list.bind("<Delete>", lambda e: self.remove_keyword())

        addf = ttk.Frame(f)
        addf.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        addf.columnconfigure(0, weight=1)

        ttk.Label(addf, text="Nova palavra (use ; para várias):").grid(row=0, column=0, sticky="w")
        self.kw_entry = ttk.Entry(addf)
        self.kw_entry.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        self.kw_entry.bind("<Return>", lambda e: self.add_keyword())

        ttk.Button(addf, text="+  Adicionar", width=14,
                   command=self.add_keyword).grid(row=1, column=1, padx=(6, 0), pady=(3, 0))
        ttk.Button(addf, text="-  Remover", width=14,
                   command=self.remove_keyword).grid(row=1, column=2, padx=(6, 0), pady=(3, 0))

        wf = ttk.Frame(f)
        wf.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(wf, text="Carregar Wordlist (.txt)",
                   command=self.load_wordlist).pack(side="left", padx=(0, 6))
        ttk.Button(wf, text="Salvar Wordlist (.txt)",
                   command=self.save_wordlist).pack(side="left", padx=(0, 6))
        ttk.Button(wf, text="Resetar Wordlist",
                   command=self.reset_wordlist).pack(side="left", padx=(0, 6))
        ttk.Button(wf, text="Selecionar tudo",
                   command=self._select_all_keywords).pack(side="left")

        self.kw_count = ttk.Label(f, text="", foreground="#0a5",
                                  font=("Segoe UI", 10, "bold"))
        self.kw_count.grid(row=3, column=0, sticky="w", pady=(10, 0))

        ttk.Label(
            f, foreground="#6b7690", justify="left",
            text=("Dica: uma palavra por linha. Linhas começando com '#' são "
                  "ignoradas ao carregar um .txt.\n"
                  "Delete remove as palavras selecionadas")
        ).grid(row=4, column=0, sticky="w", pady=(4, 0))

    # --------------------------------------------------------------
    #  ABA 2 - RESULTADOS (area grande)
    # --------------------------------------------------------------
    def _build_tab_results(self):
        f = self.tab_res
        f.rowconfigure(1, weight=1)
        f.columnconfigure(0, weight=1)

        head = ttk.Frame(f)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(head, text="Resultados da varredura",
                  font=("Segoe UI", 11, "bold")).pack(side="left")
        self.res_summary = ttk.Label(head, text="Nenhuma ocorrência ainda.",
                                     foreground="#6b7690")
        self.res_summary.pack(side="right")

        cols = ("file", "keyword", "line", "snippet")
        self.tree = ttk.Treeview(f, columns=cols, show="headings", height=18)
        self.tree.heading("file", text="Arquivo", anchor="w")
        self.tree.heading("keyword", text="Palavra", anchor="w")
        self.tree.heading("line", text="Linha", anchor="w")
        self.tree.heading("snippet", text="Trecho", anchor="w")

        self.tree.column("file", width=500, anchor="w")
        self.tree.column("keyword", width=300, anchor="w")
        self.tree.column("line", width=70, anchor="center")
        self.tree.column("snippet", width=3000, anchor="w")

        vsb = ttk.Scrollbar(f, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(f, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")

        self.tree.bind("<Double-1>", self._open_result_file)

        tagbar = ttk.Frame(f)
        tagbar.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(tagbar,
                  text=("Duplo-clique abre o arquivo. Use a barra horizontal "
                        "para ver o Trecho completo."),
                  foreground="#6b7690").pack(side="left")
        ttk.Button(tagbar, text="Copiar linha selecionada",
                   command=self._copy_selected).pack(side="right")

    # --------------------------------------------------------------
    #  Atalhos de teclado
    # --------------------------------------------------------------
    def _bind_shortcuts(self):
        self.root.bind("<Control-Key-1>", lambda e: self.nb.select(self.tab_words))
        self.root.bind("<Control-Key-2>", lambda e: self.nb.select(self.tab_res))
        self.root.bind("<Control-Key-a>", lambda e: self.start_scan())
        self.root.bind("<Control-Key-f>", lambda e: self.filter_entry.focus_set())
        self.root.bind("<F1>", lambda e: self.show_help())

    # ==============================================================
    #  FILTRO AO VIVO
    # ==============================================================
    def _match_filter(self, hit):
        """True se a ocorrencia (arquivo/palavra/trecho) casa com o filtro."""
        term = self.filter_var.get().strip().lower()
        if not term:
            return True
        fpath, kw, lineno, snippet = hit
        hay = "%s %s %s %s" % (fpath, kw, lineno, snippet)
        return term in hay.lower()

    def _apply_filter(self):
        """Repinta a tabela mostrando apenas as linhas que casam com o filtro."""
        term = self.filter_var.get().strip()
        self.tree.delete(*self.tree.get_children())

        self.visible_results = []
        for hit in self.results:
            if self._match_filter(hit):
                self.visible_results.append(hit)
                self.tree.insert("", "end", values=hit)

        if term:
            self.filter_info.config(
                text="Filtro: '%s' -> %d de %d" % (term, len(self.visible_results),
                                                    len(self.results)))
            self.res_summary.config(
                text="%d ocorrências exibidas (filtro ativo)" % len(self.visible_results))
        else:
            self.filter_info.config(text="")
            self.res_summary.config(
                text="%d ocorrências encontradas" % len(self.results))

    def _clear_filter(self):
        self.filter_var.set("")          # o trace ja chama _apply_filter()
        self.status.config(text="Filtro limpo.")

    def _scan_only_term(self):
        """Nova varredura usando SOMENTE o termo digitado no filtro."""
        term = self.filter_var.get().strip()
        if not term:
            messagebox.showwarning(
                "Buscar só este termo",
                "Digite um termo no campo de filtro (ex.: http, href, password).")
            self.filter_entry.focus_set()
            return
        self.start_scan(only_term=term)

    # ==============================================================
    #  JANELA DE AJUDA
    # ==============================================================
    def show_help(self):
        """Abre a janela de ajuda com instrucoes de uso."""
        help_win = tk.Toplevel(self.root)
        help_win.title(HELP_TITLE)
        help_win.geometry("800x660")
        help_win.minsize(560, 420)
        help_win.transient(self.root)

        frame = ttk.Frame(help_win, padding=8)
        frame.pack(fill="both", expand=True)

        txt = tk.Text(frame, wrap="word", font=("Consolas", 10),
                      background="#1e1e1e", foreground="#e6e6e6",
                      insertbackground="#e6e6e6", relief="flat")
        sb = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)

        txt.insert("1.0", HELP_TEXT)
        txt.config(state="disabled")

        bar = ttk.Frame(help_win, padding=(8, 4))
        bar.pack(fill="x")

        def export_help():
            path = filedialog.asksaveasfilename(
                title="Salvar ajuda como...",
                defaultextension=".txt",
                initialfile="FileAnalyzer_Ajuda.txt",
                filetypes=[("Texto", "*.txt")])
            if not path:
                return
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(HELP_TEXT)
                messagebox.showinfo("Ajuda", "Ajuda salva em:\n%s" % path)
            except OSError as e:
                messagebox.showerror("Erro", "Falha ao salvar:\n%s" % e)

        ttk.Button(bar, text="Salvar ajuda (.txt)",
                   command=export_help).pack(side="left")
        ttk.Button(bar, text="Fechar",
                   command=help_win.destroy).pack(side="right")

        help_win.bind("<Escape>", lambda e: help_win.destroy())
        help_win.focus_set()

    # ==============================================================
    #  WORDLIST
    # ==============================================================
    def _refresh_keyword_list(self):
        self.kw_list.delete(0, tk.END)
        for kw in self.keywords:
            self.kw_list.insert(tk.END, kw)
        self.kw_count.config(
            text="Total: %d palavras na wordlist" % len(self.keywords))

    def _select_all_keywords(self):
        self.kw_list.selection_set(0, tk.END)

    def add_keyword(self):
        kw = self.kw_entry.get().strip()
        if not kw:
            return
        novos = [p.strip() for p in kw.split(";") if p.strip()]
        added = 0
        for w in novos:
            if w not in self.keywords:
                self.keywords.append(w)
                self.kw_list.insert(tk.END, w)
                added += 1
        if added:
            self.kw_entry.delete(0, tk.END)
            self.kw_count.config(
                text="Total: %d palavras na wordlist" % len(self.keywords))
            self.kw_list.see(tk.END)
            self.status.config(text="%d palavras adicionadas" % added)

    def remove_keyword(self):
        sel = list(self.kw_list.curselection())
        if not sel:
            return
        for idx in sorted(sel, reverse=True):
            self.kw_list.delete(idx)
            del self.keywords[idx]
        self.kw_count.config(
            text="Total: %d palavras na wordlist" % len(self.keywords))
        self.status.config(text="%d palavras removidas" % len(sel))

    def reset_wordlist(self):
        self.keywords = list(DEFAULT_WORDLIST)
        self._refresh_keyword_list()
        self.status.config(text="Wordlist restaurada para o padrão.")

    def load_wordlist(self):
        path = filedialog.askopenfilename(
            title="Selecione a wordlist (.txt)",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                words = [ln.strip() for ln in f
                         if ln.strip() and not ln.startswith("#")]
        except OSError as e:
            messagebox.showerror("Erro", "Não foi possível ler o arquivo:\n%s" % e)
            return

        replace = messagebox.askyesno(
            "Wordlist",
            "Substituir a lista atual?\n\nSim = substituir\nNão = adicionar as novas")
        if replace:
            self.keywords = []
        for w in words:
            if w not in self.keywords:
                self.keywords.append(w)
        self._refresh_keyword_list()
        self.status.config(
            text="Wordlist carregada: %d palavras" % len(self.keywords))
        self.nb.select(self.tab_words)

    def save_wordlist(self):
        path = filedialog.asksaveasfilename(
            title="Salvar wordlist como...",
            defaultextension=".txt",
            initialfile="keywords.txt",
            filetypes=[("Texto", "*.txt")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.keywords) + "\n")
            self.status.config(text="Wordlist salva em %s" % os.path.basename(path))
        except OSError as e:
            messagebox.showerror("Erro", "Não foi possível salvar:\n%s" % e)

    # ==============================================================
    #  SELECAO DE ALVOS
    # ==============================================================
    def select_files(self):
        paths = filedialog.askopenfilenames(title="Selecione arquivos")
        if paths:
            self.targets.extend(paths)
            self._update_targets_label()

    def select_folder(self):
        path = filedialog.askdirectory(title="Selecione uma pasta")
        if path:
            self.targets.append(path)
            self._update_targets_label()

    def clear_targets(self):
        self.targets = []
        self._update_targets_label()
        self.status.config(text="Lista de alvos limpa.")

    def _update_targets_label(self):
        self.targets_lbl.config(text="Alvos: %d" % len(self.targets))

    def _collect_files(self):
        out = []
        use_all = self.all_ext_var.get()
        for t in self.targets:
            if os.path.isfile(t):
                out.append(t)
            elif os.path.isdir(t):
                for root_dir, _dirs, files in os.walk(t):
                    for name in files:
                        ext = os.path.splitext(name)[1].lower()
                        if use_all or ext in TEXT_EXT:
                            out.append(os.path.join(root_dir, name))
        return out

    # ==============================================================
    #  VARREDURA
    # ==============================================================
    def start_scan(self, only_term=None):
        if self.scanning:
            return
        if not self.targets:
            messagebox.showwarning("Aviso", "Selecione ao menos um arquivo ou pasta.")
            return

        # define a lista de palavras que sera usada na varredura
        if only_term:
            scan_words = [only_term]
        else:
            scan_words = list(self.keywords)
        if not scan_words:
            messagebox.showwarning("Aviso", "A wordlist está vazia.")
            return

        files = self._collect_files()
        if not files:
            messagebox.showinfo("Info", "Nenhum arquivo válido encontrado.")
            return

        self.results = []
        self.visible_results = []
        self.tree.delete(*self.tree.get_children())
        self.scanning = True
        self.last_only_term = only_term

        self.nb.select(self.tab_res)

        self.progress.config(value=0, maximum=100)
        if only_term:
            self.status.config(
                text="Analisando %d arquivos só por '%s'... 0%%" % (len(files), only_term))
        else:
            self.status.config(text="Analisando %d arquivos... 0%%" % len(files))

        self.started_at = datetime.now()
        self.finished_at = None
        self.files_scanned = len(files)
        self.scan_targets = list(self.targets)
        self.used_options = {
            "case_sensitive": self.case_var.get(),
            "whole_word": self.whole_var.get(),
            "all_ext": self.all_ext_var.get(),
            "max_mb": self.size_var.get(),
            "only_term": only_term,
        }

        threading.Thread(
            target=self._scan_worker,
            args=(files, scan_words, self.case_var.get(),
                  self.whole_var.get(), self.size_var.get()),
            daemon=True,
        ).start()

    def stop_scan(self):
        if self.scanning:
            self.scanning = False
            self.status.config(text="Interrompido pelo usuário.")

    def _scan_worker(self, files, scan_words, case_sensitive, whole_word, max_mb):
        flags = 0 if case_sensitive else re.IGNORECASE
        patterns = []
        for kw in scan_words:
            pat = r"\b%s\b" % re.escape(kw) if whole_word else re.escape(kw)
            try:
                patterns.append((kw, re.compile(pat, flags)))
            except re.error:
                continue

        total = len(files)
        for idx, path in enumerate(files, 1):
            if not self.scanning:
                break
            self._scan_one(path, patterns, max_mb)
            pct = int(idx * 100 / total) if total else 100
            self.root.after(0, self._set_progress, pct, idx, total)

        self.root.after(0, self._scan_finished)

    def _scan_one(self, path, patterns, max_mb):
        try:
            if os.path.getsize(path) > max_mb * 1024 * 1024:
                return
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for lineno, line in enumerate(f, 1):
                    for kw, pat in patterns:
                        if pat.search(line):
                            snippet = line.strip()
                            if len(snippet) > 300:
                                snippet = snippet[:300] + "..."
                            self.root.after(0, self._add_result,
                                            (path, kw, lineno, snippet))
        except (OSError, PermissionError):
            pass

    def _add_result(self, hit):
        self.results.append(hit)
        # so insere na tabela se casar com o filtro atual
        if self._match_filter(hit):
            self.visible_results.append(hit)
            self.tree.insert("", "end", values=hit)
        # atualiza contadores
        term = self.filter_var.get().strip()
        if term:
            self.res_summary.config(
                text="%d exibidas de %d (filtro ativo)" % (
                    len(self.visible_results), len(self.results)))
        else:
            self.res_summary.config(
                text="%d ocorrências encontradas" % len(self.results))

    def _set_progress(self, pct, done, total):
        self.progress.config(value=pct)
        self.status.config(text="Analisando... %d/%d  (%d%%)" % (done, total, pct))

    def _scan_finished(self):
        self.scanning = False
        self.finished_at = datetime.now()
        self.progress.config(value=100)
        term = self.filter_var.get().strip()
        if term:
            self.status.config(
                text="Concluído: %d exibidas de %d  (100%%)" % (
                    len(self.visible_results), len(self.results)))
        else:
            self.status.config(
                text="Concluído: %d ocorrências  (100%%)" % len(self.results))
        self._apply_filter()   # garante consistencia final

    # ==============================================================
    #  UTILITARIOS
    # ==============================================================
    def _copy_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        texto = "Arquivo: %s | Palavra: %s | Linha: %s | Trecho: %s" % tuple(vals)
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        self.status.config(text="Linha copiada para a área de transferência.")

    def _open_result_file(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        path = self.tree.item(sel[0], "values")[0]
        try:
            if os.name == "nt":
                os.startfile(path)
            elif os.uname().sysname == "Darwin":
                os.system('open "%s"' % path)
            else:
                os.system('xdg-open "%s"' % path)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # ---- estatisticas (respeitam o filtro ativo) ----
    def _stats(self, data=None):
        data = data if data is not None else self.visible_results
        files_hit = sorted({r[0] for r in data})
        words_hit = sorted({r[1] for r in data})
        by_word = {}
        for _f, kw, _l, _s in data:
            by_word[kw] = by_word.get(kw, 0) + 1
        return files_hit, words_hit, by_word

    def _check_results(self):
        if not self.visible_results:
            messagebox.showinfo(
                "Info", "Nada para exportar. Faça uma análise (ou limpe o filtro).")
            return False
        return True

    # ==============================================================
    #  EXPORTACAO - TXT
    # ==============================================================
    def export_txt(self):
        if not self._check_results():
            return
        path = filedialog.asksaveasfilename(
            title="Exportar relatório em TXT",
            defaultextension=".txt",
            initialfile="fileanalyzer_report.txt",
            filetypes=[("Texto", "*.txt")])
        if not path:
            return

        data = list(self.visible_results)     # exporta o que esta visivel
        files_hit, words_hit, by_word = self._stats(data)
        W = 79
        sep = "=" * W
        sub = "-" * W
        opt = self.used_options
        gen = (self.finished_at or datetime.now()).strftime("%d/%m/%Y %H:%M:%S")

        L = []
        L.append(sep)
        L.append("FILEANALYZER - RELATORIO DE VARREDURA".center(W))
        L.append(sep)
        L.append("Gerado em        : {0}".format(gen))
        if self.started_at:
            L.append("Inicio da analise: {0}".format(
                self.started_at.strftime("%d/%m/%Y %H:%M:%S")))
        if self.finished_at and self.started_at:
            L.append("Duracao          : {0:.2f} s".format(
                (self.finished_at - self.started_at).total_seconds()))
        L.append("")
        L.append("RESUMO")
        L.append(sub)
        L.append("Arquivos analisados  : {0}".format(self.files_scanned))
        L.append("Arquivos com achados : {0}".format(len(files_hit)))
        L.append("Ocorrencias totais   : {0}".format(len(data)))
        L.append("Palavras encontradas : {0}".format(len(words_hit)))
        L.append("Palavras na wordlist : {0}".format(len(self.keywords)))
        if self.last_only_term:
            L.append("Busca por termo unico: {0}".format(self.last_only_term))
        filtro = self.filter_var.get().strip()
        if filtro:
            L.append("Filtro aplicado      : {0}".format(filtro))
        L.append("")
        L.append("OPCOES DA VARREDURA")
        L.append(sub)
        L.append("Diferenciar maius/minus : {0}".format(
            "Sim" if opt.get("case_sensitive") else "Nao"))
        L.append("Palavra inteira         : {0}".format(
            "Sim" if opt.get("whole_word") else "Nao"))
        L.append("Varrer qualquer extensao: {0}".format(
            "Sim" if opt.get("all_ext") else "Nao"))
        L.append("Tamanho maximo (MB)     : {0}".format(opt.get("max_mb", "-")))
        L.append("")
        L.append("ALVOS")
        L.append(sub)
        for t in self.scan_targets:
            L.append("  - {0}".format(t))
        L.append("")
        L.append("CONTAGEM POR PALAVRA")
        L.append(sub)
        for k in sorted(by_word, key=lambda x: (-by_word[x], x)):
            label = k if len(k) <= 26 else (k[:23] + "...")
            L.append("  {0:<26} {1}".format(label, by_word[k]))

        L.append("")
        L.append(sep)
        L.append("OCORRENCIAS DETALHADAS ({0})".format(len(data)))
        L.append(sep)

        for i, (fpath, kw, lineno, snippet) in enumerate(data, 1):
            L.append("")
            L.append("[{0:04d}] {1}".format(i, fpath))
            L.append("       Palavra : {0}".format(kw))
            L.append("       Linha   : {0}".format(lineno))
            L.append("       Trecho  : {0}".format(snippet))

        L.append("")
        L.append(sep)
        L.append("Fim do relatorio - FileAnalyzer".center(W))
        L.append(sep)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(L) + "\n")
            self.status.config(text="TXT exportado: {0}".format(os.path.basename(path)))
            messagebox.showinfo("Exportar TXT", "Relatório salvo em:\n{0}".format(path))
        except OSError as e:
            messagebox.showerror("Erro", "Falha ao salvar TXT:\n{0}".format(e))

    # ==============================================================
    #  EXPORTACAO - HTML
    # ==============================================================
    def _build_html(self):
        data = list(self.visible_results)     # exporta o que esta visivel
        files_hit, words_hit, by_word = self._stats(data)
        opt = self.used_options
        gen = (self.finished_at or datetime.now()).strftime("%d/%m/%Y %H:%M:%S")
        dur = ""
        if self.started_at and self.finished_at:
            dur = "{0:.2f} s".format(
                (self.finished_at - self.started_at).total_seconds())

        rows = []
        for fpath, kw, lineno, snippet in data:
            cat = CATEGORY_MAP.get(kw.lower(), "other")
            label = CATEGORY_LABEL.get(cat, "Outro")
            safe_snip = html.escape(snippet)
            try:
                rx = re.compile(re.escape(kw), re.IGNORECASE)
                safe_snip = rx.sub(
                    lambda m: "<mark>{0}</mark>".format(html.escape(m.group(0))),
                    snippet)
            except re.error:
                pass
            rows.append(
                "<tr>"
                "<td class=\"file\">{0}</td>"
                "<td><span class=\"badge b-{1}\">{2}</span></td>"
                "<td class=\"line\">{3}</td>"
                "<td class=\"snip\">{4}</td>"
                "</tr>".format(html.escape(fpath), cat, html.escape(label),
                               lineno, safe_snip))

        if rows:
            tbody = "\n".join(rows)
        else:
            tbody = ('<tr><td colspan="4" class="empty">'
                     'Nenhuma ocorrência encontrada.</td></tr>')

        legend = "".join(
            "<span class=\"badge b-{0}\">{1}</span>".format(c, CATEGORY_LABEL[c])
            for c in ("cred", "conf", "legal", "sys", "other")
        )

        words_tbl = "".join(
            "<span class=\"badge b-{0}\">{1} &nbsp;{2}</span> ".format(
                CATEGORY_MAP.get(kw.lower(), "other"), html.escape(kw), by_word[kw])
            for kw in sorted(by_word, key=lambda k: (-by_word[k], k))
        )

        targets_list = "".join(
            "<li>{0}</li>".format(html.escape(t)) for t in self.scan_targets
        ) or "<li>-</li>"

        opts_line = (
            "Diferenciar maiúsculas: <b>{0}</b> &nbsp;|&nbsp; "
            "Palavra inteira: <b>{1}</b> &nbsp;|&nbsp; "
            "Qualquer extensão: <b>{2}</b> &nbsp;|&nbsp; "
            "Tamanho máximo: <b>{3} MB</b>".format(
                "Sim" if opt.get("case_sensitive") else "Não",
                "Sim" if opt.get("whole_word") else "Não",
                "Sim" if opt.get("all_ext") else "Não",
                opt.get("max_mb", "-"),
            )
        )

        # linha com termo unico / filtro aplicado
        extra = []
        if self.last_only_term:
            extra.append("Busca por termo único: <b>{0}</b>".format(
                html.escape(self.last_only_term)))
        filtro = self.filter_var.get().strip()
        if filtro:
            extra.append("Filtro aplicado: <b>{0}</b>".format(html.escape(filtro)))
        extra_line = ("<p style=\"margin:0 0 10px;color:#6b7690\">"
                      + " &nbsp;|&nbsp; ".join(extra) + "</p>") if extra else ""

        dur_html = (" &nbsp;|&nbsp; Duração: " + dur) if dur else ""

        body = (
            '<div class="wrap">'
            '<header>'
            '<h1>FileAnalyzer &mdash; Relat&oacute;rio de Varredura</h1>'
            '<p>An&aacute;lise de palavras-chave sens&iacute;veis em arquivos e pastas</p>'
            '<p>Gerado em ' + html.escape(gen) + dur_html + '</p>'
            '</header>'

            '<div class="cards">'
            '<div class="card"><div class="lbl">Ocorr&ecirc;ncias</div>'
            '<div class="val">' + str(len(data)) + '</div></div>'
            '<div class="card"><div class="lbl">Arquivos analisados</div>'
            '<div class="val">' + str(self.files_scanned) + '</div></div>'
            '<div class="card"><div class="lbl">Arquivos com achados</div>'
            '<div class="val">' + str(len(files_hit)) + '</div></div>'
            '<div class="card"><div class="lbl">Palavras encontradas</div>'
            '<div class="val">' + str(len(words_hit)) + '</div></div>'
            '</div>'

            '<div class="panel" style="margin-bottom:18px">'
            '<div class="ptop"><h2>Resumo</h2></div>'
            '<div style="padding:16px 18px">'
            '<p style="margin:0 0 10px;color:#6b7690">' + opts_line + '</p>'
            + extra_line +
            '<p style="margin:0 0 6px"><b>Ocorr&ecirc;ncias por palavra:</b></p>'
            '<div>' + (words_tbl or "&mdash;") + '</div>'
            '<p style="margin:14px 0 6px"><b>Alvos analisados:</b></p>'
            '<ul style="margin:0;padding-left:20px;color:#384152;font-size:13px">'
            + targets_list + '</ul>'
            '</div>'
            '</div>'

            '<div class="panel">'
            '<div class="ptop">'
            '<h2>Ocorr&ecirc;ncias detalhadas</h2>'
            '<input id="q" type="search" placeholder="Filtrar por arquivo, palavra ou trecho...">'
            '</div>'
            '<table>'
            '<thead><tr><th>Arquivo</th><th>Palavra</th><th>Linha</th><th>Trecho</th></tr></thead>'
            '<tbody id="tb">\n' + tbody + '\n</tbody>'
            '</table>'
            '<div class="legend">Categorias: ' + legend + '</div>'
            '</div>'

            '<footer>Relat&oacute;rio gerado automaticamente pelo FileAnalyzer '
            '&mdash; use apenas em sistemas autorizados.</footer>'
            '</div>'
        )

        doc = (
            '<!DOCTYPE html>\n'
            '<html lang="pt-BR">\n'
            '<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>FileAnalyzer - Relat&oacute;rio de Varredura</title>\n'
            '<style>' + HTML_CSS + '</style>\n'
            '</head>\n'
            '<body>\n' + body + '\n'
            '<script>' + HTML_JS + '</script>\n'
            '</body>\n'
            '</html>'
        )
        return doc

    def export_html(self):
        if not self._check_results():
            return
        path = filedialog.asksaveasfilename(
            title="Exportar relatório em HTML",
            defaultextension=".html",
            initialfile="fileanalyzer_report.html",
            filetypes=[("HTML", "*.html"), ("Todos", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._build_html())
            self.status.config(text="HTML exportado: {0}".format(os.path.basename(path)))
            if messagebox.askyesno("Exportar HTML",
                                   "Relatório salvo em:\n{0}\n\nAbrir no navegador?".format(path)):
                if os.name == "nt":
                    os.startfile(path)
                elif os.uname().sysname == "Darwin":
                    os.system('open "%s"' % path)
                else:
                    os.system('xdg-open "%s"' % path)
        except OSError as e:
            messagebox.showerror("Erro", "Falha ao salvar HTML:\n{0}".format(e))


def main():
    root = tk.Tk()
    FileAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
