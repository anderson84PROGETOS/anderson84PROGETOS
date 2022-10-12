#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
import requests, json, sys
import socket
import ipaddress
import re
port_range_pattern = re.compile("([0-9]+)-([0-9]+)")
port_min = 0
port_max = 65535

print(r"""                

 ____        _            ____          _       
/ ___| _   _| |__  ___   / ___|___ _ __| |_ ___ 
\___ \| | | | '_ \/ __| | |   / _ \ '__| __/ __|
 ___) | |_| | |_) \__ \ | |__|  __/ |  | |_\__ \
|____/ \__,_|_.__/|___/  \____\___|_|   \__|___/                                                
                                                                                                                        
""")
print("Coletando Informasao Espere.....")

alvo = sys.argv[1].rstrip()

req = requests.get("https://crt.sh/?q=%.{d}&output=json".format(d=alvo))

dados = json.loads(req.text)

for (Key,value) in enumerate(dados):    
    print(value['name_value'])
    
    
    
    
