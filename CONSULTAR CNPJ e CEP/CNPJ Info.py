import re
import requests
from datetime import datetime

print("""

 ██████╗███╗   ██╗██████╗      ██╗    ██╗███╗   ██╗███████╗ ██████╗ 
██╔════╝████╗  ██║██╔══██╗     ██║    ██║████╗  ██║██╔════╝██╔═══██╗
██║     ██╔██╗ ██║██████╔╝     ██║    ██║██╔██╗ ██║█████╗  ██║   ██║
██║     ██║╚██╗██║██╔═══╝ ██   ██║    ██║██║╚██╗██║██╔══╝  ██║   ██║
╚██████╗██║ ╚████║██║     ╚█████╔╝    ██║██║ ╚████║██║     ╚██████╔╝
 ╚═════╝╚═╝  ╚═══╝╚═╝      ╚════╝     ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ 
                                                                  
""")

print("\nMais informações acesse o website: https://www.informecadastral.com.br\n")

# Cabeçalhos globais para evitar bloqueios
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'application/json'
}

def limpar_cep(cep):
    """
    Remove caracteres que não são dígitos de um CEP.
    """
    return re.sub(r'\D', '', cep)

def consultar_cnpj(cnpj):
    """
    Consulta informações de um CNPJ em um serviço público ou API.
    """
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao consultar o CNPJ. Status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None

def consultar_cep(cep):
    """
    Consulta informações de latitude e longitude baseadas no CEP.
    """
    cep = limpar_cep(cep)
    if not cep.isdigit() or len(cep) != 8:
        print("CEP inválido. Certifique-se de digitar um CEP com 8 dígitos.")
        return None

    url = f"https://cep.awesomeapi.com.br/json/{cep}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            print("Acesso bloqueado! Verifique o User-Agent ou limite de requisições.")
        elif response.status_code == 400:
            print("Erro 400: O CEP enviado é inválido ou malformado.")
        else:
            print(f"Erro ao consultar o CEP. Status code: {response.status_code}")
        return None
    except requests.RequestException as e:
        print(f"Erro na requisição do CEP: {e}")
        return None

def calcular_idade(data_abertura):
    """
    Calcula a idade de uma empresa a partir da data de abertura.
    """
    try:
        data = datetime.strptime(data_abertura, "%Y-%m-%d")
        hoje = datetime.now()
        idade = hoje.year - data.year - ((hoje.month, hoje.day) < (data.month, data.day))
        return f"{idade} anos"
    except ValueError:
        return "Data inválida"

def exibir_informacoes_cnpj(dados_cnpj):
    """
    Exibe as informações de um CNPJ formatadas no terminal.
    """
    if not dados_cnpj:
        print("Nenhuma informação disponível.")
        return

    logradouro = dados_cnpj.get('logradouro', 'Não encontrado')
    numero = dados_cnpj.get('numero', 'S/N')
    municipio = dados_cnpj.get('municipio', 'Não encontrado')
    uf = dados_cnpj.get('uf', 'Não encontrado')
    cep = dados_cnpj.get('cep', '')

    print(f"""
CNPJ: {dados_cnpj.get('cnpj', 'Não encontrado')}\n
RAZÃO SOCIAL: {dados_cnpj.get('nome', 'Não encontrado')}
NOME FANTASIA: {dados_cnpj.get('fantasia', 'Não encontrado')}
SITUAÇÃO CADASTRAL: {dados_cnpj.get('situacao', 'Não encontrado')}
DATA DE ABERTURA: {dados_cnpj.get('abertura', 'Não encontrado')}
IDADE: {calcular_idade(dados_cnpj.get('abertura', 'Não encontrado'))}
CAPITAL SOCIAL: R$ {dados_cnpj.get('capital_social', 'Não encontrado')}

ENDEREÇO: {logradouro}, Número: {numero}
CIDADE/ESTADO: {municipio} - {uf}
TELEFONE: {dados_cnpj.get('telefone', 'Não encontrado')}

E-MAIL: {dados_cnpj.get('email', 'Não encontrado')}

CEP: {cep}
""")

    # Consultar CEP para obter latitude e longitude
    if cep:
        info_cep = consultar_cep(cep)
        if info_cep:
            latitude = info_cep.get('lat', 'Não disponível')
            longitude = info_cep.get('lng', 'Não disponível')
            print(f"""
Latitude: {latitude}
Longitude: {longitude}

Endereço: {logradouro}  Número:{numero}  {municipio}  {uf}

Google Maps: https://www.google.com/maps?q={latitude},{longitude}

Street View: https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}
""")


    atividades_principais = dados_cnpj.get('atividade_principal', [])
    if atividades_principais:
        print("\nATIVIDADE PRINCIPAL\n===================")
        for atividade in atividades_principais:
            print(f"CÓDIGO: {atividade.get('code', 'Não encontrado')}, DESCRIÇÃO: {atividade.get('text', 'Não encontrado')}")

    atividades_secundarias = dados_cnpj.get('atividades_secundarias', [])
    if atividades_secundarias:
        print("\nATIVIDADES SECUNDÁRIAS\n======================")
        for atividade in atividades_secundarias:
            print(f"CÓDIGO: {atividade.get('code', 'Não encontrado')}, DESCRIÇÃO: {atividade.get('text', 'Não encontrado')}")

    socios = dados_cnpj.get('qsa', [])
    if socios:
        print("\nQUADRO DE SÓCIOS\n================")
        for socio in socios:
            print(f"NOME: {socio.get('nome', 'Não encontrado')}, QUALIFICAÇÃO: {socio.get('qual', 'Não encontrado')}\n")

if __name__ == "__main__":
    cnpj = input("\nDigite o CNPJ para consulta (somente números): ")    
    if not cnpj.isdigit() or len(cnpj) != 14:
        print("CNPJ inválido. Certifique-se de digitar apenas números com 14 dígitos.")
    else:
        dados = consultar_cnpj(cnpj)
        exibir_informacoes_cnpj(dados)

input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
