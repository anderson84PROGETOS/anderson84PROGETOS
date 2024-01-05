import tkinter as tk
from tkinter import scrolledtext
import subprocess

def run_all_queries():
    result_text.delete(1.0, tk.END)  # Limpar o texto existente
    site_or_url = entry.get()

    query_types = ["A", "AAAA", "ANY", "CAA", "CNAME", "DNSKEY", "DS", "MX", "NS", "PTR", "SOA", "SRV", "TLSA", "TSIG", "TXT", "HINFO", "NSEC3"]
    query_descriptions = {
        "A": "Retorna um endereço IPv4: O registro A do DNS aponta para o endereço de IP de um determinado nome de domínio.\n",
        "AAAA": "Retorna um endereço IPv6: O registro de DNS AAAA combina um nome de domínio com um endereço IPv6.\n",
        "ANY": "Retorna todos os registros de todos os tipos conhecidos pelo servidor de nomes. Se o servidor de nomes não tiver nenhuma informação sobre o nome.\n",
        "CAA": "Autorização da autoridade de certificação DNS , restringindo CAs aceitáveis ​​para um host/domínio.\n",
        "CNAME": "O registro CNAME de DNS funciona como um pseudônimo para os nomes de domínio que compartilham um único endereço IP.\n",
        "DNSKEY": "O registro de chave usado no DNSSEC . Usa o mesmo formato do registro KEY.\n",
        "DS": "O registro usado para identificar a chave de assinatura DNSSEC de uma zona delegada.\n",
        "MX": "O registro MX direciona os e-mails para um servidor de troca de e-mails.\n",
        "NS": "O registro NS indica qual servidor DNS é autoritário.\n",
        "PTR": "O registro PTR é usado para pesquisas de DNS reverso.\n",
        "SOA": "O registro SOA contém informações importantes sobre um domínio e sobre quem é responsável por ele.\n",
        "SRV": "O registro SRV é utilizado para serviços especiais como o VoIP.\n",
        "TLSA": "O registro de recurso DNS TLSA é usado para associar um certificado de servidor TLS ou chave pública ao nome de domínio onde o registro é encontrado.\n",
        "TSIG": "Pode ser usado para autenticar atualizações dinâmicas como provenientes de um cliente aprovado ou para autenticar respostas como provenientes de um servidor de nomes recursivo aprovado [13] semelhante ao DNSSEC.\n",
        "TXT": "O registro TXT permite que um administrador de domínio deixe notas em um servidor de DNS.\n",
        "HINFO": "Armazena informações sobre o tipo de hardware e sistema operacional de um host.\n",
        "NSEC3": "É um registro de negação de autenticação usado para reforçar a segurança no DNSSEC.\n",
    }

    for query_type in query_types:
        command = f"nslookup -type={query_type} {site_or_url}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        # Adiciona a descrição em vermelho usando tags
        result_text.tag_configure(f"{query_type}_tag", foreground="#fc0834")
        result_text.insert(tk.END, f"{query_type}  ➡️ {query_descriptions[query_type]}\n", f"{query_type}_tag")
                  
        result_text.insert(tk.END, result.stdout)
        result_text.insert(tk.END, result.stderr)
        result_text.insert(tk.END, "\n\n")

# Criar a janela principal
window = tk.Tk()
window.wm_state('zoomed')
window.title("Consulta DNS")

# Criar e posicionar os widgets
entry_label = tk.Label(window, text="Digite o Nome do WebSite", font=("Arial", 12))
entry_label.grid(column=0, row=0, padx=10, pady=5, columnspan=2)

entry = tk.Entry(window, width=30, font=("Arial", 12))
entry.grid(column=0, row=1, padx=10, pady=10, columnspan=2)

run_button = tk.Button(window, text="Executar Consultas", command=run_all_queries, font=("Arial", 12), background="#11e7f2")
run_button.grid(column=0, row=2, columnspan=2, pady=10)

result_frame = tk.Frame(window)
result_frame.grid(column=0, row=3, columnspan=2)

result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=133, height=42, font=("Arial", 12))
result_text.grid(column=0, row=0, sticky=tk.W, padx=40, pady=10)

window.mainloop()
