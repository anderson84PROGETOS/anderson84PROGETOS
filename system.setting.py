import platform
import tkinter as tk
import wmi
import psutil
import wmi
import getpass
import socket
import psutil

root = tk.Tk()
root.geometry('600x1000')

# Obtém informações sobre o sistema operacional
system_name = platform.system()
system_version = platform.release()
root.title('Informações do sistema')
# Adiciona o rótulo com o nome do sistema operacional
tk.Label(root, text=f'\nSistema operacional: {system_name} {system_version}').pack()

# System information
uname = platform.uname()
username = f'Username: {getpass.getuser()}'
computername = f'Computer Name: {socket.gethostname()}'
node = f'Node Name: {uname.node}'
version = f'Version: {uname.version}'
machine = f'Machine: {uname.machine}'
processor = f'Processor: {uname.processor}'
boot_time = f'Boot Time: {psutil.boot_time()}'

tk.Label(root, text=username).pack(pady=5)
tk.Label(root, text=node).pack(pady=5)
tk.Label(root, text=version).pack(pady=5)
tk.Label(root, text=machine).pack(pady=5)
tk.Label(root, text=processor).pack(pady=5)

# RAM information
ram = psutil.virtual_memory()
total_ram = f'Total RAM: {round(ram.total/(1024*1024), 2)} MB'
available_ram = f'Available RAM: {round(ram.available/(1024*1024), 2)} MB'
used_ram = f'Used RAM: {round(ram.used/(1024*1024), 2)} MB'
percent_ram_used = f'Percent RAM used: {ram.percent}%'

# Get the main disk drive
tk.Label(root, text='#################################### Disco Information ####################################').pack(pady=10)
disk = psutil.disk_usage('/')
disk_name = f'Disk Name: {psutil.disk_partitions()[0].device}'
disk_total = f'Total Disk Space: {disk.total//(2**30)} GB'
disk_used = f'Used Disk Space: {disk.used//(2**30)} GB'
disk_free = f'Free Disk Space: {disk.free//(2**30)} GB'

tk.Label(root, text=boot_time).pack(pady=5)
tk.Label(root, text=disk_name).pack(pady=5)
tk.Label(root, text=disk_total).pack(pady=5)
tk.Label(root, text=disk_used).pack(pady=5)
tk.Label(root, text=disk_free).pack(pady=5)

# obtém o nome da memória RAM
w = wmi.WMI()
memory_ram = w.Win32_PhysicalMemory()[0].PartNumber

# exibe o nome da memória RAM na janela
tk.Label(root, text='#################################### RAM Information ####################################').pack(pady=10)
tk.Label(root, text=total_ram).pack(pady=5)
tk.Label(root, text=available_ram).pack(pady=5)
tk.Label(root, text=used_ram).pack(pady=5)
tk.Label(root, text=percent_ram_used).pack(pady=5)
tk.Label(root, text=f'Memory_Ram: {memory_ram}').pack(pady=5)

# Motherboard information
w = wmi.WMI()
board = w.Win32_BaseBoard()[0]
board_manufacturer = f'Manufacturer: {board.Manufacturer}'
board_product = f'Product: {board.Product}'

tk.Label(root, text='#################################### Motherboard Information ####################################').pack(pady=10)
tk.Label(root, text=board_manufacturer).pack(pady=5)
tk.Label(root, text=board_product).pack(pady=5)

# Get video controller information
w = wmi.WMI()
video_controllers = w.Win32_VideoController()

# Display information for each video controller
tk.Label(root, text='#################################### Video Controller Information ####################################').pack(pady=10)
for i, controller in enumerate(video_controllers):
    name = f'Name ({i+1}): {controller.Name}'
    status = f'Status ({i+1}): {controller.Status}'
    adapter_ram = f'Adapter RAM ({i+1}): {controller.AdapterRAM//(2**20)} MB'
    driver_version = f'Driver Version ({i+1}): {controller.DriverVersion}'
    tk.Label(root, text=name).pack(pady=5)
    tk.Label(root, text=status).pack(pady=5)
    tk.Label(root, text=adapter_ram).pack(pady=5)
    tk.Label(root, text=driver_version).pack(pady=5) 
#####################################################
# PULAR LINHA
root.title('Pular uma linha')
# Adiciona o primeiro rótulo
tk.Label(root, text=' ').pack()

# Função chamada quando o botão de saída é clicado
def exit_program():    
        root.destroy()
root.title('system.setting')
# Cria o botão de saída
exit_button = tk.Button(root, text='SYSTEM SETTING APERTE PARA SAIR', bg='blue', fg='white', command=exit_program)
exit_button.pack(padx=10, pady=10)

root.mainloop()

