import requests
import json
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
██╗    ██╗ █████╗ ██╗   ██╗██████╗  █████╗  ██████╗██╗  ██╗    ███╗   ███╗ █████╗  ██████╗██╗  ██╗██╗███╗   ██╗███████╗
██║    ██║██╔══██╗╚██╗ ██╔╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝    ████╗ ████║██╔══██╗██╔════╝██║  ██║██║████╗  ██║██╔════╝
██║ █╗ ██║███████║ ╚████╔╝ ██████╔╝███████║██║     █████╔╝     ██╔████╔██║███████║██║     ███████║██║██╔██╗ ██║█████╗  
██║███╗██║██╔══██║  ╚██╔╝  ██╔══██╗██╔══██║██║     ██╔═██╗     ██║╚██╔╝██║██╔══██║██║     ██╔══██║██║██║╚██╗██║██╔══╝  
╚███╔███╔╝██║  ██║   ██║   ██████╔╝██║  ██║╚██████╗██║  ██╗    ██║ ╚═╝ ██║██║  ██║╚██████╗██║  ██║██║██║ ╚████║███████╗
 ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝
                                                                                                                                                                                                     
""")

def search_wayback_machine(url):
    print(f"\nBuscando URL para: {url}")
    response = requests.get(
        f"http://web.archive.org/cdx/search/cdx?url=*.{url}/*&output=json&fl=timestamp,original&collapse=urlkey"
    )

    if response.status_code == 200:
        data = json.loads(response.text)
        total_entries = len(data) - 1  # Subtrai o cabeçalho
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\nTotal de URL Encontradas: {total_entries}")

        captured_urls = []
        for i, entry in enumerate(data):
            if i == 0:  # Ignora o cabeçalho do JSON
                continue

            timestamp = entry[0]
            formatted_time = f"{timestamp[:4]}   {timestamp[4:6]}/{timestamp[6:8]}  {timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:]}"
            captured_url = entry[1]
            formatted_entry = f"{formatted_time}    {captured_url}"
            captured_urls.append(formatted_entry)

        return captured_urls, total_entries
    else:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro: Não foi possível capturar as URLs. Código de status: {response.status_code}")
        return None, 0

def save_urls_to_file(captured_urls):
    if not captured_urls:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nNenhuma URL para salvar.")
        return

    file_path = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT +"\nDigite o nome do arquivo para salvar: ").strip()
    if not file_path:
        file_path = "captured_urls.txt"
    elif not file_path.endswith(".txt"):
        file_path += ".txt"

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(f"Foram capturadas: {len(captured_urls)} URL\n\n")
            file.write("\n\n".join(captured_urls))

        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + f"\nURL salvas com sucesso com Nome: {file_path}")
    except Exception as e:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + f"\nErro ao salvar o arquivo: {str(e)}")

def main():
    url = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Digite a URL do website (ex: example.com): ").strip()

    if not url:
        print(Fore.LIGHTRED_EX + Style.BRIGHT + "\nErro: Nenhuma URL fornecida.")
        return

    captured_urls, total_entries = search_wayback_machine(url)

    if captured_urls:
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nURL capturadas:\n")
        for url in captured_urls:
            print(Fore.LIGHTGREEN_EX + Style.BRIGHT + url)

        # Exibe o total antes de perguntar se deseja salvar
        print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"\n\nTotal de URL Encontradas: {total_entries}")

        save_choice = input(Fore.LIGHTYELLOW_EX + Style.BRIGHT + "\nDeseja salvar as URL em um arquivo? (s/n): ").lower()
        if save_choice == 's':
            save_urls_to_file(captured_urls)

    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\nPrograma finalizado.")

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
