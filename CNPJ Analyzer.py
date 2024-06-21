import requests

print("""

 ██████╗███╗   ██╗██████╗      ██╗     █████╗ ███╗   ██╗ █████╗ ██╗     ██╗   ██╗███████╗███████╗██████╗ 
██╔════╝████╗  ██║██╔══██╗     ██║    ██╔══██╗████╗  ██║██╔══██╗██║     ╚██╗ ██╔╝╚══███╔╝██╔════╝██╔══██╗
██║     ██╔██╗ ██║██████╔╝     ██║    ███████║██╔██╗ ██║███████║██║      ╚████╔╝   ███╔╝ █████╗  ██████╔╝
██║     ██║╚██╗██║██╔═══╝ ██   ██║    ██╔══██║██║╚██╗██║██╔══██║██║       ╚██╔╝   ███╔╝  ██╔══╝  ██╔══██╗
╚██████╗██║ ╚████║██║     ╚█████╔╝    ██║  ██║██║ ╚████║██║  ██║███████╗   ██║   ███████╗███████╗██║  ██║
 ╚═════╝╚═╝  ╚═══╝╚═╝      ╚════╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚══════╝╚═╝  ╚═╝
                                                                                                         
""")

def consultar_cnpj(cnpj):
    url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao consultar CNPJ: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")

# Exemplo de uso:
cnpj = input("\nDigite o número do CNPJ  ( ex: 18236120000158 ): ")  # Substitua pelo CNPJ desejado
print("\n\nMais informações Acesse o Site: https://www.informecadastral.com.br\n\n")
dados_cnpj = consultar_cnpj(cnpj)
if dados_cnpj:
    print("\n=========== Dados Encontrados ==========\n")
    print(f"Nome: {dados_cnpj.get('nome', 'Não encontrado')}")
    print(f"CNPJ: {dados_cnpj.get('cnpj', 'Não encontrado')}")
    print(f"Telefone: {dados_cnpj.get('telefone', 'Não encontrado')}")
    print(f"Situação: {dados_cnpj.get('situacao', 'Não encontrado')}")
    print(f"CNAE principal: {dados_cnpj['atividade_principal'][0]['text'] if 'atividade_principal' in dados_cnpj else 'Não encontrado'}")
    
    # Outras informações possíveis
    print(f"Data da situação cadastral: {dados_cnpj.get('data_situacao', 'Não encontrado')}")
    print(f"Data de abertura: {dados_cnpj.get('abertura', 'Não encontrado')}")
    print(f"Capital social: R$ {dados_cnpj.get('capital_social', 'Não encontrado')}")     
    
    # Quadro de sócios e administradores
    if 'qsa' in dados_cnpj:
        print("\n========== Quadro de sócios e administradores ==========\n")
        for socio in dados_cnpj['qsa']:
            print(f"Nome: {socio['nome']} | Qualificação: {socio['qual']} | Entrada: {socio['qual']}")

input("\n\n=================== PRESSIONE ENTER PARA SAIR ===================\n\n")
