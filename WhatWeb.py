import json
import subprocess

print("""

██╗    ██╗██╗  ██╗ █████╗ ████████╗██╗    ██╗███████╗██████╗     
██║    ██║██║  ██║██╔══██╗╚══██╔══╝██║    ██║██╔════╝██╔══██╗    
██║ █╗ ██║███████║███████║   ██║   ██║ █╗ ██║█████╗  ██████╔╝    
██║███╗██║██╔══██║██╔══██║   ██║   ██║███╗██║██╔══╝  ██╔══██╗    
╚███╔███╔╝██║  ██║██║  ██║   ██║   ╚███╔███╔╝███████╗██████╔╝    
 ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚══╝╚══╝ ╚══════╝╚═════╝     
                                                                 
""")

def run_whatweb(website):
    json_file = f"{website}_log.json"
    command = f"whatweb -a 3 -v --log-json {json_file} {website}"
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print("Erro ao executar o WhatWeb. Verifique se o WhatWeb está instalado e acessível.")
        exit(1)
    return json_file

def display_results(json_file):
    try:
        with open(json_file, 'r') as infile:
            data = json.load(infile)
            for entry in data:
                url = entry.get("http", {}).get("url", "")
                plugins = entry.get("plugins", {})
                print(f"URL: {url}")
                for plugin, results in plugins.items():
                    print(f"  Plugin: {plugin}")
                    for result in results:
                        print(f"    Result: {result}")
                print()
    except FileNotFoundError:
        print(f"Arquivo {json_file} não encontrado. Certifique-se de que o WhatWeb foi executado corretamente.")
        exit(1)

if __name__ == "__main__":
    website = input("\nDigite o nome do website: ")
    print()
    json_file = run_whatweb(website)
    
    print("Resultados:")
    display_results(json_file)
