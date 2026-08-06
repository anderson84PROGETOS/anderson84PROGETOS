#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEALTH-ENCODE + Estego Avançado  —  ferramenta unificada
=========================================================
Abas:
  1. LSB Codificar   (compatível Stylesuxx + compressão)
  2. LSB Decodificar
  3. Estego Avançado (método Ztegonograph – blocos 8x8 + quantização de luma)
  4. Conversor de Imagem (normaliza QUALQUER foto para PNG 1024x1024 sem perdas)

Detecção automática: ao carregar uma imagem no ESTEGO AVANÇADO,
o app já verifica sozinho se existe mensagem oculta.

Requisitos:  pip install pillow numpy
"""

import os
import threading
import time
import zlib
import warnings
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

import numpy as np
from PIL import Image, ImageOps, ImageTk

warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================================
#  PALETA / FONTES COMUNS
# ============================================================
BG      = "#0a0a0a"
PANEL   = "#0f0f0f"
GREEN   = "#00ff41"
GREEN_D = "#1f6b3a"
NORMAL  = "#79d99b"
DIM     = "#4a8f5f"
ERR     = "#ff5555"
OK      = "#55ff55"
BTN_BG  = "#1a1a1a"
EDGE    = "#2a2a2a"


def mono_font(size, bold=False):
    try:
        import tkinter.font as tkfont
        fams = set(tkfont.families())
    except Exception:
        fams = set()
    for name in ("Consolas", "Courier New", "DejaVu Sans Mono", "Menlo", "Monaco", "Courier"):
        if name in fams:
            return (name, size, "bold" if bold else "normal")
    return ("Courier New", size, "bold" if bold else "normal")


# ============================================================
#  NÚCLEO LSB (STEALTH-ENCODE)
# ============================================================
def encode_lsb(image_path, message, output_path, compatible_mode=False):
    try:
        img = Image.open(image_path).convert("RGB")
        pixels = list(img.getdata())

        if compatible_mode:
            data_to_hide = (message + "<<<END>>>").encode("utf-8")
        else:
            compressed = zlib.compress(message.encode("utf-8"), level=9)
            data_to_hide = compressed + b"<<<END>>>"

        binary_message = "".join(format(byte, "08b") for byte in data_to_hide)
        max_bits = len(pixels) * 3

        if len(binary_message) > max_bits:
            max_bytes = max_bits // 8
            raise ValueError(f"Mensagem muito grande!\nCapacidade máxima ≈ {max_bytes:,} bytes")

        encoded_pixels = []
        index = 0
        for pixel in pixels:
            r, g, b = pixel
            if index < len(binary_message):
                r = (r & ~1) | int(binary_message[index])
                index += 1
            if index < len(binary_message):
                g = (g & ~1) | int(binary_message[index])
                index += 1
            if index < len(binary_message):
                b = (b & ~1) | int(binary_message[index])
                index += 1
            encoded_pixels.append((r, g, b))

        new_img = Image.new("RGB", img.size)
        new_img.putdata(encoded_pixels)
        new_img.save(output_path)
        return True, "Modo: " + ("Compatível com Site" if compatible_mode else "Com Compressão")
    except Exception as e:
        return False, str(e)


def decode_lsb_compatible(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        pixels = list(img.getdata())
        binary_message = "".join(str(r & 1) + str(g & 1) + str(b & 1) for r, g, b in pixels)

        markers = [b"<<<END>>>", b"###END###", b"END"]
        for marker in markers:
            marker_bin = "".join(format(byte, "08b") for byte in marker)
            if marker_bin in binary_message:
                message_bin = binary_message.split(marker_bin)[0]
                try:
                    data = bytes(int(message_bin[i:i + 8], 2) for i in range(0, len(message_bin), 8))
                    try:
                        return zlib.decompress(data).decode("utf-8", errors="replace")
                    except Exception:
                        return data.decode("utf-8", errors="replace")
                except Exception:
                    pass

        message = ""
        for i in range(0, len(binary_message) - 7, 8):
            byte_str = binary_message[i:i + 8]
            try:
                char = chr(int(byte_str, 2))
                if 32 <= ord(char) <= 126 or char in "\n\r\t ":
                    message += char
                elif len(message) > 40 and not char.isprintable():
                    break
            except Exception:
                break
        return message.strip() if len(message.strip()) > 5 else None
    except Exception:
        return None


# ============================================================
#  NÚCLEO ESTEGO AVANÇADO (Ztegonograph / blocos 8x8)
# ============================================================
BS = 8
REPEAT = 7
Q_STEP = 4            # robustez VISUAL: 4 (sutil) → 8 → 12 → 20 (forte, sobrevive mais)
ENCODE_W, ENCODE_H = 1024, 1024
PREVIEW_MAX = 300
# capacidade real calculada: (128*128 blocos // repeticao - 24) // 8
MAX_BYTES = ((ENCODE_W // BS) * (ENCODE_H // BS) // REPEAT - 24) // 8   # 289 bytes com REPEAT=7

try:
    RESAMPLE = Image.Resampling.BICUBIC
except AttributeError:
    RESAMPLE = Image.BICUBIC


def text_to_bits(text):
    data = text.encode("utf-8")
    bits = []
    for i in range(15, -1, -1):
        bits.append((len(data) >> i) & 1)
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    crc = 0
    for b in data:
        crc ^= b
    for i in range(7, -1, -1):
        bits.append((crc >> i) & 1)
    return bits


def bits_to_text(voted_bits):
    n = len(voted_bits)
    if n < 16:
        return None
    length = 0
    for i in range(16):
        length = (length << 1) | voted_bits[i]
    if length < 0 or length > 2048 or 16 + length * 8 + 8 > n:
        return None
    raw = bytearray()
    for i in range(16, 16 + length * 8, 8):
        b = 0
        for j in range(8):
            b = (b << 1) | voted_bits[i + j]
        raw.append(b)
    crc = 0
    for b in raw:
        crc ^= b
    recv_crc = 0
    for i in range(16 + length * 8, 16 + length * 8 + 8):
        recv_crc = (recv_crc << 1) | voted_bits[i]
    if crc != recv_crc:
        return None
    return bytes(raw).decode("utf-8", errors="replace")


def apply_blur(arr):
    temp = arr.astype(np.float64)
    horiz = (temp[:, :-2] + 2.0 * temp[:, 1:-1] + temp[:, 2:]) / 4.0
    vert = (horiz[:-2] + 2.0 * horiz[1:-1] + horiz[2:]) / 4.0
    arr[1:-1, 1:-1] = np.round(vert).astype(np.uint8)


def embed_bits(arr, repeated_bits):
    h, w = arr.shape[:2]
    by, bx = h // BS, w // BS
    weights = np.array([0.299, 0.587, 0.114])

    reshaped = arr.reshape(by, BS, bx, BS, 3).astype(np.float64)
    mean_y = (reshaped @ weights).mean(axis=(1, 3))

    k = np.floor(mean_y / Q_STEP + 0.5).astype(np.int64)
    mean_f = mean_y.ravel()
    k_f = k.ravel()
    delta = np.zeros(by * bx)

    for i, bit in enumerate(repeated_bits):
        if (k_f[i] & 1) != bit:
            if mean_f[i] >= k_f[i] * Q_STEP:
                k_f[i] += 1
            else:
                k_f[i] -= 1
        delta[i] = k_f[i] * Q_STEP - mean_f[i]

    reshaped += delta.reshape(by, 1, bx, 1, 1)
    arr = np.clip(reshaped.reshape(h, w, 3), 0, 255)
    arr = np.round(arr).astype(np.uint8)
    return arr


def extract_raw_bits(arr, total_bits):
    h, w = arr.shape[:2]
    by, bx = h // BS, w // BS
    weights = np.array([0.299, 0.587, 0.114])
    reshaped = arr.reshape(by, BS, bx, BS, 3).astype(np.float64)
    mean_y = (reshaped @ weights).mean(axis=(1, 3))
    k = np.floor(mean_y / Q_STEP + 0.5).astype(np.int64)
    return (k & 1).ravel()[:total_bits].tolist()


def _prepare(img):
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    if img.size != (ENCODE_W, ENCODE_H):
        img = img.resize((ENCODE_W, ENCODE_H), RESAMPLE)
    return img


def encode_image_advanced(source, message):
    img = _prepare(source)
    bits = text_to_bits(message)
    repeated = []
    for b in bits:
        repeated.extend([b] * REPEAT)
    total_blocks = (ENCODE_W // BS) * (ENCODE_H // BS)
    if len(repeated) > total_blocks:
        raise ValueError(f"mensagem muito grande (máx ~{MAX_BYTES} bytes UTF-8)")
    arr = np.asarray(img, dtype=np.uint8)
    return Image.fromarray(embed_bits(arr, repeated), "RGB")


def decode_image_advanced(source):
    img = _prepare(source)
    arr = np.asarray(img, dtype=np.uint8)
    raw = extract_raw_bits(arr, (ENCODE_W // BS) * (ENCODE_H // BS))
    usable = len(raw) // REPEAT * REPEAT
    groups = np.array(raw[:usable], dtype=np.int64).reshape(-1, REPEAT)
    voted = (groups.sum(axis=1) > REPEAT / 2).astype(np.int64).tolist()
    return bits_to_text(voted)


# ============================================================
#  INTERFACE UNIFICADA
# ============================================================
class UnifiedStegoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ESTEGANOGRAFIA LSB CODIFICAR - LSB DECODIFICAR - ESTEGO AVANÇADO - CONVERSOR DE IMAGEM")
        self.root.configure(bg=BG)
        try:
            self.root.state("zoomed")
        except Exception:
            self.root.geometry("1100x900")
        self.root.minsize(700, 600)

        self.root.option_add("*Font", "Consolas 10")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TNotebook", background=BG, borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#1a1a1a", foreground=GREEN,
                             padding=[12, 6], font=("Consolas", 10, "bold"))
        self.style.map("TNotebook.Tab",
                       background=[("selected", "#003300")],
                       foreground=[("selected", GREEN)])

        self._build_header()
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # ---- Abas LSB ----
        self.tab_lsb_encode = tk.Frame(self.notebook, bg=BG)
        self.tab_lsb_decode = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_lsb_encode, text="  LSB CODIFICAR  ")
        self.notebook.add(self.tab_lsb_decode, text="  LSB DECODIFICAR  ")
        self._build_lsb_encode()
        self._build_lsb_decode()

        # ---- Aba Estego Avançado ----
        self.tab_advanced = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_advanced, text="  ESTEGO AVANÇADO  ")
        self._build_advanced_tab()

        # ---- Aba Conversor de Imagem ----
        self.tab_converter = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_converter, text="  CONVERSOR DE IMAGEM  ")
        self._build_converter_tab()

        # Status bar
        self.status = tk.Label(self.root, text="PRONTO • Selecione uma aba e comece",
                               fg=GREEN, bg="#111111", anchor="w", font=("Consolas", 10))
        self.status.pack(side=tk.BOTTOM, fill=tk.X, ipady=6, padx=8)

    def _build_header(self):
        header = tk.Frame(self.root, bg="#000000", height=90)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="ESTEGANOGRAFIA LSB CODIFICAR - LSB DECODIFICAR - ESTEGO AVANÇADO - CONVERSOR DE IMAGEM",
                 font=("Consolas", 18, "bold"), fg=GREEN, bg="#000000").pack(pady=(12, 2))
        tk.Label(header, text="LSB (Stylesuxx)  •  Blocos 8×8 Quantização de Luma  •  Detecção Automática  •  Unificado",
                 font=("Consolas", 10), fg=DIM, bg="#000000").pack()

    def update_status(self, text):
        self.status.config(text=f"[{time.strftime('%H:%M:%S')}] {text}")
        self.root.update_idletasks()

    # ==========================================================
    #  ABA 1 – LSB CODIFICAR
    # ==========================================================
    def _build_lsb_encode(self):
        frame = tk.Frame(self.tab_lsb_encode, bg=BG)
        frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=18)

        tk.Label(frame, text="SELECIONE O ALVO (IMAGEM)", font=("Consolas", 13, "bold"),
                 fg=GREEN, bg=BG).pack(anchor="w")

        self.lsb_img_path = tk.StringVar()
        path_frame = tk.Frame(frame, bg=BG)
        path_frame.pack(fill=tk.X, pady=6)
        tk.Entry(path_frame, textvariable=self.lsb_img_path, bg="#1a1a1a", fg=GREEN,
                 insertbackground=GREEN, font=("Consolas", 10)).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(path_frame, text="BROWSE", command=self._browse_lsb_encode,
                  bg="#003300", fg=GREEN, font=("Consolas", 10)).pack(side=tk.RIGHT, padx=5)

        tk.Label(frame, text="MENSAGEM A OCULTAR", font=("Consolas", 13, "bold"),
                 fg=GREEN, bg=BG).pack(anchor="w", pady=(16, 4))
        self.lsb_message = scrolledtext.ScrolledText(frame, height=11, bg="#0f0f0f",
                                                     fg=GREEN, insertbackground=GREEN,
                                                     font=("Consolas", 11))
        self.lsb_message.pack(fill=tk.BOTH, expand=True, pady=4)

        self.compat_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="🔄 Modo Compatível com Stylesuxx (RECOMENDADO)",
                       variable=self.compat_var, bg=BG, fg=GREEN, selectcolor="#003300",
                       font=("Consolas", 10), activebackground=BG, activeforeground=GREEN).pack(anchor="w", pady=6)

        out_frame = tk.Frame(frame, bg=BG)
        out_frame.pack(fill=tk.X, pady=6)
        tk.Label(out_frame, text="NOME DO ARQUIVO DE SAÍDA", fg=GREEN, bg=BG,
                 font=("Consolas", 10)).pack(anchor="w")
        self.lsb_output_name = tk.Entry(out_frame, bg="#1a1a1a", fg=GREEN, insertbackground=GREEN)
        self.lsb_output_name.insert(0, "ghost_payload.png")
        self.lsb_output_name.pack(fill=tk.X, pady=4)

        self.lsb_encode_btn = tk.Button(frame, text="EXECUTAR CODIFICAÇÃO LSB",
                                        font=("Consolas", 14, "bold"), bg="#003300", fg=GREEN,
                                        height=2, command=self._start_lsb_encode)
        self.lsb_encode_btn.pack(pady=16)

    def _browse_lsb_encode(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.lsb_img_path.set(path)

    def _start_lsb_encode(self):
        threading.Thread(target=self._do_lsb_encode, daemon=True).start()

    def _do_lsb_encode(self):
        self.lsb_encode_btn.config(state="disabled", text="PROCESSANDO...")
        self.update_status("Injetando payload LSB...")

        img_path = self.lsb_img_path.get()
        message = self.lsb_message.get("1.0", tk.END).strip()

        if not img_path or not message:
            messagebox.showerror("ERRO", "Selecione imagem e mensagem!")
            self.lsb_encode_btn.config(state="normal", text="EXECUTAR CODIFICAÇÃO LSB")
            return

        output_name = self.lsb_output_name.get().strip() or "ghost_payload.png"
        output_path = os.path.join(os.path.dirname(img_path), output_name)

        success, info = encode_lsb(img_path, message, output_path, self.compat_var.get())

        if success:
            self.update_status(f"PAYLOAD LSB INJETADO → {output_name}")
            messagebox.showinfo("SUCESSO", f"Codificado com sucesso!\n\nSalvo em\n\n{output_path}\n\n{info}")
        else:
            messagebox.showerror("FALHA", f"Erro:\n{info}")

        self.lsb_encode_btn.config(state="normal", text="EXECUTAR CODIFICAÇÃO LSB")

    # ==========================================================
    #  ABA 2 – LSB DECODIFICAR
    # ==========================================================
    def _build_lsb_decode(self):
        frame = tk.Frame(self.tab_lsb_decode, bg=BG)
        frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=18)

        tk.Label(frame, text="SELECIONE A IMAGEM COM PAYLOAD", font=("Consolas", 13, "bold"),
                 fg=GREEN, bg=BG).pack(anchor="w")

        self.lsb_decode_path = tk.StringVar()
        path_frame = tk.Frame(frame, bg=BG)
        path_frame.pack(fill=tk.X, pady=6)
        tk.Entry(path_frame, textvariable=self.lsb_decode_path, bg="#1a1a1a", fg=GREEN,
                 insertbackground=GREEN, font=("Consolas", 10)).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(path_frame, text="BROWSE", command=self._browse_lsb_decode,
                  bg="#003300", fg=GREEN, font=("Consolas", 10)).pack(side=tk.RIGHT, padx=5)

        self.lsb_decode_btn = tk.Button(frame, text="EXTRAIR MENSAGEM OCULTA (LSB)",
                                        font=("Consolas", 14, "bold"), bg="#003300", fg=GREEN,
                                        height=2, command=self._start_lsb_decode)
        self.lsb_decode_btn.pack(pady=20)

        tk.Label(frame, text="MENSAGEM EXTRAÍDA:", font=("Consolas", 12, "bold"),
                 fg=GREEN, bg=BG).pack(anchor="w")
        self.lsb_result = scrolledtext.ScrolledText(frame, height=16, bg="#0f0f0f",
                                                    fg=GREEN, font=("Consolas", 11))
        self.lsb_result.pack(fill=tk.BOTH, expand=True, pady=8)

    def _browse_lsb_decode(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.lsb_decode_path.set(path)

    def _start_lsb_decode(self):
        threading.Thread(target=self._do_lsb_decode, daemon=True).start()

    def _do_lsb_decode(self):
        self.lsb_decode_btn.config(state="disabled", text="EXTRAINDO...")
        self.update_status("Escaneando imagem (LSB)...")

        img_path = self.lsb_decode_path.get()
        if not img_path:
            messagebox.showerror("ERRO", "Selecione uma imagem!")
            self.lsb_decode_btn.config(state="normal", text="EXTRAIR MENSAGEM OCULTA (LSB)")
            return

        message = decode_lsb_compatible(img_path)

        self.lsb_result.delete("1.0", tk.END)
        if message and len(message.strip()) > 5:
            self.lsb_result.insert(tk.END, message)
            self.update_status("PAYLOAD LSB EXTRAÍDO COM SUCESSO")
            messagebox.showinfo("SUCESSO", "Mensagem recuperada!")
        else:
            self.lsb_result.insert(tk.END, "Nenhum payload claro detectado.")
            messagebox.showwarning("AVISO", "Não foi possível extrair uma mensagem clara.")

        self.lsb_decode_btn.config(state="normal", text="EXTRAIR MENSAGEM OCULTA (LSB)")

    # ==========================================================
    #  ABA 3 – ESTEGO AVANÇADO
    # ==========================================================
    def _build_advanced_tab(self):
        term = tk.Frame(self.tab_advanced, bg=PANEL, highlightthickness=1,
                        highlightbackground=GREEN, highlightcolor=GREEN)
        term.pack(expand=True, fill="both", padx=20, pady=16)

        tk.Label(term, text="Esteganografia de Imagens Oculta (Avançado)",
                 font=mono_font(14, True), bg=PANEL, fg=GREEN).pack(anchor="w")
        tk.Label(term, text=f"Oculte mensagens secretas • 1024×1024 • blocos 8×8 • ~{MAX_BYTES} bytes max",
                 font=mono_font(9), bg=PANEL, fg=DIM).pack(anchor="w", pady=(0, 12))

        # imagem
        row = tk.Frame(term, bg=PANEL)
        row.pack(fill="x")
        tk.Label(row, text="imagem", font=mono_font(11, True), bg=PANEL, fg=DIM,
                 width=8, anchor="w").pack(side="left")
        self.adv_select_btn = self._make_btn(row, "selecionar", self._adv_select_file)
        self.adv_select_btn.pack(side="left")
        self.adv_filename = tk.StringVar(value="nenhuma")
        tk.Label(row, textvariable=self.adv_filename, font=mono_font(10),
                 bg=PANEL, fg=DIM, anchor="w").pack(side="left", padx=10)

        # DETECÇÃO AUTOMÁTICA (painel de resultado ao carregar a imagem)
        self.adv_detect_label = tk.Label(term, text="detecção automática: aguardando imagem...",
                                         font=mono_font(9), bg=PANEL, fg=DIM,
                                         anchor="w", justify="left", wraplength=980)
        self.adv_detect_label.pack(fill="x", pady=(4, 0))
        self._adv_detect_serial = 0

        # mensagem
        tk.Label(term, text="mensagem", font=mono_font(11, True), bg=PANEL,
                 fg=DIM, anchor="w").pack(anchor="w", pady=(12, 2))
        self.adv_msg = tk.Text(term, height=5, wrap="word", font=mono_font(11),
                               bg="#111111", fg=GREEN, insertbackground=GREEN,
                               relief="flat", bd=0, highlightthickness=1,
                               highlightbackground=EDGE, highlightcolor=GREEN,
                               selectbackground=GREEN, selectforeground=BG,
                               padx=10, pady=8)
        self.adv_msg.pack(fill="x")

        # Feedback em tempo real
        self.adv_msg.bind("<KeyRelease>", self._check_capacity)
        self.adv_msg.bind("<ButtonRelease>", self._check_capacity)

        # robustez / capacidade (mais robustez = menos bytes, mais proteção)
        rob = tk.Frame(term, bg=PANEL)
        rob.pack(fill="x", pady=(10, 0))
        tk.Label(rob, text="robustez", font=mono_font(10, True), bg=PANEL,
                 fg=DIM, width=8, anchor="w").pack(side="left")
        self.adv_repeat_var = tk.StringVar(value="7")
        self.adv_repeat_menu = tk.OptionMenu(rob, self.adv_repeat_var, "7", "5", "3",
                                             command=self._adv_on_repeat_change)
        self.adv_repeat_menu.config(bg=BTN_BG, fg=GREEN, activebackground=GREEN,
                                    activeforeground=BG, relief="solid", bd=1,
                                    highlightthickness=0, font=mono_font(10, True))
        self.adv_repeat_menu["menu"].config(bg=BTN_BG, fg=GREEN,
                                            activebackground=GREEN, activeforeground=BG,
                                            font=mono_font(10))
        self.adv_repeat_menu.pack(side="left")
        self.adv_capacity_label = tk.Label(
            rob, text=f"capacidade atual: {MAX_BYTES} bytes (utf-8) · repetição 7× · use a MESMA robustez para extrair",
            font=mono_font(9), bg=PANEL, fg=DIM)
        self.adv_capacity_label.pack(side="left", padx=10)

        # robustez VISUAL (Q_STEP): mais alto = sobrevive melhor a JPEG/redes sociais
        qrow = tk.Frame(term, bg=PANEL)
        qrow.pack(fill="x", pady=(6, 0))
        tk.Label(qrow, text="resistência", font=mono_font(10, True), bg=PANEL,
                 fg=DIM, width=8, anchor="w").pack(side="left")
        
        self.adv_qstep_var = tk.StringVar(value="4")
        self.adv_qstep_menu = tk.OptionMenu(qrow, self.adv_qstep_var,
                                            "4", "8", "12", "20", "32", "48", "64",
                                            command=self._adv_on_qstep_change)
        
        self.adv_qstep_menu.config(bg=BTN_BG, fg=GREEN, activebackground=GREEN,
                                   activeforeground=BG, relief="solid", bd=1,
                                   highlightthickness=0, font=mono_font(10, True))
        self.adv_qstep_menu["menu"].config(bg=BTN_BG, fg=GREEN,
                                           activebackground=GREEN, activeforeground=BG,
                                           font=mono_font(10))
        self.adv_qstep_menu.pack(side="left")
        self.adv_qstep_label = tk.Label(
            qrow,
            text="4 = sutil (só PNG sem perdas)  ·  8/12 = JPEG leve  ·  20 = redes sociais (visível)",
            font=mono_font(9), bg=PANEL, fg=DIM)
        self.adv_qstep_label.pack(side="left", padx=10)

        # botões
        act = tk.Frame(term, bg=PANEL)
        act.pack(fill="x", pady=(12, 0))
        self.adv_encode_btn = self._make_btn(act, "Ocultar Mensagem", self._adv_on_encode)
        self.adv_decode_btn = self._make_btn(act, "Extrair Mensagem", self._adv_on_decode)
        self.adv_sim_btn = self._make_btn(act, "SIMULAR REDE SOCIAL (teste JPEG)", self._adv_on_simulate)
        self.adv_encode_btn.pack(side="left", expand=True, fill="x")
        self.adv_decode_btn.pack(side="left", expand=True, fill="x", padx=(10, 0))
        self.adv_sim_btn.pack(side="left", expand=True, fill="x", padx=(10, 0))

        # status interno
        tk.Frame(term, bg="#1a1a1a", height=1).pack(fill="x", pady=(12, 8))
        self.adv_status = tk.Label(term, text="pronto", font=mono_font(10),
                                   bg=PANEL, fg=NORMAL, anchor="w", justify="left")
        self.adv_status.pack(fill="x")
        tk.Label(term, text=f"* saída png · 1024×1024 · ~{MAX_BYTES} bytes máx (utf-8)",
                 font=mono_font(8), bg=PANEL, fg="#3d6b4f").pack(anchor="w", pady=(2, 0))

        # preview
        prev_frame = tk.Frame(term, bg=PANEL)
        prev_frame.pack(pady=(10, 0))
        self.adv_preview = tk.Label(prev_frame, bg=PANEL, text="(sem imagem)",
                                    font=mono_font(9), fg=DIM)
        self.adv_preview.pack()

        self.adv_current_image = None
        self.adv_preview_photo = None

    def _make_btn(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, command=cmd, font=mono_font(11, True),
                        bg=BTN_BG, fg=GREEN, activebackground=GREEN,
                        activeforeground=BG, relief="solid", bd=1,
                        cursor="hand2", padx=14, pady=5)
        btn.bind("<Enter>", lambda e: btn.config(bg=GREEN, fg=BG)
                 if str(btn["state"]) == "normal" else None)
        btn.bind("<Leave>", lambda e: btn.config(bg=BTN_BG, fg=GREEN))
        return btn

    def _check_capacity(self, event=None):
        msg = self.adv_msg.get("1.0", "end-1c")
        text_bytes = len(msg.encode("utf-8"))
        lines = msg.count("\n") + 1 if msg.strip() else 0
        avg_chars = 50
        max_lines = MAX_BYTES // avg_chars

        if not msg.strip():
            self.adv_status.config(text="pronto", fg=NORMAL)
            return

        if text_bytes > MAX_BYTES:
            excess = text_bytes - MAX_BYTES
            self.adv_status.config(
                text=f"NÃO CABE  ·  {text_bytes} bytes  ·  {lines} linhas  ·  excesso: {excess} bytes  (máx ~{max_lines} linhas)",
                fg=ERR
            )
        else:
            remaining = MAX_BYTES - text_bytes
            self.adv_status.config(
                text=f"ok  ·  {text_bytes}/{MAX_BYTES} bytes  ·  {lines} linhas  ·  sobram {remaining} bytes",
                fg=OK
            )

    def _adv_status(self, text, kind=""):
        color = {"error": ERR, "success": OK}.get(kind, NORMAL)
        self.adv_status.config(text=text, fg=color)
        self.update_status(text)

    def _adv_set_busy(self, busy):
        state = "disabled" if busy else "normal"
        for b in (self.adv_select_btn, self.adv_encode_btn, self.adv_decode_btn, self.adv_sim_btn):
            b.config(state=state)
            b.config(bg=BTN_BG, fg=GREEN_D if busy else GREEN)
        try:
            self.adv_repeat_menu.config(state=state)
            self.adv_qstep_menu.config(state=state)
        except Exception:
            pass

    def _adv_update_preview(self, img):
        preview = img.copy()
        preview.thumbnail((PREVIEW_MAX, PREVIEW_MAX), RESAMPLE)
        self.adv_preview_photo = ImageTk.PhotoImage(preview)
        self.adv_preview.config(image=self.adv_preview_photo, text="")

    def _adv_runner(self, work, done, fail):
        def worker():
            try:
                result = work()
            except Exception as e:
                self.root.after(0, fail, e)
            else:
                self.root.after(0, done, result)
        threading.Thread(target=worker, daemon=True).start()

    def _adv_select_file(self):
        path = filedialog.askopenfilename(
            title="selecionar imagem",
            filetypes=[("imagens", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tiff"),
                       ("todos os arquivos", "*.*")])
        if not path:
            return
        try:
            img = Image.open(path)
            img.load()
        except Exception:
            self._adv_status("imagem inválida", "error")
            return
        self.adv_current_image = img
        self.adv_filename.set(os.path.basename(path))
        self._adv_update_preview(img)
        self._adv_status(f"imagem carregada · {img.width}x{img.height} · verificando mensagem oculta...", "")
        self._adv_auto_detect()

    def _adv_auto_detect(self):
        """Detecta automaticamente se a imagem carregada tem mensagem oculta."""
        if self.adv_current_image is None:
            return
        self._adv_detect_serial += 1
        serial = self._adv_detect_serial
        self.adv_detect_label.config(text="verificando se há mensagem oculta...", fg=NORMAL)

        def work():
            return decode_image_advanced(self.adv_current_image)

        def done(text):
            if serial != self._adv_detect_serial:
                return
            if text:
                preview_txt = text if len(text) <= 90 else text[:90] + "..."
                self.adv_detect_label.config(
                    text=f"✔ MENSAGEM OCULTA DETECTADA ({len(text)} caracteres): {preview_txt!r}",
                    fg=OK, wraplength=980, justify="left")
                self._adv_status(f"mensagem oculta detectada automaticamente ({len(text)} caracteres)", "success")
            else:
                self.adv_detect_label.config(
                    text="✘ sem mensagem oculta detectada (imagem limpa, ou mensagem corrompida / robustez diferente)",
                    fg=DIM, wraplength=980, justify="left")
                self._adv_status("sem mensagem oculta detectada", "")

        def fail(err):
            if serial != self._adv_detect_serial:
                return
            self.adv_detect_label.config(text="erro na detecção: " + str(err), fg=ERR,
                                         wraplength=980, justify="left")

        self._adv_runner(work, done, fail)

    def _adv_on_encode(self):
        if self.adv_current_image is None:
            self._adv_status("nenhuma imagem selecionada", "error")
            return

        msg = self.adv_msg.get("1.0", "end-1c")
        if not msg.strip():
            self._adv_status("digite a mensagem", "error")
            return

        # Bloqueia se estiver acima do limite
        text_bytes = len(msg.encode("utf-8"))
        if text_bytes > MAX_BYTES:
            lines = msg.count("\n") + 1
            excess = text_bytes - MAX_BYTES
            error_msg = (
                f"NÃO CABE\n\n"
                f"Tamanho do texto:   {text_bytes} bytes\n"
                f"Linhas no texto:    {lines}\n"
                f"Capacidade máxima:  {MAX_BYTES} bytes\n"
                f"Linhas aproximadas: ~{MAX_BYTES // 50} linhas (média de 50 chars)\n\n"
                f"Excede em {excess} bytes"
            )
            messagebox.showerror("NÃO CABE", error_msg)
            return

        self._adv_set_busy(True)
        self._adv_status("codificando...", "")
        self.root.update_idletasks()

        def work():
            out = encode_image_advanced(self.adv_current_image, msg)
            recovered = decode_image_advanced(out)   # verificação automática: ida e volta
            return out, recovered == msg

        def done(result):
            out, verified = result
            path = filedialog.asksaveasfilename(
                title="salvar imagem codificada", defaultextension=".png",
                initialfile="estego.png", filetypes=[("imagem PNG", "*.png")])
            if path:
                out.save(path, "PNG")
                self.adv_current_image = out
                self.adv_filename.set(os.path.basename(path))
                self._adv_update_preview(out)
                if verified:
                    self._adv_status(f"codificado e VERIFICADO → {os.path.basename(path)}", "success")
                    self.adv_detect_label.config(
                        text=f"✔ MENSAGEM OCULTA DETECTADA ({len(msg)} caracteres): {msg[:90]!r}",
                        fg=OK, wraplength=980, justify="left")
                else:
                    self._adv_status("ATENÇÃO: verificação falhou — a extração não vai funcionar", "error")
                    messagebox.showwarning(
                        "VERIFICAÇÃO FALHOU",
                        "Após codificar, a mensagem NÃO foi recuperada.\n\n"
                        "Dica: converta a imagem na aba CONVERSOR DE IMAGEM (PNG 1024×1024)\n"
                        "e carregue ESSE arquivo no ESTEGO AVANÇADO antes de codificar.")
            else:
                self._adv_status("salvamento cancelado", "")
            self._adv_set_busy(False)

        def fail(err):
            self._adv_status("erro: " + str(err), "error")
            self._adv_set_busy(False)

        self._adv_runner(work, done, fail)

    def _adv_on_decode(self):
        if self.adv_current_image is None:
            self._adv_status("nenhuma imagem selecionada", "error")
            return
        self._adv_set_busy(True)
        self._adv_status("decodificando...", "")
        self.root.update_idletasks()

        def done(text):
            if text is None or text == "":
                self._adv_status("nenhuma mensagem encontrada ou corrompida — dica: converta no CONVERSOR e codifique com a MESMA robustez", "error")
            else:
                self.adv_msg.delete("1.0", "end")
                self.adv_msg.insert("1.0", text)
                self._adv_status("mensagem extraída", "success")
                self.adv_detect_label.config(
                    text=f"✔ MENSAGEM OCULTA DETECTADA ({len(text)} caracteres): {text[:90]!r}",
                    fg=OK, wraplength=980, justify="left")
                self._check_capacity()
            self._adv_set_busy(False)

        def fail(err):
            self._adv_status("erro: " + str(err), "error")
            self._adv_set_busy(False)

        self._adv_runner(lambda: decode_image_advanced(self.adv_current_image), done, fail)

    def _adv_on_repeat_change(self, value=None):
        global REPEAT, MAX_BYTES
        try:
            REPEAT = int(str(self.adv_repeat_var.get()))
        except Exception:
            return
        MAX_BYTES = ((ENCODE_W // BS) * (ENCODE_H // BS) // REPEAT - 24) // 8
        self.adv_capacity_label.config(
            text=f"capacidade atual: {MAX_BYTES} bytes (utf-8) · repetição {REPEAT}× · use a MESMA robustez para extrair")
        self._check_capacity()

    def _adv_on_qstep_change(self, value=None):
        global Q_STEP
        try:
            Q_STEP = int(str(self.adv_qstep_var.get()))
        except Exception:
            return
        
        label_map = {4: "sutil (só PNG)", 8: "JPEG leve", 12: "JPEG médio",
             20: "forte (redes sociais)", 32: "extremo 1", 48: "extremo 2",
             64: "brutal (visível)"}
        
        self.adv_qstep_label.config(
            text=f"Q_STEP={Q_STEP} · {label_map.get(Q_STEP, '')} · use a MESMA resistência para extrair")
        self._adv_status(f"robustez visual alterada para Q_STEP={Q_STEP}", "")

    def _adv_on_simulate(self):
        """Simula o re-encode de uma rede social (JPEG q80) e verifica se a mensagem sobrevive."""
        if self.adv_current_image is None:
            self._adv_status("nenhuma imagem selecionada", "error")
            return
        msg = self.adv_msg.get("1.0", "end-1c")
        if not msg.strip():
            self._adv_status("digite a mensagem primeiro", "error")
            return
        if len(msg.encode("utf-8")) > MAX_BYTES:
            self._adv_status("mensagem não cabe (veja o limite de robustez)", "error")
            return

        self._adv_set_busy(True)
        self._adv_status("simulando rede social (JPEG qualidade 80)...", "")

        def work():
            out = encode_image_advanced(self.adv_current_image, msg)
            # simula o que FB/IG fazem: reconverter para JPEG com perdas
            import io
            buf = io.BytesIO()
            out.save(buf, "JPEG", quality=80, subsampling=0)
            buf.seek(0)
            recompressed = Image.open(buf).convert("RGB")
            recovered = decode_image_advanced(recompressed)
            return recovered, recovered == msg

        def done(result):
            recovered, ok = result
            if ok:
                self._adv_status(
                    f"✔ SOBREVIVEU à simulação (Q_STEP={Q_STEP}, JPEG q80). Pode postar!", "success")
                messagebox.showinfo("SIMULAÇÃO OK",
                                    f"A mensagem sobreviveu ao re-encode de rede social "
                                    f"(Q_STEP={Q_STEP}, JPEG qualidade 80).\n\n"
                                    f"Mensagem recuperada: {recovered!r}")
            else:
                self._adv_status(
                    "✘ NÃO sobreviveu. Aumente a 'resistência' para 20, 32 ou 48 e tente de novo.", "error")
                messagebox.showerror(
                    "SIMULAÇÃO FALHOU",
                    "A mensagem foi DESTRUÍDA pelo re-encode JPEG.\n\n"
                    "Isso é o que acontece no Facebook/Instagram.\n\n"
                    "Solução:\n"
                    "1. Aumente a resistência para 20, 32 ou 48 (seletor no ESTEGO AVANÇADO)\n"
                    "2. Codifique de novo e rode SIMULAR REDE SOCIAL\n"
                    "3. Só poste quando aparecer 'SOBREVIVEU'\n\n"
                    f"(recuperado após JPEG: {recovered!r})")
            self._adv_set_busy(False)

        def fail(err):
            self._adv_status("erro: " + str(err), "error")
            self._adv_set_busy(False)

        self._adv_runner(work, done, fail)

    # ==========================================================
    #  ABA 4 – CONVERSOR / NORMALIZADOR DE IMAGEM
    # ==========================================================
    def _build_converter_tab(self):
        term = tk.Frame(self.tab_converter, bg=PANEL, highlightthickness=1,
                        highlightbackground=GREEN, highlightcolor=GREEN)
        term.pack(expand=True, fill="both", padx=20, pady=16)

        tk.Label(term, text="Conversor de Imagem → Formato do ESTEGO AVANÇADO",
                 font=mono_font(14, True), bg=PANEL, fg=GREEN).pack(anchor="w")
        tk.Label(term,
                 text="Converte QUALQUER imagem para 1024×1024 RGB PNG (PNG sem perdas = extração SEM erro)",
                 font=mono_font(9), bg=PANEL, fg=DIM).pack(anchor="w", pady=(0, 12))

        row = tk.Frame(term, bg=PANEL)
        row.pack(fill="x")
        tk.Label(row, text="imagem", font=mono_font(11, True), bg=PANEL, fg=DIM,
                 width=8, anchor="w").pack(side="left")
        self.conv_select_btn = self._make_btn(row, "selecionar", self._conv_select_file)
        self.conv_select_btn.pack(side="left")
        self.conv_filename = tk.StringVar(value="nenhuma")
        tk.Label(row, textvariable=self.conv_filename, font=mono_font(10),
                 bg=PANEL, fg=DIM, anchor="w").pack(side="left", padx=10)

        self.conv_info = tk.Label(term, text="—", font=mono_font(10), bg=PANEL,
                                  fg=NORMAL, anchor="w", justify="left")
        self.conv_info.pack(fill="x", pady=(8, 0))

        prevs = tk.Frame(term, bg=PANEL)
        prevs.pack(fill="x", pady=(10, 0))
        col1 = tk.Frame(prevs, bg=PANEL)
        col1.pack(side="left", expand=True, fill="x")
        col2 = tk.Frame(prevs, bg=PANEL)
        col2.pack(side="left", expand=True, fill="x", padx=(12, 0))
        tk.Label(col1, text="ORIGINAL", font=mono_font(9, True), bg=PANEL, fg=DIM).pack()
        self.conv_preview_orig = tk.Label(col1, bg=PANEL, text="(sem imagem)",
                                          font=mono_font(9), fg=DIM)
        self.conv_preview_orig.pack()
        tk.Label(col2, text="NORMALIZADA 1024×1024", font=mono_font(9, True),
                 bg=PANEL, fg=DIM).pack()
        self.conv_preview_norm = tk.Label(col2, bg=PANEL, text="(sem imagem)",
                                          font=mono_font(9), fg=DIM)
        self.conv_preview_norm.pack()

        act = tk.Frame(term, bg=PANEL)
        act.pack(fill="x", pady=(14, 0))
        self.conv_convert_btn = self._make_btn(act, "CONVERTER E SALVAR PNG (1024×1024)", self._conv_on_convert)
        self.conv_convert_btn.pack(side="left", expand=True, fill="x")
        self.conv_test_btn = self._make_btn(act, "TESTAR IDA E VOLTA (encode+decode)", self._conv_on_test)
        self.conv_test_btn.pack(side="left", expand=True, fill="x", padx=(10, 0))

        tk.Frame(term, bg="#1a1a1a", height=1).pack(fill="x", pady=(12, 8))
        self.conv_status = tk.Label(term, text="pronto — converta primeiro, depois use no ESTEGO AVANÇADO",
                                    font=mono_font(10), bg=PANEL, fg=NORMAL, anchor="w", justify="left")
        self.conv_status.pack(fill="x")

        self.conv_original = None
        self.conv_normalized = None
        self.conv_photo_orig = None
        self.conv_photo_norm = None

    def _conv_status(self, text, kind=""):
        color = {"error": ERR, "success": OK}.get(kind, NORMAL)
        self.conv_status.config(text=text, fg=color)
        self.update_status(text)

    def _conv_set_busy(self, busy):
        state = "disabled" if busy else "normal"
        for b in (self.conv_select_btn, self.conv_convert_btn, self.conv_test_btn):
            b.config(state=state)
            b.config(bg=BTN_BG, fg=GREEN_D if busy else GREEN)

    def _conv_select_file(self):
        path = filedialog.askopenfilename(
            title="selecionar imagem (qualquer formato)",
            filetypes=[("imagens", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tiff"),
                       ("todos os arquivos", "*.*")])
        if not path:
            return
        try:
            img = Image.open(path)
            img.load()
            fmt = img.format
        except Exception:
            self._conv_status("imagem inválida ou corrompida", "error")
            return
        self.conv_original = img
        self.conv_filename.set(os.path.basename(path))
        self.conv_info.config(
            text=f"original: {img.width}×{img.height}  ·  modo: {img.mode}  ·  formato: {fmt}\n"
                 f"alvo: 1024×1024 RGB  ·  saída: PNG (sem perdas)")
        self._conv_update_previews()
        self._conv_status("imagem carregada — clique em CONVERTER E SALVAR PNG", "success")

    def _conv_update_previews(self):
        if self.conv_original is None:
            return
        po = self.conv_original.copy()
        po.thumbnail((PREVIEW_MAX, PREVIEW_MAX), RESAMPLE)
        self.conv_photo_orig = ImageTk.PhotoImage(po)
        self.conv_preview_orig.config(image=self.conv_photo_orig, text="")
        if self.conv_normalized is not None:
            pn = self.conv_normalized.copy()
            pn.thumbnail((PREVIEW_MAX, PREVIEW_MAX), RESAMPLE)
            self.conv_photo_norm = ImageTk.PhotoImage(pn)
            self.conv_preview_norm.config(image=self.conv_photo_norm, text="")

    def _conv_on_convert(self):
        if self.conv_original is None:
            self._conv_status("nenhuma imagem selecionada", "error")
            return
        self._conv_set_busy(True)
        self._conv_status("normalizando para 1024×1024...", "")

        def work():
            return _prepare(self.conv_original)   # mesma normalização do ESTEGO AVANÇADO

        def done(norm):
            self.conv_normalized = norm
            self._conv_update_previews()
            path = filedialog.asksaveasfilename(
                title="salvar imagem normalizada (PNG)",
                defaultextension=".png", initialfile="normalizada_1024.png",
                filetypes=[("imagem PNG", "*.png")])
            if path:
                norm.save(path, "PNG")
                self._conv_status(
                    f"CONVERTIDO → {os.path.basename(path)}  (1024×1024 RGB PNG — use no ESTEGO AVANÇADO)",
                    "success")
            else:
                self._conv_status("salvamento cancelado — imagem já normalizada na memória (use TESTAR)", "")
            self._conv_set_busy(False)

        def fail(err):
            self._conv_status("erro: " + str(err), "error")
            self._conv_set_busy(False)

        self._adv_runner(work, done, fail)

    def _conv_on_test(self):
        if self.conv_original is None:
            self._conv_status("nenhuma imagem selecionada", "error")
            return
        self._conv_set_busy(True)
        self._conv_status("testando: normalizar → ocultar → extrair...", "")

        def work():
            norm = _prepare(self.conv_original)
            sample = "TESTE IDA E VOLTA OK - esteganografia funcionando nesta imagem"
            enc = encode_image_advanced(norm, sample)
            dec = decode_image_advanced(enc)
            return norm, (dec == sample), dec

        def done(result):
            norm, ok, dec = result
            self.conv_normalized = norm
            self._conv_update_previews()
            if ok:
                self._conv_status("TESTE OK - mensagem ocultada e extraída SEM erro (PNG sem perdas)", "success")
            else:
                self._conv_status(f"TESTE FALHOU - recuperado: {dec!r}", "error")
            self._conv_set_busy(False)

        def fail(err):
            self._conv_status("erro: " + str(err), "error")
            self._conv_set_busy(False)

        self._adv_runner(work, done, fail)


# ============================================================
#  MAIN
# ============================================================
def main():
    try:
        import numpy  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError as e:
        raise SystemExit(f"Dependência faltando: {e}\n→ pip install pillow numpy")

    root = tk.Tk()
    UnifiedStegoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
