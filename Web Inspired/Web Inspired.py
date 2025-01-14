import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import locale
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

██╗    ██╗███████╗██████╗     ██╗███╗   ██╗███████╗██████╗ ██╗██████╗ ███████╗██████╗ 
██║    ██║██╔════╝██╔══██╗    ██║████╗  ██║██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔══██╗
██║ █╗ ██║█████╗  ██████╔╝    ██║██╔██╗ ██║███████╗██████╔╝██║██████╔╝█████╗  ██║  ██║
██║███╗██║██╔══╝  ██╔══██╗    ██║██║╚██╗██║╚════██║██╔═══╝ ██║██╔══██╗██╔══╝  ██║  ██║
╚███╔███╔╝███████╗██████╔╝    ██║██║ ╚████║███████║██║     ██║██║  ██║███████╗██████╔╝
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝ 

""")                                                                                     


# Configuração para exibir a data em português do Brasil
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

# Reconfigurar a codificação de saída para latin-1
sys.stdout.reconfigure(encoding='latin-1')

# Função para formatar a data
def formatar_data(data):
    try:
        data_obj = datetime.strptime(data, "%Y-%m-%d")
        nome_dia = data_obj.strftime("%A")  # Nome do dia (ex: Segunda-feira)
        nome_mes = data_obj.strftime("%B")  # Nome do mês (ex: Janeiro)
        ano = data_obj.year  # Ano
        return f"{nome_dia}, {data_obj.day} de {nome_mes} de {ano}", data_obj.strftime("%Y-%m-%d")
    except ValueError:
        return "N/A", "N/A"

def consulta_whois_br(domain):
    url = f"https://rdap.registro.br/domain/{domain}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            whois_info = {
                "dominio": data.get("ldhName", "N/A"),
                "proprietario": data.get("entities", [{}])[0].get("vcardArray", [[], [["text", "N/A"]]])[1][0][3],
                "criado_em": formatar_data(data.get("events", [{}])[0].get("eventDate", "N/A").split("T")[0]),
                "alterado_em": formatar_data(data.get("events", [{}])[1].get("eventDate", "N/A").split("T")[0]),
                "expira_em": formatar_data(data.get("events", [{}])[2].get("eventDate", "N/A").split("T")[0]),
            }
            return whois_info
        else:
            return f"Erro: Não foi possível consultar informações para {domain}."
    except Exception as e:
        return f"Erro ao consultar WHOIS no registro.br: {e}"

def consulta_whois_com(domain):
    url = f"https://www.whois.com/whois/{domain}"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        whois_info = {}
        whois_data = soup.find_all("div", class_="df-raw")

        for item in whois_data:
            label = item.find_previous("div", class_="df-label").get_text(strip=True)
            value = item.get_text(strip=True)
            whois_info[label] = value

        # Mapeando traduções para português
        translated_info = {
            "creation_date": formatar_data(whois_info.get("Creation Date:",  "N/A")),
            "expiration_date": formatar_data(whois_info.get("Registrar Registration Expiration Date:",  "N/A")),
            "updated_date": formatar_data(whois_info.get("Updated Date:",  "N/A")),
            "registrar": whois_info.get("Registrar:",  "N/A"),
        }

        return translated_info

    except Exception as e:
        return f"Erro ao consultar WHOIS no whois.com: {e}"

def consulta_whois(domain):
    if domain.endswith(".br"):
        return consulta_whois_br(domain)
    else:
        return consulta_whois_com(domain)

def main():
    domain = input(Fore.LIGHTCYAN_EX + 'Digite o nome do website (exemplo: example.com ou example.com.br): ')

    whois_info = consulta_whois(domain)

    if isinstance(whois_info, dict):
        print(Fore.GREEN + Style.BRIGHT + f"\n\nDominio: {whois_info.get('dominio',  'N/A')}")
        registrado, registrado_iso = whois_info.get('criado_em',  ('N/A', 'N/A'))
        expira, expira_iso = whois_info.get('expira_em', ('N/A',  'N/A'))
        modificado, modificado_iso = whois_info.get('alterado_em',  ('N/A', 'N/A'))
        
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nRegistrado: {registrado:<50}Registrado: {registrado_iso}")
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nExpira: {expira:<55}Expira: {expira_iso}")
        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nModificado: {modificado:<50} Modificado: {modificado_iso}")
     
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + whois_info)

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT +"\n\n\n\n========== PRESSIONE ENTER PARA SAIR ==========" + "\n\n")
