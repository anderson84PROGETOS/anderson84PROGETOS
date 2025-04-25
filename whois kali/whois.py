import subprocess
import re
from datetime import datetime
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + r"""

██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗
██║    ██║██║  ██║██╔═══██╗██║██╔════╝
██║ █╗ ██║███████║██║   ██║██║███████╗
██║███╗██║██╔══██║██║   ██║██║╚════██║
╚███╔███╔╝██║  ██║╚██████╔╝██║███████║
 ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝
                                                                                                
""")

# Dicionário com os nomes traduzidos (sem os dois pontos!)
traducao = {
    "domain:": "Domínio",
    "owner:": "Entidade",
    "ownerid:": "CNPJ",
    "responsible:": "Responsável",
    "country:": "País",
    "owner-c:": "Contato do Dono",
    "tech-c:": "Contato Técnico",
    "nserver:": "Servidor DNS",
    "nsstat:": "Status DNS",
    "nslastaa:": "Última resposta",
    "dsrecord:": "Registro DS",
    "dsstatus:": "Status DS",
    "dslastok:": "Última verificação DS",
    "created:": "Criado em",
    "changed:": "Alterado em",
    "expires:": "Expira em",
    "status:": "Status",    
    "nic-hdl-br:": "ID NIC.br",
    "person:": "Pessoa",
    "e-mail:": "E-mail",
}

def traduzir_linha(linha):
    for termo, traducao_pt in traducao.items():
        if linha.lower().startswith(termo):
            valor = linha[len(termo):].strip()
            return Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{traducao_pt:<22}:  {valor}"
    return linha

def formatar_datas(texto):
    padrao_yyyymmdd = re.compile(r'(\d{4})(\d{2})(\d{2})')
    padrao_iso = re.compile(r'(\d{4})-(\d{2})-(\d{2})')

    def substituir(match):
        try:
            data = datetime.strptime(match.group(0), "%Y%m%d")
            return data.strftime("%d/%m/%Y")
        except:
            return match.group(0)

    def substituir_iso(match):
        try:
            data = datetime.strptime(match.group(0), "%Y-%m-%d")
            return data.strftime("%d/%m/%Y")
        except:
            return match.group(0)

    texto = padrao_yyyymmdd.sub(substituir, texto)
    texto = padrao_iso.sub(substituir_iso, texto)
    return texto

def whois_clean(domain):
    try:
        result = subprocess.run(['whois', domain], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        lines = result.stdout.splitlines()
        cleaned_lines = []
        ignore_patterns = [
            r'^% ',
            r'^\s*$',
            r'^% Copyright',
            r'^% whois\.registro\.br',
            r'^% Security and mail abuse',
            r'^% 202[0-9]',
            r'^%$',
        ]

        for line in lines:
            if not any(re.match(pat, line) for pat in ignore_patterns):
                linha_traduzida = traduzir_linha(line.strip())

                # Insere quebra de linha antes de novos blocos
                if any(chave in linha_traduzida for chave in [
                    "ID NIC.br"
                ]):
                    cleaned_lines.append("")  # Adiciona linha em branco

                cleaned_lines.append(linha_traduzida)

        resultado_limpo = '\n'.join(cleaned_lines)
        resultado_formatado = formatar_datas(resultado_limpo)
        return resultado_formatado

    except Exception as e:
        return f"Erro ao executar whois: {e}"


# Uso com entrada do usuário
if __name__ == "__main__":
    dominio = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome do domínio: ").strip()
    saida = whois_clean(dominio)
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nResultado do WHOIS\n")
    print(saida)
    
input(Fore.LIGHTRED_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")      
