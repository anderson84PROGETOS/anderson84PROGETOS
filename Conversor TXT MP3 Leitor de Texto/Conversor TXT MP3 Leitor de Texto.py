"""
Conversor TXT -> MP3 + Leitor de Texto com Vozes Neurais
(Microsoft Edge TTS)

Requisitos:
    pip install edge-tts pygame

Precisa de internet:
    As vozes são geradas na nuvem da Microsoft.
"""

import os

# ============================================================
# OCULTAR MENSAGEM DO PYGAME NO CMD
# ============================================================
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# ============================================================
# IMPORTAÇÕES
# ============================================================
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

import edge_tts
import asyncio
import threading
import tempfile
import time
import pygame


# ============================================================
# INICIALIZAÇÃO DO PYGAME
# ============================================================
pygame.mixer.init()


# ============================================================
# LISTA COMPLETA DE IDIOMAS (nome exibido, código do locale)
# ============================================================
IDIOMAS = [
    # Português
    ("Português (Brasil)", "pt-BR"),
    ("Português (Portugal)", "pt-PT"),
    ("Português (Angola)", "pt-AO"),
    ("Português (Moçambique)", "pt-MZ"),
    # Inglês
    ("Inglês (EUA)", "en-US"),
    ("Inglês (Reino Unido)", "en-GB"),
    ("Inglês (Austrália)", "en-AU"),
    ("Inglês (Canadá)", "en-CA"),
    ("Inglês (Índia)", "en-IN"),
    ("Inglês (Irlanda)", "en-IE"),
    ("Inglês (Nova Zelândia)", "en-NZ"),
    ("Inglês (África do Sul)", "en-ZA"),
    # Espanhol
    ("Espanhol (Espanha)", "es-ES"),
    ("Espanhol (México)", "es-MX"),
    ("Espanhol (Argentina)", "es-AR"),
    ("Espanhol (Chile)", "es-CL"),
    ("Espanhol (Colômbia)", "es-CO"),
    ("Espanhol (Peru)", "es-PE"),
    ("Espanhol (Venezuela)", "es-VE"),
    ("Espanhol (EUA)", "es-US"),
    # Francês
    ("Francês (França)", "fr-FR"),
    ("Francês (Canadá)", "fr-CA"),
    ("Francês (Bélgica)", "fr-BE"),
    ("Francês (Suíça)", "fr-CH"),
    # Alemão
    ("Alemão (Alemanha)", "de-DE"),
    ("Alemão (Áustria)", "de-AT"),
    ("Alemão (Suíça)", "de-CH"),
    # Italiano
    ("Italiano (Itália)", "it-IT"),
    ("Italiano (Suíça)", "it-CH"),
    # Chinês
    ("Chinês (Simplificado)", "zh-CN"),
    ("Chinês (Tradicional)", "zh-TW"),
    ("Chinês (Hong Kong)", "zh-HK"),
    ("Chinês (Macau)", "zh-MO"),
    # Japonês e Coreano
    ("Japonês", "ja-JP"),
    ("Coreano", "ko-KR"),
    # Árabe
    ("Árabe (Arábia Saudita)", "ar-SA"),
    ("Árabe (Emirados Árabes)", "ar-AE"),
    ("Árabe (Egito)", "ar-EG"),
    ("Árabe (Marrocos)", "ar-MA"),
    ("Árabe (Iraque)", "ar-IQ"),
    ("Árabe (Jordânia)", "ar-JO"),
    # Índia e Ásia
    ("Hindi", "hi-IN"),
    ("Bengali", "bn-IN"),
    ("Bengali (Bangladesh)", "bn-BD"),
    ("Tamil", "ta-IN"),
    ("Telugu", "te-IN"),
    ("Marathi", "mr-IN"),
    ("Gujarati", "gu-IN"),
    ("Kannada", "kn-IN"),
    ("Malayalam", "ml-IN"),
    ("Punjabi", "pa-IN"),
    ("Urdu", "ur-PK"),
    ("Nepali", "ne-NP"),
    ("Sinhala", "si-LK"),
    # Europa
    ("Holandês (Países Baixos)", "nl-NL"),
    ("Holandês (Bélgica)", "nl-BE"),
    ("Sueco", "sv-SE"),
    ("Norueguês", "nb-NO"),
    ("Dinamarquês", "da-DK"),
    ("Finlandês", "fi-FI"),
    ("Islandês", "is-IS"),
    ("Polonês", "pl-PL"),
    ("Tcheco", "cs-CZ"),
    ("Eslovaco", "sk-SK"),
    ("Húngaro", "hu-HU"),
    ("Romeno", "ro-RO"),
    ("Búlgaro", "bg-BG"),
    ("Croata", "hr-HR"),
    ("Sérvio", "sr-RS"),
    ("Esloveno", "sl-SI"),
    ("Grego", "el-GR"),
    ("Ucraniano", "uk-UA"),
    ("Russo", "ru-RU"),
    ("Lituano", "lt-LT"),
    ("Letão", "lv-LV"),
    ("Estoniano", "et-EE"),
    ("Macedônio", "mk-MK"),
    ("Bósnio", "bs-BA"),
    ("Albanês", "sq-AL"),
    ("Catalão", "ca-ES"),
    ("Basco", "eu-ES"),
    ("Galego", "gl-ES"),
    # Oriente Médio
    ("Hebraico", "he-IL"),
    ("Turco", "tr-TR"),
    ("Persa", "fa-IR"),
    ("Armênio", "hy-AM"),
    ("Georgiano", "ka-GE"),
    ("Azerbaijano", "az-AZ"),
    # Sudeste Asiático
    ("Indonésio", "id-ID"),
    ("Malaio", "ms-MY"),
    ("Vietnamita", "vi-VN"),
    ("Tailandês", "th-TH"),
    ("Filipino", "fil-PH"),
    ("Khmer", "km-KH"),
    ("Birmanês", "my-MM"),
    # África
    ("Africâner", "af-ZA"),
    ("Suaíli", "sw-KE"),
    ("Zulu", "zu-ZA"),
    ("Xhosa", "xh-ZA"),
    ("Amárico", "am-ET"),
    ("Somali", "so-SO"),
    # Outros
    ("Maltês", "mt-MT"),
    ("Irlandês", "ga-IE"),
    ("Galês", "cy-GB"),
    ("Luxemburguês", "lb-LU"),
    ("Frísio", "fy-NL"),
    ("Esperanto", "eo"),
]

