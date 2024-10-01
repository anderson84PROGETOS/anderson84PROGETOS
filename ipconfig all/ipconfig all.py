import subprocess

# Define o nome do arquivo onde a saída será gravada
arquivo = "red.txt"

# Executa o comando ipconfig /all e captura a saída
resultado = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True)

# Verifica se o comando foi executado com sucesso
if resultado.returncode == 0:
    # Imprime a saída na tela
    print("Resultados do comando: ipconfig /all ")
    print(resultado.stdout)  # Mostra a saída do comando

    # Grava a saída no arquivo
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(resultado.stdout)

    print(f"\nA saída foi gravada Em: {arquivo}\n")
else:
    # Em caso de erro, imprime a mensagem de erro
    print(f"Erro ao executar o comando: {resultado.stderr}")

# Mantém a janela do terminal aberta até que o usuário pressione Enter
input("\n\nPRESSIONE ENTER PARA SAIR\n=========================\n")
