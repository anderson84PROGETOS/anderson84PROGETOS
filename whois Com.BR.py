from socket import *
import re
from tkinter import *
import requests
from bs4 import BeautifulSoup

whois_arin = "who.is"

servidores_whois_tdl = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.edu': 'whois.educause.edu',
    '.br': 'whois.registro.br'
}

def requisicao_whois(servidor_whois, endereco_host, padrao):
    objeto_socket = socket(AF_INET, SOCK_STREAM)
    conexao = objeto_socket.connect_ex((servidor_whois, 43))
    if conexao == 0:
        if padrao == True:
            if servidor_whois == 'whois.verisign-grs.com':  # For .com and .net domains
                objeto_socket.send('domain {}\r\n'.format(endereco_host).encode())
            else:
                objeto_socket.send('n + {}\r\n'.format(endereco_host).encode())
            while True:
                dados = objeto_socket.recv(65500)
                if not dados:
                    break
                text_box.insert(END, dados.decode('latin-1'))
        elif padrao == False:
            objeto_socket.send('{}\r\n'.format(endereco_host).encode())
            while True:
                dados = objeto_socket.recv(65500)
                if not dados:
                    break
                text_box.insert(END, dados.decode('latin-1'))

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

def extrair_campo(whois_section, label):
    field = whois_section.find("div", text=re.compile(label))
    if field:
        value = field.find_next_sibling("div").get_text(strip=True)
        return value
    return ""

def obter_whois():
    endereco = entry.get()
    url_whois = "https://www.whois.com/whois/{}".format(endereco)
    url_registro_br = "https://registro.br/cgi-bin/whois/?qr={}".format(endereco)

    response_whois = requests.get(url_whois)
    response_registro_br = requests.get(url_registro_br)

    if response_whois.status_code == 200 and response_registro_br.status_code == 200:
        # Parse WHOIS.COM
        soup_whois = BeautifulSoup(response_whois.text, "html.parser")
        whois_section = soup_whois.find("pre", class_="df-raw")
        if whois_section:
            whois_text = whois_section.get_text()
            text_box.insert(END, whois_text)

            # Extract and display additional information
            emails = encontrar_emails(soup_whois)
            if emails:
                text_box.insert(END, "\n\nE-mails encontrados:")
                for email in emails:
                    text_box.insert(END, "\n" + email)

            # Extract more fields if needed
            name = extrair_campo(whois_section, "Registrant Name:")
            registration_date = extrair_campo(whois_section, "Creation Date:")
            expiration_date = extrair_campo(whois_section, "Registrar Registration Expiration Date:")

            if name:
                text_box.insert(END, "\n\nNome do Titular: " + name)
            if registration_date:
                text_box.insert(END, "\nData de Registro: " + registration_date)
            if expiration_date:
                text_box.insert(END, "\nData de Expiração: " + expiration_date)

        # Parse REGISTRO.BR
        soup_registro_br = BeautifulSoup(response_registro_br.text, "html.parser")
        div_result = soup_registro_br.find("div", class_="result")
        if div_result:
            result_text = div_result.get_text()
            text_box.insert(END, "\n\n" + result_text)
    else:
        text_box.insert(END, "Erro ao obter informações WHOIS.")

def obter_whois_br():
    endereco = entry.get()
    servidor_whois = servidores_whois_tdl['.br']
    requisicao_whois(servidor_whois, endereco, False)

def limpar_tudo():
    text_box.delete(1.0, END)

# Create the main window
window = Tk()
window.wm_state('zoomed')
window.title("Whois  (.BR)  (.com) ")
window.geometry("400x300")

# Criando e posicionando widgets
url_label = Label(window, text="Digite o nome do WebSite WHOIS", font=('TkDefaultFont', 12, 'bold'))
url_label.pack()

# Create a scrollbar for the text box
scrollbar = Scrollbar(window)
scrollbar.pack(side=RIGHT, fill=Y)

# Create an entry field for domain input
entry = Entry(window, width=35, font=("TkDefaultFont", 12, "bold"))
entry.pack(pady=5)

# Create a button to initiate the Whois lookup for .BR domains
button_br = Button(window, text="Whois   .BR", command=obter_whois_br, bg="#00FF00", font=("TkDefaultFont", 10, "bold"))
button_br.pack(pady=10)

# Create a button to initiate the Whois lookup
button = Button(window, text="Whois  .COM", command=obter_whois, bg="#03fcfc", font=("TkDefaultFont", 10, "bold"))
button.pack(pady=5)

# Create a button to clear the text box
clear_button = Button(window, text="Limpar Tudo", command=limpar_tudo,  bg="#fcb603", font=("TkDefaultFont", 10, "bold"))
clear_button.pack(pady=5)

# Create a text box to display the Whois results
text_box = Text(window, height=40, width=110, font=("TkDefaultFont", 11, "bold"))
text_box.pack(pady=10)

# Configure the scrollbar to work with the text box
text_box.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=text_box.yview)

# Run the main event loop
window.mainloop()
