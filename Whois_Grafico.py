from socket import *
import re
from tkinter import *

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

def obter_whois():
    endereco = entry.get()
    padrao_expressao_regular = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    if padrao_expressao_regular.match(endereco):
        requisicao_whois(whois_arin, endereco, padrao=True)
    else:
        for TLD in servidores_whois_tdl.keys():
            if endereco.endswith(TLD):
                requisicao_whois(servidores_whois_tdl[TLD], endereco, padrao=False)
                break  # Exit the loop after finding a matching TLD

def limpar_tudo():
    text_box.delete(1.0, END)

# Create the main window
window = Tk()
window.wm_state('zoomed')
window.title("Whois Lookup")
window.geometry("400x300")

# Create an entry field for domain input
entry = Entry(window, width=40)
entry.pack(pady=10)

# Create a button to initiate the Whois lookup
button = Button(window, text="Lookup", command=obter_whois)
button.pack(pady=5)

# Create a button to clear the text box
clear_button = Button(window, text="Limpar Tudo", command=limpar_tudo)
clear_button.pack(pady=5)

# Create a text box to display the Whois results
text_box = Text(window, height=100, width=100)
text_box.pack(pady=10)

# Run the main event loop
window.mainloop()
