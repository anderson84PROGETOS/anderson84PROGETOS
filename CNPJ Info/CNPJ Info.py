import requests
from datetime import datetime
from colorama import Fore, Style, init

# Inicializando o colorama
init(autoreset=True)
print(Fore.LIGHTRED_EX + Style.BRIGHT + "Acesse o site: https://www.informecadastral.com.br")
print(Fore.LIGHTCYAN_EX + Style.BRIGHT + """
 ██████╗███╗   ██╗██████╗      ██╗    ██╗███╗   ██╗███████╗ ██████╗ 
██╔════╝████╗  ██║██╔══██╗     ██║    ██║████╗  ██║██╔════╝██╔═══██╗
██║     ██╔██╗ ██║██████╔╝     ██║    ██║██╔██╗ ██║█████╗  ██║   ██║
██║     ██║╚██╗██║██╔═══╝ ██   ██║    ██║██║╚██╗██║██╔══╝  ██║   ██║
╚██████╗██║ ╚████║██║     ╚█████╔╝    ██║██║ ╚████║██║     ╚██████╔╝
 ╚═════╝╚═╝  ╚═══╝╚═╝      ╚════╝     ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ 
                                                                
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

def calcular_idade(data_abertura):
    hoje = datetime.now()
    data_abertura = datetime.strptime(data_abertura, '%d/%m/%Y')
    diferenca = hoje - data_abertura
    anos = diferenca.days // 365
    meses = (diferenca.days % 365) // 30
    dias = (diferenca.days % 365) % 30
    return f"{anos} anos, {meses} meses e {dias} dias"

def formatar_cnpj(cnpj):
    return cnpj.replace('.', '').replace('/', '').replace('-', '')

def consultar_e_mostrar(cnpj):
    dados_cnpj = consultar_cnpj(cnpj)
    if dados_cnpj:
        message = f"""
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}\nCNPJ:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('cnpj', 'Não encontrado')}{Style.RESET_ALL}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}RAZÃO SOCIAL:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('nome', 'Não encontrado')}{Style.RESET_ALL}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}MATRIZ OU FILIAL:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('tipo', 'Não encontrado')}{Style.RESET_ALL}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}NOME FANTASIA:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('fantasia', 'Não encontrado')}{Style.RESET_ALL}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}SITUAÇÃO CADASTRAL:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('situacao', 'Não encontrado')}{Style.RESET_ALL}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}DATA DA SITUAÇÃO CADASTRAL:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('data_situacao', 'Não encontrado')}{Style.RESET_ALL}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}MOTIVO DA SITUAÇÃO CADASTRAL:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('motivo_situacao', 'Não encontrado')}{Style.RESET_ALL}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}NATUREZA JURÍDICA:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('natureza_juridica', 'Não encontrado')}{Style.RESET_ALL}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}DATA DE ABERTURA:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('abertura', 'Não encontrado')}{Style.RESET_ALL}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}IDADE:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{calcular_idade(dados_cnpj['abertura']) if 'abertura' in dados_cnpj else 'Não encontrado'}{Style.RESET_ALL}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}PORTE (RFB):{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('porte', 'Não encontrado')}{Style.RESET_ALL}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}CAPITAL SOCIAL:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}R$ {dados_cnpj.get('capital_social', 'Não encontrado')}{Style.RESET_ALL}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}ATUALIZAÇÃO DESTA PÁGINA:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('ultima_atualizacao', 'Não encontrado')}{Style.RESET_ALL}\n

{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}LOCALIZAÇÃO\n==========={Style.RESET_ALL}

{Fore.LIGHTGREEN_EX}{Style.BRIGHT}ENDEREÇO:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('logradouro', 'Não encontrado')} | Número: {Fore.LIGHTGREEN_EX}{Style.BRIGHT}{dados_cnpj.get('numero', 'Não encontrado')}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}COMPLEMENTO:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('complemento', 'Não encontrado')}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}BAIRRO:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('bairro', 'Não encontrado')}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}CIDADE | ESTADO:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('municipio', 'Não encontrado')} | {dados_cnpj.get('uf', 'Não encontrado')}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}CEP:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('cep', 'Não encontrado')}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}TELEFONES:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('telefone', 'Não encontrado')}\n
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}E-MAILS:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{dados_cnpj.get('email', 'Não encontrado')}\n
{Style.RESET_ALL}

{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}ATIVIDADE ECONÔMICA PRINCIPAL\n============================={Style.RESET_ALL}

{Fore.LIGHTGREEN_EX}{Style.BRIGHT}CÓDIGO:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT} {dados_cnpj['atividade_principal'][0]['code'] if 'atividade_principal' in dados_cnpj else 'Não encontrado'}
{Fore.LIGHTGREEN_EX}{Style.BRIGHT}DESCRIÇÃO:{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{Style.BRIGHT} {dados_cnpj['atividade_principal'][0]['text'] if 'atividade_principal' in dados_cnpj else 'Não encontrado'}

""" 
        # Adiciona atividades econômicas secundárias
        if 'atividades_secundarias' in dados_cnpj:
            for atividade in dados_cnpj['atividades_secundarias']:
                message += Fore.LIGHTGREEN_EX + Style.BRIGHT + f"CÓDIGO: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{atividade['code']} | DESCRIÇÃO: " + Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"{atividade['text']}\n"


        # Adiciona informações do QSA
        message += Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n\n\nQUADRO DE SÓCIOS E ADMINISTRADORES (QSA)\n==========================================\n"
        
        if 'qsa' in dados_cnpj:
            for socio in dados_cnpj['qsa']:
                data_entrada = socio.get('data_entrada', None)
                if data_entrada:
                    # Converte para formato adequado, se necessário
                    data_entrada = datetime.strptime(data_entrada, '%d/%m/%Y').strftime('%d/%m/%Y')
                    message += f"""
NOME: {socio.get('nome', 'Não encontrado')}
QUALIFICAÇÃO: {socio.get('qual', 'Não encontrado')}
ENTRADA: {data_entrada}
"""
                else:
                    message += f"""
NOME: {socio.get('nome', 'Não encontrado')}
QUALIFICAÇÃO: {socio.get('qual', 'Não encontrado')}
"""
        else:
            message += "Não encontrado\n"

        # Exibe os dados no console
        print(message)

def main():
    cnpj = input(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "Digite o número do CNPJ (ex: 22333333011150 ou 22.333.333/0111-50): ").strip()
    cnpj_formatado = formatar_cnpj(cnpj)  # Formata o CNPJ removendo pontos e barras
    consultar_e_mostrar(cnpj_formatado)

if __name__ == "__main__":
    main()

input(Fore.LIGHTRED_EX + Style.BRIGHT + "\n========== PRESSIONE ENTER PARA SAIR ==========\n")
