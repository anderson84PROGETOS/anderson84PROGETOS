import threading
import queue
import socket
import urllib.parse
import urllib.request
import time

print("""

███████╗██╗   ██╗██████╗     ██████╗ ██████╗ ██╗   ██╗████████╗███████╗██████╗ 
██╔════╝██║   ██║██╔══██╗    ██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝██╔══██╗
███████╗██║   ██║██████╔╝    ██████╔╝██████╔╝██║   ██║   ██║   █████╗  ██████╔╝
╚════██║██║   ██║██╔══██╗    ██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝  ██╔══██╗
███████║╚██████╔╝██████╔╝    ██████╔╝██║  ██║╚██████╔╝   ██║   ███████╗██║  ██║
╚══════╝ ╚═════╝ ╚═════╝     ╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝
                                                                                                                         
""")

threads = 50
target_domain = input("\nDigite o domínio alvo (ex: example.com): ").strip()
print("\n")
wordlist = [
        "sitemap.xml","images","favicon","info.php","ri","robots.txt","~administrator","_docs","docs","pag", "pagamento", "buy", "registro", "registra", "registrado", "registrar",
        "compra", "pay", "day", "zero", "carta", "pagmnt", "guardiao", "guarda",
        "policies", "rules", "policia", "escuta", "grampo", "cabine", "trafego", "traf",
        "gabine", "intranet", "extranet", "remotedesktop", "extra", "intra", "net", "1",
        "2", "webdav", "dav", "inject", "shell", "webshell", "cube", "tube", "3",
        "access", "acess", "acessar", "bluebox", "box", "info", "down", "phpinfo", "power",
        "dell", "ibm", "hp", "solaris", "freebsd", "bsd", "daemon", "socket", "sock",
        "demo", "demom", "internetbanking", "banking", "desenv", "wire", "wired", "show",
        "shop", "casa", "piloto", "close", "open", "acesso", "acid", "active", "ad",
        "adm", "admin", "administrador", "administrator", "admins", "adsl", "ajuda",
        "alana", "alarm", "alarme", "alfa", "allow", "alrm", "aluno", "android",
        "anonimo", "anonimous", "anonymos", "anonymous", "antigo", "aovivo", "apache",
        "apache2", "aplicacao", "aplicativo", "app", "armadilha", "arquivo", "arquivos",
        "assina", "assinante", "at", "ataque", "atx", "aula", "autentica", "autenticacao",
        "autenticado", "autenticador", "auth", "auth-mac", "av", "avatar", "back", "backup",
        "banco", "bancodedados", "bank", "banking", "bat", "batmam", "batman", "bemtevi",
        "beta", "betatester", "bkp", "block", "blog", "bloqueio", "brain", "brasil",
        "broad", "broadcast", "bsd", "bus", "cache", "cacto", "cactus", "caixa", "cam",
        "cam01", "cam02", "cam1", "cam2", "camara", "camera", "cameras", "capa", "car",
        "cat", "cel", "celta", "celular", "centauro", "center", "centerdata", "central",
        "centraldecontrole", "chat", "chi", "claro", "classic", "client", "cliente",
        "clientes", "cloud", "cloudflare", "cod", "coiote", "comercio", "compu", "computador",
        "computer", "conect", "conection", "conexao", "conferencia", "config", "configura",
        "configurador", "configuration", "conta", "contas", "control", "controle",
        "controlecentral", "corp", "cpanel", "create", "criar", "cpd", "css", "dado",
        "dados", "data", "database", "datacenter", "datafile", "db", "dc", "ddns", "debian",
        "delphi", "delta", "desenvolvimento", "desktop", "deteccao", "detect", "detecta",
        "dev", "dhcp", "digama", "dir", "direcao", "direct", "directory", "direto", "diretor",
        "diretorio", "disk", "dlink", "dmz", "dns", "dns01", "dns02", "dns1", "dns2", "doc",
        "documentacao", "documentation", "documento", "documentos", "domain", "dominio",
        "download", "downloads", "drone", "drupal", "dsl", "ead", "eco", "ecologico",
        "eight", "entrar", "epsilon", "escola", "esconde", "escondido", "estacao", "eta",
        "ext", "ext1", "ext2", "extern", "faculdade", "fake", "faturamento", "fi", "fiber",
        "fibra", "fibraoptica", "file", "filedata", "files", "filiais", "filial", "financ",
        "financeiro", "fire", "firebird", "firewall", "firewl", "five", "fluxo", "fly",
        "fone", "fonte", "forum", "four", "frame", "free", "ftp", "ftpserver", "fw", "gama",
        "games", "gateway", "gerencia", "gerenciamento", "gerente", "globo", "gpo", "gt",
        "guest", "gw", "gw-srv", "hack", "hacker", "hard", "hardware", "hash", "help",
        "hiddem", "hide", "hids", "hips", "home", "honey", "honeypot", "host", "hostname",
        "hosts", "hr", "hub", "hundred", "ids", "imap", "ind", "index", "indexof", "industria",
        "industric", "info", "ingles", "instalacao", "install", "int", "intelbras", "intelbrass",
        "inter", "internet", "intra", "intranet", "ios", "iota", "ips", "ipv4", "ipv6",
        "joomla", "cartao", "card", "isp", "java", "javascript", "jogo", "jogos", "joomla",
        "js", "kiosks", "lab", "lab01", "lab1", "lambda", "larga", "leao", "lg", "link",
        "linus", "linux", "linx", "lion", "local", "localhost", "log", "logar", "login",
        "loja", "loja2", "mac", "mail", "mail2", "main", "manage", "management", "manager",
        "map", "mapa", "mapeamento", "master", "matrix", "matriz", "media", "metro", "microtik",
        "midia", "mint", "mk", "mod", "modsec", "modsecurity", "monit", "monitor", "monitora",
        "monitoramento", "mouse", "ms", "mx", "mysql", "mysql1", "mysql2", "natal", "net",
        "net1", "net2", "net3", "net4", "new", "nine", "novo", "ns01", "ns02", "ns1", "ns2",
        "ns3", "ns4", "ntp", "ntpserver", "ntserver", "nuvem", "nuvens", "oi", "old",
        "ombudsman", "omega", "omicron", "one", "onix", "op", "open", "opensource", "optica",
        "optico", "original", "ovo", "pabx", "page", "painel", "panel", "parede", "pass",
        "passwords", "pbx", "pc", "pfsense", "phone", "php", "php5", "phpmyadmin", "pi",
        "ping", "pong", "pop", "pop3", "portal", "ppp1", "pptp", "print", "printer", "pro",
        "prodruct", "producao", "produto", "prof", "professional", "professor", "program",
        "programas", "project", "projects", "projetos", "provedor", "provider", "proxy", "psi",
        "ptr", "pub", "public", "publica", "publico", "python", "qoppa", "qui", "radio",
        "radius", "rdp", "recursos", "rede", "redes", "register", "registrenational", "relay",
        "relay1", "remote", "remoto", "resolv", "resolve", "resolver", "restrict", "restrige",
        "restringe", "restrito", "rfid", "rh", "rips", "ro", "robo", "rota", "rote", "roteador",
        "roteamento", "route", "router", "router01", "router1", "samba", "sampi", "san", "script",
        "scripts", "sec", "secret", "secreta", "secretaria", "secretario", "secreto", "secure",
        "security", "seg", "segredo", "seguranca", "seguro", "senha", "senhas", "serv", "server",
        "servidor", "seven", "sf", "sftp", "sigma", "_sip", "sip", "sistema", "sistemas", "site",
        "sites", "six", "slave", "small", "smart", "smnp", "smtp", "snmp", "snort", "soft",
        "sos", "source", "_spf", "sql", "sqlserver", "squid", "srv", "srv01", "srv02",
        "srvmatriz", "srvone", "ssh", "ssl", "ssql", "stream", "streaming", "suport", "suporte",
        "sw", "switch", "swth", "system", "tau", "tclient", "ten", "test", "teste", "tester",
        "teta", "tigre", "tim", "_tls", "torvalds", "totem", "totens", "tplink", "tradicional",
        "training", "tranfere", "tranferencia", "transf", "tree", "treina", "treinamento",
        "treinamentos", "trinid", "trinit", "tv", "tvcamara", "two", "unidade", "unit",
        "universidade", "unix", "update", "upsilon", "user", "users", "usuario", "vagas",
        "virtua", "virtual", "vivo", "vmware", "voip", "vpn", "vps", "waf", "wall", "web",
        "web1", "web2", "webconf", "webconferencia", "webdisk", "weblab", "weblog", "webmail",
        "world", "wordpress", "wp", "webmaster", "webmin", "webpage", "webserver", "webservice",
        "webservices", "website", "websence", "websense", "whm", "wifi", "win", "windows",
        "wks", "word", "wordpress", "work", "workstation", "wp", "ww", "www", "www2", "wwww",
        "xeem", "xem", "xml", "zeta", "zimbra", "zebra", "zabbix", "zona", "zone"
]
resume = None
checked_subdomains = set()  # Conjunto para armazenar subdomínios já verificados
checked_paths = set()  # Conjunto para armazenar caminhos já verificados
unique_results = set()  # Conjunto para armazenar resultados únicos (URLs)

