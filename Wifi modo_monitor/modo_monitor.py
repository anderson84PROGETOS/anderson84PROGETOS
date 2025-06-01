import subprocess

def executar_comando(comando):
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        print(f"Comando '{' '.join(comando)}' executado com sucesso!")
        print(resultado.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o comando '{' '.join(comando)}':")
        print(e.stderr)

def ativar_modo_monitor(interface):
    try:
        # Parar o NetworkManager
        executar_comando(['sudo', 'systemctl', 'stop', 'NetworkManager'])
        
        # Ativar o modo monitor
        executar_comando(['sudo', 'airmon-ng', 'start', interface])
        
        # Verificar e matar processos que podem interferir
        executar_comando(['sudo', 'airmon-ng', 'check', 'kill'])
        
        # Remover e recarregar o módulo do driver da interface
        executar_comando(['sudo', 'modprobe', '-r', 'rtl8xxxu'])
        executar_comando(['sudo', 'modprobe', 'rtl8xxxu'])        
        
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

# Substitua 'wlan0' pelo nome da sua interface de rede
interface_wifi = 'wlan0'
ativar_modo_monitor(interface_wifi)
