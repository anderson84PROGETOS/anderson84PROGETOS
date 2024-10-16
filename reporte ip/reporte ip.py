import subprocess
import re
import requests
import pycountry  # Adicione esta biblioteca para converter códigos de país para nomes completos

print("""

██████╗ ███████╗██████╗  ██████╗ ██████╗ ████████╗███████╗    ██╗██████╗ 
██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝    ██║██╔══██╗
██████╔╝█████╗  ██████╔╝██║   ██║██████╔╝   ██║   █████╗      ██║██████╔╝
██╔══██╗██╔══╝  ██╔═══╝ ██║   ██║██╔══██╗   ██║   ██╔══╝      ██║██╔═══╝ 
██║  ██║███████╗██║     ╚██████╔╝██║  ██║   ██║   ███████╗    ██║██║     
╚═╝  ╚═╝╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝    ╚═╝╚═╝     
                                                                         
""")

print("Verificar IP acesse o site: https://www.abuseipdb.com\n\n")

# Função para obter as conexões do netstat
def obter_ips_netstat():
    saida_netstat = subprocess.check_output(['netstat', '-na']).decode('latin-1')  # Alteração na decodificação
    # Expressão regular para capturar endereços IP (excluindo as portas)
    padrao_ip = re.compile(r'\d+\.\d+\.\d+\.\d+')
    ips = set(re.findall(padrao_ip, saida_netstat))  # Usar 'set' para evitar duplicatas
    return ips

# Função para converter código do país em nome completo
def obter_nome_pais(codigo_pais):
    if not codigo_pais or len(codigo_pais) != 2:  # Verifica se o código do país é válido
        return "Desconhecido"
    
    try:
        pais = pycountry.countries.get(alpha_2=codigo_pais)
        if pais:
            return pais.name
        else:
            return "Desconhecido"
    except LookupError:
        return "Desconhecido"

# Função para verificar o IP no AbuseIPDB
def verificar_ip_no_abuseipdb(ip, chave_api):
    url = f"https://api.abuseipdb.com/api/v2/check"
    parametros = {'ipAddress': ip, 'maxAgeInDays': 90}  # Verificar relatórios nos últimos 90 dias
    cabecalhos = {
        'Accept': 'application/json',
        'Key': chave_api  # Substitua pela sua chave de API do AbuseIPDB
    }
    
    resposta = requests.get(url, headers=cabecalhos, params=parametros)
    
    if resposta.status_code == 200:
        dados = resposta.json()
        if dados['data']['totalReports'] > 0:  # Se o IP foi reportado
            relatorios = dados['data'].get('reports', [])  # Usa get() para evitar KeyError
            codigo_pais = dados['data'].get('countryCode', 'Desconhecido')  # Caso a cidade não seja informada
            cidade_completa = obter_nome_pais(codigo_pais)
            return {
                'ip': ip,
                'total_relatorios': dados['data']['totalReports'],
                'pontuacao_confianca': dados['data']['abuseConfidenceScore'],
                'relatorio_recente': relatorios[-1] if relatorios else None,
                'cidade': cidade_completa
            }
    return None

# Função principal para executar o script
def main():
    chave_api = 'sua chave de API'  # Substitua pela sua chave de API do AbuseIPDB
    ips = obter_ips_netstat()

    for ip in ips:
        resultado = verificar_ip_no_abuseipdb(ip, chave_api)
        if resultado:
            print(f"IP: {resultado['ip']:<20} foi reportado {resultado['total_relatorios']} vezes\n\n")
            print(f"Pontuação de Confiança: {resultado['pontuacao_confianca']}")
            if resultado['relatorio_recente']:
                print(f"Relatório Mais Recente: {resultado['relatorio_recente']}")
            print(f"País: {resultado['cidade']}")
        else:
            print(f"IP: {ip:<20} está limpo")
    
if __name__ == "__main__":
    main()

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
