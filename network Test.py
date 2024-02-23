import os
import speedtest

def print_banner():
    print("""

    ███╗   ██╗███████╗████████╗██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗    ████████╗███████╗███████╗████████╗
    ████╗  ██║██╔════╝╚══██╔══╝██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝    ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝
    ██╔██╗ ██║█████╗     ██║   ██║ █╗ ██║██║   ██║██████╔╝█████╔╝        ██║   █████╗  ███████╗   ██║   
    ██║╚██╗██║██╔══╝     ██║   ██║███╗██║██║   ██║██╔══██╗██╔═██╗        ██║   ██╔══╝  ╚════██║   ██║   
    ██║ ╚████║███████╗   ██║   ╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗       ██║   ███████╗███████║   ██║   
    ╚═╝  ╚═══╝╚══════╝   ╚═╝    ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝       ╚═╝   ╚══════╝╚══════╝   ╚═╝                                                                                                         
""")

def ping_website():
    site_name_v4 = input("Digite o nome do site Teste IPv4 para ping: ")
    ping_command_v4 = f"ping -4 -n 10 {site_name_v4}"
    os.system(ping_command_v4)

    ipv6_choice = input("\nDeseja testar o IPv6? (s/n): ").lower()
    if ipv6_choice == 's':
        ipv6_test()
        scan_choice = input("\nDeseja fazer o traceroute do site? (s/n): ").lower()
        if scan_choice == 's':
            tracert_website()
    else:
        scan_choice = input("\nDeseja fazer o traceroute do site? (s/n): ").lower()
        if scan_choice == 's':
            tracert_website()

def ipv6_test():
    site_name_v6 = input("\nDigite o nome do site Teste IPv6 para ping: ")
    ping_command_v6 = f"ping -6 -n 10 {site_name_v6}"
    os.system(ping_command_v6)

def tracert_website():
    print("\n")
    site_name = input("\nDigite o nome do site para traceroute: ")
    tracert_command = f"tracert -h 10 -4 {site_name}"
    os.system(tracert_command)

def testar_internet():
    # Cria um objeto Speedtest
    st = speedtest.Speedtest()
    print("====================================")

    print("\nTestando velocidade da internet...")

    # Realiza o teste de velocidade
    download_speed = st.download() / (1024 * 1024)  # Convertendo bytes para megabits
    upload_speed = st.upload() / (1024 * 1024)  # Convertendo bytes para megabits

    print("\nVelocidade de Download:", round(download_speed, 2), "Mbps")
    print("\nVelocidade de Upload:", round(upload_speed, 2), "Mbps")

    return max(download_speed, upload_speed)

def verificar_status(speed, limite_download=100, limite_upload=40):
    if speed >= max(limite_download, limite_upload):
        return "\nInternet Está Boa!"
    else:
        return "\nInternet Está Ruim!"

def main():
    print_banner()
    ping_website()  # Realiza o ping antes de testar a internet
    speed = testar_internet()  # Testa a internet e obtém a velocidade máxima
    status = verificar_status(speed)
    print(status)
    input("\nTeste Terminado [PRESSIONE ENTER PARA SAIR]\n")

# Chamada para a função main
if __name__ == "__main__":
    main()
