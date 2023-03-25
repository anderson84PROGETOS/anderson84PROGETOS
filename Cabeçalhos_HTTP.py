import subprocess

# Pedir ao usuário para digitar o URL do website
url = input("\nDigite o nome ou a url do website: ")

# mostra o Cabeçalhos HTTP
print("\n↓↓ Cabeçalhos HTTP ↓↓\n")

# Executar o comando curl com as opções especificadas
command = ["curl", "-s", "--head", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36", url]
result = subprocess.run(command, stdout=subprocess.PIPE)

# Exibir a saída capturada
print(result.stdout.decode())

# Fim do Cabeçalhos HTTP
input("\nCabeçalhos HTTP FIM [ENTER SAIR]\n")
