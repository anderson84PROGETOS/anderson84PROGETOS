import requests

print("""

██████╗ ███████╗██████╗ ██╗██████╗ ███████╗ ██████╗████████╗
██╔══██╗██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝
██████╔╝█████╗  ██║  ██║██║██████╔╝█████╗  ██║        ██║   
██╔══██╗██╔══╝  ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║   
██║  ██║███████╗██████╔╝██║██║  ██║███████╗╚██████╗   ██║   
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝   
                                                         
""")

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

def obter_cabecalho_http(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        # Tenta acessar via HTTPS (porta 443)
        url_https = f"https://{url}"
        response = requests.get(url_https, headers=headers, timeout=5, allow_redirects=True)
        print(f"\nCabeçalhos HTTP para: {url_https}")
       
        exibir_historico_redirecionamentos(response)
        exibir_cabecalhos(response)
    except requests.exceptions.RequestException:
        try:
            # Tenta acessar via HTTP (porta 80)
            url_http = f"http://{url}"
            response = requests.get(url_http, headers=headers, timeout=5, allow_redirects=True)
            print(f"\n\nCabeçalhos HTTP para: {url_http}")
        
            exibir_historico_redirecionamentos(response)
            exibir_cabecalhos(response)
        except requests.exceptions.RequestException as e:
            print(f"Erro ao conectar-se a {url}: {e}")    

def exibir_historico_redirecionamentos(response):
    print("\n\nHistórico de Redirecionamentos\n")

    # Mostrar primeiro o status 200 (se aplicável)
    if response.status_code == 200:
        print(f"200 - OK -> {response.url}\n")
    
    # Exibir o restante dos redirecionamentos, exceto 200
    for resp in response.history:
        if resp.status_code != 200:  # Ignorar status 200 nos redirecionamentos
            status_code = resp.status_code
            status_name = status_code_translation.get(status_code, "DESCONHECIDO")
            print(f"{status_code} - {status_name} -> {resp.url}\n")

    # Exibir a resposta final, se não for 200
    if response.status_code != 200:
        status_code = response.status_code
        status_name = status_code_translation.get(status_code, "DESCONHECIDO")
        print(f"{status_code} - {status_name} -> {response.url}\n")

def exibir_cabecalhos(response):
    print("\nCabeçalhos HTTP\n")
    for key, value in response.headers.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    site = input("\nDigite o nome do site: ")
    obter_cabecalho_http(site)

input("\n\n========== PRESSIONE ENTER PARA SAIR ==========\n\n")
