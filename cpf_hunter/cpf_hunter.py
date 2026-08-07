#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPF Hunter - GUI Edition + HTML Export + Tor Support
Busca multifonte de CPF em sistemas brasileiros
Estilo Hacker Green com exportação para relatório HTML
"""

import asyncio
import json
import os
import re
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from base64 import b64decode
from threading import Thread
from datetime import datetime
from html import escape
import warnings
import time

# Suprimir warnings específicos
warnings.filterwarnings("ignore", category=UserWarning, module="bs4")
warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    from aiohttp import ClientSession, TCPConnector
except ImportError:
    print("[!] Instalando dependência necessária: aiohttp")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
    from aiohttp import ClientSession, TCPConnector

try:
    from bs4 import BeautifulSoup
    try:
        from bs4 import XMLParsedAsHTMLWarning
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    except ImportError:
        pass
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

# =============================================================================
# DADOS EMBUTIDOS (originalmente em data.json)
# =============================================================================
LOOKUP_DATA = {
    "sites": [
        {"app": "U2VyYXNh", "id": 0, "json": "eyJjcGYiOiAie2NwZn0ifQ==", "method": "POST", "silent": True, "url": "aHR0cHM6Ly9hcGktYXV0aC5zZXJhc2EuY29tLmJyL3YxL3VzZXIvY3Bm", "valid": "response.status == 200"},
        {"app": "QmFuY28gVG95b3Rh", "form": "Y3BmPXtjcGZ9JnBlcmZpbD0x", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkJ30=", "id": 1, "method": "POST", "silent": True, "url": "aHR0cHM6Ly9pbnN0aXR1Y2lvbmFsLmJhbmNvdG95b3RhLmNvbS5ici9hcGkvc3NvL2F1dGVudGljYWNhby9zZW5oaGEvYnVzY2FyUGVyZ3VudGFzLmpzb24=", "valid": "jsonData['result'] == 'SUCCESS'"},
        {"app": "RkdWIENvbmhlY2ltZW50bw==", "form": "Y3BmPXtjcGZ9", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkOyBjaGFyc2V0PVVURi04J30=", "id": 2, "method": "POST", "silent": True, "url": "aHR0cHM6Ly9pbnNjcmljYW8uY29uaGVjaW1lbnRvLmZndi5ici9SZWN1cGVyYXJTZW5oYS9Tb2xpY2l0YXJFbWFpbA==", "valid": "'CPF n&#xE3;o encontrado.' not in responseContent and 'Insira um n&#xFA;mero de CPF v&#xE1;lido.' not in responseContent"},
        {"app": "U0VCUkFF", "id": 3, "method": "GET", "silent": True, "url": "aHR0cHM6Ly9nZXN0YW8tYW1laS1iYWNrZW5kLnNlYnJhZS5jb20uYnIvZ2VzdGFvLWFtZWkvcHVibGljL3YxL3VzZXJzL3JlZ2lzdGVyZWQve2NwZn0=", "valid": "jsonData['isExiste'] == True"},
        {"app": "SW5mb0pvYnM=", "form": "X19WSUVXU1RBVEU9ampPNFVHJTJGUTlUOFZvVzN3dVJLYlcxc29mak5sS0IlMkZJQ2I1cXdCZWJGQiUyQjlSQlhmaUU5OFRhd3FBUnpRUWZXN3lyJTJGbE9YYmpVU0JpdEcyb0oxbjQ2QXFERERQTEZPbDd4azkxVkhsM1piT1hHVVk2NmVPaW55YVB4WUpYU2JTbDRuSXVQR1BnVmVnSXVLeHhNS0ZEb3IwZTFZa25SN2dZR1VaZDNBZmJVM01kJTJGNlklMkJjeG4xR3lqTCUyQkIlMkJtTkVRWlluZTdWMVB6ZzZySXROZzZLZmVkanVvYm5NeU8yYkw3dDE0RzdmODNvN3pHNWZteWViWDBETko5dVo1MGJLSE1FQ2VHMjVMbCUyQjE5cktpQjVONW16bVNCSzRzWlpWWnVqQU44MjVkdnNlJTJGOTdWTGtkYWYwdnp3aWwyaUdaV0hUT28yR2NzczJkY29hdFdmJTJGRkljUUpSZGFydjdhZUVQZUQ2bTBuM3dHc1N0NURJeHJQdnFkeGVPUHFhdnVBQiUyRkFucTRzckJQQm1aWFBVR1Vpb0k2dmhhRTdJU29mOUFjb1FXVlpzTm44VSUyQnI1VENrYVVHNHZadTZJODZIVVdQSVElMkIxRSUyRlJ2N0pCN0xEaEV6SGRVN2F0VmppRDgza0dmWHFiZSUyQmsxdjVqQmxwUnlZOTVyUDJKM0JSaVpaVllmJTJCMXBtU1djTUxXRlZOJTJGb0N0SlRMSmRPNSUyQmxLb0RpRTVRaXRHS2p4UzZja0tobU9MdzdCOHJaVjExQ2Z1RE9scklqa0hmMkdON1loY0g5WFZuclRPSzZHak9QS0NiYkhsbll5OUh5OHB2bThUJTJCd1c2NGd3V2kya1hvanRMSU1xMkhLSkdpMXdFODFIdGNLckFKd3VxYm41V2ZhT0MzQmRJZURZJTJCJTJCUmtDZ3BLeFNmRFhCdk93RElBNUZVcDNEU3hMVmJQdmZFSE9JRU1QOEh4eFQ4MHFxMWllTXU5NmNlOFVpeEVWVjdTbHRKc0ZzM3pnRXBxVTQ1OGxiS21ZaW1pb0EzYTlORHZuWCUyRlZCMTdCVWJNU2NuWURDME0lMkY3ZUFIRHp6dXdhb0g0OEliV1ZhdmwlMkZaVlgxTmxqSFZ2b2YlMkIxNXBXZ3FPMEd0Qjgxekh4NUtDcWV3czRaMHBxWU1pRVYwOExzVVViWmlPVjl0anRDRU9hZWRLWWNTUHZqOVk1a1R1V3BodUF3MUM5SlZwQVFDT3RUQ2NEYnZJakRrb0klMkJxOWJUNExtcmM2dnFwWG1LJTJCSURxTUhRVjYyRkN5RmRaNnFGWVBpRTAyUGNRTzVQSDYlMkZ2ajNWMXMwMCUyQmEwZ3BJWGw4d1glMkJMbnVGS0hpMHhMVWN4S3JCa3BTMFphWU1sSDhnZU1ZM0FqYmNtOFV0Q3ZmQnlJQ2pBUkR6TXdidDZFbnFzVzltMW9LU1NYOFVGaXZPNW1aJTJCYzUwa0JMYUIlMkZzRSUyRjclMkZqdUpqVjhzWkJaJTJCNEo2OEFXaGQ1MzRjVzhienF5MDZoYjlSWlRiQWNMZzNlUnM0SHdKT0Y2TUY2WFN4RGdzRDFlUkRURTlOekYlMkYwNDJVVDNXYVRVemJCNzlra1BYSHlHOHloZE1OVm8lMkI1c2ZwZXhtM2l2cnFaMXJibTdZN1Z0V2NUMEhBS0V5SVdHWjZmN2xFdkdoZXd1eEZhdm1QVWJtemdTc2RvcVU3UTlKUWhHbG9PUDRmTlpuOG1zYzNwQVh5M3UwMkNLQ1pUaCUyRjVyNGtWZnF4MU81dWp4NGhUbHh4RSUyQkhSM2g1bWswMDZiYnNsUmduY1c5R3RuTiUyRnFVajVEaSUyRjQ1OGs2MURNNk1HMEt5eDdmWE5xb1dBYTRmSEZxQ0hBckRvMUozVjF0SkdSTUgyRDA1NW5iVVg3SllmempXTHhycmZmR2F5Z3ZTU0hrTmpyRUNMSmZ1ZVpvSkpKVmMxd1IwOU9zdU5BZkU0Mk9DWHNSZkxEQjMwNXBXb09tVVVFVnhaWlNWSlJiNHV6YkpCM2Fjb0RyOFFWRjduQlBoUFdUZFVGU0p2bnV6UzJsMmppTWpVJTJGWWxtRVlwTG1uSVdzMjY4R28lMkZHS2xrViUyRkZ3dTJVTkh1QkdZN2ZNdWRod3hMbk1YcUZYWjhWYlpzWWJEJTJCQXNNMDNBdExyYmt3a2dpYmtoRnN6VFhHck96eCUyQlRGOUVvV2J2Ulk4b0k4T3pscEFub1hMQXV5NzE2VyUyRm9ETHpEMWNUNlFFd01XZmVJTXNLb2ZZMEElM0QlM0QmX19WSUVXU1RBVEVHRU5FUkFUT1I9RDRDMzVFQ0EmY1JlbVBhc3NFbWFpbENvbXBhbnklMjR0eHRFbWFpbD0mY1JlbVBhc3NFbWFpbENvbXBhbnklMjR0eHRDUE5KPSZjUmVtUGFzc0NhbmRpZGF0ZSUyNHR4dEVtYWlsPSZjUmVtUGFzc0NhbmRpZGF0ZSUyNHR4dENQRj17Y3BmfSZjUmVtUGFzc0NhbmRpZGF0ZSUyNHJidGxzdFNlbmQ9MSZjUmVtUGFzc0NhbmRpZGF0ZSUyNGJ0blN0ZXAyPUVudmlhcg==", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkJ30=", "id": 4, "method": "POST", "returnData": "soup.find('span', {'id': 'cRemPassCandidate_lblResult2'}).getText()", "silent": False, "url": "aHR0cHM6Ly93d3cuaW5mb2pvYnMuY29tLmJyL1JlbWVtYmVyUGFzcy5hc3B4", "valid": "'Enviamos um e-mail para' in soup.find('span', {'id': 'cRemPassCandidate_lblResult2'}).getText()"},
        {"app": "SG9zcGl0YWwgZGFzIENsw4PCrW5pY2FzIFVTUA==", "form": "X19FVkVOVFRBUkdFVD0mX19FVkVOVEFSR1VNRU5UPSZfX1ZJRVdTVEFURT0lMkZ3RVBEd1VLTVRjNU1qQTROamszTUE5a0ZnUUNBdzlrRmdJQ0N3OFBGZ0llQkZSbGVIUmxaR1FDQlE4UEZnSWZBR1ZrWkdTckFWeEptOVluSUNFQldXT2NJZUplN3NpM2p2RkpxN2ZyWGNpUXlnRGVlUSUzRCUzRCZfX1ZJRVdTVEFURUdFTkVSQVRPUj1FNkEzNTQyRSZfX0VWRU5UVkFMSURBVElPTj0lMkZ3RWRBQWJHQ3BIcFAlMkJVb2tRRkclMkZuckZmUTZTM1hOb1hBYVh2aUp0SUVvN0JEJTJGcXpqR1hFeUR3SVNvWDdhdDEzSmRFRXJBNEJFQ3hSV1lCZFhlQnhPSThsaFltRkNEM3h0UFFYUXFaWnJ2R0g3bEdtUXRocHk2bU5QdkVBbG84RVI3NmQ2dVJUWUFKNGNWU1g0JTJGMFBDRWZRUkNLcld5NUJmQ1BpbXhjV1hRUFZSJTJCdVlnJTNEJTNEJnR4dF9sb2dpbj17Y3BmfSZ0eHRfc2VuaGE9JmJ0X0VzcXVlY2lTZW5oYT1Fc3F1ZWNpK2Erc2VuaGE=", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkJ30=", "id": 5, "method": "POST", "silent": True, "url": "aHR0cHM6Ly93d3cuaGNycC51c3AuYnIvQ29uc3VsdGFGaW5hbkZvcm5lY2Vkb3JGQUVQQS9sb2dpbi5hc3B4", "valid": "'verifique se esteja informando corretamente' not in soup.find('span', {'id': 'lbErro'}).getText()"},
        {"app": "VW5pdmVyc2lkYWRlIEFuaGVtYmkgTW9ydW1iaQ==", "form": "Y3BmPXtjcGZ9", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkJ30=", "id": 6, "method": "POST", "silent": False, "url": "aHR0cHM6Ly9hcGl1YW0uZWFkLmJyL3YxL2F1dGgvcmVjb3Zlcg==", "valid": "jsonData['status'] == 'success'"},
        {"app": "VW5pdmVyc2lkYWRlIFPDg8KjbyBKdWRhcw==", "form": "Y3BmPXtjcGZ9", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkJ30=", "id": 7, "method": "POST", "silent": False, "url": "aHR0cHM6Ly9hcGlzanQuZWFkLmJyL3YxL2F1dGgvcmVjb3Zlcg==", "valid": "jsonData['status'] == 'success'"},
        {"app": "VW5pdmVyc2lkYWRlIFVGQUJD", "form": "Q2FkYXN0cm9JbmRleEZvcm0lNUJ0aXBvX2RvYyU1RD1jcGYmQ2FkYXN0cm9JbmRleEZvcm0lNUJudW1fZG9jJTVEPXtjcGZ9Jnl0MD1Db250aW51YXI=", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkJ30=", "id": 8, "method": "POST", "silent": True, "url": "aHR0cHM6Ly9hY2Vzc28udWZhYmMuZWR1LmJyL2NhZGFzdHJvL2luZGV4", "valid": "'favor entrar em contato com o setor' not in responseContent and response.status == 200"},
        {"app": "Q2xhcmV0aWFubyAtIENlbnRybyBVbml2ZXJzaXTDg8Khcmlv", "form": "Y3BmPXtjcGZ9JmNvbW1pdD1SZWN1cGVyYXI=", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkJ30=", "id": 9, "method": "POST", "silent": True, "url": "aHR0cHM6Ly9wb3J0YWwucmVkZWNsYXJldGlhbm8uZWR1LmJyL2JyL3JlbWVtYmVyL2xvZ2lu", "valid": "'nenhuma' not in responseContent"},
        {"app": "VU5JUA==", "id": 10, "method": "GET", "returnData": "repr(jsonData)", "silent": True, "url": "aHR0cHM6Ly9hcGkudW5pcC5ici9zaXN0ZW1hcy9pbnNjcmljb2VzL3YxL2luc2NyaWNvZXMve2NwZn0=", "valid": "response.status == 200 and len(jsonData) > 0"},
        {"app": "UXVhbGlDb3Jw", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbjtjaGFyc2V0PVVURi04J30=", "id": 12, "method": "POST", "silent": True, "string": "{}", "url": "aHR0cHM6Ly9zZXJ2aWNvc3BvcnRhbC5xdWFsaWNvcnAubmV0L2FyZWEtbG9nYWRhLWNpYW0vdXNlci9jaGVjay97Y3BmfT9hcGkta2V5PTkxY2U1YmIyLWQxNzctNDk2Yi1hMTA3LWIwY2RiNmMxNGY1Mw==", "valid": "'User does not exist.' not in responseContent and response.status == 200"},
        {"app": "TmF0dXJh", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbicsJ0NsaWVudF9pZCc6ICc4MjQyYjM5Ni1hNzg2LTMzNWUtOGVjYi01Mjc5ZDNiODA1NGEnfQ==", "id": 13, "json": "eyJjcGYiOiAie2NwZn0ifQ==", "method": "POST", "returnData": "repr(jsonData)", "silent": False, "url": "aHR0cHM6Ly9hcGlndy5uYXR1cmEuY29tLmJyL3YxL2xlZ2FjeXdlYi9lY29tbWVyY2UvcmVzdC9tb2RlbC9hdGcvdXNlcnByb2ZpbGluZy9Qcm9maWxlQWN0b3IvcmVzZXRQYXNzd29yZA==", "valid": "'clientEmail' in jsonData"},
        {"app": "Q29ycmVpb3M=", "id": 14, "method": "GET", "returnData": "repr(jsonData)", "silent": False, "url": "aHR0cHM6Ly9tZXVjb3JyZWlvcy5jb3JyZWlvcy5jb20uYnIvYXBwL2NhZGFzdHJvL2VzcXVlY2kvY2hlY2EtaWRlbnRpZmljYWNhby5waHA/cGVzc29hPXBmJmlkZW50aWZpY2FjYW89e2NwZn0=", "valid": "'email' in jsonData"},
        {"app": "RXZlbnRpbQ==", "id": 15, "method": "GET", "silent": True, "url": "aHR0cHM6Ly93d3cuZXZlbnRpbS5jb20uYnIvYXBpL2NwZi92YWxpZGF0ZT9jcGZOdW1iZXI9e2NwZn0mYWZmaWxpYXRlPUJSMQ==", "valid": "response.status == 406"},
        {"app": "VGlja2V0MzYw", "form": "ZG9jdW1lbnQ9e2NwZn0=", "formatted": True, "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkOyBjaGFyc2V0PVVURi04J30=", "id": 16, "method": "POST", "returnData": "repr(jsonData)", "silent": True, "url": "aHR0cHM6Ly93d3cudGlja2V0MzYwLmNvbS5ici91c3VhcmlvX2VzcXVlY2ktc2VuaGEvc2VhcmNo", "valid": "response.status == 200"},
        {"app": "SW5ncmVzc29zIENvcmludGhpYW5z", "form": "Y3BmPXtjcGZ9", "formatted": True, "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkOyBjaGFyc2V0PVVURi04J30=", "id": 17, "method": "POST", "returnData": "soup.find('span', {'id': 'msg'}).getText()", "silent": True, "url": "aHR0cHM6Ly93d3cuaW5ncmVzc29zY29yaW50aGlhbnMuY29tLmJyL3NjcmlwdHMvZXNxdWVjaS1taW5oYS1zZW5oYS5hc3A=", "valid": "'Sucesso' in responseContent"},
        {"app": "VW5pbWVkIFNlZ3VyYWRvcmE=", "formatted": False, "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbicsJ1gtSWJtLUNsaWVudC1JZCc6ICc5NWNjODA0MS1kYmM2LTQwOTItOGUwZS0yYWRkMGRlNTZkNzknfQ==", "id": 18, "json": "eyJhcGxpY2FjYW9PcmlnZW0iOiAiUE9SVEFMX1BGIiwidXN1YXJpbyI6ICJ7Y3BmfyJ9", "method": "POST", "returnData": "repr(jsonData)", "silent": True, "url": "aHR0cHM6Ly9jb25uZWN0aW9uYnVzLnNlZ3Vyb3N1bmltZWQuY29tLmJyL3NlZ3Vyb3MtdW5pbWVkL3ByZC92MS91c3VhcmlvL2VzcXVlY2ktc2VuaGE=", "valid": "jsonData['codigo'] == '0'"},
        {"app": "TW92aWRh", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbid9", "id": 19, "json": "eyJjcGYiOiAie2NwZn0iLCJ0aXBvIjogImVtYWlsIn0=", "method": "POST", "returnData": "repr(jsonData)", "silent": False, "url": "aHR0cHM6Ly9iZmYtYjJjLm1vdmlkYWNsb3VkLmNvbS5ici9hcGkvdjEvdXN1YXJpby9yZWN1cGVyYXItc2VuaGE=", "valid": "jsonData['success'] == True"},
        {"app": "UGV0eg==", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbicsJ0FjY2VwdCc6J2FwcGxpY2F0aW9uL2pzb24sIHRleHQvcGxhaW4sICovKid9", "id": 20, "json": "eyJjcGYiOiAie2NwZn0ifQ==", "method": "POST", "returnData": "repr(jsonData)", "silent": True, "url": "aHR0cHM6Ly93d3cucGV0ei5jb20uYnIvYXBpL3YzL3B1YmxpYy9jbGllbnQvYWNjZXNz", "valid": "'error' not in responseContent"},
        {"app": "UGVybmFtYnVjYW5hcw==", "id": 21, "headers": "eydBdXRob3JpemF0aW9uJzogJ0JlYXJlciBZdTJvVmdxNUNCNTNHZjJjWjZRM2hKMTZNWkZNJ30=", "method": "GET", "returnData": "repr(jsonData)", "silent": True, "url": "aHR0cHM6Ly9hcGlnZWUtdmFyZWpvLXByZC5wZXJuYW1idWNhbmFzLmNvbS5ici9nZXJlbmNpYW1lbnRvX2NsaWVudGVzL2NsaWVudGVzL3tjcGZ9", "valid": "response.status == 200 and 'nomeCompleto' in responseContent"},
        {"app": "TWFyaXNh", "url": "aHR0cHM6Ly93d3cubWFyaXNhLmNvbS5ici9yZWdpc3Rlci9uZXdjdXN0b21lcg==", "valid": "'CPF j&aacute; cadastrado' in responseContent and response.status == 200", "form": "dHlwZT1DVVNUT01FUiZmaXJzdE5hbWU9Q2F0YXJpbmErQ3Jpc3RpYW5lK0FsbGFuYStTaWx2YSZiaXJ0aERhdGU9MDMlMkYwNiUyRjIwMDQmY3BmQ25waj17Y3BmfSZnZW5kZXI9RkVNQUxFJmRkZENlbGxQaG9uZU51bWJlcj0xMSZjZWxsUGhvbmVOdW1iZXI9NjU5ODgtMTczOSZkZGRQaG9uZU51bWJlcj0xMSZwaG9uZU51bWJlcj02NTM1LTM0ODMmZW1haWw9Y2F0YXJpbmFfc2lsdmElNDB6aXBtYWlsLmNvbSZwd2Q9SU11aEEzSEtQbyZjaGVja1B3ZD1JTXVoQTNIS1BvJnVzZXJEYXRhQWNjZXB0YW5jZVRlcm09dHJ1ZSZvcHRJbkVtYWlsPW9uJm9wdEluU01TPW9uJkNTUkZUb2tlbj1kMDlkY2EzYS0wOGRiLTRlMmEtYWM5Yi1kN2YxZjI2ODRjOTA=", "headers": "eydDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkJywnQ29va2llJzogJ0pTRVNTSU9OSUQ9Q0EwMTM1MkY1QjhBNTk2NjMxNUU3MUMwM0MzNDc1OTcubm9kZS02Oyd9", "formatted": True, "id": 23, "method": "POST", "silent": True}
    ]
}


# =============================================================================
# FUNÇÕES DE VALIDAÇÃO CORRIGIDAS
# =============================================================================

def decode64(encoded_value):
    """Decodifica base64 para string UTF-8."""
    return b64decode(encoded_value).decode('UTF-8')


def validar_cpf(cpf, debug=False):
    """
    Valida CPF de forma robusta.
    Remove qualquer caractere não-dígito, incluindo unicode invisível.
    Retorna (cpf_limpo, mensagem_erro_ou_None).
    """
    original = cpf
    cpf = cpf.strip()
    if debug:
        print(f"[DEBUG] CPF original bytes: {original.encode('utf-8').hex()}")
        print(f"[DEBUG] CPF após strip bytes: {cpf.encode('utf-8').hex()}")

    # Remove TUDO que não for dígito
    cpf = re.sub(r'[^\d]', '', cpf)

    if debug:
        print(f"[DEBUG] CPF após re.sub: '{cpf}' (len={len(cpf)})")

    if len(cpf) != 11:
        return None, f"CPF deve ter 11 dígitos (encontrados {len(cpf)}): '{cpf}'"

    if cpf == cpf[0] * 11:
        return None, "CPF com dígitos repetidos (inválido por definição)"

    for i in range(9, 11):
        soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
        digito = (soma * 10 % 11) % 10
        if int(cpf[i]) != digito:
            return None, f"Dígito verificador {i-8} inválido (esperado {digito}, encontrado {cpf[i]})"

    return cpf, None


def formatar_cpf(cpf):
    """Formata CPF no padrão XXX.XXX.XXX-XX."""
    return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'


def get_soup(response_content, content_type=""):
    """Cria objeto BeautifulSoup com parser adequado."""
    if 'xml' in content_type.lower() or 'soap' in content_type.lower():
        return BeautifulSoup(response_content, 'lxml-xml')
    else:
        return BeautifulSoup(response_content, 'html.parser')


async def do_request(lookup, cpf, stealth_mode, proxy_url=None, timeout=15):
    app_name = decode64(lookup['app'])
    url_template = decode64(lookup['url'])
    cpf_fmt = cpf

    if 'formatted' in lookup and lookup['formatted']:
        cpf_fmt = formatar_cpf(cpf)

    url = url_template.replace('{cpf}', cpf_fmt)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.0; rv:40.0) Gecko/20100101 Firefox/40.0"
    }
    if 'headers' in lookup:
        headers.update(eval(decode64(lookup['headers'])))

    json_body = None
    form_data = None

    if 'json' in lookup:
        json_str = decode64(lookup['json']).replace('{cpf}', cpf_fmt)
        json_body = json.loads(json_str)
    if 'form' in lookup:
        form_str = decode64(lookup['form']).replace('{cpf}', cpf_fmt)
        form_data = form_str

    if lookup['silent'] is False and stealth_mode:
        return {'app': app_name, 'url': url, 'found': False,
                'data': None, 'error': 'Pulado (modo silencioso)'}

    try:
        if proxy_url and (proxy_url.startswith('socks5://') or proxy_url.startswith('socks5h://')):
            try:
                from aiohttp_socks import ProxyConnector
            except ImportError:
                return {
                    'app': app_name,
                    'url': url,
                    'found': False,
                    'data': None,
                    'error': 'Instale: pip install aiohttp-socks'
                }
            connector = ProxyConnector.from_url(proxy_url, rdns=True)
        else:
            connector = TCPConnector(ssl=False)

        async with ClientSession(connector=connector) as session:
            request_kwargs = {
                'method': lookup['method'],
                'url': url,
                'json': json_body,
                'data': form_data,
                'headers': headers,
                'ssl': False,
                'timeout': timeout,
            }
            if proxy_url and proxy_url.startswith('socks5://'):
                if ProxyConnector is None:
                    return {'app': app_name, 'url': url, 'found': False, 'data': None,
                            'error': 'Instale: pip install aiohttp-socks'}
                connector = ProxyConnector.from_url(proxy_url, rdns=True)  # rdns=True = DNS pelo Tor
            else:
                connector = TCPConnector(ssl=False)

            async with session.request(**request_kwargs) as response:
                response_content = await response.text()
                content_type = response.headers.get('Content-Type', '')

                json_data = None
                soup = None

                if 'application/json' in content_type or 'json' in content_type:
                    try:
                        json_data = await response.json()
                    except Exception:
                        json_data = None

                if json_data is None:
                    soup = get_soup(response_content, content_type)
                else:
                    soup = get_soup("", "")

                local_vars = {
                    'response': response,
                    'responseContent': response_content,
                    'jsonData': json_data,
                    'soup': soup,
                }
                found = eval(lookup['valid'], {"__builtins__": {}}, local_vars)

                extra_data = None
                if found and 'returnData' in lookup:
                    try:
                        extra_data = eval(lookup['returnData'], {"__builtins__": {}}, {
                            'response': response,
                            'jsonData': json_data,
                            'soup': soup,
                            'repr': repr,
                        })
                    except Exception as e:
                        extra_data = f'[Erro ao extrair: {e}]'

                return {
                    'app': app_name,
                    'url': url,
                    'found': found,
                    'data': extra_data,
                    'error': None
                }
    except asyncio.TimeoutError:
        return {'app': app_name, 'url': url, 'found': False,
                'data': None, 'error': 'Timeout'}
    except Exception as e:
        return {'app': app_name, 'url': url, 'found': False,
                'data': None, 'error': repr(e)}


# =============================================================================
# GERADOR DE RELATÓRIO HTML
# =============================================================================

def gerar_html(cpf_alvo, results, stealth_mode, show_all, tempo_total, usou_tor=False):
    cpf_fmt = formatar_cpf(cpf_alvo) if len(cpf_alvo) == 11 else cpf_alvo
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    found_count = sum(1 for r in results if r['found'])
    error_count = sum(1 for r in results if r['error'] and not r['found'])
    not_found_count = sum(1 for r in results if not r['found'] and not r['error'])

    linhas_tabela = ""
    for r in results:
        if r['found']:
            classe, status, badge = "found", "ENCONTRADA", "badge-found"
        elif r['error']:
            classe, status, badge = "error", "ERRO", "badge-error"
        else:
            classe, status, badge = "notfound", "NAO ENCONTRADA", "badge-notfound"

        dados = escape(str(r['data'] or ""))
        erro = escape(str(r['error'] or ""))
        url = escape(r['url'])
        app = escape(r['app'])

        linha = f"""                <tr class="{classe}">
                    <td><span class="status-badge {badge}">{status}</span></td>
                    <td>{app}</td>
                    <td class="url-cell"><code>{url}</code></td>
                    <td>{dados}</td>
                    <td>{erro}</td>
                </tr>"""
        linhas_tabela += linha + "\n"

    sistemas_encontrados = ""
    found_systems = [r for r in results if r['found']]
    if found_systems:
        for r in found_systems:
            dados = escape(str(r['data'] or "-"))
            sistemas_encontrados += f"""                        <div class="system-card">
                            <div class="system-name">◆ {escape(r['app'])}</div>
                            <div class="system-data">{dados}</div>
                        </div>\n"""
    else:
        sistemas_encontrados = """                        <div class="system-card no-data">
                            <div class="system-name">■ Nenhuma conta encontrada</div>
                        </div>\n"""

    modo = "Stealth (Silencioso)" if stealth_mode else "Noisy (Barulhento - pode alertar o alvo)"
    todos = "Sim" if show_all else "Não"
    rota = "Tor (anonimizado)" if usou_tor else "Conexão direta"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CPF Hunter - Relatório de Busca</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #0a0a0a; color: #00ff41; font-family: 'Consolas', 'Courier New', monospace; line-height: 1.6; padding: 20px; min-height: 100vh; }}
        body::before {{ content: ''; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: repeating-linear-gradient(0deg, rgba(0,255,65,0.03) 0px, rgba(0,255,65,0.03) 1px, transparent 1px, transparent 3px); pointer-events: none; z-index: 9999; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: rgba(0,10,0,0.85); border: 1px solid #00ff41; border-radius: 8px; padding: 30px; box-shadow: 0 0 30px rgba(0,255,65,0.1), inset 0 0 30px rgba(0,255,65,0.02); }}
        .header {{ text-align: center; padding-bottom: 25px; border-bottom: 1px solid #00ff41; margin-bottom: 25px; }}
        .header h1 {{ font-size: 28px; color: #00ff41; text-shadow: 0 0 20px rgba(0,255,65,0.5); letter-spacing: 3px; margin-bottom: 5px; }}
        .header .subtitle {{ color: #008a1e; font-size: 14px; letter-spacing: 1px; }}
        .header .date {{ color: #005a12; font-size: 12px; margin-top: 8px; }}
        .ascii-art {{ font-size: 10px; line-height: 1.2; color: #00ff41; margin-bottom: 15px; text-align: center; opacity: 0.7; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px; }}
        .info-card {{ background: rgba(0,255,65,0.03); border: 1px solid #005a12; border-radius: 4px; padding: 15px; text-align: center; }}
        .info-card .label {{ color: #005a12; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; }}
        .info-card .value {{ color: #00ff41; font-size: 22px; font-weight: bold; margin-top: 5px; text-shadow: 0 0 10px rgba(0,255,65,0.3); }}
        .info-card .value.red {{ color: #ff3333; text-shadow: 0 0 10px rgba(255,51,51,0.3); }}
        .info-card .value.yellow {{ color: #ffcc00; text-shadow: 0 0 10px rgba(255,204,0,0.3); }}
        .info-card .value.cyan {{ color: #00ffff; text-shadow: 0 0 10px rgba(0,255,255,0.3); }}
        .target-info {{ background: rgba(0,255,65,0.05); border: 1px solid #00ff41; border-radius: 4px; padding: 15px 20px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }}
        .target-info .cpf-display {{ font-size: 20px; font-weight: bold; color: #00ff41; text-shadow: 0 0 15px rgba(0,255,65,0.4); }}
        .target-info .mode-badge {{ font-size: 12px; padding: 4px 12px; border-radius: 3px; border: 1px solid; }}
        .mode-stealth {{ color: #00ff41; border-color: #00ff41; }}
        .mode-noisy {{ color: #ffcc00; border-color: #ffcc00; }}
        .section-title {{ font-size: 16px; color: #00ff41; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 1px solid #003300; letter-spacing: 2px; }}
        .section-title::before {{ content: ">> "; }}
        .systems-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-bottom: 30px; }}
        .system-card {{ background: rgba(0,255,65,0.03); border: 1px solid #005a12; border-radius: 4px; padding: 12px 15px; transition: all 0.3s ease; }}
        .system-card:hover {{ border-color: #00ff41; background: rgba(0,255,65,0.06); }}
        .system-card .system-name {{ color: #00ff41; font-weight: bold; font-size: 14px; margin-bottom: 4px; }}
        .system-card .system-data {{ color: #008a1e; font-size: 12px; word-break: break-all; }}
        .system-card.no-data .system-name {{ color: #005a12; }}
        .table-container {{ overflow-x: auto; margin-bottom: 25px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        thead th {{ background: #001a00; color: #00ff41; text-align: left; padding: 12px 10px; border-bottom: 2px solid #00ff41; font-weight: bold; letter-spacing: 1px; white-space: nowrap; }}
        tbody td {{ padding: 10px; border-bottom: 1px solid #002200; vertical-align: top; }}
        tbody tr:hover {{ background: rgba(0,255,65,0.04); }}
        tbody tr.found td {{ color: #00ff41; }}
        tbody tr.notfound td {{ color: #005a12; }}
        tbody tr.error td {{ color: #ff3333; }}
        .url-cell code {{ font-size: 11px; color: inherit; word-break: break-all; }}
        .status-badge {{ display: inline-block; padding: 3px 10px; border-radius: 3px; font-size: 10px; font-weight: bold; letter-spacing: 1px; }}
        .badge-found {{ background: rgba(0,255,65,0.15); color: #00ff41; border: 1px solid #00ff41; }}
        .badge-notfound {{ background: rgba(0,90,18,0.15); color: #005a12; border: 1px solid #005a12; }}
        .badge-error {{ background: rgba(255,51,51,0.15); color: #ff3333; border: 1px solid #ff3333; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #003300; text-align: center; font-size: 11px; color: #003300; }}
        .footer .blink {{ animation: blink 1.5s ease-in-out infinite; }}
        @keyframes blink {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: #0a0a0a; }}
        ::-webkit-scrollbar-thumb {{ background: #005a12; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #00ff41; }}
        @media (max-width: 768px) {{ body {{ padding: 10px; }} .container {{ padding: 15px; }} .header h1 {{ font-size: 20px; }} .info-grid {{ grid-template-columns: repeat(2,1fr); }} table {{ font-size: 11px; }} }}
        @media (max-width: 480px) {{ .info-grid {{ grid-template-columns: 1fr; }} .systems-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="ascii-art"> 
            </div>
            <h1>RELATÓRIO DE BUSCA</h1>
            <div class="subtitle">Multi-Source CPF Reconnaissance Tool  |  v2.1  Green</div>
            <div class="date">Gerado em: {agora}</div>
        </div>
        <div class="info-grid">
            <div class="info-card"><div class="label">Sistemas Consultados</div><div class="value">{len(results)}</div></div>
            <div class="info-card"><div class="label">Contas Encontradas</div><div class="value">{found_count}</div></div>
            <div class="info-card"><div class="label">Nao Encontradas</div><div class="value yellow">{not_found_count}</div></div>
            <div class="info-card"><div class="label">Erros</div><div class="value red">{error_count}</div></div>
            <div class="info-card"><div class="label">Tempo Total</div><div class="value cyan">{tempo_total:.2f}s</div></div>
        </div>
        <div class="target-info">
            <div class="cpf-display">[ CPF: {cpf_fmt} ]</div>
            <div class="mode-badge {'mode-stealth' if stealth_mode else 'mode-noisy'}">Modo: {modo}</div>
            <div style="color: #005a12; font-size: 12px;">Rota: {rota}  |  Show All: {todos}</div>
        </div>
        <div class="section-title">Sistemas com Conta Encontrada</div>
        <div class="systems-grid">{sistemas_encontrados}</div>
        <div class="section-title">Resultado Detalhado por Sistema</div>
        <div class="table-container">
            <table>
                <thead><tr><th>Status</th><th>Sistema</th><th>URL</th><th>Dados</th><th>Erro</th></tr></thead>
                <tbody>{linhas_tabela}</tbody>
            </table>
        </div>
        <div class="footer">
            <span class="blink">[ SISTEMA FINALIZADO ]</span><br>
            CPF Hunter v2.1  |  Green Hacker Edition  |  {agora}
        </div>
    </div>
</body>
</html>"""
    return html


