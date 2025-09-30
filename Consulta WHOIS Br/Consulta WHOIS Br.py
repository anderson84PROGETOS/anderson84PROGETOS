import socket
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import re

# Traduções completas
traducoes_completas = {
    "domain": "Domínio",
    "owner": "Titular",
    "ownerid": "Documento",
    "responsible": "Responsável",
    "country": "País",
    "phone": "Telefone",
    "owner-c": "Titular-c",
    "tech-c": "Tecnologia-c",
    "nserver": "Servidor DNS",
    "nsstat": "Status DNS",
    "nslastaa": "Última verificação DNS",
    "dsrecord": "Registro DS",
    "dsstatus": "Status DS",
    "dslastok": "Último DSOK",
    "created": "Criado",
    "changed": "Alterado",
    "expires": "Expiração",
    "status": "Status",
    "nic-hdl-br": "NIC-hdl",   
    "person": "Pessoa Nome",
    "e-mail": "E-mail",    
    "registrar": "Registrador",
    "contact": "Contato",
    "saci": "SACI",
    "tech": "Contato Técnico",
    "admin-c": "Contato Administrativo",
    "billing-c": "Contato Financeiro",
    "org": "Organização",
    "address": "Endereço",
    "postalcode": "CEP",
    "city": "Cidade",
    "state": "Estado",
    "remarks": "Observações",
    "remark": "Observações",
    "statusmsg": "Mensagem de Status",
    "ref": "Referência",
    "registrar-url": "Site do Registrador",
    "registrant-type": "Tipo de Registrante"
}

# Regex para detectar datas YYYYMMDD ou YYYY-MM-DD
regex_datas = re.compile(r'(\b\d{8}\b|\b\d{4}-\d{2}-\d{2}\b)')

def formatar_datas_em_linha(linha):
    """Formata todas as datas encontradas em uma linha para DD/MM/AAAA"""
    def substituir(match):
        data_str = match.group(0)
        formatos = ["%Y%m%d", "%Y-%m-%d"]
        for fmt in formatos:
            try:
                dt = datetime.strptime(data_str, fmt)
                return dt.strftime("%d/%m/%Y")
            except:
                continue
        return data_str
    return regex_datas.sub(substituir, linha)

# Consulta WHOIS via socket
def requisicao_whois(dominio):
    servidor = 'whois.registro.br'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    resultado = ''
    try:
        s.connect((servidor, 43))
        s.send((dominio + "\r\n").encode())
        while True:
            dados = s.recv(65535)
            if not dados:
                break
            resultado += dados.decode(errors='ignore')
    except Exception as e:
        resultado = f"⚠️ Erro: {e}"
    finally:
        s.close()
    # Remove linhas de comentário que começam com %
    resultado = "\n".join(l for l in resultado.splitlines() if not l.strip().startswith("%"))
    return resultado

# Traduz e formata o WHOIS
def traduzir_whois_br(texto):
    resumo = []
    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha:
            continue

        # Detecta chave e valor
        if ":" in linha:
            chave, valor = linha.split(":", 1)
        else:
            partes = linha.split(maxsplit=1)
            if len(partes) == 2:
                chave, valor = partes
            else:
                resumo.append(linha)
                continue

        chave_lower = chave.strip().lower()
        valor = valor.strip()
        chave_traduzida = traducoes_completas.get(chave_lower, chave)

        # Formata datas na linha inteira
        valor = formatar_datas_em_linha(valor)

        resumo.append(f"{chave_traduzida:<30} {valor}")

        # Adiciona linha em branco APENAS após NIC-hdl
        if chave_lower == "nic-hdl-br":
            resumo.append("")  # linha em branco

    return "\n".join(resumo)


# Interface Tkinter
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Consulta WHOIS BR")
        self.geometry("1050x870")
        self.criar_interface()

    def criar_interface(self):
        frm_topo = ttk.Frame(self)
        frm_topo.pack(pady=5)
        ttk.Label(frm_topo, text="🔎 Digite o domínio para consulta 🔍", font=("Arial", 10)).pack(pady=5)

        self.entrada_dominio = ttk.Entry(frm_topo, width=42, font=("Arial", 10))
        self.entrada_dominio.pack(padx=5)

        botoes_frame = ttk.Frame(frm_topo)
        botoes_frame.pack(pady=5)

        botao_buscar = tk.Button(botoes_frame, text="Consultar WHOIS", bg="#03fc0b", fg="black", command=self.buscar)
        botao_buscar.pack(side="left", padx=5)

        botao_salvar = tk.Button(botoes_frame, text="💾 Salvar Resultado", bg="#fc9d03", fg="black", command=self.salvar)
        botao_salvar.pack(side="left", padx=5)

        botao_limpar = tk.Button(botoes_frame, text="🧹 Limpar", bg="#03e8fc", fg="black", command=self.limpar)
        botao_limpar.pack(side="left", padx=5)

        frm_texto = ttk.Frame(self)
        frm_texto.pack(pady=5)

        scrollbar = ttk.Scrollbar(frm_texto)
        scrollbar.pack(side='right', fill='y')

        self.caixa_texto = tk.Text(frm_texto, width=120, height=45, yscrollcommand=scrollbar.set)
        self.caixa_texto.pack(pady=5)
        scrollbar.config(command=self.caixa_texto.yview)

    def buscar(self):
        dominio = self.entrada_dominio.get().strip()
        if not dominio:
            messagebox.showwarning("Aviso", "⚠️ Digite um domínio!")
            return
        resultado = requisicao_whois(dominio)
        resumo = traduzir_whois_br(resultado)
        self.caixa_texto.delete("1.0", "end")
        self.caixa_texto.insert("1.0", resumo)

    def salvar(self):
        texto = self.caixa_texto.get("1.0", "end").strip()
        if not texto:
            messagebox.showwarning("Aviso", "⚠️ Nenhum resultado para salvar!")
            return
        arquivo = filedialog.asksaveasfilename(defaultextension=".txt",
                                               filetypes=[("Arquivo de Texto", "*.txt")])
        if arquivo:
            try:
                with open(arquivo, "w", encoding="utf-8") as f:
                    f.write(texto)
                messagebox.showinfo("Sucesso", "✅ Resultado salvo!")
            except Exception as e:
                messagebox.showerror("Erro", f"❌ Não foi possível salvar:\n{e}")

    def limpar(self):
        self.entrada_dominio.delete(0, "end")
        self.caixa_texto.delete("1.0", "end")

if __name__ == "__main__":
    app = App()
    app.mainloop()
