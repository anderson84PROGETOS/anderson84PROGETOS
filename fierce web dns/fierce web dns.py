import dns.resolver
import threading
import platform
import os
import sys  # Importação corrigida
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███████╗██╗███████╗██████╗  ██████╗███████╗    ██╗    ██╗███████╗██████╗     ██████╗ ███╗   ██╗███████╗
██╔════╝██║██╔════╝██╔══██╗██╔════╝██╔════╝    ██║    ██║██╔════╝██╔══██╗    ██╔══██╗████╗  ██║██╔════╝
█████╗  ██║█████╗  ██████╔╝██║     █████╗      ██║ █╗ ██║█████╗  ██████╔╝    ██║  ██║██╔██╗ ██║███████╗
██╔══╝  ██║██╔══╝  ██╔══██╗██║     ██╔══╝      ██║███╗██║██╔══╝  ██╔══██╗    ██║  ██║██║╚██╗██║╚════██║
██║     ██║███████╗██║  ██║╚██████╗███████╗    ╚███╔███╔╝███████╗██████╔╝    ██████╔╝██║ ╚████║███████║
╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝     ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                                                                                                        
""")

# Função para listar arquivos .txt na pasta onde o script está
def listar_txt_na_pasta():
    pasta_atual = os.getcwd()  # Obtém o diretório atual
    txt_files = [f for f in os.listdir(pasta_atual) if f.endswith('.txt')]

    if not txt_files:
        print("\nNenhum arquivo .txt encontrado na pasta.")
        sys.exit()

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Escolha um arquivo de wordlist\n")
    for idx, file in enumerate(txt_files, start=1):
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{idx} = {file}")

    while True:
        try:
            choice = int(input(Fore.LIGHTYELLOW_EX + Style.BRIGHT +  "\nDigite o número do arquivo wordlist: "))
            if 1 <= choice <= len(txt_files):
                return os.path.join(pasta_atual, txt_files[choice - 1])
            else:
                print("Opção inválida. Tente novamente.")
        except ValueError:
            print("\nPor favor, insira um número válido.")

# Leitura do arquivo de wordlist
wordlist_file = listar_txt_na_pasta()

# Abrindo o arquivo de wordlist
with open(wordlist_file, 'r', encoding='utf-8') as f:
    subdominios = f.read().splitlines()  # Usa os subdomínios da wordlist

# Exibe o número de palavras na wordlist
print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\n[+] A wordlist contém {len(subdominios)} Palavras\n")

# Detecta o sistema operacional
sistema = platform.system()

# Lista para armazenar resultados únicos
resultados = set()

# Função para verificar conectividade com DNS
def testar_dns():
    try:
        dns.resolver.resolve("google.com", "A")
        return True
    except dns.exception.DNSException:
        return False

# Função para resolver subdomínio
def resolver_subdominio(subdominio, dominio):
    alvo = f"{subdominio}.{dominio}"
    try:
        resposta = dns.resolver.resolve(alvo, 'A')
        for ip in resposta:
            resultados.add(f"{alvo:<30} ==>    {ip}")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout, dns.exception.DNSException):
        pass  # Ignora erros

# Função principal para iniciar a enumeração
def enumerar_subdominios(dominio):
    threads = []
    for sub in subdominios:
        thread = threading.Thread(target=resolver_subdominio, args=(sub, dominio))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()

    if resultados:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT +  "\n### Resultados Encontrados ###\n")
        for resultado in sorted(resultados):
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + resultado)
    else:
        print("\nNenhum subdomínio encontrado.")

# Função para salvar resultados em um arquivo
def salvar_resultados():
    resposta = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n\nDeseja salvar os resultados? (S/N): ").strip().lower()
    if resposta == 's':
        nome_arquivo = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar (ex: arquivo.txt): ").strip()
        try:
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                for resultado in sorted(resultados):
                    f.write(f"{resultado}\n")
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nResultados salvos em: {nome_arquivo}")
        except Exception as e:
            print(Fore.LIGHTRED_EX + Style.BRIGHT +  f"\nErro ao salvar o arquivo: {e}")
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT +  "\nResultados não salvos.")

# Entrada do usuário
if __name__ == "__main__":
    if not testar_dns():
        print("[!] Erro: Sem conexão com servidores DNS. Verifique sua internet.")
        exit()

    site = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDigite o nome ou a URL do website: ").strip()
    
    # Extrai o domínio da URL, se necessário
    if site.startswith("http"):
        site = site.split("//")[-1].split("/")[0]
    
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n[+] Sistema Detectado: {sistema}\n")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT +  "[+] Enumerando subdomínios...\n")
    enumerar_subdominios(site)
    
    # Pergunta se deseja salvar os resultados
    salvar_resultados()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
