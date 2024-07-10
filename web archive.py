import requests
import json
import os

print("""

██╗    ██╗███████╗██████╗      █████╗ ██████╗  ██████╗██╗  ██╗██╗██╗   ██╗███████╗
██║    ██║██╔════╝██╔══██╗    ██╔══██╗██╔══██╗██╔════╝██║  ██║██║██║   ██║██╔════╝
██║ █╗ ██║█████╗  ██████╔╝    ███████║██████╔╝██║     ███████║██║██║   ██║█████╗  
██║███╗██║██╔══╝  ██╔══██╗    ██╔══██║██╔══██╗██║     ██╔══██║██║╚██╗ ██╔╝██╔══╝  
╚███╔███╔╝███████╗██████╔╝    ██║  ██║██║  ██║╚██████╗██║  ██║██║ ╚████╔╝ ███████╗
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝
                                                                                  
""")

def waybackurls(host, with_subs):
    if with_subs:
        url = 'http://web.archive.org/cdx/search/cdx?url=*.%s/*&output=json&fl=original&collapse=urlkey' % host
    else:
        url = 'http://web.archive.org/cdx/search/cdx?url=%s/*&output=json&fl=original&collapse=urlkey' % host
    r = requests.get(url)
    results = r.json()
    return results[1:]

if __name__ == '__main__':
    host = input("\nDigite o nome do website: ")
    with_subs_input = input("\nIncluir subdomínios? (s/n): ").strip().lower()
    with_subs = with_subs_input == 's'

    urls = waybackurls(host, with_subs)
    json_urls = json.dumps(urls)
    
    if urls:
        num_urls = len(urls)  # Conta o número de URLs encontradas
        print(f'\n[*] Foram Encontradas: {num_urls}  ===> URL\n')
        for url in urls:
            print(url)
        
        filename = '%s-waybackurls.json' % host
        with open(filename, 'w') as f:
            f.write(json_urls)
        print('\n[*] Resultados salvos Em: %s' % filename)
        
        # Perguntar se deseja salvar os URLs extraídos
        save_choice = input("\n\nDeseja salvar os URLs extraídos? (s/n): ").strip().lower()
        if save_choice == 's':
            output_filename = input("\nDigite o nome do arquivo para salvar (com extensão .txt): ").strip()
            grep_command = f"grep -Poi '\\[\"\\K.*?(?=\")' {filename} | sort | uniq > {output_filename}"
            os.system(grep_command)
            print('\n[*] URLs extraídos salvos Em: %s' % output_filename)
            # Mostrar os URLs novamente após salvar
            print('\n[*] URLs Extraídos [*]\n')
            with open(output_filename, 'r') as f:
                for line in f:
                    print(line.strip())
    else:
        print('\n[-] Nada Encontrado')
