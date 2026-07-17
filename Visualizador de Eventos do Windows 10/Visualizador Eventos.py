import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import subprocess
import threading
import pythoncom
import time
import winreg
import re
import os
from datetime import datetime

# =============================================================================
# Tenta importar parsers XML (usa lxml se disponível, fallback para ET)
# =============================================================================
HAS_LXML = False
try:
    from lxml import etree as LXML_ETREE
    HAS_LXML = True
except ImportError:
    import xml.etree.ElementTree as ET

# =============================================================================
# CONSTANTES
# =============================================================================
NIVEIS_CORES = {
    "Crítico": "#FF0000",
    "Erro": "#FF0000",
    "Aviso": "#FF8C00",
    "Informações": "#000000",
    "Êxito de Auditoria": "#008000",
    "Falha de Auditoria": "#FF0000",
    "Detalhes": "#808080"
}

LEVEL_MAP = {
    "1": "Crítico",
    "2": "Erro",
    "3": "Aviso",
    "4": "Informações",
    "5": "Detalhes",
    "0": "Informações"
}

KEYWORDS_MAP = {
    "0x80000000000000": "Clássico",
    "0x8010000000000000": "Resposta de Auditoria",
    "0x8020000000000000": "Falha de Auditoria",
    "0x4000000000000000": "Evento Correlacionado",
    "0x8000000000000000": "Nenhum(a)",
    "0x8080000000000000": "Auditoria de Êxito"
}

# Namespace do Windows Event Log
NS = "http://schemas.microsoft.com/win/2004/08/events/event"


# =============================================================================
# PARSER DE XML ROBUSTO
# =============================================================================
def parse_event_xml(xml_string):
    if not xml_string or not xml_string.strip():
        return None
    
    if HAS_LXML:
        try:
            parser = LXML_ETREE.XMLParser(recover=True, huge_tree=True)
            return LXML_ETREE.fromstring(xml_string.encode('utf-8', errors='replace'), parser)
        except:
            pass
    
    try:
        return ET.fromstring(xml_string)
    except ET.ParseError:
        pass
    
    try:
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', xml_string)
        cleaned = re.sub(r'<(\w+)([^>]*)(?<!/)>', r'<\1\2/>', cleaned)
        return ET.fromstring(cleaned)
    except:
        return None


def safe_find(root, xpath, ns_map=None):
    try:
        if ns_map:
            return root.find(xpath, ns_map)
        return root.find(xpath)
    except:
        return None


def safe_findall(root, xpath, ns_map=None):
    try:
        if ns_map:
            return root.findall(xpath, ns_map)
        return root.findall(xpath)
    except:
        return []


def safe_get_text(element):
    try:
        return element.text if element is not None and element.text else ''
    except:
        return ''


def safe_get_attr(element, attr):
    try:
        return element.get(attr, '') if element is not None else ''
    except:
        return ''


# =============================================================================
# CLASSE EventoCompleto
# =============================================================================
class EventoCompleto:
    def __init__(self, xml_string, log_name):
        self.xml_string = xml_string
        self.log_name = log_name
        self.raw_xml = xml_string
        
        self.fonte = 'Desconhecido'
        self.id_evento = '0'
        self.version = ''
        self.nivel = 'Informações'
        self.task = '0'
        self.opcode = ''
        self.keywords = '0x0000000000000000'
        self.keywords_nome = 'Nenhum(a)'
        self.data_hora = ''
        self.event_record_id = ''
        self.computador = ''
        self.channel = log_name
        self.user_id = ''
        self.event_data_list = []
        self.event_data_dict = {}
        self.message = ''
        self.level_display = ''
        self.task_display = ''
        self.opcode_display = ''
        self.keywords_display = []
        self.provider_display = ''
        
        self._parse_xml()
    
    def _extrair_campo_system(self, root, nome_tag, ns_map):
        try:
            xpath = f'.//ns:System/ns:{nome_tag}'
            el = root.find(xpath, ns_map)
            return safe_get_text(el)
        except:
            return ''
    
    def _extrair_atributo_system(self, root, nome_tag, attr, ns_map):
        try:
            xpath = f'.//ns:System/ns:{nome_tag}'
            el = root.find(xpath, ns_map)
            return safe_get_attr(el, attr)
        except:
            return ''
    
    def _parse_xml(self):
        root = parse_event_xml(self.xml_string)
        if root is None:
            self._parse_with_regex()
            return
        
        ns_map = {'ns': NS}
        
        try:
            system = root.find('.//ns:System', ns_map)
            if system is None:
                system = root.find('.//System')
                if system is None:
                    self._parse_with_regex()
                    return
                ns_map = {}
            
            provider_el = system.find('ns:Provider', ns_map) if ns_map else system.find('Provider')
            if provider_el is None and not ns_map:
                provider_el = system.find('Provider')
            self.fonte = safe_get_attr(provider_el, 'Name')
            if not self.fonte:
                self.fonte = safe_get_text(provider_el) or 'Desconhecido'
            
            eventid_el = system.find('ns:EventID', ns_map) if ns_map else system.find('EventID')
            raw_id = safe_get_text(eventid_el)
            if raw_id:
                raw_id = raw_id.split()[0] if ' ' in raw_id else raw_id
                try:
                    self.id_evento = str(int(float(raw_id)))
                except ValueError:
                    self.id_evento = raw_id
            
            self.version = self._extrair_campo_system(root, 'Version', ns_map)
            level_val = self._extrair_campo_system(root, 'Level', ns_map)
            self.nivel = LEVEL_MAP.get(level_val, 'Informações')
            self.task = self._extrair_campo_system(root, 'Task', ns_map) or '0'
            self.opcode = self._extrair_campo_system(root, 'Opcode', ns_map)
            
            kw_text = self._extrair_campo_system(root, 'Keywords', ns_map)
            if kw_text:
                kw_text = kw_text.strip()
                try:
                    kw_int = int(kw_text, 16) if kw_text.startswith('0x') else int(kw_text)
                    self.keywords = f"0x{kw_int:016X}"
                except:
                    self.keywords = kw_text
            self.keywords_nome = KEYWORDS_MAP.get(self.keywords, self.keywords)
            
            time_el = system.find('ns:TimeCreated', ns_map) if ns_map else system.find('TimeCreated')
            sys_time = safe_get_attr(time_el, 'SystemTime')
            if sys_time:
                try:
                    sys_time_clean = sys_time.replace('Z', '+00:00')
                    dt = datetime.fromisoformat(sys_time_clean)
                    self.data_hora = dt.strftime("%d/%m/%Y %H:%M:%S")
                except:
                    try:
                        dt = datetime.strptime(sys_time[:19], "%Y-%m-%dT%H:%M:%S")
                        self.data_hora = dt.strftime("%d/%m/%Y %H:%M:%S")
                    except:
                        self.data_hora = sys_time[:19]
            
            self.event_record_id = self._extrair_campo_system(root, 'EventRecordID', ns_map)
            self.computador = self._extrair_campo_system(root, 'Computer', ns_map)
            
            channel = self._extrair_campo_system(root, 'Channel', ns_map)
            if channel:
                self.channel = channel
            
            security_el = system.find('ns:Security', ns_map) if ns_map else system.find('Security')
            self.user_id = safe_get_attr(security_el, 'UserID')
            
            eventdata = root.find('.//ns:EventData', ns_map) if ns_map else root.find('.//EventData')
            if eventdata is None and not ns_map:
                for elem in root.iter():
                    if elem.tag.endswith('EventData'):
                        eventdata = elem
                        break
            
            if eventdata is not None:
                data_elements = eventdata.findall('ns:Data', ns_map) if ns_map else eventdata.findall('Data')
                if not data_elements and not ns_map:
                    data_elements = [elem for elem in eventdata if elem.tag.endswith('Data')]
                
                for data in data_elements:
                    name = safe_get_attr(data, 'Name') or ''
                    text = safe_get_text(data) or ''
                    self.event_data_list.append((name, text))
                    if name:
                        self.event_data_dict[name] = text
            
            renderinfo = root.find('.//ns:RenderingInfo', ns_map) if ns_map else root.find('.//RenderingInfo')
            if renderinfo is None and not ns_map:
                for elem in root.iter():
                    if elem.tag.endswith('RenderingInfo'):
                        renderinfo = elem
                        break
            
            if renderinfo is not None:
                msg_el = renderinfo.find('ns:Message', ns_map) if ns_map else renderinfo.find('Message')
                if msg_el is None and not ns_map:
                    for elem in renderinfo:
                        if elem.tag.endswith('Message'):
                            msg_el = elem
                            break
                self.message = safe_get_text(msg_el)
                
                lvl_el = renderinfo.find('ns:Level', ns_map) if ns_map else renderinfo.find('Level')
                if lvl_el is None and not ns_map:
                    for elem in renderinfo:
                        if elem.tag.endswith('Level'):
                            lvl_el = elem
                            break
                self.level_display = safe_get_text(lvl_el)
                
                tsk_el = renderinfo.find('ns:Task', ns_map) if ns_map else renderinfo.find('Task')
                if tsk_el is None and not ns_map:
                    for elem in renderinfo:
                        if elem.tag.endswith('Task'):
                            tsk_el = elem
                            break
                self.task_display = safe_get_text(tsk_el)
                
                opc_el = renderinfo.find('ns:Opcode', ns_map) if ns_map else renderinfo.find('Opcode')
                if opc_el is None and not ns_map:
                    for elem in renderinfo:
                        if elem.tag.endswith('Opcode'):
                            opc_el = elem
                            break
                self.opcode_display = safe_get_text(opc_el)
                
                kw_elements = renderinfo.findall('ns:Keywords', ns_map) if ns_map else renderinfo.findall('Keywords')
                if not kw_elements and not ns_map:
                    kw_elements = [elem for elem in renderinfo if elem.tag.endswith('Keywords')]
                for kw_el in kw_elements:
                    kw_text = safe_get_text(kw_el)
                    if kw_text:
                        self.keywords_display.append(kw_text)
                
                prov_el = renderinfo.find('ns:Provider', ns_map) if ns_map else renderinfo.find('Provider')
                if prov_el is None and not ns_map:
                    for elem in renderinfo:
                        if elem.tag.endswith('Provider'):
                            prov_el = elem
                            break
                self.provider_display = safe_get_text(prov_el)
        
        except Exception as e:
            if not self.fonte or self.fonte == 'Desconhecido':
                self._parse_with_regex()
    
    def _parse_with_regex(self):
        xml = self.xml_string
        
        m = re.search(r'Provider\s+Name="([^"]+)"', xml)
        if m: self.fonte = m.group(1)
        
        m = re.search(r'<EventID[^>]*>(\d+)', xml)
        if m: self.id_evento = m.group(1)
        
        m = re.search(r'<Level[^>]*>(\d+)', xml)
        if m: self.nivel = LEVEL_MAP.get(m.group(1), 'Informações')
        
        m = re.search(r'TimeCreated\s+SystemTime="([^"]+)"', xml)
        if m:
            sys_time = m.group(1)
            try:
                dt = datetime.fromisoformat(sys_time.replace('Z', '+00:00'))
                self.data_hora = dt.strftime("%d/%m/%Y %H:%M:%S")
            except:
                self.data_hora = sys_time[:19]
        
        m = re.search(r'<Computer[^>]*>([^<]+)', xml)
        if m: self.computador = m.group(1)
        
        m = re.search(r'<Channel[^>]*>([^<]+)', xml)
        if m: self.channel = m.group(1)
        
        m = re.search(r'<Keywords[^>]*>([^<]+)', xml)
        if m: 
            kw = m.group(1).strip()
            self.keywords = kw
            self.keywords_nome = KEYWORDS_MAP.get(kw, kw)
        
        m = re.search(r'<EventRecordID[^>]*>(\d+)', xml)
        if m: self.event_record_id = m.group(1)
        
        m = re.search(r'<Task[^>]*>(\d+)', xml)
        if m: self.task = m.group(1)
        
        for m in re.finditer(r'<Data\s+Name="([^"]*)">(.*?)</Data>', xml, re.DOTALL):
            name = m.group(1)
            text = m.group(2).strip()
            self.event_data_list.append((name, text))
            if name:
                self.event_data_dict[name] = text
        
        if not self.event_data_list:
            for m in re.finditer(r'<Data[^>]*>(.*?)</Data>', xml, re.DOTALL):
                text = m.group(1).strip()
                if text:
                    self.event_data_list.append(('', text))
        
        m = re.search(r'<Message[^>]*>(.*?)</Message>', xml, re.DOTALL)
        if m: self.message = m.group(1).strip()
        
        m = re.search(r'<Task[^>]*>(.*?)</Task>', xml, re.DOTALL)
        if m and not self.task_display: 
            self.task_display = m.group(1).strip()
    
    def obter_descricao(self):
        if self.message:
            return self.message
        
        if self.event_data_list:
            partes = []
            for name, val in self.event_data_list:
                if val:
                    if name:
                        partes.append(f"{name}: {val}")
                    else:
                        partes.append(val)
            if partes:
                return '\n'.join(partes)
        
        return "Sem descrição disponível para este evento."
    
    def obter_categoria(self):
        if self.task_display:
            return self.task_display
        return str(self.task) if self.task != '0' else 'N/D'
    
    def to_dict(self):
        return {
            "nivel": self.nivel,
            "data": self.data_hora,
            "fonte": self.fonte,
            "id": self.id_evento,
            "categoria": self.obter_categoria(),
            "computador": self.computador,
            "descricao": self.obter_descricao(),
            "xml": self.raw_xml,
            "keywords": self.keywords_nome,
            "level_display": self.level_display,
            "opcode": self.opcode_display or self.opcode,
            "event_record_id": self.event_record_id,
            "channel": self.channel,
            "event_data": self.event_data_dict,
            "version": self.version,
            "log_name": self.log_name
        }


