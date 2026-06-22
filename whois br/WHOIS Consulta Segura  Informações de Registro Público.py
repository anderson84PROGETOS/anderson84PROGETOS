import socket
import re
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

# ===================== TRADUÇÃO WHOIS =====================
traducao = {
    "domain:": "Domínio",
    "owner:": "Entidade",
    "ownerid:": "CNPJ",
    "responsible:": "Responsável",
    "country:": "País",
    "created:": "Criado em",
    "changed:": "Alterado em",
    "expires:": "Expira em",
    "status:": "Status",
    "nserver:": "Servidor DNS",
    "nameserver:": "Servidor DNS",
    "nameservers:": "Servidores DNS",
    "person:": "Pessoa",
    "e-mail:": "E-mail",
    "email:": "E-mail",
    "inetnum:": "Faixa de IP",
    "netname:": "Nome da Rede",
    "descr:": "Descrição",
    "org:": "Organização",
    "address:": "Endereço",
    "phone:": "Telefone",
    "abuse-mailbox:": "E-mail de Abuso",
    "source:": "Fonte",
    # Campos .gov e internacionais
    "registrar:": "Registrador",
    "registrant:": "Registrante",
    "registrant organization:": "Organização Registrante",
    "registrant street:": "Endereço",
    "registrant city:": "Cidade",
    "registrant state/province:": "Estado/Província",
    "registrant postal code:": "CEP",
    "registrant country:": "País",
    "registrant phone:": "Telefone",
    "registrant email:": "E-mail",
    "admin:": "Administrador",
    "tech:": "Técnico",
    "name server:": "Servidor DNS",
    "dnssec:": "DNSSEC",
    "domain status:": "Status do Domínio",
    "updated date:": "Atualizado em",
    "creation date:": "Criado em",
    "registry expiry date:": "Expira em",
}

def formatar_data_brasileira(texto):
    formatos = ["%Y-%m-%d", "%Y%m%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"]
    for formato in formatos:
        try:
            data = datetime.strptime(texto.strip(), formato)
            return data.strftime("%d/%m/%Y")
        except:
            continue
    return texto

def traduzir_linha(linha):
    linha_lower = linha.lower()
    for termo, traducao_pt in traducao.items():
        if linha_lower.startswith(termo):
            valor = linha[len(termo):].strip()
            return f"{traducao_pt:<42}: {valor}"
    if ":" in linha:
        campo, valor = linha.split(":", 1)
        campo = campo.strip()
        return f"{campo:<42}: {valor.strip()}"
    return linha

def consultar_whois(entrada):
    try:
        # Detecta tipo
        try:
            socket.inet_pton(socket.AF_INET, entrada)
            tipo = "ipv4"
        except:
            try:
                socket.inet_pton(socket.AF_INET6, entrada)
                tipo = "ipv6"
            except:
                tipo = "dominio"

        if tipo in ["ipv4", "ipv6"]:
            servidor = 'whois.iana.org'
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((servidor, 43))
                s.send((entrada + "\r\n").encode())
                resposta = b""
                while True:
                    dados = s.recv(4096)
                    if not dados: break
                    resposta += dados
            texto_iana = resposta.decode(errors='ignore')
            match = re.search(r"refer:\s*(\S+)", texto_iana, re.IGNORECASE)
            servidor = match.group(1) if match else 'whois.arin.net'
        else:
            tld = '.' + entrada.split('.')[-1].lower()
            servidores_whois_tld = {
                '.com': 'whois.verisign-grs.com',
                '.net': 'whois.verisign-grs.com',
                '.org': 'whois.pir.org',
                '.br': 'whois.registro.br',
                '.gov': 'whois.nic.gov',
                '.edu': 'whois.educause.edu',
            }
            servidor = servidores_whois_tld.get(tld)
            if not servidor:
                return "TLD não suportado no momento."

        # Consulta WHOIS
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(15)
            s.connect((servidor, 43))
            s.send((entrada + "\r\n").encode())
            resposta = b""
            while True:
                dados = s.recv(4096)
                if not dados: break
                resposta += dados

        texto = resposta.decode(errors='ignore')

        # ==================== LIMPEZA DE DISCLAIMERS ====================
        texto = re.sub(
            r'(Information.*?support.*?access.*?)(\n\n|\Z)',
            '',
            texto,
            flags=re.IGNORECASE | re.DOTALL
        )

        linhas = texto.splitlines()
        saida_formatada = ["=" * 90, f"WHOIS → {entrada.upper()}", "=" * 90, ""]

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            linha_lower = linha.lower()
            
            if re.search(r'copyright|terms|usage|legal|reserved|icann|verisign|notice|for more|information is provided', linha_lower):
                continue

            disclaimers = ["information is provided", "informational purposes", "as is without", "guarantee of accuracy"]
            if any(frase in linha_lower for frase in disclaimers):
                continue

            if linha.startswith(('%', '#', '>>>', '---', '==')):
                continue

            # Formatar datas
            linha = re.sub(r"\d{4}-\d{2}-\d{2}(T[\d:.Z]+)?|\d{8}",
                          lambda m: formatar_data_brasileira(m.group()), linha)

            linha_traduzida = traduzir_linha(linha)
            saida_formatada.append(linha_traduzida)

        return "\n".join(saida_formatada)

    except Exception as e:
        return f"[-] Erro na consulta: {e}"

