import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from socket import socket, AF_INET, SOCK_STREAM
import re
import subprocess

print("""

██╗    ██╗███████╗██████╗ ███████╗██╗████████╗███████╗    ████████╗ ██████╗  ██████╗ ██╗     ███████╗
██║    ██║██╔════╝██╔══██╗██╔════╝██║╚══██╔══╝██╔════╝    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔════╝
██║ █╗ ██║█████╗  ██████╔╝███████╗██║   ██║   █████╗         ██║   ██║   ██║██║   ██║██║     ███████╗
██║███╗██║██╔══╝  ██╔══██╗╚════██║██║   ██║   ██╔══╝         ██║   ██║   ██║██║   ██║██║     ╚════██║
╚███╔███╔╝███████╗██████╔╝███████║██║   ██║   ███████╗       ██║   ╚██████╔╝╚██████╔╝███████╗███████║
 ╚══╝╚══╝ ╚══════╝╚═════╝ ╚══════╝╚═╝   ╚═╝   ╚══════╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚══════╝
                                                                                                     
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

def fetch_and_process(url, headers, user_agent_name):
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url)
    
    print(f"\n\nStatus da resposta HTTP ({user_agent_name}): {response.status_code}")

    print(f"\n\n============= Cabeçalhos HTTP ({user_agent_name}) =============\n")
    for key, value in response.headers.items():
        print(f"{key}: {value}")
    
    if user_agent_name != "CURL":
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"\n\n============= Parágrafos ({user_agent_name}) =============\n")
        paragraphs = soup.find_all('p')
        for para in paragraphs:
            print(para.get_text())
        
        print(f"\n\n============= Links ({user_agent_name}) =============\n")
        links = soup.find_all('a')
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            if href:
                print(f"{text}: {href}")
        
        print(f"\n\n============= Títulos ({user_agent_name}) =============\n")
        titles = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for title in titles:
            print(title.get_text().strip())
        
        print(f"\n\n============= Imagens ({user_agent_name}) =============\n")
        images = soup.find_all('img')
        for img in images:
            src = img.get('src')
            alt = img.get('alt')
            if src:
                print(f"Fonte: {src}, Texto alternativo: {alt}")
        
        print(f"\n\n============= Listas ({user_agent_name}) =============\n")
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            items = lst.find_all('li')
            for item in items:
                print(item.get_text().strip())
        
        print(f"\n\n============= Tabelas ({user_agent_name}) =============\n")
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                col_texts = [col.get_text().strip() for col in cols]
                print('\t'.join(col_texts))
        
        print(f"\n\n============= Outros Textos ({user_agent_name}) =============\n")
        other_texts = soup.find_all(string=True)
        for text in other_texts:
            if text.parent.name not in ['script', 'style', 'head', 'title', 'meta', '[document]']:
                content = text.strip()
                if content:
                    print(content)

def requisicao_whois(servidor_whois, endereco_host, padrao):
    objeto_socket = socket(AF_INET, SOCK_STREAM)
    conexao = objeto_socket.connect_ex((servidor_whois, 43))
    if conexao == 0:
        if padrao:
            if servidor_whois == 'whois.verisign-grs.com':
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

def obter_whois_gov(endereco):
    servidores_whois_tdl = {'.gov': 'whois.nic.gov'}
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        requisicao_whois(servidor_whois_gov, endereco, False)
    else:
        print("Servidor WHOIS para domínios .gov não encontrado.")

def encontrar_emails(soup):
    email_regex = r"[\w\.-]+@[\w\.-]+"
    emails = []

    email_section = soup.find("div", class_="row-fluid registry-data")
    if email_section:
        email_text = email_section.find_all("div", class_="row")[1].find("div", class_="span9").get_text()
        email_matches = re.findall(email_regex, email_text)
        emails.extend(email_matches)

    whois_section = soup.find("pre", class_="df-raw")
    if whois_section:
        whois_text = whois_section.get_text()
        email_matches = re.findall(email_regex, whois_text)
        emails.extend(email_matches)

    return emails

def extrair_campo(whois_section, label):
    field = whois_section.find("div", string=re.compile(label))
    if field:
        value = field.find_next_sibling("div").get_text(strip=True)
        return value
    return ""

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

            emails = encontrar_emails(soup_whois)
            if emails:
                print("\nE-mails encontrados:")
                for email in emails:
                    print(email)

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
    servidores_whois_tdl = {'.br': 'whois.registro.br'}
    servidor_whois = servidores_whois_tdl['.br']
    requisicao_whois(servidor_whois, endereco, False)

def dns_transfer(site):
    print("\n\n\n\n========================================== Transferência de Zona DNS ==========================================\n")
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    output_list_dns = []
    for server in servers:
        output = subprocess.run(['nslookup', '-type=any', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    for output in output_list_dns:
        print(output)

def get_ipv4_addresses(site):
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    output_list_dns = []
    for server in servers:
        output = subprocess.run(['nslookup', '-type=A', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    ipv4_addresses = []
    for output in output_list_dns:
        ipv4_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
        ipv4_addresses.extend(ipv4_matches)

    ipv4_addresses = list(set(ipv4_addresses))
    return ipv4_addresses

def exibir_ipv4(site):
    ipv4_addresses = get_ipv4_addresses(site)
    if ipv4_addresses:
        print("\n\n\n\n========================================== Endereços IPv4 Encontrados ==========================================\n")
        for ipv4_address in ipv4_addresses:
            print(ipv4_address)
    else:
        print("\nNenhum Endereço IPv4 encontrado.")

def exibir_robots_txt(site, headers):
    robots_url = urljoin(site, '/robots.txt')
    response = requests.get(robots_url, headers=headers)
    print(f"\n\n============= Conteúdo do robots.txt =============\n")
    if response.status_code == 200:
        print(response.text)
    else:
        print(f"Não foi possível acessar o robots.txt (Status: {response.status_code})")

def web_scraper(url, headers):
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("Erro na URL")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', response.text))
    
    print(f"\nForam Encontrados ====>  {len(subdomains)}  Subdomínios\n")
    for subdomain in subdomains:
        print(subdomain)
    
    links = soup.find_all('a', href=True)
    urls = {link['href'] for link in links if link['href'].startswith('http://') or link['href'].startswith('https://') or link['href'].startswith('/')}
    complete_urls = {urljoin(url, link) if link.startswith('/') else link for link in urls}
    internal_urls = {link for link in complete_urls if urlparse(url).netloc in urlparse(link).netloc}
    
    print(f"\nForam Encontradas ====>  {len(internal_urls)}   URL internas\n")
    for internal_url in internal_urls:
        print(internal_url)

def main():
    while True:
        print("""
Escolha uma opção:

1 = Usando User Agent do Firefox
2 = Cabeçalhos HTTP (CURL)
3 = Consulta Whois
4 = Transferência de Zona DNS
5 = Exibir IPv4
6 = Exibir robots.txt
7 = Scraper Web

0 = Sair
""")
        choice = input("\nDigite o número da sua escolha: ")
        print("\n\n")
        
        if choice == '1':
            print("\n\n\n\n🎯=========================== Usando User Agent do Firefox ===========================🎯\n")
            fetch_and_process(url, headers_firefox, "Firefox")
        
        elif choice == '2':
            print("\n\n\n\n🎯=========================== Usando User Agent do CURL ===========================🎯\n")
            fetch_and_process(url, headers_curl, "CURL")
        
        elif choice == '3':
            print("\n\n\n\n========================================== Consulta Whois ==========================================\n")
            obter_whois_br(site)
            obter_whois(site)
            if re.search(r'\.gov$', site):
                obter_whois_gov(site)
        
        elif choice == '4':
            dns_transfer(site)
            
            
        elif choice == '5':
            exibir_ipv4(site)  # Exibir os endereços IPv4 encontrados     
        
        elif choice == '6':
            print("\n\n\n\n🎯=========================== Exibir robots.txt ===========================🎯\n")
            exibir_robots_txt(url, headers_firefox)
        
        elif choice == '7':
            print("\n\n\n\n🎯=========================== Scraper Web ===========================🎯\n")
            web_scraper(url, headers_firefox)

           

        elif choice == '0':
            break
        
        else:
            print("\nOpção inválida. Tente novamente.")

if __name__ == "__main__":
    main()

