import os

print("""\n

    ██████╗ ██╗███╗   ██╗ ██████╗     ████████╗██████╗  █████╗  ██████╗███████╗██████╗ ████████╗
    ██╔══██╗██║████╗  ██║██╔════╝     ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗╚══██╔══╝
    ██████╔╝██║██╔██╗ ██║██║  ███╗       ██║   ██████╔╝███████║██║     █████╗  ██████╔╝   ██║   
    ██╔═══╝ ██║██║╚██╗██║██║   ██║       ██║   ██╔══██╗██╔══██║██║     ██╔══╝  ██╔══██╗   ██║   
    ██║     ██║██║ ╚████║╚██████╔╝       ██║   ██║  ██║██║  ██║╚██████╗███████╗██║  ██║   ██║   
    ╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝        ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝   ╚═╝   
                                                                                                                                                                                                                                                                                                                                
""")

def ping_website():
    site_name = input("Digite o nome do site para ping: ")    
    ping_command = f"ping -4 -n 10 {site_name}"
    os.system(ping_command)
   

def tracert_website():
    print("\n")
    site_name = input("\nDigite o nome do site para traceroute: ")
    tracert_command = f"tracert -h 10 -4 {site_name}"
    os.system(tracert_command)

def main():
    ping_website()
    print("===============================================================")
    scan_choice = input("\nDeseja fazer o tracert do site? (s/n): ").lower()
    if scan_choice == 's':
        tracert_website()    

if __name__ == "__main__":
    main()
input("\n[PRESIONE ENTER PARA SAIR]\n")
