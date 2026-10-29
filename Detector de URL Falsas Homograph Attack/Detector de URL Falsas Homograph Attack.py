#!/usr/bin/env python3
"""
Detector de URL Falsas (IDN Homograph Attack) com Exportação em HTML
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import unicodedata
from datetime import datetime

# ── Mapeamento dos homoglyphs mais comuns ──────────────────────────
HOMOGLYPHS = {
    1072: ("а", "a", 97),    # cirílico а  → latino a
    1077: ("е", "e", 101),   # cirílico е  → latino e
    1086: ("о", "o", 111),   # cirílico о  → latino o
    1088: ("р", "p", 112),   # cirílico р  → latino p
    1089: ("с", "c",  99),   # cirílico с  → latino c
    1091: ("у", "y", 121),   # cirílico у  → latino y
    1093: ("х", "x", 120),   # cirílico х  → latino x
    1110: ("і", "i", 105),   # cirílico і  → latino i
    1112: ("ј", "j", 106),   # cirílico ј  → latino j
    1109: ("ѕ", "s", 115),   # cirílico ѕ  → latino s
    1111: ("ї", "ï", 239),   # cirílico ї  → latino ï
    1076: ("д", "d", 100),   # cirílico д  → (parecido)
    1075: ("г", "r", 114),   # cirílico г  → (parecido)
    1084: ("м", "m", 109),   # cirílico м  → (parecido)
    1090: ("т", "t", 116),   # cirílico т  → (parecido)
    1085: ("н", "h", 104),   # cirílico н  → (parecido)
    1082: ("к", "k", 107),   # cirílico к  → (parecido)
}

# ── Cores do tema escuro da Interface ─────────────────────────────
BG_DARK   = "#0f0f1a"
BG_PANEL  = "#1a1a2e"
BG_ENTRY  = "#16213e"
FG_WHITE  = "#e0e0e0"
FG_GREEN  = "#00e676"
FG_RED    = "#ff1744"
FG_YELLOW = "#ffd600"
FG_CYAN   = "#00e5ff"
FG_ORANGE = "#ff9100"
ACCENT    = "#7c4dff"


class HomographDetector:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🔍 Detector de URL Falsas Homograph Attack")
        self.root.geometry("1024x750")
        self.root.state("zoomed")  # Windows
        self.root.minsize(900, 600)
        self.root.configure(bg=BG_DARK)

        # Variável para armazenar os dados da última análise (usado no HTML)
        self.dados_analise = None

        self._build_ui()

    # ──────────────────── CONSTRUÇÃO DA UI ──────────────────────
    def _build_ui(self):
        # Título
        tk.Label(
            self.root, text="🛡️ Detector de Homograph Attack em URL     🛡️",
            font=("Segoe UI", 18, "bold"), fg=FG_CYAN, bg=BG_DARK,
        ).pack(pady=(18, 4))

        tk.Label(
            self.root, text="Cole um link suspeito e descubra letras falsas disfarçadas",
            font=("Segoe UI", 10), fg="#888", bg=BG_DARK,
        ).pack(pady=(0, 12))

        # Frame de entrada
        frame_in = tk.Frame(self.root, bg=BG_PANEL, padx=14, pady=10)
        frame_in.pack(fill="x", padx=20, pady=6)

        tk.Label(
            frame_in, text="URL / Domínio:",
            font=("Consolas", 11, "bold"), fg=FG_WHITE, bg=BG_PANEL,
        ).grid(row=0, column=0, sticky="w")

        self.entry = tk.Entry(
            frame_in, font=("Consolas", 13),
            bg=BG_ENTRY, fg=FG_YELLOW, insertbackground=FG_YELLOW,
            relief="flat", bd=6,
        )
        self.entry.grid(row=1, column=0, sticky="ew", pady=6, ipady=4)
        frame_in.columnconfigure(0, weight=1)

        # Frame de Botões
        frame_btn = tk.Frame(self.root, bg=BG_DARK)
        frame_btn.pack(pady=6)

        # Estilo dos botões corrigido (Dicionário padrão para evitar erros no VS Code)
        btn_style = {
            "font": ("Segoe UI", 10, "bold"),
            "relief": "flat",
            "cursor": "hand2",
            "activebackground": ACCENT,
            "activeforeground": "white",
        }

        self.btn_analisar = tk.Button(
            frame_btn, text="🔎 ANALISAR URL",
            bg=ACCENT, fg="white", command=self.analisar, **btn_style
        )
        self.btn_analisar.pack(side="left", padx=5, ipadx=10, ipady=4)

        self.btn_html = tk.Button(
            frame_btn, text="💾 Salvar Relatório HTML",
            bg="#00b0ff", fg="white", command=self.salvar_html, **btn_style
        )
        self.btn_html.pack(side="left", padx=5, ipadx=10, ipady=4)

        self.btn_exemplo = tk.Button(
            frame_btn, text="📋 Exemplo Falso",
            bg="#37474f", fg=FG_WHITE, command=self.carregar_exemplo, **btn_style
        )
        self.btn_exemplo.pack(side="left", padx=5, ipadx=10, ipady=4)

        self.btn_limpar = tk.Button(
            frame_btn, text="🗑 Limpar",
            bg="#37474f", fg=FG_WHITE, command=self.limpar, **btn_style
        )
        self.btn_limpar.pack(side="left", padx=5, ipadx=10, ipady=4)

        # Veredicto
        self.lbl_veredicto = tk.Label(self.root, text="", font=("Segoe UI", 14, "bold"), bg=BG_DARK)
        self.lbl_veredicto.pack(pady=(8, 2))

        # Área de resultado
        self.txt_result = scrolledtext.ScrolledText(
            self.root, font=("Consolas", 11), bg="#111122", fg=FG_WHITE,
            insertbackground=FG_WHITE, relief="flat", bd=8, wrap="word",
        )
        self.txt_result.pack(fill="both", expand=True, padx=20, pady=(4, 16))

        # Tags de cor para o Text widget
        self.txt_result.tag_configure("titulo", foreground=FG_CYAN, font=("Consolas", 12, "bold"))
        self.txt_result.tag_configure("seguro", foreground=FG_GREEN)
        self.txt_result.tag_configure("perigo", foreground=FG_RED, font=("Consolas", 11, "bold"))
        self.txt_result.tag_configure("alerta", foreground=FG_YELLOW)
        self.txt_result.tag_configure("info", foreground=FG_ORANGE)
        self.txt_result.tag_configure("separador", foreground="#555")

    # ──────────────────── LÓGICA PRINCIPAL ──────────────────────
    def analisar(self):
        url = self.entry.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Cole uma URL para analisar.")
            return

        self.txt_result.delete("1.0", "end")
        
        # Resetando dados para o relatório HTML
        self.dados_analise = {
            "url": url,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "seguro": True,
            "caracteres": [],
            "alertas": []
        }

        self._escrever("=" * 72 + "\n", "separador")
        self._escrever(f"  URL analisada:  {url}\n", "titulo")
        self._escrever("=" * 72 + "\n\n", "separador")
        self._escrever("  POS  |  CARACTERE  |  ord()  |  ASCII?  |  NOME UNICODE\n", "info")
        self._escrever("  " + "-" * 68 + "\n", "separador")

        suspeitas = []

        for pos, char in enumerate(url):
            codigo = ord(char)
            eh_ascii = char.isascii()
            nome = unicodedata.name(char, "DESCONHECIDO")

            # Salvar dados para HTML
            char_data = {"pos": pos, "char": char, "ord": codigo, "is_ascii": eh_ascii, "name": nome}
            self.dados_analise["caracteres"].append(char_data)

            if eh_ascii:
                tag, ascii_str = "seguro", "✅ Sim"
            else:
                tag, ascii_str = "perigo", "❌ NÃO"
                suspeitas.append(char_data)
                self.dados_analise["seguro"] = False

            linha = f"  {pos:<4} |  {char:^11}  |  {codigo:<5}  |  {ascii_str:<8}  |  {nome}\n"
            self._escrever(linha, tag)

        self._escrever("\n" + "=" * 72 + "\n", "separador")

        if suspeitas:
            self._escrever("\n  🚨  LETRAS FALSAS DETECTADAS:\n\n", "perigo")
            for item in suspeitas:
                cod = item["ord"]
                if cod in HOMOGLYPHS:
                    _, latino, cod_lat = HOMOGLYPHS[cod]
                    msg = (f"Posição {item['pos']}: '{item['char']}' (ord={cod}) "
                           f"parece o '{latino}' latino (ord={cod_lat}), mas é CIRÍLICO!")
                    
                    self.dados_analise["alertas"].append(msg)
                    self._escrever(f"   → {msg}\n\n", "perigo")
                else:
                    msg = f"Posição {item['pos']}: '{item['char']}' (ord={cod}) não é padrão ASCII."
                    self.dados_analise["alertas"].append(msg)
                    self._escrever(f"   → {msg}\n\n", "alerta")

            self.lbl_veredicto.config(text="⛔ URL SUSPEITA — HOMOGRAPH DETECTADO!", fg=FG_RED)
        else:
            self._escrever("\n  ✅ Todas as letras são ASCII legítimas.\n", "seguro")
            self.lbl_veredicto.config(text="✅ URL Segura — Sem homoglyphs detectados", fg=FG_GREEN)

        self._escrever("\n" + "=" * 72 + "\n", "separador")

    # ──────────────────── GERADOR HTML ────────────────────────────
    def salvar_html(self):
        if not self.dados_analise:
            messagebox.showinfo("Aviso", "Por favor, analise uma URL primeiro.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("Arquivos HTML", "*.html")],
            title="Salvar Relatório de Segurança",
            initialfile="relatorio_seguranca_url.html"
        )

        if not filepath:
            return

        # ── Construção do HTML e CSS Profissional ──
        status_classe = "status-safe" if self.dados_analise["seguro"] else "status-danger"
        status_texto = "✅ URL SEGURA (Nenhuma anomalia detectada)" if self.dados_analise["seguro"] else "🚨 URL PERIGOSA (Possível Homograph Attack)"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Relatório de Segurança - Homograph Attack</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-top: 0; }}
                .header-info {{ font-size: 1.1em; margin-bottom: 20px; color: #555; }}
                .url-box {{ background: #eef2f5; padding: 15px; border-radius: 6px; word-break: break-all; font-family: monospace; font-size: 1.2em; border: 1px solid #dce4ec; }}
                
                .status-banner {{ padding: 15px 20px; border-radius: 6px; font-weight: bold; font-size: 1.2em; margin: 20px 0; }}
                .status-safe {{ background-color: #e8f5e9; color: #2e7d32; border-left: 6px solid #2e7d32; }}
                .status-danger {{ background-color: #ffebee; color: #c62828; border-left: 6px solid #c62828; }}
                
                .alerts-box {{ background: #fff3e0; border: 1px solid #ffe0b2; padding: 15px; border-radius: 6px; margin-bottom: 20px; }}
                .alerts-box h3 {{ margin-top: 0; color: #e65100; }}
                .alerts-box ul {{ margin-bottom: 0; }}
                
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-family: monospace; font-size: 1.1em; }}
                th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ecf0f1; }}
                th {{ background-color: #f8f9fa; color: #2c3e50; font-family: 'Segoe UI', sans-serif; text-transform: uppercase; font-size: 0.9em; }}
                tr:hover {{ background-color: #f5f7fa; }}
                
                .char-danger {{ color: #e74c3c; font-weight: bold; background: #fdf0ed; padding: 2px 6px; border-radius: 4px; }}
                .char-safe {{ color: #27ae60; }}
                .footer {{ margin-top: 30px; text-align: center; color: #95a5a6; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🛡️ Relatório de Análise de URL (Homograph Attack)</h1>
                
                <div class="header-info">
                    <strong>Data da Análise:</strong> {self.dados_analise['data']}
                </div>
                
                <div class="url-box">
                    <strong>URL Analisada:</strong><br><br>{self.dados_analise['url']}
                </div>

                <div class="status-banner {status_classe}">
                    {status_texto}
                </div>
        """

        # Se tiver alertas, adiciona a caixa de alertas
        if not self.dados_analise["seguro"]:
            html_content += """
                <div class="alerts-box">
                    <h3>🚨 Alertas de Caracteres Falsos Detectados:</h3>
                    <ul>
            """
            for alerta in self.dados_analise["alertas"]:
                html_content += f"<li>{alerta}</li>"
            html_content += """
                    </ul>
                </div>
            """

        # Construir a Tabela
        html_content += """
                <h3>Detalhamento caractere por caractere</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Posição</th>
                            <th>Caractere</th>
                            <th>Código ord()</th>
                            <th>É Padrão (ASCII)?</th>
                            <th>Nome Unicode</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for item in self.dados_analise["caracteres"]:
            cls = "char-safe" if item["is_ascii"] else "char-danger"
            ascii_txt = "Sim" if item["is_ascii"] else "NÃO"
            char_display = item["char"] if item["char"].strip() else "&nbsp;"
            
            html_content += f"""
                        <tr>
                            <td>{item['pos']}</td>
                            <td class="{cls}"><strong>{char_display}</strong></td>
                            <td>{item['ord']}</td>
                            <td class="{cls}">{ascii_txt}</td>
                            <td>{item['name']}</td>
                        </tr>
            """

        html_content += """
                    </tbody>
                </table>
                
                <div class="footer">
                    Relatório gerado automaticamente pela ferramenta Python Homograph Detector.
                </div>
            </div>
        </body>
        </html>
        """

        # Salvar o arquivo
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            messagebox.showinfo("Sucesso", f"Relatório HTML salvo com sucesso em:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{str(e)}")


    # ──────────────────── HELPERS ───────────────────────────────
    def _escrever(self, texto: str, tag: str):
        self.txt_result.insert("end", texto, tag)
        self.txt_result.see("end")

    def carregar_exemplo(self):
        exemplo = "https://www.b\u0430nc\u043e.com.br/login"
        self.entry.delete(0, "end")
        self.entry.insert(0, exemplo)
        self.lbl_veredicto.config(text="")

    def limpar(self):
        self.entry.delete(0, "end")
        self.txt_result.delete("1.0", "end")
        self.lbl_veredicto.config(text="")
        self.dados_analise = None


if __name__ == "__main__":
    root = tk.Tk()
    app = HomographDetector(root)
    root.mainloop()
