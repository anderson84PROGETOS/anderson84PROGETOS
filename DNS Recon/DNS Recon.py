import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import scrolledtext
import threading
import dns.resolver
import dns.reversename
import socket
import whois
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# --- Configurações ---
DNS_TIMEOUT = 5

# --- Funções utilitárias ---
def log_print(text_widget, text, newline=True):
    """Insere texto no ScrolledText de forma thread-safe."""
    def _insert():
        if newline:
            text_widget.insert(tk.END, text + "\n")
        else:
            text_widget.insert(tk.END, text)
        text_widget.see(tk.END)
    text_widget.after(0, _insert)

def query_records(domain, types, output_widget):
    resolver = dns.resolver.Resolver()
    resolver.timeout = DNS_TIMEOUT
    resolver.lifetime = DNS_TIMEOUT
    for rtype in types:
        try:
            answers = resolver.resolve(domain, rtype)
            log_print(output_widget, f"\n=== {rtype} records for {domain} ===\n")
            for r in answers:
                log_print(output_widget, str(r))
        except dns.resolver.NoAnswer:
            log_print(output_widget, f"[{rtype}] No answer.")
        except dns.resolver.NXDOMAIN:
            log_print(output_widget, f"[{rtype}] NXDOMAIN - domain does not exist.")
        except Exception as e:
            log_print(output_widget, f"[{rtype}] Error: {e}")

def reverse_lookup(ip, output_widget):
    try:
        rev = dns.reversename.from_address(ip)
        resolver = dns.resolver.Resolver()
        resolver.timeout = DNS_TIMEOUT
        resolver.lifetime = DNS_TIMEOUT
        answers = resolver.resolve(rev, "PTR")
        log_print(output_widget, f"Reverse lookup for {ip}:")
        for r in answers:
            log_print(output_widget, str(r))
    except Exception as e:
        log_print(output_widget, f"Reverse lookup error for {ip}: {e}")

def do_whois(domain, output_widget):
    try:
        log_print(output_widget, f"\n\n=== WHOIS for {domain} ===\n")
        w = whois.whois(domain)
        if hasattr(w, "text") and w.text:
            text = w.text
            if len(text) > 15000:
                text = text[:15000] + "\n...truncated..."
            log_print(output_widget, text)
        else:
            for k, v in w.items():
                log_print(output_widget, f"{k}: {v}")
    except Exception as e:
        log_print(output_widget, f"WHOIS error: {e}")

def resolve_host(host, output_widget):
    try:
        # Pega somente endereços IPv4
        ai = socket.getaddrinfo(host, None, family=socket.AF_INET)
        ips = sorted({item[4][0] for item in ai})
        return host, ips, None
    except Exception as e:
        return host, [], str(e)

def enumerate_subdomains(domain, wordlist, output_widget, progress_callback=None):
    found = []
    start = time.time()
    log_print(output_widget, f"\n=== Iniciando Enumeração de Subdomínios: {len(wordlist)} Nomes\n")
    with ThreadPoolExecutor() as ex:
        futures = {ex.submit(resolve_host, f"{w}.{domain}", output_widget): w for w in wordlist}
        total = len(futures)
        done = 0
        for fut in as_completed(futures):
            done += 1
            host = futures[fut]
            try:
                h, ips, err = fut.result()
                if ips:
                    found.append((h, ips))
                    log_print(output_widget, f"[ENCONTRADO] {h:<30} -> {', '.join(ips)}")
                if progress_callback:
                    progress_callback(done, total)
            except Exception:
                if progress_callback:
                    progress_callback(done, total)
    elapsed = time.time() - start
    log_print(output_widget, f"\n\n=== Enumeração finalizada em {elapsed:.1f}s. Encontrados: {len(found)} \n")
    return found

