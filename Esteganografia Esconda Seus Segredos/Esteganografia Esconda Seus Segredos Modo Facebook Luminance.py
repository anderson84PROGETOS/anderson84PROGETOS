#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════╗
║  ESTEGANOGRAFIA - Esconda Seus Segredos                                    ║
║  + MODO FACEBOOK INDESTRUTÍVEL (QIM Luminance YCbCr + Redundância 5x)      ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import hashlib
import struct
import threading
import time
import math
import zlib
from pathlib import Path
import platform

try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps
    import numpy as np
    PIL_DISPONIVEL = True
except ImportError:
    PIL_DISPONIVEL = False


# ========================== MOTOR LSB OFFLINE ==========================

class MotorEsteganografia:
    CABECALHO_MAGICO = b'ZSTEG'
    VERSAO = b'\x02'
    TIPO_TEXTO = 0x01
    TIPO_TEXTO_CRIPTOGRAFADO = 0x03

    @staticmethod
    def _criptografar_xor(dados, senha):
        chave = hashlib.sha256(senha.encode()).digest()
        return bytes([b ^ chave[i % len(chave)] for i, b in enumerate(dados)])

    @staticmethod
    def _bytes_para_bits(dados):
        bits = []
        for byte in dados:
            for i in range(8):
                bits.append((byte >> i) & 1)
        return bits

    @staticmethod
    def _bits_para_bytes(bits):
        resultado = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                if i + j < len(bits):
                    byte |= (bits[i + j] << j)
            resultado.append(byte)
        return bytes(resultado)

    @staticmethod
    def codificar_texto(caminho_imagem, caminho_saida, texto, senha=None, callback=None):
        img = Image.open(caminho_imagem).convert('RGB')
        pixels = np.array(img)
        dados = texto.encode('utf-8')
        tipo = MotorEsteganografia.TIPO_TEXTO
        if senha:
            dados = MotorEsteganografia._criptografar_xor(dados, senha)
            tipo = MotorEsteganografia.TIPO_TEXTO_CRIPTOGRAFADO
        carga = bytearray(MotorEsteganografia.CABECALHO_MAGICO + MotorEsteganografia.VERSAO)
        carga.append(tipo)
        carga.extend(struct.pack('<I', len(dados)))
        carga.extend(struct.pack('<I', 0))
        carga.extend(dados)
        bits = MotorEsteganografia._bytes_para_bits(bytes(carga))
        pixels_planos = pixels.flatten()
        if len(bits) > len(pixels_planos):
            raise ValueError("Imagem muito pequena para LSB!")
        for i, bit in enumerate(bits):
            pixels_planos[i] = (pixels_planos[i] & 0xFE) | bit
            if callback and i % 10000 == 0:
                callback(i / len(bits) * 100)
        pixels = pixels_planos.reshape(pixels.shape)
        Image.fromarray(pixels.astype('uint8'), 'RGB').save(caminho_saida, 'PNG')
        if callback: callback(100)
        return True

    @staticmethod
    def decodificar(caminho_imagem, senha=None, callback=None):
        img = Image.open(caminho_imagem).convert('RGB')
        pixels_planos = np.array(img).flatten()
        bits_cabecalho = [pixels_planos[i] & 1 for i in range(120)]
        bytes_cab = MotorEsteganografia._bits_para_bytes(bits_cabecalho)
        if bytes_cab[:5] != MotorEsteganografia.CABECALHO_MAGICO:
            raise ValueError("Nenhum dado LSB encontrado!")
        tipo = bytes_cab[6]
        tam_dados = struct.unpack('<I', bytes_cab[7:11])[0]
        tam_nome = struct.unpack('<I', bytes_cab[11:15])[0]
        total_bits = (15 + tam_nome + tam_dados) * 8
        if total_bits > len(pixels_planos):
            raise ValueError("Dados LSB corrompidos!")
        todos_bits = []
        for i in range(total_bits):
            todos_bits.append(pixels_planos[i] & 1)
            if callback and i % 10000 == 0:
                callback(i / total_bits * 100)
        todos_bytes = MotorEsteganografia._bits_para_bytes(todos_bits)
        dados = todos_bytes[15+tam_nome:15+tam_nome+tam_dados]
        cripto = tipo == MotorEsteganografia.TIPO_TEXTO_CRIPTOGRAFADO
        if cripto:
            if not senha:
                raise ValueError("Mensagem criptografada! Digite a senha.")
            dados = MotorEsteganografia._criptografar_xor(dados, senha)
        if callback: callback(100)
        return {'texto': dados.decode('utf-8', errors='ignore'), 'tamanho': tam_dados}


# ========================== MOTOR FACEBOOK INDESTRUTÍVEL ==========================

