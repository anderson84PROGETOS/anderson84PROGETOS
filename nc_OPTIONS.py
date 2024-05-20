import subprocess

# Defina o nome do site
site = input("\nDigite o nome do site (Exemplo: businesscorp.com.br): ")

# Crie o comando netcat
command = f"nc -v {site} 80"

# Crie a solicitação HTTP OPTIONS
http_request = f"OPTIONS / HTTP/1.0\r\nHost: {site}\r\n\r\n"

try:
    # Inicie o subprocesso com o comando netcat
    process = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Envie a solicitação HTTP OPTIONS
    stdout, stderr = process.communicate(input=http_request.encode())

    # Imprima a resposta do servidor
    print("\nResposta do servidor\n\n", stdout.decode()) 

    # Verifique a saída de erro para encontrar a linha com "open"
    stderr_output = stderr.decode()
    for line in stderr_output.splitlines():
        if "open" in line:
            print(line)
            break

except Exception as e:
    print(f"Ocorreu um erro: {e}")
