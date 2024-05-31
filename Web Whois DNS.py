import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from socket import socket, AF_INET, SOCK_STREAM
import re
import subprocess

print("""

██╗    ██╗███████╗██████╗     ██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ██████╗ ███╗   ██╗███████╗
██║    ██║██╔════╝██╔══██╗    ██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ██╔══██╗████╗  ██║██╔════╝
██║ █╗ ██║█████╗  ██████╔╝    ██║ █╗ ██║███████║██║   ██║██║███████╗    ██║  ██║██╔██╗ ██║███████╗
██║███╗██║██╔══╝  ██╔══██╗    ██║███╗██║██╔══██║██║   ██║██║╚════██║    ██║  ██║██║╚██╗██║╚════██║
╚███╔███╔╝███████╗██████╔╝    ╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ██████╔╝██║ ╚████║███████║
 ╚══╝╚══╝ ╚══════╝╚═════╝      ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚═════╝ ╚═╝  ╚═══╝╚══════╝
                                                                                                                                                                       
""")

# Solicitar a URL do usuário
url = input("\nDigite a URL do website: ")
site = url.replace('http://', '').replace('https://', '').split('/')[0]

# User agent para simular requisições feitas pelo navegador Firefox
user_agent_firefox = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'

# User agent para simular requisições feitas pelo cURL
user_agent_curl = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'

# Cabeçalhos padrão para Firefox
headers_firefox = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': url,
    'User-Agent': user_agent_firefox
}

# Cabeçalhos padrão para cURL
headers_curl = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': url,
    'User-Agent': user_agent_curl
}

# Função para fazer a requisição e processar o conteúdo
def fetch_and_process(url, headers, user_agent_name):
    # Criar uma sessão para manter cookies e outras configurações
    session = requests.Session()
    session.headers.update(headers)
    
    # Fazer a requisição HTTP para obter o conteúdo da página com os cabeçalhos
    response = session.get(url)
    
    # Verificar o código de status e continuar mesmo que não seja 200
    print(f"\n\nStatus da resposta HTTP ({user_agent_name}): {response.status_code}")

    # Extrair e imprimir os cabeçalhos HTTP da resposta
    print(f"\n\n============= Cabeçalhos HTTP ({user_agent_name}) =============\n")
    for key, value in response.headers.items():
        print(f"{key}: {value}")
    
    # Se o user agent não for o cURL, continuar com a extração de conteúdo
    if user_agent_name != "CURL":
        # Analisar o conteúdo HTML da página
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extrair e imprimir parágrafos
        print(f"\n\n============= Parágrafos ({user_agent_name}) =============\n")
        paragraphs = soup.find_all('p')
        for para in paragraphs:
            print(para.get_text())
        
        # Extrair e imprimir links
        print(f"\n\n============= Links ({user_agent_name}) =============\n")
        links = soup.find_all('a')
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            if href:
                print(f"{text}: {href}")
        
        # Extrair e imprimir títulos
        print(f"\n\n============= Títulos ({user_agent_name}) =============\n")
        titles = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for title in titles:
            print(title.get_text().strip())
        
        # Extrair e imprimir imagens
        print(f"\n\n============= Imagens ({user_agent_name}) =============\n")
        images = soup.find_all('img')
        for img in images:
            src = img.get('src')
            alt = img.get('alt')
            if src:
                print(f"Fonte: {src}, Texto alternativo: {alt}")
        
        # Extrair e imprimir listas
        print(f"\n\n============= Listas ({user_agent_name}) =============\n")
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            items = lst.find_all('li')
            for item in items:
                print(item.get_text().strip())
        
        # Extrair e imprimir tabelas
        print(f"\n\n============= Tabelas ({user_agent_name}) =============\n")
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                col_texts = [col.get_text().strip() for col in cols]
                print('\t'.join(col_texts))
        
        # Extrair e imprimir todos os outros textos
        print(f"\n\n============= Outros Textos ({user_agent_name}) =============\n")
        other_texts = soup.find_all(string=True)
        for text in other_texts:
            if text.parent.name not in ['script', 'style', 'head', 'title', 'meta', '[document]']:
                content = text.strip()
                if content:
                    print(content)
        
        # Obter e imprimir o conteúdo do robots.txt
        robots_url = urljoin(url, '/robots.txt')
        robots_response = session.get(robots_url)
        print(f"\n\n============= Robots.txt ({user_agent_name}) =============\n")
        if robots_response.status_code == 200:
            print(robots_response.text)
        else:
            print(f"Não foi possível acessar o robots.txt ({user_agent_name}) (Status: {robots_response.status_code})")

# Usar o user agent do Firefox
print("\n\n\n\n🎯=========================== Usando User Agent do Firefox ===========================🎯\n")
fetch_and_process(url, headers_firefox, "Firefox")

# Usar o user agent do cURL
print("\n\n\n\n🎯=========================== Usando User Agent do CURL ===========================🎯\n")
fetch_and_process(url, headers_curl, "CURL")

# Função para requisitar informações WHOIS
def requisicao_whois(servidor_whois, endereco_host, padrao):
    objeto_socket = socket(AF_INET, SOCK_STREAM)
    conexao = objeto_socket.connect_ex((servidor_whois, 43))
    if conexao == 0:
        if padrao:
            if servidor_whois == 'whois.verisign-grs.com':  # For .com and .net domains
                objeto_socket.send(f'domain {endereco_host}\r\n'.encode())
            else:
                objeto_socket.send(f'n + {endereco_host}\r\n'.encode())
        else:
            objeto_socket.send(f'{endereco_host}\r\n'.encode())
        
        while True:
            dados = objeto_socket.recv(65500)
            if not dados:
                break
            print(dados.decode('latin-1'))
    objeto_socket.close()

