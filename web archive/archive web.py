import requests  # Biblioteca para realizar requisições HTTP
import time

print(""" 

 █████╗ ██████╗  ██████╗██╗  ██╗██╗██╗   ██╗███████╗    ██╗    ██╗███████╗██████╗ 
██╔══██╗██╔══██╗██╔════╝██║  ██║██║██║   ██║██╔════╝    ██║    ██║██╔════╝██╔══██╗
███████║██████╔╝██║     ███████║██║██║   ██║█████╗      ██║ █╗ ██║█████╗  ██████╔╝
██╔══██║██╔══██╗██║     ██╔══██║██║╚██╗ ██╔╝██╔══╝      ██║███╗██║██╔══╝  ██╔══██╗
██║  ██║██║  ██║╚██████╗██║  ██║██║ ╚████╔╝ ███████╗    ╚███╔███╔╝███████╗██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝     ╚══╝╚══╝ ╚══════╝╚═════╝ 
                                                                           
""")

def waybackurls(host):
    url = f'http://web.archive.org/cdx/search/cdx?url={host}/*&output=json&fl=original&collapse=urlkey'
    
    print("\nConectando ao Internet Archive e obtendo dados...\n")
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Erro ao acessar o Internet Archive.")
        return []
    
    results = response.json()
    
    if len(results) <= 1:
        print("Nenhuma URL encontrada.")
        return []
    
    urls = []
    
    print("\nProcessando URL\n")
    for item in results[1:]:
        urls.append(item[0])
        time.sleep(0.001)  # Atraso de 0.001 segundos para cada atualização, opcional
    
    return urls

def main():
    website_url = input("Digite a URL completa do website (ex: https://exemplo.com.br): ")
    
    urls = waybackurls(website_url)
    
    if urls:
        print(f"\nTotal de URL Encontradas: {len(urls)}\n")
        # Atraso de 3 segundos antes de mostrar as URLs
        time.sleep(3)
        for url in urls:
            print(url)
    else:
        print("Nenhuma URL encontrada ou erro ao acessar o Internet Archive.")

    save_option = input("\n\n\nDeseja salvar os resultados? (s/n): ").strip().lower()
    if save_option == 's':
        file_name = input("\nDigite o nome do arquivo (ex: arquivo.txt): ").strip()
        try:
            with open(file_name, 'w', encoding='utf-8') as file:  # Adicione a codificação aqui
                file.write(f"URL Encontradas para: {website_url} ({len(urls)} URL Encontradas)\n\n")
                for url in urls:
                    file.write(url + '\n')
            print(f"\nResultados salvos Em: {file_name}")
        except Exception as e:
            print(f"\nErro ao salvar o arquivo: {e}")

if __name__ == "__main__":  
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
