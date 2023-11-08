import tkinter as tk
import pyperclip
import dns.resolver
import os
import sys  # Adicione esta linha para importar o módulo sys

# Redirecionar stdout e stderr para um arquivo vazio
devnull = open(os.devnull, 'w')
sys.stdout = devnull
sys.stderr = devnull

def search_domain():
    domain = domain_entry.get().strip()
    record_type = record_type_var.get()  # Obtém o tipo de registro selecionado

    # Mapeamento dos tipos de registro DNS para suas descrições
    type_descriptions = {
        "A": "      🔜 " "Mapeia um nome de domínio para um endereço IPv4.",
        "AAAA": "   🔜 " "Mapeia um nome de domínio para um endereço IPv6.",
        "NS": "     🔜 " "Define os servidores de nomes autorizados para um domínio.",
        "PTR": "    🔜 " "É usado para fazer uma pesquisa inversa, mapeando um endereço IP para um nome de domínio.",
        "TXT": "    🔜 " "Armazena texto associado a um nome de domínio, frequentemente usado para informações de autenticação e políticas de segurança.",
        "MX": "     🔜 " "Define os servidores de email que recebem mensagens de email para um domínio.",
        "SOA": "    🔜 " "Contém informações sobre a zona de autoridade de um domínio, como o endereço de email do administrador.",
        "DS":  "    🔜 " "É usado em registros DNSSEC para prover informações de segurança sobre a zona.",
        "SRV": "    🔜 " "Define serviços disponíveis em um domínio, frequentemente usados para localizar servidores de chat, voip.",
        "NSEC3": "  🔜 " "É um registro de negação de autenticação usado para reforçar a segurança no DNSSEC.",
        "HINFO": "  🔜 " "Armazena informações sobre o tipo de hardware e sistema operacional de um host.",
        "CNAME": "  🔜 " "Mapeia um nome de domínio para outro nome de domínio, frequentemente usado para criar alias."
    }

    try:
        result = dns.resolver.query(domain, record_type)
        results = [f'{record_type} Records for {domain}: {type_descriptions.get(record_type, "Descrição não encontrada.")}']
        for r in result:
            results.append(r.to_text())

        email_list.delete(0, tk.END)
        for result in results:
            email_list.insert(tk.END, result)
    except dns.resolver.NXDOMAIN:
        email_list.delete(0, tk.END)
        email_list.insert(tk.END, f"Erro - Domínio não encontrado")
    except dns.resolver.NoAnswer:
        email_list.delete(0, tk.END)
        email_list.insert(tk.END, f"Erro - Nenhum registro {record_type} encontrado")

def copy_results():
    results = email_list.get(0, tk.END)
    results_str = "\n".join(results)
    pyperclip.copy(results_str)

def clear_results():
    email_list.delete(0, tk.END)  # Limpa apenas a lista de resultados

# Configurar a janela principal
window = tk.Tk()
window.title("DNS Info")
window.geometry("800x600")
window.wm_state('zoomed')

# Adicionar widgets
domain_label = tk.Label(window, text="Digite o domínio", font=("Arial", 14))
domain_label.pack()

domain_entry = tk.Entry(window, width=50, font=("Arial", 14))
domain_entry.pack()

record_type_label = tk.Label(window, text="Selecione o tipo de registro", font=("Arial", 14))
record_type_label.pack()

record_type_var = tk.StringVar()
record_type_var.set("A")  # Tipo de registro padrão

# Adicione as opções adicionais aqui
record_type_option_menu = tk.OptionMenu(window, record_type_var, "A", "AAAA", "NS", "PTR", "TXT", "MX", "SOA", "DS", "SRV", "NSEC3", "HINFO", "CNAME")
record_type_option_menu.configure(bg="#07fa81")
record_type_option_menu.pack()

search_button = tk.Button(window, text="Buscar", font=("Arial", 14), command=search_domain, bg="#00FFFF")
search_button.pack(pady=5)

email_list = tk.Listbox(window, width=140, height=37, font=("Arial", 12))
email_list.pack(pady=5)

copy_button = tk.Button(window, text="Copiar resultados", font=("Arial", 14), command=copy_results)
copy_button.pack()

clear_button = tk.Button(window, text="Limpar resultados", font=("Arial", 14), command=clear_results, bg="#f54254")
clear_button.pack()

# Iniciar a janela principal
window.mainloop()
