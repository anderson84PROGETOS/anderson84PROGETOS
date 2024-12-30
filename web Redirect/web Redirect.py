import requests
from urllib.parse import urlparse
import socket
import pycountry  # Biblioteca para obter o nome completo do país
from colorama import Fore, Style, init
from bs4 import BeautifulSoup  # Importando o BeautifulSoup para processar HTML

# Inicializa o colorama
init(autoreset=True)

# Imprime o texto com a cor azul claro
print(Fore.LIGHTBLUE_EX + """

██╗    ██╗███████╗██████╗     ██████╗ ███████╗██████╗ ██╗██████╗ ███████╗ ██████╗████████╗
██║    ██║██╔════╝██╔══██╗    ██╔══██╗██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝
██║ █╗ ██║█████╗  ██████╔╝    ██████╔╝█████╗  ██║  ██║██║██████╔╝█████╗  ██║        ██║   
██║███╗██║██╔══╝  ██╔══██╗    ██╔══██╗██╔══╝  ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║   
╚███╔███╔╝███████╗██████╔╝    ██║  ██║███████╗██████╔╝██║██║  ██║███████╗╚██████╗   ██║   
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝   
                                                                                                                                                                                                              
""")

def obter_pais_completo(codigo_pais):
    """
    Obtém o nome completo do país a partir do código do país.
    """
    try:
        pais = pycountry.countries.get(alpha_2=codigo_pais)
        return pais.name if pais else "DESCONHECIDO"
    except Exception as e:
        print(Fore.LIGHTRED_EX + f"Erro ao converter código do país: {e}")
    return "DESCONHECIDO"

def obter_pais(endereco_ip):
    """
    Obtém o país associado a um endereço IP usando a API pública ipinfo.io.
    """
    try:
        resposta = requests.get(f"https://ipinfo.io/{endereco_ip}/json")
        if resposta.status_code == 200:
            dados = resposta.json()
            codigo_pais = dados.get("country", "DESCONHECIDO")
            return obter_pais_completo(codigo_pais)
    except Exception as e:
        print(Fore.LIGHTRED_EX + f"Erro ao obter o país: {e}")
    return "DESCONHECIDO"

def obter_titulo_pagina(url):
    """
    Obtém o título da página usando BeautifulSoup para analisar o HTML.
    """
    try:
        # Realiza a requisição ao site
        resposta = requests.get(url)
        if resposta.status_code == 200:
            # Usa BeautifulSoup para parsear o conteúdo HTML
            soup = BeautifulSoup(resposta.content, 'html.parser')
            titulo = soup.title.string.strip() if soup.title else 'Título não encontrado'
            return titulo
        else:
            return "Título não encontrado"
    except Exception as e:
        print(Fore.LIGHTRED_EX + f"Erro ao obter o título: {e}")
    return "Título não encontrado"