user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0"

def build_wordlist(wordlist):
    found_resume = False
    words = queue.Queue()

    for word in wordlist:
        if resume is not None:
            if found_resume:
                words.put(word)
            else:
                if word == resume:
                    found_resume = True
                    print("Resuming wordlist from: %s" % resume)
        else:
            words.put(word)

    return words

def subdomain_bruter(word_queue):
    while not word_queue.empty():
        attempt = word_queue.get()
        subdomain = f"{attempt}.{target_domain}"
        
        if subdomain not in checked_subdomains:
            try:
                ip = socket.gethostbyname(subdomain)
                for protocol in ['http', 'https']:
                    url = f"{protocol}://{subdomain}"
                    try:
                        headers = {"User-Agent": user_agent}
                        r = urllib.request.Request(url, headers=headers)
                        response = urllib.request.urlopen(r)
                        code = response.code
                        if code == 200 and url not in unique_results:
                            print(f"{url} ({ip})")
                            unique_results.add(url)
                            break
                    except urllib.error.URLError as e:
                        pass
                    except ConnectionResetError:
                        time.sleep(1)
                        continue
                checked_subdomains.add(subdomain)
            except socket.gaierror:
                pass
            except UnicodeError:
                pass

def path_bruter(word_queue):
    while not word_queue.empty():
        attempt = word_queue.get()
        for protocol in ['http', 'https']:
            path = f"{protocol}://{target_domain}/{urllib.parse.quote(attempt)}"
            
            if path not in checked_paths:
                try:
                    headers = {"User-Agent": user_agent}
                    r = urllib.request.Request(path, headers=headers)
                    response = urllib.request.urlopen(r)
                    code = response.code
                    if code == 200 and path not in unique_results:
                        print(f"{path}")
                        unique_results.add(path)
                        break
                except urllib.error.URLError as e:
                    pass
                except ConnectionResetError:
                    time.sleep(1)
                    continue
                checked_paths.add(path)