# ===================== INTERFACE =====================
root = tk.Tk()
root.title("WHOIS • Consulta Segura • Informações de Registro Público")
root.geometry("1000x720")
root.configure(bg="#0a0a0a")
root.wm_state('zoomed')

fonte_titulo = ("Consolas", 16, "bold")
fonte_texto = ("Consolas", 12)          # ← Alterado para 12

header = tk.Label(root, text="WHOIS • Consulta Segura • Informações de Registro Público",
                  font=("Consolas", 15, "bold"), fg="#00ff41", bg="#0a0a0a")
header.pack(pady=10)

label_domain = tk.Label(root, text="ALVO (domínio ou IP)",
                        font=fonte_titulo, fg="#00ff41", bg="#0a0a0a")
label_domain.pack(pady=5)

entry_domain = tk.Entry(root, font=("Consolas", 14), width=50,
                        bg="#1a1a1a", fg="#00ff41", insertbackground="#00ff41",
                        relief="solid", bd=2)
entry_domain.pack(pady=8)

frame_botoes = tk.Frame(root, bg="#0a0a0a")
frame_botoes.pack(pady=12)

btn_consultar = tk.Button(frame_botoes, text="INICIAR SCAN", font=("Consolas", 12, "bold"),
                          bg="#001a00", fg="#00ff41", activebackground="#00ff80",
                          activeforeground="black", width=20, height=2,
                          command=lambda: consultar_e_mostrar())
btn_consultar.pack(side=tk.LEFT, padx=15)

btn_txt = tk.Button(frame_botoes, text="SALVAR EM TXT", font=("Consolas", 12, "bold"),
                    bg="#001a00", fg="#00ff41", activebackground="#00ff80",
                    activeforeground="black", width=20, height=2,
                    command=lambda: salvar_txt())
btn_txt.pack(side=tk.LEFT, padx=15)

# ScrolledText com fonte 12 e sem quebra de linha
text_output = ScrolledText(root, font=fonte_texto, bg="#000000", fg="#00ff41",
                           insertbackground="#00ff41", relief="solid", bd=3,
                           selectbackground="#00ff80", selectforeground="black",
                           wrap="none")   # ← Sem quebra de linha

text_output.pack(pady=15, padx=20, fill=tk.BOTH, expand=True)

# Tags de cores
text_output.tag_configure("cnpj", foreground="#ff0000", font=("Consolas", 12, "bold"))
text_output.tag_configure("email", foreground="#ff7f00", font=("Consolas", 12, "bold"))
text_output.tag_configure("header", foreground="#00ff80", font=("Consolas", 13, "bold"))

footer = tk.Label(root, text="WHOIS • Consulta Segura • Informações de Registro Público",
                  font=("Consolas", 9), fg="#008800", bg="#0a0a0a")
footer.pack(side=tk.BOTTOM, pady=8)

# ===================== FUNÇÕES DA INTERFACE =====================
def consultar_e_mostrar():
    dominio = entry_domain.get().strip()
    if not dominio:
        messagebox.showerror("ERRO", "Digite um alvo válido.")
        return
   
    text_output.delete(1.0, tk.END)
    text_output.insert(tk.END, f"[+] Iniciando consulta WHOIS em {dominio}...\n\n", "header")
    root.update()
   
    resultado = consultar_whois(dominio)
    text_output.delete(1.0, tk.END)
   
    for linha in resultado.splitlines():
        if "CNPJ" in linha:
            text_output.insert(tk.END, linha + "\n", "cnpj")
        elif "E-mail" in linha or "Abuse" in linha:
            text_output.insert(tk.END, linha + "\n", "email")
        elif linha.startswith("=") or "WHOIS →" in linha:
            text_output.insert(tk.END, linha + "\n", "header")
        else:
            text_output.insert(tk.END, linha + "\n")

def salvar_txt():
    dominio = entry_domain.get().strip()
    if not dominio:
        messagebox.showerror("ERRO", "Nenhum alvo informado.")
        return
    texto = text_output.get(1.0, tk.END).strip()
    if not texto:
        messagebox.showerror("ERRO", "Faça uma consulta antes.")
        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt")],
        initialfile=f"whois_{dominio.replace('.', '_')}"
    )
    if not caminho:
        return

    try:
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(f"WHOIS REPORT - {dominio.upper()}\n")
            f.write("="*90 + "\n\n")
            f.write(texto)
        messagebox.showinfo("SUCESSO", f"Arquivo TXT salvo com sucesso:\n{caminho}")
    except Exception as e:
        messagebox.showerror("ERRO", str(e))

root.mainloop()
