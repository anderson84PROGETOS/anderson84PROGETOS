import socket
import requests
from tqdm import tqdm  # Importar a biblioteca tqdm para a barra de progresso

print("""

███╗   ██╗███████╗████████╗██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗    ███████╗ ██████╗ █████╗ ███╗   ██╗
████╗  ██║██╔════╝╚══██╔══╝██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝    ██╔════╝██╔════╝██╔══██╗████╗  ██║
██╔██╗ ██║█████╗     ██║   ██║ █╗ ██║██║   ██║██████╔╝█████╔╝     ███████╗██║     ███████║██╔██╗ ██║
██║╚██╗██║██╔══╝     ██║   ██║███╗██║██║   ██║██╔══██╗██╔═██╗     ╚════██║██║     ██╔══██║██║╚██╗██║
██║ ╚████║███████╗   ██║   ╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗    ███████║╚██████╗██║  ██║██║ ╚████║
╚═╝  ╚═══╝╚══════╝   ╚═╝    ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝

""")

# Mapeamento de portas para nomes de serviços
service_ports = {
    21: 'FTP',
    22: 'SSH',
    23: 'Telnet',
    25: 'SMTP',
    53: 'DNS',
    67: 'DHCP (Servidor)',
    68: 'DHCP (Cliente)',
    80: 'HTTP',
    110: 'POP3',
    143: 'IMAP',
    161: 'SNMP',
    162: 'SNMP (Trap)',
    443: 'HTTPS',
    3306: 'MySQL',
    3389: 'RDP',
    5900: 'VNC',
    6379: 'Redis',
    8080: 'HTTP Alternativo',
    5432: 'PostgreSQL',
    27017: 'MongoDB',
    # Adicione mais portas e serviços conforme necessário
}

def parse_ports(ports_input):
    ports = set()  # Usar um conjunto para evitar duplicatas
    try:
        # Verificar se a entrada contém um intervalo
        if '-' in ports_input:
            start_port, end_port = map(int, ports_input.split('-'))
            # Adicionar todas as portas no intervalo
            if 1 <= start_port <= 65535 and 1 <= end_port <= 65535 and start_port <= end_port:
                ports.update(range(start_port, end_port + 1))
            else:
                print("Erro: O intervalo de portas deve estar entre 1 e 65535.")
        else:
            # Verificar se a entrada contém múltiplas portas
            for port in ports_input.split(','):
                port = int(port.strip())
                if 1 <= port <= 65535:
                    ports.add(port)
                else:
                    print(f"Erro: Porta {port} fora do intervalo permitido (1-65535).")
    except ValueError:
        print("Erro: Entrada inválida. Por favor, use o formato correto.")

    return ports

def check_ports(url, ports):
    # Criar uma lista para armazenar os resultados
    results = []
    
    # Utilizar tqdm para criar a barra de progresso
    print("")
    for port in tqdm(ports, desc="Verificando portas", unit="porta", ncols=82):
        try:
            # Criar um socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # Tempo limite de 2 segundos
            # Tentar conectar
            result = sock.connect_ex((url, port))
            if result == 0:
                service_name = service_ports.get(port, 'Desconhecida')
                results.append(f'\nPorta {port} ({service_name}) aberta em: {url}')
            sock.close()
        except Exception as e:
            results.append(f'Erro ao tentar conectar à porta {port} em {url}: {e}')

    return results

def make_request(url):
    # Cabeçalhos personalizados para evitar erros 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        # Fazer uma solicitação GET
        response = requests.get(f'http://{url}', headers=headers)
        return response.status_code, response.headers  # Retorna o código de status e os cabeçalhos
    except requests.RequestException as e:
        return None, f'Erro ao fazer a requisição: {e}'

def main():
    # Solicitar a entrada do usuário
    url = input('\nDigite o nome do website (ex: www.exemplo.com): ')
    ports_input = input("\nDigite a porta pra ser escaneada (1 a 65535, ex: 80 ou 21-80 ou 21,22,80): ")
    ports = parse_ports(ports_input)

    # Exibir os resultados
    results = check_ports(url, ports)
    print('\n\nResultados das portas abertas\n')
    if results:
        for result in results:
            print(result)
    else:
        print(f'Nenhuma porta aberta encontrada em: {url}')

    # Fazer uma requisição HTTP com os cabeçalhos personalizados
    status_code, headers = make_request(url)
    print(f'\n\nCódigo de status da requisição: {status_code}')
    if status_code == 200:
        print('\n\nCabeçalhos da resposta\n')
        for header, value in headers.items():
            print(f'{header}: {value}')  # Exibir cabeçalhos
    else:
        print('Conteúdo da resposta (sem cabeçalho)')
        print(headers)

if __name__ == '__main__':
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
