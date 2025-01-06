import dns.resolver
import requests
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██████╗ ███████╗███████╗ ██████╗ ██╗   ██╗██╗███████╗ █████╗     ██████╗ ███╗   ██╗███████╗
██╔══██╗██╔════╝██╔════╝██╔═══██╗██║   ██║██║██╔════╝██╔══██╗    ██╔══██╗████╗  ██║██╔════╝
██████╔╝█████╗  ███████╗██║   ██║██║   ██║██║███████╗███████║    ██║  ██║██╔██╗ ██║███████╗
██╔═══╝ ██╔══╝  ╚════██║██║▄▄ ██║██║   ██║██║╚════██║██╔══██║    ██║  ██║██║╚██╗██║╚════██║
██║     ███████╗███████║╚██████╔╝╚██████╔╝██║███████║██║  ██║    ██████╔╝██║ ╚████║███████║
╚═╝     ╚══════╝╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚═╝╚══════╝╚═╝  ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                           
""")

def get_ip_details(ip):
    try:
        # Faz a solicitação GET para a API ip-api.com
        response = requests.get(f'http://ip-api.com/json/{ip}')
        data = response.json()
        if data['status'] == 'fail':
            return 'Detalhes do IP não disponíveis'
        return f"{ip}"
    except requests.RequestException:
        return "Detalhes do IP não disponíveis"

def get_dns_records(domain):
    print(Fore.LIGHTMAGENTA_EX + f"\nConsultando registros DNS para: {domain}\n")

    # Função para resolver o IP de um domínio
    def resolve_ip(domain_name):
        try:
            answers = dns.resolver.resolve(domain_name, 'A')
            return answers[0].to_text()
        except Exception as e:
            return None

    # Consultar A primeiro
    try:
        answers = dns.resolver.resolve(domain, 'A')
        print(Fore.LIGHTGREEN_EX + "Registros [A]")
        print(Fore.LIGHTWHITE_EX + "=============")
        for answer in answers:
            ip = resolve_ip(answer.to_text())
            ip_details = get_ip_details(ip)
            print(Fore.LIGHTGREEN_EX + f"{answer} ")
        print()
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        print(f"O domínio {domain} não existe.")
    except dns.resolver.NoNameservers:
        print(f"Nenhum servidor de nomes pôde ser encontrado para {domain}.")
    except Exception as e:
        pass

    # Consultar NS
    try:
        answers = dns.resolver.resolve(domain, 'NS')
        print(Fore.LIGHTMAGENTA_EX + "Registros [NS]")
        print(Fore.LIGHTWHITE_EX + "==============")
        for answer in answers:
            answer_str = str(answer)  # Converte o objeto NS para string
            ip = resolve_ip(answer_str)  # Usa a string do servidor para resolver o IP        
            print(Fore.LIGHTMAGENTA_EX + f"{answer_str:<25} IP: {ip:<20}")  # Formatação com a string
        print()
    except Exception as e:
        pass  # O bloco de exceções foi removido conforme solicitado

    # Consultar PTR
    try:
        answers = dns.resolver.resolve(domain, 'PTR')
        print(Fore.LIGHTYELLOW_EX + "Registros [PTR]")
        print(Fore.LIGHTWHITE_EX + "===============")
        for answer in answers:
            ip = resolve_ip(answer.to_text())
            ip_details = get_ip_details(ip) if ip else "IP não encontrado"
            print(Fore.LIGHTWHITE_EX + f"{answer} IP: {ip_details}")
        print()
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        print(f"O domínio {domain} não existe.")
    except dns.resolver.NoNameservers:
        print(f"Nenhum servidor de nomes pôde ser encontrado para {domain}.")
    except Exception as e:
        pass
    
    # Consultar MX
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        print(Fore.LIGHTCYAN_EX + "Registros [MX]")
        print(Fore.LIGHTWHITE_EX + "==============")        
        if answers:
            for answer in answers:
                mx_record = answer.exchange.to_text()  # Converte o registro MX para texto                
                ip = resolve_ip(mx_record)  # Resolve IP do servidor MX
                if ip:
                    ip_details = get_ip_details(ip)  # Obtém detalhes do IP
                    print(Fore.LIGHTCYAN_EX + f"{mx_record:<30} IP: {ip_details:<20}")  # Exibe o registro MX e o IP na mesma linha
    except Exception:
        pass  # Suprime qualquer mensagem de erro

    # Consultar SOA
    try:
        answers = dns.resolver.resolve(domain, 'SOA')
        print(Fore.LIGHTRED_EX + "\nRegistros [SOA]")
        print(Fore.LIGHTWHITE_EX + "===============")
        for answer in answers:
            ip = resolve_ip(answer.mname.to_text())
            ip_details = get_ip_details(ip) if ip else "IP não encontrado"
            print(Fore.LIGHTRED_EX + f"{answer} IP: {ip_details}")
        print()
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        print(f"O domínio {domain} não existe.")
    except dns.resolver.NoNameservers:
        print(f"Nenhum servidor de nomes pôde ser encontrado para {domain}.")
    except Exception as e:
        pass

    # Consultar DS
    try:
        answers = dns.resolver.resolve(domain, 'DS')
        print(Fore.LIGHTYELLOW_EX + "Registros [DS]")
        print(Fore.LIGHTWHITE_EX + "==============")
        for answer in answers:
            ip = resolve_ip(answer.to_text())
            ip_details = get_ip_details(ip)
            print(Fore.LIGHTWHITE_EX + f"{answer}")
        print()
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        print(f"O domínio {domain} não existe.")
    except dns.resolver.NoNameservers:
        print(f"Nenhum servidor de nomes pôde ser encontrado para {domain}.")
    except Exception as e:
        pass
    
    # Consultar registros SRV para serviços comuns
    srv_found = False  # Flag para verificar se encontrou registros SRV
    srv_services = ['_sip._tcp', '_sip._udp', '_sips._tcp', '_h323cs._tcp', '_h323ls._udp', '_sip._tls']

    for service in srv_services:
        srv_domain = f"{service}.{domain}"
        try:
            srv_records = dns.resolver.resolve(srv_domain, 'SRV')
            if srv_records:
                if not srv_found:
                    print(Fore.LIGHTWHITE_EX + f"\nService Records [SRV]")
                    print(Fore.LIGHTGREEN_EX + "=====================")
                    srv_found = True
                for srv in srv_records:
                    try:
                        srv_target_str = str(srv.target)  # Convertendo srv.target para string
                        # Resolver IP do destino (srv.target)
                        srv_ip = dns.resolver.resolve(srv_target_str, 'A')[0]
                        # Exibir o registro SRV com alinhamento
                        print(Fore.LIGHTWHITE_EX + f"[SRV]  {srv_domain:<30} {srv_target_str:<30} IP: {srv_ip} Port: {srv.port}")
                    except:
                        pass  # Ignorar exceções ao resolver o IP
        except:
            pass  # Ignorar exceções ao consultar o SRV

    if not srv_found:
        pass  # Não exibe mensagem de erro se não encontrar registros SRV

    # Consultar tentativa de transferência de zona (zone transfer)
    print("")  # Linha de separação
    ns_servers = []
    try:
        answers = dns.resolver.resolve(domain, 'NS')
        for rdata in answers:
            ns_domain = str(rdata.target).strip('.')
            ns_servers.append(ns_domain)
    except:
        pass  # Ignorar exceções ao consultar os servidores de nome (NS) 

    # Consultar registros NSEC3
    try:
        answers = dns.resolver.resolve(domain, 'NSEC3')
        print(Fore.LIGHTYELLOW_EX + "Registros [NSEC3]")
        print(Fore.LIGHTWHITE_EX + "=================")
        for answer in answers:
            ip = resolve_ip(answer.to_text())
            ip_details = get_ip_details(ip) if ip else "IP não encontrado"
            print(Fore.LIGHTWHITE_EX + f"{answer} IP: {ip_details}")
        print()
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        print(f"O domínio {domain} não existe.")
    except dns.resolver.NoNameservers:
        print(f"Nenhum servidor de nomes pôde ser encontrado para {domain}.")
    except Exception as e:
        pass

    # Consultar HINFO
    try:
        answers = dns.resolver.resolve(domain, 'HINFO')
        print(Fore.LIGHTGREEN_EX + "\nRegistros [HINFO]")
        print(Fore.LIGHTWHITE_EX + "=================")
        for answer in answers:
            ip = resolve_ip(answer.to_text())
            ip_details = get_ip_details(ip) 
            print(Fore.LIGHTGREEN_EX + f"{answer}")
        print()
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        print(f"O domínio {domain} não existe.")
    except dns.resolver.NoNameservers:
        print(f"Nenhum servidor de nomes pôde ser encontrado para {domain}.")
    except Exception as e:
        pass

    # Consultar CNAME
    try:
        answers = dns.resolver.resolve(domain, 'CNAME')
        print(Fore.LIGHTYELLOW_EX + "Registros [CNAME]")
        print(Fore.LIGHTWHITE_EX + "=================")
        for answer in answers:
            ip = resolve_ip(answer.to_text())
            ip_details = get_ip_details(ip) if ip else "IP não encontrado"
            print(Fore.LIGHTWHITE_EX + f"{answer} IP: {ip_details}")
        print()
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        print(f"O domínio {domain} não existe.")
    except dns.resolver.NoNameservers:
        print(f"Nenhum servidor de nomes pôde ser encontrado para {domain}.")
    except Exception as e:
        pass

    # Consultar ANY
    try:
        answers = dns.resolver.resolve(domain, 'ANY')
        print(Fore.LIGHTYELLOW_EX + "Registros [ANY]")
        print(Fore.LIGHTWHITE_EX + "================")
        for answer in answers:
            ip = resolve_ip(answer.to_text())
            ip_details = get_ip_details(ip) if ip else "IP não encontrado"
            print(Fore.LIGHTWHITE_EX + f"{answer} IP: {ip_details}")
        print()
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        print(f"O domínio {domain} não existe.")
    except dns.resolver.NoNameservers:
        print(f"Nenhum servidor de nomes pôde ser encontrado para {domain}.")
    except Exception as e:
        pass    
    # Consultar TXT por último
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        print(Fore.LIGHTYELLOW_EX + "\nRegistros [TXT]")
        print(Fore.LIGHTWHITE_EX + "===============")        
        
        if not answers:
            print("Nenhum registro TXT encontrado.")  # Caso não haja registros        
        
        for answer in answers:
            answer_str = answer.to_text()  # Extrai o conteúdo do registro TXT para string            
            
            # Depuração: Verificar se o domínio está correto            
            ip = resolve_ip(domain)            
            
            # Verificação para garantir que o IP está sendo resolvido
            if ip:                
                ip_details = get_ip_details(ip)
                print(Fore.LIGHTYELLOW_EX + f"[TXT] {answer_str:<50} IP: {ip_details:<30}")  # Exibe o registro TXT e o IP na mesma linha
        print()
    except Exception:
        pass  # Removido o print de erro

if __name__ == "__main__":
    domain = input(Fore.LIGHTGREEN_EX + "\nDigite o domínio para consulta DNS: ").strip()
    get_dns_records(domain)

input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
