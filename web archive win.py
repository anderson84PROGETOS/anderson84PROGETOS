import requests

print("""

██╗    ██╗███████╗██████╗      █████╗ ██████╗  ██████╗██╗  ██╗██╗██╗   ██╗███████╗    ██╗    ██╗██╗███╗   ██╗
██║    ██║██╔════╝██╔══██╗    ██╔══██╗██╔══██╗██╔════╝██║  ██║██║██║   ██║██╔════╝    ██║    ██║██║████╗  ██║
██║ █╗ ██║█████╗  ██████╔╝    ███████║██████╔╝██║     ███████║██║██║   ██║█████╗      ██║ █╗ ██║██║██╔██╗ ██║
██║███╗██║██╔══╝  ██╔══██╗    ██╔══██║██╔══██╗██║     ██╔══██║██║╚██╗ ██╔╝██╔══╝      ██║███╗██║██║██║╚██╗██║
╚███╔███╔╝███████╗██████╔╝    ██║  ██║██║  ██║╚██████╗██║  ██║██║ ╚████╔╝ ███████╗    ╚███╔███╔╝██║██║ ╚████║
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝     ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝
                                                                                                        
""")

def waybackurls(host, with_subs):
    if with_subs:
        url = 'http://web.archive.org/cdx/search/cdx?url=*.%s/*&output=json&fl=original&collapse=urlkey' % host
    else:
        url = 'http://web.archive.org/cdx/search/cdx?url=%s/*&output=json&fl=original&collapse=urlkey' % host
    r = requests.get(url)
    results = r.json()
    return [item[0] for item in results[1:]]  # Extrai apenas os URLs da lista de listas

if __name__ == '__main__':
    host = input("\nDigite o nome do website: ")
    with_subs_input = input("\nIncluir subdomínios? (s/n): ").strip().lower()
    with_subs = with_subs_input == 's'

    urls = waybackurls(host, with_subs)
    
    if urls:
        num_urls = len(urls)  # Conta o número de URLs encontradas
        print(f'\n[*] Foram Encontradas: {num_urls}  ===> URL\n')
        for url in urls:
            print(url)
        
        save_choice = input("\nDeseja salvar os URLs extraídos? (s/n): ").strip().lower()
        if save_choice == 's':
            filename = input("\nDigite o nome do arquivo para salvar (com extensão .txt): ").strip()
            with open(filename, 'w', encoding='utf-8') as f:  # Abrir o arquivo com o codec utf-8
                for url in urls:
                    f.write(url + '\n')
            print(f'\n[*] URLs extraídos salvos em: {filename}')
        else:
            print("\n[-] URLs não foram salvos.")
        
        # Mostrar os URLs novamente após salvar
        print('\n[*] URLs Extraídos [*]\n')
        for url in urls:
            print(url)
    else:
        print('\n[-] Nada Encontrado')

input("\n\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")  # Pausa antes de sair
