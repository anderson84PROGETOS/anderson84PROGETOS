import socket
import requests
import re
import threading
import sys
from tkinter import Tk, Label, Entry, Button, END
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import webbrowser

# Traduções completas para WHOIS registro.br
traducoes_completas = {
    "domain": "Domínio",
    "owner": "Titular",
    "ownerid": "Documento CNPJ",
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
    resultado = "\n".join(l for l in resultado.splitlines() if not l.strip().startswith("%"))
    return resultado

def traduzir_whois_br(texto):
    resumo = []
    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha:
            continue
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
        valor = formatar_datas_em_linha(valor)
        resumo.append(f"{chave_traduzida:<30} {valor}")
        if chave_lower == "nic-hdl-br":
            resumo.append("")
    return "\n".join(resumo)

def normalize_domain(raw: str) -> str:
    raw = raw.strip()
    if raw == "":
        return ""
    raw = re.sub(r"^https?://", "", raw, flags=re.I)
    raw = raw.split("/")[0]
    raw = raw.split(":")[0]
    return raw

def lookup_site(domain: str) -> dict:
    result = {"domain": domain}
    ip = None
    try:
        ip = socket.gethostbyname(domain)
        result["ip"] = ip
    except Exception as e:
        result["ip_error"] = str(e)

    if ip:
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}", timeout=8)
            data = r.json()
            if data.get("status") == "success":
                result["ip_api"] = data
            else:
                result["ip_api_error"] = data
        except Exception as e:
            result["ip_api_error"] = str(e)

    try:
        bruto = requisicao_whois(domain)
        result["whois"] = traduzir_whois_br(bruto)
    except Exception as e:
        result["whois_error"] = str(e)

    headers_info = {}
    page_title = None
    for scheme in ("https://", "http://"):
        try:
            url = scheme + domain
            r = requests.get(url, timeout=8, allow_redirects=True)
            headers_info[scheme[:-3]] = {
                "final_url": r.url,
                "status_code": r.status_code,
                "headers": dict(r.headers)
            }
            m = re.search(r"<title[^>]*>(.*?)</title>", r.text, flags=re.I | re.S)
            if m:
                page_title = m.group(1).strip()
            break
        except Exception as e:
            headers_info[scheme[:-3]] = {"error": str(e)}
            continue

    if headers_info:
        result["http"] = headers_info
    if page_title:
        result["title"] = page_title
    return result

