from socket import *
import re

port_range_pattern = re.compile("([0-9]+)-([0-9]+)")
print(r"""********************************************************************************************                                             
                                  _           _     
                        __      _| |__   ___ (_)___ 
                        \ \ /\ / / '_ \ / _ \| / __|
                         \ V  V /| | | | (_) | \__ \
                          \_/\_/ |_| |_|\___/|_|___/
                                                                                                    """)
print("\n*********************************************************************************************")


endereco = input("Digite Domínio : ")
print()


whois_arin = "whois.arin.net"

servidores_whois_tdl = {'.br': 'whois.registro.br', '.org': 'whois.pir.org', '.com': 'whois.verisign-grs.com', '.pt': 'whois.dns.pt'}

padrao_expressao_regular = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

def requisicao_whois(servidor_whois, endereco_host, padrao):
    objeto_socket = socket(AF_INET, SOCK_STREAM)
    conexao = objeto_socket.connect_ex((servidor_whois, 43))
    if conexao == 0:
        if padrao == True:
            objeto_socket.send('n + {}\r\n'.format(endereco_host).encode())
            while True:
                dados = objeto_socket.recv(65500)
                if not dados:
                    break
                print(dados.decode('latin-1'))
        elif padrao == False:
            objeto_socket.send('{}\r\n'.format(endereco_host).encode())
            while True:
                dados = objeto_socket.recv(65500)
                if not dados:
                    break
                print(dados.decode('latin-1'))

if padrao_expressao_regular.match(endereco):
    requisicao_whois(whois_arin, endereco, padrao = True)
else:
    for TLD in servidores_whois_tdl.keys():
        if endereco.endswith(TLD):
            requisicao_whois(servidores_whois_tdl[TLD], endereco, padrao = False)

input('\n\033[31mPressione Enter Para Sair!')   
