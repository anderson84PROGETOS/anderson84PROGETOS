import requests
from colorama import init, Fore, Style
from deep_translator import GoogleTranslator

# Inicializando o colorama
init(autoreset=True)

# Banner ASCII
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """

 ██████╗██╗   ██╗███████╗    ██╗███╗   ██╗███████╗ ██████╗ 
██╔════╝██║   ██║██╔════╝    ██║████╗  ██║██╔════╝██╔═══██╗
██║     ██║   ██║█████╗      ██║██╔██╗ ██║█████╗  ██║   ██║
██║     ╚██╗ ██╔╝██╔══╝      ██║██║╚██╗██║██╔══╝  ██║   ██║
╚██████╗ ╚████╔╝ ███████╗    ██║██║ ╚████║██║     ╚██████╔╝
 ╚═════╝  ╚═══╝  ╚══════╝    ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ 

""")

def buscar_cve_info(cve_id):
    url = f"https://cvedb.shodan.io/cve/CVE-{cve_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao acessar {url} (Status Code: {response.status_code})")
        return

    try:
        data = response.json()
    except ValueError:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "Erro ao interpretar a resposta como JSON.")
        return

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nInformações para: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{cve_id}\n")

    # Descrição em inglês
    descricao = data.get("summary", "Descrição não disponível.")
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nDescrição Original (Inglês)\n")
    print(Fore.LIGHTCYAN_EX + descricao)

    # Descrição traduzida
    try:
        descricao_pt = GoogleTranslator(source='auto', target='pt').translate(descricao)
    except Exception as e:
        descricao_pt = "Erro na tradução automática."
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"Erro ao traduzir: {e}")

    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDescrição Traduzida (Português-BR)\n")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + descricao_pt + "\n")

    # Pontuação CVSS
    cvss_score = data.get("cvss", "Pontuação CVSS não disponível.")
    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nPontuação CVSS: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{cvss_score}")

    # Classificação de severidade com base na pontuação CVSS
    try:
        score = float(cvss_score)
        if score == 0.0:
            nivel = "Sem impacto"
            cor = Fore.WHITE
        elif score <= 3.9:
            nivel = "Baixo"
            cor = Fore.LIGHTCYAN_EX + Style.BRIGHT
        elif score <= 6.9:
            nivel = "Médio"
            cor = Fore.LIGHTYELLOW_EX + Style.BRIGHT
        elif score <= 8.9:
            nivel = "Alto"
            cor = Fore.LIGHTRED_EX + Style.BRIGHT 
        else:
            nivel = "Crítico"
            cor = Fore.LIGHTMAGENTA_EX + Style.BRIGHT
        print(cor + Style.BRIGHT + f"\nNível de Severidade: {nivel}\n")
    except:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + + "\nNível de Severidade: Indefinido\n")

    # Referências formatadas apenas com número e link
    referencias = data.get("references", [])
    referencias_unicas = sorted(set(referencias))

    if referencias_unicas:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nReferências externas\n")
        for i, ref in enumerate(referencias_unicas, start=1):
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{i} = {ref}")
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "-" * 75)
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + + "Nenhuma referência encontrada.")

if __name__ == "__main__":
    cve = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a CVE (ex: 2006-3530): ").strip().upper()
    buscar_cve_info(cve)

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
