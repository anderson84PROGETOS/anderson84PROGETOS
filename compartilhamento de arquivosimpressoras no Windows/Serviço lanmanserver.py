import subprocess
import tkinter as tk
from tkinter import messagebox

SERVICE_NAME = "lanmanserver"

def run_powershell(cmd):
    # Removido print para não mostrar no terminal
    completed = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
    # Remover prints de saída e erro para não aparecer no terminal
    # if completed.stdout:
    #     print(completed.stdout.strip())
    # if completed.stderr:
    #     print("Erro:", completed.stderr.strip())
    if completed.returncode == 0:
        return completed.stdout.strip()
    else:
        return None

def get_service_status():
    cmd = f"Get-Service -Name {SERVICE_NAME}"
    output = run_powershell(cmd)
    if output:
        return output
    else:
        return "Erro ao obter status."

def activate_service():
    cmd1 = f"Set-Service -Name {SERVICE_NAME} -StartupType Automatic"
    cmd2 = f"Start-Service -Name {SERVICE_NAME}"
    run_powershell(cmd1)
    run_powershell(cmd2)
    messagebox.showinfo("Sucesso", "Serviço ativado.")
    update_status()

def deactivate_service():
    cmd1 = f"Set-Service -Name {SERVICE_NAME} -StartupType Disabled" # Set-Service -Name lanmanserver -StartupType Disabled
    cmd2 = f"Stop-Service -Name {SERVICE_NAME}"
    run_powershell(cmd1)
    run_powershell(cmd2)
    messagebox.showinfo("Sucesso", "Serviço desativado.")
    update_status()

def update_status():
    status = get_service_status()
    # Removido print para não mostrar no terminal
    # print(status)
    text_output.delete(1.0, tk.END)
    text_output.insert(tk.END, status)

root = tk.Tk()
root.title("Gerenciador do Serviço lanmanserver")
root.geometry("500x350")

btn_status = tk.Button(root, text="Mostrar Status", command=update_status, width=30, font=("Arial", 12), bg="#4CAF50", fg="white", activebackground="#45a049")
btn_status.pack(pady=5)

btn_activate = tk.Button(root, text="Ativar Serviço", command=activate_service, width=30, font=("Arial", 12), bg="#2196F3", fg="white", activebackground="#1e88e5")
btn_activate.pack(pady=5)

btn_deactivate = tk.Button(root, text="Desativar Serviço", command=deactivate_service, width=30, font=("Arial", 12), bg="#f44336", fg="white", activebackground="#d32f2f")
btn_deactivate.pack(pady=5)

text_output = tk.Text(root, height=10, width=60, font=("Consolas", 11))
text_output.pack(pady=10)

root.mainloop()
