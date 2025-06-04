import requests
from colorama import init, Fore, Style

# Inicializando o colorama
init(autoreset=True)

# Banner do script
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
 ██████╗ ██████╗ ██╗     ██╗     ███████╗ ██████╗████████╗    ██╗  ██╗████████╗████████╗██████╗ 
██╔════╝██╔═══██╗██║     ██║     ██╔════╝██╔════╝╚══██╔══╝    ██║  ██║╚══██╔══╝╚══██╔══╝██╔══██╗
██║     ██║   ██║██║     ██║     █████╗  ██║        ██║       ███████║   ██║      ██║   ██████╔╝
██║     ██║   ██║██║     ██║     ██╔══╝  ██║        ██║       ██╔══██║   ██║      ██║   ██╔═══╝ 
╚██████╗╚██████╔╝███████╗███████╗███████╗╚██████╗   ██║       ██║  ██║   ██║      ██║   ██║     
 ╚═════╝ ╚═════╝ ╚══════╝╚══════╝╚══════╝ ╚═════╝   ╚═╝       ╚═╝  ╚═╝   ╚═╝      ╚═╝   ╚═╝

""")

def analisar_headers(url, headers, numero_agente):
    try:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n[→] Enviando requisição com User-Agent {numero_agente}: {headers['User-Agent']}")
        response = requests.get(url, headers=headers, timeout=10)

        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\n[✓] Status Code: {response.status_code} ({response.reason})")

        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n[-] Cabeçalhos HTTP Recebidos\n" + "-" * 100)
        for header, valor in response.headers.items():
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{header:<30}: {valor}")
        print("-" * 100)

        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\n[🔒] Análise de Segurança dos Cabeçalhos\n" + "-" * 100)

        cabecalhos_segurança = {
            "Content-Security-Policy": "Protege contra XSS e injeções.",
            "X-Frame-Options": "Evita clickjacking.",
            "X-Content-Type-Options": "Previne MIME-sniffing.",
            "Strict-Transport-Security": "Impõe HTTPS."
        }

        ausentes = 0

        for chave, descricao in cabecalhos_segurança.items():
            if chave in response.headers:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT +  f"[✔] {chave:<30} → Presente ({descricao})")
            else:
                ausentes += 1
                print(Fore.LIGHTRED_EX + Style.BRIGHT + f"[✖] {chave:<30} → Ausente  ❌ ({descricao})")

        print("-" * 100)

        # Avaliação de vulnerabilidade baseada nos cabeçalhos ausentes
        if ausentes == 0:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n[✔] O site está seguro em relação aos cabeçalhos HTTP de segurança analisados.\n")
        elif ausentes <= 2:
            print(Fore.YELLOW + Style.BRIGHT + f"\n[!] Atenção: O site está moderadamente vulnerável. Faltam {ausentes} cabeçalhos de segurança importantes.\n")
        else:
            print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\n[✖] ALERTA: O site está altamente vulnerável! Faltam {ausentes} cabeçalhos essenciais para segurança.\n")

    except requests.RequestException as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\n[!] Erro ao conectar: {e}")

if __name__ == "__main__":
    url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL para análise de cabeçalhos (Ex: https://exemplo.com): ").strip()
    if not url.startswith("http"):
        url = "https://" + url

    headers1 = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Accept": "text/html",
        "Connection": "close"
    }

    headers2 = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    analisar_headers(url, headers1, "1")
    analisar_headers(url, headers2, "2")

input(Fore.LIGHTRED_EX + "\n\n  ========== PRESSIONE ENTER PARA SAIR ==========\n")
