import subprocess
import re
from colorama import init, Fore, Style
from pywifi import PyWiFi

# Inicializando o colorama
init(autoreset=True)
# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗    ██╗██╗███████╗██╗    ███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗ 
██║    ██║██║██╔════╝██║    ██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗
██║ █╗ ██║██║█████╗  ██║    ███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝
██║███╗██║██║██╔══╝  ██║    ╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗
╚███╔███╔╝██║██║     ██║    ███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝                                                                                                                                                                                                                                                       
""")

def scan_wifi_windows():
    print(Fore.LIGHTCYAN_EX + "\nEscaneando redes Wi-Fi disponíveis no Windows\n")
    try:
        result = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=Bssid"], encoding='cp850')
        redes = result.split("\n\n")
        
        wifi = PyWiFi()
        iface = wifi.interfaces()[0]
        iface.scan()
        scan_results = iface.scan_results()
        
        padrao_ssid = re.compile(r"SSID \d+ : (.+)")
        padrao_bssid = re.compile(r"BSSID \d+\s+: (.+)")
        padrao_sinal = re.compile(r"Sinal\s+: (\d+)%")
        padrao_tipo_radio = re.compile(r"Tipo de rádio\s+: (.+)")
        padrao_canal = re.compile(r"Canal\s+: (\d+)")
        padrao_autenticacao = re.compile(r"Autenticação\s+: (.+)")
        padrao_criptografia = re.compile(r"Criptografia\s+: (.+)")

        output = ""
        for rede in redes:
            ssid = padrao_ssid.search(rede)
            bssid = padrao_bssid.search(rede)
            sinal = padrao_sinal.search(rede)
            tipo_radio = padrao_tipo_radio.search(rede)
            canal = padrao_canal.search(rede)
            autenticacao = padrao_autenticacao.search(rede)
            criptografia = padrao_criptografia.search(rede)

            if ssid:
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "SSID: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + ssid.group(1))
                output += f"SSID: {ssid.group(1)}\n"
            if bssid:
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nBSSID: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + bssid.group(1))
                output += f"BSSID: {bssid.group(1)}\n"            
            if tipo_radio:
                print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nTipo de rádio: {tipo_radio.group(1)}")
                output += f"Tipo de rádio: {tipo_radio.group(1)}\n"            
            if autenticacao:
                print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"Autenticação: {autenticacao.group(1)}")
                output += f"Autenticação: {autenticacao.group(1)}\n"
            if criptografia:
                print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"Criptografia: {criptografia.group(1)}")
                output += f"Criptografia: {criptografia.group(1)}\n"                
            if canal:
                print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nCanal: {canal.group(1)}")
                output += f"Canal: {canal.group(1)}\n"    
            if sinal:
                sinal_valor = int(sinal.group(1))
                cor_sinal = Fore.LIGHTGREEN_EX + Style.BRIGHT if sinal_valor > 70 else Fore.LIGHTYELLOW_EX + Style.BRIGHT  if sinal_valor > 40 else Fore.LIGHTRED_EX + Style.BRIGHT
                print(cor_sinal + f"\nSinal Wifi: {sinal.group(1)}%")
                output += f"Sinal Wifi: {sinal.group(1)}%\n"
                print(Fore.WHITE + "==========================\n")    
            
            print("\n")
            output += "==========================\n\n"
        
        save_results(output)
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"\nErro ao executar netsh: {e}")
    except Exception as e:
        print(Fore.RED + f"\nErro ao escanear redes Wi-Fi: {e}")

def save_results(output):
    file_path = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Digite o caminho do arquivo para salvar os resultados (exemplo: resultados.txt): ")
    try:
        with open(file_path, "w") as file:
            file.write(output)
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nResultados salvos em: {file_path}")
    except Exception:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nO arquivo NÃO foi salvo")

if __name__ == "__main__":
    scan_wifi_windows()

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
