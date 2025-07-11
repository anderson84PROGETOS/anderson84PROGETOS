import subprocess
from datetime import datetime
from colorama import init, Fore, Style
# Inicializa colorama
init(autoreset=True)

def banner():
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗██╗███╗   ██╗███████╗ ██████╗ 
██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝████╗ ████║██║████╗  ██║██╔════╝██╔═══██╗
███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██╔████╔██║██║██╔██╗ ██║█████╗  ██║   ██║
╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║██║██║╚██╗██║██╔══╝  ██║   ██║
███████║   ██║   ███████║   ██║   ███████╗██║ ╚═╝ ██║██║██║ ╚████║██║     ╚██████╔╝
╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ 
""")

def exibir_systeminfo_completo():
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n🔍 [INFO] Coletando dados do sistema com systeminfo\n")
    try:
        output = subprocess.check_output("systeminfo", shell=True, encoding="utf-8", errors="ignore")
        linhas_formatadas = []
        for linha in output.splitlines():
            if ":" in linha:
                partes = linha.split(":", 1)
                chave = partes[0].strip()
                valor = partes[1].strip()
                linhas_formatadas.append(f"{Fore.LIGHTYELLOW_EX + Style.BRIGHT + chave:<60} {Fore.LIGHTGREEN_EX + Style.BRIGHT + valor}")
            else:
                linhas_formatadas.append(Fore.LIGHTYELLOW_EX + Style.BRIGHT + linha.strip())
        
        texto_formatado = "\n".join(linhas_formatadas)
        print(texto_formatado)
        return output
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "Erro ao executar systeminfo:", e)
        return ""

def extrair_data_instalacao(systeminfo_texto):
    for linha in systeminfo_texto.splitlines():
        if "instalação" in linha.lower():
            partes = linha.split(":", 1)
            if len(partes) >= 2:
                data_str = partes[1].strip()
                try:
                    return datetime.strptime(data_str, "%d/%m/%Y, %H:%M:%S")
                except ValueError:
                    pass
    return None

def calcular_tempo_passado(data_inicio):
    agora = datetime.now()
    delta = agora - data_inicio
    dias = delta.days
    anos = dias // 365
    meses = (dias % 365) // 30
    dias_restantes = (dias % 365) % 30
    return f"{anos} anos, {meses} meses e {dias_restantes} dias"

def main():
    banner()
    texto = exibir_systeminfo_completo()
    data_instalacao = extrair_data_instalacao(texto)
    if data_instalacao:
        tempo = calcular_tempo_passado(data_instalacao)
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\n🗓️  Data de instalação do Windows : " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + data_instalacao.strftime('%d/%m/%Y %H:%M:%S'))
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "⏳ Tempo desde a instalação       : " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + tempo)

if __name__ == "__main__":
    main()
input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
