import requests
import json

print(r"""            

    ███████╗██╗   ██╗██████╗ ███████╗     ██████╗██████╗ ████████╗
    ██╔════╝██║   ██║██╔══██╗██╔════╝    ██╔════╝██╔══██╗╚══██╔══╝
    ███████╗██║   ██║██████╔╝███████╗    ██║     ██████╔╝   ██║   
    ╚════██║██║   ██║██╔══██╗╚════██║    ██║     ██╔══██╗   ██║   
    ███████║╚██████╔╝██████╔╝███████║    ╚██████╗██║  ██║   ██║   
    ╚══════╝ ╚═════╝ ╚═════╝ ╚══════╝     ╚═════╝╚═╝  ╚═╝   ╚═╝   
                                                                                      
""")     

alvo = input("\nDigite o nome do WebSite: ").rstrip()

print("\n🔎 Coletando Informações. Aguarde 🔍\n")

req = requests.get("https://crt.sh/?q=%.{d}&output=json".format(d=alvo))
dados = json.loads(req.text)

print("\nℹ️ Informações Encontradas ℹ️ \n")
numero_subdominios = len(dados)
for item in dados:
    print(item['name_value'])

escolha = input("\nDeseja Salvar as informações em um arquivo? (s/n): ").lower()

if escolha == 's':
    nome_arquivo = input("\nDigite o nome do arquivo para salvar as informações: ")
    with open(nome_arquivo, "w") as file:
        for item in dados:
            file.write(item['name_value'] + "\n")
    print(f"\n🔎 Informações Salvas no Arquivo '{nome_arquivo}' 🔍\n")
elif escolha == 'n':
    print("\n🔎 Informações não foram salvas. 🔍\n")
else:
    print("\nEscolha inválida. As informações não foram salvas.\n")

print(f"\nℹ️ Total de Subdomínios Encontrados: {numero_subdominios}\n")

input("\nDigite ENTER para sair\n")
