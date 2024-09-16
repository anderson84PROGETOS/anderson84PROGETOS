import os
import subprocess

# Diretório onde os PDFs estão armazenados
pasta_pdfs = "pdfs"
arquivo_saida = "resultado.txt"

# Função para executar o exiftool e salvar a saída em um arquivo
def executar_exiftool(pasta, arquivo_txt):
    with open(arquivo_txt, 'w', encoding='utf-8', errors='replace') as f:
        for arquivo in os.listdir(pasta):
            if arquivo.endswith(".pdf"):
                caminho_arquivo = os.path.join(pasta, arquivo)
                print(f"Processando: {caminho_arquivo}")
                # Executa o comando exiftool
                resultado = subprocess.run(["exiftool", caminho_arquivo], capture_output=True)
                # Salva o resultado no arquivo
                f.write(f"\nMetadados do arquivo: {arquivo}\n\n")
                # Tenta decodificar o stdout com UTF-8, substituindo caracteres problemáticos
                f.write(resultado.stdout.decode('utf-8', errors='replace'))
                f.write("\n" + "-"*50 + "\n")
    print(f"\n\nResultados salvos em: {arquivo_txt}")

# Chama a função para processar todos os PDFs
executar_exiftool(pasta_pdfs, arquivo_saida)
