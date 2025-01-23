import requests
import dns.resolver
from colorama import Fore, Style, init
from datetime import datetime

# Inicializando o colorama
init(autoreset=True)

print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
 _ __,   ___ __,  _,  _, _,_ __, __,    _, __,  _, _,   _,  _,  _, ___ _  _, _, _ 
 | |_)    |  |_) /_\ / ` |_/ |_  |_)   / _ |_  / \ |   / \ / ` /_\  |  | / \ |\ |
 | |      |  | \ | | \ , | \ |   | \   \ / |   \ / | , \ / \ , | |  |  | \ / | \|
 ~ ~      ~  ~ ~ ~ ~  ~  ~ ~ ~~~ ~ ~    ~  ~~~  ~  ~~~  ~   ~  ~ ~  ~  ~  ~  ~  ~
""")

def obter_informacoes_ip(consulta):
    url = f"http://ip-api.com/json/{consulta}"
    try:
        resposta = requests.get(url, timeout=10)
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados.get("status") == "success":
                # Exibindo informações principais
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Endereço IP     >   {dados.get('query')}")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Código do País  >   {dados.get('countryCode')}")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"País            >   {dados.get('country')}")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Data & Hora     >   {get_current_datetime()}")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Código Região   >   {dados.get('region')}")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Região          >   {dados.get('regionName')}")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Cidade          >   {dados.get('city')}")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Zip code        >   {dados.get('zip')}")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Fuso Horário    >   {dados.get('timezone')}")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"ISP             >   {dados.get('isp')}")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"Organização     >   {dados.get('org')}")
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"ASN             >   {dados.get('as')}")

                # Obtendo latitude e longitude
                latitude = dados.get('lat')
                longitude = dados.get('lon')
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Latitude        >   {Fore.LIGHTGREEN_EX + Style.BRIGHT + str(latitude)}")
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Longitude       >   {Fore.LIGHTGREEN_EX + Style.BRIGHT + str(longitude)}")
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"Localização     >   {Fore.LIGHTGREEN_EX + Style.BRIGHT + str(latitude)},{str(longitude)}")

                # Gerando URLs do Google Maps e Street View
                google_maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
                street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}&heading=-45&pitch=38&fov=80"

                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nGoogle Maps: {Fore.LIGHTGREEN_EX + Style.BRIGHT + google_maps_url}")
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + f"\nStreet View: {Fore.LIGHTGREEN_EX + Style.BRIGHT + street_view_url}")
            else:
                print(Fore.LIGHTRED_EX + "Não foi possível obter os dados para a consulta informada.")
        else:
            print(Fore.LIGHTRED_EX + f"Erro HTTP: {resposta.status_code}")
    except requests.exceptions.RequestException as e:
        print(Fore.LIGHTRED_EX + f"Erro: {e}")

# Função para obter a data e hora atual formatada
def get_current_datetime():
    # Obtendo data e hora atuais
    now = datetime.now()
    hour = now.hour
    # Definindo o período do dia
    if 5 <= hour < 12:
        period = "Manhã"
    elif 12 <= hour < 18:
        period = "Tarde"
    else:
        period = "Noite"
    
    # Dicionário de meses em português
    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    # Formatando a data e hora para o formato desejado (exemplo: janeiro 22, 2025, Horas: 20:30 noite)
    month_name = meses_pt[now.month]
    
    # Devolvendo a data e hora com a formatação desejada em maiúsculas
    return f"{month_name.upper()} {now.day},    ANO: {now.year},     HORAS: {now.strftime('%H:%M')}  {period.upper()}".upper()

# Resolvendo registros MX
def resolver_dns_mx(consulta):
    try:
        # Resolvendo registros MX (Mail Exchange)
        registros_mx = dns.resolver.resolve(consulta, 'MX')
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\n\nRegistros MX para: {consulta}\n")
        for rdata in registros_mx:
            # Resolvendo o IP do servidor de e-mail
            try:
                exchange_ip = dns.resolver.resolve(rdata.exchange, 'A')[0].address
                print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{str(rdata.exchange):<40} MX  IP: {exchange_ip}")

            except dns.resolver.NoAnswer:
                pass        
    except dns.exception.DNSException as e:
        pass

if __name__ == "__main__":
    consulta = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "ENTER PARA VER MEU IP ou Digite o endereço IP ou o nome do website: ").strip()
    print("\n")
    obter_informacoes_ip(consulta)
    resolver_dns_mx(consulta)
    
input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