# Fallback caso a lista remota falhe completamente
VOZES_FALLBACK = {
    "pt-BR": ["pt-BR-FranciscaNeural", "pt-BR-AntonioNeural"],
    "pt-PT": ["pt-PT-RaquelNeural", "pt-PT-DuarteNeural"],
    "en-US": ["en-US-JennyNeural", "en-US-GuyNeural", "en-US-AriaNeural"],
    "es-ES": ["es-ES-ElviraNeural", "es-ES-AlvaroNeural"],
    "fr-FR": ["fr-FR-DeniseNeural", "fr-FR-HenriNeural"],
    "de-DE": ["de-DE-KatjaNeural", "de-DE-ConradNeural"],
    "ja-JP": ["ja-JP-NanamiNeural", "ja-JP-KeitaNeural"],
    "zh-CN": ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"],
}


class TextToSpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor TXT → MP3 + Leitor de Texto (Vozes Neurais)")
        self.root.geometry("820x820")
        self.root.resizable(True, True)
        self.root.configure(bg="#1e1e2e")

        self.arquivo_txt = None
        self.falando = False
        self.pausado = False
        self.vozes = {}
        self.todas_vozes = []
        self.idioma_map = {nome: codigo for nome, codigo in IDIOMAS}

        # Inicializa o pygame
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
        except Exception as e:
            messagebox.showwarning(
                "Aviso",
                f"Não foi possível iniciar o áudio do sistema:\n{e}\n"
                "A conversão para MP3 ainda funcionará."
            )

        # ---------------- Estilo global ----------------
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        style.configure("TCombobox", fieldbackground="#313244", background="#313244", foreground="#cdd6f4")
        style.map("TCombobox", fieldbackground=[("readonly", "#313244")])
        style.configure("TScale", background="#1e1e2e", troughcolor="#45475a")

        # ---------------- Título ----------------
        tk.Label(
            root,
            text="Conversor de Texto para Áudio (MP3)",
            font=("Segoe UI", 18, "bold"),
            bg="#1e1e2e",
            fg="#89b4fa"
        ).pack(pady=(15, 5))

        tk.Label(
            root,
            text="Síntese neural via Microsoft Edge TTS",
            font=("Segoe UI", 10),
            bg="#1e1e2e",
            fg="#a6adc8"
        ).pack(pady=(0, 12))

        # ---------------- Seleção de arquivo ----------------
        frame_arquivo = tk.Frame(root, bg="#1e1e2e")
        frame_arquivo.pack(pady=6, fill="x", padx=25)

        self.label_arquivo = tk.Label(
            frame_arquivo,
            text="Nenhum arquivo selecionado",
            fg="#a6adc8",
            bg="#1e1e2e",
            wraplength=520,
            font=("Segoe UI", 10)
        )
        self.label_arquivo.pack(side="left", fill="x", expand=True)

        btn_selecionar = tk.Button(
            frame_arquivo,
            text="Selecionar arquivo .txt",
            command=self.selecionar_arquivo,
            bg="#a6e3a1",
            fg="#1e1e2e",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            activebackground="#94e2d5"
        )
        btn_selecionar.pack(side="right", padx=5)

        # ---------------- Área de texto ----------------
        tk.Label(
            root,
            text="Conteúdo do arquivo (pode editar):",
            font=("Segoe UI", 11),
            bg="#1e1e2e",
            fg="#cdd6f4"
        ).pack(anchor="w", padx=25)

        self.texto_area = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            height=11,
            font=("Segoe UI", 10),
            bg="#313244",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#45475a",
            highlightcolor="#89b4fa"
        )
        self.texto_area.pack(padx=25, pady=6, fill="both", expand=True)

        # ---------------- Idioma e Voz ----------------
        frame_voz = tk.Frame(root, bg="#1e1e2e")
        frame_voz.pack(pady=10, fill="x", padx=25)

        tk.Label(frame_voz, text="Idioma:", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10)).pack(side="left")
        self.idioma_var = tk.StringVar(value="Português (Brasil)")
        self.combo_idioma = ttk.Combobox(
            frame_voz,
            textvariable=self.idioma_var,
            values=[i[0] for i in IDIOMAS],
            state="readonly",
            width=28
        )
        self.combo_idioma.current(0)
        self.combo_idioma.pack(side="left", padx=8)
        self.combo_idioma.bind("<<ComboboxSelected>>", self.atualizar_vozes)

        tk.Label(frame_voz, text="Voz:", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10)).pack(side="left", padx=(15, 0))
        self.voz_var = tk.StringVar()
        self.combo_voz = ttk.Combobox(
            frame_voz,
            textvariable=self.voz_var,
            state="readonly",
            width=40
        )
        self.combo_voz.pack(side="left", padx=8)

        btn_atualizar = tk.Button(
            frame_voz,
            text="🔄 Recarregar",
            command=lambda: threading.Thread(target=self.carregar_vozes, daemon=True).start(),
            bg="#585b70",
            fg="#cdd6f4",
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            activebackground="#6c7086"
        )
        btn_atualizar.pack(side="left", padx=6)

        # ============================================================
        # AJUSTES DE VOZ  (SLIDERS iguais à foto)
        # ============================================================
        frame_ajuste = tk.Frame(root, bg="#1e1e2e")
        frame_ajuste.pack(pady=10, fill="x", padx=25)

        # --- Velocidade ---
        row1 = tk.Frame(frame_ajuste, bg="#1e1e2e")
        row1.pack(fill="x", pady=3)
        tk.Label(row1, text="Velocidade (%):", width=14, anchor="w",
                 bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10)).pack(side="left")
        self.rate_var = tk.DoubleVar(value=0)
        self.lbl_rate = tk.Label(row1, text="+0", width=5, anchor="e",
                                 bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10))
        self.lbl_rate.pack(side="right", padx=(8, 0))
        scale_rate = ttk.Scale(row1, from_=-50, to=50, orient="horizontal",
                               variable=self.rate_var, length=380,
                               command=lambda v: self.lbl_rate.config(text=f"{int(float(v)):+d}"))
        scale_rate.pack(side="left", fill="x", expand=True, padx=6)

        # --- Tom ---
        row2 = tk.Frame(frame_ajuste, bg="#1e1e2e")
        row2.pack(fill="x", pady=3)
        tk.Label(row2, text="Tom (Hz):", width=14, anchor="w",
                 bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10)).pack(side="left")
        self.pitch_var = tk.DoubleVar(value=0)
        self.lbl_pitch = tk.Label(row2, text="+0", width=5, anchor="e",
                                  bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10))
        self.lbl_pitch.pack(side="right", padx=(8, 0))
        scale_pitch = ttk.Scale(row2, from_=-50, to=50, orient="horizontal",
                                variable=self.pitch_var, length=380,
                                command=lambda v: self.lbl_pitch.config(text=f"{int(float(v)):+d}"))
        scale_pitch.pack(side="left", fill="x", expand=True, padx=6)

        # --- Volume ---
        row3 = tk.Frame(frame_ajuste, bg="#1e1e2e")
        row3.pack(fill="x", pady=3)
        tk.Label(row3, text="Volume (%):", width=14, anchor="w",
                 bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10)).pack(side="left")
        self.volume_var = tk.DoubleVar(value=0)
        self.lbl_volume = tk.Label(row3, text="+0", width=5, anchor="e",
                                   bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10))
        self.lbl_volume.pack(side="right", padx=(8, 0))
        scale_volume = ttk.Scale(row3, from_=-50, to=50, orient="horizontal",
                                 variable=self.volume_var, length=380,
                                 command=lambda v: self.lbl_volume.config(text=f"{int(float(v)):+d}"))
        scale_volume.pack(side="left", fill="x", expand=True, padx=6)

        # Texto explicativo (igual à foto)
        tk.Label(
            frame_ajuste,
            text="(← negativo = mais lento / mais grave / mais baixo   |   positivo = mais rápido / mais agudo / mais alto →)",
            fg="#a6adc8",
            bg="#1e1e2e",
            font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(4, 0))

        # ---------------- Botões ----------------
        frame_botoes = tk.Frame(root, bg="#1e1e2e")
        frame_botoes.pack(pady=15)

        self.btn_ler = tk.Button(
            frame_botoes,
            text="🔊  Ler Texto",
            command=self.iniciar_leitura,
            bg="#f9e2af",
            fg="#1e1e2e",
            font=("Segoe UI", 11, "bold"),
            width=13,
            height=2,
            relief="flat",
            cursor="hand2",
            activebackground="#f5c2e7"
        )
        self.btn_ler.pack(side="left", padx=7)

        self.btn_pausar = tk.Button(
            frame_botoes,
            text="⏸  Pausar",
            command=self.toggle_pausa,
            bg="#cba6f7",
            fg="#1e1e2e",
            font=("Segoe UI", 11, "bold"),
            width=11,
            height=2,
            relief="flat",
            cursor="hand2",
            state="disabled",
            activebackground="#b4befe"
        )
        self.btn_pausar.pack(side="left", padx=7)

        self.btn_parar = tk.Button(
            frame_botoes,
            text="⏹  Parar",
            command=self.parar_fala,
            bg="#f38ba8",
            fg="#1e1e2e",
            font=("Segoe UI", 11, "bold"),
            width=10,
            height=2,
            relief="flat",
            cursor="hand2",
            state="disabled",
            activebackground="#eba0ac"
        )
        self.btn_parar.pack(side="left", padx=7)

        self.btn_converter = tk.Button(
            frame_botoes,
            text="💾  Salvar MP3",
            command=self.iniciar_conversao,
            bg="#89b4fa",
            fg="#1e1e2e",
            font=("Segoe UI", 11, "bold"),
            width=13,
            height=2,
            relief="flat",
            cursor="hand2",
            activebackground="#74c7ec"
        )
        self.btn_converter.pack(side="left", padx=7)

        # ---------------- Status ----------------
        self.status = tk.Label(
            root,
            text="Carregando vozes...",
            fg="#89b4fa",
            bg="#1e1e2e",
            font=("Segoe UI", 10)
        )
        self.status.pack(pady=8)

        # Carrega as vozes em segundo plano
        threading.Thread(target=self.carregar_vozes, daemon=True).start()

    # ============================================================
    # VOZES
    # ============================================================
    def carregar_vozes(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            vozes = loop.run_until_complete(edge_tts.list_voices())
            loop.close()
            self.todas_vozes = vozes
            self.root.after(0, self.atualizar_vozes)
            self.root.after(0, lambda: self.status.config(
                text=f"Pronto — {len(vozes)} vozes carregadas da Microsoft", fg="#a6e3a1"))
        except Exception as e:
            self.root.after(0, lambda: self.status.config(
                text=f"Erro ao carregar vozes: {e}", fg="#f38ba8"))

    def atualizar_vozes(self, event=None):
        codigo = self.idioma_map.get(self.idioma_var.get(), "pt-BR")

        lista = []
        self.vozes = {}
        genero = {"Female": "Feminina", "Male": "Masculina"}

        for v in self.todas_vozes:
            if v["Locale"].lower().startswith(codigo.lower()):
                short = v["ShortName"]
                sexo = genero.get(v.get("Gender", ""), v.get("Gender", ""))
                nome = f"{short} — {sexo}"
                lista.append(nome)
                self.vozes[nome] = short

        lista.sort(key=lambda x: (not x.endswith("Feminina"), x))

        if lista:
            self.combo_voz["values"] = lista
            self.combo_voz.current(0)
        else:
            fallback = VOZES_FALLBACK.get(codigo, [])
            if fallback:
                lista = [f"{v} — ?" for v in fallback]
                self.vozes = {f"{v} — ?": v for v in fallback}
                self.combo_voz["values"] = lista
                self.combo_voz.current(0)
                self.status.config(
                    text=f"Usando lista local para {self.idioma_var.get()} (sem conexão)",
                    fg="#f9e2af"
                )
            else:
                self.combo_voz["values"] = []
                self.combo_voz.set("Nenhuma voz encontrada")

    # ============================================================
    # ARQUIVO
    # ============================================================
    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecione um arquivo de texto",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        if caminho:
            self.arquivo_txt = caminho
            self.label_arquivo.config(text=os.path.basename(caminho), fg="#cdd6f4")
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    texto = f.read()
                self.texto_area.delete(1.0, tk.END)
                self.texto_area.insert(tk.END, texto)
                self.status.config(text="Arquivo carregado!", fg="#a6e3a1")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{e}")

    def obter_texto(self):
        return self.texto_area.get(1.0, tk.END).strip()

    def obter_voz_selecionada(self):
        nome = self.voz_var.get()
        return self.vozes.get(nome, "pt-BR-FranciscaNeural")

    def obter_parametros(self):
        rate = int(round(self.rate_var.get()))
        pitch = int(round(self.pitch_var.get()))
        volume = int(round(self.volume_var.get()))

        rate = max(-50, min(50, rate))
        pitch = max(-50, min(50, pitch))
        volume = max(-50, min(50, volume))

        return f"{rate:+d}%", f"{pitch:+d}Hz", f"{volume:+d}%"

    # ============================================================
    # LER TEXTO
    # ============================================================
    def iniciar_leitura(self):
        texto = self.obter_texto()
        if not texto:
            messagebox.showwarning("Aviso", "Não há texto para ler!")
            return
        if self.falando:
            return

        self.falando = True
        self.pausado = False
        self.btn_ler.config(state="disabled")
        self.btn_pausar.config(state="normal", text="⏸  Pausar")
        self.btn_parar.config(state="normal")
        self.btn_converter.config(state="disabled")
        self.status.config(text="Gerando e lendo áudio...", fg="#f9e2af")

        threading.Thread(target=self.ler_texto, args=(texto,), daemon=True).start()

    def ler_texto(self, texto):
        caminho_temp = None
        try:
            voz = self.obter_voz_selecionada()
            rate, pitch, volume = self.obter_parametros()

            communicate = edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch, volume=volume)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                caminho_temp = tmp.name

            asyncio.run(communicate.save(caminho_temp))

            pygame.mixer.music.load(caminho_temp)
            pygame.mixer.music.play()

            while self.falando:
                if self.pausado:
                    time.sleep(0.1)
                    continue
                if not pygame.mixer.music.get_busy():
                    break
                pygame.time.Clock().tick(10)

            self.root.after(0, self.leitura_concluida)
        except Exception as e:
            erro = str(e)
            self.root.after(0, lambda: self.erro_leitura(erro))
        finally:
            if caminho_temp and os.path.exists(caminho_temp):
                try:
                    os.remove(caminho_temp)
                except:
                    pass

    def toggle_pausa(self):
        if not self.falando:
            return
        if self.pausado:
            try:
                pygame.mixer.music.unpause()
            except:
                pass
            self.pausado = False
            self.btn_pausar.config(text="⏸  Pausar")
            self.status.config(text="Reproduzindo...", fg="#a6e3a1")
        else:
            try:
                pygame.mixer.music.pause()
            except:
                pass
            self.pausado = True
            self.btn_pausar.config(text="▶  Continuar")
            self.status.config(text="Pausado", fg="#f9e2af")

    def leitura_concluida(self):
        self.falando = False
        self.pausado = False
        self.btn_ler.config(state="normal")
        self.btn_pausar.config(state="disabled", text="⏸  Pausar")
        self.btn_parar.config(state="disabled")
        self.btn_converter.config(state="normal")
        self.status.config(text="Leitura concluída!", fg="#a6e3a1")

    def erro_leitura(self, mensagem):
        self.falando = False
        self.pausado = False
        self.btn_ler.config(state="normal")
        self.btn_pausar.config(state="disabled", text="⏸  Pausar")
        self.btn_parar.config(state="disabled")
        self.btn_converter.config(state="normal")
        self.status.config(text="Erro na leitura", fg="#f38ba8")
        messagebox.showerror("Erro", f"Falha ao ler o texto:\n{mensagem}")

    def parar_fala(self):
        self.falando = False
        self.pausado = False
        try:
            pygame.mixer.music.stop()
        except:
            pass
        self.btn_ler.config(state="normal")
        self.btn_pausar.config(state="disabled", text="⏸  Pausar")
        self.btn_parar.config(state="disabled")
        self.btn_converter.config(state="normal")
        self.status.config(text="Leitura interrompida", fg="#f9e2af")

    # ============================================================
    # SALVAR MP3
    # ============================================================
    def iniciar_conversao(self):
        texto = self.obter_texto()
        if not texto:
            messagebox.showwarning("Aviso", "Não há texto para converter!")
            return

        nome_padrao = "audio.mp3"
        if self.arquivo_txt:
            nome_padrao = os.path.splitext(os.path.basename(self.arquivo_txt))[0] + ".mp3"

        caminho_mp3 = filedialog.asksaveasfilename(
            title="Salvar arquivo MP3",
            defaultextension=".mp3",
            initialfile=nome_padrao,
            filetypes=[("Arquivo MP3", "*.mp3")]
        )
        if not caminho_mp3:
            return

        self.btn_converter.config(state="disabled")
        self.btn_ler.config(state="disabled")
        self.status.config(text="Gerando MP3...", fg="#f9e2af")

        threading.Thread(target=self.converter, args=(texto, caminho_mp3), daemon=True).start()

    def converter(self, texto, caminho_mp3):
        try:
            voz = self.obter_voz_selecionada()
            rate, pitch, volume = self.obter_parametros()
            communicate = edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch, volume=volume)
            asyncio.run(communicate.save(caminho_mp3))
            self.root.after(0, lambda: self.sucesso(caminho_mp3))
        except Exception as e:
            erro = str(e)
            self.root.after(0, lambda: self.erro(erro))

    def sucesso(self, caminho):
        self.btn_converter.config(state="normal")
        self.btn_ler.config(state="normal")
        self.status.config(text="MP3 gerado com sucesso!", fg="#a6e3a1")
        messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{caminho}")

    def erro(self, mensagem):
        self.btn_converter.config(state="normal")
        self.btn_ler.config(state="normal")
        self.status.config(text="Erro na conversão", fg="#f38ba8")
        messagebox.showerror("Erro", f"Falha ao gerar o áudio:\n{mensagem}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TextToSpeechApp(root)
    root.mainloop()
