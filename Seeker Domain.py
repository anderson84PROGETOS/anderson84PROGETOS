import requests
from bs4 import BeautifulSoup
import re
import random

print("""

███████╗███████╗███████╗██╗  ██╗███████╗██████╗     ██████╗  ██████╗ ███╗   ███╗ █████╗ ██╗███╗   ██╗
██╔════╝██╔════╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗    ██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██║████╗  ██║
███████╗█████╗  █████╗  █████╔╝ █████╗  ██████╔╝    ██║  ██║██║   ██║██╔████╔██║███████║██║██╔██╗ ██║
╚════██║██╔══╝  ██╔══╝  ██╔═██╗ ██╔══╝  ██╔══██╗    ██║  ██║██║   ██║██║╚██╔╝██║██╔══██║██║██║╚██╗██║
███████║███████╗███████╗██║  ██╗███████╗██║  ██║    ██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║██║██║ ╚████║
╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝    ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
                                                                                                                                  
""")

def uso():
    print("Extrai hosts/subdomínios, IP ou emails para um domínio específico com pesquisa Google.")
    print()
    print("Uso: python Subdomain.py3")
    exit(1)

def obter_resultado(conteudo, regexpresultado):
    resultado = re.findall(regexpresultado, conteudo)
    return int(resultado[0].replace(",", "")) if resultado else 0

def consulta_google(dominio, paginas=20, verbosidade=False):
    tmprnd = str(random.randint(1000, 9999))
    resultados = []
    regexpresultado = 'Results <b>[0-9,]*</b> - <b>[0-9,]*</b> of[" about "]+<b>[0-9,]*</b>'

    regexpconsulta = f'[a-zA-Z0-9\\._-]+\\.{dominio}|[a-zA-Z0-9._-]+@<em>{dominio}</em>'
    print("\n")
    consulta_base = f"\n\nhttp://www.google.com/search?num=100&q=site%3A{dominio}"

    for i in range(paginas):
        if i == 0:
            consulta = consulta_base
        else:
            consulta = f"\n{consulta_base}&start={i*100}"

        resposta = requests.get(consulta, headers={"User-Agent": "Mozilla/5.0"})
        conteudo = resposta.text
        
        if verbosidade:
        
            print(f"\nConsultando página: {i + 1} {consulta}\n")

        sopa = BeautifulSoup(conteudo, 'html.parser')
        for link in sopa.find_all('a', href=True):
            correspondencia = re.search(regexpconsulta, link['href'])
            if correspondencia:
                resultados.append(correspondencia.group(0))

        if obter_resultado(conteudo, regexpresultado) < 100:
            break

    resultados = list(set(resultados))
    print(f"\nAchou {len(resultados)} resultados únicos\n")
    for resultado in resultados:
        print(resultado)

    salvar = input(f"\nDeseja salvar os resultados em um arquivo? (s/n): ").strip().lower()
    if salvar == 's' or salvar == 'sim':
        nome_arquivo = input("\nDigite o nome do arquivo para salvar (com a extensão.txt): ").strip()
        with open(f'{nome_arquivo}.txt', 'w') as f:
            for resultado in resultados:
                f.write(f"{resultado}\n")
        print(f"\nResultados salvos Em: {nome_arquivo}.txt")
    else:
        print("\nResultados não foram salvos.")

if __name__ == "__main__":
    # Este script permite extrair hosts/subdomínios, IPs ou emails para um domínio específico usando pesquisa do Google.")    
    
    dominio = input("\nDigite o domínio alvo (exemplo: example.com): ").strip()
    verbosidade = True  # Verbosidade ativada por padrão

    consulta_google(dominio, paginas=20, verbosidade=verbosidade)

input("\n\n\nPRESSIONE ENTER PARA SAIR\n=========================\n\n")