# Mapeamento dos códigos de status HTTP para tradução
status_code_translation = {
    100: "CONTINUAR",
    101: "MUDANDO PROTOCOLO",
    102: "PROCESSANDO",
    200: "OK",
    201: "CRIADO",
    202: "ACEITO",
    203: "NÃO AUTORIZADO (INFORMAL)",
    204: "SEM CONTEÚDO",
    205: "RESETAR CONTEÚDO",
    206: "CONTEÚDO PARCIAL",
    207: "MULTI-STATUS",
    208: "JÁ REPORTADO",
    226: "IMU",
    300: "MÚLTIPLAS ESCOLHAS",
    301: "MOVIDO PERMANENTEMENTE",
    302: "ENCONTRADO",
    303: "VEJA OUTRO",
    304: "NÃO MODIFICADO",
    305: "USAR PROXY",
    306: "SWITCH PROXY (INUTILIZADO)",
    307: "REDIRECIONAMENTO TEMPORÁRIO",
    308: "REDIRECIONAMENTO PERMANENTE",
    400: "REQUISIÇÃO INVÁLIDA",
    401: "NÃO AUTORIZADO",
    402: "PAGAMENTO REQUERIDO",
    403: "ACESSO PROIBIDO",
    404: "NÃO ENCONTRADO",
    405: "MÉTODO NÃO PERMITIDO",
    406: "NÃO ACEITÁVEL",
    407: "AUTENTICAÇÃO DE PROXY REQUERIDA",
    408: "TIMEOUT DE REQUISIÇÃO",
    409: "CONFLITO",
    410: "GONE",
    411: "TAMANHO REQUERIDO",
    412: "PRÉ-CONDIÇÕES FALHARAM",
    413: "CARGA ÚTIL MUITO GRANDE",
    414: "URI MUITO LONGO",
    415: "TIPO DE MÍDIA NÃO SUPORTADO",
    416: "INTERVALO NÃO SATISFATÓRIO",
    417: "EXPECTATIVA FALHOU",
    418: "SOU UM TEA POT (ESPECIAL)",
    421: "MÁ REQUISIÇÃO DE DIREÇÃO",
    422: "ENTIDADE INPROCESSADA",
    423: "BLOQUEADO",
    424: "DEPENDÊNCIA FALHOU",
    425: "ORDENAR REQUISIÇÃO",
    426: "ATUALIZAÇÃO REQUERIDA",
    428: "PRÉ-CONDIÇÃO REQUERIDA",
    429: "MUITOS PEDIDOS",
    431: "CABEÇALHO REQUISITADO UM TANTO GRANDE",
    451: "INDISPONÍVEL POR REQUISITO LEGAL",
    500: "ERRO INTERNO DO SERVIDOR",
    501: "NÃO IMPLEMENTADO",
    502: "BAD GATEWAY",
    503: "SERVIÇO INDISPONÍVEL",
    504: "GATEWAY TIMEOUT",
    505: "VERSÃO HTTP NÃO SUPORTADA",
    506: "VARIAÇÃO DE NEGOCIAÇÃO FALHOU",
    507: "ESPACO INSUFICIENTE",
    508: "LOOP DETECTADO",
    510: "NÃO EXTENDIDO",
    511: "AUTENTICAÇÃO DE REDE REQUERIDA",
    520: "ERRO DESCONHECIDO",
    521: "SERVIÇO DESATIVADO",
    522: "TIMEOUT DE CONEXÃO",
    523: "DESTINO INALCANÇÁVEL",
    524: "TIMEOUT DE CONEXÃO COM ORIGEM",
    525: "PROBLEMA COM SSL",
    526: "CERTIFICADO SSL INVÁLIDO",
    527: "PROBLEMA DE REDE",
    530: "ERRO NÃO DEFINIDO",
    598: "TIMEOUT DE LEITURA DE REDE",
    599: "TIMEOUT DE CONEXÃO",
    600: "CONECTOR FALHOU",
    601: "FAILOVER FALHOU",
    602: "ERRO CONEXÃO REMOTA",
    603: "SERVIÇO INDISPONÍVEL TEMPORÁRIO",
    604: "USO RESTRITO",
    605: "SERVIÇO NOVIDADE",
    606: "ERRO NO SERVIDOR",
    607: "ERRO NO NÚCLEO",
    608: "OPERAÇÃO CANCELADA",
    609: "PERMISSÃO NEGADA",
    610: "NÃO CONECTADO",
    611: "NÃO AUTORIZADO PELO GATEWAY",
    612: "CONEXÃO VAZIA",
    613: "SUSPENSO",
    614: "TIMEOUT INTERNO",
    615: "TIMEOUT DE SERVIÇO",
    616: "EXCESSO DE CONEXÕES",
    617: "REQUISIÇÃO DESCONHECIDA",
    618: "FALHA DE AUTORIZAÇÃO",
    619: "DADOS INSUFICIENTES",
    620: "CONFLITO DE DADOS",
    621: "SERVIÇO INDISPONÍVEL EM REDE",
    622: "FALHA DE CONEXÃO",
    623: "SERVIÇO TEMPORARIAMENTE INDISPONÍVEL",
    624: "CONFLITO DE INFORMAÇÃO",
    625: "ERRO DESCONHECIDO DO SERVIDOR",
    626: "INDEFINIDO",
    627: "NÃO CONECTADO À INTERNET",
    628: "ERRO DE CONSULTA",
    629: "ERRO NO BANCO DE DADOS",
    630: "RECURSO INDISPONÍVEL",
    631: "RECURSO NÃO ENCONTRADO",
    632: "ERROR",
    633: "ERRO DE TRANSMISSÃO",
    634: "ERRO INTERNO NO SERVIDOR",
    635: "SERVIÇO CONGESTIONADO",
    636: "ERRO DE REQUISIÇÃO",
    637: "ERRO NO RECURSO",
    638: "ERRO EXTERNO",
    639: "CONFLITO DE RECURSO",
    640: "FALHA INTERNA",
    641: "SERVIÇO PENDENTE",
    642: "SERVIÇO INDISPONÍVEL - AGUARDE",
    643: "SERVIÇO PAREADO",
    644: "ERRO DE SINCRONIZAÇÃO",
    645: "FALHA DE CONEXÃO",
    646: "RECURSO PENDENTE",
    647: "PROCESSANDO",
    648: "TIMEOUT DE RESPOSTA",
    649: "ERRO DE LAYOUT",
    650: "NÃO CONECTADO",
    651: "INÍCIO MAL SUCEDIDO",
    652: "EXCESSO DE USO",
    653: "RECURSO EXCEDIDO",
    654: "QUEDA DE SERVIÇO",
    655: "FALHA AO INICIAR",
    656: "LIMITAÇÃO DE RECURSO",
    657: "SERVIÇO RECUSADO",
    658: "SERVIÇO FALHADO",
    659: "MÁ QUANTIDADE DE DADOS",
    660: "ERRO DE CONECTIVIDADE",
    661: "INÍCIO MAL SUCEDIDO",
    662: "PROCESSO DESCONHECIDO",
    663: "ERRO COM SERVIÇO",
    664: "CONECTANDO",
    665: "FALHA INTERNA",
    666: "LIMITADO",
    667: "EXCEDEU O LIMITE",
    668: "FALHA DE RECURSO",
    669: "ERRO DE ARQUIVO",
    670: "FALHA AO RECONECTAR",
    671: "NÃO AUTORIZADO",
    672: "CONECTOR FALHOU",
    673: "FALHA NO PROXY",
    674: "SUPERAÇÃO DE LIMITE",
    675: "RECURSO NÃO PERMITIDO",
    676: "ERRO DE CONEXÃO",
    677: "SERVIÇO NÃO DISPONÍVEL",
    678: "CONFLITO EXCESSIVO",
    679: "INTERNET NÃO DISPONÍVEL",
    680: "ERRO NO ENDPOINT",
    681: "REQUISIÇÃO INDISPONÍVEL",
    682: "ERRO DE FALHA",
    683: "SERVIÇO REJEITADO",
    684: "MÉTODO NÃO PERMITIDO",
    685: "INTERNAL ERROR",
    686: "NÃO ENCONTRADO",
    687: "CONECTANDO-",
    688: "SERVIÇO FINALIZADO",
    689: "ERRO RECURSO",
    690: "SERVIÇO DESATIVADO",
    691: "ERRO DE CARGA"
}

