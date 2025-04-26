import re
import socket
from datetime import datetime
from colorama import Fore, Style, init

# Inicializa o Colorama
init(autoreset=True)

# Banner
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗    ██████╗ ██████╗ 
██║    ██║██║  ██║██╔═══██╗██║██╔════╝    ██╔══██╗██╔══██╗
██║ █╗ ██║███████║██║   ██║██║███████╗    ██████╔╝██████╔╝
██║███╗██║██╔══██║██║   ██║██║╚════██║    ██╔══██╗██╔══██╗
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║    ██████╔╝██║  ██║
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝    ╚═════╝ ╚═╝  ╚═╝
""")

# Servidores WHOIS por TLD
servidores_whois_tld = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.org': 'whois.pir.org',
    '.br': 'whois.registro.br',
    '.gov': 'whois.dotgov.gov',
    '.edu': 'whois.educause.edu',
}

# Campos traduzidos
traducao = {
    "domain:": "Domínio",
    "owner:": "Entidade",
    "ownerid:": "CNPJ",
    "responsible:": "Responsável",
    "country:": "País",
    "created:": "Criado em",
    "changed:": "Alterado em",
    "expires:": "Expira em",
    "status:": "Status",
    "nserver:": "Servidor DNS",
    "person:": "Pessoa",
    "e-mail:": "E-mail",
    "inetnum:": "Faixa de IP",
    "netname:": "Nome da Rede",
    "descr:": "Descrição",
    "org:": "Organização",
    "address:": "Endereço",
    "phone:": "Telefone",
    "abuse-mailbox:": "Abuse E-mail",
    "source:": "Fonte",
}

# Formatação de datas
def formatar_data_brasileira(texto):
    formatos = ["%Y-%m-%d", "%Y%m%d", "%Y-%m-%dT%H:%M:%SZ"]
    for formato in formatos:
        try:
            data = datetime.strptime(texto, formato)
            return data.strftime("%d/%m/%Y")
        except:
            continue
    return texto

# Tradução de linha
def traduzir_linha(linha):
    for termo, traducao_pt in traducao.items():
        if linha.lower().startswith(termo):
            valor = linha[len(termo):].strip()
            campo_formatado = f"{traducao_pt:<22}"
            return Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{campo_formatado}: {valor}"
    
    if ":" in linha:
        campo, valor = linha.split(":", 1)
        campo_formatado = f"{campo.strip():<22}"
        return Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{campo_formatado}: {valor.strip()}"

    return linha

# WHOIS para domínio ou IP
def consultar_whois(entrada):
    try:
        # Detecta se é IP
        try:
            socket.inet_pton(socket.AF_INET, entrada)
            tipo = "ipv4"
        except:
            try:
                socket.inet_pton(socket.AF_INET6, entrada)
                tipo = "ipv6"
            except:
                tipo = "dominio"

        # Para IPs, busca o servidor via IANA
        if tipo in ["ipv4", "ipv6"]:
            servidor_iana = 'whois.iana.org'
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((servidor_iana, 43))
                s.send((entrada + "\r\n").encode())
                resposta = b""
                while True:
                    dados = s.recv(4096)
                    if not dados:
                        break
                    resposta += dados
            texto_iana = resposta.decode(errors='ignore')
            match = re.search(r"refer:\s*(\S+)", texto_iana)
            servidor = match.group(1) if match else 'whois.arin.net'
        else:
            tld = '.' + entrada.split('.')[-1]
            servidor = servidores_whois_tld.get(tld.lower())
            if not servidor:
                return Fore.RED + "TLD não suportado."

        # Consulta ao servidor WHOIS
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((servidor, 43))
            s.send((entrada + "\r\n").encode())
            resposta = b""
            while True:
                dados = s.recv(4096)
                if not dados:
                    break
                resposta += dados

        texto = resposta.decode(errors='ignore')
        linhas = texto.splitlines()
        saida_formatada = []

        for linha in linhas:
            if not linha.strip():
                continue
            # Remove linhas de copyright, %, # ou termos legais
            if re.search(r'copyright|terms|usage|legal|reserved', linha, re.IGNORECASE):
                continue
            if linha.startswith(('%', '#')):
                continue

            campo_original = linha.strip().split(":", 1)[0].lower()

            if campo_original in ["nic-hdl-br"]:
                saida_formatada.append("")

            linha_traduzida = traduzir_linha(linha.strip())
            linha_data_formatada = re.sub(
                r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z)?|\d{8}",
                lambda x: formatar_data_brasileira(x.group()),
                linha_traduzida
            )
            saida_formatada.append(linha_data_formatada)

        return "\n".join(saida_formatada)

    except Exception as e:
        return Fore.RED + f"Erro ao consultar WHOIS: {e}"

# Execução
if __name__ == "__main__":
    entrada = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite um domínio ou IP para consulta WHOIS: ").strip()
    resultado = consultar_whois(entrada)
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nResultado da Consulta WHOIS\n")
    print(resultado)
    input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