# =============================================================================
# INTERFACE GRÁFICA
# =============================================================================

class HackerGreenGUI:
    BG_COLOR = '#0a0a0a'
    FG_COLOR = '#00ff41'
    FG_DIM = '#008a1e'
    FG_RED = '#ff3333'
    FG_YELLOW = '#ffcc00'
    FG_CYAN = '#00ffff'
    SELECT_BG = '#001a00'
    BTN_ACTIVE_BG = '#003300'

    def __init__(self, root):
        self.root = root
        self.root.title("CPF Hunter v2.1 - Green Hacker Edition (Tor Ready)")
        self.root.configure(bg=self.BG_COLOR)
        self.root.minsize(1200, 750)

        self._config_styles()

        self.running = False
        self.stealth_mode = tk.BooleanVar(value=True)
        self.show_all = tk.BooleanVar(value=False)
        self.use_proxy = tk.BooleanVar(value=False)
        self.use_tor = tk.BooleanVar(value=False)
        self.proxy_host = tk.StringVar(value="127.0.0.1:8080")
        self.tor_host = tk.StringVar(value="127.0.0.1:9050")
        self.results_data = []
        self.last_cpf = ""
        self.tempo_busca = 0.0
        self.usou_tor = False

        self._build_header()
        self._build_controls()
        self._build_status_bar()
        self._build_main_area()

        self.root.grid_rowconfigure(4, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self._matrix_clock()

        self.root.bind('<Return>', lambda e: self.iniciar_busca())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-l>', lambda e: self.limpar_resultados())
        self.root.bind('<Control-e>', lambda e: self.exportar_html())

        self.use_tor.trace_add('write', self._toggle_route_mode)
        self.use_proxy.trace_add('write', self._toggle_route_mode)

        self.cpf_entry.focus_set()

    # ------------------------------------------------------------------
    # Tor check helpers (sem recursão)
    # ------------------------------------------------------------------

    def _check_tor(self):
        import asyncio
        from aiohttp import ClientSession

        tor_str = self.tor_entry.get().strip() or "127.0.0.1:9050"
        proxy = f"socks5://{tor_str}"   # sem o h
        

        async def test():
            try:
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(proxy, rdns=True)
                async with ClientSession(connector=connector) as session:
                    async with session.get(
                        "https://check.torproject.org/api/ip",
                        timeout=12
                    ) as resp:
                        data = await resp.json()
                        return data.get("IsTor", False) is True
            except Exception as e:
                self._log(f"[x] Teste Tor falhou: {e}", 'error')
                return False

        try:
            return asyncio.run(test())
        except Exception:
            return False

    def _set_tor_status_light(self, ok):
        """Atualiza o indicador visual do Tor (sem testar novamente)."""
        if ok:
            self.lbl_tor_status.config(text="● TOR ON", fg="#00ff41")
            self._log("[+] Tor confirmado: tráfego anonimizado", 'tor')
        else:
            self.lbl_tor_status.config(text="● TOR OFF", fg="#ff3333")
            self._log("[!] Tor NÃO está funcionando (verifique se está rodando)", 'error')

    # ------------------------------------------------------------------

    def _toggle_route_mode(self, *args):
        if self.use_tor.get() and self.use_proxy.get():
            self.use_proxy.set(False)

    def _config_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Hacker.Treeview', background=self.BG_COLOR, foreground=self.FG_COLOR,
                        fieldbackground=self.BG_COLOR, borderwidth=0, rowheight=26, font=('Consolas', 10))
        style.map('Hacker.Treeview', background=[('selected', self.SELECT_BG)], foreground=[('selected', self.FG_CYAN)])
        style.configure('Hacker.Treeview.Heading', background=self.SELECT_BG, foreground=self.FG_COLOR,
                        relief='flat', borderwidth=1, font=('Consolas', 10, 'bold'))
        style.map('Hacker.Treeview.Heading', background=[('active', self.SELECT_BG)])
        style.configure('Hacker.Horizontal.TProgressbar', background=self.FG_COLOR,
                        troughcolor=self.BG_COLOR, bordercolor=self.FG_COLOR,
                        lightcolor=self.FG_COLOR, darkcolor=self.FG_DIM)

    def _build_header(self):
        hf = tk.Frame(self.root, bg=self.BG_COLOR)
        hf.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 5))
        ascii_art = """\
  ██████  ██████  ███████ ██   ██ ██    ██ ███    ██ ████████ ███████ ██████
 ██      ██    ██ ██      ██   ██ ██    ██ ████   ██    ██    ██      ██   ██
 ██      ██    ██ ███████ ███████ ██    ██ ██ ██  ██    ██    █████   ██████
 ██      ██    ██      ██ ██   ██ ██    ██ ██  ██ ██    ██    ██      ██   ██
  ██████  ██████  ███████ ██   ██  ██████  ██   ████    ██    ███████ ██   ██ """
        tk.Label(hf, text=ascii_art, fg=self.FG_COLOR, bg=self.BG_COLOR,
                 font=('Consolas', 8, 'bold'), justify=tk.LEFT).pack()
        tk.Label(hf, text="╔══════════════════════════════════════════════════════════╗\n"
                          "║  Multi-Source CPF Reconnaissance Tool  |  v2.1  Green    ║\n"
                          "╚══════════════════════════════════════════════════════════╝",
                 fg=self.FG_DIM, bg=self.BG_COLOR, font=('Consolas', 9), justify=tk.CENTER).pack(pady=(2, 0))
        tk.Frame(hf, height=2, bg=self.FG_COLOR).pack(fill=tk.X, pady=(5, 0))

    def _build_controls(self):
        cf = tk.Frame(self.root, bg=self.BG_COLOR)
        cf.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        cf.grid_columnconfigure(1, weight=1)

        # Linha 1
        r1 = tk.Frame(cf, bg=self.BG_COLOR)
        r1.pack(fill=tk.X, pady=2)
        tk.Label(r1, text="[ CPF ]>", fg=self.FG_DIM, bg=self.BG_COLOR,
                 font=('Consolas', 11, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        self.cpf_entry = tk.Entry(r1, width=30, font=('Consolas', 12, 'bold'),
                                   bg=self.BG_COLOR, fg=self.FG_COLOR,
                                   insertbackground=self.FG_COLOR,
                                   relief='flat', bd=2,
                                   highlightthickness=1, highlightcolor=self.FG_COLOR,
                                   highlightbackground=self.FG_DIM)
        self.cpf_entry.pack(side=tk.LEFT, padx=5, ipady=4)
        self.cpf_entry.insert(0, "Digite o CPF (apenas números)")
        self.cpf_entry.bind('<FocusIn>', lambda e: self._on_entry_focus())
        self.cpf_entry.bind('<FocusOut>', lambda e: self._on_entry_blur())

        self.btn_iniciar = tk.Button(r1, text="[ INICIAR ]", command=self.iniciar_busca,
                                      bg=self.SELECT_BG, fg=self.BTN_ACTIVE_BG,
                                      activebackground=self.BTN_ACTIVE_BG,
                                      activeforeground=self.FG_COLOR,
                                      font=('Consolas', 11, 'bold'),
                                      relief='flat', bd=2, highlightthickness=1,
                                      highlightcolor=self.FG_COLOR, padx=15, pady=4, cursor='hand2')
        self.btn_iniciar.pack(side=tk.LEFT, padx=5)

        self.btn_parar = tk.Button(r1, text="[ PARAR ]", command=self.parar_busca,
                                    bg=self.SELECT_BG, fg=self.FG_RED,
                                    activebackground='#330000', activeforeground=self.FG_RED,
                                    font=('Consolas', 11, 'bold'), relief='flat', bd=2,
                                    highlightthickness=1, highlightcolor=self.FG_RED,
                                    padx=15, pady=4, cursor='hand2', state='disabled')
        self.btn_parar.pack(side=tk.LEFT, padx=5)

        btn_limpar = tk.Button(r1, text="[ LIMPAR ]", command=self.limpar_resultados,
                                bg=self.SELECT_BG, fg=self.FG_YELLOW,
                                activebackground='#332200', activeforeground=self.FG_YELLOW,
                                font=('Consolas', 11, 'bold'), relief='flat', bd=2,
                                highlightthickness=1, highlightcolor=self.FG_YELLOW,
                                padx=10, pady=4, cursor='hand2')
        btn_limpar.pack(side=tk.LEFT, padx=5)

        self.btn_export = tk.Button(r1, text="[ EXPORT HTML ]", command=self.exportar_html,
                                     bg=self.SELECT_BG, fg=self.FG_CYAN,
                                     activebackground='#003333', activeforeground=self.FG_CYAN,
                                     font=('Consolas', 11, 'bold'), relief='flat', bd=2,
                                     highlightthickness=1, highlightcolor=self.FG_CYAN,
                                     padx=10, pady=4, cursor='hand2')
        self.btn_export.pack(side=tk.LEFT, padx=5)

        # Linha 2
        r2 = tk.Frame(cf, bg=self.BG_COLOR)
        r2.pack(fill=tk.X, pady=5)

        self._mk_cb(r2, "[x] Stealth", self.stealth_mode, "Silencioso: pula sites que alertam o alvo")
        tk.Label(r2, text="  |  ", fg=self.FG_DIM, bg=self.BG_COLOR, font=('Consolas', 10)).pack(side=tk.LEFT)
        self._mk_cb(r2, "[x] Show All", self.show_all, "Mostra todos resultados")
        tk.Label(r2, text="  |  ", fg=self.FG_DIM, bg=self.BG_COLOR, font=('Consolas', 10)).pack(side=tk.LEFT)
        self._mk_cb(r2, "[x] TOR", self.use_tor, "Roteia via Tor (SOCKS5 :9050)")

        self.tor_entry = tk.Entry(r2, width=16, font=('Consolas', 10), bg=self.BG_COLOR, fg=self.FG_YELLOW,
                                   insertbackground=self.FG_COLOR, relief='flat', bd=1,
                                   highlightthickness=1, highlightcolor=self.FG_YELLOW,
                                   highlightbackground=self.FG_DIM)
        self.tor_entry.insert(0, "127.0.0.1:9050")
        self.tor_entry.pack(side=tk.LEFT, padx=3, ipady=2)

        # ---- Indicador visual do Tor CRIADO AQUI (antes era dead code) ----
        self.lbl_tor_status = tk.Label(
            r2, text="● TOR",
            fg="#555555", bg=self.BG_COLOR,
            font=('Consolas', 10, 'bold')
        )
        self.lbl_tor_status.pack(side=tk.LEFT, padx=(8, 0))

        tk.Label(r2, text="  |  ", fg=self.FG_DIM, bg=self.BG_COLOR, font=('Consolas', 10)).pack(side=tk.LEFT)
        self._mk_cb(r2, "[x] Proxy", self.use_proxy, "Proxy HTTP (Burp, mitmproxy)")

        self.proxy_entry = tk.Entry(r2, width=16, font=('Consolas', 10), bg=self.BG_COLOR, fg=self.FG_DIM,
                                     insertbackground=self.FG_COLOR, relief='flat', bd=1,
                                     highlightthickness=1, highlightcolor=self.FG_DIM,
                                     highlightbackground=self.FG_DIM)
        self.proxy_entry.insert(0, "127.0.0.1:8080")
        self.proxy_entry.pack(side=tk.LEFT, padx=3, ipady=2)

        tk.Label(r2, text="  |  ", fg=self.FG_DIM, bg=self.BG_COLOR, font=('Consolas', 10)).pack(side=tk.LEFT)
        self.lbl_info = tk.Label(r2, text="[ Pronto ]", fg=self.FG_DIM, bg=self.BG_COLOR, font=('Consolas', 10))
        self.lbl_info.pack(side=tk.LEFT)

    def _mk_cb(self, parent, text, var, tip=None):
        cb = tk.Checkbutton(parent, text=text, variable=var, bg=self.BG_COLOR, fg=self.FG_COLOR,
                             selectcolor=self.BG_COLOR, activebackground=self.BG_COLOR,
                             activeforeground=self.FG_COLOR, font=('Consolas', 10, 'bold'),
                             relief='flat', bd=0, highlightthickness=0)
        cb.pack(side=tk.LEFT)

    def _build_status_bar(self):
        sf = tk.Frame(self.root, bg=self.BG_COLOR)
        sf.grid(row=2, column=0, sticky='ew', padx=10, pady=2)
        self.progress = ttk.Progressbar(sf, mode='determinate', style='Hacker.Horizontal.TProgressbar', length=400)
        self.progress.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        self.lbl_status = tk.Label(sf, text="[ AGUARDANDO ]", fg=self.FG_DIM, bg=self.BG_COLOR, font=('Consolas', 9, 'bold'))
        self.lbl_status.pack(side=tk.LEFT, padx=5)
        self.lbl_counter = tk.Label(sf, text="0 / 0", fg=self.FG_DIM, bg=self.BG_COLOR, font=('Consolas', 9))
        self.lbl_counter.pack(side=tk.RIGHT, padx=5)
        tk.Frame(self.root, height=1, bg=self.FG_DIM).grid(row=3, column=0, sticky='ew', padx=10, pady=(2, 0))

    def _build_main_area(self):
        mf = tk.Frame(self.root, bg=self.BG_COLOR)
        mf.grid(row=4, column=0, sticky='nsew', padx=10, pady=(5, 10))
        mf.grid_rowconfigure(0, weight=3)
        mf.grid_rowconfigure(1, weight=1)
        mf.grid_columnconfigure(0, weight=1)

        tf = tk.Frame(mf, bg=self.BG_COLOR, highlightthickness=1, highlightcolor=self.FG_DIM)
        tf.grid(row=0, column=0, sticky='nsew', pady=(0, 5))
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        cols = ('#1', '#2', '#3', '#4', '#5')
        self.tree = ttk.Treeview(tf, columns=cols, show='headings', style='Hacker.Treeview', selectmode='extended')
        for c, t in zip(cols, ['Status', 'Sistema', 'URL', 'Dados', 'Erro']):
            self.tree.heading(c, text=t)
        self.tree.column('#1', width=80, anchor='w')
        self.tree.column('#2', width=400, anchor='w')
        self.tree.column('#3', width=900, anchor='w')
        self.tree.column('#4', width=500, anchor='w')
        self.tree.column('#5', width=2000, anchor='w')

        vsb = ttk.Scrollbar(tf, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky='ns')
        hsb = ttk.Scrollbar(tf, orient='horizontal', command=self.tree.xview)
        self.tree.configure(xscrollcommand=hsb.set)
        hsb.grid(row=1, column=0, sticky='ew')
        self.tree.grid(row=0, column=0, sticky='nsew')
        self.tree.bind('<Double-1>', self._copy_row)

        lf = tk.Frame(mf, bg=self.BG_COLOR, highlightthickness=1, highlightcolor=self.FG_DIM)
        lf.grid(row=1, column=0, sticky='nsew')
        lf.grid_rowconfigure(0, weight=1)
        lf.grid_columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(lf, bg=self.BG_COLOR, fg=self.FG_DIM,
                                                   insertbackground=self.FG_COLOR, font=('Consolas', 9),
                                                   relief='flat', bd=5, state='disabled', wrap=tk.WORD,
                                                   highlightthickness=0)
        
        self.log_text.grid(row=0, column=0, sticky='nsew')
        self.log_text.tag_configure('found', foreground=self.FG_COLOR, font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('error', foreground=self.FG_RED)
        self.log_text.tag_configure('info', foreground=self.FG_DIM)
        self.log_text.tag_configure('success', foreground=self.FG_CYAN, font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('warn', foreground=self.FG_YELLOW)
        self.log_text.tag_configure('tor', foreground='#ff6600', font=('Consolas', 9, 'bold'))

    def _matrix_clock(self):
        cf = tk.Frame(self.root, bg=self.BG_COLOR)
        cf.grid(row=5, column=0, sticky='e', padx=15, pady=(0, 5))
        self.clk = tk.Label(cf, text="", fg=self.FG_DIM, bg=self.BG_COLOR, font=('Consolas', 8))
        self.clk.pack()
        def upd():
            self.clk.config(text=f"[ {datetime.now().strftime('%H:%M:%S')} ]  |  CPF Hunter v2.1")
            self.root.after(1000, upd)
        upd()

    def _on_entry_focus(self):
        if self.cpf_entry.get() == "Digite o CPF (apenas números)":
            self.cpf_entry.delete(0, tk.END)
            self.cpf_entry.config(fg=self.FG_COLOR)

    def _on_entry_blur(self):
        if not self.cpf_entry.get().strip():
            self.cpf_entry.insert(0, "Digite o CPF (apenas números)")
            self.cpf_entry.config(fg=self.FG_DIM)

    def _log(self, msg, tag='info'):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, msg + '\n', tag)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def _upd_status(self, cur, total, res=None):
        self.progress['value'] = (cur / total) * 100
        self.lbl_counter.config(text=f"{cur} / {total}")
        if res:
            if res['found']:
                self.lbl_status.config(text=f"[ ENCONTRADO: {res['app']} ]", fg=self.FG_COLOR)
            elif res['error']:
                self.lbl_status.config(text=f"[ ERRO: {res['app']} ]", fg=self.FG_RED)
            else:
                self.lbl_status.config(text=f"[ VERIFICANDO: {res['app']} ]", fg=self.FG_DIM)
        self.root.update_idletasks()

    def _add_tree(self, r):
        st = "[+]" if r['found'] else ("[x]" if r['error'] else "[-]")
        d = str(r['data'] or "")[:57] + "..." if len(str(r['data'] or "")) > 60 else str(r['data'] or "")
        vals = (st, r['app'], r['url'], d, str(r['error'] or ""))
        item = self.tree.insert('', tk.END, values=vals)
        if r['found']:
            self.tree.tag_configure('fr', foreground=self.FG_COLOR, font=('Consolas', 10, 'bold'))
            self.tree.item(item, tags=('fr',))
        elif r['error']:
            self.tree.tag_configure('er', foreground=self.FG_RED)
            self.tree.item(item, tags=('er',))
        else:
            self.tree.tag_configure('nr', foreground=self.FG_DIM)
            self.tree.item(item, tags=('nr',))

    def _copy_row(self, e=None):
        s = self.tree.selection()
        if not s: return
        v = self.tree.item(s[0], 'values')
        self.root.clipboard_clear()
        self.root.clipboard_append(" | ".join(str(x) for x in v))

    # ---- Export HTML ----
    def exportar_html(self, e=None):
        if not self.results_data:
            return messagebox.showwarning("Sem dados", "Execute uma busca primeiro.")
        cpf = self.last_cpf
        if not cpf:
            return messagebox.showwarning("Sem dados", "Nenhum CPF consultado.")
        arq = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("Todos", "*.*")],
            initialfile=f"cpf_hunter_{cpf}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        if not arq:
            return
        try:
            html = gerar_html(cpf, self.results_data, self.stealth_mode.get(),
                              self.show_all.get(), self.tempo_busca, self.usou_tor)
            with open(arq, 'w', encoding='utf-8') as f:
                f.write(html)
            self._log(f"[+] HTML salvo: {arq}", 'success')
            if messagebox.askyesno("Sucesso", f"Salvo em:\n{arq}\n\nAbrir no navegador?"):
                import webbrowser
                webbrowser.open(f'file://{os.path.abspath(arq)}')
        except Exception as ex:
            self._log(f"[x] Erro: {ex}", 'error')
            messagebox.showerror("Erro", str(ex))

    # ---- Lógica ----
    def iniciar_busca(self):
        if self.running:
            return
        raw = self.cpf_entry.get().strip()
        if raw == "Digite o CPF (apenas números)":
            self._log("[!] Digite um CPF válido.", 'warn')
            return

        # Validar com debug para diagnóstico
        cpf, erro = validar_cpf(raw)
        if not cpf:
            self._log(f"[!] CPF inválido: {raw}", 'error')
            self._log(f"[!] Motivo: {erro}", 'error')
            self._log(f"[!] Bytes recebidos: {raw.encode('utf-8').hex()}", 'error')
            self._log(f"[!] Tente digitar manualmente apenas os 11 números.", 'warn')
            self.lbl_info.config(text="[ CPF Inválido ]", fg=self.FG_RED)
            return

        self.running = True
        self.last_cpf = cpf
        self.btn_iniciar.config(state='disabled')
        self.btn_parar.config(state='normal')
        self.cpf_entry.config(state='disabled')
        self.btn_export.config(state='disabled')

        self.limpar_resultados()

        cpf_fmt = formatar_cpf(cpf)
        self.lbl_info.config(text=f"[ Alvo: {cpf_fmt} ]", fg=self.FG_COLOR)

        self.proxy_url = None
        self.usou_tor = False

        # ---- Tor / Proxy setup + teste real do Tor ----
        if self.use_tor.get():
            tor_str = self.tor_entry.get().strip()
            if tor_str:
                self.proxy_url = f"socks5://{tor_str}"   # ← socks5 (sem o h)
                self.usou_tor = True
                self._log(f"[*] Usando Tor: {self.proxy_url}", 'tor')

                self.lbl_tor_status.config(text="● TESTANDO...", fg="#ffcc00")
                self.root.update_idletasks()
                tor_ok = self._check_tor()
                self._set_tor_status_light(tor_ok)

                if not tor_ok:
                    self._log("[!] Abortando: Tor não está respondendo.", 'error')
                    self.lbl_info.config(text="[ Tor offline ]", fg=self.FG_RED)
                    self.running = False
                    self.btn_iniciar.config(state='normal')
                    self.btn_parar.config(state='disabled')
                    self.cpf_entry.config(state='normal')
                    self.btn_export.config(state='normal')
                    return
                
        elif self.use_proxy.get():
            px = self.proxy_entry.get().strip()
            if px:
                self.proxy_url = f"http://{px}"
                self._log(f"[*] Usando proxy HTTP: {self.proxy_url}", 'info')

        self._log(f"[+] CPF: {cpf_fmt}", 'found')
        self._log(f"[+] Stealth: {self.stealth_mode.get()}, Show All: {self.show_all.get()}", 'info')
        self._log(f"[+] Rota: {'Tor' if self.usou_tor else 'Proxy' if self.proxy_url else 'Direta'}", 'info')
        self._log("─" * 90, 'info')
        self.progress['value'] = 0
        self.lbl_status.config(text="[ INICIANDO ]", fg=self.FG_YELLOW)
        self.lbl_counter.config(text="0 / 0")

        Thread(target=self._thread_busca, args=(cpf,), daemon=True).start()

    def parar_busca(self):
        if self.running:
            self.running = False
            self._log("[!] Interrompido pelo usuário.", 'warn')
            self._finalizar()

    def limpar_resultados(self, keep_log=False):
        for i in self.tree.get_children():
            self.tree.delete(i)
        if not keep_log:
            self.log_text.config(state='normal')
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state='disabled')
        self.progress['value'] = 0
        self.lbl_counter.config(text="0 / 0")
        self.lbl_status.config(text="[ AGUARDANDO ]", fg=self.FG_DIM)

    def _finalizar(self):
        self.running = False
        self.btn_iniciar.config(state='normal')
        self.btn_parar.config(state='disabled')
        self.cpf_entry.config(state='normal')
        self.btn_export.config(state='normal')

        found = len([r for r in self.results_data if r and r.get('found')])
        errs = len([r for r in self.results_data if r and r.get('error')])

        self.lbl_status.config(text="[ CONCLUÍDO ]" if self.progress['value'] >= 100 else "[ INTERROMPIDO ]",
                                fg=self.FG_COLOR if self.progress['value'] >= 100 else self.FG_YELLOW)
        self._log("─" * 90, 'info')
        self._log(f"[+] Finalizado em {self.tempo_busca:.2f}s. Encontradas: {found}, Erros: {errs}", 'success')
        self._log("[+] Use [ EXPORT HTML ] para salvar relatório.", 'info')
        self.lbl_info.config(text=f"[ {found} conta(s) ]" if found else "[ Nenhuma conta ]",
                              fg=self.FG_COLOR if found else self.FG_YELLOW)

    def _thread_busca(self, cpf):
        inicio = time.time()
        async def run():
            sites = LOOKUP_DATA['sites']
            results = []
            for idx, s in enumerate(sites):
                if not self.running:
                    break
                r = await do_request(s, cpf, self.stealth_mode.get(), self.proxy_url)
                self.root.after(0, lambda res=r: self._process(res))
                self.root.after(0, lambda i=idx+1, t=len(sites), res=r: self._upd_status(i, t, res))
                results.append(r)
            self.tempo_busca = time.time() - inicio
            self.results_data = results
            self.root.after(0, self._finalizar)
        asyncio.run(run())

    def _process(self, r):
        if r['found']:
            self._add_tree(r)
            d = r['data'] or ""
            self._log(f"[+] {r['app']}: CONTA ENCONTRADA" + (f" | {d}" if d else ""), 'found')
        elif self.show_all.get() or r['error']:
            self._add_tree(r)
            if r['error']:
                self._log(f"[x] {r['app']}: {r['error'][:100]}", 'error')
            else:
                self._log(f"[-] {r['app']}: Não encontrado", 'info')


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    root = tk.Tk()
    app = HackerGreenGUI(root)
    root.mainloop()