def obter_informacoes_do_site(url):
    """
    Obtém informações detalhadas sobre um site, incluindo IP, país, cabeçalhos HTTP, e mais.
    """
    try:
        # Adicionar esquema (http ou https) se estiver ausente
        if not url.startswith(('http://', 'https://')): 
            url = 'http://' + url

        # Cabeçalhos para evitar erro 403
        cabecalhos = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/',
            'Cache-Control': 'no-cache'
        }

        # Realizar a requisição ao site
        resposta = requests.get(url, headers=cabecalhos, allow_redirects=True)
        url_analisada = urlparse(url)

        # Obter informações do IP
        endereco_ip = socket.gethostbyname(url_analisada.netloc)
        pais = obter_pais(endereco_ip)  # Obter o país usando a função

        # Processar cabeçalhos HTTP
        cabecalhos_site = resposta.headers
        servidor = cabecalhos_site.get("Server", "DESCONHECIDO")
        cookies = list(resposta.cookies.keys())
        metodos_acesso = cabecalhos_site.get("Access-Control-Allow-Methods", "DESCONHECIDO")
        cabecalhos_incomuns = [k for k in cabecalhos_site.keys() if k.lower() not in
                               ["content-type", "content-length", "server", "date", "set-cookie"]]

        # Capturar o histórico de redirecionamentos
        redirecionamentos = []
        for resp in resposta.history:
            status_traduzido = status_code_translation.get(resp.status_code, f"Status {resp.status_code} desconhecido")
            redirecionamentos.append(f"{resp.status_code} - {status_traduzido} -> {resp.url}")

        # Obter o título da página
        titulo = obter_titulo_pagina(url)

        # Exibir o título da página
        print(Fore.LIGHTCYAN_EX + f"Relatório WhatWeb para: {url}")
        print(Fore.LIGHTWHITE_EX + f"Título    : {titulo}")

        # Exibir o resultado com informações do site
        print(Fore.LIGHTGREEN_EX + f"Status    : {resposta.status_code} {resposta.reason}")
        print(Fore.LIGHTCYAN_EX + f"IP        : {endereco_ip}")
        print(Fore.LIGHTGREEN_EX + f"País      : {pais}")
        print(Fore.LIGHTMAGENTA_EX + f"Servidor  : {servidor}\n")

        # Exibir o histórico de redirecionamentos
        if redirecionamentos:
            print(Fore.LIGHTYELLOW_EX + "\nHistórico de Redirecionamentos")
            for redir in redirecionamentos:
                print(Fore.LIGHTGREEN_EX + f"\n{redir}")
        else:
            print(Fore.LIGHTYELLOW_EX + "Nenhum redirecionamento detectado.")

        # Exibir resumo
        print(Fore.LIGHTCYAN_EX + "\n\nResumo    :", end=" ")
        if metodos_acesso != "DESCONHECIDO":
            print(Fore.LIGHTGREEN_EX + f"Access-Control-Allow-Methods[{metodos_acesso}], ", end="") 
        if cookies:
            print(Fore.LIGHTYELLOW_EX + f"Cookies[{', '.join(cookies)}], ", end="")
        if servidor != "DESCONHECIDO":
            print(Fore.LIGHTMAGENTA_EX + f"ServidorHTTP[{servidor}], ", end="")
        if cabecalhos_incomuns:
            print(Fore.LIGHTRED_EX + f"CabeçalhosIncomuns[{', '.join(cabecalhos_incomuns)}]")

        print("\n" + Fore.LIGHTCYAN_EX + "\nPlugins Detectados\n")
        if metodos_acesso != "DESCONHECIDO":
            print(Fore.LIGHTGREEN_EX + "[ Access-Control-Allow-Methods ]\n    Especifica os métodos permitidos ao acessar um recurso.")
            print(Fore.LIGHTYELLOW_EX + f"    Valor        : {metodos_acesso}\n")
        if servidor != "DESCONHECIDO":
            print(Fore.LIGHTMAGENTA_EX + "[ ServidorHTTP ]\n    Informação do cabeçalho do servidor HTTP.")
            print(Fore.LIGHTCYAN_EX + f"    Valor        : {servidor} (do cabeçalho do servidor)\n")
        if cookies:
            print(Fore.LIGHTYELLOW_EX + "[ Cookies ]\n    Exibe os nomes dos cookies encontrados nos cabeçalhos HTTP.")
            print(Fore.LIGHTCYAN_EX + f"    Valor        : {', '.join(cookies)}\n")
        if cabecalhos_incomuns:
            print(Fore.LIGHTRED_EX + "[ CabeçalhosIncomuns ]\n    Cabeçalhos HTTP incomuns encontrados.")
            print(Fore.LIGHTCYAN_EX + f"    Valor        : {', '.join(cabecalhos_incomuns)}\n")

        print("\n" + Fore.LIGHTCYAN_EX + "Cabeçalhos HTTP\n")
        for k, v in cabecalhos_site.items():
            print(Fore.LIGHTGREEN_EX + f"    {k}: {v}")

    except Exception as e:
        print(Fore.LIGHTRED_EX + f"Erro: {e}")

# Exemplo de execução
if __name__ == "__main__":
    site = input("\nDigite o nome do website: ")
    print("\n")
    obter_informacoes_do_site(site)
    
input(Fore.LIGHTCYAN_EX + "\n\n========== PRESSIONE ENTER PARA SAIR ==========\n")
