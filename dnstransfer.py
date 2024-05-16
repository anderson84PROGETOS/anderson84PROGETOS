import subprocess

print("""

██████╗ ███╗   ██╗███████╗    ████████╗██████╗  █████╗ ███╗   ██╗███████╗███████╗███████╗██████╗ 
██╔══██╗████╗  ██║██╔════╝    ╚══██╔══╝██╔══██╗██╔══██╗████╗  ██║██╔════╝██╔════╝██╔════╝██╔══██╗
██║  ██║██╔██╗ ██║███████╗       ██║   ██████╔╝███████║██╔██╗ ██║███████╗█████╗  █████╗  ██████╔╝
██║  ██║██║╚██╗██║╚════██║       ██║   ██╔══██╗██╔══██║██║╚██╗██║╚════██║██╔══╝  ██╔══╝  ██╔══██╗
██████╔╝██║ ╚████║███████║       ██║   ██║  ██║██║  ██║██║ ╚████║███████║██║     ███████╗██║  ██║
╚═════╝ ╚═╝  ╚═══╝╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                                                                 
""")

def nslookup_axfr(domain, ns):
    # Execute o comando nslookup para obter as informações de zona
    output = subprocess.run(['nslookup', '-type=any', domain, ns], capture_output=True, text=True)
    return output.stdout

domain = input(f"\nDigite o nome do website: ")

# Obtém os servidores de nomes usando nslookup
output = subprocess.run(['nslookup', '-type=ns', domain], capture_output=True, text=True)
ns_lines = output.stdout.splitlines()
ns_list = [line.split()[-1] for line in ns_lines if 'nameserver' in line or line.strip().startswith(domain)]

# Exibe os servidores de nomes encontrados
print("\nServidores de nomes\n")
for ns in ns_list:
    print(ns)

print("")

# Executa a transferência de zona para cada servidor de nomes
print(f"\nResultado da transferência de zona para: {domain}")
print("\n")
for ns in ns_list:
    print("\n")
    print(f"Transferência de zona de:  {domain}   usando: {ns}")
    print("\n")
    print(nslookup_axfr(domain, ns))

input("\n\n🎯 Pressione Enter para sair 🎯\n")    
    