# =============================================================================
# CLASSE PRINCIPAL
# =============================================================================
class VisualizadorEventosFiel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Visualizador Eventos")
        self.geometry("1400x850")
        self.state("zoomed")
        
        # ===== DADOS =====
        self.eventos = []
        self.eventos_dict = []
        self.log_atual = "Sistema"
        self.log_atual_real = "System"
        self.total_registros_log = 0
        self.logs_disponiveis = {}
        self.logs_disponiveis_reverso = {}
        self.filtro_ativo = False
        
        self.criar_interface()
        self.verificar_status_servicos()
        self.carregar_logs_disponiveis()
        
        self.bind("<Control-f>", lambda e: self.pesquisar())
        self.bind("<Control-F>", lambda e: self.pesquisar())
        self.bind("<F5>", lambda e: self.atualizar())

    # =========================================================================
    # INTERFACE
    # =========================================================================
    def criar_interface(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        menu_arquivo = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=menu_arquivo)
        menu_arquivo.add_command(label="Abrir Log Salvo...", command=self.abrir_log_salvo)
        menu_arquivo.add_separator()
        menu_arquivo.add_command(label="Exportar Eventos...", command=self.exportar_logs)
        menu_arquivo.add_separator()
        menu_arquivo.add_command(label="Sair", command=self.quit)
        
        menu_acao = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ação", menu=menu_acao)
        menu_acao.add_command(label="Criar Exibição Personalizada...", command=self.criar_exibicao)
        menu_acao.add_separator()
        menu_acao.add_command(label="Limpar Log...", command=self.limpar_log)
        menu_acao.add_separator()
        menu_acao.add_command(label="Atualizar", command=self.atualizar, accelerator="F5")
        
        menu_exibir = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Exibir", menu=menu_exibir)
        menu_exibir.add_command(label="Adicionar/Remover Colunas...", command=self.configurar_colunas)
        menu_exibir.add_separator()
        menu_exibir.add_command(label="Localizar...", command=self.pesquisar, accelerator="Ctrl+F")
        menu_exibir.add_separator()
        menu_exibir.add_command(label="Filtrar Log Atual...", command=self.aplicar_filtro_avancado)
        
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # ===== PAINEL ESQUERDO =====
        left = ttk.Frame(paned, width=320)
        paned.add(left, weight=1)
        
        left_border = ttk.LabelFrame(left, text="", padding=0)
        left_border.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        left_frame = ttk.Frame(left_border)
        left_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        left_vsb = ttk.Scrollbar(left_frame, orient=tk.VERTICAL)
        left_hsb = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL)
        
        self.tree_logs = ttk.Treeview(
            left_frame, 
            height=25,
            yscrollcommand=left_vsb.set,
            xscrollcommand=left_hsb.set
        )
        
        left_vsb.config(command=self.tree_logs.yview)
        left_hsb.config(command=self.tree_logs.xview)
        
        self.tree_logs.grid(row=0, column=0, sticky="nsew")
        left_vsb.grid(row=0, column=1, sticky="ns")
        left_hsb.grid(row=1, column=0, sticky="ew")
        
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Estrutura de pastas
        self.tree_logs.insert("", "end", 
            text="📁 Visualizador de Eventos (Local)", 
            open=True, iid="_raiz_")
        self.tree_logs.insert("_raiz_", "end", 
            text="📁 Logs do Windows", 
            open=True, iid="_windows_logs_")
        self.tree_logs.insert("_raiz_", "end", 
            text="📁 Logs de Aplicativos e Serviços", 
            open=False, iid="_apps_logs_")
        self.tree_logs.insert("_apps_logs_", "end", 
            text="📁 Microsoft", 
            open=False, iid="_microsoft_logs_")
        self.tree_logs.insert("_apps_logs_", "end", 
            text="📁 Outros Logs", 
            open=False, iid="_outros_logs_")
        
        self.tree_logs.bind("<<TreeviewSelect>>", self.selecionar_log)
        self.tree_logs.bind("<Double-1>", self.selecionar_log)

        # ===== PAINEL DIREITO =====
        right = ttk.Frame(paned)
        paned.add(right, weight=4)

        top = ttk.Frame(right)
        top.pack(fill=tk.X, pady=2)
        
        self.caminho_label = ttk.Label(
            top, 
            text="Visualizador de Eventos (Local) > Logs do Windows > Sistema", 
            font=("Segoe UI", 9)
        )
        self.caminho_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(top, text="Qtd:").pack(side=tk.RIGHT, padx=2)
        self.qtd_eventos = ttk.Combobox(
            top, 
            values=["50", "100", "200", "500", "1000", "2000", "5000", "10000", "Todos"], 
            width=8
        )
        self.qtd_eventos.set("1000")
        self.qtd_eventos.pack(side=tk.RIGHT, padx=2)
        
        self.label_total_eventos = ttk.Label(
            top, text="de 0 eventos",
            font=("Segoe UI", 9, "italic"), foreground="#555555"
        )
        self.label_total_eventos.pack(side=tk.RIGHT, padx=(0, 4))
        
        info_frame = ttk.LabelFrame(right, text="", padding=5)
        info_frame.pack(fill=tk.X, pady=2, padx=2)
        
        self.info_log_label = ttk.Label(info_frame, text="", font=("Segoe UI", 9, "bold"))
        self.info_log_label.pack(side=tk.LEFT, padx=5)
        
        self.eventlog_status_label = ttk.Label(info_frame, text="", font=("Segoe UI", 9))
        self.eventlog_status_label.pack(side=tk.RIGHT, padx=5)
        
        toolbar = ttk.Frame(right)
        toolbar.pack(fill=tk.X, pady=2)
        
        ttk.Button(toolbar, text="🔍 Filtrar Log Atual", command=self.aplicar_filtro_avancado).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="🔄 Atualizar", command=self.atualizar).pack(side=tk.LEFT, padx=1)
        
        ttk.Label(toolbar, text="    Ações:").pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="📋 Salvar Eventos...", command=self.exportar_logs).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="🔎 Localizar...", command=self.pesquisar).pack(side=tk.LEFT, padx=1)
        
        ttk.Label(toolbar, text="    Nível:").pack(side=tk.LEFT, padx=2)
        self.filtro_nivel = ttk.Combobox(
            toolbar, 
            values=["Todos", "Crítico", "Erro", "Aviso", "Informações", "Detalhes", 
                    "Êxito de Auditoria", "Falha de Auditoria"], 
            width=14
        )
        self.filtro_nivel.set("Todos")
        self.filtro_nivel.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(toolbar, text="IDs:").pack(side=tk.LEFT, padx=2)
        self.filtro_id = ttk.Entry(toolbar, width=10)
        self.filtro_id.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(toolbar, text="Fonte:").pack(side=tk.LEFT, padx=2)
        self.filtro_texto = ttk.Entry(toolbar, width=12)
        self.filtro_texto.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(toolbar, text="Ir", command=self.aplicar_filtro_rapido, width=3).pack(side=tk.LEFT, padx=1)
        
        self.filtro_nivel.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtro_rapido())
        self.filtro_id.bind("<Return>", lambda e: self.aplicar_filtro_rapido())
        self.filtro_texto.bind("<Return>", lambda e: self.aplicar_filtro_rapido())
        
        table_frame = ttk.Frame(right)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        cols = ("nivel", "data", "fonte", "id", "categoria", "computador")
        self.tree = ttk.Treeview(
            table_frame, 
            columns=cols, 
            show="headings", 
            height=16, 
            selectmode="extended"
        )
        
        headers = ["Nível", "Data e Hora", "Fonte", "ID do Evento", "Categoria da Tarefa", "Computador"]
        widths = [80, 150, 280, 90, 200, 140]
        for col, header, w in zip(cols, headers, widths):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=w)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.bind("<Double-1>", self.mostrar_detalhes_janela)
        self.tree.bind("<Return>", self.mostrar_detalhes_janela)
        
        self.barra_status = ttk.Label(right, text="Pronto", relief=tk.SUNKEN, anchor=tk.W)
        self.barra_status.pack(fill=tk.X, side=tk.BOTTOM)

    def _formatar_numero(self, numero):
        if numero == 0:
            return "0"
        return f"{numero:,}".replace(",", ".")

    def _obter_nome_amigavel(self, nome_real):
        mapeamento = {
            "Application": "Aplicação",
            "Security": "Segurança",
            "Setup": "Instalação",
            "System": "Sistema",
            "ForwardedEvents": "Eventos Encaminhados"
        }
        return mapeamento.get(nome_real, nome_real)

    # =========================================================================
    # LOGS DISPONÍVEIS
    # =========================================================================
    def _listar_logs_wevtutil(self):
        try:
            result = subprocess.run(
                ["wevtutil", "el"], 
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                logs = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
                return logs
            return []
        except:
            return []

    def carregar_logs_disponiveis(self):
        threading.Thread(target=self._listar_logs, daemon=True).start()

    def _listar_logs(self):
        pythoncom.CoInitialize()
        try:
            self.barra_status.config(text="Carregando logs disponíveis...")
            
            logs_completos = self._listar_logs_wevtutil()
            self.logs_disponiveis = {}
            self.logs_disponiveis_reverso = {}
            
            logs_principais_ordem = ["Application", "Security", "Setup", "System", "ForwardedEvents"]
            
            principais = []
            microsoft = []
            outros = []
            
            for log_real in logs_completos:
                nome_amigavel = self._obter_nome_amigavel(log_real)
                
                if log_real in logs_principais_ordem:
                    principais.append((nome_amigavel, log_real))
                elif log_real.startswith("Microsoft-Windows-") or log_real.startswith("Microsoft-"):
                    microsoft.append((nome_amigavel, log_real))
                else:
                    outros.append((nome_amigavel, log_real))
            
            principais_ordenados = []
            for lp in logs_principais_ordem:
                for p in principais:
                    if p[1] == lp:
                        principais_ordenados.append(p)
                        break
            for p in principais:
                if p[1] not in logs_principais_ordem:
                    principais_ordenados.append(p)
            
            for item in self.tree_logs.get_children():
                try:
                    self.tree_logs.delete(item)
                except:
                    pass
            
            self.tree_logs.insert("", "end", 
                text="📁 Visualizador de Eventos (Local)", 
                open=True, iid="_raiz_")
            self.tree_logs.insert("_raiz_", "end", 
                text="📁 Logs do Windows", 
                open=True, iid="_windows_logs_")
            self.tree_logs.insert("_raiz_", "end", 
                text="📁 Logs de Aplicativos e Serviços", 
                open=False, iid="_apps_logs_")
            self.tree_logs.insert("_apps_logs_", "end", 
                text="📁 Microsoft", 
                open=False, iid="_microsoft_logs_")
            self.tree_logs.insert("_apps_logs_", "end", 
                text="📁 Outros Logs", 
                open=False, iid="_outros_logs_")
            
            for nome_amigavel, log_real in principais_ordenados:
                iid = f"_log_{log_real}_"
                try:
                    self.tree_logs.insert("_windows_logs_", "end", 
                        text=f"📄 {nome_amigavel}", iid=iid)
                except:
                    iid = f"_log_{log_real}_{time.time()}" 
                    self.tree_logs.insert("_windows_logs_", "end", 
                        text=f"📄 {nome_amigavel}", iid=iid)
                
                self.logs_disponiveis[nome_amigavel] = log_real
                self.logs_disponiveis[log_real] = log_real
                self.logs_disponiveis_reverso[log_real] = nome_amigavel
            
            for nome_amigavel, log_real in sorted(microsoft, key=lambda x: x[0]):
                iid = f"_log_ms_{log_real}_"
                try:
                    if iid not in self.tree_logs.get_children("_microsoft_logs_"):
                        self.tree_logs.insert("_microsoft_logs_", "end", 
                            text=f"📄 {nome_amigavel}", iid=iid)
                except:
                    iid = f"_log_ms_{log_real}_{time.time()}"
                    self.tree_logs.insert("_microsoft_logs_", "end", 
                        text=f"📄 {nome_amigavel}", iid=iid)
                
                self.logs_disponiveis[nome_amigavel] = log_real
                self.logs_disponiveis[log_real] = log_real
                self.logs_disponiveis_reverso[log_real] = nome_amigavel
            
            for nome_amigavel, log_real in sorted(outros, key=lambda x: x[0]):
                iid = f"_log_out_{log_real}_"
                try:
                    if iid not in self.tree_logs.get_children("_outros_logs_"):
                        self.tree_logs.insert("_outros_logs_", "end", 
                            text=f"📄 {nome_amigavel}", iid=iid)
                except:
                    iid = f"_log_out_{log_real}_{time.time()}"
                    self.tree_logs.insert("_outros_logs_", "end", 
                        text=f"📄 {nome_amigavel}", iid=iid)
                
                self.logs_disponiveis[nome_amigavel] = log_real
                self.logs_disponiveis[log_real] = log_real
                self.logs_disponiveis_reverso[log_real] = nome_amigavel
            
            total_logs = len(principais) + len(microsoft) + len(outros)
            self.barra_status.config(text=f"Logs carregados: {total_logs}")
            
            self.after(100, lambda: self._selecionar_log_inicial())
            
        except Exception as e:
            self.after(0, lambda: messagebox.showwarning(
                "Aviso", f"Erro ao carregar logs: {str(e)[:150]}"))
            
            self._criar_fallback_logs()
        finally:
            pythoncom.CoUninitialize()

    def _criar_fallback_logs(self):
        self.logs_disponiveis = {
            "Aplicação": "Application",
            "Segurança": "Security",
            "Instalação": "Setup",
            "Sistema": "System",
            "Application": "Application",
            "Security": "Security",
            "Setup": "Setup",
            "System": "System"
        }
        
        for item in self.tree_logs.get_children():
            try:
                self.tree_logs.delete(item)
            except:
                pass
        
        self.tree_logs.insert("", "end", 
            text="📁 Visualizador de Eventos (Local)", open=True, iid="_raiz_")
        self.tree_logs.insert("_raiz_", "end", 
            text="📁 Logs do Windows", open=True, iid="_windows_logs_")
        self.tree_logs.insert("_raiz_", "end", 
            text="📁 Logs de Aplicativos e Serviços", open=False, iid="_apps_logs_")
        self.tree_logs.insert("_apps_logs_", "end", 
            text="📁 Microsoft", open=False, iid="_microsoft_logs_")
        self.tree_logs.insert("_apps_logs_", "end", 
            text="📁 Outros Logs", open=False, iid="_outros_logs_")
        
        self.tree_logs.insert("_windows_logs_", "end", 
            text="📄 Aplicação", iid="_log_Application_")
        self.tree_logs.insert("_windows_logs_", "end", 
            text="📄 Segurança", iid="_log_Security_")
        self.tree_logs.insert("_windows_logs_", "end", 
            text="📄 Instalação", iid="_log_Setup_")
        self.tree_logs.insert("_windows_logs_", "end", 
            text="📄 Sistema", iid="_log_System_")
        
        self.after(100, lambda: self._selecionar_log_inicial())

    def _selecionar_log_inicial(self):
        try:
            children = self.tree_logs.get_children("_windows_logs_")
            for child in children:
                texto = self.tree_logs.item(child, "text")
                nome = texto.replace("📄 ", "").replace("📁 ", "")
                if nome == "Sistema":
                    self.tree_logs.selection_set(child)
                    self.tree_logs.focus(child)
                    self.after(100, lambda: self.carregar_eventos_log("Sistema", "System"))
                    return
            
            if children:
                primeiro = children[0]
                texto = self.tree_logs.item(primeiro, "text")
                nome = texto.replace("📄 ", "").replace("📁 ", "")
                nome_real = self.logs_disponiveis.get(nome, nome)
                self.tree_logs.selection_set(primeiro)
                self.tree_logs.focus(primeiro)
                self.after(100, lambda t=nome, r=nome_real: self.carregar_eventos_log(t, r))
        except Exception as e:
            pass

    def _extrair_nome_log(self, texto_item):
        nome = texto_item.replace("📄 ", "").replace("📁 ", "").strip()
        return nome

    def selecionar_log(self, e=None):
        sel = self.tree_logs.selection()
        if not sel: return
        
        item = sel[0]
        texto_item = self.tree_logs.item(item, "text")
        nome_amigavel = self._extrair_nome_log(texto_item)
        
        pasta_icons = ["📁 Visualizador de Eventos (Local)", "📁 Logs do Windows", 
                       "📁 Logs de Aplicativos e Serviços", "📁 Microsoft", "📁 Outros Logs"]
        if texto_item in pasta_icons or nome_amigavel in ["Visualizador de Eventos (Local)", 
            "Logs do Windows", "Logs de Aplicativos e Serviços", "Microsoft", "Outros Logs"]:
            return
        
        nome_real = self.logs_disponiveis.get(nome_amigavel, nome_amigavel)
        
        try:
            parent = self.tree_logs.parent(item)
        except:
            parent = ""
        
        if parent == "_windows_logs_":
            caminho = f"Visualizador de Eventos (Local) > Logs do Windows > {nome_amigavel}"
        elif parent == "_microsoft_logs_":
            caminho = f"Visualizador de Eventos (Local) > Logs de Aplicativos e Serviços > Microsoft > {nome_amigavel}"
        elif parent == "_outros_logs_":
            caminho = f"Visualizador de Eventos (Local) > Logs de Aplicativos e Serviços > Outros Logs > {nome_amigavel}"
        elif parent == "_apps_logs_":
            caminho = f"Visualizador de Eventos (Local) > Logs de Aplicativos e Serviços > {nome_amigavel}"
        else:
            caminho = f"Visualizador de Eventos (Local) > {nome_amigavel}"
        
        self.caminho_label.config(text=caminho)
        self.log_atual = nome_amigavel
        self.log_atual_real = nome_real
        self.barra_status.config(text=f"Carregando {nome_amigavel}...")
        
        threading.Thread(target=self._carregar_eventos_thread, 
            args=(nome_amigavel, nome_real), daemon=True).start()

    def carregar_eventos_log(self, nome_amigavel, nome_real=None):
        self.log_atual = nome_amigavel
        
        if nome_real is None:
            nome_real = self.logs_disponiveis.get(nome_amigavel, nome_amigavel)
        
        self.log_atual_real = nome_real
        
        caminho = f"Visualizador de Eventos (Local) > Logs do Windows > {nome_amigavel}"
        self.caminho_label.config(text=caminho)
        self.barra_status.config(text=f"Carregando {nome_amigavel}...")
        threading.Thread(target=self._carregar_eventos_thread, 
            args=(nome_amigavel, nome_real), daemon=True).start()

    # =========================================================================
    # CARREGAMENTO DE EVENTOS - CORRIGIDO PARA EVITAR ERROS
    # =========================================================================
    def _carregar_eventos_thread(self, nome_amigavel, nome_real):
        pythoncom.CoInitialize()
        start_time = time.time()
        
        try:
            valor_qtd = self.qtd_eventos.get().strip()
            if valor_qtd == "Todos":
                max_events = 99999
            else:
                try:
                    max_events = int(valor_qtd)
                except:
                    max_events = 1000
            
            # ===== TENTATIVA 1: wevtutil com /e:Events =====
            cmd = [
                "wevtutil", "qe", nome_real,
                "/f:XML",
                "/e:Events",
                "/rd:true",
                "/c:" + str(max_events)
            ]
            
            self.after(0, lambda n=nome_amigavel: self.barra_status.config(
                text=f"Lendo {n}..."))
            
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120
                )
                sucesso = result.returncode == 0
            except:
                sucesso = False
                result = None
            
            # ===== TENTATIVA 2: Fallback sem /e:Events =====
            if not sucesso:
                cmd2 = [
                    "wevtutil", "qe", nome_real,
                    "/f:XML",
                    "/rd:true",
                    "/c:" + str(max_events)
                ]
                try:
                    result = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
                    sucesso = result.returncode == 0
                except:
                    sucesso = False
            
            # ===== SE TODAS AS TENTATIVAS FALHARAM =====
            if not sucesso:
                # Verifica se o log existe
                try:
                    gli_check = subprocess.run(
                        ["wevtutil", "gli", nome_real],
                        capture_output=True, text=True, timeout=10
                    )
                    if gli_check.returncode == 0:
                        # Log existe mas pode estar vazio ou inacessível
                        # Tenta ler com menos eventos
                        cmd3 = [
                            "wevtutil", "qe", nome_real,
                            "/f:XML",
                            "/e:Events",
                            "/rd:true",
                            "/c:10"
                        ]
                        try:
                            result = subprocess.run(cmd3, capture_output=True, text=True, timeout=30)
                            if result.returncode == 0:
                                sucesso = True
                            else:
                                # Log existe mas vazio
                                self.eventos = []
                                self.eventos_dict = []
                                self.total_registros_log = 0
                                
                                # Tenta obter o total de registros
                                self._obter_total_registros(nome_real)
                                
                                elapsed = time.time() - start_time
                                self.after(0, lambda e=elapsed: self.atualizar_tabela(e))
                                self.after(0, lambda n=nome_amigavel: self.barra_status.config(
                                    text=f"{n}: 0 eventos (log vazio ou sem permissão)"))
                                pythoncom.CoUninitialize()
                                return
                        except:
                            pass
                    
                    if not sucesso:
                        # Log existe mas com erro de permissão ou outro
                        error_msg = result.stderr.strip() if result and result.stderr else "Log inacessível ou vazio"
                        self.after(0, lambda n=nome_amigavel, e=error_msg: 
                            self.barra_status.config(text=f"⚠️ {n}: {e[:80]}"))
                        
                        # Mostra log vazio em vez de erro
                        self.eventos = []
                        self.eventos_dict = []
                        self.total_registros_log = 0
                        
                        self._obter_total_registros(nome_real)
                        
                        elapsed = time.time() - start_time
                        self.after(0, lambda e=elapsed: self.atualizar_tabela(e))
                        pythoncom.CoUninitialize()
                        return
                        
                except:
                    # Log realmente não existe ou comando falhou
                    self.after(0, lambda n=nome_amigavel: 
                        self.barra_status.config(text=f"❌ {n}: Log não encontrado"))
                    self.after(0, lambda n=nome_amigavel: 
                        messagebox.showerror("Erro", 
                            f"Não foi possível ler o log '{n}'.\n\n"
                            f"O log pode estar vazio, corrompido ou sem permissão de leitura."))
                    pythoncom.CoUninitialize()
                    return
            
            # ===== PROCESSA O XML =====
            xml_output = result.stdout if result else ""
            
            if not xml_output or not xml_output.strip():
                self.eventos = []
                self.eventos_dict = []
                self.total_registros_log = 0
                
                self._obter_total_registros(nome_real)
                
                elapsed = time.time() - start_time
                self.after(0, lambda e=elapsed: self.atualizar_tabela(e))
                pythoncom.CoUninitialize()
                return
            
            eventos = []
            
            # Tenta parsear XML completo
            root = parse_event_xml(xml_output)
            if root is not None:
                events_found = root.findall('.//ns:Event', {'ns': NS})
                if not events_found:
                    events_found = root.findall('.//Event')
                if not events_found:
                    events_found = [child for child in root.iter() 
                                    if child.tag.endswith('Event') and child.tag != root.tag]
                
                for event_elem in events_found:
                    try:
                        xml_str = ET.tostring(event_elem, encoding='unicode')
                        ev = EventoCompleto(xml_str, nome_real)
                        if ev.fonte != 'Desconhecido' or ev.id_evento != '0':
                            eventos.append(ev)
                    except:
                        continue
            
            # Se não encontrou eventos no XML, tenta regex
            if not eventos:
                padrao_evento = r'<Event\s[^>]*>.*?</Event>'
                matches = re.findall(padrao_evento, xml_output, re.DOTALL)
                
                if not matches:
                    padrao_fallback = r'<Event[^>]*>(.*?)</Event>'
                    matches = re.findall(padrao_fallback, xml_output, re.DOTALL)
                    matches = [f'<Event xmlns="{NS}">{m}</Event>' for m in matches]
                
                if not matches:
                    partes = xml_output.split('<Event')
                    for parte in partes[1:]:
                        if '</Event>' in parte:
                            evento_bruto = '<Event' + parte.split('</Event>')[0] + '</Event>'
                            matches.append(evento_bruto)
                
                for xml_event_str in matches:
                    try:
                        ev = EventoCompleto(xml_event_str, nome_real)
                        if ev.fonte != 'Desconhecido' or ev.id_evento != '0':
                            eventos.append(ev)
                    except:
                        continue
            
            eventos.reverse()
            
            self.eventos = eventos
            self.eventos_dict = [ev.to_dict() for ev in eventos]
            
            # Obtém total de registros
            self._obter_total_registros(nome_real)
            
            elapsed = time.time() - start_time
            self.after(0, lambda e=elapsed: self.atualizar_tabela(e))
            
        except Exception as erro:
            erro_msg = str(erro)
            # Em vez de mostrar erro, mostra log vazio
            self.eventos = []
            self.eventos_dict = []
            self.total_registros_log = 0
            self._obter_total_registros(nome_real)
            
            elapsed = time.time() - start_time
            self.after(0, lambda e=elapsed: self.atualizar_tabela(e))
            self.after(0, lambda n=nome_amigavel: 
                self.barra_status.config(text=f"{n}: Sem eventos disponíveis"))
        finally:
            pythoncom.CoUninitialize()

    def _obter_total_registros(self, nome_real):
        """Tenta obter o total de registros do log"""
        try:
            gli_result = subprocess.run(
                ["wevtutil", "gli", nome_real],
                capture_output=True, text=True, timeout=10
            )
            if gli_result.returncode == 0:
                total = 0
                for line in gli_result.stdout.split('\n'):
                    line_lower = line.lower()
                    if 'numberoflogrecords' in line_lower or 'numberofrecords' in line_lower:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            try:
                                total = int(parts[1].strip())
                            except:
                                total = len(self.eventos) if self.eventos else 0
                            break
                self.total_registros_log = total or len(self.eventos) if self.eventos else 0
            else:
                self.total_registros_log = len(self.eventos) if self.eventos else 0
        except:
            self.total_registros_log = len(self.eventos) if self.eventos else 0

    def verificar_status_servicos(self):
        try:
            import win32serviceutil
            import win32service
            
            status_eventlog = win32serviceutil.QueryServiceStatus("EventLog")
            estado_eventlog = status_eventlog[1]
            
            estados = {
                win32service.SERVICE_STOPPED: "🛑 PARADO",
                win32service.SERVICE_RUNNING: "✅ ATIVO",
                win32service.SERVICE_START_PENDING: "⏳ INICIANDO",
                win32service.SERVICE_STOP_PENDING: "⏳ PARANDO",
                win32service.SERVICE_PAUSED: "⏸️ PAUSADO"
            }
            
            texto = estados.get(estado_eventlog, f"❓ ({estado_eventlog})")
            self.after(0, lambda: self.eventlog_status_label.config(
                text=f"Serviço EventLog: {texto}"))
            
            return estado_eventlog == win32service.SERVICE_RUNNING
        except Exception as e:
            self.after(0, lambda: self.eventlog_status_label.config(
                text=f"❌ Erro: {str(e)[:40]}"))
            return False

    # =========================================================================
    # ATUALIZAÇÃO DA TABELA
    # =========================================================================
    def atualizar_tabela(self, elapsed=0):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        limite_exibicao = 5000
        if len(self.eventos) > limite_exibicao:
            eventos_mostrar = self.eventos[-limite_exibicao:]
        else:
            eventos_mostrar = self.eventos
        
        for ev in eventos_mostrar:
            self.tree.insert("", "end", values=(
                ev.nivel, ev.data_hora, ev.fonte, 
                ev.id_evento, ev.obter_categoria(), ev.computador
            ))
        
        numero_formatado = self._formatar_numero(self.total_registros_log)
        
        info_text = f"Número de eventos: {numero_formatado}"
        if self.eventos:
            datas_validas = [ev.data_hora for ev in self.eventos if ev.data_hora]
            if datas_validas:
                info_text += f" | Mais recente: {datas_validas[-1]}"
        
        self.info_log_label.config(text=info_text)
        self.label_total_eventos.config(text=f"de {numero_formatado} eventos")
        
        current_vals = list(self.qtd_eventos["values"])
        str_total = str(self.total_registros_log)
        if str_total not in current_vals:
            self.qtd_eventos["values"] = current_vals + [str_total]
        
        qtd_carregada = len(self.eventos)
        qtd_exibida = len(eventos_mostrar)
        
        status = f"{self.log_atual}: {numero_formatado} eventos"
        if qtd_carregada != self.total_registros_log:
            status += f" | Carregados: {qtd_carregada}"
        status += f" | Exibindo: {qtd_exibida}"
        if elapsed:
            status += f" | ⏱ {elapsed:.1f}s"
        
        self.barra_status.config(text=status)

    # =========================================================================
    # FILTROS
    # =========================================================================
    def aplicar_filtro_rapido(self):
        nivel = self.filtro_nivel.get().strip()
        id_filtro = self.filtro_id.get().strip()
        texto = self.filtro_texto.get().strip().lower()
        
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        ids_busca = set()
        if id_filtro:
            partes = re.split(r'[,;:\-]+', id_filtro)
            for p in partes:
                p = p.strip()
                if p.isdigit():
                    ids_busca.add(int(p))
                elif '-' in p:
                    try:
                        inicio, fim = p.split('-')
                        ids_busca.update(range(int(inicio), int(fim)+1))
                    except:
                        pass
        
        count = 0
        for ev in self.eventos:
            if nivel != "Todos":
                if nivel == "Crítico" and ev.nivel != "Crítico": continue
                if nivel == "Erro" and ev.nivel != "Erro": continue
                if nivel == "Aviso" and ev.nivel != "Aviso": continue
                if nivel == "Informações" and ev.nivel not in ["Informações", "Info"]: continue
                if nivel == "Detalhes" and ev.nivel != "Detalhes": continue
                if nivel == "Êxito de Auditoria" and ev.nivel != "Êxito de Auditoria": continue
                if nivel == "Falha de Auditoria" and ev.nivel != "Falha de Auditoria": continue
            
            if ids_busca:
                try:
                    if int(ev.id_evento) not in ids_busca: continue
                except ValueError:
                    continue
            
            if texto:
                if texto not in ev.fonte.lower() and texto not in ev.obter_descricao().lower():
                    continue
            
            self.tree.insert("", "end", values=(
                ev.nivel, ev.data_hora, ev.fonte, 
                ev.id_evento, ev.obter_categoria(), ev.computador
            ))
            count += 1
        
        self.filtro_ativo = True
        self.barra_status.config(text=f"Filtro aplicado: {count} resultados de {len(self.eventos)} eventos")

    def aplicar_filtro_avancado(self):
        janela = tk.Toplevel(self)
        janela.title("Filtrar Log Atual")
        janela.geometry("600x450")
        janela.transient(self)
        janela.grab_set()
        
        frame = ttk.Frame(janela, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        aba1 = ttk.Frame(notebook, padding=10)
        notebook.add(aba1, text="Filtro")
        
        ttk.Label(aba1, text="Registrado:").grid(row=0, column=0, sticky=tk.W, pady=5)
        periodo = ttk.Combobox(aba1, values=["Qualquer período", "Última hora", "Últimas 12 horas", 
                                              "Últimas 24 horas", "Últimos 7 dias", "Últimos 30 dias"],
                                width=30)
        periodo.set("Qualquer período")
        periodo.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(aba1, text="Nível do evento:").grid(row=1, column=0, sticky=tk.W, pady=5)
        nivel_frame = ttk.Frame(aba1)
        nivel_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        niveis_vars = {}
        for i, (nivel, cor) in enumerate(NIVEIS_CORES.items()):
            var = tk.BooleanVar(value=True)
            niveis_vars[nivel] = var
            ttk.Checkbutton(nivel_frame, text=nivel, variable=var).grid(
                row=i//2, column=i%2, sticky=tk.W, padx=5)
        
        ttk.Label(aba1, text="IDs do Evento:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ids_entry = ttk.Entry(aba1, width=40)
        ids_entry.grid(row=2, column=1, pady=5, padx=5)
        ttk.Label(aba1, text="Separados por vírgula. Ex: 4624,4625,1102", 
                  font=("Segoe UI", 8)).grid(row=3, column=1, sticky=tk.W)
        
        ttk.Label(aba1, text="Fonte:").grid(row=4, column=0, sticky=tk.W, pady=5)
        fonte_entry = ttk.Entry(aba1, width=40)
        fonte_entry.grid(row=4, column=1, pady=5, padx=5)
        
        ttk.Label(aba1, text="Computador:").grid(row=5, column=0, sticky=tk.W, pady=5)
        comp_entry = ttk.Entry(aba1, width=40)
        comp_entry.grid(row=5, column=1, pady=5, padx=5)
        
        aba2 = ttk.Frame(notebook, padding=10)
        notebook.add(aba2, text="XML")
        
        ttk.Label(aba2, text="Consulta XML/XPath:").pack(anchor=tk.W)
        xml_text = tk.Text(aba2, height=12, font=("Consolas", 9))
        xml_text.pack(fill=tk.BOTH, expand=True, pady=5)
        xml_text.insert(tk.END, """<QueryList>
  <Query Id="0">
    <Select Path="Security">
      *[System[EventID=4624]]
    </Select>
  </Query>
</QueryList>""")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        def aplicar():
            periodo_sel = periodo.get()
            ids_text = ids_entry.get().strip()
            fonte_text = fonte_entry.get().strip()
            comp_text = comp_entry.get().strip()
            
            niveis_selecionados = [n for n, v in niveis_vars.items() if v.get()]
            
            for i in self.tree.get_children():
                self.tree.delete(i)
            
            count = 0
            for ev in self.eventos:
                if ev.nivel not in niveis_selecionados:
                    continue
                
                if ids_text:
                    ids_set = set()
                    for p in ids_text.split(','):
                        p = p.strip()
                        if p.isdigit():
                            ids_set.add(int(p))
                    if ids_set and int(ev.id_evento) not in ids_set:
                        continue
                
                if fonte_text and fonte_text.lower() not in ev.fonte.lower():
                    continue
                
                if comp_text and comp_text.lower() not in ev.computador.lower():
                    continue
                
                if periodo_sel != "Qualquer período" and ev.data_hora:
                    try:
                        dt_ev = datetime.strptime(ev.data_hora, "%d/%m/%Y %H:%M:%S")
                        agora = datetime.now()
                        if periodo_sel == "Última hora" and (agora - dt_ev).total_seconds() > 3600:
                            continue
                        elif periodo_sel == "Últimas 12 horas" and (agora - dt_ev).total_seconds() > 43200:
                            continue
                        elif periodo_sel == "Últimas 24 horas" and (agora - dt_ev).total_seconds() > 86400:
                            continue
                        elif periodo_sel == "Últimos 7 dias" and (agora - dt_ev).total_seconds() > 604800:
                            continue
                        elif periodo_sel == "Últimos 30 dias" and (agora - dt_ev).total_seconds() > 2592000:
                            continue
                    except:
                        pass
                
                self.tree.insert("", "end", values=(
                    ev.nivel, ev.data_hora, ev.fonte, 
                    ev.id_evento, ev.obter_categoria(), ev.computador
                ))
                count += 1
            
            self.filtro_ativo = True
            self.barra_status.config(text=f"Filtro avançado: {count} resultados")
            janela.destroy()
        
        ttk.Button(btn_frame, text="OK", command=aplicar).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="Cancelar", command=janela.destroy).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="Limpar", command=lambda: [
            self.filtro_nivel.set("Todos"),
            self.filtro_id.delete(0, tk.END),
            self.filtro_texto.delete(0, tk.END),
            self.aplicar_filtro_rapido(),
            janela.destroy()
        ]).pack(side=tk.LEFT, padx=2)

    # =========================================================================
    # DETALHES DO EVENTO
    # =========================================================================
    def mostrar_detalhes_janela(self, e=None):
        sel = self.tree.selection()
        if not sel: return
        
        idx = self.tree.index(sel[0])
        
        if idx < len(self.eventos):
            ev = self.eventos[idx]
            if isinstance(ev, EventoCompleto):
                self._mostrar_detalhes_completo(ev)
            elif idx < len(self.eventos_dict):
                self._mostrar_detalhes_dict(self.eventos_dict[idx])
        elif idx < len(self.eventos_dict):
            self._mostrar_detalhes_dict(self.eventos_dict[idx])

    def _mostrar_detalhes_completo(self, ev):
        janela = tk.Toplevel(self)
        janela.title(f"Propriedades do Evento - {ev.id_evento}")
        janela.geometry("800x600")
        janela.minsize(600, 400)
        janela.transient(self)
        
        frame = ttk.Frame(janela, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        aba_geral = ttk.Frame(notebook, padding=10)
        notebook.add(aba_geral, text="Geral")
        
        text_container = ttk.Frame(aba_geral)
        text_container.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_container, wrap=tk.WORD, font=("Segoe UI", 9))
        text_scroll_y = ttk.Scrollbar(text_container, orient="vertical", command=text_widget.yview)
        text_scroll_x = ttk.Scrollbar(text_container, orient="horizontal", command=text_widget.xview)
        text_widget.configure(yscrollcommand=text_scroll_y.set, xscrollcommand=text_scroll_x.set)
        
        text_widget.grid(row=0, column=0, sticky="nsew")
        text_scroll_y.grid(row=0, column=1, sticky="ns")
        text_scroll_x.grid(row=1, column=0, sticky="ew")
        
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)
        
        cabecalho = f"""Nome do Log: {ev.channel or ev.log_name}
Fonte: {ev.fonte}
Data: {ev.data_hora or 'N/D'}
ID do Evento: {ev.id_evento}
Nível: {ev.nivel}
Computador: {ev.computador or 'N/D'}
Categoria da Tarefa: {ev.obter_categoria()}
Palavras-chave: {ev.keywords_nome}
Usuário: {ev.user_id if ev.user_id else 'N/D'}
Código de Operação: {ev.opcode_display or ev.opcode or 'N/D'}
Registro do Evento: {ev.event_record_id}
Versão: {ev.version if ev.version else 'N/D'}
"""
        text_widget.insert(tk.END, cabecalho + "\n")
        
        text_widget.insert(tk.END, "Descrição:\n", "negrito")
        text_widget.tag_config("negrito", font=("Segoe UI", 9, "bold"))
        
        descricao = ev.obter_descricao()
        if descricao:
            text_widget.insert(tk.END, f"{descricao}\n\n")
        else:
            text_widget.insert(tk.END, "Não há descrição disponível para este evento.\n\n")
        
        if ev.event_data_list:
            text_widget.insert(tk.END, "Dados do Evento:\n", "negrito")
            for name, val in ev.event_data_list:
                if val:
                    text_widget.insert(tk.END, f"  {name}: {val}\n")
        
        text_widget.config(state=tk.DISABLED)
        
        aba_detalhes = ttk.Frame(notebook, padding=10)
        notebook.add(aba_detalhes, text="Detalhes")
        
        detalhes_paned = ttk.PanedWindow(aba_detalhes, orient=tk.VERTICAL)
        detalhes_paned.pack(fill=tk.BOTH, expand=True)
        
        tree_container = ttk.Frame(detalhes_paned)
        detalhes_paned.add(tree_container, weight=1)
        
        tree_detalhes = ttk.Treeview(tree_container, columns=("valor",), show="tree", height=10)
        tree_detalhes.heading("#0", text="Campo")
        tree_detalhes.heading("valor", text="Valor")
        tree_detalhes.column("#0", width=250)
        tree_detalhes.column("valor", width=400)
        
        tree_vsb = ttk.Scrollbar(tree_container, orient="vertical", command=tree_detalhes.yview)
        tree_hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=tree_detalhes.xview)
        tree_detalhes.configure(yscrollcommand=tree_vsb.set, xscrollcommand=tree_hsb.set)
        
        tree_detalhes.grid(row=0, column=0, sticky="nsew")
        tree_vsb.grid(row=0, column=1, sticky="ns")
        tree_hsb.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        sys_root = tree_detalhes.insert("", "end", text="📁 System", open=True)
        tree_detalhes.insert(sys_root, "end", text="📄 Provider", values=(f"Name: {ev.fonte}",))
        tree_detalhes.insert(sys_root, "end", text="📄 EventID", values=(ev.id_evento,))
        tree_detalhes.insert(sys_root, "end", text="📄 Version", values=(ev.version,))
        tree_detalhes.insert(sys_root, "end", text="📄 Level", values=(ev.nivel,))
        tree_detalhes.insert(sys_root, "end", text="📄 Task", values=(ev.task,))
        tree_detalhes.insert(sys_root, "end", text="📄 Opcode", values=(ev.opcode,))
        tree_detalhes.insert(sys_root, "end", text="📄 Keywords", values=(ev.keywords,))
        tree_detalhes.insert(sys_root, "end", text="📄 TimeCreated", values=(ev.data_hora,))
        tree_detalhes.insert(sys_root, "end", text="📄 EventRecordID", values=(ev.event_record_id,))
        tree_detalhes.insert(sys_root, "end", text="📄 Channel", values=(ev.channel,))
        tree_detalhes.insert(sys_root, "end", text="📄 Computer", values=(ev.computador,))
        tree_detalhes.insert(sys_root, "end", text="📄 Security", values=(f"UserID: {ev.user_id}" if ev.user_id else "",))
        
        if ev.event_data_list:
            ed_root = tree_detalhes.insert("", "end", text="📁 EventData", open=True)
            for name, val in ev.event_data_list:
                if val:
                    tree_detalhes.insert(ed_root, "end", text=f"📄 {name or '(sem nome)'}", values=(val,))
        
        xml_frame = ttk.Frame(detalhes_paned)
        detalhes_paned.add(xml_frame, weight=1)
        
        ttk.Label(xml_frame, text="XML do Evento:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        
        xml_container = ttk.Frame(xml_frame)
        xml_container.pack(fill=tk.BOTH, expand=True)
        
        xml_text = tk.Text(xml_container, wrap=tk.NONE, font=("Consolas", 8), height=8)
        xml_scroll_y = ttk.Scrollbar(xml_container, orient="vertical", command=xml_text.yview)
        xml_scroll_x = ttk.Scrollbar(xml_container, orient="horizontal", command=xml_text.xview)
        xml_text.configure(yscrollcommand=xml_scroll_y.set, xscrollcommand=xml_scroll_x.set)
        
        xml_text.grid(row=0, column=0, sticky="nsew")
        xml_scroll_y.grid(row=0, column=1, sticky="ns")
        xml_scroll_x.grid(row=1, column=0, sticky="ew")
        
        xml_container.grid_rowconfigure(0, weight=1)
        xml_container.grid_columnconfigure(0, weight=1)
        
        xml_formatado = ev.raw_xml
        try:
            if HAS_LXML:
                parser = LXML_ETREE.XMLParser(remove_blank_text=True)
                root = LXML_ETREE.fromstring(ev.raw_xml.encode('utf-8', errors='replace'), parser)
                xml_formatado = LXML_ETREE.tostring(root, pretty_print=True, encoding='unicode')
            else:
                root = ET.fromstring(ev.raw_xml)
                xml_formatado = ET.tostring(root, encoding='unicode')
        except:
            xml_formatado = ev.raw_xml
        
        xml_text.insert(tk.END, xml_formatado)
        xml_text.config(state=tk.DISABLED)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        def copiar_xml():
            janela.clipboard_clear()
            janela.clipboard_append(xml_formatado)
            self.barra_status.config(text="XML copiado para a área de transferência")
        
        ttk.Button(btn_frame, text="Copiar XML", command=copiar_xml).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Fechar", command=janela.destroy).pack(side=tk.RIGHT, padx=2)
        
        janela.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (janela.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (janela.winfo_height() // 2)
        janela.geometry(f"+{max(0,x)}+{max(0,y)}")

    def _mostrar_detalhes_dict(self, ev_dict):
        janela = tk.Toplevel(self)
        janela.title(f"Propriedades do Evento - {ev_dict['id']}")
        janela.geometry("750x500")
        janela.transient(self)
        
        frame = ttk.Frame(janela, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        aba_geral = ttk.Frame(notebook, padding=10)
        notebook.add(aba_geral, text="Geral")
        
        text_container = ttk.Frame(aba_geral)
        text_container.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_container, wrap=tk.WORD, font=("Segoe UI", 9))
        text_scroll_y = ttk.Scrollbar(text_container, orient="vertical", command=text_widget.yview)
        text_scroll_x = ttk.Scrollbar(text_container, orient="horizontal", command=text_widget.xview)
        text_widget.configure(yscrollcommand=text_scroll_y.set, xscrollcommand=text_scroll_x.set)
        
        text_widget.grid(row=0, column=0, sticky="nsew")
        text_scroll_y.grid(row=0, column=1, sticky="ns")
        text_scroll_x.grid(row=1, column=0, sticky="ew")
        
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)
        
        detalhes = f"""ID do Evento: {ev_dict['id']}

Nível: {ev_dict['nivel']}
Fonte: {ev_dict['fonte']}
Data/Hora: {ev_dict['data']}
Categoria da Tarefa: {ev_dict['categoria']}
Computador: {ev_dict['computador']}
Keywords: {ev_dict.get('keywords', 'N/D')}

Descrição:
{ev_dict.get('descricao', 'Sem descrição disponível.')}
"""
        text_widget.insert(tk.END, detalhes)
        text_widget.config(state=tk.DISABLED)
        
        if 'xml' in ev_dict and ev_dict['xml']:
            aba_xml = ttk.Frame(notebook, padding=10)
            notebook.add(aba_xml, text="XML")
            
            xml_container = ttk.Frame(aba_xml)
            xml_container.pack(fill=tk.BOTH, expand=True)
            
            xml_text = tk.Text(xml_container, wrap=tk.NONE, font=("Consolas", 9))
            xml_scroll_y = ttk.Scrollbar(xml_container, orient="vertical", command=xml_text.yview)
            xml_scroll_x = ttk.Scrollbar(xml_container, orient="horizontal", command=xml_text.xview)
            xml_text.configure(yscrollcommand=xml_scroll_y.set, xscrollcommand=xml_scroll_x.set)
            
            xml_text.grid(row=0, column=0, sticky="nsew")
            xml_scroll_y.grid(row=0, column=1, sticky="ns")
            xml_scroll_x.grid(row=1, column=0, sticky="ew")
            
            xml_container.grid_rowconfigure(0, weight=1)
            xml_container.grid_columnconfigure(0, weight=1)
            
            xml_text.insert(tk.END, ev_dict['xml'])
            xml_text.config(state=tk.DISABLED)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="Fechar", command=janela.destroy).pack(side=tk.RIGHT)
        
        janela.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (janela.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (janela.winfo_height() // 2)
        janela.geometry(f"+{max(0,x)}+{max(0,y)}")

    # =========================================================================
    # PESQUISA
    # =========================================================================
    def pesquisar(self):
        termo = simpledialog.askstring("Localizar", "Localizar:")
        if not termo: return
        termo = termo.lower()
        
        threading.Thread(target=self._localizar, args=(termo,), daemon=True).start()

    def _localizar(self, termo):
        pythoncom.CoInitialize()
        resultados = []
        
        self.after(0, lambda: self.barra_status.config(text=f"Localizando '{termo}' em todos os logs..."))
        
        for nome_amigavel, nome_real in list(self.logs_disponiveis.items()):
            try:
                cmd = [
                    "wevtutil", "qe", nome_real,
                    "/f:XML",
                    "/e:Events",
                    "/rd:true",
                    "/c:5000"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode != 0:
                    continue
                
                xml_output = result.stdout
                padrao = r'<Event\s[^>]*>.*?</Event>'
                matches = re.findall(padrao, xml_output, re.DOTALL)
                
                for xml_event in matches:
                    try:
                        ev = EventoCompleto(xml_event, nome_real)
                        
                        if (termo in ev.fonte.lower() or 
                            termo in ev.id_evento or
                            termo in ev.obter_descricao().lower() or
                            termo in ev.computador.lower() or
                            any(termo in val.lower() for _, val in ev.event_data_list if val)):
                            resultados.append(ev)
                    except:
                        continue
                
                self.after(0, lambda l=nome_amigavel, r=len(resultados): 
                    self.barra_status.config(text=f"Localizando '{termo}' em {l}... ({r} encontrados)"))
                
            except:
                continue
        
        if resultados:
            self.eventos = resultados
            self.eventos_dict = [ev.to_dict() for ev in resultados]
        
        self.after(0, lambda r=resultados, t=termo: self._exibir_resultados(r, t))
        pythoncom.CoUninitialize()

    def _exibir_resultados(self, resultados, termo):
        self.atualizar_tabela()
        self.caminho_label.config(text=f"Resultados da pesquisa: '{termo}'")
        self.barra_status.config(text=f"Localização concluída: {len(resultados)} resultados em todos os logs")

    # =========================================================================
    # EXPORTAÇÃO
    # =========================================================================
    def exportar_logs(self):
        if not self.eventos:
            messagebox.showinfo("Exportar", "Nenhum evento para exportar.")
            return
        
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("CSV", "*.csv"), ("XML", "*.xml"), ("Todos", "*.*")]
        )
        if not arquivo: return
        
        try:
            ext = os.path.splitext(arquivo)[1].lower()
            
            if ext == '.xml':
                with open(arquivo, "w", encoding="utf-8") as f:
                    f.write('<?xml version="1.0" encoding="utf-8"?>\n')
                    f.write('<Events>\n')
                    for ev in self.eventos[:5000]:
                        try:
                            f.write(ev.raw_xml + '\n')
                        except:
                            pass
                    f.write('</Events>\n')
            
            elif ext == '.csv':
                with open(arquivo, "w", encoding="utf-8-sig") as f:
                    f.write("Nível;Data e Hora;Fonte;ID do Evento;Categoria;Computador;Descrição\n")
                    for ev in self.eventos[:10000]:
                        if isinstance(ev, EventoCompleto):
                            desc = ev.obter_descricao().replace('\n', ' ').replace(';', ',')
                            f.write(f"{ev.nivel};{ev.data_hora};{ev.fonte};"
                                    f"{ev.id_evento};{ev.obter_categoria()};{ev.computador};{desc}\n")
                        else:
                            desc = ev.get('descricao', '').replace('\n', ' ').replace(';', ',')
                            f.write(f"{ev['nivel']};{ev['data']};{ev['fonte']};"
                                    f"{ev['id']};{ev['categoria']};{ev['computador']};{desc}\n")
            else:
                with open(arquivo, "w", encoding="utf-8") as f:
                    f.write(f"Log: {self.log_atual}\n")
                    f.write(f"Número de eventos: {self._formatar_numero(self.total_registros_log)}\n")
                    f.write(f"Exportado em: {time.strftime('%d/%m/%Y %H:%M:%S')}\n")
                    f.write("=" * 100 + "\n\n")
                    
                    for ev in self.eventos[:5000]:
                        if isinstance(ev, EventoCompleto):
                            f.write(f"[{ev.nivel}] {ev.data_hora} | {ev.fonte} | ID: {ev.id_evento}\n")
                            f.write(f"   Computador: {ev.computador} | Categoria: {ev.obter_categoria()} | Keywords: {ev.keywords_nome}\n")
                            desc = ev.obter_descricao()[:200].replace('\n', ' ')
                            f.write(f"   Descrição: {desc}\n")
                        else:
                            f.write(f"[{ev['nivel']}] {ev['data']} | {ev['fonte']} | ID: {ev['id']}\n")
                            desc = ev.get('descricao', '')[:200].replace('\n', ' ')
                            f.write(f"   Descrição: {desc}\n")
                        f.write("-" * 100 + "\n")
            
            messagebox.showinfo("Exportar", f"Eventos exportados com sucesso para:\n{arquivo}")
            self.barra_status.config(text=f"Exportado: {arquivo}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")

    # =========================================================================
    # AÇÕES
    # =========================================================================
    def abrir_log_salvo(self):
        arquivo = filedialog.askopenfilename(
            title="Abrir Log Salvo",
            filetypes=[("Arquivos de Log", "*.evtx *.evt *.txt"), 
                       ("EVTX", "*.evtx"), ("EVT", "*.evt"), 
                       ("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if not arquivo: return
        
        threading.Thread(target=self._abrir_log_arquivo, args=(arquivo,), daemon=True).start()
    
    def _abrir_log_arquivo(self, caminho):
        pythoncom.CoInitialize()
        try:
            self.after(0, lambda: self.barra_status.config(text=f"Abrindo {os.path.basename(caminho)}..."))
            
            cmd = [
                "wevtutil", "qe", caminho,
                "/lf:true",
                "/f:XML",
                "/e:Events",
                "/rd:true",
                "/c:5000"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                with open(caminho, "r", encoding="utf-8") as f:
                    conteudo = f.read()
                self.after(0, lambda: messagebox.showinfo(
                    "Log Carregado", f"Arquivo de texto carregado.\n{len(conteudo)} caracteres."))
                return
            
            xml_output = result.stdout
            padrao = r'<Event[^>]*>.*?</Event>'
            matches = re.findall(padrao, xml_output, re.DOTALL)
            
            eventos = []
            for xml_event in matches:
                try:
                    ev = EventoCompleto(xml_event, os.path.basename(caminho))
                    eventos.append(ev)
                except:
                    continue
            
            eventos.reverse()
            self.eventos = eventos
            self.eventos_dict = [ev.to_dict() for ev in eventos]
            self.total_registros_log = len(eventos)
            self.log_atual = os.path.basename(caminho)
            
            self.after(0, lambda: self.atualizar_tabela())
            self.after(0, lambda: self.caminho_label.config(
                text=f"Arquivo: {os.path.basename(caminho)}"))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Erro ao abrir arquivo: {str(e)[:200]}"))
        finally:
            pythoncom.CoUninitialize()

    def criar_exibicao(self):
        messagebox.showinfo("Criar Exibição Personalizada", 
                          "Use o filtro avançado para criar consultas personalizadas.")

    def limpar_log(self):
        resposta = messagebox.askyesno(
            "Limpar Log",
            f"Tem certeza de que deseja limpar o log '{self.log_atual}'?\n\n"
            f"Isso gerará o evento ID 1102 no Security log.",
            icon="warning"
        )
        if not resposta: return
        
        try:
            nome_real = self.log_atual_real
            subprocess.run(["wevtutil", "cl", nome_real], check=True, timeout=30)
            messagebox.showinfo("Limpar Log", 
                              f"Log '{self.log_atual}' limpo com sucesso.\n"
                              f"Verifique o evento 1102 no log de Segurança.")
            self.atualizar()
        except subprocess.TimeoutExpired:
            messagebox.showerror("Erro", "Timeout ao limpar o log.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao limpar log: {str(e)[:200]}")

    def configurar_colunas(self):
        janela = tk.Toplevel(self)
        janela.title("Adicionar/Remover Colunas")
        janela.geometry("400x350")
        
        frame = ttk.Frame(janela, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Selecione as colunas para exibir:", 
                 font=("Segoe UI", 10)).pack(anchor=tk.W, pady=(0, 10))
        
        colunas = [
            "Nível", "Data e Hora", "Fonte", "ID do Evento",
            "Categoria da Tarefa", "Computador", "Keywords",
            "Versão", "EventRecordID", "Opcode", "Usuário"
        ]
        
        for nome in colunas:
            var = tk.BooleanVar(value=nome in ["Nível", "Data e Hora", "Fonte", "ID do Evento", 
                                                 "Categoria da Tarefa", "Computador"])
            ttk.Checkbutton(frame, text=nome, variable=var).pack(anchor=tk.W, pady=2)
        
        ttk.Button(frame, text="Fechar", command=janela.destroy).pack(pady=15)

    def atualizar(self):
        self.filtro_nivel.set("Todos")
        self.filtro_id.delete(0, tk.END)
        self.filtro_texto.delete(0, tk.END)
        self.filtro_ativo = False
        self.barra_status.config(text=f"Atualizando {self.log_atual}...")
        self.carregar_eventos_log(self.log_atual, self.log_atual_real)


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    app = VisualizadorEventosFiel()
    app.mainloop()
