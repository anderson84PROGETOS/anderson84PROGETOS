import requests
import json
import sys

print(r"""            
 ___  __  __  ____  ___     ___  ____  ____  ____  ___ 
/ __)(  )(  )(  _ \/ __)   / __)( ___)(  _ \(_  _)/ __)
\__ \ )(__)(  ) _ <\__ \  ( (__  )__)  )   /  )(  \__ \
(___/(______)(____/(___/   \___)(____)(_)\_) (__) (___/
        
""")     

alvo = input("\nDigite o nome do site alvo: ").rstrip()

print("\n🔎 Coletando Informações Espere 🔍\n")

req = requests.get("https://crt.sh/?q=%.{d}&output=json".format(d=alvo))
dados = json.loads(req.text)

for (Key,value) in enumerate(dados):
    print(value['name_value'])
    
input("\n🔎 Informações Enserada Aperte Enter Sair 🔍\n") 
