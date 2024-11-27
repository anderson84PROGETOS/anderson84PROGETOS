import socket
import os
import requests

print("""

██████╗ ███╗   ██╗███████╗    ███████╗██╗   ██╗██████╗ 
██╔══██╗████╗  ██║██╔════╝    ██╔════╝██║   ██║██╔══██╗
██║  ██║██╔██╗ ██║███████╗    ███████╗██║   ██║██████╔╝
██║  ██║██║╚██╗██║╚════██║    ╚════██║██║   ██║██╔══██╗
██████╔╝██║ ╚████║███████║    ███████║╚██████╔╝██████╔╝
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚══════╝ ╚═════╝ ╚═════╝ 
                                                       
""")

# Função para verificar o protocolo (HTTPS ou HTTP)
def check_protocol(hostname):
    """Verifica se o hostname suporta HTTPS, senão retorna HTTP."""
    https_url = f"https://{hostname}"
    http_url = f"http://{hostname}"
    try:
        response = requests.get(https_url, timeout=2)  # Tenta acessar via HTTPS
        if response.status_code == 200:
            return https_url  # Retorna o URL com HTTPS se for bem-sucedido
    except requests.RequestException:
        pass  # Se falhar ao tentar HTTPS, tenta HTTP
    return http_url  # Retorna o URL com HTTP se HTTPS não for possível

# Função para tentar resolver os subdomínios
def resolver_subdominios(nome_do_website, arquivo_lista):
    found_count = 0  # Contador de subdomínios encontrados
    try:
        with open(arquivo_lista, 'r') as arquivo:
            for linha in arquivo:
                subdominio = linha.strip()  # Remove espaços e quebras de linha
                if subdominio:
                    dominio_completo = subdominio + '.' + nome_do_website
                    try:
                        ip = socket.gethostbyname(dominio_completo)
                        # Verifica se o subdomínio suporta HTTPS ou usa HTTP
                        protocolo_url = check_protocol(dominio_completo)
                        print(f"\n[√] HOST ENCONTRADO: {protocolo_url:<40}  IP: {ip} ")
                        found_count += 1  # Incrementa o contador quando encontra o subdomínio
                    except socket.gaierror:
                        continue  # Se não conseguir resolver, pula para o próximo
        # Exibir o total de URLs encontradas ao final
        print(f"\n\n\n[+] Total de URLs Encontradas: {found_count}")
        print(f"\n[+] Busca finalizada.\n")
    except FileNotFoundError:
        print(f"\n[!] O arquivo {arquivo_lista} não foi encontrado.")

# Solicitar o nome do website
nome_do_website = input("\nDigite o nome do website: ")

# Caminho para o arquivo common.txt na mesma pasta que o script
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "common.txt")

# Verificar se o arquivo common.txt existe na pasta do script
if os.path.exists(file_path):
    print(f"\n[+] Lendo caminhos do arquivo: {file_path}\n")
    resolver_subdominios(nome_do_website, file_path)
else:
    print(f"\n[!] Arquivo 'common.txt' não encontrado na pasta do script: {script_dir}")

# Mensagem para o usuário pressionar ENTER para sair
input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
