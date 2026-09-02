#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                                    ║
║ ███████╗███████╗████████╗███████╗ ██████╗  █████╗ ███╗   ██╗ ██████╗  ██████╗ ██████╗  █████╗ ███████╗██╗ █████╗   ║
║ ██╔════╝██╔════╝╚══██╔══╝██╔════╝██╔════╝ ██╔══██╗████╗  ██║██╔═══██╗██╔════╝ ██╔══██╗██╔══██╗██╔════╝██║██╔══██╗  ║
║ █████╗  ███████╗   ██║   █████╗  ██║  ███╗███████║██╔██╗ ██║██║   ██║██║  ███╗██████╔╝███████║█████╗  ██║███████║  ║
║ ██╔══╝  ╚════██║   ██║   ██╔══╝  ██║   ██║██╔══██║██║╚██╗██║██║   ██║██║   ██║██╔══██╗██╔══██║██╔══╝  ██║██╔══██║  ║
║ ███████╗███████║   ██║   ███████╗╚██████╔╝██║  ██║██║ ╚████║╚██████╔╝╚██████╔╝██║  ██║██║  ██║██║     ██║██║  ██║  ║
║ ╚══════╝╚══════╝   ╚═╝   ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝  ║
║                                                                                                                    ║
║                            Esteganografia - Esconda Seus Segredos                                                  ║
║                              [ Edição Hacker - Estilo Matrix ]                                                     ║
║                                                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

Ferramenta de Esteganografia com Interface Gráfica estilo Hacker
- Esconder texto em imagens (Esteganografia LSB)
- Esconder arquivos em imagens
- Criptografia XOR integrada com SHA-256
- Análise forense de imagem
- Aba de Ajuda completa
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import random
import string
import hashlib
import struct
import threading
import time
import math
from pathlib import Path
import platform

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    import numpy as np
    PIL_DISPONIVEL = True
except ImportError:
    PIL_DISPONIVEL = False
    pass


# ========================== MOTOR DE ESTEGANOGRAFIA ==========================

