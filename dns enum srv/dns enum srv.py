import subprocess
import re
import socket
from colorama import init, Fore, Style

# Inicializa o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██████╗ ███╗   ██╗███████╗    ███████╗███╗   ██╗██╗   ██╗███╗   ███╗    ███████╗██████╗ ██╗   ██╗
██╔══██╗████╗  ██║██╔════╝    ██╔════╝████╗  ██║██║   ██║████╗ ████║    ██╔════╝██╔══██╗██║   ██║
██║  ██║██╔██╗ ██║███████╗    █████╗  ██╔██╗ ██║██║   ██║██╔████╔██║    ███████╗██████╔╝██║   ██║
██║  ██║██║╚██╗██║╚════██║    ██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║    ╚════██║██╔══██╗╚██╗ ██╔╝
██████╔╝██║ ╚████║███████║    ███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║    ███████║██║  ██║ ╚████╔╝ 
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝    ╚══════╝╚═╝  ╚═╝  ╚═══╝

""")

# Entrada do usuário
dominio = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do domínio (ex: exemplo.com.br): ").strip()

comando_str = (Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f'nmap -D RND:20 -sS --script dns-srv-enum '+ Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f'--script-args "dns-srv-enum.domain=\'{dominio}\'" {dominio}')

print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nComando que será executado\n")
print(comando_str)

# Comando Nmap com Decoy e SYN Scan
comando = [
    "nmap", "-D", "RND:20", "-sS",
    "--script", "dns-srv-enum",
    "--script-args", f"dns-srv-enum.domain='{dominio}'",
    dominio
]

# Executa o comando
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n[+] Executando Nmap para: {dominio}\n")
resultado = subprocess.run(comando, capture_output=True, text=True)
saida = resultado.stdout

# Regex para capturar porta/protocolo e hostname
padrao_host = re.findall(r"(\d+/(tcp|udp))\s+\d+\s+\d+\s+([\w\.-]+)", saida)

# Evita duplicatas
resultados_formatados = {}
for porta_proto, _, host in padrao_host:
    if (porta_proto, host) not in resultados_formatados:
        try:
            ip = socket.gethostbyname(host)
            resultados_formatados[(porta_proto, host)] = ip
        except socket.gaierror:
            resultados_formatados[(porta_proto, host)] = "[ERRO: IP não encontrado]"

# Exibe saída formatada
# Exibe saída formatada
print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n[+] Resultados com Port e IP\n")
saida_final = ""
for (porta_proto, host), ip in sorted(resultados_formatados.items()):
    linha = (
        Fore.LIGHTYELLOW_EX + Style.BRIGHT + "Port: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{porta_proto:<10}  {host:<30}  " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + "IP: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{ip}")
    print(linha)
    saida_final += f"Port: {porta_proto:<10}  {host:<30}  IP: {ip}\n"  # para salvar no .txt (sem cor)


# Pergunta se deseja salvar
salvar = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n\nDeseja salvar os resultados em um arquivo? (s/n): ").strip().lower()
if salvar == "s":
    nome_arquivo = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDigite o nome do arquivo (ex: exemplo: ").strip()
    if not nome_arquivo.endswith(".txt"):
        nome_arquivo += ".txt"
    try:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(f"Resultados para o domínio: {dominio}\n\n")
            f.write(saida_final)
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n[+] Resultados salvos em: {nome_arquivo}")
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\n[ERRO] Falha ao salvar o arquivo: {e}")

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
