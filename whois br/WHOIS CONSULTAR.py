import socket
import re
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading


# ==================== CORES ====================
class Colors:
    BG = "#0a0a0a"
    FG = "#00ff41"
    ACCENT = "#00ff9d"
    CNPJ_COLOR = "#ff8c00"    # Laranja Abóbora
    EMAIL_COLOR = "#00b7ff"   # Azul Neon
    RED = "#ff0044"

# Tradução dos campos
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
    "nameservers:": "Servidor DNS",
    "person:": "Pessoa",
    "e-mail:": "E-mail",
    "email:": "E-mail",
    "inetnum:": "Faixa de IP",
    "netname:": "Nome da Rede",
    "descr:": "Descrição",
    "org:": "Organização",
    "address:": "Endereço",
    "phone:": "Telefone",
    "abuse-mailbox:": "Abuse E-mail",
}

servidores_whois_tld = {
    '.com': 'whois.verisign-grs.com',
    '.net': 'whois.verisign-grs.com',
    '.org': 'whois.pir.org',
    '.br': 'whois.registro.br',
    '.gov': 'whois.dotgov.gov',
    '.edu': 'whois.educause.edu',
    '.io': 'whois.nic.io',
    '.dev': 'whois.nic.dev',
    '.app': 'whois.nic.google',
}

def formatar_data_brasileira(texto):
    formatos = ["%Y-%m-%d", "%Y%m%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"]
    for fmt in formatos:
        try:
            data = datetime.strptime(texto.strip(), fmt)
            return data.strftime("%d/%m/%Y %H:%M")
        except:
            continue
    return texto

def traduzir_linha(linha):
    linha = linha.strip()
    for termo, traducao_pt in traducao.items():
        if linha.lower().startswith(termo):
            valor = linha[len(termo):].strip()
            return f"{traducao_pt:<30} : {valor}", traducao_pt
    if ":" in linha:
        campo, valor = linha.split(":", 1)
        return f"{campo.strip():<30} : {valor.strip()}", campo.strip()
    return linha, None

# ==================== CONSULTA WHOIS (Sua versão) ====================
def consultar_whois(entrada):
    try:
        # Detecta se é IP
        try:
            socket.inet_pton(socket.AF_INET, entrada)
            tipo = "ipv4"
        except:
            try:
                socket.inet_pton(socket.AF_INET6, entrada)
                tipo = "ipv6"
            except:
                tipo = "dominio"

        # Para IPs, busca servidor via IANA
        if tipo in ["ipv4", "ipv6"]:
            servidor_iana = 'whois.iana.org'
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(12)
                s.connect((servidor_iana, 43))
                s.send((entrada + "\r\n").encode())
                resposta = b""
                while True:
                    dados = s.recv(4096)
                    if not dados:
                        break
                    resposta += dados
            texto_iana = resposta.decode(errors='ignore')
            match = re.search(r"refer:\s*(\S+)", texto_iana)
            servidor = match.group(1) if match else 'whois.arin.net'
        else:
            tld = '.' + entrada.split('.')[-1]
            servidor = servidores_whois_tld.get(tld.lower())
            if not servidor:
                return [("❌ TLD não suportado.", None)]

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(12)
            s.connect((servidor, 43))
            s.send((entrada + "\r\n").encode())
            resposta = b""
            while True:
                dados = s.recv(4096)
                if not dados:
                    break
                resposta += dados

        texto = resposta.decode(errors='ignore')
        linhas = texto.splitlines()
        saida_formatada = []

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            # Ignorar linhas técnicas e comentários
            if re.search(r'copyright|terms|usage|legal|reserved|icann|verisign|notice|last update|for more information|registry database|compilation|repackaging|electronic processes|high-volume|automated', linha, re.IGNORECASE):
                continue

            if linha.startswith(('%', '#', '>')):
                continue

            # Ignorar disclaimers (duas grandes regex)
            if re.search(r"""
                (registrar's\s+sponsorship|
                domain\s+name\s+registration|
                expiration\s+date|
                sponsoring\s+registrar|
                whois\s+database|
                information\s+purposes|
                guarantee\s+its\s+accuracy|
                abide|
                lawful\s+purposes|
                unsolicited|
                commercial\s+advertising|
                restrict\s+your\s+access|
                electronic\s+processes|
                high-volume|
                automated|
                legal|
                reserved|
                terms|
                usage|
                copyright|
                notice|
                compilation|
                repackaging|
                icann|
                last\s+update|
                for\s+more\s+information|
                registry\s+database|
                currently\s+set\s+to\s+expire|
                support\s+the\s+transmission|
                registrant's\s+agreement|
                Registrars.|
                reported\s+date\s+of\s+expiration)
                """, linha, re.IGNORECASE | re.VERBOSE):
                continue

            if re.search(r"""
                (registrar's\s+sponsorship|
                domain\s+name\s+registration|
                expiration\s+date|
                sponsoring\s+registrar|
                whois\s+database|
                information\s+purposes|
                informational\s+purposes|
                guarantee\s+its\s+accuracy|
                guarantee\s+of\s+accuracy|
                "as\s+is"|
                abide|
                lawful\s+purposes|
                unlawful\s+behavior|
                unsolicited|
                commercial\s+advertising|
                support\s+unlawful|
                restrict\s+or\s+deny\s+your\s+access|
                restrict\s+your\s+access|
                electronic\s+processes|
                high-volume|
                automated|
                legal|
                reserved|
                terms|
                usage|
                copyright|
                notice|
                compilation|
                repackaging|
                icann|
                last\s+update|
                for\s+more\s+information|
                registry\s+database|
                currently\s+set\s+to\s+expire|
                support\s+the\s+transmission|
                registrant's\s+agreement|
                reported\s+date\s+of\s+expiration|
                we\s+reserve\s+the\s+right|
                modify\s+existing\s+registrations|
                domain\s+names\s+or\s+modify|
                provided\s+by\s+the\s+registry|
                allow,\s+enable,\s+or\s+otherwise\s+support)
                """, linha, re.IGNORECASE | re.VERBOSE):
                continue

            # Formatar datas
            def substituir_data(match):
                return formatar_data_brasileira(match.group())

            linha = re.sub(
                r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z)?|\d{8}",
                substituir_data,
                linha
            )

            linha_traduzida, campo = traduzir_linha(linha)
            saida_formatada.append((linha_traduzida, campo))

        return saida_formatada if saida_formatada else [("Nenhuma informação útil retornada.", None)]

    except Exception as e:
        return [(f"❌ Erro ao consultar WHOIS: {e}", None)]

