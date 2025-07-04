import tkinter as tk
from tkinter import scrolledtext
import subprocess
import re
import os
import json
import platform

class ChromeSecurityChecker:
    def __init__(self, root):
        # Inicializa a janela principal do Tkinter
        self.root = root
        self.root.title("Verificador de Segurança do Google Chrome")
        self.root.geometry("1100x940")

        # Define a versão mínima considerada segura do Chrome
        self.safe_version = "138.0.7204.96"
        # Lista de palavras-chave suspeitas para verificar em extensões
        self.suspect_keywords = [
            "adware", "hacker", "vpn", "stealer", "keylogger", "proxy", "cookie", "inject"
        ]

        # Elementos da interface gráfica
        self.label = tk.Label(root, text="Clique para verificar a segurança do Google Chrome", font=("Arial", 12))
        self.label.pack(pady=10)

        self.button = tk.Button(root, text="Verificar Agora", bg="#05fc4f", font=("Arial", 12), command=self.analyze)
        self.button.pack(pady=10)

        self.safe_label = tk.Label(root, text=f"🔒 Versão mínima segura: {self.safe_version}", font=("Arial", 10), fg="gray")
        self.safe_label.pack()

        self.output = scrolledtext.ScrolledText(self.root, width=130, height=50, font=("Consolas", 10))
        self.output.pack(padx=10, pady=10)

    def get_chrome_user_data_path(self):
        """Retorna o caminho do diretório de dados do Chrome com base no sistema operacional."""
        system = platform.system()
        if system == "Windows":
            return os.path.join(os.getenv('LOCALAPPDATA'), 'Google', 'Chrome', 'User Data')
        elif system == "Darwin":  # macOS
            return os.path.expanduser('~/Library/Application Support/Google/Chrome')
        elif system == "Linux":
            return os.path.expanduser('~/.config/google-chrome')
        return None

    def compare_versions(self, current, minimum):
        """Compara duas versões do Chrome (formato X.Y.Z.W) para verificar se a atual é segura."""
        try:
            c_parts = list(map(int, current.split(".")))
            m_parts = list(map(int, minimum.split(".")))
            return c_parts >= m_parts
        except:
            return False

    def get_chrome_version(self):
        """Obtém a versão do Chrome instalada no sistema."""
        try:
            if platform.system() == "Windows":
                output = subprocess.check_output(
                    r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
                    shell=True, text=True)
                match = re.search(r"version\s+REG_SZ\s+([0-9.]+)", output)
                return match.group(1) if match else None
            else:
                # Para outros sistemas, tenta executar o comando do Chrome
                try:
                    output = subprocess.check_output(["google-chrome", "--version"], text=True)
                    match = re.search(r"Google Chrome ([0-9.]+)", output)
                    return match.group(1) if match else None
                except:
                    return None
        except:
            return None

    def traduzir_nome(self, nome_chave, ext_path, version):
        """Traduz o nome da extensão se ele usar mensagens localizadas (__MSG_)."""
        match = re.match(r"__MSG_(.+)__", nome_chave)
        if not match:
            return nome_chave
        chave = match.group(1)

        locales_dir = os.path.join(ext_path, version, '_locales')
        if not os.path.exists(locales_dir):
            return nome_chave

        prioridade = ['pt_BR', 'pt', 'en']
        for lang in prioridade:
            path = os.path.join(locales_dir, lang, 'messages.json')
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        mensagens = json.load(f)
                        if chave in mensagens:
                            return mensagens[chave].get('message', nome_chave)
                except:
                    continue

        for idioma in os.listdir(locales_dir):
            if idioma in prioridade:
                continue
            path = os.path.join(locales_dir, idioma, 'messages.json')
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        mensagens = json.load(f)
                        if chave in mensagens:
                            return mensagens[chave].get('message', nome_chave)
                except:
                    continue

        return nome_chave

    def analyze_extension_files(self, ext_path, version):
        """Analisa os arquivos da extensão em busca de conteúdo suspeito."""
        findings = []
        manifest_path = os.path.join(ext_path, version, 'manifest.json')
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

                # Verifica scripts de conteúdo
                content_scripts = manifest.get('content_scripts', [])
                for cs in content_scripts:
                    scripts = cs.get('js', [])
                    if scripts:
                        findings.append(f"Content Scripts: {', '.join(scripts)}")

                # Verifica scripts de fundo
                background = manifest.get('background', {})
                bg_scripts = background.get('scripts', [])
                if bg_scripts:
                    findings.append(f"Background Scripts: {', '.join(bg_scripts)}")

                # Verifica permissões suspeitas
                permissions = manifest.get('permissions', [])
                suspicious_permissions = [
                    'activeTab', 'tabs', 'webRequest', 'webNavigation', 'storage', 
                    'cookies', 'management', 'proxy'
                ]
                matched_permissions = [p for p in permissions if p in suspicious_permissions]
                if matched_permissions:
                    findings.append(f"Suspicious Permissions: {', '.join(matched_permissions)}")

        except:
            findings.append("\nError reading manifest.json\n")

        # Escaneia arquivos JavaScript em busca de palavras-chave suspeitas
        js_files = []
        for root, _, files in os.walk(os.path.join(ext_path, version)):
            js_files.extend(os.path.join(root, f) for f in files if f.endswith('.js'))

        for js_file in js_files[:5]:  # Limita a 5 arquivos para evitar sobrecarga
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    matched_keywords = [kw for kw in self.suspect_keywords if kw in content]
                    if matched_keywords:
                        findings.append(f"Suspicious keywords in {os.path.basename(js_file)}: {', '.join(matched_keywords)}")
            except:
                continue

        return findings

    def check_all_extensions(self):
        """Verifica todas as extensões instaladas em todos os perfis do Chrome."""
        extensoes = []
        base_path = self.get_chrome_user_data_path()

        if not base_path or not os.path.exists(base_path):
            return extensoes

        for profile in os.listdir(base_path):
            ext_dir = os.path.join(base_path, profile, 'Extensions')
            if not os.path.exists(ext_dir):
                continue

            for ext_id in os.listdir(ext_dir):
                ext_path = os.path.join(ext_dir, ext_id)
                if not os.path.isdir(ext_path):
                    continue

                try:
                    versions = os.listdir(ext_path)
                    versions.sort(reverse=True)
                    latest_version = versions[0]
                    manifest_path = os.path.join(ext_path, latest_version, 'manifest.json')

                    if os.path.exists(manifest_path):
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                            nome_raw = manifest.get('name', 'Desconhecida')
                            descricao = manifest.get('description', '')
                            nome = self.traduzir_nome(nome_raw, ext_path, latest_version)
                            full_info = {
                                "id": ext_id,
                                "nome": nome,
                                "descricao": descricao,
                                "profile": profile,
                                "path": ext_path,  # Caminho completo da extensão
                                "version": latest_version
                            }
                            extensoes.append(full_info)
                except:
                    continue

        return extensoes

    def analyze(self):
        """Executa a análise completa do Chrome e suas extensões, mostrando o caminho base uma vez."""
        self.output.delete(1.0, tk.END)
        version = self.get_chrome_version()
        if not version:
            self.output.insert(tk.END, "\n❌ Não foi possível detectar a versão do Chrome.\n")
            return

        self.output.insert(tk.END, f"Versão do Chrome Detectada: {version}\n")
        self.output.insert(tk.END, f"\nVersão mínima segura: {self.safe_version}\n")

        if self.compare_versions(version, self.safe_version):
            self.output.insert(tk.END, "\n✅ Sua versão está atualizada e segura.\n\n")
        else:
            self.output.insert(tk.END, "\n❌ Sua versão está desatualizada. Atualize o Chrome imediatamente!\n\n")

        # Exibe o caminho base do diretório de extensões uma única vez
        base_path = os.path.join(self.get_chrome_user_data_path(), 'Default', 'Extensions')
        self.output.insert(tk.END, f"\nCaminho das Extensões: {base_path}\n")
        self.output.insert(tk.END, "\n🔍 Verificando Extensões instaladas em Todos os Perfis\n\n")

        extensoes = self.check_all_extensions()
        if not extensoes:
            self.output.insert(tk.END, "\nNenhuma extensão encontrada.\n")
            return

        suspeitas = []
        for ext in extensoes:
            nome_desc = f"{ext['nome']} {ext['descricao']}".lower()
            matched_keywords = [kw for kw in self.suspect_keywords if kw in nome_desc]
            is_suspect = bool(matched_keywords)

            # Exibe apenas informações básicas, sem o caminho completo
            self.output.insert(tk.END, f"\n[{ext['profile']}] ID: {ext['id']}  Nome: {ext['nome']}\n")
            if is_suspect:
                ext['matched_keywords'] = matched_keywords
                ext['findings'] = self.analyze_extension_files(ext['path'], ext['version'])
                suspeitas.append(ext)

        self.output.insert(tk.END, f"\n\n🔢 Total de Extensões Encontradas: {len(extensoes)}\n")
        if suspeitas:
            self.output.insert(tk.END, f"\n\n⚠️ Extensões Suspeitas Detectadas: {len(suspeitas)}\n")
            for ext in suspeitas:
                self.output.insert(tk.END, f"\n\n\n\n⚠️ [{ext['profile']}] {ext['nome']} (ID: {ext['id']})\n")
                self.output.insert(tk.END, f"\n  - Motivo: Palavras-chave Encontradas: {', '.join(ext['matched_keywords'])}\n")
                if ext['findings']:
                    self.output.insert(tk.END, "\n  - Detalhes Adicionais\n\n")
                    for finding in ext['findings']:
                        self.output.insert(tk.END, f"    * {finding}\n")
                else:
                    self.output.insert(tk.END, "\n  - Nenhum detalhe adicional encontrado.\n")
        else:
            self.output.insert(tk.END, "\n✅ Nenhuma Extensão Suspeita Detectada.\n")

# Executa a aplicação
if __name__ == "__main__":
    root = tk.Tk()
    app = ChromeSecurityChecker(root)
    root.mainloop()
