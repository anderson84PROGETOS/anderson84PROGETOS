import dns.resolver
import os
import sys
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

 ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗███████╗██████╗      ██████╗███╗   ██╗ █████╗ ███╗   ███╗███████╗    
██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗    ██╔════╝████╗  ██║██╔══██╗████╗ ████║██╔════╝    
██║     ███████║█████╗  ██║     █████╔╝ █████╗  ██████╔╝    ██║     ██╔██╗ ██║███████║██╔████╔██║█████╗      
██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ ██╔══╝  ██╔══██╗    ██║     ██║╚██╗██║██╔══██║██║╚██╔╝██║██╔══╝      
╚██████╗██║  ██║███████╗╚██████╗██║  ██╗███████╗██║  ██║    ╚██████╗██║ ╚████║██║  ██║██║ ╚═╝ ██║███████╗    
 ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝     ╚═════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝                                                                                                               
""")

# Função para listar arquivos .txt na pasta onde o script está
def listar_txt_na_pasta():
    txt_files = [f for f in os.listdir(os.path.dirname(__file__)) if f.endswith('.txt')]

    if not txt_files:
        print("\nNenhum arquivo .txt encontrado na pasta.")
        sys.exit()

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Escolha um arquivo de wordlist\n")
    for idx, file in enumerate(txt_files, start=1):
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{idx} = {file}")

    while True:
        try:
            choice = int(input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o número do arquivo wordlist: "))
            print("\n")
            if 1 <= choice <= len(txt_files):
                return os.path.join(os.path.dirname(__file__), txt_files[choice - 1])
            else:
                print("Opção inválida. Tente novamente.")
        except ValueError:
            print("Por favor, insira um número válido.")

# Função para ler o conteúdo do arquivo wordlist
def ler_wordlist(caminho_arquivo):
    try:
        with open(caminho_arquivo, 'r') as file:
            subdominios = [line.strip() for line in file.readlines() if line.strip()]
        return subdominios
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return []

# Função para obter o CNAME de um domínio
def obter_cname(site, cname_set, resultados):
    try:
        respostas = dns.resolver.resolve(site, 'CNAME', lifetime=10)        
        for resposta in respostas:
            cname = resposta.to_text()
            if cname not in cname_set:  # Evita duplicação de CNAME
                cname_set.add(cname)  # Adiciona o CNAME à lista
                # Tenta obter o IP do CNAME
                try:
                    ip_respostas = dns.resolver.resolve(cname, 'A', lifetime=10)
                    for ip_resposta in ip_respostas:
                        ip = ip_resposta.to_text()
                        if ip:
                            pass
                except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                    pass
                except dns.exception.DNSException as e:
                    print(f"Erro ao consultar IP para {cname}: {e}")
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        pass
    except dns.exception.DNSException as e:
        print(f"Erro ao consultar CNAME para {site}: {e}")

# Função para obter IP do CNAME
def obter_ip_do_cname(cname, resultados):
    try:
        respostas = dns.resolver.resolve(cname, 'A', lifetime=10)
        for resposta in respostas:
            ip = resposta.to_text()
            if ip:
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"CNAME => " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{cname:<74} IP: {ip}")
                resultados.append(f"\nCNAME: {cname:<67} -> IP: {ip}")
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        pass
    except dns.exception.DNSException as e:
        print(f"Erro ao consultar IP para {cname}: {e}")

# Função para encontrar subdomínios
def encontrar_subdominios(site, subdominios_comuns, cname_set, resultados):
    for sub in subdominios_comuns:
        subdominio = f"{sub}.{site}"
        try:
            respostas = dns.resolver.resolve(subdominio, 'A', lifetime=10)
            for resposta in respostas:
                # Verificando se o subdomínio é um CNAME antes de exibi-lo
                if subdominio not in cname_set:
                    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Subdominio Encontrado: " + Fore.LIGHTCYAN_EX + Style.BRIGHT + f"{subdominio:<60}" + Fore.LIGHTGREEN_EX + Style.BRIGHT + f" IP: {resposta.to_text()}")
                    resultados.append(f"Subdominio: {subdominio:<62} -> IP: {resposta.to_text()}")
                    obter_cname(subdominio, cname_set, resultados)
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass
        except dns.exception.DNSException as e:
            print(f"Erro ao consultar subdomínio {subdominio}: {e}")

# Função para salvar resultados em um arquivo .txt
def perguntar_salvar_resultados(resultados):
    # Perguntar se o usuário deseja salvar os resultados
    salvar = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDeseja salvar os resultados? (s/n): ").lower()

    if salvar == 's':
        nome_arquivo = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o nome do arquivo para salvar os resultados (exemplo: arquivo.txt): ")
        
        try:
            with open(nome_arquivo, 'w') as file:
                file.write("======= CNAME Encontrados =====\n")
                for resultado in resultados:
                    if 'CNAME' in resultado:
                        file.write(resultado + "\n")
                
                file.write("\n\n======== Subdomínios Encontrados =========\n\n")
                for resultado in resultados:
                    if 'Subdominio' in resultado:
                        file.write(resultado + "\n")
            
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nResultados salvos em: {nome_arquivo}")
        except Exception as e:
            print(f"Erro ao salvar os resultados: {e}")
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "Resultados não salvos.")

if __name__ == "__main__":
    caminho_arquivo = listar_txt_na_pasta()
    subdominios_comuns = ler_wordlist(caminho_arquivo)
    
    if not subdominios_comuns:
        print("A lista de subdomínios está vazia ou não foi carregada corretamente.")
        sys.exit()

    site = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do website: ")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nEscaneando Subdominio\n")

    cname_set = set()
    resultados = []
    subdominios_encontrados = []

    obter_cname(site, cname_set, resultados)
    encontrar_subdominios(site, subdominios_comuns, cname_set, resultados)

    if cname_set:
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nCNAME Encontrados\n")
        for cname in cname_set:
            obter_ip_do_cname(cname, resultados)
    else:
        print("\nNenhum CNAME encontrado.")    

    # No final do script, substitua a chamada original
    perguntar_salvar_resultados(resultados)

# Finalizar o programa
input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== SCAN FINALIZADO. PRESSIONE ENTER PARA SAIR ==========\n\n")