# --- GUI ---
class DNSDumpsterLikeApp:
    def __init__(self, root):
        self.root = root
        root.title("DNS Recon")
        root.geometry("1100x800")
        root.state('zoomed')  # Abre a janela maximizada

        # Top frame
        top_frame = ttk.Frame(root, padding=(6,6))
        top_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top_frame, text="Domínio:").pack(side=tk.LEFT)
        self.domain_var = tk.StringVar()
        self.domain_entry = ttk.Entry(top_frame, width=40, textvariable=self.domain_var)
        self.domain_entry.pack(side=tk.LEFT, padx=(4,10))
        self.domain_entry.bind("<Return>", lambda e: self.start_lookup())

        self.btn_lookup = tk.Button(top_frame, text="Pesquisar DNS + WHOIS", bg="#03fc24", fg="black", command=self.start_lookup)
        self.btn_lookup.pack(side=tk.LEFT, padx=(0,4))

        self.btn_enum = tk.Button(top_frame, text="Enumerar Subdomínios", bg="#03fcf0", fg="black", command=self.start_enum)
        self.btn_enum.pack(side=tk.LEFT, padx=(0,4))

        self.btn_clear = tk.Button(top_frame, text="Limpar", bg="#fc0328", fg="black", command=self.clear_output)
        self.btn_clear.pack(side=tk.LEFT, padx=(0,4))

        self.btn_save = tk.Button(top_frame, text="Salvar Resultado", bg="#f5b507", fg="black", command=self.save_output)
        self.btn_save.pack(side=tk.LEFT, padx=(0,4))

        self.progress = ttk.Progressbar(top_frame, length=200, mode="determinate")
        self.progress.pack(side=tk.RIGHT, padx=(6,0))

        # Mid frame
        mid_frame = ttk.Frame(root, padding=(6,0))
        mid_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(mid_frame, text="Wordlist (carregue .txt):").pack(side=tk.LEFT, anchor=tk.W)

        # Entry que mostrará o caminho e número de entradas
        self.wordlist_entry = ttk.Entry(mid_frame, width=80)
        self.wordlist_entry.pack(side=tk.LEFT, padx=(6,0), fill=tk.X, expand=True)

        self.btn_load_wordlist = tk.Button(mid_frame, text="Carregar .txt", bg="#b1fc03", fg="black", command=self.load_wordlist_file)
        self.btn_load_wordlist.pack(side=tk.LEFT, padx=(6,0))

        # ScrolledText
        self.output = scrolledtext.ScrolledText(root, width=130, height=40, wrap=tk.NONE)
        self.output.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # --- Funções GUI ---
    def set_status(self, text):
        self.status_var.set(text)

    def clear_output(self):
        self.output.delete("1.0", tk.END)

    def save_output(self):
        content = self.output.get("1.0", tk.END)
        if not content.strip():
            messagebox.showinfo("Salvar", "Nada para salvar.")
            return
        path = filedialog.asksaveasfilename(title="Salvar resultado", defaultextension=".txt",
                                            filetypes=[("Text files","*.txt"), ("All files","*.*")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Salvar", f"Resultado salvo em\n\n{path}")

    def load_wordlist_file(self):
        """Carrega wordlist e mostra no Entry"""
        path = filedialog.askopenfilename(title="Selecionar wordlist (.txt)",
                                        filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao abrir o arquivo:\n{e}")
            return
        if not lines:
            messagebox.showinfo("Wordlist", "Arquivo carregado, mas sem entradas válidas.")
            return

        self.wordlist = lines
        # Atualiza Entry para mostrar caminho + quantidade de entradas
        self.wordlist_entry.delete(0, tk.END)
        self.wordlist_entry.insert(0, f"Wordlist carregada: {path}   A Wordlist Contém: {len(lines)}  Linhas ")

    def start_lookup(self):
        domain = self.domain_var.get().strip()
        if not domain:
            messagebox.showwarning("Aviso", "Digite um domínio.")
            return
        self.btn_lookup.config(state=tk.DISABLED)
        self.btn_enum.config(state=tk.DISABLED)
        self.set_status(f"Iniciando pesquisas para {domain} ...")
        threading.Thread(target=self._do_lookup, args=(domain,), daemon=True).start()

    def _do_lookup(self, domain):
        try:
            log_print(self.output, f"Inicio de pesquisa para: {domain}\n")
            query_records(domain, ["A", "MX", "NS", "TXT", "SOA"], self.output)
            try:
                answers = dns.resolver.resolve(domain, "A")
                ips = [str(r) for r in answers]
            except Exception:
                ips = []
            for ip in ips:
                reverse_lookup(ip, self.output)
            do_whois(domain, self.output)
            log_print(self.output, "\n== FIM da pesquisa principal ==\n")
        finally:
            self.btn_lookup.config(state=tk.NORMAL)
            self.btn_enum.config(state=tk.NORMAL)
            self.set_status("Pronto")

    def start_enum(self):
        domain = self.domain_var.get().strip()
        if not domain:
            messagebox.showwarning("Aviso", "Digite um domínio para enumerar subdomínios.")
            return

        if not hasattr(self, 'wordlist') or not self.wordlist:
            messagebox.showwarning("Aviso", "Nenhuma wordlist carregada. Carregue um arquivo .txt.")
            return

        wordlist = self.wordlist
        self.btn_enum.config(state=tk.DISABLED)
        self.btn_lookup.config(state=tk.DISABLED)
        self.progress["maximum"] = len(wordlist)
        self.progress["value"] = 0
        self.set_status(f"Enumerando subdomínios de {domain} ...")
        threading.Thread(target=self._do_enum, args=(domain, wordlist), daemon=True).start()

    def _do_enum(self, domain, wordlist):
        def progress_cb(done, total):
            self.progress["value"] = done
            self.set_status(f"Progresso: {done}/{total}")
        try:
            found = enumerate_subdomains(domain, wordlist, self.output, progress_callback=progress_cb)
            if found:
                log_print(self.output, "\nResumo de subdomínios Encontrados\n")
                for h, ips in found:
                    log_print(self.output, f"{h:<30} -> {', '.join(ips)}")
            else:
                log_print(self.output, "\nNenhum subdomínio encontrado com a wordlist fornecida\n")
        finally:
            self.progress["value"] = 0
            self.btn_enum.config(state=tk.NORMAL)
            self.btn_lookup.config(state=tk.NORMAL)
            self.set_status("Pronto")

# --- Main ---
def main():
    root = tk.Tk()
    app = DNSDumpsterLikeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()  