class MotorEsteganografia:
    """Motor principal de esteganografia LSB"""

    CABECALHO_MAGICO = b'ZSTEG'
    VERSAO = b'\x02'

    # Tipos de carga útil
    TIPO_TEXTO = 0x01
    TIPO_ARQUIVO = 0x02
    TIPO_TEXTO_CRIPTOGRAFADO = 0x03
    TIPO_ARQUIVO_CRIPTOGRAFADO = 0x04

    @staticmethod
    def _criptografar_xor(dados: bytes, senha: str) -> bytes:
        """Criptografia XOR com derivação de chave SHA-256"""
        chave = hashlib.sha256(senha.encode()).digest()
        criptografado = bytearray()
        for i, byte in enumerate(dados):
            criptografado.append(byte ^ chave[i % len(chave)])
        return bytes(criptografado)

    @staticmethod
    def _descriptografar_xor(dados: bytes, senha: str) -> bytes:
        """Descriptografia XOR (operação simétrica)"""
        return MotorEsteganografia._criptografar_xor(dados, senha)

    @staticmethod
    def _inteiro_para_bits(valor: int, num_bits: int = 32) -> list:
        """Converte inteiro para lista de bits"""
        return [(valor >> i) & 1 for i in range(num_bits)]

    @staticmethod
    def _bits_para_inteiro(bits: list) -> int:
        """Converte lista de bits para inteiro"""
        valor = 0
        for i, bit in enumerate(bits):
            valor |= (bit << i)
        return valor

    @staticmethod
    def _bytes_para_bits(dados: bytes) -> list:
        """Converte bytes para lista de bits"""
        bits = []
        for byte in dados:
            for i in range(8):
                bits.append((byte >> i) & 1)
        return bits

    @staticmethod
    def _bits_para_bytes(bits: list) -> bytes:
        """Converte lista de bits para bytes"""
        resultado = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                if i + j < len(bits):
                    byte |= (bits[i + j] << j)
            resultado.append(byte)
        return bytes(resultado)

    @staticmethod
    def calcular_capacidade(caminho_imagem: str) -> int:
        """Calcula capacidade máxima de dados em bytes"""
        img = Image.open(caminho_imagem)
        largura, altura = img.size
        canais = len(img.getbands())
        total_bits = largura * altura * canais
        # Subtrair cabeçalho (mágico + versão + tipo + tamanho + tam_nome)
        bits_cabecalho = (5 + 1 + 1 + 4 + 4) * 8
        bits_disponiveis = total_bits - bits_cabecalho
        return max(0, bits_disponiveis // 8)

    @staticmethod
    def obter_info_imagem(caminho_imagem: str) -> dict:
        """Retorna informações detalhadas da imagem"""
        img = Image.open(caminho_imagem)
        largura, altura = img.size
        canais = len(img.getbands())
        modo = img.mode
        tamanho_arquivo = os.path.getsize(caminho_imagem)
        capacidade = MotorEsteganografia.calcular_capacidade(caminho_imagem)

        return {
            'largura': largura,
            'altura': altura,
            'canais': canais,
            'modo': modo,
            'tamanho_arquivo': tamanho_arquivo,
            'capacidade': capacidade,
            'capacidade_kb': capacidade / 1024,
            'total_pixels': largura * altura
        }

    @staticmethod
    def codificar_texto(caminho_imagem: str, caminho_saida: str, texto: str,
                        senha: str = None, callback=None) -> bool:
        """Esconde texto em uma imagem usando LSB"""
        try:
            img = Image.open(caminho_imagem).convert('RGB')
            pixels = np.array(img)

            dados = texto.encode('utf-8')
            tipo_carga = MotorEsteganografia.TIPO_TEXTO
            nome_arquivo = b''

            if senha:
                dados = MotorEsteganografia._criptografar_xor(dados, senha)
                tipo_carga = MotorEsteganografia.TIPO_TEXTO_CRIPTOGRAFADO

            # Construir carga: MÁGICO + VERSÃO + TIPO + TAM_DADOS + TAM_NOME + NOME + DADOS
            carga = bytearray()
            carga.extend(MotorEsteganografia.CABECALHO_MAGICO)
            carga.extend(MotorEsteganografia.VERSAO)
            carga.append(tipo_carga)
            carga.extend(struct.pack('<I', len(dados)))
            carga.extend(struct.pack('<I', len(nome_arquivo)))
            carga.extend(nome_arquivo)
            carga.extend(dados)

            # Verificar capacidade
            total_pixels = pixels.shape[0] * pixels.shape[1]
            total_canais = total_pixels * 3
            bits_necessarios = len(carga) * 8

            if bits_necessarios > total_canais:
                raise ValueError(
                    f"Imagem muito pequena! Necessário: {bits_necessarios} bits, "
                    f"Disponível: {total_canais} bits"
                )

            # Converter carga para bits
            bits = MotorEsteganografia._bytes_para_bits(bytes(carga))

            # Embutir bits usando LSB
            pixels_planos = pixels.flatten()
            total_bits = len(bits)

            for i, bit in enumerate(bits):
                pixels_planos[i] = (pixels_planos[i] & 0xFE) | bit
                if callback and i % 10000 == 0:
                    callback(i / total_bits * 100)

            # Reconstruir imagem
            pixels = pixels_planos.reshape(pixels.shape)
            resultado = Image.fromarray(pixels.astype('uint8'), 'RGB')
            resultado.save(caminho_saida, 'PNG')

            if callback:
                callback(100)

            return True

        except Exception as e:
            raise e

    @staticmethod
    def codificar_arquivo(caminho_imagem: str, caminho_saida: str, caminho_arquivo: str,
                          senha: str = None, callback=None) -> bool:
        """Esconde um arquivo dentro de uma imagem"""
        try:
            img = Image.open(caminho_imagem).convert('RGB')
            pixels = np.array(img)

            with open(caminho_arquivo, 'rb') as f:
                dados = f.read()

            nome_arquivo = os.path.basename(caminho_arquivo).encode('utf-8')
            tipo_carga = MotorEsteganografia.TIPO_ARQUIVO

            if senha:
                dados = MotorEsteganografia._criptografar_xor(dados, senha)
                tipo_carga = MotorEsteganografia.TIPO_ARQUIVO_CRIPTOGRAFADO

            # Construir carga
            carga = bytearray()
            carga.extend(MotorEsteganografia.CABECALHO_MAGICO)
            carga.extend(MotorEsteganografia.VERSAO)
            carga.append(tipo_carga)
            carga.extend(struct.pack('<I', len(dados)))
            carga.extend(struct.pack('<I', len(nome_arquivo)))
            carga.extend(nome_arquivo)
            carga.extend(dados)

            # Verificar capacidade
            total_pixels = pixels.shape[0] * pixels.shape[1]
            total_canais = total_pixels * 3
            bits_necessarios = len(carga) * 8

            if bits_necessarios > total_canais:
                raise ValueError(
                    f"Imagem muito pequena! Necessário: {len(carga)} bytes, "
                    f"Disponível: {total_canais // 8} bytes"
                )

            # Converter e embutir
            bits = MotorEsteganografia._bytes_para_bits(bytes(carga))
            pixels_planos = pixels.flatten()
            total_bits = len(bits)

            for i, bit in enumerate(bits):
                pixels_planos[i] = (pixels_planos[i] & 0xFE) | bit
                if callback and i % 10000 == 0:
                    callback(i / total_bits * 100)

            pixels = pixels_planos.reshape(pixels.shape)
            resultado = Image.fromarray(pixels.astype('uint8'), 'RGB')
            resultado.save(caminho_saida, 'PNG')

            if callback:
                callback(100)

            return True

        except Exception as e:
            raise e

    @staticmethod
    def decodificar(caminho_imagem: str, senha: str = None, callback=None) -> dict:
        """Extrai dados escondidos de uma imagem"""
        try:
            img = Image.open(caminho_imagem).convert('RGB')
            pixels = np.array(img)
            pixels_planos = pixels.flatten()

            total_pixels = len(pixels_planos)

            # Extrair cabeçalho primeiro para saber o tamanho
            # Cabeçalho: MÁGICO(5) + VERSÃO(1) + TIPO(1) + TAMANHO(4) + TAM_NOME(4) = 15 bytes = 120 bits
            bits_cabecalho = []
            for i in range(120):
                bits_cabecalho.append(pixels_planos[i] & 1)

            bytes_cabecalho = MotorEsteganografia._bits_para_bytes(bits_cabecalho)

            # Verificar cabeçalho mágico
            magico = bytes_cabecalho[:5]
            if magico != MotorEsteganografia.CABECALHO_MAGICO:
                raise ValueError("Nenhum dado oculto encontrado nesta imagem!")

            versao = bytes_cabecalho[5]
            tipo_carga = bytes_cabecalho[6]
            tamanho_dados = struct.unpack('<I', bytes_cabecalho[7:11])[0]
            tam_nome = struct.unpack('<I', bytes_cabecalho[11:15])[0]

            # Calcular total de bits necessários
            tamanho_total_carga = 15 + tam_nome + tamanho_dados
            total_bits_necessarios = tamanho_total_carga * 8

            if total_bits_necessarios > total_pixels:
                raise ValueError("Dados corrompidos!")

            # Extrair todos os bits
            todos_bits = []
            for i in range(total_bits_necessarios):
                todos_bits.append(pixels_planos[i] & 1)
                if callback and i % 10000 == 0:
                    callback(i / total_bits_necessarios * 100)

            todos_bytes = MotorEsteganografia._bits_para_bytes(todos_bits)

            # Extrair nome do arquivo e dados
            nome_arquivo = todos_bytes[15:15 + tam_nome].decode('utf-8') if tam_nome > 0 else ''
            dados = todos_bytes[15 + tam_nome:15 + tam_nome + tamanho_dados]

            # Descriptografar se necessário
            esta_criptografado = tipo_carga in (
                MotorEsteganografia.TIPO_TEXTO_CRIPTOGRAFADO,
                MotorEsteganografia.TIPO_ARQUIVO_CRIPTOGRAFADO
            )

            if esta_criptografado:
                if not senha:
                    raise ValueError("Esta mensagem está criptografada! Forneça a senha.")
                dados = MotorEsteganografia._descriptografar_xor(dados, senha)

            eh_texto = tipo_carga in (
                MotorEsteganografia.TIPO_TEXTO,
                MotorEsteganografia.TIPO_TEXTO_CRIPTOGRAFADO
            )

            if callback:
                callback(100)

            return {
                'tipo': 'texto' if eh_texto else 'arquivo',
                'dados': dados,
                'texto': dados.decode('utf-8') if eh_texto else None,
                'nome_arquivo': nome_arquivo,
                'tamanho': tamanho_dados,
                'criptografado': esta_criptografado,
                'versao': versao
            }

        except Exception as e:
            raise e

    @staticmethod
    def analisar_imagem(caminho_imagem: str) -> dict:
        """Analisa uma imagem em busca de dados ocultos"""
        try:
            img = Image.open(caminho_imagem).convert('RGB')
            pixels = np.array(img)
            pixels_planos = pixels.flatten()

            # Verificar cabeçalho
            bits_cabecalho = [pixels_planos[i] & 1 for i in range(120)]
            bytes_cabecalho = MotorEsteganografia._bits_para_bytes(bits_cabecalho)

            tem_dados = bytes_cabecalho[:5] == MotorEsteganografia.CABECALHO_MAGICO

            # Análise LSB
            lsb_zeros = np.sum(pixels_planos & 1 == 0)
            lsb_uns = np.sum(pixels_planos & 1 == 1)
            total = len(pixels_planos)

            # Análise Chi-quadrado simplificada
            esperado = total / 2
            chi_quadrado = ((lsb_zeros - esperado) ** 2 / esperado +
                           (lsb_uns - esperado) ** 2 / esperado)

            # Entropia
            histograma = np.histogram(pixels_planos, bins=256, range=(0, 256))[0]
            histograma = histograma[histograma > 0]
            probabilidades = histograma / total
            entropia = -np.sum(probabilidades * np.log2(probabilidades))

            resultado = {
                'tem_dados_ocultos': tem_dados,
                'lsb_zeros': int(lsb_zeros),
                'lsb_uns': int(lsb_uns),
                'razao_lsb': lsb_uns / total,
                'chi_quadrado': chi_quadrado,
                'entropia': entropia,
                'suspeito': chi_quadrado < 10 or tem_dados,
                'total_pixels': total // 3
            }

            if tem_dados:
                tipo_carga = bytes_cabecalho[6]
                tamanho_dados = struct.unpack('<I', bytes_cabecalho[7:11])[0]
                resultado['tipo_carga'] = tipo_carga
                resultado['tamanho_carga'] = tamanho_dados
                resultado['criptografado'] = tipo_carga in (0x03, 0x04)

            return resultado

        except Exception as e:
            raise e


# ========================== WIDGET DE TERMINAL ==========================

class TerminalHacker(tk.Frame):
    """Widget de terminal estilo hacker"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#0a0a0a', **kwargs)

        self.texto = scrolledtext.ScrolledText(
            self,
            bg='#0a0a0a',
            fg='#00ff00',
            insertbackground='#00ff00',
            font=('Courier New', 10),
            wrap=tk.WORD,
            state='disabled',
            relief='flat',
            borderwidth=0,
            highlightthickness=1,
            highlightbackground='#003300',
            highlightcolor='#00ff00'
        )
        self.texto.pack(fill='both', expand=True, padx=2, pady=2)

        # Configuração de cores (tags)
        self.texto.tag_config('verde', foreground='#00ff00')
        self.texto.tag_config('verde_claro', foreground='#00ff88')
        self.texto.tag_config('verde_escuro', foreground='#005500')
        self.texto.tag_config('vermelho', foreground='#ff0040')
        self.texto.tag_config('amarelo', foreground='#ffff00')
        self.texto.tag_config('ciano', foreground='#00ffff')
        self.texto.tag_config('branco', foreground="#ffffff")
        self.texto.tag_config('abobora', foreground='#FF7518')
        self.texto.tag_config('cabecalho', foreground='#00ff00',
                              font=('Courier New', 10, 'bold'))
        self.texto.tag_config('sucesso', foreground='#00ff88',
                              font=('Courier New', 10, 'bold'))
        self.texto.tag_config('erro', foreground='#ff0040',
                              font=('Courier New', 10, 'bold'))
        self.texto.tag_config('info', foreground='#00aaff')
        self.texto.tag_config('aviso', foreground='#ffaa00')
        self.texto.tag_config('ascii_art', foreground='#00ff00',
                              font=('Courier New', 8))

    def escrever(self, texto, tag='verde'):
        self.texto.config(state='normal')
        self.texto.insert('end', texto, tag)
        self.texto.see('end')
        self.texto.config(state='disabled')

    def escrever_linha(self, texto='', tag='verde'):
        self.escrever(texto + '\n', tag)

    def limpar(self):
        self.texto.config(state='normal')
        self.texto.delete('1.0', 'end')
        self.texto.config(state='disabled')


# ========================== BARRA DE PROGRESSO HACKER ==========================

class BarraProgressoHacker(tk.Canvas):
    """Barra de progresso estilo hacker"""

    def __init__(self, parent, width=400, height=25, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg='#0a0a0a', highlightthickness=1,
                         highlightbackground='#003300', **kwargs)
        self._largura = width
        self._altura = height
        self._progresso = 0
        self._desenhar()

    def _desenhar(self):
        self.delete('all')

        # Borda
        self.create_rectangle(2, 2, self._largura - 2, self._altura - 2,
                              outline='#003300', width=1)

        # Preenchimento do progresso
        largura_preenchimento = int((self._largura - 4) * self._progresso / 100)
        if largura_preenchimento > 0:
            for i in range(largura_preenchimento):
                intensidade = int(100 + 155 * (i / max(largura_preenchimento, 1)))
                cor = f'#00{format(min(intensidade, 255), "02x")}00'
                self.create_line(i + 3, 3, i + 3, self._altura - 3, fill=cor)

        # Texto de porcentagem
        texto = (f"[{'█' * (int(self._progresso) // 5)}"
                 f"{'░' * (20 - int(self._progresso) // 5)}] "
                 f"{self._progresso:.1f}%")
        self.create_text(self._largura // 2, self._altura // 2,
                         text=texto, fill='#00ff00',
                         font=('Courier New', 8, 'bold'))

    def definir_progresso(self, valor):
        self._progresso = min(100, max(0, valor))
        self._desenhar()


# ========================== INTERFACE PRINCIPAL ==========================

class AplicativoEsteganografia:
    """Aplicação principal de Esteganografia"""

    def __init__(self):
        self.root = tk.Tk()

        self.root.title("Esteganografia Esconda Seus Segredos")
        self.root.configure(bg="#0a0a0a")

        # Maximizar / ocupar a tela
        try:
            if platform.system() == "Windows":
                self.root.after(
                    100,
                    lambda: self.root.state("zoomed")
                )
            else:
                largura = self.root.winfo_screenwidth()
                altura = self.root.winfo_screenheight()

                self.root.geometry(
                    f"{largura}x{altura}+0+0"
                )
        except Exception:
            pass

        # Variáveis
        self.imagem_atual = None
        self.motor = MotorEsteganografia()

        # Configurar estilo
        self._configurar_estilos()

        # Construir interface
        self._construir_interface()

        # Mostrar banner
        self._mostrar_banner()

    def _configurar_estilos(self):
        """Configura estilos visuais ttk"""
        estilo = ttk.Style()
        estilo.theme_use('clam')

        # Abas do Notebook
        estilo.configure('Hacker.TNotebook', background='#0a0a0a', borderwidth=0)
        estilo.configure('Hacker.TNotebook.Tab',
                         background='#0a1a0a',
                         foreground='#00ff00',
                         padding=[15, 5],
                         font=('Courier New', 10, 'bold'))
        estilo.map('Hacker.TNotebook.Tab',
                   background=[('selected', '#003300'), ('active', '#002200')],
                   foreground=[('selected', '#00ff00'), ('active', '#00ff88')])

        estilo.configure('Hacker.TFrame', background='#0a0a0a')

        estilo.configure('Hacker.TLabel',
                         background='#0a0a0a',
                         foreground='#00ff00',
                         font=('Courier New', 10))

        estilo.configure('Titulo.TLabel',
                         background='#0a0a0a',
                         foreground='#00ff00',
                         font=('Courier New', 14, 'bold'))

    def _criar_botao_hacker(self, parent, texto, comando, largura=20):
        """Cria botão personalizado estilo hacker"""
        btn = tk.Button(
            parent,
            text=texto,
            command=comando,
            bg='#001a00',
            fg='#00ff00',
            activebackground='#003300',
            activeforeground='#00ff88',
            font=('Courier New', 10, 'bold'),
            relief='flat',
            borderwidth=1,
            width=largura,
            cursor='hand2',
            highlightbackground='#003300',
            highlightcolor='#00ff00',
            highlightthickness=1
        )

        def ao_entrar(e):
            btn.config(bg='#003300', fg='#00ff88')

        def ao_sair(e):
            btn.config(bg='#001a00', fg='#00ff00')

        btn.bind('<Enter>', ao_entrar)
        btn.bind('<Leave>', ao_sair)

        return btn

    def _criar_entrada_hacker(self, parent, mostrar=None, largura=40):
        """Cria campo de entrada estilo hacker"""
        entrada = tk.Entry(
            parent,
            bg='#0a1a0a',
            fg='#00ff00',
            insertbackground='#00ff00',
            font=('Courier New', 10),
            relief='flat',
            borderwidth=0,
            width=largura,
            highlightbackground='#003300',
            highlightcolor='#00ff00',
            highlightthickness=1,
            show=mostrar
        )
        return entrada

    def _criar_texto_hacker(self, parent, altura=10, largura=50):
        """Cria widget de texto estilo hacker"""
        texto = scrolledtext.ScrolledText(
            parent,
            bg='#0a1a0a',
            fg='#00ff00',
            insertbackground='#00ff00',
            font=('Courier New', 10),
            wrap=tk.WORD,
            height=altura,
            width=largura,
            relief='flat',
            borderwidth=0,
            highlightbackground='#003300',
            highlightcolor='#00ff00',
            highlightthickness=1
        )
        return texto

    def _construir_interface(self):
        """Constrói a interface gráfica completa"""

        # ===== Cabeçalho com arte ASCII =====
        quadro_cabecalho = tk.Frame(self.root, bg='#0a0a0a')
        quadro_cabecalho.pack(fill='x', padx=5, pady=(5, 0))

        linha1 = tk.Label(quadro_cabecalho,
                          text="╔" + "═" * 96 + "╗",
                          bg='#0a0a0a', fg='#003300',
                          font=('Courier New', 8))
        linha1.pack()

        texto_titulo = ("║  ▓▓▓ Esteganografia  ▓▓▓  │  "
                        "Esconda Seus Segredos  │  "
                        "[ CLASSIFICADO - ULTRA SECRETO ]        ║")
        rotulo_titulo = tk.Label(quadro_cabecalho,
                                 text=texto_titulo,
                                 bg='#0a0a0a', fg='#00ff00',
                                 font=('Courier New', 9, 'bold'))
        rotulo_titulo.pack()

        linha2 = tk.Label(quadro_cabecalho,
                          text="╚" + "═" * 96 + "╝",
                          bg='#0a0a0a', fg='#003300',
                          font=('Courier New', 8))
        linha2.pack()

        # ===== Container principal =====
        container_principal = tk.PanedWindow(
            self.root, orient='horizontal',
            bg='#0a0a0a', sashwidth=3,
            sashrelief='flat'
        )
        container_principal.pack(fill='both', expand=True, padx=5, pady=5)

        # ===== Painel Esquerdo (Abas) =====
        quadro_esquerdo = tk.Frame(container_principal, bg='#0a0a0a')
        container_principal.add(quadro_esquerdo, width=650)

        self.caderno = ttk.Notebook(quadro_esquerdo, style='Hacker.TNotebook')
        self.caderno.pack(fill='both', expand=True)

        # Aba 1: Codificar
        self._construir_aba_codificar()

        # Aba 2: Decodificar
        self._construir_aba_decodificar()

        # Aba 3: Analisar
        self._construir_aba_analisar()

        # Aba 4: Arquivo Esteganográfico
        self._construir_aba_arquivo()

        # Aba 5: AJUDA
        self._construir_aba_ajuda()

        # ===== Painel Direito (Terminal) =====
        quadro_direito = tk.Frame(container_principal, bg='#0a0a0a')
        container_principal.add(quadro_direito, width=440)

        cabecalho_terminal = tk.Label(
            quadro_direito,
            text="┌─[ SAÍDA DO TERMINAL ]────────────────────┐",
            bg='#0a0a0a', fg='#003300',
            font=('Courier New', 9))
        cabecalho_terminal.pack(fill='x')

        self.terminal = TerminalHacker(quadro_direito)
        self.terminal.pack(fill='both', expand=True)

        rodape_terminal = tk.Label(
            quadro_direito,
            text="└───────────────────────────────────────────┘",
            bg='#0a0a0a', fg='#003300',
            font=('Courier New', 9))
        rodape_terminal.pack(fill='x')

        # ===== Barra de Status =====
        self._construir_barra_status()

    def _construir_aba_codificar(self):
        """Aba de codificação (esconder texto)"""
        aba = tk.Frame(self.caderno, bg='#0a0a0a')
        self.caderno.add(aba, text=' ⟨ CODIFICAR ⟩ ')

        tk.Label(aba,
                 text="┌─[ ESTEGANOGRAFIA DE TEXTO - CODIFICADOR ]──────────┐",
                 bg='#0a0a0a', fg='#003300',
                 font=('Courier New', 9)).pack(fill='x', padx=5, pady=(5, 0))

        # Quadro da imagem
        quadro_img = tk.Frame(aba, bg='#0a0a0a')
        quadro_img.pack(fill='x', padx=10, pady=5)

        tk.Label(quadro_img, text="[>] Imagem de entrada:",
                 bg='#0a0a0a', fg='#00ff00',
                 font=('Courier New', 10)).pack(anchor='w')

        quadro_entrada = tk.Frame(quadro_img, bg='#0a0a0a')
        quadro_entrada.pack(fill='x', pady=2)

        self.caminho_imagem_codificar = self._criar_entrada_hacker(
            quadro_entrada, largura=55)
        self.caminho_imagem_codificar.pack(
            side='left', fill='x', expand=True, padx=(0, 5))

        btn_procurar = self._criar_botao_hacker(
            quadro_entrada, "[ PROCURAR ]",
            self._procurar_imagem_codificar, largura=12)
        btn_procurar.pack(side='right')

        # Pré-visualização da imagem
        self.quadro_preview_codificar = tk.Frame(
            aba, bg='#0a1a0a',
            highlightbackground='#003300',
            highlightthickness=1)
        self.quadro_preview_codificar.pack(fill='x', padx=10, pady=5)

        self.rotulo_preview_codificar = tk.Label(
            self.quadro_preview_codificar,
            text="[ NENHUMA IMAGEM CARREGADA ]",
            bg='#0a1a0a', fg='#005500',
            font=('Courier New', 10),
            height=3)
        self.rotulo_preview_codificar.pack(pady=10)

        # Mensagem secreta
        quadro_msg = tk.Frame(aba, bg='#0a0a0a')
        quadro_msg.pack(fill='both', expand=True, padx=10, pady=5)

        tk.Label(quadro_msg, text="[>] Mensagem secreta:",
                 bg='#0a0a0a', fg='#00ff00',
                 font=('Courier New', 10)).pack(anchor='w')

        self.mensagem_codificar = self._criar_texto_hacker(quadro_msg, altura=6)
        self.mensagem_codificar.pack(fill='both', expand=True, pady=2)

        # Senha
        quadro_senha = tk.Frame(aba, bg='#0a0a0a')
        quadro_senha.pack(fill='x', padx=10, pady=5)

        tk.Label(quadro_senha, text="[>] Senha (opcional):",
                 bg='#0a0a0a', fg='#00ff00',
                 font=('Courier New', 10)).pack(anchor='w')

        self.senha_codificar = self._criar_entrada_hacker(
            quadro_senha, mostrar='•', largura=40)
        self.senha_codificar.pack(fill='x', pady=2)

        # Progresso
        self.progresso_codificar = BarraProgressoHacker(aba, width=600)
        self.progresso_codificar.pack(padx=10, pady=5)

        # Botão codificar
        quadro_btn = tk.Frame(aba, bg='#0a0a0a')
        quadro_btn.pack(fill='x', padx=10, pady=5)

        btn_codificar = self._criar_botao_hacker(
            quadro_btn, "◄◄ CODIFICAR MENSAGEM ►►",
            self._codificar_texto, largura=28)
        btn_codificar.pack(pady=5)

        tk.Label(aba,
                 text="└────────────────────────────────────────────────────┘",
                 bg='#0a0a0a', fg='#003300',
                 font=('Courier New', 9)).pack(fill='x', padx=5)

    def _construir_aba_decodificar(self):
        """Aba de decodificação (extrair texto)"""
        aba = tk.Frame(self.caderno, bg='#0a0a0a')
        self.caderno.add(aba, text=' ⟨ DECODIFICAR ⟩ ')

        tk.Label(aba,
                 text="┌─[ ESTEGANOGRAFIA DE TEXTO - DECODIFICADOR ]────────┐",
                 bg='#0a0a0a', fg='#003300',
                 font=('Courier New', 9)).pack(fill='x', padx=5, pady=(5, 0))

        # Imagem
        quadro_img = tk.Frame(aba, bg='#0a0a0a')
        quadro_img.pack(fill='x', padx=10, pady=5)

        tk.Label(quadro_img, text="[>] Imagem com dados ocultos:",
                 bg='#0a0a0a', fg='#00ff00',
                 font=('Courier New', 10)).pack(anchor='w')

        quadro_entrada = tk.Frame(quadro_img, bg='#0a0a0a')
        quadro_entrada.pack(fill='x', pady=2)

        self.caminho_imagem_decodificar = self._criar_entrada_hacker(
            quadro_entrada, largura=55)
        self.caminho_imagem_decodificar.pack(
            side='left', fill='x', expand=True, padx=(0, 5))

        btn_procurar = self._criar_botao_hacker(
            quadro_entrada, "[ PROCURAR ]",
            self._procurar_imagem_decodificar, largura=12)
        btn_procurar.pack(side='right')

        # Senha
        quadro_senha = tk.Frame(aba, bg='#0a0a0a')
        quadro_senha.pack(fill='x', padx=10, pady=5)

        tk.Label(quadro_senha, text="[>] Senha (se criptografado):",
                 bg='#0a0a0a', fg='#00ff00',
                 font=('Courier New', 10)).pack(anchor='w')

        self.senha_decodificar = self._criar_entrada_hacker(
            quadro_senha, mostrar='•', largura=40)
        self.senha_decodificar.pack(fill='x', pady=2)

        # Progresso
        self.progresso_decodificar = BarraProgressoHacker(aba, width=600)
        self.progresso_decodificar.pack(padx=10, pady=5)

        # Botão decodificar
        btn_decodificar = self._criar_botao_hacker(
            aba, "◄◄ DECODIFICAR MENSAGEM ►►",
            self._decodificar_texto, largura=28)
        btn_decodificar.pack(pady=5)

        # Resultado
        quadro_resultado = tk.Frame(aba, bg='#0a0a0a')
        quadro_resultado.pack(fill='both', expand=True, padx=10, pady=5)

        tk.Label(quadro_resultado, text="[>] Mensagem extraída:",
                 bg='#0a0a0a', fg='#00ff00',
                 font=('Courier New', 10)).pack(anchor='w')

        self.resultado_decodificar = self._criar_texto_hacker(
            quadro_resultado, altura=8)
        self.resultado_decodificar.pack(fill='both', expand=True, pady=2)

        tk.Label(aba,
                 text="└────────────────────────────────────────────────────┘",
                 bg='#0a0a0a', fg='#003300',
                 font=('Courier New', 9)).pack(fill='x', padx=5)

    def _construir_aba_analisar(self):
        """Aba de análise forense"""
        aba = tk.Frame(self.caderno, bg='#0a0a0a')
        self.caderno.add(aba, text=' ⟨ ANALISAR ⟩ ')

        tk.Label(aba,
                 text="┌─[ ANÁLISE DE IMAGEM - FORENSE ]─────────────────────┐",
                 bg='#0a0a0a', fg='#003300',
                 font=('Courier New', 9)).pack(fill='x', padx=5, pady=(5, 0))

        # Imagem
        quadro_img = tk.Frame(aba, bg='#0a0a0a')
        quadro_img.pack(fill='x', padx=10, pady=5)

        tk.Label(quadro_img, text="[>] Imagem para análise:",
                 bg='#0a0a0a', fg='#00ff00',
                 font=('Courier New', 10)).pack(anchor='w')

        quadro_entrada = tk.Frame(quadro_img, bg='#0a0a0a')
        quadro_entrada.pack(fill='x', pady=2)

        self.caminho_imagem_analisar = self._criar_entrada_hacker(
            quadro_entrada, largura=55)
        self.caminho_imagem_analisar.pack(
            side='left', fill='x', expand=True, padx=(0, 5))

        btn_procurar = self._criar_botao_hacker(
            quadro_entrada, "[ PROCURAR ]",
            self._procurar_imagem_analisar, largura=12)
        btn_procurar.pack(side='right')

        # Botões de análise
        quadro_btn = tk.Frame(aba, bg='#0a0a0a')
        quadro_btn.pack(fill='x', padx=10, pady=5)

        btn_analisar = self._criar_botao_hacker(
            quadro_btn, "◄◄ ANALISAR IMAGEM ►►",
            self._analisar_imagem, largura=25)
        btn_analisar.pack(side='left', padx=5)

        btn_info = self._criar_botao_hacker(
            quadro_btn, "[ INFO DA IMAGEM ]",
            self._mostrar_info_imagem, largura=18)
        btn_info.pack(side='left', padx=5)

        # Resultado da análise
        quadro_resultado = tk.Frame(aba, bg='#0a0a0a')
        quadro_resultado.pack(fill='both', expand=True, padx=10, pady=5)

        self.terminal_analise = TerminalHacker(quadro_resultado)
        self.terminal_analise.pack(fill='both', expand=True)

        tk.Label(aba,
                 text="└─────────────────────────────────────────────────────┘",
                 bg='#0a0a0a', fg='#003300',
                 font=('Courier New', 9)).pack(fill='x', padx=5)

    def _construir_aba_arquivo(self):
        """Aba de esteganografia de arquivos"""
        aba = tk.Frame(self.caderno, bg='#0a0a0a')
        self.caderno.add(aba, text=' ⟨ ARQ. ESTEG ⟩ ')

        tk.Label(aba,
                 text="┌─[ ESTEGANOGRAFIA DE ARQUIVOS ]──────────────────────┐",
                 bg='#0a0a0a', fg='#003300',
                 font=('Courier New', 9)).pack(fill='x', padx=5, pady=(5, 0))

        # Imagem de cobertura
        quadro_img = tk.Frame(aba, bg='#0a0a0a')
        quadro_img.pack(fill='x', padx=10, pady=5)

        tk.Label(quadro_img, text="[>] Imagem de cobertura:",
                 bg='#0a0a0a', fg='#00ff00',
                 font=('Courier New', 10)).pack(anchor='w')

        quadro_entrada1 = tk.Frame(quadro_img, bg='#0a0a0a')
        quadro_entrada1.pack(fill='x', pady=2)

        self.caminho_imagem_arquivo = self._criar_entrada_hacker(
            quadro_entrada1, largura=55)
        self.caminho_imagem_arquivo.pack(
            side='left', fill='x', expand=True, padx=(0, 5))

        btn_procurar1 = self._criar_botao_hacker(
            quadro_entrada1, "[ PROCURAR ]",
            self._procurar_imagem_arquivo, largura=12)
        btn_procurar1.pack(side='right')

        # Arquivo para esconder
        quadro_arq = tk.Frame(aba, bg='#0a0a0a')
        quadro_arq.pack(fill='x', padx=10, pady=5)

        tk.Label(quadro_arq, text="[>] Arquivo para esconder:",
                 bg='#0a0a0a', fg='#00ff00',
                 font=('Courier New', 10)).pack(anchor='w')

        quadro_entrada2 = tk.Frame(quadro_arq, bg='#0a0a0a')
        quadro_entrada2.pack(fill='x', pady=2)

        self.caminho_arquivo_esconder = self._criar_entrada_hacker(
            quadro_entrada2, largura=55)
        self.caminho_arquivo_esconder.pack(
            side='left', fill='x', expand=True, padx=(0, 5))

        btn_procurar2 = self._criar_botao_hacker(
            quadro_entrada2, "[ PROCURAR ]",
            self._procurar_arquivo_esconder, largura=12)
        btn_procurar2.pack(side='right')

        # Senha
        quadro_senha = tk.Frame(aba, bg='#0a0a0a')
        quadro_senha.pack(fill='x', padx=10, pady=5)

        tk.Label(quadro_senha, text="[>] Senha (opcional):",
                 bg='#0a0a0a', fg='#00ff00',
                 font=('Courier New', 10)).pack(anchor='w')

        self.senha_arquivo = self._criar_entrada_hacker(
            quadro_senha, mostrar='•', largura=40)
        self.senha_arquivo.pack(fill='x', pady=2)

        # Progresso
        self.progresso_arquivo = BarraProgressoHacker(aba, width=600)
        self.progresso_arquivo.pack(padx=10, pady=5)

        # Botões
        quadro_btn = tk.Frame(aba, bg='#0a0a0a')
        quadro_btn.pack(fill='x', padx=10, pady=5)

        btn_esconder = self._criar_botao_hacker(
            quadro_btn, "◄◄ ESCONDER ARQUIVO ►►",
            self._codificar_arquivo, largura=22)
        btn_esconder.pack(side='left', padx=5)

        btn_extrair = self._criar_botao_hacker(
            quadro_btn, "◄◄ EXTRAIR ARQUIVO ►►",
            self._decodificar_arquivo, largura=22)
        btn_extrair.pack(side='left', padx=5)

        tk.Label(aba,
                 text="└─────────────────────────────────────────────────────┘",
                 bg='#0a0a0a', fg='#003300',
                 font=('Courier New', 9)).pack(fill='x', padx=5)

    def _construir_aba_ajuda(self):
        """Aba de ajuda com explicação completa de como funciona"""
        aba = tk.Frame(self.caderno, bg='#0a0a0a')
        self.caderno.add(aba, text=' ⟨ AJUDA ⟩ ')

        tk.Label(aba,
                 text="┌─[ MANUAL DE AJUDA - COMO FUNCIONA ]─────────────────┐",
                 bg='#0a0a0a', fg='#003300',
                 font=('Courier New', 9)).pack(fill='x', padx=5, pady=(5, 0))

        # Terminal de ajuda com scroll
        quadro_ajuda = tk.Frame(aba, bg='#0a0a0a')
        quadro_ajuda.pack(fill='both', expand=True, padx=10, pady=5)

        terminal_ajuda = TerminalHacker(quadro_ajuda)
        terminal_ajuda.pack(fill='both', expand=True)

        # Conteúdo da ajuda
        terminal_ajuda.escrever_linha(
            "╔══════════════════════════════════════════════════╗", 'cabecalho')
        terminal_ajuda.escrever_linha(
            "║       MANUAL COMPLETO DE AJUDA                   ║", 'cabecalho')
        terminal_ajuda.escrever_linha(
            "║      Esteganografia: Esconda Seus Segredos       ║", 'cabecalho')
        terminal_ajuda.escrever_linha(
            "╚══════════════════════════════════════════════════╝", 'cabecalho')
        terminal_ajuda.escrever_linha("")

        # ── O QUE É ESTEGANOGRAFIA ──
        terminal_ajuda.escrever_linha(
            "  ═══ O QUE É ESTEGANOGRAFIA? ═══════════════════", 'amarelo')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  Esteganografia é a arte de esconder informações", 'verde')
        terminal_ajuda.escrever_linha(
            "  dentro de outros arquivos (como imagens) de forma", 'verde')
        terminal_ajuda.escrever_linha(
            "  que ninguém perceba que existe algo oculto.", 'verde')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  Diferente da criptografia (que embaralha dados),", 'verde')
        terminal_ajuda.escrever_linha(
            "  a esteganografia ESCONDE a própria existência", 'verde')
        terminal_ajuda.escrever_linha(
            "  da mensagem secreta.", 'verde')
        terminal_ajuda.escrever_linha("")

        # ── COMO FUNCIONA (LSB) ──
        terminal_ajuda.escrever_linha(
            "  ═══ COMO FUNCIONA? (Método LSB) ═══════════════", 'amarelo')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  Este programa usa o método LSB (Bit Menos", 'verde')
        terminal_ajuda.escrever_linha(
            "  Significativo). Funciona assim:", 'verde')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  1. Cada pixel de uma imagem tem valores de cor", 'ciano')
        terminal_ajuda.escrever_linha(
            "     (Vermelho, Verde, Azul) de 0 a 255.", 'ciano')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  2. Em binário, 255 = 11111111. O último bit", 'ciano')
        terminal_ajuda.escrever_linha(
            "     (o menos significativo) pode ser alterado", 'ciano')
        terminal_ajuda.escrever_linha(
            "     sem que o olho humano perceba diferença.", 'ciano')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  3. Exemplo: cor 11111110 e 11111111 são", 'ciano')
        terminal_ajuda.escrever_linha(
            "     visualmente idênticas! (254 vs 255)", 'ciano')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  4. A mensagem é convertida em bits (0s e 1s)", 'ciano')
        terminal_ajuda.escrever_linha(
            "     e cada bit é escondido no último bit de", 'ciano')
        terminal_ajuda.escrever_linha(
            "     cada canal de cor de cada pixel.", 'ciano')
        terminal_ajuda.escrever_linha("")

        # ── ABA CODIFICAR ──
        terminal_ajuda.escrever_linha(
            "  ═══ ABA 'CODIFICAR' ════════════════════════════", 'amarelo')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  Serve para ESCONDER TEXTO dentro de uma imagem.", 'verde_claro')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  Passo a passo:", 'branco')
        terminal_ajuda.escrever_linha(
            "  1. Clique em [PROCURAR] e escolha uma imagem", 'verde')
        terminal_ajuda.escrever_linha(
            "     (PNG, JPG, BMP, TIFF).", 'verde')
        terminal_ajuda.escrever_linha(
            "  2. Digite sua mensagem secreta no campo de texto.", 'verde')
        terminal_ajuda.escrever_linha(
            "  3. (Opcional) Digite uma senha para criptografar.", 'verde')
        terminal_ajuda.escrever_linha(
            "  4. Clique em 'CODIFICAR MENSAGEM'.", 'verde')
        terminal_ajuda.escrever_linha(
            "  5. Escolha onde salvar a nova imagem PNG.", 'verde')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  ⚠ A imagem de saída é SEMPRE em formato PNG", 'aviso')
        terminal_ajuda.escrever_linha(
            "    (formato sem perdas, preserva os bits ocultos).", 'aviso')
        terminal_ajuda.escrever_linha("")

        # ── ABA DECODIFICAR ──
        terminal_ajuda.escrever_linha(
            "  ═══ ABA 'DECODIFICAR' ══════════════════════════", 'amarelo')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  Serve para EXTRAIR TEXTO de uma imagem que", 'verde_claro')
        terminal_ajuda.escrever_linha(
            "  contenha dados ocultos.", 'verde_claro')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  Passo a passo:", 'branco')
        terminal_ajuda.escrever_linha(
            "  1. Clique em [PROCURAR] e escolha a imagem PNG", 'verde')
        terminal_ajuda.escrever_linha(
            "     que contém a mensagem oculta.", 'verde')
        terminal_ajuda.escrever_linha(
            "  2. Se a mensagem foi criptografada, digite a", 'verde')
        terminal_ajuda.escrever_linha(
            "     mesma senha usada na codificação.", 'verde')
        terminal_ajuda.escrever_linha(
            "  3. Clique em 'DECODIFICAR MENSAGEM'.", 'verde')
        terminal_ajuda.escrever_linha(
            "  4. A mensagem aparecerá no campo de resultado.", 'verde')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  ⚠ Se a senha estiver errada, o texto extraído", 'aviso')
        terminal_ajuda.escrever_linha(
            "    será ilegível (caracteres embaralhados).", 'aviso')
        terminal_ajuda.escrever_linha("")

        # ── ABA ANALISAR ──
        terminal_ajuda.escrever_linha(
            "  ═══ ABA 'ANALISAR' ═════════════════════════════", 'amarelo')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  Serve para INVESTIGAR uma imagem e detectar", 'verde_claro')
        terminal_ajuda.escrever_linha(
            "  se ela contém dados ocultos.", 'verde_claro')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  O que a análise mostra:", 'branco')
        terminal_ajuda.escrever_linha(
            "  • Se existem dados ocultos no formato ZSteg", 'verde')
        terminal_ajuda.escrever_linha(
            "  • Análise LSB (distribuição dos bits menos", 'verde')
        terminal_ajuda.escrever_linha(
            "    significativos)", 'verde')
        terminal_ajuda.escrever_linha(
            "  • Teste Chi-Quadrado (detecta manipulação)", 'verde')
        terminal_ajuda.escrever_linha(
            "  • Entropia da imagem", 'verde')
        terminal_ajuda.escrever_linha(
            "  • Tipo e tamanho dos dados ocultos", 'verde')
        terminal_ajuda.escrever_linha(
            "  • Se os dados estão criptografados", 'verde')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  O botão 'INFO DA IMAGEM' mostra detalhes:", 'branco')
        terminal_ajuda.escrever_linha(
            "  • Dimensões, formato, tamanho do arquivo", 'verde')
        terminal_ajuda.escrever_linha(
            "  • Capacidade máxima de armazenamento oculto", 'verde')
        terminal_ajuda.escrever_linha("")

        # ── ABA ARQUIVO ESTEGANOGRÁFICO ──
        terminal_ajuda.escrever_linha(
            "  ═══ ABA 'ARQ. ESTEG' ═══════════════════════════", 'amarelo')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  Serve para ESCONDER QUALQUER ARQUIVO dentro", 'verde_claro')
        terminal_ajuda.escrever_linha(
            "  de uma imagem (documentos, PDFs, ZIPs, etc).", 'verde_claro')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  Para ESCONDER um arquivo:", 'branco')
        terminal_ajuda.escrever_linha(
            "  1. Selecione a imagem de cobertura (quanto", 'verde')
        terminal_ajuda.escrever_linha(
            "     maior a imagem, mais dados cabem).", 'verde')
        terminal_ajuda.escrever_linha(
            "  2. Selecione o arquivo que deseja esconder.", 'verde')
        terminal_ajuda.escrever_linha(
            "  3. (Opcional) Digite uma senha.", 'verde')
        terminal_ajuda.escrever_linha(
            "  4. Clique em 'ESCONDER ARQUIVO'.", 'verde')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  Para EXTRAIR um arquivo:", 'branco')
        terminal_ajuda.escrever_linha(
            "  1. Selecione a imagem que contém o arquivo.", 'verde')
        terminal_ajuda.escrever_linha(
            "  2. Se usou senha, digite-a.", 'verde')
        terminal_ajuda.escrever_linha(
            "  3. Clique em 'EXTRAIR ARQUIVO'.", 'verde')
        terminal_ajuda.escrever_linha(
            "  4. Escolha onde salvar o arquivo extraído.", 'verde')
        terminal_ajuda.escrever_linha("")

        # ── CRIPTOGRAFIA ──
        terminal_ajuda.escrever_linha(
            "  ═══ SOBRE A CRIPTOGRAFIA ═══════════════════════", 'amarelo')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  A criptografia é OPCIONAL mas recomendada.", 'verde_claro')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  • Usa criptografia XOR com chave derivada de", 'verde')
        terminal_ajuda.escrever_linha(
            "    SHA-256 (256 bits) a partir da sua senha.", 'verde')
        terminal_ajuda.escrever_linha(
            "  • Mesmo que alguém descubra que há dados", 'verde')
        terminal_ajuda.escrever_linha(
            "    ocultos, sem a senha não conseguirá ler.", 'verde')
        terminal_ajuda.escrever_linha(
            "  • A mesma senha usada para codificar deve", 'verde')
        terminal_ajuda.escrever_linha(
            "    ser usada para decodificar.", 'verde')
        terminal_ajuda.escrever_linha("")

        # ── CAPACIDADE ──
        terminal_ajuda.escrever_linha(
            "  ═══ CAPACIDADE DE ARMAZENAMENTO ════════════════", 'amarelo')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  A quantidade de dados que cabe depende do", 'verde')
        terminal_ajuda.escrever_linha(
            "  tamanho da imagem:", 'verde')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  • Cada pixel pode guardar 3 bits (R, G, B)", 'ciano')
        terminal_ajuda.escrever_linha(
            "  • Imagem 800x600 = 480.000 pixels", 'ciano')
        terminal_ajuda.escrever_linha(
            "    = 1.440.000 bits = ~175 KB de dados", 'ciano')
        terminal_ajuda.escrever_linha(
            "  • Imagem 1920x1080 = 2.073.600 pixels", 'ciano')
        terminal_ajuda.escrever_linha(
            "    = 6.220.800 bits = ~760 KB de dados", 'ciano')
        terminal_ajuda.escrever_linha(
            "  • Imagem 4000x3000 = 12.000.000 pixels", 'ciano')
        terminal_ajuda.escrever_linha(
            "    = 36.000.000 bits = ~4.3 MB de dados", 'ciano')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  ⚠ Use a aba 'ANALISAR' > 'INFO DA IMAGEM'", 'aviso')
        terminal_ajuda.escrever_linha(
            "    para ver a capacidade exata.", 'aviso')
        terminal_ajuda.escrever_linha("")

        # ── DICAS IMPORTANTES ──
        terminal_ajuda.escrever_linha(
            "  ═══ DICAS IMPORTANTES ══════════════════════════", 'amarelo')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  ✓ SEMPRE salve como PNG (sem compressão com", 'sucesso')
        terminal_ajuda.escrever_linha(
            "    perda). JPEG destrói os dados ocultos!", 'sucesso')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  ✓ Use imagens grandes para esconder mais dados.", 'sucesso')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  ✓ Use senha para proteção extra.", 'sucesso')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  ✓ Não edite/redimensione a imagem após", 'sucesso')
        terminal_ajuda.escrever_linha(
            "    codificar, pois isso destrói os dados.", 'sucesso')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  ✓ Não publique em redes sociais que", 'sucesso')
        terminal_ajuda.escrever_linha(
            "    recomprimem imagens (Instagram, WhatsApp).", 'sucesso')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  ✗ NÃO use JPEG como saída - a compressão", 'erro')
        terminal_ajuda.escrever_linha(
            "    com perda destrói os bits ocultos!", 'erro')
        terminal_ajuda.escrever_linha("")

        # ── TERMINAL ──
        terminal_ajuda.escrever_linha(
            "  ═══ SOBRE O TERMINAL (PAINEL DIREITO) ══════════", 'amarelo')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  O painel à direita é o Terminal de Saída.", 'verde')
        terminal_ajuda.escrever_linha(
            "  Ele exibe em tempo real:", 'verde')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  • Logs de todas as operações realizadas", 'ciano')
        terminal_ajuda.escrever_linha(
            "  • Mensagens de sucesso e erro", 'ciano')
        terminal_ajuda.escrever_linha(
            "  • Detalhes técnicos dos processos", 'ciano')
        terminal_ajuda.escrever_linha(
            "  • Informações sobre arquivos processados", 'ciano')
        terminal_ajuda.escrever_linha("")

        # ── DEPENDÊNCIAS ──
        terminal_ajuda.escrever_linha(
            "  ═══ DEPENDÊNCIAS NECESSÁRIAS ════════════════════", 'amarelo')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  Para funcionar, instale:", 'verde')
        terminal_ajuda.escrever_linha(
            "  $ pip install Pillow numpy", 'branco')
        terminal_ajuda.escrever_linha("")
        terminal_ajuda.escrever_linha(
            "  • Pillow: manipulação de imagens", 'ciano')
        terminal_ajuda.escrever_linha(
            "  • NumPy: operações rápidas com arrays", 'ciano')
        terminal_ajuda.escrever_linha(
            "  • tkinter: interface gráfica (já vem com Python)", 'ciano')
        terminal_ajuda.escrever_linha("")

        terminal_ajuda.escrever_linha(
            "  ══════════════════════════════════════════════════", 'verde_escuro')
        terminal_ajuda.escrever_linha(
            "  Desenvolvido com ♥ em Python", 'verde_escuro')
        terminal_ajuda.escrever_linha(
            "  Esteganografia  - Edição Hacker", 'verde_escuro')
        terminal_ajuda.escrever_linha(
            "  ══════════════════════════════════════════════════", 'verde_escuro')

        tk.Label(aba,
                 text="└─────────────────────────────────────────────────────┘",
                 bg='#0a0a0a', fg='#003300',
                 font=('Courier New', 9)).pack(fill='x', padx=5)

    def _construir_barra_status(self):
        """Barra de status inferior"""
        quadro_status = tk.Frame(self.root, bg='#001100')
        quadro_status.pack(fill='x', side='bottom')

        self.rotulo_status = tk.Label(
            quadro_status,
            text="  ▶ SISTEMA PRONTO  │  Esteganografia  │  [CONEXÃO SEGURA]",
            bg='#001100', fg='#00aa00',
            font=('Courier New', 9),
            anchor='w'
        )
        self.rotulo_status.pack(fill='x', padx=5, pady=2)

        self.estado_piscar = True
        self._piscar_status()

    def _piscar_status(self):
        """Efeito de piscar no indicador de status"""
        indicador = "●" if self.estado_piscar else "○"
        texto_base = ("SISTEMA PRONTO  │  Esteganografia   │  "
                      "[CONEXÃO SEGURA]")
        self.rotulo_status.config(text=f"  {indicador} {texto_base}")
        self.estado_piscar = not self.estado_piscar
        self.root.after(1000, self._piscar_status)

    def _mostrar_banner(self):
        """Mostra banner ASCII no terminal"""
        banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  ███████╗███████╗████████╗███████╗ ██████╗ ██████╗  █████╗ ███████╗  ║
║  ██╔════╝██╔════╝╚══██╔══╝██╔════╝██╔════╝ ██╔══██╗██╔══██╗██╔════╝  ║
║  █████╗  ███████╗   ██║   █████╗  ██║  ███╗██████╔╝███████║█████╗    ║
║  ██╔══╝  ╚════██║   ██║   ██╔══╝  ██║   ██║██╔══██╗██╔══██║██╔══╝    ║
║  ███████╗███████║   ██║   ███████╗╚██████╔╝██║  ██║██║  ██║██║       ║
║  ╚══════╝╚══════╝   ╚═╝   ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝       ║
║                                                                      ║
║                            ESTEGANOGRAFIA                            ║
║                       [ Esconda Seus Segredos ]                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
        self.terminal.escrever_linha(banner, 'cabecalho')
        self.terminal.escrever_linha("  [*] Sistema inicializado...", 'verde')
        self.terminal.escrever_linha(
            "  [*] Motor de esteganografia carregado", 'verde')
        self.terminal.escrever_linha(
            "  [*] Algoritmo LSB pronto", 'verde')
        self.terminal.escrever_linha(
            "  [*] Módulo de criptografia XOR carregado", 'verde')
        self.terminal.escrever_linha(
            "  [*] Aguardando comandos...", 'verde_claro')
        self.terminal.escrever_linha("")
        self.terminal.escrever_linha(
            "  ─────────────────────────────────", 'verde_escuro')
        self.terminal.escrever_linha("")

    def _definir_status(self, texto, cor='#00aa00'):
        """Atualiza barra de status"""
        indicador = "●"
        self.rotulo_status.config(
            text=f"  {indicador}  {texto}",
            fg=cor
        )

    def _registrar(self, mensagem, tag='verde'):
        """Registra mensagem no terminal"""
        marca_tempo = time.strftime('%H:%M:%S')
        self.terminal.escrever_linha(
            f"  [{marca_tempo}] {mensagem}", tag)

    # ==================== FUNÇÕES DE NAVEGAÇÃO ====================

    def _procurar_imagem_codificar(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar Imagem",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("Todos os arquivos", "*.*")
            ]
        )
        if caminho:
            self.caminho_imagem_codificar.delete(0, 'end')
            self.caminho_imagem_codificar.insert(0, caminho)
            self._atualizar_preview_codificar(caminho)
            self._registrar(
                f"Imagem carregada: {os.path.basename(caminho)}", 'ciano')

    def _procurar_imagem_decodificar(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar Imagem",
            filetypes=[
                ("Imagens PNG", "*.png"),
                ("Todos os arquivos", "*.*")
            ]
        )
        if caminho:
            self.caminho_imagem_decodificar.delete(0, 'end')
            self.caminho_imagem_decodificar.insert(0, caminho)
            self._registrar(
                f"Imagem para decodificação: {os.path.basename(caminho)}",
                'ciano')

    def _procurar_imagem_analisar(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar Imagem",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("Todos os arquivos", "*.*")
            ]
        )
        if caminho:
            self.caminho_imagem_analisar.delete(0, 'end')
            self.caminho_imagem_analisar.insert(0, caminho)
            self._registrar(
                f"Imagem para análise: {os.path.basename(caminho)}", 'ciano')

    def _procurar_imagem_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar Imagem de Cobertura",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("Todos os arquivos", "*.*")
            ]
        )
        if caminho:
            self.caminho_imagem_arquivo.delete(0, 'end')
            self.caminho_imagem_arquivo.insert(0, caminho)
            self._registrar(
                f"Imagem de cobertura: {os.path.basename(caminho)}", 'ciano')

    def _procurar_arquivo_esconder(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar Arquivo para Esconder")
        if caminho:
            self.caminho_arquivo_esconder.delete(0, 'end')
            self.caminho_arquivo_esconder.insert(0, caminho)
            tamanho = os.path.getsize(caminho)
            self._registrar(
                f"Arquivo selecionado: {os.path.basename(caminho)} "
                f"({tamanho} bytes)", 'ciano')

    def _atualizar_preview_codificar(self, caminho_imagem):
        """Atualiza pré-visualização da imagem"""
        try:
            info = MotorEsteganografia.obter_info_imagem(caminho_imagem)

            texto_preview = (
                f"  📷 {os.path.basename(caminho_imagem)}\n"
                f"  Dimensões: {info['largura']}x{info['altura']} │ "
                f"Modo: {info['modo']} │ "
                f"Tamanho: {info['tamanho_arquivo'] / 1024:.1f} KB\n"
                f"  Capacidade: {info['capacidade_kb']:.1f} KB │ "
                f"Pixels: {info['total_pixels']:,}"
            )

            self.rotulo_preview_codificar.config(
                text=texto_preview,
                fg='#00ff00',
                justify='left'
            )
        except Exception as e:
            self.rotulo_preview_codificar.config(
                text=f"  [ERRO] {str(e)}",
                fg='#ff0040'
            )

    # ==================== FUNÇÕES DE CODIFICAÇÃO/DECODIFICAÇÃO ====================

    def _codificar_texto(self):
        """Codifica texto na imagem"""
        caminho_imagem = self.caminho_imagem_codificar.get().strip()
        mensagem = self.mensagem_codificar.get('1.0', 'end').strip()
        senha = self.senha_codificar.get().strip() or None

        if not caminho_imagem:
            self._registrar("[ERRO] Selecione uma imagem!", 'erro')
            messagebox.showerror("Erro", "Selecione uma imagem de entrada!")
            return

        if not mensagem:
            self._registrar("[ERRO] Digite uma mensagem!", 'erro')
            messagebox.showerror("Erro", "Digite uma mensagem para esconder!")
            return

        if not os.path.exists(caminho_imagem):
            self._registrar("[ERRO] Arquivo não encontrado!", 'erro')
            messagebox.showerror("Erro", "Arquivo de imagem não encontrado!")
            return

        caminho_saida = filedialog.asksaveasfilename(
            title="Salvar Imagem com Dados Ocultos",
            defaultextension=".png",
            filetypes=[("PNG", "*.png")]
        )

        if not caminho_saida:
            return

        self._definir_status("CODIFICANDO... ████████░░░░", '#ffaa00')
        self._registrar("Iniciando processo de codificação...", 'amarelo')
        self._registrar(
            f"  Mensagem: {len(mensagem)} caracteres", 'ciano')
        self._registrar(
            f"  Criptografia: "
            f"{'SIM (XOR-SHA256)' if senha else 'NÃO'}", 'ciano')

        def thread_codificar():
            try:
                def callback_progresso(p):
                    self.root.after(
                        0, self.progresso_codificar.definir_progresso, p)

                MotorEsteganografia.codificar_texto(
                    caminho_imagem, caminho_saida, mensagem,
                    senha, callback_progresso
                )

                self.root.after(
                    0, self._codificacao_sucesso, caminho_saida)

            except Exception as e:
                self.root.after(0, self._codificacao_erro, str(e))

        thread = threading.Thread(target=thread_codificar, daemon=True)
        thread.start()

    def _codificacao_sucesso(self, caminho_saida):
        """Callback de sucesso da codificação"""
        self.progresso_codificar.definir_progresso(100)
        self._registrar(
            "[SUCESSO] Mensagem escondida com sucesso!", 'sucesso')
        self._registrar(
            f"  Arquivo salvo: {os.path.basename(caminho_saida)}",
            'verde_claro')
        self._registrar(
            f"  Tamanho: {os.path.getsize(caminho_saida) / 1024:.1f} KB",
            'verde_claro')
        self._definir_status("CODIFICAÇÃO CONCLUÍDA ✓", '#00ff00')

        self.terminal.escrever_linha("")
        self.terminal.escrever_linha(
            "  ╔═══════════════════════════════════╗", 'sucesso')
        self.terminal.escrever_linha(
            "  ║   ✓ CODIFICAÇÃO BEM-SUCEDIDA!    ║", 'sucesso')
        self.terminal.escrever_linha(
            "  ╚═══════════════════════════════════╝", 'sucesso')
        self.terminal.escrever_linha("")

    def _codificacao_erro(self, msg_erro):
        """Callback de erro da codificação"""
        self._registrar(f"[ERRO] {msg_erro}", 'erro')
        self._definir_status(f"ERRO: {msg_erro}", '#ff0040')
        messagebox.showerror("Erro na Codificação", msg_erro)

    def _decodificar_texto(self):
        """Decodifica texto da imagem"""
        caminho_imagem = self.caminho_imagem_decodificar.get().strip()
        senha = self.senha_decodificar.get().strip() or None

        if not caminho_imagem:
            self._registrar("[ERRO] Selecione uma imagem!", 'erro')
            messagebox.showerror("Erro", "Selecione uma imagem!")
            return

        if not os.path.exists(caminho_imagem):
            self._registrar("[ERRO] Arquivo não encontrado!", 'erro')
            messagebox.showerror("Erro", "Arquivo não encontrado!")
            return

        self._definir_status("DECODIFICANDO... ████████░░░░", '#ffaa00')
        self._registrar("Iniciando processo de decodificação...", 'amarelo')

        def thread_decodificar():
            try:
                def callback_progresso(p):
                    self.root.after(
                        0, self.progresso_decodificar.definir_progresso, p)

                resultado = MotorEsteganografia.decodificar(
                    caminho_imagem, senha, callback_progresso)
                self.root.after(
                    0, self._decodificacao_sucesso, resultado)

            except Exception as e:
                self.root.after(0, self._decodificacao_erro, str(e))

        thread = threading.Thread(target=thread_decodificar, daemon=True)
        thread.start()

    def _decodificacao_sucesso(self, resultado):
        """Callback de sucesso da decodificação"""
        self.progresso_decodificar.definir_progresso(100)

        if resultado['tipo'] == 'texto':
            self.resultado_decodificar.delete('1.0', 'end')
            self.resultado_decodificar.insert('1.0', resultado['texto'])

            self._registrar(
                "[SUCESSO] Mensagem extraída com sucesso!", 'sucesso')
            self._registrar(f"  Tipo: Texto", 'ciano')
            self._registrar(
                f"  Tamanho: {resultado['tamanho']} bytes", 'ciano')
            self._registrar(
                f"  Criptografado: "
                f"{'Sim' if resultado['criptografado'] else 'Não'}",
                'ciano')

            self.terminal.escrever_linha("")
            self.terminal.escrever_linha(
                "  ╔════════════════════════════════════╗", 'sucesso')
            self.terminal.escrever_linha(
                "  ║  ✓ DECODIFICAÇÃO BEM-SUCEDIDA!    ║", 'sucesso')
            self.terminal.escrever_linha(
                "  ╚════════════════════════════════════╝", 'sucesso')
            self.terminal.escrever_linha("")
            self.terminal.escrever_linha(
                
                f"Mensagem\n\n{resultado['texto']}", 'abobora')
            self.terminal.escrever_linha("")
            
        else:
            self._registrar(
                "[INFO] Dados do tipo arquivo detectados.", 'info')
            self._registrar(
                "[INFO] Use a aba 'ARQ. ESTEG' para extrair.", 'info')

        self._definir_status("DECODIFICAÇÃO CONCLUÍDA ✓", '#00ff00')

    def _decodificacao_erro(self, msg_erro):
        """Callback de erro da decodificação"""
        self._registrar(f"[ERRO] {msg_erro}", 'erro')
        self._definir_status(f"ERRO: {msg_erro}", '#ff0040')
        messagebox.showerror("Erro na Decodificação", msg_erro)

    def _codificar_arquivo(self):
        """Esconde arquivo na imagem"""
        caminho_imagem = self.caminho_imagem_arquivo.get().strip()
        caminho_arquivo = self.caminho_arquivo_esconder.get().strip()
        senha = self.senha_arquivo.get().strip() or None

        if not caminho_imagem or not caminho_arquivo:
            self._registrar(
                "[ERRO] Selecione imagem e arquivo!", 'erro')
            messagebox.showerror(
                "Erro", "Selecione a imagem e o arquivo!")
            return

        caminho_saida = filedialog.asksaveasfilename(
            title="Salvar Imagem com Arquivo Oculto",
            defaultextension=".png",
            filetypes=[("PNG", "*.png")]
        )

        if not caminho_saida:
            return

        self._definir_status(
            "ESCONDENDO ARQUIVO... ████████░░░░", '#ffaa00')
        self._registrar("Iniciando ocultação de arquivo...", 'amarelo')
        self._registrar(
            f"  Arquivo: {os.path.basename(caminho_arquivo)}", 'ciano')
        self._registrar(
            f"  Tamanho: {os.path.getsize(caminho_arquivo)} bytes", 'ciano')

        def thread_codificar():
            try:
                def callback_progresso(p):
                    self.root.after(
                        0, self.progresso_arquivo.definir_progresso, p)

                MotorEsteganografia.codificar_arquivo(
                    caminho_imagem, caminho_saida, caminho_arquivo,
                    senha, callback_progresso
                )

                self.root.after(
                    0, self._arquivo_codificacao_sucesso, caminho_saida)

            except Exception as e:
                self.root.after(0, self._codificacao_erro, str(e))

        thread = threading.Thread(target=thread_codificar, daemon=True)
        thread.start()

    def _arquivo_codificacao_sucesso(self, caminho_saida):
        """Sucesso na ocultação de arquivo"""
        self.progresso_arquivo.definir_progresso(100)
        self._registrar(
            "[SUCESSO] Arquivo escondido com sucesso!", 'sucesso')
        self._registrar(
            f"  Salvo em: {os.path.basename(caminho_saida)}",
            'verde_claro')
        self._definir_status(
            "ARQUIVO ESCONDIDO COM SUCESSO ✓", '#00ff00')

        self.terminal.escrever_linha("")
        self.terminal.escrever_linha(
            "  ╔══════════════════════════════════════╗", 'sucesso')
        self.terminal.escrever_linha(
            "  ║  ✓ ARQUIVO ESCONDIDO COM SUCESSO!    ║", 'sucesso')
        self.terminal.escrever_linha(
            "  ╚══════════════════════════════════════╝", 'sucesso')
        self.terminal.escrever_linha("")

    def _decodificar_arquivo(self):
        """Extrai arquivo da imagem"""
        caminho_imagem = self.caminho_imagem_arquivo.get().strip()
        senha = self.senha_arquivo.get().strip() or None

        if not caminho_imagem:
            self._registrar("[ERRO] Selecione uma imagem!", 'erro')
            messagebox.showerror("Erro", "Selecione uma imagem!")
            return

        self._definir_status(
            "EXTRAINDO ARQUIVO... ████████░░░░", '#ffaa00')
        self._registrar("Extraindo arquivo oculto...", 'amarelo')

        def thread_decodificar():
            try:
                def callback_progresso(p):
                    self.root.after(
                        0, self.progresso_arquivo.definir_progresso, p)

                resultado = MotorEsteganografia.decodificar(
                    caminho_imagem, senha, callback_progresso)
                self.root.after(
                    0, self._arquivo_decodificacao_sucesso, resultado)

            except Exception as e:
                self.root.after(0, self._decodificacao_erro, str(e))

        thread = threading.Thread(target=thread_decodificar, daemon=True)
        thread.start()

    def _arquivo_decodificacao_sucesso(self, resultado):
        """Sucesso na extração de arquivo"""
        self.progresso_arquivo.definir_progresso(100)

        if resultado['tipo'] == 'arquivo':
            nome_padrao = resultado['nome_arquivo'] or 'arquivo_extraido'

            caminho_saida = filedialog.asksaveasfilename(
                title="Salvar Arquivo Extraído",
                initialfile=nome_padrao
            )

            if caminho_saida:
                with open(caminho_saida, 'wb') as f:
                    f.write(resultado['dados'])

                self._registrar(
                    "[SUCESSO] Arquivo extraído com sucesso!", 'sucesso')
                self._registrar(
                    f"  Nome original: {resultado['nome_arquivo']}",
                    'ciano')
                self._registrar(
                    f"  Tamanho: {resultado['tamanho']} bytes", 'ciano')
                self._registrar(
                    f"  Salvo em: {caminho_saida}", 'verde_claro')

                self.terminal.escrever_linha("")
                self.terminal.escrever_linha(
                    "  ╔══════════════════════════════════════╗", 'sucesso')
                self.terminal.escrever_linha(
                    "  ║  ✓ ARQUIVO EXTRAÍDO COM SUCESSO!     ║", 'sucesso')
                self.terminal.escrever_linha(
                    "  ╚══════════════════════════════════════╝", 'sucesso')
                self.terminal.escrever_linha("")
        else:
            self._registrar(
                "[INFO] Dados de texto encontrados, não arquivo.", 'info')
            if resultado['texto']:
                self._registrar(
                    f"  Texto: {resultado['texto'][:100]}", 'branco')

        self._definir_status("EXTRAÇÃO CONCLUÍDA ✓", '#00ff00')

    # ==================== FUNÇÕES DE ANÁLISE ====================

    def _analisar_imagem(self):
        """Analisa imagem em busca de dados ocultos"""
        caminho_imagem = self.caminho_imagem_analisar.get().strip()

        if not caminho_imagem:
            self._registrar("[ERRO] Selecione uma imagem!", 'erro')
            return

        if not os.path.exists(caminho_imagem):
            self._registrar("[ERRO] Arquivo não encontrado!", 'erro')
            return

        self._definir_status("ANALISANDO... ████████░░░░", '#ffaa00')
        self._registrar("Iniciando análise forense...", 'amarelo')

        try:
            resultado = MotorEsteganografia.analisar_imagem(caminho_imagem)
            info = MotorEsteganografia.obter_info_imagem(caminho_imagem)

            term = self.terminal_analise
            term.limpar()

            term.escrever_linha(
                "╔══════════════════════════════════════════════╗",
                'cabecalho')
            term.escrever_linha(
                "║     RELATÓRIO DE ANÁLISE FORENSE DE IMAGEM   ║",
                'cabecalho')
            term.escrever_linha(
                "╚══════════════════════════════════════════════╝",
                'cabecalho')
            term.escrever_linha("")

            term.escrever_linha(
                f"  [ARQUIVO] {os.path.basename(caminho_imagem)}", 'ciano')
            term.escrever_linha(
                f"  [TAMANHO] {info['tamanho_arquivo']:,} bytes", 'ciano')
            term.escrever_linha(
                f"  [DIMENSÕES] {info['largura']}x{info['altura']} pixels",
                'ciano')
            term.escrever_linha(
                f"  [MODO] {info['modo']}", 'ciano')
            term.escrever_linha(
                f"  [CAPACIDADE] {info['capacidade_kb']:.2f} KB", 'ciano')
            term.escrever_linha("")

            term.escrever_linha(
                "  ─── ANÁLISE LSB ─────────────────────────────",
                'verde_escuro')
            term.escrever_linha(
                f"  LSB 0s: {resultado['lsb_zeros']:,}", 'verde')
            term.escrever_linha(
                f"  LSB 1s: {resultado['lsb_uns']:,}", 'verde')
            term.escrever_linha(
                f"  Razão LSB: {resultado['razao_lsb']:.6f}", 'verde')
            term.escrever_linha(
                f"  Chi-Quadrado: {resultado['chi_quadrado']:.4f}", 'verde')
            term.escrever_linha(
                f"  Entropia: {resultado['entropia']:.6f} bits", 'verde')
            term.escrever_linha("")

            term.escrever_linha(
                "  ─── RESULTADOS DA DETECÇÃO ──────────────────",
                'verde_escuro')

            if resultado['tem_dados_ocultos']:
                term.escrever_linha(
                    "  ⚠ DADOS OCULTOS DETECTADOS!", 'erro')
                tipo_str = ('Texto'
                            if resultado.get('tipo_carga', 0) in (1, 3)
                            else 'Arquivo')
                term.escrever_linha(
                    f"    Tipo: {tipo_str}", 'amarelo')
                term.escrever_linha(
                    f"    Tamanho: "
                    f"{resultado.get('tamanho_carga', 'N/D')} bytes",
                    'amarelo')
                term.escrever_linha(
                    f"    Criptografado: "
                    f"{'Sim' if resultado.get('criptografado') else 'Não'}",
                    'amarelo')
            else:
                term.escrever_linha(
                    "  ✓ Nenhum dado ZSteg detectado", 'sucesso')

            if resultado['suspeito']:
                term.escrever_linha(
                    "  ⚠ Imagem apresenta sinais de manipulação!",
                    'aviso')
            else:
                term.escrever_linha(
                    "  ✓ Imagem parece limpa", 'sucesso')

            term.escrever_linha("")
            term.escrever_linha(
                "  ═════════════════════════════════════════════",
                'verde_escuro')
            term.escrever_linha("  Análise concluída.", 'verde')

            self._registrar("[SUCESSO] Análise concluída!", 'sucesso')
            self._definir_status("ANÁLISE CONCLUÍDA ✓", '#00ff00')

        except Exception as e:
            self._registrar(f"[ERRO] {str(e)}", 'erro')
            self._definir_status(f"ERRO: {str(e)}", '#ff0040')

    def _mostrar_info_imagem(self):
        """Mostra informações detalhadas da imagem"""
        caminho_imagem = self.caminho_imagem_analisar.get().strip()

        if not caminho_imagem or not os.path.exists(caminho_imagem):
            self._registrar(
                "[ERRO] Selecione uma imagem válida!", 'erro')
            return

        try:
            info = MotorEsteganografia.obter_info_imagem(caminho_imagem)

            term = self.terminal_analise
            term.limpar()

            term.escrever_linha(
                "╔══════════════════════════════════════════════╗",
                'cabecalho')
            term.escrever_linha(
                "║      RELATÓRIO DE INFORMAÇÕES DA IMAGEM      ║",
                'cabecalho')
            term.escrever_linha(
                "╚══════════════════════════════════════════════╝",
                'cabecalho')
            term.escrever_linha("")

            term.escrever_linha(
                f"  Nome do arquivo: {os.path.basename(caminho_imagem)}",
                'ciano')
            term.escrever_linha(
                f"  Caminho:         {caminho_imagem}", 'verde_escuro')
            term.escrever_linha(
                f"  Formato:         "
                f"{Path(caminho_imagem).suffix.upper()}", 'ciano')
            term.escrever_linha(
                f"  Largura:         {info['largura']} px", 'verde')
            term.escrever_linha(
                f"  Altura:          {info['altura']} px", 'verde')
            term.escrever_linha(
                f"  Canais:          {info['canais']}", 'verde')
            term.escrever_linha(
                f"  Modo de cor:     {info['modo']}", 'verde')
            term.escrever_linha(
                f"  Tamanho arq.:    {info['tamanho_arquivo']:,} bytes "
                f"({info['tamanho_arquivo']/1024:.2f} KB)", 'verde')
            term.escrever_linha(
                f"  Total de pixels: {info['total_pixels']:,}", 'verde')
            term.escrever_linha(
                f"  Capacidade:      {info['capacidade']:,} bytes "
                f"({info['capacidade_kb']:.2f} KB)", 'verde_claro')
            term.escrever_linha("")

            # Barra visual de capacidade
            cap_kb = info['capacidade_kb']
            if cap_kb > 100:
                term.escrever_linha(
                    "  Classificação: ████████████████ EXCELENTE",
                    'sucesso')
            elif cap_kb > 10:
                term.escrever_linha(
                    "  Classificação: ████████████░░░░ BOA",
                    'verde')
            elif cap_kb > 1:
                term.escrever_linha(
                    "  Classificação: ████████░░░░░░░░ MODERADA",
                    'amarelo')
            else:
                term.escrever_linha(
                    "  Classificação: ████░░░░░░░░░░░░ BAIXA",
                    'aviso')

            term.escrever_linha("")
            term.escrever_linha(
                "  ═════════════════════════════════════════════",
                'verde_escuro')

            self._registrar(
                "[INFO] Informações da imagem exibidas", 'info')

        except Exception as e:
            self._registrar(f"[ERRO] {str(e)}", 'erro')

    def executar(self):
        """Inicia a aplicação"""
        self.root.mainloop()


# ========================== PONTO DE ENTRADA ==========================

def principal():

    if not PIL_DISPONIVEL:
        root = tk.Tk()

        root.title("Esteganografia - ERRO")
        root.configure(bg="#0a0a0a")
        root.geometry("600x250")

        tk.Label(
            root,
            text=(
                "⚠ DEPENDÊNCIAS NÃO ENCONTRADAS ⚠\n\n"
                "Execute no terminal:\n"
                "pip install Pillow numpy\n\n"
                "Depois rode o script novamente."
            ),
            bg="#0a0a0a",
            fg="#ff0040",
            font=("Courier New", 12, "bold"),
            justify="center"
        ).pack(expand=True)

        root.mainloop()
        return

    app = AplicativoEsteganografia()
    app.executar()


if __name__ == "__main__":
    principal()