# Função para obter WHOIS para domínios .gov
def obter_whois_gov(endereco):
    servidores_whois_tdl = {
        '.gov': 'whois.nic.gov'
    }
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        requisicao_whois(servidor_whois_gov, endereco, False)
    else:
        print("Servidor WHOIS para domínios .gov não encontrado.")

# Função para encontrar e-mails em um BeautifulSoup object
def encontrar_emails(soup):
    email_regex = r"[\w\.-]+@[\w\.-]+"
    emails = []

    # Procura e retorna os e-mails na página principal do WHOIS
    email_section = soup.find("div", class_="row-fluid registry-data")
    if email_section:
        email_text = email_section.find_all("div", class_="row")[1].find("div", class_="span9").get_text()
        email_matches = re.findall(email_regex, email_text)
        emails.extend(email_matches)

    # Procura e retorna os e-mails no resultado completo do WHOIS
    whois_section = soup.find("pre", class_="df-raw")
    if whois_section:
        whois_text = whois_section.get_text()
        email_matches = re.findall(email_regex, whois_text)
        emails.extend(email_matches)

    return emails

# Função para extrair campos específicos do WHOIS
def extrair_campo(whois_section, label):
    field = whois_section.find("div", string=re.compile(label))
    if field:
        value = field.find_next_sibling("div").get_text(strip=True)
        return value
    return ""

# Função para obter informações WHOIS
def obter_whois(endereco):
    url_whois = f"https://www.whois.com/whois/{endereco}"
    url_registro_br = f"https://registro.br/cgi-bin/whois/?qr={endereco}"

    response_whois = requests.get(url_whois)
    response_registro_br = requests.get(url_registro_br)

    if response_whois.status_code == 200:
        soup_whois = BeautifulSoup(response_whois.text, "html.parser")
        whois_section = soup_whois.find("pre", class_="df-raw")
        if whois_section:
            whois_text = whois_section.get_text()
            print(whois_text)

            # Extract and display additional information
            emails = encontrar_emails(soup_whois)
            if emails:
                print("\nE-mails encontrados:")
                for email in emails:
                    print(email)

            # Extract more fields if needed
            name = extrair_campo(whois_section, "Registrant Name:")
            registration_date = extrair_campo(whois_section, "Creation Date:")
            expiration_date = extrair_campo(whois_section, "Registrar Registration Expiration Date:")

            if name:
                print("Nome do Titular:", name)
            if registration_date:
                print("Data de Registro:", registration_date)
            if expiration_date:
                print("Data de Expiração:", expiration_date)

    if response_registro_br.status_code == 200:
        soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
        div_result = soup_registro_br.find("div", class_="result")
        if div_result:
            result_text = div_result.get_text()
            print(result_text)

def obter_whois_br(endereco):
    servidores_whois_tdl = {
        '.br': 'whois.registro.br'
    }
    servidor_whois = servidores_whois_tdl['.br']
    requisicao_whois(servidor_whois, endereco, False)

# Função principal para executar as operações
def main():
    endereco = url.replace('http://', '').replace('https://', '').split('/')[0]
    
    print("\n\n\n\n========================================== Consulta Whois ==========================================\n")
    obter_whois_br(endereco)
    obter_whois(endereco)
    if re.search(r'\.gov$', endereco):
        obter_whois_gov(endereco)

# Função para executar a transferência de zona DNS
def dns_transfer(site):
    print("\n\n\n\n========================================== Transferência de Zona DNS ==========================================\n")
    # Executa o comando 'nslookup' e captura a saída
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)

    # Divide a saída em linhas e extrai os servidores DNS
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    # Lista para armazenar a saída de cada consulta do nslookup
    output_list_dns = []

    # Itera sobre cada servidor DNS e executa o comando 'nslookup -type=any'
    for server in servers:
        output = subprocess.run(['nslookup', '-type=any', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    # Imprime a saída do nslookup na tela
    for output in output_list_dns:
        print(output)

    # Lista para armazenar os endereços IPv4 encontrados
    ipv4_addresses = []

    # Extrai os endereços IPv4 de cada saída do nslookup
    for output in output_list_dns:
        ipv4_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
        ipv4_addresses.extend(ipv4_matches)

    # Remove duplicatas dos endereços IPv4
    ipv4_addresses = list(set(ipv4_addresses))

    # Imprime os endereços IPv4 na tela
    print("\n↓ Endereços IPv4 encontrados ↓\n")
    for ipv4_address in ipv4_addresses:
        print(ipv4_address) 

    # Cabeçalhos com os agentes do usuário
    headers = [
        'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0'
    ]

    # Lista para armazenar a saída dos cabeçalhos HTTP
    output_list_headers = []

    # Fazendo solicitações HTTP com os agentes do usuário e armazenando os cabeçalhos
    for agent in headers:
        response = requests.get("http://" + site, headers={'User-Agent': agent})
        output_list_headers.append(response.headers)

    # Imprime os cabeçalhos HTTP na tela
    for headers in output_list_headers:
        print("\n↓ Cabeçalhos HTTP ↓\n")
        for header, value in headers.items():
            print(f"{header}: {value}")
        print("\n")

# Executar a função principal
if __name__ == "__main__":
    main()
    dns_transfer(site)

input("\n\n🎯 Pressione Enter para sair 🎯\n")
