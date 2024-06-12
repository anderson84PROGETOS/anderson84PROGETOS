import tkinter as tk
from tkinter import scrolledtext
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from socket import socket, AF_INET, SOCK_STREAM
import re
import subprocess

# Cabeçalhos padrão para Firefox
user_agent_firefox = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
headers_firefox = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'User-Agent': user_agent_firefox
}

# Cabeçalhos padrão para cURL
user_agent_curl = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
headers_curl = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'User-Agent': user_agent_curl
}

# Função para exibir resultados no ScrolledText
def display_result(text):
    result_text.insert(tk.END, text + "\n\n")
    result_text.see(tk.END)

def fetch_and_process(url, headers, user_agent_name):
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url)
    
    result = f"Status da resposta HTTP ({user_agent_name}): {response.status_code}\n\n"
    result += f"============= Cabeçalhos HTTP ({user_agent_name}) =============\n\n"
    for key, value in response.headers.items():
        result += f"{key}: {value}\n"
    
    if user_agent_name != "CURL":
        soup = BeautifulSoup(response.content, 'html.parser')
        
        result += f"\n============= Parágrafos ({user_agent_name}) =============\n"
        paragraphs = soup.find_all('p')
        for para in paragraphs:
            result += para.get_text() + "\n"
        
        result += f"\n============= Links ({user_agent_name}) =============\n"
        links = soup.find_all('a')
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            if href:
                result += f"{text}: {href}\n"
        
        result += f"\n============= Títulos ({user_agent_name}) =============\n"
        titles = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for title in titles:
            result += title.get_text().strip() + "\n"
        
        result += f"\n============= Imagens ({user_agent_name}) =============\n"
        images = soup.find_all('img')
        for img in images:
            src = img.get('src')
            alt = img.get('alt')
            if src:
                result += f"Fonte: {src}, Texto alternativo: {alt}\n"
        
        result += f"\n============= Listas ({user_agent_name}) =============\n"
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            items = lst.find_all('li')
            for item in items:
                result += item.get_text().strip() + "\n"
        
        result += f"\n============= Tabelas ({user_agent_name}) =============\n"
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                col_texts = [col.get_text().strip() for col in cols]
                result += '\t'.join(col_texts) + "\n"
        
        result += f"\n============= Outros Textos ({user_agent_name}) =============\n"
        other_texts = soup.find_all(string=True)
        for text in other_texts:
            if text.parent.name not in ['script', 'style', 'head', 'title', 'meta', '[document]']:
                content = text.strip()
                if content:
                    result += content + "\n"

    display_result(result)

# whois .br .com .gov
def requisicao_whois(servidor_whois, endereco_host, padrao):
    result = ""
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
            result += dados.decode('latin-1')
    objeto_socket.close()
    display_result(result)

def obter_whois_gov(endereco):
    servidores_whois_tdl = {'.gov': 'whois.nic.gov'}
    servidor_whois_gov = servidores_whois_tdl.get('.gov', None)
    if servidor_whois_gov:
        requisicao_whois(servidor_whois_gov, endereco, False)
    else:
        display_result("Servidor WHOIS para domínios .gov não encontrado.")

def obter_whois_br(endereco):
    servidores_whois_tdl = {'.br': 'whois.registro.br'}
    servidor_whois = servidores_whois_tdl['.br']
    requisicao_whois(servidor_whois, endereco, False)

def obter_whois_com(endereco):
    servidores_whois_tdl = {'.com': 'whois.verisign-grs.com'}
    servidor_whois = servidores_whois_tdl['.com']
    requisicao_whois(servidor_whois, endereco, True)

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
            display_result(whois_text)

    if response_registro_br.status_code == 200:
        soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
        div_result = soup_registro_br.find("div", class_="result")
        if div_result:
            result_text = div_result.get_text()
            display_result(result_text)

# Transferência de Zona DNS
def dns_transfer(site):
    result = "========================================== Transferência de Zona DNS ==========================================\n\n"
    output_dns = subprocess.run(['nslookup', '-query=ns', site], capture_output=True, text=True)
    lines = output_dns.stdout.splitlines()
    servers = [line.split()[-1] for line in lines if 'nameserver' in line]

    output_list_dns = []
    for server in servers:
        output = subprocess.run(['nslookup', '-type=any', site, server], capture_output=True, text=True)
        output_list_dns.append(output.stdout)

    for output in output_list_dns:
        result += output

    display_result(result)


# ipv4
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
        result = "========================================== Endereços IPv4 Encontrados ==========================================\n\n"
        for ipv4_address in ipv4_addresses:
            result += ipv4_address + "\n"
        display_result(result)
    else:
        display_result("Nenhum Endereço IPv4 encontrado.")

