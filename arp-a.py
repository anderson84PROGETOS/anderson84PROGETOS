import subprocess
import webbrowser

print("""

     █████╗ ██████╗ ██████╗            █████╗ 
    ██╔══██╗██╔══██╗██╔══██╗          ██╔══██╗
    ███████║██████╔╝██████╔╝    █████╗███████║
    ██╔══██║██╔══██╗██╔═══╝     ╚════╝██╔══██║
    ██║  ██║██║  ██║██║               ██║  ██║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝               ╚═╝  ╚═╝
                                            
""")

print("\nAcesse este site para descobrir o nome do fabricante do MAC do modem:  https://macvendors.com\n")

def open_mac_vendor_site():
    webbrowser.open("https://macvendors.com")

def arp_scan():
    try:
        # Executa o comando arp -a e captura a saída
        arp_output = subprocess.check_output(["arp", "-a"], universal_newlines=True)
        
        # Separa as linhas da saída
        arp_lines = arp_output.split('\n')
        
        # Dicionário para armazenar contagem de IPs
        ip_count = {}
        
        # Dicionário para armazenar MACs para cada IP
        ip_mac_mapping = {}
        
        # Loop pelas linhas e extrai IP e MAC
        for line in arp_lines:
            if 'dynamic' in line.lower():
                parts = line.split()
                if len(parts) >= 3:
                    ip = parts[1]
                    mac = parts[3]
                    
                    # Atualiza contagem de IP
                    ip_count[ip] = ip_count.get(ip, 0) + 1
                    
                    # Atualiza o mapeamento de MAC para o IP
                    if ip not in ip_mac_mapping:
                        ip_mac_mapping[ip] = []
                    ip_mac_mapping[ip].append(mac)
        
        # IPs e MACs repetidos
        repeated_ips = [ip for ip, count in ip_count.items() if count > 1]
        repeated_mac = [mac for ip, mac_list in ip_mac_mapping.items() if len(mac_list) > 1 for mac in mac_list]
        
        # Imprime IPs e MACs repetidos
        print("\nIPs repetidos:", repeated_ips)
        print("MACs repetidos:", repeated_mac)
        
        # Imprime a saída completa do arp -a
        print("\nSaída completa do arp -a")
        print(arp_output)
    
    except subprocess.CalledProcessError as e:
        print("Erro ao executar o comando arp -a", e)

if __name__ == "__main__":
    arp_scan()

    open_site = input("\nDeseja acessar o site https://macvendors.com? (s/n): ").lower()
    if open_site == 's':
        open_mac_vendor_site()

input("\n➡️  PRESSIONE ENTER PARA SAIR ➡️\n") 