# ==================== INTERFACE ====================
def consultar_e_mostrar():
    dominio = entry.get().strip()
    if not dominio:
        messagebox.showerror("Erro", "Digite um domínio ou IP")
        return

    text_output.delete(1.0, tk.END)
    text_output.insert(tk.END, f"🔍 Consultando {dominio.upper()}\n\n", "info")
    root.update()

    def thread_consulta():
        resultado = consultar_whois(dominio)
        text_output.delete(1.0, tk.END)
        text_output.insert(tk.END, f"🌐 WHOIS- {dominio.upper()}\n", "title")
        text_output.insert(tk.END, "="*85 + "\n\n", "separator")

        for item in resultado:
            if isinstance(item, tuple) and len(item) == 2:
                linha, campo = item
            else:
                linha = str(item)
                campo = None

            if campo and ("CNPJ" in str(campo) or "ownerid" in str(campo).lower()):
                text_output.insert(tk.END, linha + "\n", "cnpj")
            elif campo and ("E-mail" in str(campo) or "email" in str(campo).lower()):
                text_output.insert(tk.END, linha + "\n", "email")
            else:
                text_output.insert(tk.END, linha + "\n")

    threading.Thread(target=thread_consulta, daemon=True).start()

# ==================== SALVAR TXT ====================
def salvar_txt():
    dominio = entry.get().strip().lower()
    if not dominio:
        messagebox.showerror("Erro", "Digite um domínio ou IP.")
        return
    texto = text_output.get(1.0, tk.END).strip()
    if not texto or "Consultando" in texto:
        messagebox.showerror("Erro", "Faça a consulta antes.")
        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Arquivos de Texto", "*.txt")],
        initialfile=f"whois_{dominio.replace('.', '_')}.txt"
    )
    if not caminho:
        return

    try:
        with open(caminho, 'w', encoding='utf-8') as arquivo:
            arquivo.write(f"WHOIS RESULTADO - Consulta: {dominio.upper()}\n")
            arquivo.write("="*80 + "\n\n")
            arquivo.write(texto)
        messagebox.showinfo("✅ Sucesso", f"Arquivo TXT salvo com sucesso\n\n{caminho}")
    except Exception as e:
        messagebox.showerror("Erro ao salvar TXT", str(e))

# ==================== GUI ====================
root = tk.Tk()
root.title("⚡ WHOIS CONSULTAR")
root.geometry("1080x740")
root.wm_state('zoomed')  # janela maximizada
root.configure(bg=Colors.BG)

tk.Label(root, text="WHOIS CONSULTAR ", font=("Courier", 26, "bold"), 
         fg=Colors.FG, bg=Colors.BG).pack(pady=12)

tk.Label(root, text="Digite o domínio ou IP", font=("Courier", 12), 
         fg=Colors.ACCENT, bg=Colors.BG).pack(pady=5)

entry = tk.Entry(root, font=("Courier", 14), width=60, 
                 bg="#1a1a1a", fg=Colors.FG, insertbackground=Colors.ACCENT)
entry.pack(pady=8)

btn_frame = tk.Frame(root, bg=Colors.BG)
btn_frame.pack(pady=12)

tk.Button(btn_frame, text="⚡ CONSULTAR", font=("Courier", 12, "bold"),
          bg="#00ff41", fg="black", width=18, height=2,
          command=consultar_e_mostrar).pack(side=tk.LEFT, padx=10)

tk.Button(btn_frame, text="💾 SALVAR TXT", font=("Courier", 12, "bold"),
          bg=Colors.RED, fg="white", width=18, height=2,
          command=salvar_txt).pack(side=tk.LEFT, padx=10)

text_output = ScrolledText(root, font=("Courier", 11), bg="#0a0a0a", fg=Colors.FG,
                           insertbackground=Colors.FG, selectbackground="#00ff9d", height=28)
text_output.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

# Na parte da GUI, adicione isso no ScrolledText:
text_output.tag_config("cnpj", foreground=Colors.CNPJ_COLOR, font=("Courier", 10, "bold"))
text_output.tag_config("email", foreground=Colors.EMAIL_COLOR, font=("Courier", 10, "bold"))

text_output.tag_config("title", foreground=Colors.ACCENT, font=("Courier", 12, "bold"))
text_output.tag_config("info", foreground=Colors.FG)
text_output.tag_config("separator", foreground="#555555")
text_output.tag_config("cnpj", foreground=Colors.CNPJ_COLOR, font=("Courier", 11, "bold"))
text_output.tag_config("email", foreground=Colors.EMAIL_COLOR, font=("Courier", 11, "bold"))

footer = tk.Label(root, text="🟠 WHOIS CONSULTAR 🔵 ", 
                  font=("Courier", 9), fg="#444444", bg=Colors.BG)
footer.pack(pady=5)

root.mainloop()
