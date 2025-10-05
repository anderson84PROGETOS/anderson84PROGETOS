import psutil
from prettytable import PrettyTable
from colorama import Fore, Style, init

# Inicializa o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + Style.BRIGHT + """
                 _           _             _       _                   _      _   _         _       _      __   _               _         _            
                | |         | |           | |     | |                 | |    | | (_)       | |     | |    / _| (_)             | |       | |           
  _ __     ___  | |_   ___  | |_    __ _  | |_    | |_    __ _   ___  | | __ | |  _   ___  | |_    | |   | |_   _   _ __     __| |  ___  | |_   _ __   
 | '_ \   / _ \ | __| / __| | __|  / _` | | __|   | __|  / _` | / __| | |/ / | | | | / __| | __|   | |   |  _| | | | '_ \   / _` | / __| | __| | '__|  
 | | | | |  __/ | |_  \__ \ | |_  | (_| | | |_    | |_  | (_| | \__ \ |   <  | | | | \__ \ | |_    | |   | |   | | | | | | | (_| | \__ \ | |_  | |     
 |_| |_|  \___|  \__| |___/  \__|  \__,_|  \__|    \__|  \__,_| |___/ |_|\_\ |_| |_| |___/  \__|   | |   |_|   |_| |_| |_|  \__,_| |___/  \__| |_|     
                                                                                                   | |                                                 
                                                                                                   |_|                                                                                                                                                                                                                                                                                                                             
""")

print("netstat -ano          tasklist | findstr 852\n")
# Cria a tabela
tabela = PrettyTable()
tabela.field_names = ["name", "port", "address", "pid", "tasklist_info"]

# Itera sobre todas as conexões de rede
for conn in psutil.net_connections(kind='inet'):
    try:
        processo = psutil.Process(conn.pid)
        nome = processo.name()
        pid = conn.pid
        # Sessão (Windows) - não disponível direto em psutil, podemos usar 1 como placeholder
        sessao = "Console"
        num_sessao = 1
        memoria = f"{processo.memory_info().rss // 1024} K"
        tasklist_info = f"{nome:<25}{pid:<8}{sessao:<10}{num_sessao:<12}{memoria:<10}"
    except:
        nome = "N/A"
        pid = "N/A"
        tasklist_info = "N/A"
    
    port = conn.laddr.port if conn.laddr else "N/A"
    address = conn.laddr.ip if conn.laddr else "N/A"

    # Cores
    nome_col = Fore.LIGHTGREEN_EX + Style.BRIGHT + str(nome)
    port_col = Fore.LIGHTYELLOW_EX + Style.BRIGHT + str(port)
    address_col = Fore.LIGHTCYAN_EX + Style.BRIGHT + str(address)
    pid_col = Fore.LIGHTMAGENTA_EX + Style.BRIGHT + str(pid)
    tasklist_col = Fore.LIGHTRED_EX + tasklist_info

    tabela.add_row([nome_col, port_col, address_col, pid_col, tasklist_col])

# Exibe a tabela
print(tabela)

input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
