import dns.resolver

print("""

██████╗ ███╗   ██╗███████╗    ██████╗ ██████╗ ██╗   ██╗████████╗███████╗
██╔══██╗████╗  ██║██╔════╝    ██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝
██║  ██║██╔██╗ ██║███████╗    ██████╔╝██████╔╝██║   ██║   ██║   █████╗  
██║  ██║██║╚██╗██║╚════██║    ██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝  
██████╔╝██║ ╚████║███████║    ██████╔╝██║  ██║╚██████╔╝   ██║   ███████╗
╚═════╝ ╚═╝  ╚═══╝╚══════╝    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝
                                                                        

""")

# Solicita o nome do website ao usuário
alvo = input("\nDigite o nome do website: ")

print("\n========== Encontrando subdomínios ==========\n")

# Lista de subdomínios para teste
subdominios = [
    "pag", "pagamento", "buy", "registro", "registra", "registrado", "registrar", "compra", "pay", "day", "zero", "carta", "pagmnt", "guardiao", "guarda", "policies", "rules", "policia", "escuta", "grampo", "cabine", "trafego", "traf", "gabine", "intranet", "extranet", "remotedesktop", "extra", "intra", "net", "1", "2", "webdav", "dav", "inject", "shell", "webshell", "cube", "tube", "3", "access", "acess", "acessar", "bluebox", "box", "info", "down", "phpinfo", "power", "dell", "ibm", "hpv", "solaris", "freebsd", "bsd", "daemon", "socket", "sock", "demo", "demom", "internetbanking", "banking", "desenv", "wire", "wired", "show", "shop", "casa", "piloto", "close", "open", "acesso", "acid", "active", "ad", "adm", "admin", "administrador", "administrator", "admins", "adsl", "ajuda", "alana", "alarm", "alarme", "alfa", "allow", "alrm", "aluno", "android", "anonimo", "anonimous", "anonymos", "anonymous", "antigo", "aovivo", "apache", "apache2", "aplicacao", "aplicativo", "app", "armadilha", "arquivo", "arquivos", "assina", "assinante", "at", "ataque", "atx", "aula", "autentica", "autenticacao", "autenticado", "autenticador", "auth", "auth-mac", "av", "avatar", "back", "backup", "banco", "bancodedados", "bank", "banking", "bat", "batmam", "batman", "bemtevi", "beta", "betatester", "bkp", "block", "blog", "bloqueio", "brain", "brasil", "broad", "broadcast", "bsd", "bus", "cache", "cacto", "cactus", "caixa", "cam", "cam01", "cam02", "cam1", "cam2", "camara", "camera", "cameras", "capa", "car", "cat", "cel", "celta", "celular", "centauro", "center", "centerdata", "central", "centraldecontrole", "chat", "chi", "claro", "classic", "client", "cliente", "clientes", "cloud", "cloudflare", "cod", "coiote", "comercio", "compu", "computador", "computer", "conect", "conection", "conexao", "conferencia", "config", "configura", "configurador", "configuration", "conta", "contas", "control", "controle", "controlecentral", "corp", "cpanel", "create", "criar", "cpd", "css", "dado", "dados", "data", "database", "datacenter", "datafile", "db", "dc", "ddns", "debian", "delphi", "delta", "desenvolvimento", "desktop", "deteccao", "detect", "detecta", "dev", "dhcp", "digama", "dir", "direcao", "direct", "directory", "direto", "diretor", "diretorio", "disk", "dlink", "dmz", "dns", "dns01", "dns02", "dns1", "dns2", "doc", "documentacao", "documentation", "documento", "documentos", "domain", "dominio", "download", "downloads", "drone", "drupal", "dsl", "ead", "eco", "ecologico", "eight", "entrar", "epsilon", "escola", "esconde", "escondido", "estacao", "eta", "ext", "ext1", "ext2", "extern", "faculdade", "fake", "faturamento", "fi", "fiber", "fibra", "fibraoptica", "file", "filedata", "files", "filiais", "filial", "financ", "financeiro", "fire", "firebird", "firewall", "firewl", "five", "fluxo", "fly", "fone", "fonte", "forum", "four", "frame", "free", "ftp", "ftpserver", "fw", "gama", "games", "gateway", "gerencia", "gerenciamento", "gerente", "globo", "gpo", "gt", "guest", "gw", "gw-srv", "hack", "hacker", "hard", "hardware", "hash", "help", "hiddem", "hide", "hids", "hips", "home", "honey", "honeypot", "host", "hostname", "hosts", "hr", "hub", "hundred", "ids", "imap", "ind", "index", "indexof", "industria", "industric", "info", "ingles", "instalacao", "install", "int", "intelbras", "intelbrass", "inter", "internet", "intra", "intranet", "ios", "iota", "ips", "ipv4", "ipv6", "joomla", "cartao", "card", "isp", "java", "javascript", "jogo", "jogos", "joomla", "js", "kiosks", "lab", "lab01", "lab1", "lambda", "larga", "leao", "lg", "link", "linus", "linux", "linx", "lion", "local", "localhost", "log", "logar", "login", "loja", "loja2", "mac", "mail", "mail2", "main", "manage", "management", "manager", "map", "mapa", "mapeamento", "master", "matrix", "matriz", "media", "metro", "microtik", "midia", "mint", "mk", "mod", "modsec", "modsecurity", "monit", "monitor", "monitora", "monitoramento", "mouse", "ms", "mx", "mysql", "mysql1", "mysql2", "natal", "net", "net1", "net2", "net3", "net4", "new", "nine", "novo", "ns01", "ns02", "ns1", "ns2", "ns3", "ns4", "ntp", "ntpserver", "ntserver", "nuvem", "nuvens", "oi", "old", "ombudsman", "omega", "omicron", "one", "onix", "op", "open", "opensource", "optica", "optico", "original", "ovo", "pabx", "page", "painel", "panel", "parede", "pass", "passwords", "pbx", "pc", "pfsense", "phone", "php", "php5", "phpmyadmin", "pi", "ping", "pong", "pop", "pop3", "portal", "ppp1", "pptp", "print", "printer", "pro", "prodruct", "producao", "produto", "prof", "professional", "professor", "program", "programas", "project", "projects", "projetos", "provedor", "provider", "proxy", "psi", "ptr", "pub", "public", "publica", "publico", "python", "qoppa", "qui", "radio", "radius", "rdp", "recursos", "rede", "redes", "register", "registrenational", "relay", "relay1", "remote", "remoto", "resolv", "resolve", "resolver", "restrict", "restrige", "restringe", "restrito", "rfid", "rh", "rips", "ro", "robo", "rota", "rote", "roteador", "roteamento", "route", "router", "router01", "router1", "samba", "sampi", "san", "script", "scripts", "sec", "secret", "secreta", "secretaria", "secretario", "secreto", "secure", "security", "seg", "segredo", "seguranca", "seguro", "senha", "senhas", "serv", "server", "servidor", "seven", "sf", "sftp", "sigma", "_sip", "sip", "sistema", "sistemas", "site", "sites", "six", "slave", "small", "smart", "smnp", "smtp", "snmp", "snort", "soft", "sos", "source", "_spf", "sql", "sqlserver", "squid", "srv", "srv01", "srv02", "srvmatriz", "srvone", "ssh", "ssl", "ssql", "stream", "streaming", "suport", "suporte", "sw", "switch", "swth", "system", "tau", "tclient", "ten", "test", "teste", "tester", "teta", "tigre", "tim", "_tls", "torvalds", "totem", "totens", "tplink", "tradicional", "training", "tranfere", "tranferencia", "transf", "tree", "treina", "treinamento", "treinamentos", "trinid", "trinit", "tv", "tvcamara", "two", "unidade", "unit", "universidade", "unix", "update", "upsilonv", "user", "usersv", "usuario", "vagas", "virtua", "virtual", "vivo", "vmware", "voip", "vpn", "vps", "waf", "wall", "web", "web1", "web2", "webconf", "webconferencia", "webdisk", "weblab", "weblog", "webmail", "world", "wordpress", "wp", "webmaster", "webmin", "webpage", "webserver", "webservice", "webservices", "website", "websence", "websense", "whm", "wifi", "win", "windows", "wks", "word", "wordpress", "work", "workstation", "wp", "ww", "www", "www2", "wwww", "xeem", "xem", "xml", "zeta", "zimbra", "zebra", "zabbix", "zona", "zone"
]

# Cria um resolver DNS
res = dns.resolver.Resolver()

# Itera sobre cada subdomínio na lista e tenta resolver seu IP
for subdominio in subdominios:
    try:
        sub_alvo = f"{subdominio}.{alvo}"
        resultado = res.resolve(sub_alvo, "A")
        for ip in resultado:
            print(f"{sub_alvo} -> {ip}")
    except dns.resolver.NXDOMAIN:
        pass
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.Timeout:
        print(f"Timeout ao resolver {sub_alvo}")
    except Exception as e:
        print(f"Erro ao resolver {sub_alvo}: {e}")

input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
