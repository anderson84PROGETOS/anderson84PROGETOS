import socket

def main():
    alvo = input("\nDigite a URL do website: ")
    print("\n")
    wordlist = "word.txt"
    resultados = []

    try:
        with open(wordlist, "r") as word:
            for linha in word:
                txt = linha.strip()
                result = txt + alvo
                try:
                    ip = socket.gethostbyname(result)
                    print(f"HOST ENCONTRADO: {result} ====> IP: {ip}")
                    resultados.append(f"HOST ENCONTRADO: {result} ====> IP: {ip}\n")
                except socket.gaierror:
                    continue

    except FileNotFoundError:
        print("\nArquivo da wordlist não encontrado.")

    # Pergunta ao usuário se deseja salvar os resultados
    salvar = input("\nDeseja salvar os resultados? (s/n): ")
    if salvar.lower() == 's':
        nome_arquivo = input("\nDigite o nome do arquivo para salvar os resultados: ")
        salvar_resultados(nome_arquivo, alvo, resultados)

    input("\nPressione ENTER Para Sair\n")

def salvar_resultados(nome_arquivo, alvo, resultados):
    try:
        with open(nome_arquivo, "a") as arquivo:
            arquivo.write(f"\nResultados para o alvo: {alvo}\n\n")
            arquivo.writelines(resultados)
        print("\n\nResultados salvos com sucesso!")

    except IOError:
        print("Erro ao salvar os resultados.")

if __name__ == "__main__":
    main()
