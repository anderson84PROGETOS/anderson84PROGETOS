import psutil
import platform
import wmi
import GPUtil
import os
import subprocess
import re

# Get the full hostname
# Obter o nome do usuário
username = os.getlogin()

# Obter o nome do computador
computer_name = subprocess.check_output('whoami').strip().decode('utf-8').split('\\')[0]

# Obter a versão do Windows
ver_output = subprocess.check_output('ver', shell=True)
ver_info = re.search(r'(\d+[\d\.]+\d+)', ver_output.decode('cp1252')).group(0)

# Exibir o nome do usuário, nome do computador e versão do Windows
print("\n▼ informação_PC ▼")
print("Nome do usuário:", username)
print("Nome do computador:", computer_name)
print("Versão do Windows:", ver_info)
print()

# Obter informações da CPU
cpu_name = platform.processor()
cpu_cores = psutil.cpu_count(logical=True)
cpu_freq = psutil.cpu_freq()

print("▼ CPU ▼")
print(f"Nome: {cpu_name}")
print(f"Núcleos: {cpu_cores}")
print(f"Frequência: {cpu_freq.max:.2f}MHz (máxima) / {cpu_freq.min:.2f}MHz (mínima)")
print()

# Obter informações da RAM
ram_total = psutil.virtual_memory().total
ram_available = psutil.virtual_memory().available
print("▼ RAM ▼")
print(f"Total: {ram_total/(1024**3):.2f}GB")
print(f"Disponível: {ram_available/(1024**3):.2f}GB")
print()
# Criando uma conexão com o objeto Win32_PhysicalMemory
w = wmi.WMI(namespace="root\\CIMV2")
memory_modules = w.Win32_PhysicalMemory()

# Iterando sobre cada módulo de memória e imprimindo informações
for i, module in enumerate(memory_modules):
    print(f"Módulo de memória {i+1}:")
    print(f"\tFabricante: {module.Manufacturer}")
    print(f"\tModelo: {module.PartNumber}")
    print(f"\tCapacidade: {int(module.Capacity)//(1024**3)} GB")
    print()

# Obter informações do armazenamento
disk_usage = psutil.disk_usage("/")
disk_total = disk_usage.total
disk_used = disk_usage.used
disk_free = disk_usage.free

print("▼ Armazenamento HD ▼")
print(f"Total: {disk_total/(1024**3):.2f}GB")
print(f"Usado: {disk_used/(1024**3):.2f}GB")
print(f"Livre: {disk_free/(1024**3):.2f}GB")
print()

# Informações sobre o sistema operacional
print(f"\nSistema operacional: {platform.system()} {platform.release()} {platform.machine()}")

# Informações sobre a CPU
processor = platform.processor()
cpufreq = psutil.cpu_freq()
print(f"\nCPU: {processor} ({psutil.cpu_count()} cores)")
print(f"\nFrequência: {cpufreq.current:.1f}MHz (min: {cpufreq.min:.1f}MHz, max: {cpufreq.max:.1f}MHz)")

# Informações sobre a RAM
mem = psutil.virtual_memory()
print(f"\nRAM: {mem.total//(1024**3)}GB ({mem.percent}% utilizado)")

# Informações sobre a placa-mãe
w = wmi.WMI()
board = w.Win32_BaseBoard()[0]
print(f"\nPlaca-mãe: {board.Manufacturer} {board.Product}")

# Informações sobre o armazenamento
hdd = psutil.disk_usage('/')
print(f"\nArmazenamento HD: {hdd.total//(1024**3)}GB ({hdd.percent}% utilizado)")
print()

# Criando uma conexão com o objeto Win32_VideoController
w = wmi.WMI(namespace="root\\cimv2")
video_controllers = w.Win32_VideoController()

# Iterando sobre cada placa de vídeo e imprimindo informações
for i, controller in enumerate(video_controllers):
    print("\n▼ placa de video onboard ▼")
    print(f"Placa de vídeo: {controller.Name}")
    #print(f"Descrição: {controller.Description}")
    print(f"Memória dedicada: {controller.AdapterRAM//(1024**2)} MB")

# Informações sobre os gráficos
print("\n▼ placa de video Dedicada ▼")
gpus = GPUtil.getGPUs()

if gpus:
    gpu = gpus[0]
    print(f"Placa de vídeo: {gpu.name}")
    print(f"Uso da GPU: {gpu.load*100}%")
    print(f"Memória total: {gpu.memoryTotal//(1024**2)}MB")
    print(f"Memória utilizada: {gpu.memoryUsed//(1024**2)}MB")
    print(f"Temperatura: {gpu.temperature}°C")
else:
    print("Não foi encontrada nenhuma placa de vídeo Dedicada")


input("\nInformação Terminada [ENTER SAIR]")
