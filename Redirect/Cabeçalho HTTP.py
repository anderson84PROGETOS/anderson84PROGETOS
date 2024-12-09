import subprocess

def obter_cabecalho_http(url):
    try:
        # Adiciona http:// se o usuário inserir apenas o nome do site
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        
        # Executa o comando curl para capturar o cabeçalho HTTP e seguir redirecionamentos
        comando = ["curl", "-I", "-L", "--write-out", "\n", "--silent", url]
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)

        # Retorna o cabeçalho retornado
        cabecalho = resultado.stdout
        return cabecalho
    except subprocess.CalledProcessError as e:
        return f"Erro ao executar o comando curl: {e}"

# Solicita ao usuário a URL ou nome do website
url = input("\nDigite a URL ou nome do website: ").strip()

# Obtém o cabeçalho HTTP
cabecalho_http = obter_cabecalho_http(url)

# Exibe o histórico de redirecionamentos com formatação especial
print("\nHistórico de Redirecionamentos\n")
redirecionamentos = cabecalho_http.split("\n\n")
for i, redirecionamento in enumerate(redirecionamentos):
    if "HTTP/" in redirecionamento:
        print(f"Redirecionamento: {i + 1}\n")
        print(redirecionamento.strip())
        print("\n" + "="*80 + "\n")

input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
