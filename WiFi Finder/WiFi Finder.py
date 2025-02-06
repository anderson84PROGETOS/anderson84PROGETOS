import subprocess
import re
from mac_vendor_lookup import MacLookup
from colorama import init, Fore, Style
# Inicializando o colorama
init(autoreset=True)
# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗    ██╗██╗███████╗██╗    ███████╗██╗███╗   ██╗██████╗ ███████╗██████╗ 
██║    ██║██║██╔════╝██║    ██╔════╝██║████╗  ██║██╔══██╗██╔════╝██╔══██╗
██║ █╗ ██║██║█████╗  ██║    █████╗  ██║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
██║███╗██║██║██╔══╝  ██║    ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
╚███╔███╔╝██║██║     ██║    ██║     ██║██║ ╚████║██████╔╝███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝                                                                                                                                                                                                                                                                                                                         
""")
print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Exemplo: Copiar e colar no website o BSSID Endereço MAC: f0:25:8e:cb:5f:14")
print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nSe não aparecer o nome do Fabricante, acesse o website: https://macvendors.com\n")

def scan_wifi_windows():
    """Escaneia redes Wi-Fi usando netsh no Windows."""
    padrao_ssid = re.compile(r"SSID \d+ : (.+)")
    padrao_bssid = re.compile(r"BSSID \d+\s+: (.+)")
    padrao_sinal = re.compile(r"Sinal\s+: (\d+)%")
    padrao_canal = re.compile(r"Canal\s+: (\d+)")
    padrao_autenticacao = re.compile(r"Autenticação\s+: (.+)")
    redes_encontradas = {}

    try:
        result = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=Bssid"], encoding='cp850')
        redes = result.split("\n\n")

        for rede in redes:
            ssid = padrao_ssid.search(rede)
            bssid = padrao_bssid.search(rede)
            sinal = padrao_sinal.search(rede)
            canal = padrao_canal.search(rede)
            autenticacao = padrao_autenticacao.search(rede)

            if ssid and bssid:
                mac_address = bssid.group(1)
                if mac_address not in redes_encontradas:
                    try:
                        fabricante = MacLookup().lookup(mac_address)
                    except:
                        fabricante = "Desconhecido"

                    sinal_status = "Fraco" if int(sinal.group(1)) < 40 else "Médio" if int(sinal.group(1)) < 70 else "Forte"
                    seguranca = autenticacao.group(1) if autenticacao else "Desconhecido"
                    redes_encontradas[mac_address] = (ssid.group(1), canal.group(1), fabricante, sinal.group(1), sinal_status, seguranca)
    except subprocess.CalledProcessError as e:
        print(f"\nErro ao executar netsh: {e}")    
    return redes_encontradas

def mostrar_resultados():
    redes_netsh = scan_wifi_windows()
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n=== Redes Wi-Fi detectadas pelo Windows (netsh) ===\n")
    print("SSID                         BSSID                     Canal    Fabricante                               Sinal         Segurança")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "=" * 134)
    for bssid, (ssid, canal, fabricante, sinal, sinal_status, seguranca) in redes_netsh.items():
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{ssid:<28} {bssid:<25} {canal:<8} {fabricante:<40} {sinal}% ({sinal_status:<5})    {seguranca}")   

if __name__ == "__main__":
    mostrar_resultados()
input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
