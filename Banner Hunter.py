import socket
import time
import threading
import sys
import errno

print("""

██████╗  █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗     ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗ 
██╔══██╗██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗    ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
██████╔╝███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝    ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝
██╔══██╗██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗    ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
██████╔╝██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║    ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
                                                                                                            
""")

class ScannerDeBanners:
    def __init__(self, alvo, portas, threads, timeout):
        self.alvo = alvo
        self.portas = [int(porta) for porta in portas]  # Converter para inteiros
        self.threads = threads
        self.timeout = timeout
        self.portas_abertas = []

    def obter_resultado(self):
        return self.iniciar_threads()

    def verificar_porta_aberta(self, porta):
        s = socket.socket()
        s.settimeout(float(self.timeout))
        try:
            resultado = s.connect_ex((self.alvo, porta))
            if resultado == 0:
                self.portas_abertas.append(porta)
        except socket.error:
            pass
        finally:
            s.close()

    def iniciar_threads(self):
        lista_threads = []
        for porta in self.portas:
            thread = threading.Thread(target=self.verificar_porta_aberta, args=(porta,))
            thread.start()
            lista_threads.append(thread)

            if len(lista_threads) >= self.threads:
                for t in lista_threads:
                    t.join()
                lista_threads = []

        for t in lista_threads:
            t.join()

        return (self.alvo, self.portas_abertas)

class CapturaDeBanner:
    def __init__(self, host, threads, saida):
        self.host = host
        self.threads = threads
        self.saida = saida
        self.banners = []
        self.iterar_enderecos()

    def iterar_enderecos(self):
        inicio = time.time()
        for endereco, portas in self.host.items():
            self.iniciar_threads(endereco, portas)
        fim = time.time()
        print("\n", '*' * 60, '\n')
        for i in self.banners:
            print("[+] IP : {} | Porta : {} | Banner : {}".format(i[0][0], i[0][1], i[1]))
        print("\n", '*' * 55, '\n')
        print("[+] Varredura Iniciada   Em: ", time.ctime(inicio))
        print("[+] Varredura Finalizada Em: ", time.ctime(fim))
        print('[+] Tempo Total Decorido Em: ', end=' ')
        tempo_decorrido = (fim - inicio) / 60  # Converter para minutos
        print(f"{tempo_decorrido:.2f} minutos")
        print("\n", '*' * 55, '\n')

        if self.saida:
            with open(self.saida, 'a') as f:
                for endereco, portas in self.host.items():
                    for porta, banner in self.banners:
                        f.write(f"{endereco} | Porta: {porta} | Banner: {banner}\n")

    def iniciar_threads(self, endereco, portas):
        lista_threads = []
        for porta in portas:
            thread = threading.Thread(target=self.banner_ip, args=(endereco, porta))
            thread.start()
            lista_threads.append(thread)

            if len(lista_threads) >= self.threads:
                for t in lista_threads:
                    t.join()
                lista_threads = []

        for t in lista_threads:
            t.join()

    def banner_ip(self, endereco, porta):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(float(1.0))
        try:
            s.connect((endereco, porta))
            if porta == 80:
                mensagem = (
                    "GET / HTTP/1.1\r\n"
                    f"Host: {endereco}\r\n"
                    "User-Agent: Mozilla/5.0\r\n"
                    "Accept-Language: en-US,en;q=0.5\r\n"
                    "Connection: keep-alive\r\n"
                    "Upgrade-Insecure-Requests: 1\r\n"
                    "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n"
                    "\r\n"
                )
                s.sendall(mensagem.encode())
                
                resposta = b""
                while b"\r\n\r\n" not in resposta:
                    dados = s.recv(4096)
                    if not dados:
                        break
                    resposta += dados
                
                cabeçalhos = resposta.split(b"\r\n\r\n")[0]
                banner_texto = cabeçalhos.decode('utf-8', errors='ignore')
                print("\n")                
                banner_texto = "Cabeçalho HTTP\n=============================================================\n" + banner_texto

            else:
                banner = s.recv(4096)
                banner_texto = banner.decode('utf-8', errors='ignore')

            self.banners.append([(endereco, porta), banner_texto])
        except socket.error as e:
            if e.errno != errno.ECONNREFUSED:
                # Para exibir apenas portas abertas, não adicionar banners de erros
                pass
        finally:
            s.close()

def extrair_portas(portas):
    lista_portas = []
    if portas:
        if "-" in portas and "," not in portas:
            x1, x2 = portas.split('-')
            lista_portas = list(range(int(x1), int(x2) + 1))
        elif "," in portas and "-" not in portas:
            lista_portas = [int(porta) for porta in portas.split(',')]
        elif "," in portas and "-" in portas:
            lista_portas_intervalo = []
            for i in portas.split(','):
                if "-" in i:
                    y1, y2 = i.split('-')
                    lista_portas_intervalo.extend(list(range(int(y1), int(y2) + 1)))
                else:
                    lista_portas_intervalo.append(int(i))
            lista_portas = lista_portas_intervalo
        else:
            lista_portas.append(int(portas))
    else:
        print("[*] Por favor forneça portas para varredura.")
        sys.exit(0)
    return lista_portas

def ip_valido(ip):
    try:
        socket.inet_aton(ip)
    except socket.error:
        ip = socket.gethostbyname(ip)
    return ip

def principal():
    alvo = input("\nDigite o nome do website (ex: www.exemplo.com): ").strip()
    portas = input("\n\nDigite uma porta ou intervalo de portas (ex: 21-80 ou 80): ").strip()
    threads = 10
    timeout = 1.0
    saida = None
    print()
    if not alvo:
        print("\n[*] Por favor, especifique o alvo. Ex: www.site.org")
        sys.exit(0)
    if not portas:
        print("\n[*] Por favor, especifique as portas separadas por vírgulas ou forneça intervalo de portas. Ex. 80-1200")
        sys.exit(0)

    host = {}
    host[ip_valido(alvo)] = extrair_portas(portas)
    if not host:
        print("\n[*] Entrada Inválida!")
        sys.exit(0)

    for item in host.items():
        verificar = ScannerDeBanners(item[0], item[1], threads, timeout)
        resultado = verificar.obter_resultado()
        
        print("\n[+] IP : {} | Portas Abertas : {}".format(resultado[0], resultado[1]))
        

    CapturaDeBanner(host, threads, saida)

if __name__ == '__main__':
    principal()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
