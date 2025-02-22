import requests
from bs4 import BeautifulSoup
import webbrowser
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
 ██████╗  ██████╗  ██████╗  ██████╗ ██╗     ███████╗    ██╗  ██╗ █████╗  ██████╗██╗  ██╗███████╗██████╗ 
██╔════╝ ██╔═══██╗██╔═══██╗██╔════╝ ██║     ██╔════╝    ██║  ██║██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██║  ███╗██║   ██║██║   ██║██║  ███╗██║     █████╗      ███████║███████║██║     █████╔╝ █████╗  ██████╔╝
██║   ██║██║   ██║██║   ██║██║   ██║██║     ██╔══╝      ██╔══██║██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
╚██████╔╝╚██████╔╝╚██████╔╝╚██████╔╝███████╗███████╗    ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
 ╚═════╝  ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝╚══════╝    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝

""")

def construir_consulta_dork(site_nome, dork_selecionada):
    consultas = {
        "Publicly exposed documents": f"site:{site_nome} ext:doc | ext:docx | ext:odt | ext:rtf | ext:sxw | ext:psw | ext:ppt | ext:pptx | ext:pps | ext:csv",
        "Directory listing vulns": f"site:{site_nome} intitle:index.of",
        "Configuration files exposed": f"site:{site_nome} ext:xml | ext:conf | ext:cnf | ext:reg | ext:inf | ext:rdp | ext:cfg | ext:txt | ext:ora | ext:ini | ext:env",
        "Database files exposed": f"site:{site_nome} ext:sql | ext:dbf | ext:mdb",
        "Log files exposed": f"site:{site_nome} ext:log",
        "Backup and old files": f"site:{site_nome} ext:bkf | ext:bkp | ext:bak | ext:old | ext:backup",
        "Login pages": f"site:{site_nome} inurl:login | inurl:signin | intitle:Login | intitle:\"sign in\" | inurl:auth",
        "SQL errors": f"site:{site_nome} intext:\"sql syntax near\" | intext:\"syntax error has occurred\" | intext:\"incorrect syntax near\" | intext:\"unexpected end of SQL command\" | intext:\"Warning: mysql_connect()\" | intext:\"Warning: mysql_query()\" | intext:\"Warning: pg_connect()\"",
        "PHP errors/warnings": f"site:{site_nome} \"PHP Parse error\" | \"PHP Warning\" | \"PHP Error\"",
        "phpinfo()": f"site:{site_nome} ext:php intitle:phpinfo \"published by the PHP Group\"",
        "Search pastebin.com / pasting sites": f"site:pastebin.com | site:paste2.org | site:pastehtml.com | site:slexy.org | site:snipplr.com | site:snipt.net | site:textsnip.com | site:bitpaste.app | site:justpaste.it | site:heypasteit.com | site:hastebin.com | site:dpaste.org | site:dpaste.com | site:codepad.org | site:jsitor.com | site:codepen.io | site:jsfiddle.net | site:dotnetfiddle.net | site:phpfiddle.org | site:ide.geeksforgeeks.org | site:repl.it | site:ideone.com | site:paste.debian.net | site:paste.org | site:paste.org.ru | site:codebeautify.org  | site:codeshare.io | site:trello.com {site_nome}",
        "Search github.com and gitlab.com": f"site:github.com | site:gitlab.com {site_nome}",
        "Search stackoverflow.com": f"site:stackoverflow.com {site_nome}",
        "Signup pages": f"site:{site_nome} inurl:signup | inurl:register | intitle:Signup",
        "Find Subdomains": f"site:*.{site_nome}",
        "Find Sub-Subdomains": f"site:*.*.{site_nome}",
        "Search in Wayback Machine": f"https://web.archive.org/web/*/{site_nome}/*",
        "Show only IP addresses (opens multiple tabs)": f"({site_nome}) (site:*.*.29.* | site:*.*.28.* | site:*.*.27.* | site:*.*.26.* | site:*.*.25.* | site:*.*.24.* | site:*.*.23.* | site:*.*.22.* | site:*.*.21.* | site:*.*.20.* | site:*.*.19.* | site:*.*.18.* | site:*.*.17.* | site:*.*.16.* | site:*.*.15.* | site:*.*.14.* | site:*.*.13.* | site:*.*.12.* | site:*.*.11.* | site:*.*.10.* | site:*.*.9.* | site:*.*.8.* | site:*.*.7.* | site:*.*.6.* | site:*.*.5.* | site:*.*.4.* | site:*.*.3.* | site:*.*.2.* | site:*.*.1.* | site:*.*.0.*)",
        "Para encontrar documentos Apresentaçoes e desenhos vazados": f"site:docs.{site_nome}/document/d",
        "Para encontrar presentation": f"site:docs.{site_nome}/presentation/d",
        "Para encontrar drawings": f"site:docs.{site_nome}/drawings/d",
        "Já para encontrar qualquer tipo de arquivo como imagens vídeos zip e PDF": f"site:docs.{site_nome}/file/d",
        "Agora se você quer encontrar uma pasta completa do Google Drive exposta": f"site:docs.{site_nome}/folder/d",
        "Esses para achar itens secreto": f"site:docs.{site_nome}/open intext:secreto",
        "achar inurl e index.php": f'"{site_nome}" + inurl=index.php?id=1',
        "achar arquivo pdf": f"site:{site_nome} ext:pdf",
        "achar arquivo xml": f"site:{site_nome} ext:xml",
        "achar arquivo docx": f"site:{site_nome} ext:docx",
        "achar arquivo intext":f"intext:{site_nome}",
        "achar arquivo txt senha url": f"filetype:txt intext:senha url site:{site_nome}",       
        "achar Arquivo nos Servidores do Scribd": f"servidores site:scribd.com AND:{site_nome}",
        "achar arquivo sql aperte a tecla espaço ou nome do site": f"{site_nome} filetype:sql",
        "achar arquivo env": f"filetype:env {site_nome}",
        "Achar arquivo inurl": f"inurl:{site_nome}",
        "Achar arquivo pdf xlsx docx txt": f"'{site_nome}' filetype:pdf OR filetype:xlsx OR filetype:docx OR filetype:txt",
        "Achar arquivo txt": f"site:{site_nome} filetype:txt",
        "Achar arquivo WEBCAM 7 Aperte Espasso": f"{site_nome} intitle:\"WEBCAM 7\" -inurl:/admin.html",
        "Achar arquivo robots.txt": f"{site_nome} robots.txt",
        "Achar arquivo senha": f"intitle:\"index of\" intext:{site_nome}",
        "Achar nome de pessoa": f'intext:"{site_nome}"',
        "Nome do IP": f'IP:{site_nome}',
        "Achar arquivo pdf confidencial": f'filetype:pdf intitle:confidencial site:{site_nome}',
        "Confidencial": f'intitle:confidencial filetype:pdf intext:"{site_nome}"',
        "Achar credit card": f'site:pastebin.com {site_nome} credit card',
        "Achar coisas em google drive": f'site:drive.google.com {site_nome}',
        "Achar email": f'"{site_nome}"',
        "Login -Painel": 'site:itau.com.br intitle:Login -Painel',
    }
    return consultas.get(dork_selecionada, "")

def obter_dados_hacking():
    site_nome = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Insira o nome para pesquisar ou o nome do website: ").strip()
    if not site_nome:
        print("Por favor, insira o nome do site.")
        return

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nSelecione uma Dork\n")
    dorks = [
        "Publicly exposed documents",
        "Directory listing vulns",
        "Configuration files exposed",
        "Database files exposed",
        "Log files exposed",
        "Backup and old files",
        "Login pages",
        "SQL errors",
        "PHP errors/warnings",
        "phpinfo()",
        "Search pastebin.com / pasting sites",
        "Search github.com and gitlab.com",
        "Search stackoverflow.com",
        "Signup pages",
        "Find Subdomains",
        "Find Sub-Subdomains",
        "Search in Wayback Machine",
        "Show only IP addresses (opens multiple tabs)",
        "Para encontrar documentos Apresentaçoes e desenhos vazados",
        "Para encontrar presentation",
        "Para encontrar drawings",
        "Já para encontrar qualquer tipo de arquivo como imagens vídeos zip e PDF",
        "Agora se você quer encontrar uma pasta completa do Google Drive exposta",
        "Esses para achar itens secreto",
        "achar inurl e index.php",
        "achar arquivo pdf",
        "achar arquivo xml",
        "achar arquivo docx",
        "achar arquivo intext",
        "achar arquivo txt senha url",
        "achar Arquivo nos Servidores do Scribd",
        "achar arquivo sql aperte a tecla espaço ou nome do site",
        "achar arquivo env",
        "Achar arquivo inurl",
        "Achar arquivo pdf xlsx docx txt",
        "Achar arquivo txt",
        "Achar arquivo WEBCAM 7 Aperte Espasso",
        "Achar arquivo robots.txt",
        "Achar arquivo senha",
        "Achar nome de pessoa",
        "Nome do IP",
        "Achar arquivo pdf confidencial",
        "Confidencial",
        "Achar credit card",
        "Achar coisas em google drive",
        "Achar email",
        "Login -Painel",
    ]

    for idx, dork in enumerate(dorks, 1):
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{idx}. {dork}")

    dork_selecionada = input(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nEscolha o número da Dork: ").strip()
    
    if not dork_selecionada.isdigit() or not (1 <= int(dork_selecionada) <= len(dorks)):
        print("Dork inválida. Tente novamente.")
        return

    dork_selecionada = dorks[int(dork_selecionada) - 1]
    consulta_dork = construir_consulta_dork(site_nome, dork_selecionada)
    
    if consulta_dork:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\nConsultando: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f" {consulta_dork}")
        
        # Realizar a pesquisa no Google
        search_url = f"https://www.google.com/search?q={consulta_dork}"
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

        try:
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()  # Lança um erro se a resposta for inválida            

            # Abertura automática do Google
            motor_pesquisa = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n\n\nDeseja abrir o Google com a consulta da dork selecionada? (s/n): ").strip().lower()
            print("\n")
            if motor_pesquisa == "s":
                # Cria a URL para pesquisa
                url = f"https://www.google.com/search?q={consulta_dork.replace(' ', '+')}"
                
                # Abre a URL de pesquisa no Google
                webbrowser.open(url)                
                print(Fore.LIGHTCYAN_EX + Style.BRIGHT + f"\nAbrindo o Google com a Consulta: " + Fore.LIGHTGREEN_EX + Style.BRIGHT + f"{consulta_dork}")
            elif motor_pesquisa == "n":
                pass         
                
        except requests.exceptions.RequestException as e:
            print(f"\nErro ao realizar a pesquisa: {e}")
    else:
        print("\nNenhuma consulta dork encontrada.")

# Chamar a função para testar
obter_dados_hacking()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
