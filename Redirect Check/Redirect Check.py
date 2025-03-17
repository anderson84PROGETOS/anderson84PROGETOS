import requests
from colorama import Fore, Style, init
import whois
from datetime import datetime

# Inicializando o colorama
init(autoreset=True)

# Exibe o banner inicial mais compacto
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██████╗ ███████╗██████╗ ██╗██████╗ ███████╗ ██████╗████████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
██╔══██╗██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
██████╔╝█████╗  ██║  ██║██║██████╔╝█████╗  ██║        ██║       ██║     ███████║█████╗  ██║     █████╔╝ 
██╔══██╗██╔══╝  ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║       ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ 
██║  ██║███████╗██████╔╝██║██║  ██║███████╗╚██████╗   ██║       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝        ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝
                                                                                                                                                                                                                                                                       
""")

# Cabeçalhos para evitar erro 403
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def get_domain_info(url):
    # Extrai o domínio da URL
    dominio = url.split('://')[-1].split('/')[0]
    try:
        w = whois.whois(dominio)
        data_criacao = w.creation_date
        data_atualizacao = w.updated_date
        data_expiracao = w.expiration_date

        # Converte datas para o formato desejado
        if isinstance(data_criacao, list):
            data_criacao = data_criacao[0]
        if isinstance(data_atualizacao, list):
            data_atualizacao = data_atualizacao[0]
        if isinstance(data_expiracao, list):
            data_expiracao = data_expiracao[0]

        # Formata as datas em português brasileiro
        dias_semana = {
            'Monday': 'segunda-feira', 'Tuesday': 'terça-feira', 'Wednesday': 'quarta-feira',
            'Thursday': 'quinta-feira', 'Friday': 'sexta-feira', 'Saturday': 'sábado', 'Sunday': 'domingo'
        }
        meses = {
            'January': 'janeiro', 'February': 'fevereiro', 'March': 'março', 'April': 'abril',
            'May': 'maio', 'June': 'junho', 'July': 'julho', 'August': 'agosto',
            'September': 'setembro', 'October': 'outubro', 'November': 'novembro', 'December': 'dezembro'
        }

        criacao_str = (f"{dias_semana[data_criacao.strftime('%A')]}, {data_criacao.day} de {meses[data_criacao.strftime('%B')]} de {data_criacao.year}"
                       if data_criacao else "Desconhecido")
        atualizacao_str = (f"{dias_semana[data_atualizacao.strftime('%A')]}, {data_atualizacao.day} de {meses[data_atualizacao.strftime('%B')]} de {data_atualizacao.year}"
                           if data_atualizacao else "Desconhecido")
        expiracao_str = (f"{dias_semana[data_expiracao.strftime('%A')]}, {data_expiracao.day} de {meses[data_expiracao.strftime('%B')]} de {data_expiracao.year}"
                         if data_expiracao else "Desconhecido")
        
        # Formata datas no formato ISO (YYYY-MM-DD)
        criacao_iso = data_criacao.strftime('%Y-%m-%d') if data_criacao else "Desconhecido"
        atualizacao_iso = data_atualizacao.strftime('%Y-%m-%d') if data_atualizacao else "Desconhecido"
        expiracao_iso = data_expiracao.strftime('%Y-%m-%d') if data_expiracao else "Desconhecido"

        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n\n============== Mais Informações ==============\n")
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Domínio: {dominio}")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nRegistrado: {criacao_str:<50} Registrado: {criacao_iso}")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nModificado: {atualizacao_str:<50} Modificado: {atualizacao_iso}")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nExpira: {expiracao_str:<54} Expira: {expiracao_iso}")
        
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao obter informações do domínio: {e}")
        

def verificar_open_redirect(url):
    # Dicionário para mapear códigos de status para mensagens
    status_messages = {
        200: "OK",
        301: "MOVIDO PERMANENTEMENTE",
        302: "ENCONTRADO",
        303: "VEJA OUTRO",
        307: "REDIRECIONAMENTO TEMPORÁRIO",
        308: "REDIRECIONAMENTO PERMANENTE"
    }
    
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nVerificando Redirecionamentos em: {url}\n")
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Histórico de Redirecionamentos\n")
    
    # Configura uma sessão para rastrear o histórico
    session = requests.Session()
    try:
        # Faz a requisição com cabeçalhos personalizados
        response = session.get(url, headers=headers, timeout=5, allow_redirects=True)
        
        # Exibe o status final primeiro (200, se aplicável)
        final_status = response.status_code
        final_msg = status_messages.get(final_status, "STATUS DESCONHECIDO")
        if final_status == 200:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{final_status} - {final_msg} -> {response.url}")
        
        # Itera sobre o histórico de redirecionamentos (se houver)
        if response.history:
            for redirect in response.history:
                status_msg = status_messages.get(redirect.status_code, "STATUS DESCONHECIDO")
                location = redirect.headers.get("Location", "Nenhum Location encontrado")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n{redirect.status_code} - {status_msg} -> {location}")
        
    except requests.exceptions.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao acessar a URL: {e}")
        return

# Função principal
def main():
    url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite o nome ou a URL do site (exemplo: example.com ou https://example.com): ").strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    verificar_open_redirect(url)
    get_domain_info(url)

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