class MotorFacebook:
    """
    Motor QIM baseado no canal de LUMINOSIDADE (Y do espaço YCbCr).
    Usa Redundância Quíntupla (5x) e Quantização Q=56.
    Resistente ao algoritmo de compressão JPEG do Facebook e Messenger.
    """
    SYNC_WORD = [1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1] # 24 bits Sync

    @staticmethod
    def _criptografar_xor(dados, senha):
        chave = hashlib.sha256(senha.encode()).digest()
        return bytes([b ^ chave[i % len(chave)] for i, b in enumerate(dados)])

    @staticmethod
    def _aplicar_repeticao_5x(bits):
        """Cada bit é repetido 5 vezes para votação de maioria absoluta"""
        res = []
        for b in bits:
            res.extend([b] * 5)
        return res

    @staticmethod
    def _decodificar_repeticao_5x(bits):
        """Votação de maioria em blocos de 5 bits (se 3 ou mais forem 1, é 1)"""
        res = []
        for i in range(0, len(bits) - 4, 5):
            soma = bits[i] + bits[i+1] + bits[i+2] + bits[i+3] + bits[i+4]
            res.append(1 if soma >= 3 else 0)
        return res

    @staticmethod
    def otimizar_para_facebook(caminho, saida, formato="1200x630"):
        img = Image.open(caminho).convert('RGB')
        if formato == "1200x630":
            target_w, target_h = (1200, 630)
        elif formato == "1080x1350":
            target_w, target_h = (1080, 1350)
        else:
            target_w, target_h = (1200, 1200)
        
        # Crop e Fit mantendo proporção sem achatar
        img = ImageOps.fit(img, (target_w, target_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        
        # Aumento sutil de nitidez para combater a compressão agressiva
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)
        img.save(saida, 'PNG')
        return img.size

    @staticmethod
    def codificar_facebook(caminho_imagem, caminho_saida, texto, senha=None, tam_bloco=8, intensidade=56, callback=None):
        img_rgb = Image.open(caminho_imagem).convert('RGB')
        
        # Converter para YCbCr para alterar APENAS o Brilho (Y)
        img_ycbcr = img_rgb.convert('YCbCr')
        y, cb, cr = img_ycbcr.split()
        
        pixels_y = np.array(y, dtype=np.float32)
        largura, altura = img_rgb.size

        dados_texto = texto.encode('utf-8')
        dados_comprimidos = zlib.compress(dados_texto, 9)
        
        if senha:
            dados_comprimidos = MotorFacebook._criptografar_xor(dados_comprimidos, senha)
            
        payload = (b'\x01' if senha else b'\x00') + dados_comprimidos
        if len(payload) > 32000:
            raise ValueError("Texto muito grande! Escreva uma mensagem menor.")

        tam_bits = [(len(payload) >> i) & 1 for i in range(16)]
        payload_bits = [(byte >> i) & 1 for byte in payload for i in range(8)]

        # Bitstream = SYNC + Tamanho(5x) + Dados(5x)
        bitstream = (MotorFacebook.SYNC_WORD +
                     MotorFacebook._aplicar_repeticao_5x(tam_bits) +
                     MotorFacebook._aplicar_repeticao_5x(payload_bits))

        blocos_x = largura // tam_bloco
        blocos_y = altura // tam_bloco
        total_blocos = blocos_x * blocos_y

        if len(bitstream) > total_blocos:
            raise ValueError(f"Imagem pequena! Precisa de {len(bitstream)} blocos. Disponível: {total_blocos}")

        Q = float(intensidade)
        total_bits = len(bitstream)

        # Aplicar QIM na Luminosidade (Y)
        for idx, bit in enumerate(bitstream):
            bx = idx % blocos_x
            by = idx // blocos_x
            x_i, y_i = bx * tam_bloco, by * tam_bloco
            
            bloco_y = pixels_y[y_i:y_i+tam_bloco, x_i:x_i+tam_bloco]
            media_y = float(bloco_y.mean())

            # Quantização QIM em Y
            k = math.floor((media_y - (bit * Q / 2.0)) / Q + 0.5)
            nova_media_y = k * Q + (bit * Q / 2.0)
            
            diff = nova_media_y - media_y
            pixels_y[y_i:y_i+tam_bloco, x_i:x_i+tam_bloco] = np.clip(bloco_y + diff, 0, 255)

            if callback and idx % 500 == 0:
                callback(idx / total_bits * 100)

        # Reconstruir imagem YCbCr -> RGB
        y_mod = Image.fromarray(np.uint8(pixels_y), mode='L')
        img_final = Image.merge('YCbCr', (y_mod, cb, cr)).convert('RGB')
        img_final.save(caminho_saida, 'PNG')

        if callback: callback(100)
        return {'bits_usados': total_bits, 'bytes_comprimidos': len(payload)}

    @staticmethod
    def decodificar_facebook(caminho_imagem, senha=None, tam_bloco=8, intensidade=56, callback=None):
        img_rgb = Image.open(caminho_imagem).convert('RGB')
        img_ycbcr = img_rgb.convert('YCbCr')
        y, _, _ = img_ycbcr.split()
        
        pixels_y = np.array(y, dtype=np.float32)
        largura, altura = img_rgb.size

        blocos_x = largura // tam_bloco
        blocos_y = altura // tam_bloco

        bits_extraidos = []
        Q = float(intensidade)

        if callback: callback(15)

        # Extração QIM da Luminosidade
        for by in range(blocos_y):
            for bx in range(blocos_x):
                x_i, y_i = bx * tam_bloco, by * tam_bloco
                bloco_y = pixels_y[y_i:y_i+tam_bloco, x_i:x_i+tam_bloco]
                media_y = float(bloco_y.mean())

                # Distância para bit 0 e bit 1
                dist_0 = abs(media_y - (math.floor(media_y / Q + 0.5) * Q))
                dist_1 = abs(media_y - (math.floor((media_y - Q/2.0) / Q + 0.5) * Q + Q/2.0))

                bits_extraidos.append(0 if dist_0 < dist_1 else 1)

        if callback: callback(45)

        # Localizar SYNC WORD
        start_idx = -1
        sync_len = len(MotorFacebook.SYNC_WORD)

        for i in range(len(bits_extraidos) - sync_len):
            erros = sum(1 for a, b in zip(bits_extraidos[i:i+sync_len], MotorFacebook.SYNC_WORD) if a != b)
            if erros <= 5: # Aceita até 5 bits errados na sincronicidade causada pelo JPEG do FB
                start_idx = i + sync_len
                break

        if start_idx == -1:
            raise ValueError("Sinal não encontrado. Verifique se a foto é a correta.")

        # Ler Tamanho (16 bits * 5 repetições = 80 bits)
        if start_idx + 80 > len(bits_extraidos):
            raise ValueError("Imagem cortada!")

        tam_bits = MotorFacebook._decodificar_repeticao_5x(bits_extraidos[start_idx : start_idx + 80])
        payload_size = sum(bit << i for i, bit in enumerate(tam_bits))

        if payload_size == 0 or payload_size > 32000:
            raise ValueError("Dados corrompidos na leitura inicial.")

        # Ler Payload (payload_size * 8 * 5 bits)
        bits_necessarios = payload_size * 8 * 5
        if start_idx + 80 + bits_necessarios > len(bits_extraidos):
            raise ValueError("A mensagem foi cortada ao baixar do Facebook!")

        payload_bits = MotorFacebook._decodificar_repeticao_5x(
            bits_extraidos[start_idx + 80 : start_idx + 80 + bits_necessarios]
        )

        payload = bytearray()
        for i in range(0, len(payload_bits), 8):
            byte = 0
            for j in range(8):
                if i + j < len(payload_bits):
                    byte |= (payload_bits[i + j] << j)
            payload.append(byte)

        if callback: callback(80)

        cripto_flag = payload[0]
        dados = bytes(payload[1:])

        if cripto_flag == 1:
            if not senha:
                raise ValueError("Esta mensagem tem senha! Digite a senha no campo acima.")
            dados = MotorFacebook._criptografar_xor(dados, senha)

        try:
            texto = zlib.decompress(dados).decode('utf-8')
        except zlib.error:
            raise ValueError("Senha incorreta ou imagem excessivamente corrompida.")

        if callback: callback(100)
        return {'texto': texto, 'tamanho': len(texto), 'criptografado': (cripto_flag == 1)}

    @staticmethod
    def tentar_decodificar_auto(caminho_imagem, senha=None, callback=None):
        # Testa variações caso o Facebook tenha alterado levemente a luz
        intensidades = [56, 48, 64, 40]
        total = len(intensidades)
        
        for i, q in enumerate(intensidades):
            if callback: callback((i / total) * 100)
            try:
                res = MotorFacebook.decodificar_facebook(caminho_imagem, senha, 8, q)
                return res
            except Exception:
                continue
        raise ValueError("Não encontrou mensagem. Verifique se baixou a foto original e se a senha está certa.")


# ========================== WIDGETS UI ==========================

class TerminalHacker(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#0a0a0a', **kwargs)
        self.texto = scrolledtext.ScrolledText(
            self, bg='#0a0a0a', fg='#00ff00', insertbackground='#00ff00',
            font=('Courier New', 10), wrap=tk.WORD, state='disabled',
            relief='flat', borderwidth=0, highlightthickness=1,
            highlightbackground='#003300', highlightcolor='#00ff00'
        )
        self.texto.pack(fill='both', expand=True, padx=2, pady=2)
        for tag, cor in [('verde', '#00ff00'), ('verde_claro', '#00ff88'),
                          ('vermelho', '#ff0040'), ('amarelo', '#ffff00'),
                          ('ciano', '#00ffff'), ('abobora', '#FF7518'),
                          ('branco', '#ffffff')]:
            self.texto.tag_config(tag, foreground=cor)
        self.texto.tag_config('cabecalho', foreground='#00ff00', font=('Courier New', 10, 'bold'))
        self.texto.tag_config('sucesso', foreground='#00ff88', font=('Courier New', 10, 'bold'))
        self.texto.tag_config('erro', foreground='#ff0040', font=('Courier New', 10, 'bold'))

    def escrever_linha(self, texto='', tag='verde'):
        self.texto.config(state='normal')
        self.texto.insert('end', texto + '\n', tag)
        self.texto.see('end')
        self.texto.config(state='disabled')


class BarraProgressoHacker(tk.Canvas):
    def __init__(self, parent, width=400, height=25, **kwargs):
        super().__init__(parent, width=width, height=height, bg='#0a0a0a',
                         highlightthickness=1, highlightbackground='#003300', **kwargs)
        self._largura = width
        self._altura = height
        self._progresso = 0
        self._desenhar()

    def _desenhar(self):
        self.delete('all')
        self.create_rectangle(2, 2, self._largura - 2, self._altura - 2, outline='#003300', width=1)
        w = int((self._largura - 4) * self._progresso / 100)
        if w > 0:
            for i in range(w):
                c = f'#00{format(min(int(100 + 155 * (i / max(w, 1))), 255), "02x")}00'
                self.create_line(i + 3, 3, i + 3, self._altura - 3, fill=c)
        t = f"[{'█' * (int(self._progresso) // 5)}{'░' * (20 - int(self._progresso) // 5)}] {self._progresso:.1f}%"
        self.create_text(self._largura // 2, self._altura // 2, text=t, fill='#00ff00', font=('Courier New', 8, 'bold'))

    def definir_progresso(self, valor):
        self._progresso = min(100, max(0, valor))
        self._desenhar()


# ========================== INTERFACE PRINCIPAL ==========================

class AplicativoEsteganografia:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Esteganografia Esconda Seus Segredos Modo Facebook Luminance")
        self.root.configure(bg="#0a0a0a")
        try:
            if platform.system() == "Windows":
                self.root.after(100, lambda: self.root.state("zoomed"))
            else:
                self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        except Exception:
            pass
        self._configurar_estilos()
        self._construir_interface()
        self._mostrar_banner()

    def _configurar_estilos(self):
        estilo = ttk.Style()
        estilo.theme_use('clam')
        estilo.configure('Hacker.TNotebook', background='#0a0a0a', borderwidth=0)
        estilo.configure('Hacker.TNotebook.Tab', background='#0a1a0a', foreground='#00ff00', padding=[15, 5], font=('Courier New', 10, 'bold'))
        estilo.map('Hacker.TNotebook.Tab', background=[('selected', '#003300'), ('active', '#002200')], foreground=[('selected', '#00ff00'), ('active', '#00ff88')])

    def _criar_botao_hacker(self, parent, texto, comando, largura=20, cor='#00ff00'):
        btn = tk.Button(parent, text=texto, command=comando, bg='#001a00', fg=cor, activebackground='#003300', activeforeground='#00ff88', font=('Courier New', 10, 'bold'), relief='flat', borderwidth=1, width=largura, cursor='hand2', highlightbackground='#003300', highlightcolor='#00ff00', highlightthickness=1)
        btn.bind('<Enter>', lambda e: btn.config(bg='#003300', fg='#00ff88'))
        btn.bind('<Leave>', lambda e: btn.config(bg='#001a00', fg=cor))
        return btn

    def _criar_entrada_hacker(self, parent, mostrar=None, largura=40):
        return tk.Entry(parent, bg='#0a1a0a', fg='#00ff00', insertbackground='#00ff00', font=('Courier New', 10), relief='flat', borderwidth=0, width=largura, highlightbackground='#003300', highlightcolor='#00ff00', highlightthickness=1, show=mostrar)

    def _criar_texto_hacker(self, parent, altura=10, largura=50):
        return scrolledtext.ScrolledText(parent, bg='#0a1a0a', fg='#00ff00', insertbackground='#00ff00', font=('Courier New', 10), wrap=tk.WORD, height=altura, width=largura, relief='flat', borderwidth=0, highlightbackground='#003300', highlightcolor='#00ff00', highlightthickness=1)

    def _construir_interface(self):
        quadro_cab = tk.Frame(self.root, bg='#0a0a0a')
        quadro_cab.pack(fill='x', padx=5, pady=(5, 0))
        tk.Label(quadro_cab, text="╔" + "═" * 125 + "╗", bg='#0a0a0a', fg='#003300', font=('Courier New', 8)).pack()
        tk.Label(quadro_cab, text="║  ▓▓▓ Esteganografia  ▓▓▓  │  Esconda Seus Segredos  │  [ MODO FACEBOOK INDESTRUTÍVEL ]                                  ║", bg='#0a0a0a', fg='#00ff00', font=('Courier New', 9, 'bold')).pack()
        tk.Label(quadro_cab, text="╚" + "═" * 125 + "╝", bg='#0a0a0a', fg='#003300', font=('Courier New', 8)).pack()

        # Layout ajustado para painel vertical (Abas em cima, Terminal em baixo)
        container = tk.PanedWindow(self.root, orient='vertical', bg='#0a0a0a', sashwidth=3, sashrelief='flat')
        container.pack(fill='both', expand=True, padx=5, pady=5)

        quadro_topo = tk.Frame(container, bg='#0a0a0a')
        container.add(quadro_topo, height=450)

        self.caderno = ttk.Notebook(quadro_topo, style='Hacker.TNotebook')
        self.caderno.pack(fill='both', expand=True)

        self._aba_modificar_imagem()
        self._aba_facebook_codificar()
        self._aba_facebook_decodificar()
        self._aba_codificar_lsb()
        self._aba_decodificar_lsb()
        self._aba_ajuda()

        quadro_baixo = tk.Frame(container, bg='#0a0a0a')
        container.add(quadro_baixo, height=220)
        
        tk.Label(quadro_baixo, text="┌─[ TERMINAL DE COMANDOS ]" + "─" * 100, bg='#0a0a0a', fg='#003300', font=('Courier New', 9), anchor='w').pack(fill='x')
        self.terminal = TerminalHacker(quadro_baixo)
        self.terminal.pack(fill='both', expand=True)
        tk.Label(quadro_baixo, text="└" + "─" * 125, bg='#0a0a0a', fg='#003300', font=('Courier New', 9), anchor='w').pack(fill='x')

        self._construir_barra_status()

    def _aba_modificar_imagem(self):
        aba = tk.Frame(self.caderno, bg='#0a0a0a')
        self.caderno.add(aba, text=' ⟨ 1. PREPARAR IMG ⟩ ')

        tk.Label(aba, text="┌─[ PASSO 1: PADRONIZAR IMAGEM PARA O FACEBOOK ]─────┐", bg='#0a0a0a', fg='#003300', font=('Courier New', 9)).pack(fill='x', padx=5, pady=5)
        tk.Label(aba, text=" Selecione a imagem que deseja postar. O script vai ajustar\n o tamanho exato do Facebook para evitar distorções do algoritmo.", bg='#1a1a00', fg='#ffff00', font=('Courier New', 9), justify='left').pack(fill='x', padx=10, pady=5)

        q1 = tk.Frame(aba, bg='#0a0a0a'); q1.pack(fill='x', padx=10, pady=5)
        tk.Label(q1, text="[>] Imagem original:", bg='#0a0a0a', fg='#00ff00', font=('Courier New', 10)).pack(anchor='w')
        qe = tk.Frame(q1, bg='#0a0a0a'); qe.pack(fill='x', pady=2)
        self.caminho_imagem_mod = self._criar_entrada_hacker(qe, largura=55)
        self.caminho_imagem_mod.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self._criar_botao_hacker(qe, "[ PROCURAR ]", self._procurar_imagem_mod, largura=12).pack(side='right')

        self.lbl_preview_mod = tk.Label(aba, text="[ NENHUMA IMAGEM CARREGADA ]", bg='#0a1a0a', fg='#005500', font=('Courier New', 10), height=3, highlightbackground='#003300', highlightthickness=1)
        self.lbl_preview_mod.pack(fill='x', padx=10, pady=5)

        q_btn = tk.Frame(aba, bg='#0a0a0a'); q_btn.pack(pady=20)
        self._criar_botao_hacker(q_btn, "OTIMIZAR PARA FACEBOOK PAISAGEM (1200x630)", lambda: self._modificar_padrao_fb("1200x630"), largura=50, cor='#00ffff').pack(pady=5)
        self._criar_botao_hacker(q_btn, "OTIMIZAR PARA FACEBOOK QUADRADO (1200x1200)", lambda: self._modificar_padrao_fb("1200x1200"), largura=50, cor='#00ffff').pack(pady=5)

    def _aba_facebook_codificar(self):
        aba = tk.Frame(self.caderno, bg='#0a0a0a')
        self.caderno.add(aba, text=' ⟨ 2. ESCONDER MSG ⟩ ')

        tk.Label(aba, text="┌─[ PASSO 2: ESCONDER MENSAGEM COM BLINDAGEM ]────────┐", bg='#0a0a0a', fg='#003300', font=('Courier New', 9)).pack(fill='x', padx=5, pady=5)

        q1 = tk.Frame(aba, bg='#0a0a0a'); q1.pack(fill='x', padx=10, pady=2)
        tk.Label(q1, text="[>] Imagem Otimizada (do Passo 1):", bg='#0a0a0a', fg='#00ff00', font=('Courier New', 10)).pack(anchor='w')
        qe = tk.Frame(q1, bg='#0a0a0a'); qe.pack(fill='x')
        self.caminho_fb_cod = self._criar_entrada_hacker(qe, largura=55)
        self.caminho_fb_cod.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self._criar_botao_hacker(qe, "[ PROCURAR ]", lambda: self._procurar_img(self.caminho_fb_cod), largura=12).pack(side='right')

        q2 = tk.Frame(aba, bg='#0a0a0a'); q2.pack(fill='both', expand=True, padx=10, pady=5)
        tk.Label(q2, text="[>] Mensagem secreta:", bg='#0a0a0a', fg='#00ff00', font=('Courier New', 10)).pack(anchor='w')
        self.txt_fb_cod = self._criar_texto_hacker(q2, altura=6)
        self.txt_fb_cod.pack(fill='both', expand=True)

        qc = tk.Frame(aba, bg='#0a0a0a'); qc.pack(fill='x', padx=10, pady=2)
        tk.Label(qc, text="Senha (Opcional):", bg='#0a0a0a', fg='#00ff00', font=('Courier New', 10)).pack(side='left')
        self.senha_fb_cod = self._criar_entrada_hacker(qc, mostrar='•', largura=20)
        self.senha_fb_cod.pack(side='left', padx=10)

        self.prog_fb_cod = BarraProgressoHacker(aba, width=600)
        self.prog_fb_cod.pack(padx=10, pady=5)

        self._criar_botao_hacker(aba, "◄◄ GERAR IMAGEM BLINDADA PARA UPLOAD ►►", self._codificar_fb, largura=40, cor='#00ffff').pack(pady=10)

    def _aba_facebook_decodificar(self):
        aba = tk.Frame(self.caderno, bg='#0a0a0a')
        self.caderno.add(aba, text=' ⟨ 3. EXTRAIR MSG ⟩ ')

        tk.Label(aba, text="┌─[ PASSO 3: LER MENSAGEM DO FACEBOOK ]──────────────┐", bg='#0a0a0a', fg='#003300', font=('Courier New', 9)).pack(fill='x', padx=5, pady=5)
        tk.Label(aba, text=" Baixe a foto postada no Facebook para o computador/celular\n e selecione o arquivo baixado abaixo para ler.", bg='#001a1a', fg='#00ffaa', font=('Courier New', 9), justify='left').pack(fill='x', padx=10, pady=5)

        q1 = tk.Frame(aba, bg='#0a0a0a'); q1.pack(fill='x', padx=10, pady=2)
        tk.Label(q1, text="[>] Imagem Baixada:", bg='#0a0a0a', fg='#00ff00', font=('Courier New', 10)).pack(anchor='w')
        qe = tk.Frame(q1, bg='#0a0a0a'); qe.pack(fill='x')
        self.caminho_fb_dec = self._criar_entrada_hacker(qe, largura=55)
        self.caminho_fb_dec.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self._criar_botao_hacker(qe, "[ PROCURAR ]", lambda: self._procurar_img(self.caminho_fb_dec), largura=12).pack(side='right')

        qc = tk.Frame(aba, bg='#0a0a0a'); qc.pack(fill='x', padx=10, pady=5)
        tk.Label(qc, text="Senha (Se usou):", bg='#0a0a0a', fg='#00ff00', font=('Courier New', 10)).pack(side='left')
        self.senha_fb_dec = self._criar_entrada_hacker(qc, mostrar='•', largura=20)
        self.senha_fb_dec.pack(side='left', padx=10)

        self.prog_fb_dec = BarraProgressoHacker(aba, width=600)
        self.prog_fb_dec.pack(padx=10, pady=5)

        self._criar_botao_hacker(aba, "◄◄ EXTRAIR MENSAGEM ►►", self._decodificar_fb, largura=30, cor='#00ffff').pack(pady=5)

        qr = tk.Frame(aba, bg='#0a0a0a'); qr.pack(fill='both', expand=True, padx=10, pady=5)
        tk.Label(qr, text="[>] Mensagem extraída:", bg='#0a0a0a', fg='#00ff00', font=('Courier New', 10)).pack(anchor='w')
        self.txt_resultado_fb = self._criar_texto_hacker(qr, altura=6)
        self.txt_resultado_fb.pack(fill='both', expand=True)

    def _aba_codificar_lsb(self):
        aba = tk.Frame(self.caderno, bg='#0a0a0a')
        self.caderno.add(aba, text=' ⟨ LSB OFFLINE ⟩ ')
        tk.Label(aba, text=" Modo LSB Tradicional: Funciona apenas para salvar em PNG localmente.\n NÃO enviar pelo Facebook/WhatsApp.", bg='#1a0a00', fg='#ff4040', font=('Courier New', 9), justify='left').pack(fill='x', padx=10, pady=5)

        q1 = tk.Frame(aba, bg='#0a0a0a'); q1.pack(fill='x', padx=10, pady=5)
        tk.Label(q1, text="Imagem:", bg='#0a0a0a', fg='#00ff00').pack(anchor='w')
        qe = tk.Frame(q1, bg='#0a0a0a'); qe.pack(fill='x')
        self.img_lsb_cod = self._criar_entrada_hacker(qe, largura=55)
        self.img_lsb_cod.pack(side='left', fill='x', expand=True)
        self._criar_botao_hacker(qe, "PROCURAR", lambda: self._procurar_img(self.img_lsb_cod), largura=10).pack(side='right')

        q2 = tk.Frame(aba, bg='#0a0a0a'); q2.pack(fill='both', expand=True, padx=10, pady=5)
        tk.Label(q2, text="Mensagem:", bg='#0a0a0a', fg='#00ff00').pack(anchor='w')
        self.txt_lsb_cod = self._criar_texto_hacker(q2, altura=4)
        self.txt_lsb_cod.pack(fill='both', expand=True)

        qc = tk.Frame(aba, bg='#0a0a0a'); qc.pack(fill='x', padx=10, pady=5)
        tk.Label(qc, text="Senha:", bg='#0a0a0a', fg='#00ff00').pack(side='left')
        self.senha_lsb_cod = self._criar_entrada_hacker(qc, mostrar='•', largura=20)
        self.senha_lsb_cod.pack(side='left', padx=5)

        self.prog_lsb_cod = BarraProgressoHacker(aba, width=600)
        self.prog_lsb_cod.pack(padx=10, pady=5)

        self._criar_botao_hacker(aba, "CODIFICAR LSB (Offline)", self._codificar_lsb, largura=25).pack(pady=5)

    def _aba_decodificar_lsb(self):
        aba = tk.Frame(self.caderno, bg='#0a0a0a')
        self.caderno.add(aba, text=' ⟨ DECOD LSB ⟩ ')

        q1 = tk.Frame(aba, bg='#0a0a0a'); q1.pack(fill='x', padx=10, pady=10)
        tk.Label(q1, text="Imagem PNG:", bg='#0a0a0a', fg='#00ff00').pack(anchor='w')
        qe = tk.Frame(q1, bg='#0a0a0a'); qe.pack(fill='x')
        self.img_lsb_dec = self._criar_entrada_hacker(qe, largura=55)
        self.img_lsb_dec.pack(side='left', fill='x', expand=True)
        self._criar_botao_hacker(qe, "PROCURAR", lambda: self._procurar_img(self.img_lsb_dec), largura=10).pack(side='right')

        qc = tk.Frame(aba, bg='#0a0a0a'); qc.pack(fill='x', padx=10, pady=5)
        tk.Label(qc, text="Senha:", bg='#0a0a0a', fg='#00ff00').pack(side='left')
        self.senha_lsb_dec = self._criar_entrada_hacker(qc, mostrar='•', largura=20)
        self.senha_lsb_dec.pack(side='left', padx=5)

        self.prog_lsb_dec = BarraProgressoHacker(aba, width=600)
        self.prog_lsb_dec.pack(padx=10, pady=5)

        self._criar_botao_hacker(aba, "DECODIFICAR LSB", self._decodificar_lsb, largura=25).pack(pady=5)

        qr = tk.Frame(aba, bg='#0a0a0a'); qr.pack(fill='both', expand=True, padx=10, pady=5)
        tk.Label(qr, text="Resultado:", bg='#0a0a0a', fg='#00ff00').pack(anchor='w')
        self.txt_lsb_dec = self._criar_texto_hacker(qr, altura=6)
        self.txt_lsb_dec.pack(fill='both', expand=True)

    def _aba_ajuda(self):
        aba = tk.Frame(self.caderno, bg='#0a0a0a')
        self.caderno.add(aba, text=' ⟨ AJUDA ⟩ ')

        term_ajuda = TerminalHacker(aba)
        term_ajuda.pack(fill='both', expand=True, padx=10, pady=10)

        conteudo = [
            ("╔════════════════════════════════════════════════╗", 'cabecalho'),
            ("║       MANUAL - MODO FACEBOOK INDESTRUTÍVEL     ║", 'cabecalho'),
            ("╚════════════════════════════════════════════════╝", 'cabecalho'),
            ("", 'verde'),
            ("Siga estes passos na ordem:", 'amarelo'),
            ("", 'verde'),
            ("1) PASSO 1 - PREPARAR IMG:", 'branco'),
            ("   Selecione a foto e clique no botão 'OTIMIZAR'.", 'verde'),
            ("   O programa vai salvar a foto na proporção exata.", 'verde'),
            ("", 'verde'),
            ("2) PASSO 2 - ESCONDER MSG:", 'branco'),
            ("   Digite a mensagem secreta e clique em 'GERAR IMAGEM'.", 'verde'),
            ("   O programa vai criar uma imagem blindada.", 'verde'),
            ("", 'verde'),
            ("3) POSTAR NO FACEBOOK:", 'branco'),
            ("   Poste a foto blindada normalmente na rede social.", 'verde'),
            ("", 'verde'),
            ("4) PASSO 3 - EXTRAIR MSG:", 'branco'),
            ("   Baixe a foto do Facebook para seu PC/Celular.", 'verde'),
            ("   Abra no Passo 3 e clique em 'EXTRAIR MENSAGEM'.", 'verde'),
        ]
        for texto, tag in conteudo:
            term_ajuda.escrever_linha("  " + texto, tag)

    def _construir_barra_status(self):
        qs = tk.Frame(self.root, bg='#001100'); qs.pack(fill='x', side='bottom')
        self.rotulo_status = tk.Label(qs, text=" ● SISTEMA PRONTO", bg='#001100', fg='#00aa00', font=('Courier New', 9), anchor='w')
        self.rotulo_status.pack(fill='x', padx=5, pady=2)

    def _mostrar_banner(self):
        banner = """  ██████╗ ██╗███╗   ███╗
 ██╔═══██╗██║████╗ ████║    MOTOR YCbCr LUMINANCE
 ██║   ██║██║██╔████╔██║    [LUMINOSIDADE A PROVA DE JPEG]
 ██║▄▄ ██║██║██║╚██╔╝██║    Redundância Quíntupla (5x)
 ╚██████╔╝██║██║ ╚═╝ ██║
  ╚══▀▀═╝ ╚═╝╚═╝     ╚═╝"""
        self.terminal.escrever_linha(banner, 'cabecalho')
        self.terminal.escrever_linha() # Linha em branco conforme solicitado
        self.terminal.escrever_linha("  [*] Motor de Luminosidade YCbCr ativado.", 'verde')
        self.terminal.escrever_linha("  [*] Redundância Quíntupla (5x) ligada.", 'verde')
        self.terminal.escrever_linha("  [*] Aguardando comandos...", 'verde_claro')

    def _definir_status(self, txt, cor='#00aa00'):
        self.rotulo_status.config(text=f"  ●  {txt}", fg=cor)

    def _registrar(self, msg, tag='verde'):
        self.terminal.escrever_linha(f"  [{time.strftime('%H:%M:%S')}] {msg}", tag)

    def _erro_ui(self, titulo, mensagem):
        messagebox.showerror(titulo, mensagem)
        self._registrar(f"ERRO: {mensagem}", 'erro')
        self._definir_status("ERRO", '#ff0040')

    def _procurar_img(self, entry_widget):
        p = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp *.bmp"), ("Todos", "*.*")])
        if p:
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, p)

    def _procurar_imagem_mod(self):
        p = filedialog.askopenfilename(filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp *.bmp"), ("Todos", "*.*")])
        if p:
            self.caminho_imagem_mod.delete(0, 'end')
            self.caminho_imagem_mod.insert(0, p)
            self.lbl_preview_mod.config(text=f"📷 {os.path.basename(p)}\nClique num dos botões abaixo para otimizar.", fg='#00ff00')

    def _modificar_padrao_fb(self, formato):
        c = self.caminho_imagem_mod.get().strip()
        if not c or not os.path.exists(c):
            messagebox.showerror("Erro", "Selecione uma imagem primeiro!")
            return

        s = filedialog.asksaveasfilename(title="Salvar Imagem Otimizada", defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not s: return

        self._definir_status("OTIMIZANDO IMAGEM...", '#ffaa00')
        try:
            dim = MotorFacebook.otimizar_para_facebook(c, s, formato)
            self._registrar(f"Imagem otimizada com sucesso ({dim[0]}x{dim[1]})", 'sucesso')
            self._definir_status("CONCLUÍDO", '#00ff00')

            self.caminho_fb_cod.delete(0, 'end')
            self.caminho_fb_cod.insert(0, s)
            self.caderno.select(1)
        except Exception as e:
            self._erro_ui("Erro", str(e))

    def _codificar_fb(self):
        c = self.caminho_fb_cod.get().strip()
        m = self.txt_fb_cod.get('1.0', 'end').strip()
        s = self.senha_fb_cod.get().strip() or None

        if not c or not os.path.exists(c):
            messagebox.showerror("Erro", "Selecione a imagem do Passo 1!")
            return
        if not m:
            messagebox.showerror("Erro", "Escreva a mensagem secreta!")
            return

        out = filedialog.asksaveasfilename(title="Salvar Imagem Blindada", defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not out: return

        self._definir_status("CODIFICANDO...", '#ffaa00')
        self._registrar("Iniciando blindagem de Luminosidade YCbCr...", 'amarelo')

        def worker():
            try:
                def cb(p): self.root.after(0, self.prog_fb_cod.definir_progresso, p)
                res = MotorFacebook.codificar_facebook(c, out, m, s, 8, 56, cb)
                msg_ok = f"Imagem blindada com sucesso! ({res['bytes_comprimidos']} bytes embutidos)."
                arq_ok = os.path.basename(out)
                self.root.after(0, lambda: self._codificar_fb_sucesso(msg_ok, arq_ok))
            except Exception as e:
                em = str(e)
                self.root.after(0, lambda: self._erro_ui("Erro", em))

        threading.Thread(target=worker, daemon=True).start()

    def _codificar_fb_sucesso(self, msg, arq):
        self._registrar(msg, 'sucesso')
        self._registrar(f"Salvo em: {arq}", 'verde_claro')
        self._definir_status("PRONTO PARA POSTAR", '#00ff00')
        self.terminal.escrever_linha("\n  ✓ IMAGEM PRONTA PARA UPLOAD NO FACEBOOK!\n", 'sucesso')

    def _decodificar_fb(self):
        c = self.caminho_fb_dec.get().strip()
        s = self.senha_fb_dec.get().strip() or None

        if not c or not os.path.exists(c):
            messagebox.showerror("Erro", "Selecione a foto baixada do Facebook!")
            return

        self.txt_resultado_fb.delete('1.0', 'end')
        self._definir_status("EXTRAINDO...", '#ffaa00')
        self._registrar("Escaneando canal de luminosidade da imagem...", 'amarelo')

        def worker():
            try:
                def cb(p): self.root.after(0, self.prog_fb_dec.definir_progresso, p)
                r = MotorFacebook.tentar_decodificar_auto(c, s, cb)
                to = r['texto']
                self.root.after(0, lambda: self._decodificar_fb_sucesso(to))
            except Exception as e:
                em = str(e)
                self.root.after(0, lambda: self._erro_ui("Erro na Leitura", em))

        threading.Thread(target=worker, daemon=True).start()

    def _decodificar_fb_sucesso(self, texto):
        self.txt_resultado_fb.delete('1.0', 'end')
        self.txt_resultado_fb.insert('1.0', texto)
        self._registrar("SUCESSO! Mensagem extraída com sucesso!", 'sucesso')
        self._definir_status("LEITURA CONCLUÍDA", '#00ff00')
        self.terminal.escrever_linha(f"\nMensagem Extraída\n\n{texto}\n", 'abobora')

    def _codificar_lsb(self):
        c, m, s = self.img_lsb_cod.get().strip(), self.txt_lsb_cod.get('1.0', 'end').strip(), self.senha_lsb_cod.get().strip() or None
        if not c or not m: return messagebox.showerror("Erro", "Preencha os campos!")
        out = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not out: return

        def worker():
            try:
                MotorEsteganografia.codificar_texto(c, out, m, s, lambda p: self.root.after(0, self.prog_lsb_cod.definir_progresso, p))
                self.root.after(0, lambda: self._registrar("LSB Concluído!", 'sucesso'))
            except Exception as e:
                em = str(e); self.root.after(0, lambda: self._erro_ui("Erro", em))

        threading.Thread(target=worker, daemon=True).start()

    def _decodificar_lsb(self):
        c, s = self.img_lsb_dec.get().strip(), self.senha_lsb_dec.get().strip() or None
        if not c: return messagebox.showerror("Erro", "Selecione a imagem!")

        def worker():
            try:
                r = MotorEsteganografia.decodificar(c, s, lambda p: self.root.after(0, self.prog_lsb_dec.definir_progresso, p))
                to = r['texto']
                self.root.after(0, lambda: (self.txt_lsb_dec.delete('1.0', 'end'), self.txt_lsb_dec.insert('1.0', to), self._registrar("LSB Extraído!", 'sucesso')))
            except Exception as e:
                em = str(e); self.root.after(0, lambda: self._erro_ui("Erro", em))

        threading.Thread(target=worker, daemon=True).start()

    def ejecutar(self):
        self.root.mainloop()


# ========================== MAIN ==========================

def principal():
    if not PIL_DISPONIVEL:
        root = tk.Tk()
        root.title("Erro")
        root.configure(bg="#0a0a0a")
        root.geometry("500x200")
        tk.Label(root, text="⚠ Instale as dependências executando no terminal:\npip install Pillow numpy", bg="#0a0a0a", fg="#ff0040", font=("Courier New", 12, "bold")).pack(expand=True)
        root.mainloop()
        return

    app = AplicativoEsteganografia()
    app.ejecutar()

if __name__ == "__main__":
    principal()
