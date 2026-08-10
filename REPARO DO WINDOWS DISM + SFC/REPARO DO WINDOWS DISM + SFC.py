import subprocess
import os
import time
from datetime import timedelta

# Cores ANSI (funcionam no Windows 10/11)
class Cores:
    RESET = "\033[0m"
    VERMELHO = "\033[91m"
    VERDE = "\033[92m"
    AMARELO = "\033[93m"
    AZUL = "\033[94m"
    ROXO = "\033[95m"
    CIANO = "\033[96m"
    BRANCO = "\033[97m"
    NEGRITO = "\033[1m"

def limpar_tela():
    os.system("cls")

def mostrar_help():
    limpar_tela()
    print(f"{Cores.CIANO}{Cores.NEGRITO}{'=' * 60}")
    print("                    AJUDA - O QUE CADA COMANDO FAZ")
    print(f"{'=' * 60}{Cores.RESET}\n")

    print(f"{Cores.AZUL}1. DISM /Online /Cleanup-Image /RestoreHealth{Cores.RESET}")
    print("   • Repara o repositório de componentes do Windows")
    print("   • Baixa arquivos originais da Microsoft se necessário")
    print("   • Corrige a base do sistema")
    print("   • Recomendado rodar primeiro\n")

    print(f"{Cores.VERDE}2. SFC /scannow{Cores.RESET}")
    print("   • Verifica todos os arquivos protegidos do Windows")
    print("   • Substitui arquivos corrompidos pela versão original")
    print("   • Usa o repositório que o DISM reparou")
    print("   • Recomendado rodar depois do DISM\n")

    print(f"{Cores.AMARELO}Importante:{Cores.RESET}")
    print("   • Não instala programas")
    print("   • Não muda senhas")
    print("   • Não mexe no navegador")
    print("   • Não apaga seus arquivos pessoais")
    print("   • Só repara arquivos de sistema do Windows\n")

    print(f"{Cores.ROXO}Log do SFC:{Cores.RESET}")
    print("   C:\\Windows\\Logs\\CBS\\CBS.log\n")

    input(f"{Cores.CIANO}Pressione Enter para voltar ao menu...{Cores.RESET}")

def rodar_comando(comando, nome, cor):
    limpar_tela()
    print(f"{cor}{Cores.NEGRITO}{'=' * 60}")
    print(f"  Executando: {nome}")
    print(f"{'=' * 60}{Cores.RESET}\n")
    print("A porcentagem vai aparecer abaixo em tempo real")
    print("\nNão feche esta janela!\n")

    inicio = time.time()
    processo = subprocess.run(comando, shell=True)
    tempo_total = time.time() - inicio

    print(f"\n{cor}{Cores.NEGRITO}{'=' * 60}")
    print(f"  {nome} finalizado!\n")
    print(f"  Tempo total: {str(timedelta(seconds=int(tempo_total)))}")
    print(f"{'=' * 60}{Cores.RESET}")

    return processo.returncode

def main():
    while True:
        limpar_tela()
        print(f"{Cores.CIANO}{Cores.NEGRITO}{'=' * 60}")
        print("       REPARO DO WINDOWS - DISM + SFC")
        print(f"{'=' * 60}{Cores.RESET}\n")

        print(f"{Cores.AZUL}1. Rodar DISM /RestoreHealth{Cores.RESET}")
        print(f"{Cores.VERDE}2. Rodar SFC /scannow{Cores.RESET}")
        print(f"{Cores.AMARELO}3. Rodar os dois (DISM + SFC){Cores.RESET}")
        print(f"{Cores.ROXO}4. Abrir pasta do log (CBS.log){Cores.RESET}")
        print(f"{Cores.CIANO}5. Help - O que cada comando faz{Cores.RESET}")
        print(f"{Cores.VERMELHO}0. Sair{Cores.RESET}")
        print()

        opcao = input(f"{Cores.BRANCO}Escolha uma opção: {Cores.RESET}").strip()

        if opcao == "1":
            rodar_comando("DISM /Online /Cleanup-Image /RestoreHealth", "DISM RestoreHealth", Cores.AZUL)
            input(f"\n{Cores.AZUL}Pressione Enter para voltar ao menu...{Cores.RESET}")

        elif opcao == "2":
            rodar_comando("sfc /scannow", "SFC /scannow", Cores.VERDE)
            input(f"\n{Cores.VERDE}Pressione Enter para voltar ao menu...{Cores.RESET}")

        elif opcao == "3":
            print(f"\n{Cores.AMARELO}Rodando DISM primeiro...{Cores.RESET}")
            time.sleep(1)
            code1 = rodar_comando("DISM /Online /Cleanup-Image /RestoreHealth", "DISM RestoreHealth", Cores.AZUL)

            print(f"\n{Cores.AMARELO}Agora rodando SFC...{Cores.RESET}")
            time.sleep(2)
            code2 = rodar_comando("sfc /scannow", "SFC /scannow", Cores.VERDE)

            print(f"\n{Cores.AMARELO}{Cores.NEGRITO}{'=' * 60}")
            if code1 == 0 and code2 == 0:
                print("  Os dois comandos terminaram com sucesso!")
            else:
                print("  Algum comando retornou erro.")
            print(f"{'=' * 60}{Cores.RESET}")
            input(f"\n{Cores.AMARELO}Pressione Enter para voltar ao menu...{Cores.RESET}")

        elif opcao == "4":
            os.startfile(r"C:\Windows\Logs\CBS")
            print(f"\n{Cores.ROXO}Pasta do log aberta.{Cores.RESET}")
            time.sleep(1.5)

        elif opcao == "5":
            mostrar_help()

        elif opcao == "0":
            print(f"\n{Cores.VERMELHO}Saindo...{Cores.RESET}")
            break

        else:
            print(f"\n{Cores.VERMELHO}Opção inválida!{Cores.RESET}")
            time.sleep(1.2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Cores.VERMELHO}Script interrompido pelo usuário.{Cores.RESET}")
