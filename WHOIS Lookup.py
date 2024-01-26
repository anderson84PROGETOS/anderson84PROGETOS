from socket import *
import re
import tkinter as tk
from tkinter import *
import requests
from bs4 import BeautifulSoup

# Dicionário de servidores WHOIS para TLDs específicos
servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br',
    '.org': 'whois.pir.org',
    '.info': 'whois.afilias.net',
    '.ru': 'whois.tcinet.ru',
    '.gov': 'whois.dotgov.gov',
}

# Função para enviar requisições Whois
def requisicao_whois(servidor_whois, endereco_host):
    objeto_socket = socket(AF_INET, SOCK_STREAM)
    conexao = objeto_socket.connect_ex((servidor_whois, 43))
    if conexao == 0:
        objeto_socket.send('{}\r\n'.format(endereco_host).encode())
        while True:
            dados = objeto_socket.recv(65500)
            if not dados:
                break
            decoded_data = dados.decode('latin-1')
            # Filtrar apenas as informações específicas
            filtered_data = filtrar_informacoes(decoded_data)
            text_box.insert(END, filtered_data)

# Função para encontrar e-mails em uma página HTML
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

# Função para filtrar as informações específicas do Whois
def filtrar_informacoes(data):
    relevant_info = []
    relevant_fields = ["domain", "ownerid", "nserver", "person", "e-mail", "owner"]  
     
    for line in data.split("\n"):
        if "domain (.br)" in line.lower() or "registrant (tax id)" in line.lower() or "ticket" in line.lower():
            continue  # Ignorar estas linhas
        for field in relevant_fields:
            if field in line.lower():
                relevant_info.append(line.strip())
                break  # Adicionar uma quebra aqui para pular duas linhas entre as informações
    return "\n\n".join(relevant_info)

# Função para obter informações Whois de um domínio
def obter_whois():
    endereco = entry.get()
    url_whois = "https://www.whois.com/whois/{}".format(endereco)
    response_whois = requests.get(url_whois)
    if response_whois.status_code == 200:
        soup_whois = BeautifulSoup(response_whois.text, "html.parser")
        whois_section = soup_whois.find("pre", class_="df-raw")
        if whois_section:
            whois_text = whois_section.get_text()
            text_box.insert(END, filtrar_informacoes(whois_text))
            emails = encontrar_emails(soup_whois)
            if emails:
                text_box.insert(END, "\n\nE-mails encontrados:")
                for email in emails:
                    text_box.insert(END, "\n" + email)
    else:
        text_box.insert(END, "Erro ao obter informações WHOIS.")

# Função para obter informações Whois de um domínio .BR ou .GOV
def obter_whois_br():
    endereco = entry.get()
    tld = endereco[endereco.rfind('.'):].lower()  # Obtém o TLD do endereço inserido
    if tld in servidores_whois_tdl:
        servidor_whois = servidores_whois_tdl[tld]
        requisicao_whois(servidor_whois, endereco)
    else:
        text_box.insert(END, "O domínio inserido não está na lista de servidores WHOIS.")


# Função para limpar a caixa de texto
def limpar_tudo():
    text_box.delete(1.0, END)

# Criando a janela principal
window = Tk()
window.wm_state('zoomed')
window.title("Whois (.com) (.BR) ")
window.geometry("400x300")

# Criando e posicionando widgets
url_label = Label(window, text="Digite o nome WebSite", font=('TkDefaultFont', 11, 'bold'))
url_label.pack()

# Criando uma barra de rolagem para a caixa de texto
scrollbar = Scrollbar(window)
scrollbar.pack(side=RIGHT, fill=Y)

# Criando uma entrada para inserção do domínio
entry = Entry(window, width=40, font=("TkDefaultFont", 12, "bold"))
entry.pack(pady=10)

# Botão para iniciar a consulta Whois para domínios .BR
button_br = Button(window, text="Whois  (.BR)", command=obter_whois_br, bg="#00FF00", font=("TkDefaultFont", 10, "bold"))
button_br.pack(pady=10)

# Botão para iniciar a consulta Whois para domínios .COM
button = Button(window, text="Whois (.COM)", command=obter_whois, bg="#0cf2e3", font=("TkDefaultFont", 10, "bold"))
button.pack(pady=5)

# Botão para limpar a caixa de texto
clear_button = Button(window, text="Limpar Tudo", command=limpar_tudo,  bg="#D2691E", font=("TkDefaultFont", 10, "bold"))
clear_button.pack(pady=5)

# Caixa de texto para exibir os resultados Whois
text_box = Text(window, height=35, width=120, font=("TkDefaultFont", 12, "bold"))
text_box.pack(pady=10)

# Configurando a barra de rolagem para funcionar com a caixa de texto
text_box.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=text_box.yview)

# Executando o loop principal
window.mainloop()
