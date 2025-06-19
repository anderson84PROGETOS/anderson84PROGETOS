import subprocess
import re
import sys
import requests
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗    ██╗██╗███████╗██╗     ██████╗ ███████╗ ██████╗ 
██║    ██║██║██╔════╝██║    ██╔════╝ ██╔════╝██╔═══██╗
██║ █╗ ██║██║█████╗  ██║    ██║  ███╗█████╗  ██║   ██║
██║███╗██║██║██╔══╝  ██║    ██║   ██║██╔══╝  ██║   ██║
╚███╔███╔╝██║██║     ██║    ╚██████╔╝███████╗╚██████╔╝
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝     ╚═════╝ ╚══════╝ ╚═════╝ 
                               
""")

def consulta_fabricante(bssid):
    # Extrai OUI (3 primeiros bytes)
    oui = bssid.upper().replace(":", "")[:6]
    url = f"https://api.macvendors.com/{oui}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text
        else:
            return "Fabricante não encontrado"
    except Exception as e:
        return Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao consultar fabricante: {e}"

def main():
    bssid = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "🔍 Digite o BSSID do roteador (ex: 54:a6:5c:8e:4f:3f): ").strip()

    fabricante = consulta_fabricante(bssid)
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n🏷️ Fabricante: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{fabricante}")

    try:
        result = subprocess.run(['geomac', '-P', bssid], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\n❌ Erro ao executar geomac para o BSSID {bssid}\n")
        sys.exit(1)

    output = result.stdout
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\n=== Saída do geomac ===\n")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + output)

    pattern = re.compile(r'^\s*(\w+)\s*\|\s*([+-]?\d+\.\d+),\s*([+-]?\d+\.\d+)', re.MULTILINE)
    matches = pattern.findall(output)

    if not matches:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\n❌ Nenhuma localização encontrada para o BSSID {bssid}\n")
        sys.exit(1)

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n✅ Geolocalizações Encontradas\n")

    for source, lat, lon in matches:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n📍Fonte: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{source}")
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nCoordenadas: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{lat},{lon}")
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n🗺️ Google Maps: https://www.google.com/maps/place/{lat},{lon}")
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n🚗 Street View: https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}&heading=-45&pitch=38&fov=80\n")

if __name__ == "__main__":
    main()
    
input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n") 
