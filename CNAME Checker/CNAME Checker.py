import dns.resolver
import os
import sys
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
 ██████╗███╗   ██╗ █████╗ ███╗   ███╗███████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗███████╗██████╗ 
██╔════╝████╗  ██║██╔══██╗████╗ ████║██╔════╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██║     ██╔██╗ ██║███████║██╔████╔██║█████╗      ██║     ███████║█████╗  ██║     █████╔╝ █████╗  ██████╔╝
██║     ██║╚██╗██║██╔══██║██║╚██╔╝██║██╔══╝      ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ ██╔══╝  ██╔══██╗
╚██████╗██║ ╚████║██║  ██║██║ ╚═╝ ██║███████╗    ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗███████╗██║  ██║
 ╚═════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝     ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
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

def obter_cname(site, cname_list, resultados):
    try:
        # Definindo um tempo limite de 10 segundos
        respostas = dns.resolver.resolve(site, 'CNAME', lifetime=10)  
        for resposta in respostas:
            cname_list.append(resposta.to_text())  # Adiciona o CNAME à lista
            resultados.append(f"\nCNAME: {resposta.to_text()}\n")
    except dns.resolver.NoAnswer:
        pass  # Caso não haja CNAME, não faz nada
    except dns.resolver.NXDOMAIN:
        pass  # Caso o domínio não exista, não faz nada
    except dns.exception.DNSException as e:
        print(f"Erro ao consultar CNAME para {site}: {e}")

def obter_ip_do_cname(cname, resultados):
    try:
        # Tentando obter o IP associado ao CNAME
        respostas = dns.resolver.resolve(cname, 'A', lifetime=10)
        for resposta in respostas:
            print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nCNAME => " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{cname:<74} IP: {resposta.to_text()}")
            resultados.append(f"\nCNAME: {cname:<60} -> IP: {resposta.to_text()}")
    except dns.resolver.NoAnswer:
        pass  # Caso não haja resposta de A record, não faz nada
    except dns.resolver.NXDOMAIN:
        pass  # Caso o CNAME não tenha um IP associado
    except dns.exception.DNSException as e:
        print(f"Erro ao consultar IP para {cname}: {e}")

def encontrar_subdominios(site, subdominios_comuns, cname_list, resultados):
    for sub in subdominios_comuns:
        subdominio = f"{sub}.{site}"
        try:
            # Tentando consultar o A record (registro de endereço IP) para cada subdomínio
            respostas = dns.resolver.resolve(subdominio, 'A', lifetime=10)
            for resposta in respostas:
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Subdominio Encontrado: " + Fore.LIGHTCYAN_EX + Style.BRIGHT + f"{subdominio:<60}" + Fore.LIGHTGREEN_EX + Style.BRIGHT + f" IP: {resposta.to_text()}")
                resultados.append(f"Subdominio: {subdominio:<60} -> IP: {resposta.to_text()}")
                
                # Procurando o CNAME para cada subdomínio encontrado
                obter_cname(subdominio, cname_list, resultados)

        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            # Subdomínio não encontrado, nada a fazer
            pass
        except dns.exception.DNSException as e:
            print(f"Erro ao consultar subdomínio {subdominio}: {e}")

# Função para salvar os resultados em arquivos separados com separadores
def salvar_resultados(nome_arquivo, subdominios, cname_list, resultados):
    try:
        with open(nome_arquivo, 'w') as file:
            # Salvar subdomínios e IPs encontrados           
            for linha in subdominios:
                file.write(linha + '\n')           
            
            # Salvar CNAMEs encontrados
            file.write("CNAME Encontrados\n")
            for cname in cname_list:
                file.write(f"\nCNAME: {cname}\n")

            # Adicionar separador
            file.write("\n====================\n")

            # Salvar os resultados gerais
            file.write("\nResultados Finais\n\n")
            for linha in resultados:
                file.write(linha + '\n')

        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nResultados salvos em: {nome_arquivo}")
    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")

# No código principal (onde a função é chamada), substitua a chamada anterior para `salvar_resultados`
# por essa nova versão, passando as listas de subdomínios e cname_list separadas:

if __name__ == "__main__":
    # Listar e selecionar o arquivo .txt
    caminho_arquivo = listar_txt_na_pasta()

    # Ler subdomínios do arquivo
    subdominios_comuns = ler_wordlist(caminho_arquivo)
    
    if not subdominios_comuns:
        print("A lista de subdomínios está vazia ou não foi carregada corretamente.")
        sys.exit()

    # Solicitar o nome do site
    site = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do website: ")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nEscaneando Subdominio\n")
    # Lista para armazenar os CNAMEs encontrados
    cname_list = []
    resultados = []
    subdominios_encontrados = []

    # Obter CNAME do domínio principal
    obter_cname(site, cname_list, resultados)
    
    # Encontrar subdomínios e seus CNAMEs
    encontrar_subdominios(site, subdominios_comuns, cname_list, resultados)

    # Exibir CNAMEs encontrados após a varredura
    if cname_list:
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nCNAME Encontrados\n")
        for cname in cname_list:
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + cname)
            # Exibir o IP associado ao CNAME
            obter_ip_do_cname(cname, resultados)
    else:
        print("\nNenhum CNAME encontrado.")
    
    # Perguntar se deseja salvar as informações
    salvar = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDeseja salvar todas as informações? (s/n): ").strip().lower()
    if salvar == 's':
        nome_arquivo = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nDigite o nome do arquivo (exemplo: cname.txt): ")
        salvar_resultados(nome_arquivo, subdominios_encontrados, cname_list, resultados)

# Finalizar o programa
input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== SCAN FINALIZADO. PRESSIONE ENTER PARA SAIR ==========\n\n")