# Conteúdo do robots.txt
def exibir_robots_txt(site):
    robots_url = urljoin(site, '/robots.txt')
    response = requests.get(robots_url, headers=headers_firefox)
    if response.status_code == 200:
        display_result(f"============= Conteúdo do robots.txt =============\n\n{response.text}")
    else:
        display_result(f"Não foi possível acessar o robots.txt (Status: {response.status_code})")

# web_scraper
def web_scraper(url):
    response = requests.get(url, headers=headers_firefox)
    if response.status_code != 200:
        display_result("Erro na URL")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    subdomains = set(re.findall(r'(https?://(?:[\w-]+\.)+[\w]+)', response.text))
    result = f"Foram Encontrados ====>  {len(subdomains)}  Subdomínios\n\n"
    for subdomain in subdomains:
        result += subdomain + "\n"
    
    links = soup.find_all('a', href=True)
    urls = {link['href'] for link in links if link['href'].startswith('http://') or link['href'].startswith('https://') or link['href'].startswith('/')}
    complete_urls = {urljoin(url, link) if link.startswith('/') else link for link in urls}
    internal_urls = {link for link in complete_urls if urlparse(url).netloc in urlparse(link).netloc}
    
    result += f"\n\nForam Encontradas ====>  {len(internal_urls)}   URL internas\n\n"
    for internal_url in internal_urls:
        result += internal_url + "\n"

    display_result(result)

# buttons
def handle_choice(choice, url):
    site = url.replace('http://', '').replace('https://', '').split('/')[0]

    if choice == '1':
        fetch_and_process(url, headers_firefox, "Firefox")

    elif choice == '2':
        fetch_and_process(url, headers_curl, "CURL")
    
    elif choice == '3':
        dns_transfer(site)

    elif choice == '4':
        exibir_ipv4(site)

    elif choice == '5':
        exibir_robots_txt(url)

    elif choice == '6':
        web_scraper(url)

    elif choice == '7':
        obter_whois_br(site)

    elif choice == '8':
        obter_whois(site)
        if re.search(r'\.gov$', site):
            obter_whois_gov(site)    
    
    else:
        display_result("Opção inválida. Tente novamente.")

def on_button_click(choice):
    url = website_entry.get().strip()
    if url:
        handle_choice(choice, url)
    else:
        display_result("Por favor, insira uma URL válida.")

# Configurar a janela principal
window = tk.Tk()
window.wm_state('zoomed')
window.title("Analysis Tools")

# Criar o frame para a entrada do website
input_frame = tk.Frame(window)
input_frame.grid(column=0, row=0, columnspan=2, padx=5)

# Label e entrada para o nome do website
website_label = tk.Label(input_frame, text="Digite a URL do website", font=("Arial", 12))
website_label.grid(column=0, row=0)

website_entry = tk.Entry(input_frame, width=30, font=("Arial", 12))
website_entry.grid(column=0, row=1, padx=5, pady=3)

# Adicionando um espaço vazio entre a entrada de texto e os botões
empty_space = tk.Label(input_frame)
empty_space.grid(column=0, row=2)

# Botões para as diferentes opções
buttons = [
    ("1 = Usando User Agent do Firefox", "1"),
    ("2 = Cabeçalhos HTTP (CURL)", "2"),    
    ("3 = Transferência de Zona DNS", "3"),
    ("4 = Exibir IPv4", "4"),
    ("5 = Exibir robots.txt", "5"),
    ("6 = Scraper Web", "6"),
    ("7 = whois.br", "7"),
    ("8 = Whois.com", "8"),
]

for i, (text, choice) in enumerate(buttons):
    if choice == "7":
        button = tk.Button(input_frame, text=text, command=lambda choice=choice: on_button_click(choice), bg='#00ff00', font=("Arial", 10))


    elif choice == "8":
         button = tk.Button(input_frame, text=text, command=lambda choice=choice: on_button_click(choice), bg='#fca503', fg='#030303', width=12)

    else:
        button = tk.Button(input_frame, text=text, command=lambda choice=choice: on_button_click(choice))
    button.grid(column=0, row=2+i, pady=2)

# Criar o frame para os resultados
result_frame = tk.Frame(window)
result_frame.grid(column=0, row=12, columnspan=2, padx=2, pady=2)

# Criar o widget ScrolledText para os resultados
result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=133, height=36, font=("Arial", 12))
result_text.grid(column=0, row=0, padx=40, sticky=tk.W)

window.mainloop()