def save_results():
    while True:
        save = input("\nDeseja salvar os resultados? (s/n): ").lower()
        if save == 's':
            file_name = input("\nDigite o nome do arquivo (com extensão .txt): ")
            with open(file_name, "w") as f:
                for result in unique_results:
                    f.write(f"{result}\n")
            print(f"\nResultados salvos com sucesso Em: {file_name}")
            print(f"\nForam salvos {len(unique_results)} resultados.")
            break
        elif save == 'n':
            break
        else:
            print("Opção inválida. Por favor, escolha 's' para salvar ou 'n' para não salvar.")

if __name__ == "__main__":
    try:
        subdomain_word_queue = build_wordlist(wordlist)
        path_word_queue = build_wordlist(wordlist)

        threads_list = []
        for i in range(threads // 2):
            t = threading.Thread(target=subdomain_bruter, args=(subdomain_word_queue,))
            t.start()
            threads_list.append(t)

        for i in range(threads // 2):
            t = threading.Thread(target=path_bruter, args=(path_word_queue,))
            t.start()
            threads_list.append(t)

        for t in threads_list:
            t.join()

        save_results()

    except KeyboardInterrupt:
        print("\n\nScript interrompido pelo usuário.")
        save_results()

    input("\n\n🎯 Pressione Enter para sair 🎯\n")