class App:
    def __init__(self, root):
        self.root = root
        root.title("Site Info whois br")
        root.geometry("1280x1024")

        Label(root, text="Digite o site (ex: example.com ou https://example.com)", font=("Arial", 10)).pack(pady=6)
        self.entry = Entry(root, width=52)
        self.entry.pack(pady=4)
        self.entry.bind('<Return>', lambda e: self.on_search())

        frame = ttk.Frame(root)
        frame.pack(pady=6)

        self.search_btn = Button(frame, text="Pesquisar", bg="#03fc0b", fg="black", command=self.on_search)
        self.search_btn.grid(row=0, column=0, padx=6)

        self.clear_btn = Button(frame, text="Limpar", bg="#fc9d03", fg="black", command=self.on_clear)
        self.clear_btn.grid(row=0, column=1, padx=6)

        self.save_btn = Button(frame, text="Salvar relatório", bg="#f54242", fg="black", command=self.save_report)
        self.save_btn.grid(row=0, column=2, padx=6)

        # Novo botão para abrir no Google Maps
        self.map_btn = Button(frame, text="Abrir no Google Maps", bg="#03e8fc", fg="black", command=self.open_map)
        self.map_btn.grid(row=0, column=3, padx=6)
        self.map_btn.config(state="disabled")

        self.text_area = ScrolledText(root, width=145, height=50)
        self.text_area.pack(pady=10)

        self.last_coords = None

    def open_map(self):
        if self.last_coords:
            lat, lon = self.last_coords
            url = f"https://www.google.com/maps?q={lat},{lon}"
            webbrowser.open(url)
        else:
            messagebox.showinfo("Google Maps", "Nenhuma coordenada disponível.")

    def on_clear(self):
        self.text_area.delete(1.0, END)
        self.entry.delete(0, END)

    def save_report(self):
        content = self.text_area.get(1.0, END).strip()
        if not content:
            messagebox.showinfo("Salvar relatório", "Nenhum conteúdo para salvar.")
            return
        fname = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text files", "*.txt"), ("All files", "*")])
        if fname:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Salvar relatório", f"Relatório salvo em: {fname}")

    def on_search(self):
        raw = self.entry.get()
        domain = normalize_domain(raw)
        if not domain:
            messagebox.showwarning("Aviso", "Digite um domínio válido.")
            return
        thread = threading.Thread(target=self._run_lookup, args=(domain,))
        thread.daemon = True
        thread.start()

    def _run_lookup(self, domain: str):
        self.search_btn.config(state="disabled")
        self.map_btn.config(state="disabled")
        self.last_coords = None
        self.text_area.delete(1.0, END)
        self.text_area.insert(END, f"Consultando: {domain}\n\n")
        try:
            res = lookup_site(domain)
            self._pretty_print_result(res)
        except Exception as e:
            self.text_area.insert(END, f"Erro durante a consulta: {e}\n")
        finally:
            self.search_btn.config(state="normal")

    def _pretty_print_result(self, r: dict):
        def p(s=""):
            self.text_area.insert(END, s + "\n")

        p(f"Domínio: {r.get('domain')}")
        if 'ip' in r:
            p(f"\nIP: {r.get('ip')}")
        if 'ip_error' in r:
            p(f"\nErro DNS: {r.get('ip_error')}")

        p('\n\n-- GEO / ASN (via ip-api.com) --\n')
        ip_api = r.get('ip_api')
        if ip_api:
            p(f"País: {ip_api.get('country')}, {ip_api.get('countryCode')}")
            p(f"Região/Estado: {ip_api.get('regionName')} ({ip_api.get('region')})")
            p(f"Cidade: {ip_api.get('city')}")           
            self.last_coords = (ip_api.get('lat'), ip_api.get('lon'))
            self.map_btn.config(state="normal")  # ✅ Ativa o botão Google Maps
            p(f"ISP: {ip_api.get('isp')}")
            p(f"Org: {ip_api.get('org')}")
            p(f"AS: {ip_api.get('as')}")
            p(f"Timezone: {ip_api.get('timezone')}")
            p(f"\nLat/Lon: {ip_api.get('lat')}, {ip_api.get('lon')}")
            if ip_api.get('as'):
                asn = ip_api.get('as').split()[0].replace("AS", "")
                p(f"\nDetalhes AS: https://bgp.he.net/AS{asn}")
        else:
            if 'ip_api_error' in r:
                p(f"ip-api error: {r.get('ip_api_error')}")
            else:
                p("Sem dados ip-api")

        p('\n\n-- WHOIS (registro.br) --\n')
        who = r.get('whois')
        if who:
            p(who)
        else:
            p(f"WHOIS error: {r.get('whois_error')}")

        p('\n\n-- HTTP / HEADERS --\n')
        http = r.get('http')
        if http:
            for scheme, info in http.items():
                p(f"Esquema: {scheme.upper()}\n")
                if 'error' in info:                    
                    continue

                p(f"➜ URL Final: {info.get('final_url')}\n")
                p(f"➜ Código de Status: {info.get('status_code')}\n")
                headers = info.get('headers', {})
                if headers:
                    p("➜ Cabeçalhos\n")
                    for h, v in headers.items():
                        p(f"{h}: {v}")
        else:
            p("Sem dados HTTP")

        if r.get('title'):
            p('\n\n-- TÍTULO DA PÁGINA --\n')
            p(f"{r.get('title')}")      

if __name__ == '__main__':
    try:
        import requests  # noqa
    except Exception:       
        sys.exit(1)

    root = Tk()
    app = App(root)
    root.mainloop()
