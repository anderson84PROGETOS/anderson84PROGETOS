import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import socket
import threading
import queue

# Dicionário de protocolos conhecidos (nome curto, descrição)
PORT_SERVICES = {
    7: ("Eco", "Protocolo Echo, responde com os dados recebidos"),
    9: ("Descartar", "Protocolo Discard, descarta dados recebidos"),
    13: ("Horário", "Protocolo Daytime, retorna a hora atual"),
    17: ("Citação", "Quote of the Day (Citação do Dia)"),
    19: ("Gerador de Caractere", "Protocolo Chargen"),
    20: ("FTP Dados", "Protocolo de Transferência de Arquivos (dados)"),
    21: ("FTP", "Protocolo de Transferência de Arquivos (controle)"),
    22: ("SSH", "Shell Seguro"),
    23: ("Telnet", "Protocolo Telnet"),
    25: ("SMTP", "Protocolo Simples de Transferência de Correio"),
    37: ("Tempo", "Protocolo de Tempo"),
    43: ("WHOIS", "Protocolo WHOIS"),
    49: ("TACACS", "Sistema de Controle de Acesso a Terminais"),
    53: ("DNS", "Sistema de Nomes de Domínio"),
    67: ("DHCP Servidor", "Protocolo de Configuração Dinâmica de Host (servidor)"),
    68: ("DHCP Cliente", "Protocolo de Configuração Dinâmica de Host (cliente)"),
    69: ("TFTP", "Protocolo de Transferência de Arquivos Trivial"),
    70: ("Gopher", "Protocolo Gopher"),
    79: ("Finger", "Protocolo Finger"),
    80: ("HTTP", "Protocolo de Transferência de Hipertexto"),
    88: ("Kerberos", "Autenticação Kerberos"),
    110: ("POP3", "Protocolo de Correio v3"),
    111: ("RPCbind", "Vinculação de Chamada de Procedimento Remoto"),
    119: ("NNTP", "Protocolo de Transferência de Notícias"),
    123: ("NTP", "Protocolo de Tempo de Rede"),
    135: ("MS RPC", "Chamada de Procedimento Remoto da Microsoft"),
    137: ("NetBIOS Nome", "Serviço de Nome NetBIOS"),
    138: ("NetBIOS Datagrama", "Serviço de Datagrama NetBIOS"),
    139: ("NetBIOS Sessão", "Serviço de Sessão NetBIOS"),
    143: ("IMAP", "Protocolo de Acesso a Mensagens da Internet"),
    161: ("SNMP", "Protocolo Simples de Gerenciamento de Rede"),
    162: ("SNMP Trap", "Armadilha SNMP"),
    179: ("BGP", "Protocolo de Roteamento de Bordas"),
    194: ("IRC", "Bate-papo por Retransmissão na Internet"),
    389: ("LDAP", "Protocolo de Acesso a Diretórios Leve"),
    427: ("SLP", "Protocolo de Localização de Serviços"),
    443: ("HTTPS", "HTTP Seguro"),
    445: ("SMB", "Bloco de Mensagens do Servidor (Microsoft)"),
    465: ("SMTPS", "SMTP Seguro"),
    514: ("Syslog", "Registro do Sistema"),
    515: ("LPD", "Daemon de Impressora de Linha"),
    520: ("RIP", "Protocolo de Informação de Roteamento"),
    548: ("AFP", "Protocolo de Arquivamento da Apple"),
    554: ("RTSP", "Protocolo de Streaming em Tempo Real"),
    587: ("SMTP (TLS)", "SMTP com TLS"),
    631: ("IPP", "Protocolo de Impressão na Internet (CUPS)"),
    636: ("LDAPS", "LDAP Seguro"),
    873: ("Rsync", "Sincronização de Arquivos Rsync"),
    993: ("IMAPS", "IMAP Seguro"),
    995: ("POP3S", "POP3 Seguro"),
    1080: ("SOCKS", "Proxy SOCKS"),
    1433: ("MSSQL", "Microsoft SQL Server"),
    1521: ("Oracle DB", "Banco de Dados Oracle"),
    1723: ("PPTP", "Protocolo de Túnel Ponto a Ponto"),
    1812: ("RADIUS", "Serviço de Autenticação Remota de Usuários"),
    1813: ("RADIUS Contabil.", "Contabilização RADIUS"),
    2049: ("NFS", "Sistema de Arquivos de Rede"),
    2082: ("cPanel", "Painel de Controle cPanel"),
    2083: ("cPanel SSL", "Painel de Controle cPanel (seguro)"),
    2181: ("ZooKeeper", "Apache ZooKeeper"),
    2375: ("Docker", "API do Docker"),
    2525: ("SMTP Alternativo", "Porta alternativa para SMTP"),
    3306: ("MySQL", "Banco de Dados MySQL"),
    3389: ("RDP", "Protocolo de Área de Trabalho Remota (Microsoft)"),
    3478: ("STUN", "Utilitários de Travessia de NAT"),
    3690: ("SVN", "Subversion (controle de versão)"),
    4369: ("Erlang EPMD", "Daemon de Mapeamento de Porta Erlang"),
    5432: ("PostgreSQL", "Banco de Dados PostgreSQL"),
    5900: ("VNC", "Computação em Rede Virtual"),
    5984: ("CouchDB", "Banco de Dados Apache CouchDB"),
    6379: ("Redis", "Banco de Dados Redis"),
    6667: ("IRC", "Bate-papo por Retransmissão na Internet (porta alternativa)"),
    8000: ("HTTP Alternativo", "Porta alternativa para HTTP"),
    8080: ("HTTP-Proxy", "Proxy HTTP ou HTTP alternativo"),
    8443: ("HTTPS Alternativo", "Porta alternativa para HTTPS"),
    8888: ("HTTP Alternativo", "Porta alternativa para HTTP (comum em apps personalizados)"),
    9000: ("SonarQube", "Servidor SonarQube"),
    9042: ("Cassandra", "Banco de Dados Apache Cassandra"),
    9200: ("Elasticsearch", "API HTTP do Elasticsearch"),
    9300: ("Elasticsearch", "Comunicação de cluster do Elasticsearch"),
    9418: ("Git", "Protocolo Git"),
    11211: ("Memcached", "Sistema de cache Memcached"),
    27017: ("MongoDB", "Banco de Dados MongoDB"),
    50000: ("SAP", "Aplicações SAP (pode variar)"),
}


class PortScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Scanner de Portas")
        self.root.geometry("1050x900")

        # Entrada IP
        tk.Label(root, text="Endereço IP ou Nome do website", font=("Arial", 12, "bold")).pack(pady=5)
        self.entry_ip = tk.Entry(root, width=40, font=("Arial", 12, "bold"))
        self.entry_ip.pack(pady=5)

        # Entrada de range de portas
        tk.Label(root, text="Porta inicial", font=("Arial", 12, "bold")).pack(pady=5)
        self.entry_port_start = tk.Entry(root, width=8, font=("Arial", 12, "bold"))
        self.entry_port_start.pack(pady=5)

        tk.Label(root, text="Porta Final", font=("Arial", 12, "bold")).pack(pady=5)
        self.entry_port_end = tk.Entry(root, width=8, font=("Arial", 12, "bold"))
        self.entry_port_end.pack(pady=5)

        # Botão iniciar
        self.btn_scan = tk.Button(root, text="Iniciar Scan", bg="#03fc24", fg="black", font=("Arial", 11), command=self.start_scan)
        self.btn_scan.pack(pady=10)

        # Botão salvar
        self.btn_save = tk.Button(root, text="Salvar Portas abertas", bg="#fc9d03", fg="black", font=("Arial", 11), command=self.save_results, state=tk.DISABLED)
        self.btn_save.pack(pady=5)

        # Barra de progresso
        self.progress = ttk.Progressbar(root, length=500, mode="determinate")
        self.progress.pack(pady=10)

        # Frame com Scrollbar + Text
        frame = tk.Frame(root)
        frame.pack(pady=10, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_output = tk.Text(frame, wrap=tk.WORD, width=120, height=35, bg="#1e1e1e", fg="white", yscrollcommand=scrollbar.set)
        self.text_output.pack(pady=10)

        scrollbar.config(command=self.text_output.yview)

        # Definir tags para colorir
        self.text_output.tag_config("open", foreground="lime")     # verde
        self.text_output.tag_config("closed", foreground="red")    # vermelho
        self.text_output.tag_config("normal", foreground="white")  # padrão

        # Fila para comunicação com thread
        self.queue = queue.Queue()

        # Lista para guardar portas abertas
        self.open_ports = []

    def start_scan(self):
        ip = self.entry_ip.get().strip()
        if not ip:
            messagebox.showwarning("Aviso", "Digite um IP válido")
            return

        try:
            port_start = int(self.entry_port_start.get())
            port_end = int(self.entry_port_end.get())
        except ValueError:
            messagebox.showwarning("Aviso", "Digite portas válidas")
            return

        if port_start < 0 or port_end > 65535 or port_start > port_end:
            messagebox.showwarning("Aviso", "Intervalo de portas inválido")
            return

        self.text_output.delete(1.0, tk.END)
        self.progress["value"] = 0
        total_ports = port_end - port_start + 1
        self.progress["maximum"] = total_ports
        self.open_ports.clear()
        self.btn_save.config(state=tk.DISABLED)

        thread = threading.Thread(target=self.scan_ports, args=(ip, port_start, port_end))
        thread.daemon = True
        thread.start()

        self.root.after(100, self.update_output)

    def scan_ports(self, ip, port_start, port_end):
        for port in range(port_start, port_end + 1):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            try:
                result = sock.connect_ex((ip, port))
                if result == 0:
                    service, desc = PORT_SERVICES.get(port, (f"Porta {port}", "Serviço desconhecido"))
                    msg = f"[+] Porta {port} ABERTA ({service})\t {desc}\n"

                    self.queue.put(("open", msg))
                    self.open_ports.append(msg)
                else:
                    self.queue.put(("closed", f"[-] Porta {port} fechada\n"))
            except Exception as e:
                self.queue.put(("normal", f"Erro na porta {port}: {e}\n"))
            finally:
                sock.close()
                self.queue.put(("progress", 1))

        self.queue.put(("normal", "\n\n>>> Scan concluído!\n"))
        self.queue.put(("enable_save", None))

    def update_output(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if isinstance(item, tuple):
                    if item[0] == "progress":
                        self.progress["value"] += item[1]
                    elif item[0] == "enable_save":
                        self.btn_save.config(state=tk.NORMAL)
                    else:
                        tag, msg = item
                        self.text_output.insert(tk.END, msg, tag)
                        self.text_output.see(tk.END)
        except queue.Empty:
            pass
        self.root.after(100, self.update_output)

    def save_results(self):
        if not self.open_ports:
            messagebox.showinfo("Info", "Nenhuma porta aberta para salvar.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Arquivo de texto", "*.txt")])
        if file_path:
            with open(file_path, "w") as f:
                f.writelines(self.open_ports)
            messagebox.showinfo("Sucesso", f"Portas abertas salvas em: {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PortScannerGUI(root)
    root.mainloop()
