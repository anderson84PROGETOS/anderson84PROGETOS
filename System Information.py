import platform
import getpass
import socket
import tkinter as tk
import wmi

root = tk.Tk()
root.geometry('400x300')
root.title('System Information')

uname = platform.uname()
system = f'System: {uname.system}'

release = f'Release: {uname.release}'
version = f'Version: {uname.version}'
machine = f'Machine: {uname.machine}'
processor = f'Processor: {uname.processor}'

username = f'Username: {getpass.getuser()}'
computername = f'Computer Name: {socket.gethostname()}'


tk.Label(root, text=system).pack(pady=5)

tk.Label(root, text=release).pack(pady=5)
tk.Label(root, text=version).pack(pady=5)
tk.Label(root, text=machine).pack(pady=5)
tk.Label(root, text=processor).pack(pady=5)
tk.Label(root, text=username).pack(pady=5)
tk.Label(root, text=computername).pack(pady=5)

# obtém o nome da memória RAM
w = wmi.WMI()
memory_ram = w.Win32_PhysicalMemory()[0].PartNumber

# exibe o nome da memória RAM na janela
tk.Label(root, text=f'Memory_Ram: {memory_ram}').pack(pady=5)

root.mainloop()
