import subprocess
import re

# Função para escanear redes Wi-Fi usando netsh e formatar a saída
def scan_wifi_windows():
    print("\nEscaneando redes Wi-Fi disponíveis no Windows\n")
    try:
        # Executa o comando e define a codificação para cp850
        result = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=Bssid"], encoding='cp850')
        
        # Divide a saída em blocos, um para cada rede Wi-Fi
        redes = result.split("\n\n")
        
        # Regex para extrair informações necessárias
        padrao_ssid = re.compile(r"SSID \d+ : (.+)")
        padrao_bssid = re.compile(r"BSSID \d+\s+: (.+)")
        padrao_sinal = re.compile(r"Sinal\s+: (\d+)%")
        padrao_tipo_radio = re.compile(r"Tipo de rádio\s+: (.+)")
        padrao_canal = re.compile(r"Canal\s+: (\d+)")
        padrao_autenticacao = re.compile(r"Autenticação\s+: (.+)")
        padrao_criptografia = re.compile(r"Criptografia\s+: (.+)")

        # Dicionário para mapear criptografias técnicas para tipos comuns
        tipos_criptografia = {
            "WEP": "WEP",
            "TKIP": "WPA",
            "CCMP": "WPA2",
            "GCMP": "WPA3"
        }

        # Loop para processar cada rede Wi-Fi detectada
        for rede in redes:
            ssid = padrao_ssid.search(rede)
            bssid = padrao_bssid.search(rede)
            sinal = padrao_sinal.search(rede)
            tipo_radio = padrao_tipo_radio.search(rede)
            canal = padrao_canal.search(rede)
            autenticacao = padrao_autenticacao.search(rede)
            criptografia = padrao_criptografia.search(rede)
            
            # Exibindo a rede formatada
            if ssid:
                print(f"SSID: {ssid.group(1)}\n")
            if bssid:
                print(f"BSSID: {bssid.group(1)}\n")
            if sinal:
                print(f"Sinal: {sinal.group(1)}%\n")
            if tipo_radio:
                print(f"Tipo de rádio: {tipo_radio.group(1)}\n")
            if canal:
                print(f"Canal: {canal.group(1)}\n")
            if autenticacao:
                print(f"Autenticação: {autenticacao.group(1)}\n")
            if criptografia:
                # Mapeia o tipo de criptografia para um tipo mais comum
                tipo_segurança = tipos_criptografia.get(criptografia.group(1), criptografia.group(1))
                print(f"Criptografia (Segurança): {tipo_segurança}")
                
            # Separador entre redes
            print("\n=============================================\n")
    
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar netsh: {e}")

# Execução da função
if __name__ == "__main__":
    scan_wifi_windows()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
