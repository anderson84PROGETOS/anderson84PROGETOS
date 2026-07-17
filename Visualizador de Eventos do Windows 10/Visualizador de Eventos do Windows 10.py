#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualizador de Eventos do Windows 10 - Réplica em Python/Tkinter
Usa wevtutil como backend (mesmo mecanismo do Visualizador de Eventos nativo)
"""

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

        except Exception:
            if not self.fonte or self.fonte == 'Desconhecido':
                self._parse_with_regex()

    def _parse_with_regex(self):
        xml = self.xml_string

        m = re.search(r'Provider\s+Name="([^"]+)"', xml)
        if m:
            self.fonte = m.group(1)

        m = re.search(r'<EventID[^>]*>(\d+)', xml)
        if m:
            self.id_evento = m.group(1)

        m = re.search(r'<Level[^>]*>(\d+)', xml)
        if m:
            self.nivel = LEVEL_MAP.get(m.group(1), 'Informações')

        m = re.search(r'<TimeCreated\s+SystemTime="([^"]+)"', xml)
        if m:
            try:
                sys_time = m.group(1)
                sys_time_clean = sys_time.replace('Z', '+00:00')
                dt = datetime.fromisoformat(sys_time_clean)
                self.data_hora = dt.strftime("%d/%m/%Y %H:%M:%S")
            except:
                self.data_hora = m.group(1)[:19]

        m = re.search(r'<Computer[^>]*>([^<]+)', xml)
        if m:
            self.computador = m.group(1).strip()

        m = re.search(r'<EventRecordID[^>]*>(\d+)', xml)
        if m:
            self.event_record_id = m.group(1)

        m = re.search(r'<Channel[^>]*>([^<]+)', xml)
        if m:
            self.channel = m.group(1).strip()

        m = re.search(r'<Keywords[^>]*>([^<]+)', xml)
        if m:
            kw = m.group(1).strip()
            self.keywords = kw
            self.keywords_nome = KEYWORDS_MAP.get(kw, kw)

        m = re.search(r'<Security[^>]*\s+UserID="([^"]+)"', xml)
        if m:
            self.user_id = m.group(1)

        # Extrair EventData com regex
        ed_match = re.search(r'<EventData>(.*?)</EventData>', xml, re.DOTALL)
        if ed_match:
            data_matches = re.findall(r'<Data\s+Name="([^"]*)"[^>]*>\s*(.*?)\s*</Data>', ed_match.group(1), re.DOTALL)
            for name, val in data_matches:
                self.event_data_list.append((name, val.strip()))
                if name:
                    self.event_data_dict[name] = val.strip()

    def obter_descricao(self):
        if self.id_evento == "1102":
            user = self.event_data_dict.get("SubjectUserName", "N/A")
            return (f"O log de auditoria foi limpo.\n\n"
                    f"Assunto:\n"
                    f"  ID de Segurança: {self.event_data_dict.get('SubjectUserSid', 'N/A')}\n"
                    f"  Nome da Conta: {user}\n"
                    f"  Domínio: {self.event_data_dict.get('SubjectDomainName', 'N/A')}\n"
                    f"  ID de Logon: {self.event_data_dict.get('SubjectLogonId', 'N/A')}")

        # Mapeamento de IDs comuns para descrições
        descricoes = {
            "4624": (f"Uma conta foi conectada com êxito.\n\n"
                     f"  Tipo de Logon: {self.event_data_dict.get('LogonType', 'N/A')}\n"
                     f"  Conta: {self.event_data_dict.get('TargetUserName', 'N/A')}\n"
                     f"  Domínio: {self.event_data_dict.get('TargetDomainName', 'N/A')}\n"
                     f"  Endereço de Origem: {self.event_data_dict.get('IpAddress', 'N/A')}"),
            "4625": (f"Falha ao conectar uma conta.\n\n"
                     f"  Conta: {self.event_data_dict.get('TargetUserName', 'N/A')}\n"
                     f"  Domínio: {self.event_data_dict.get('TargetDomainName', 'N/A')}\n"
                     f"  Endereço de Origem: {self.event_data_dict.get('IpAddress', 'N/A')}"),
            "4634": "Uma conta foi desconectada.",
            "4647": "Início do desligamento do sistema.",
            "4648": "Foi feita uma tentativa de logon usando credenciais explícitas.",
            "4672": "Privilégios especiais atribuídos a novo logon.",
            "4688": "Um novo processo foi criado.",
            "4689": "Um processo foi encerrado.",
            "4698": "Uma tarefa agendada foi criada.",
            "4699": "Uma tarefa agendada foi excluída.",
            "4700": "Uma tarefa agendada foi habilitada.",
            "4701": "Uma tarefa agendada foi desabilitada.",
            "4702": "Uma tarefa agendada foi atualizada.",
            "4719": "A política de auditoria do sistema foi alterada.",
            "4720": "Uma conta de usuário foi criada.",
            "4722": "Uma conta de usuário foi habilitada.",
            "4723": "Tentativa de alteração de senha.",
            "4724": "Tentativa de redefinição de senha.",
            "4725": "Uma conta de usuário foi desabilitada.",
            "4726": "Uma conta de usuário foi excluída.",
            "4728": "Um membro foi adicionado a um grupo de segurança global.",
            "4732": "Um membro foi adicionado a um grupo de segurança local.",
            "4733": "Um membro foi removido de um grupo de segurança local.",
            "4738": "Uma conta de usuário foi alterada.",
            "4740": "Uma conta de usuário foi bloqueada.",
            "4768": "Um TGT (Ticket Granting Ticket) foi solicitado.",
            "4769": "Um tíquete de serviço foi solicitado.",
            "4770": "Um tíquete de serviço foi renovado.",
            "4771": "Falha na pré-autenticação do Kerberos.",
            "4776": "O controlador de domínio validou as credenciais.",
            "4778": "Uma sessão foi reconectada a uma estação de janela.",
            "4779": "Uma sessão foi desconectada de uma estação de janela.",
            "4780": "O grupo de administradores foi enumerado.",
            "4800": "A estação de trabalho foi bloqueada.",
            "4801": "A estação de trabalho foi desbloqueada.",
            "4902": "A política de auditoria por usuário foi criada.",
            "4907": "As configurações de auditoria no objeto foram alteradas.",
            "4944": "A política do Firewall do Windows foi ativada.",
            "4946": "Foi feita uma exceção na lista do Firewall do Windows.",
            "4947": "Foi feita uma modificação de exceção do Firewall do Windows.",
            "4950": "Uma configuração do Firewall do Windows foi alterada.",
            "4953": "Uma regra do Firewall do Windows foi ignorada.",
            "4954": "As configurações do Firewall do Windows foram alteradas.",
            "4976": "Foi estabelecida uma negociação de modo principal com chave inválida.",
            "5049": "Um modo de segurança IPsec foi desativado.",
            "5050": "Uma tentativa de desativar programaticamente o Firewall do Windows.",
            "5051": "Um arquivo foi bloqueado virtualmente.",
            "5061": "Operação criptográfica.",
            "5120": "O servidor OCSP foi iniciado.",
            "5121": "O servidor OCSP foi interrompido.",
            "5140": "Um objeto de sistema de arquivos foi acessado.",
            "5152": "O pacote foi descartado pelo Firewall do Windows.",
            "5154": "O Firewall do Windows permitiu a conexão.",
            "5155": "O Firewall do Windows bloqueou a conexão.",
            "5156": "A conexão foi permitida pelo Firewall do Windows.",
            "5157": "A conexão foi bloqueada pelo Firewall do Windows.",
            "5158": "O serviço de plataforma de filtro permitiu a ligação.",
            "5159": "O serviço de plataforma de filtro bloqueou a ligação.",
            "5379": "As credenciais foram lidas pelo Gerenciador de Credenciais.",
            "5380": "Cofre de credenciais encontrado.",
            "5381": "Cofre de credenciais não encontrado.",
            "5440": "A enumeração de provedores de auditoria do LPC foi iniciada.",
            "5441": "Provedor de auditoria do LPC foi criado.",
            "5442": "Provedor de auditoria do LPC foi alterado.",
            "5443": "Provedor de auditoria do LPC foi removido.",
            "5444": "Provedor de auditoria do registro WMI foi criado.",
            "5446": "Filtro de auditoria do registro WMI foi criado.",
            "5447": "Filtro de auditoria do registro WMI foi alterado.",
            "5449": "Provedor de auditoria do LPC do AIP foi criado.",
            "5456": "A regra de conexão de segurança do IPsec foi adicionada.",
            "5457": "A regra de conexão de segurança do IPsec foi alterada.",
            "5458": "A regra de conexão de segurança do IPsec foi excluída.",
            "5459": "A regra de modo de segurança rápida do IPsec foi excluída.",
            "5460": "A regra de modo principal do IPsec foi excluída.",
            "5461": "A regra de modo rápido de segurança do IPsec foi adicionada.",
            "5462": "A regra de modo principal do IPsec foi adicionada.",
            "5463": "A regra de modo rápido de segurança do IPsec foi alterada.",
            "5464": "A regra de modo principal do IPsec foi alterada.",
            "5465": "A regra de conexão de segurança do IPsec foi alterada.",
            "5466": "O banco de dados de IPsec não foi atualizado.",
            "5467": "O banco de dados de IPsec foi atualizado.",
            "5468": "O banco de dados de IPsec foi atualizado novamente.",
            "5472": "A regra de modo rápido de segurança do IPsec foi alterada.",
            "5473": "A regra de modo principal do IPsec foi alterada.",
            "5474": "A regra de modo rápido de segurança do IPsec foi alterada.",
            "5477": "A consulta de associação de modo rápido falhou.",
            "5478": "O serviço IPsec foi iniciado.",
            "5479": "O serviço IPsec foi desativado.",
            "5480": "O serviço IPsec falhou ao obter a lista completa de interfaces de rede.",
            "5483": "O serviço IPsec não foi iniciado.",
            "5484": "O serviço IPsec foi desativado e descarregado.",
            "5485": "O serviço IPsec falhou em alguns eventos de rede."
        }
        return descricoes.get(self.id_evento, "Descrição não disponível para este evento.")

    def obter_categoria(self):
        categorias = {
            "1102": "Auditar Limpeza de Log",
            "4624": "Logon",
            "4625": "Falha de Logon",
            "4634": "Logoff",
            "4647": "Desligamento",
            "4648": "Logon com Credenciais Explícitas",
            "4672": "Atribuição de Privilégios Especiais",
            "4688": "Criação de Processo",
            "4689": "Término de Processo",
            "4698": "Tarefa Agendada",
            "4699": "Tarefa Agendada",
            "4700": "Tarefa Agendada",
            "4701": "Tarefa Agendada",
            "4702": "Tarefa Agendada",
            "4719": "Alteração de Política de Auditoria",
            "4720": "Gerenciamento de Contas de Usuário",
            "4722": "Gerenciamento de Contas de Usuário",
            "4723": "Gerenciamento de Contas de Usuário",
            "4724": "Gerenciamento de Contas de Usuário",
            "4725": "Gerenciamento de Contas de Usuário",
            "4726": "Gerenciamento de Contas de Usuário",
            "4728": "Gerenciamento de Grupo de Segurança",
            "4732": "Gerenciamento de Grupo de Segurança",
            "4733": "Gerenciamento de Grupo de Segurança",
            "4738": "Gerenciamento de Contas de Usuário",
            "4740": "Gerenciamento de Contas de Usuário",
            "4768": "Autenticação Kerberos",
            "4769": "Autenticação Kerberos",
            "4770": "Autenticação Kerberos",
            "4771": "Autenticação Kerberos",
            "4776": "Validação de Credenciais",
            "4778": "Conexão de Sessão",
            "4779": "Conexão de Sessão",
            "4780": "Gerenciamento de Grupo de Segurança",
            "4800": "Bloqueio de Estação de Trabalho",
            "4801": "Desbloqueio de Estação de Trabalho",
            "4902": "Alteração de Política de Auditoria",
            "4907": "Alteração de Política de Auditoria",
            "4944": "Política do Firewall do Windows",
            "4946": "Política do Firewall do Windows",
            "4947": "Política do Firewall do Windows",
            "4950": "Política do Firewall do Windows",
            "4953": "Política do Firewall do Windows",
            "4954": "Política do Firewall do Windows",
            "4976": "Negociação IPsec",
            "5049": "Negociação IPsec",
            "5050": "Política do Firewall do Windows",
            "5051": "Proteção contra Malware",
            "5061": "Operação Criptográfica",
            "5120": "Servidor OCSP",
            "5121": "Servidor OCSP",
            "5140": "Acesso a Objeto de Sistema de Arquivos",
            "5152": "Filtragem de Pacotes do Firewall do Windows",
            "5154": "Filtragem de Pacotes do Firewall do Windows",
            "5155": "Filtragem de Pacotes do Firewall do Windows",
            "5156": "Filtragem de Pacotes do Firewall do Windows",
            "5157": "Filtragem de Pacotes do Firewall do Windows",
            "5158": "Filtragem de Pacotes do Firewall do Windows",
            "5159": "Filtragem de Pacotes do Firewall do Windows",
            "5379": "Gerenciamento de Credenciais",
            "5380": "Gerenciamento de Credenciais",
            "5381": "Gerenciamento de Credenciais",
            "5440": "Auditoria do LPC de AIP",
            "5441": "Auditoria do LPC de AIP",
            "5442": "Auditoria do LPC de AIP",
            "5443": "Auditoria do LPC de AIP",
            "5444": "Auditoria do Registro WMI",
            "5446": "Auditoria do Registro WMI",
            "5447": "Auditoria do Registro WMI",
            "5449": "Auditoria do LPC de AIP",
            "5456": "Política IPsec",
            "5457": "Política IPsec",
            "5458": "Política IPsec",
            "5459": "Política IPsec",
            "5460": "Política IPsec",
            "5461": "Política IPsec",
            "5462": "Política IPsec",
            "5463": "Política IPsec",
            "5464": "Política IPsec",
            "5465": "Política IPsec",
            "5466": "Política IPsec",
            "5467": "Política IPsec",
            "5468": "Política IPsec",
            "5472": "Política IPsec",
            "5473": "Política IPsec",
            "5474": "Política IPsec",
            "5477": "Política IPsec",
            "5478": "Política IPsec",
            "5479": "Política IPsec",
            "5480": "Política IPsec",
            "5483": "Política IPsec",
            "5484": "Política IPsec",
            "5485": "Política IPsec"
        }
        return categorias.get(self.id_evento, self.task)

    def to_dict(self):
        return {
            'id': self.id_evento,
            'nivel': self.nivel,
            'fonte': self.fonte,
            'data': self.data_hora,
            'categoria': self.obter_categoria(),
            'computador': self.computador,
            'descricao': self.obter_descricao(),
            'keywords': self.keywords_nome,
            'xml': self.raw_xml
        }


# =============================================================================
# BARRA DE PROGRESSO VERDE
# =============================================================================
class BarraProgressoVerde(tk.Canvas):
    """Barra de progresso verde personalizada com cantos arredondados visuais."""

    def __init__(self, parent, width=400, height=28, **kwargs):
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bg=kwargs.get('bg', '#F0F0F0'),
                         **{k: v for k, v in kwargs.items() if k != 'bg'})

        self.largura = width
        self.altura = height
        self._valor = 0.0
        self._animacao_ativa = False
        self._texto_id = None
        self._barra_id = None
        self._fundo_id = None

        # Cores do gradiente verde (estilo Windows 10)
        self.cor_preenchimento_claro = "#6BB86B"
        self.cor_preenchimento_escuro = "#4CAF50"
        self.cor_borda_clara = "#3D8B40"
        self.cor_borda_escura = "#388E3C"
        self.cor_fundo = "#E8E8E8"
        self.cor_texto = "#FFFFFF"

        self.raio = 4
        self.margem = 1
        self._desenhar()

    def _desenhar(self):
        """Desenha o fundo e a barra de progresso."""
        self.delete("all")

        margem = self.margem
        r = self.raio
        w = self.largura - 2 * margem
        h = self.altura - 2 * margem

        # Remover IDs antigos
        self._texto_id = None
        self._barra_id = None
        self._fundo_id = None

        # --- Fundo (borda escura) ---
        self.create_rounded_rect(margem, margem, self.largura - margem,
                                  self.altura - margem, r + 1,
                                  fill=self.cor_borda_escura,
                                  outline=self.cor_borda_escura, width=1)

        # --- Interior (fundo claro) ---
        self.create_rounded_rect(margem + 1, margem + 1,
                                  self.largura - margem - 1,
                                  self.altura - margem - 1, r,
                                  fill=self.cor_fundo,
                                  outline=self.cor_fundo, width=0)

        # --- Barra de progresso ---
        if self._valor > 0:
            larg_preenchida = max(2, int((w - 2) * (self._valor / 100.0)))
            if larg_preenchida > 0:
                x1 = margem + 2
                y1 = margem + 2
                x2 = margem + 2 + larg_preenchida
                y2 = self.altura - margem - 2
                r_peq = max(1, r - 1)

                # Gradiente visual: retângulo principal + faixa mais clara no topo
                self._barra_id = self.create_rounded_rect(
                    x1, y1, x2, y2, r_peq,
                    fill=self.cor_preenchimento_escuro,
                    outline=self.cor_preenchimento_escuro, width=0
                )

                # Faixa de destaque no topo (efeito 3D leve)
                if h > 8:
                    faixa_h = max(2, int(h * 0.35))
                    self.create_rounded_rect(
                        x1, y1, x2, y1 + faixa_h, max(1, r_peq - 1),
                        fill=self.cor_preenchimento_claro,
                        outline="", width=0
                    )

        # --- Texto da porcentagem ---
        texto = f"{int(round(self._valor))}%"
        self._texto_id = self.create_text(
            self.largura // 2, self.altura // 2,
            text=texto, fill=self.cor_texto,
            font=("Segoe UI", 9, "bold"),
            anchor=tk.CENTER
        )

        # Atualizar cor do texto baseado no preenchimento
        self._ajustar_cor_texto()

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        """Desenha um retângulo com cantos arredondados."""
        if r <= 0:
            return self.create_rectangle(x1, y1, x2, y2, **kwargs)

        pontos = (
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1
        )
        return self.create_polygon(pontos, smooth=True, **kwargs)

    def _ajustar_cor_texto(self):
        """Ajusta a cor do texto baseado na posição da barra."""
        if self._texto_id is None:
            return

        meio = self.largura // 2
        larg_preenchida = int((self.largura - 4) * (self._valor / 100.0))

        # Se o texto está sobre a parte preenchida, texto branco; senão, texto escuro
        if larg_preenchida >= meio:
            self.itemconfig(self._texto_id, fill="#FFFFFF")
            # Adicionar sombra para legibilidade
            try:
                self.itemconfig(self._texto_id, font=("Segoe UI", 9, "bold"))
            except:
                pass
        else:
            self.itemconfig(self._texto_id, fill="#444444")

    def set_valor(self, valor):
        """Define o valor atual (0-100) sem animação."""
        valor = max(0.0, min(100.0, float(valor)))
        self._valor = valor
        self._desenhar()
        self.update_idletasks()

    def animar_para(self, valor_alvo, duracao=300, passos=20):
        """Anima a transição para um valor alvo."""
        valor_alvo = max(0.0, min(100.0, float(valor_alvo)))
        valor_inicial = self._valor

        if abs(valor_alvo - valor_inicial) < 0.5:
            self.set_valor(valor_alvo)
            return

        if self._animacao_ativa:
            return

        self._animacao_ativa = True
        self._animar_passos(valor_inicial, valor_alvo, duracao, passos, 0)

    def _animar_passos(self, inicio, fim, duracao, passos, passo_atual):
        if passo_atual >= passos:
            self.set_valor(fim)
            self._animacao_ativa = False
            return

        progresso = (passo_atual + 1) / passos
        # Easing suave (quadrático)
        progresso_easing = progresso * progresso * (3 - 2 * progresso)
        valor_atual = inicio + (fim - inicio) * progresso_easing
        self.set_valor(valor_atual)

        intervalo = max(10, int(duracao / passos))
        self.after(intervalo, lambda: self._animar_passos(
            inicio, fim, duracao, passos, passo_atual + 1
        ))

    def reset(self):
        """Reseta a barra para 0%."""
        self._animacao_ativa = False
        self.set_valor(0.0)


# =============================================================================
# CLASSE PRINCIPAL - VisualizadorEventosFiel
# =============================================================================
class VisualizadorEventosFiel(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Visualizador de Eventos do Windows 10")
        self.geometry("1200x750")
        self.state("zoomed")   # Abre maximizado
        self.minsize(900, 600)

        # Configurar estilo
        try:
            self.style = ttk.Style()
            self.style.theme_use("vista")
        except:
            pass

        # Variáveis de estado
        self.eventos = []
        self.eventos_dict = []
        self.total_registros_log = 0
        self.log_atual = "Nenhum"
        self.filtro_ativo = False
        self.todos_os_logs = []

        # Cache de logs disponíveis
        self.logs_disponiveis = {}
        self.listar_logs()

        # ========== CONSTRUÇÃO DA INTERFACE ==========
        self._construir_menu()
        self._construir_barra_ferramentas()
        self._construir_painel_principal()
        self._construir_barra_status()

        # ========== CARREGAMENTO AUTOMÁTICO ==========
        self.after(500, self._disparar_carregamento_inicial)

        # Bind de fechamento
        self.protocol("WM_DELETE_WINDOW", self._fechar)

    # =========================================================================
    # LISTAGEM DE LOGS
    # =========================================================================
    def listar_logs(self):
        """Lista todos os logs do Windows via wevtutil el."""
        self.logs_disponiveis = {}
        logs_preferenciais = [
            "Application", "Security", "System", "Setup",
            "Windows PowerShell",
            "Microsoft-Windows-TaskScheduler/Operational",
            "Microsoft-Windows-Sysmon/Operational",
            "Microsoft-Windows-TerminalServices-LocalSessionManager/Operational",
            "Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational",
            "Microsoft-Windows-Windows Firewall With Advanced Security/Firewall",
            "Microsoft-Windows-AppLocker/EXE and DLL",
            "Microsoft-Windows-AppLocker/MSI and Script",
            "Microsoft-Windows-AppLocker/Packaged app-Execution",
            "Microsoft-Windows-AppLocker/Packaged app-Installation",
            "HardwareEvents", "Internet Explorer", "Key Management Service",
            "Microsoft-Windows-Diagnostics-Performance/Operational",
            "Microsoft-Windows-DNS-Client/Operational",
            "Microsoft-Windows-Dhcp-Client/Operational",
            "Microsoft-Windows-NetworkProfile/Operational",
            "Microsoft-Windows-NCSI/Operational",
            "Microsoft-Windows-WLAN-AutoConfig/Operational",
            "OpenSSH/Admin", "OpenSSH/Operational",
            "Microsoft-Windows-PowerShell/Operational",
            "Microsoft-Windows-PrintService/Admin",
            "Microsoft-Windows-PrintService/Operational",
            "Microsoft-Windows-RemoteAssistance/Operational",
            "Microsoft-Windows-RemoteDesktopServices-RDPCoreTS/Operational",
            "Microsoft-Windows-RestartManager/Operational",
            "Microsoft-Windows-SmartCard-Audit/Authentication",
            "Microsoft-Windows-Store/Operational",
            "Microsoft-Windows-User Profile Service/Operational",
            "Microsoft-Windows-User-Logger/Operational",
            "Microsoft-Windows-VolumeSnapshot-Driver/Operational",
            "Microsoft-Windows-WinRM/Operational",
            "Microsoft-Windows-WMI-Activity/Operational",
            "Windows System Resource Manager"
        ]

        try:
            result = subprocess.run(["wevtutil", "el"], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logs_raw = [l.strip() for l in result.stdout.splitlines() if l.strip()]

                for log_nome in logs_raw:
                    nome_curto = log_nome.split('/')[-1].split('-')[-1]
                    nome_amigavel = log_nome

                    # Nomes amigáveis para logs comuns
                    mapa_nomes = {
                        "Application": "Application",
                        "Security": "Security",
                        "System": "System",
                        "Setup": "Setup",
                        "ForwardedEvents": "ForwardedEvents",
                        "HardwareEvents": "HardwareEvents",
                        "Internet Explorer": "Internet Explorer",
                        "Key Management Service": "Key Management Service",
                        "Windows PowerShell": "Windows PowerShell",
                        "Microsoft-Windows-TaskScheduler/Operational": "TaskScheduler",
                        "Microsoft-Windows-Sysmon/Operational": "Sysmon",
                        "Microsoft-Windows-TerminalServices-LocalSessionManager/Operational": "RemoteDesktop (Sessions)",
                        "Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational": "RemoteDesktop (Connections)",
                        "Microsoft-Windows-Windows Firewall With Advanced Security/Firewall": "Firewall",
                        "Microsoft-Windows-AppLocker/EXE and DLL": "AppLocker (EXE-DLL)",
                        "Microsoft-Windows-AppLocker/MSI and Script": "AppLocker (MSI-Script)",
                        "Microsoft-Windows-AppLocker/Packaged app-Execution": "AppLocker (Packaged-Execution)",
                        "Microsoft-Windows-AppLocker/Packaged app-Installation": "AppLocker (Packaged-Install)",
                        "Microsoft-Windows-Diagnostics-Performance/Operational": "Diagnostics-Performance",
                        "Microsoft-Windows-DNS-Client/Operational": "DNS Client",
                        "Microsoft-Windows-Dhcp-Client/Operational": "DHCP Client",
                        "Microsoft-Windows-NetworkProfile/Operational": "Network Profile",
                        "Microsoft-Windows-NCSI/Operational": "Network Connectivity Status",
                        "Microsoft-Windows-WLAN-AutoConfig/Operational": "WLAN AutoConfig",
                        "Microsoft-Windows-PowerShell/Operational": "PowerShell (Operational)",
                        "Microsoft-Windows-PrintService/Admin": "PrintService (Admin)",
                        "Microsoft-Windows-PrintService/Operational": "PrintService (Operational)",
                        "Microsoft-Windows-RemoteDesktopServices-RDPCoreTS/Operational": "RDP Core TS",
                        "Microsoft-Windows-SmartCard-Audit/Authentication": "SmartCard Authentication",
                        "Microsoft-Windows-User Profile Service/Operational": "User Profile Service",
                        "Microsoft-Windows-VolumeSnapshot-Driver/Operational": "Volume Snapshot",
                        "Microsoft-Windows-WinRM/Operational": "WinRM",
                        "Microsoft-Windows-WMI-Activity/Operational": "WMI Activity",
                        "OpenSSH/Admin": "OpenSSH (Admin)",
                        "OpenSSH/Operational": "OpenSSH (Operational)"
                    }

                    nome_amigavel = mapa_nomes.get(log_nome, log_nome)
                    self.logs_disponiveis[nome_amigavel] = log_nome

                # Reordena para colocar logs preferenciais primeiro
                logs_ordenados = {}
                for pref in logs_preferenciais:
                    for nome_amigavel, nome_real in list(self.logs_disponiveis.items()):
                        if nome_real == pref or nome_real.endswith(pref):
                            logs_ordenados[nome_amigavel] = nome_real
                            break

                for nome_amigavel, nome_real in self.logs_disponiveis.items():
                    if nome_real not in logs_ordenados.values():
                        logs_ordenados[nome_amigavel] = nome_real

                self.logs_disponiveis = logs_ordenados
        except:
            # Fallback: logs padrão
            self.logs_disponiveis = {
                "Application": "Application",
                "Security": "Security",
                "System": "System",
                "Setup": "Setup"
            }

    # =========================================================================
    # CONSTRUÇÃO DA INTERFACE
    # =========================================================================
    def _construir_menu(self):
        """Constrói a barra de menus (réplica do Visualizador de Eventos)."""
        self.menu_bar = tk.Menu(self, font=("Segoe UI", 9))

        # Arquivo
        menu_arquivo = tk.Menu(self.menu_bar, tearoff=0, font=("Segoe UI", 9))
        menu_arquivo.add_command(label="Abrir Log Salvo...", command=self.abrir_log_salvo, accelerator="Ctrl+O")
        menu_arquivo.add_separator()
        menu_arquivo.add_command(label="Exportar...", command=self.exportar_logs, accelerator="Ctrl+E")
        menu_arquivo.add_separator()
        menu_arquivo.add_command(label="Sair", command=self._fechar, accelerator="Alt+F4")
        self.menu_bar.add_cascade(label="Arquivo", menu=menu_arquivo)

        # Ação
        menu_acao = tk.Menu(self.menu_bar, tearoff=0, font=("Segoe UI", 9))
        menu_acao.add_command(label="Localizar...", command=self.pesquisar, accelerator="Ctrl+F")
        menu_acao.add_command(label="Localizar Próximo", state=tk.DISABLED, accelerator="F3")
        menu_acao.add_separator()
        menu_acao.add_command(label="Filtrar Log Atual...", command=self.filtro_avancado)
        menu_acao.add_command(label="Limpar Log...", command=self.limpar_log)
        menu_acao.add_separator()
        menu_acao.add_command(label="Propriedades", state=tk.DISABLED, accelerator="Enter")
        menu_acao.add_command(label="Salvar Eventos Selecionados...", state=tk.DISABLED)
        menu_acao.add_separator()
        menu_acao.add_command(label="Anexar uma Tarefa a Este Evento...", state=tk.DISABLED)
        menu_acao.add_command(label="Exibir", command=lambda: self.mostrar_detalhes_janela())
        menu_acao.add_separator()
        menu_acao.add_command(label="Atualizar", command=self.atualizar, accelerator="F5")
        self.menu_bar.add_cascade(label="Ação", menu=menu_acao)

        # Exibir
        menu_exibir = tk.Menu(self.menu_bar, tearoff=0, font=("Segoe UI", 9))
        menu_exibir.add_command(label="Adicionar/Remover Colunas...", command=self.configurar_colunas)
        menu_exibir.add_separator()
        menu_exibir.add_command(label="Ir para o final", state=tk.DISABLED)
        menu_exibir.add_command(label="Ir para o início", state=tk.DISABLED)
        self.menu_bar.add_cascade(label="Exibir", menu=menu_exibir)

        # Ajuda
        menu_ajuda = tk.Menu(self.menu_bar, tearoff=0, font=("Segoe UI", 9))
        menu_ajuda.add_command(label="Sobre o Visualizador de Eventos", command=self._sobre)
        self.menu_bar.add_cascade(label="Ajuda", menu=menu_ajuda)

        self.config(menu=self.menu_bar)

        # Atalhos de teclado
        self.bind("<Control-o>", lambda e: self.abrir_log_salvo())
        self.bind("<Control-O>", lambda e: self.abrir_log_salvo())
        self.bind("<Control-e>", lambda e: self.exportar_logs())
        self.bind("<Control-E>", lambda e: self.exportar_logs())
        self.bind("<Control-f>", lambda e: self.pesquisar())
        self.bind("<Control-F>", lambda e: self.pesquisar())
        self.bind("<F5>", lambda e: self.atualizar())

    def _construir_barra_ferramentas(self):
        """Constrói a barra de ferramentas superior."""
        frame_ferramentas = ttk.Frame(self)
        frame_ferramentas.pack(fill=tk.X, padx=5, pady=(3, 0))

        # Botões de ação
        ttk.Button(frame_ferramentas, text="✕  Remover Ações",
                   command=lambda: None, width=18).pack(side=tk.LEFT, padx=1)
        ttk.Button(frame_ferramentas, text="Criar Exibição Personalizada...",
                   command=self.criar_exibicao, width=28).pack(side=tk.LEFT, padx=1)
        ttk.Button(frame_ferramentas, text="Atualizar",
                   command=self.atualizar, width=12).pack(side=tk.LEFT, padx=1)

        # Barra de progresso verde
        self.progress_bar = BarraProgressoVerde(frame_ferramentas, width=250, height=24)
        self.progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)

    def _construir_painel_principal(self):
        """Constrói o painel principal com árvore de logs, tabela e pré-visualização."""
        paned_principal = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_principal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ============ PAINEL ESQUERDO (Árvore de Logs) ============
        frame_esquerdo = ttk.Frame(paned_principal, width=280)
        paned_principal.add(frame_esquerdo, weight=0)

        ttk.Label(frame_esquerdo, text="Visualizador de Eventos (Local)",
                 font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=5, pady=(5, 2))

        self.tree_logs = ttk.Treeview(frame_esquerdo, columns=(), show="tree", height=20)
        scroll_tree = ttk.Scrollbar(frame_esquerdo, orient="vertical", command=self.tree_logs.yview)
        self.tree_logs.configure(yscrollcommand=scroll_tree.set)

        self.tree_logs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_tree.pack(side=tk.RIGHT, fill=tk.Y)

        # Popula a árvore de logs
        self._popular_arvore_logs()

        self.tree_logs.bind("<<TreeviewSelect>>", self._ao_selecionar_log)

        # ============ PAINEL DIREITO (Tabela + Detalhes) ============
        frame_direito = ttk.Frame(paned_principal)
        paned_principal.add(frame_direito, weight=1)

        paned_vertical = ttk.PanedWindow(frame_direito, orient=tk.VERTICAL)
        paned_vertical.pack(fill=tk.BOTH, expand=True)

        # --- CAMINHO DO LOG ---
        self.caminho_label = ttk.Label(frame_direito, text="Nenhum log selecionado",
                                        font=("Segoe UI", 9))
        self.caminho_label.pack(anchor=tk.W, padx=2, pady=(2, 0))

        # --- FILTRO RÁPIDO ---
        frame_filtro = ttk.Frame(frame_direito)
        frame_filtro.pack(fill=tk.X, padx=2, pady=2)

        ttk.Label(frame_filtro, text="Filtrar:", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        self.filtro_nivel = ttk.Combobox(frame_filtro, values=[
            "Todos", "Crítico", "Erro", "Aviso", "Informações",
            "Êxito de Auditoria", "Falha de Auditoria", "Detalhes"
        ], width=18, state="readonly")
        self.filtro_nivel.set("Todos")
        self.filtro_nivel.pack(side=tk.LEFT, padx=5)
        self.filtro_nivel.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtro_rapido())

        ttk.Label(frame_filtro, text="ID:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.filtro_id = ttk.Entry(frame_filtro, width=12)
        self.filtro_id.pack(side=tk.LEFT, padx=2)
        self.filtro_id.bind("<Return>", lambda e: self.aplicar_filtro_rapido())

        ttk.Label(frame_filtro, text="Texto:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.filtro_texto = ttk.Entry(frame_filtro, width=20)
        self.filtro_texto.pack(side=tk.LEFT, padx=2)
        self.filtro_texto.bind("<Return>", lambda e: self.aplicar_filtro_rapido())

        ttk.Button(frame_filtro, text="Limpar", command=self.limpar_filtro_rapido,
                   width=8).pack(side=tk.LEFT, padx=3)

        ttk.Button(frame_filtro, text="Filtrar Log Atual...",
                   command=self.filtro_avancado, width=18).pack(side=tk.RIGHT, padx=3)

        # --- TABELA DE EVENTOS ---
        frame_tabela = ttk.Frame(paned_vertical)
        paned_vertical.add(frame_tabela, weight=2)

        colunas = ("nivel", "data", "fonte", "id", "categoria", "computador")
        cabecalhos = {
            "nivel": "Nível",
            "data": "Data e Hora",
            "fonte": "Fonte",
            "id": "ID do Evento",
            "categoria": "Categoria da Tarefa",
            "computador": "Computador"
        }

        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=15)
        for col, cab in cabecalhos.items():
            self.tree.heading(col, text=cab, command=lambda c=col: self._ordenar_por(c))
            self.tree.column(col, width=120, minwidth=60)

        self.tree.column("nivel", width=90)
        self.tree.column("id", width=90)
        self.tree.column("data", width=160)
        self.tree.column("computador", width=140)

        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.bind("<Double-1>", self.mostrar_detalhes_janela)
        self.tree.bind("<Return>", self.mostrar_detalhes_janela)
        self.tree.bind("<Button-3>", self._menu_contexto_evento)

        # --- PRÉ-VISUALIZAÇÃO (abaixo da tabela) ---
        frame_preview = ttk.LabelFrame(paned_vertical, text="Pré-visualização do Evento", padding=5)
        paned_vertical.add(frame_preview, weight=1)

        self.preview_text = tk.Text(frame_preview, wrap=tk.WORD, font=("Segoe UI", 9),
                                     height=8, relief=tk.FLAT, borderwidth=1)
        scroll_preview = ttk.Scrollbar(frame_preview, orient="vertical",
                                        command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scroll_preview.set)

        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_preview.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_text.config(state=tk.DISABLED)

        self.tree.bind("<<TreeviewSelect>>", self._atualizar_preview)

    def _construir_barra_status(self):
        """Constrói a barra de status inferior."""
        self.barra_status = ttk.Label(self, text="Visualizador de Eventos pronto",
                                       relief=tk.SUNKEN, anchor=tk.W,
                                       font=("Segoe UI", 9), padding=(5, 2))
        self.barra_status.pack(side=tk.BOTTOM, fill=tk.X)

    def _popular_arvore_logs(self):
        """Popula a TreeView com os logs do Windows."""
        self.tree_logs.delete(*self.tree_logs.get_children())

        # Nó principal "Visualizador de Eventos (Local)"
        raiz = self.tree_logs.insert("", "end", text="Visualizador de Eventos (Local)",
                                      open=True, tags=("raiz",))

        # --- Logs do Windows ---
        windows_logs = self.tree_logs.insert(raiz, "end", text="Logs do Windows",
                                              open=True, tags=("pasta",))

        logs_principais = ["Application", "Security", "System", "Setup"]
        for log_nome in logs_principais:
            if log_nome in self.logs_disponiveis:
                self.tree_logs.insert(windows_logs, "end", text=log_nome,
                                       values=(log_nome,), tags=("log",))
            else:
                # Busca pelo nome real
                for nome_amigavel, nome_real in self.logs_disponiveis.items():
                    if nome_real == log_nome:
                        self.tree_logs.insert(windows_logs, "end", text=nome_amigavel,
                                               values=(nome_amigavel,), tags=("log",))
                        break

        # --- Applications and Services Logs ---
        apps_logs = self.tree_logs.insert(raiz, "end", text="Applications and Services Logs",
                                           open=False, tags=("pasta",))

        # Subpastas para organização
        subpastas = {
            "Microsoft": {},
            "OpenSSH": {}
        }

        for nome_amigavel in self.logs_disponiveis:
            if nome_amigavel in logs_principais:
                continue
            if nome_amigavel.startswith("Microsoft-") or "/" in nome_amigavel:
                if "OpenSSH" in nome_amigavel:
                    subpastas["OpenSSH"][nome_amigavel] = self.logs_disponiveis[nome_amigavel]
                else:
                    subpastas["Microsoft"][nome_amigavel] = self.logs_disponiveis[nome_amigavel]

        # Pasta Microsoft
        ms_pasta = self.tree_logs.insert(apps_logs, "end", text="Microsoft",
                                          open=False, tags=("pasta",))
        # Pasta Windows
        win_pasta = self.tree_logs.insert(ms_pasta, "end", text="Windows",
                                           open=False, tags=("pasta",))

        for nome_amigavel in sorted(subpastas["Microsoft"].keys()):
            self.tree_logs.insert(win_pasta, "end", text=nome_amigavel,
                                   values=(nome_amigavel,), tags=("log",))

        # OpenSSH
        if subpastas["OpenSSH"]:
            ssh_pasta = self.tree_logs.insert(apps_logs, "end", text="OpenSSH",
                                               open=False, tags=("pasta",))
            for nome_amigavel in sorted(subpastas["OpenSSH"].keys()):
                self.tree_logs.insert(ssh_pasta, "end", text=nome_amigavel,
                                       values=(nome_amigavel,), tags=("log",))

        # Logs não categorizados
        for nome_amigavel in self.logs_disponiveis:
            if (nome_amigavel not in logs_principais and
                nome_amigavel not in subpastas["Microsoft"] and
                nome_amigavel not in subpastas["OpenSSH"]):
                self.tree_logs.insert(apps_logs, "end", text=nome_amigavel,
                                       values=(nome_amigavel,), tags=("log",))

    # =========================================================================
    # CARREGAMENTO DE EVENTOS
    # =========================================================================
    def _disparar_carregamento_inicial(self):
        """Inicia o carregamento automático dos logs."""
        log_inicial = "Application"
        self.caminho_label.config(text=f"Carregando {log_inicial}...")
        self.barra_status.config(text=f"Inicializando... Carregando {log_inicial}")
        self.progress_bar.reset()
        self.carregar_eventos_log(log_inicial)

    def carregar_eventos_log(self, nome_log_display):
        """Carrega eventos de um log em thread separada com barra de progresso."""
        threading.Thread(
            target=self._carregar_eventos_thread,
            args=(nome_log_display,),
            daemon=True
        ).start()

    def _carregar_eventos_thread(self, nome_log_display):
        """Thread de carregamento com atualizações de progresso."""
        pythoncom.CoInitialize()
        try:
            self.after(0, lambda: self._atualizar_progresso(0, f"Iniciando carregamento de {nome_log_display}..."))

            nome_real = self.logs_disponiveis.get(nome_log_display, nome_log_display)

            self.after(0, lambda: self._atualizar_progresso(3, f"Consultando log {nome_log_display}..."))

            # Primeiro, conta o total de eventos
            try:
                cmd_count = ["wevtutil", "gli", nome_real]
                result_count = subprocess.run(cmd_count, capture_output=True, text=True, timeout=30)
                total_eventos = 0
                if result_count.returncode == 0:
                    for line in result_count.stdout.splitlines():
                        if "numberOfLogRecords" in line.lower() or "eventos" in line.lower():
                            try:
                                total_eventos = int(line.split(':')[1].strip())
                            except:
                                pass
                        m = re.search(r'(\d[\d,]*)', line)
                        if m and ('event' in line.lower() or 'regist' in line.lower()):
                                    try:
                                        total_eventos = int(m.group(1).replace(',', ''))
                                    except:
                                        pass
                    if total_eventos == 0:
                        # Tenta pegar de outra forma
                        for line in result_count.stdout.splitlines():
                            m = re.search(r':\s*(\d+)', line)
                            if m:
                                try:
                                    total_eventos = int(m.group(1))
                                except:
                                    pass
                                break
            except:
                total_eventos = 0

            # Determina quantidade a carregar
            if total_eventos > 50000:
                qtd_eventos = 50000
            elif total_eventos > 10000:
                qtd_eventos = total_eventos
            else:
                qtd_eventos = total_eventos if total_eventos > 0 else 5000

            self.after(0, lambda: self._atualizar_progresso(5, f"Carregando até {qtd_eventos} eventos de {nome_log_display}..."))

            # Comando wevtutil COM /e:Events para XML bem formado
            cmd = [
                "wevtutil", "qe", nome_real,
                "/f:XML",
                "/e:Events",
                "/rd:true",
                f"/c:{qtd_eventos}"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                erro = result.stderr[:200] if result.stderr else "Erro desconhecido"
                self.after(0, lambda e=erro: self._erro_carregamento(f"Erro wevtutil: {e}"))
                return

            self.after(0, lambda: self._atualizar_progresso(15, "Processando XML dos eventos..."))

            xml_output = result.stdout

            # Extrai eventos individuais com regex
            padrao = r'<Event\s[^>]*>.*?</Event>'
            matches = re.findall(padrao, xml_output, re.DOTALL)

            if not matches:
                # Tenta padrão alternativo
                padrao2 = r'<Event[^>]*>.*?Event>'
                matches = re.findall(padrao2, xml_output, re.DOTALL)

            total_encontrados = len(matches)
            self.after(0, lambda: self._atualizar_progresso(20, f"Parseando {total_encontrados} eventos..."))

            eventos_temp = []
            eventos_dict_temp = []

            for i, xml_event in enumerate(matches):
                try:
                    ev = EventoCompleto(xml_event, nome_real)
                    eventos_temp.append(ev)
                    eventos_dict_temp.append(ev.to_dict())

                    # Atualiza progresso de 20% a 90% baseado no progresso do parse
                    if total_encontrados > 0 and i % max(1, total_encontrados // 20) == 0:
                        pct = 20 + int(70 * (i + 1) / total_encontrados)
                        self.after(0, lambda p=pct, i=i, t=total_encontrados:
                            self._atualizar_progresso(p, f"Parseando eventos... {i+1}/{t}"))
                except Exception:
                    continue

            # Inverte para ordem cronológica (mais recentes primeiro já estamos com /rd:true)
            # Se quiser mais recentes primeiro, mantém como está
            # eventos_temp.reverse()
            # eventos_dict_temp.reverse()

            self.after(0, lambda: self._atualizar_progresso(92, "Atualizando interface..."))

            eventos_temp.reverse()
            eventos_dict_temp.reverse()

            self.eventos = eventos_temp
            self.eventos_dict = eventos_dict_temp
            self.total_registros_log = total_encontrados
            self.log_atual = nome_log_display

            self.after(0, lambda: self._atualizar_progresso(96, "Renderizando tabela..."))
            self.after(0, self.atualizar_tabela)

            self.after(0, lambda: self._atualizar_progresso(98, "Finalizando..."))
            self.after(0, lambda: self.caminho_label.config(
                text=f"{nome_log_display}  |  Número de eventos: {self._formatar_numero(total_encontrados)}"))
            self.after(0, lambda: self.barra_status.config(
                text=f"{nome_log_display}: {self._formatar_numero(total_encontrados)} eventos carregados"))

            self.after(0, lambda: self._atualizar_progresso(100, "Carregamento concluído!"))
            self.after(500, lambda: self.progress_bar.animar_para(100, duracao=200))

        except subprocess.TimeoutExpired:
            self.after(0, lambda: self._erro_carregamento("Timeout: o comando wevtutil excedeu 120 segundos."))
        except Exception as e:
            self.after(0, lambda e=e: self._erro_carregamento(f"Erro inesperado: {str(e)[:200]}"))
        finally:
            pythoncom.CoUninitialize()

    def _atualizar_progresso(self, valor, mensagem=""):
        """Atualiza a barra de progresso e a mensagem de status."""
        self.progress_bar.animar_para(valor, duracao=200)
        if mensagem:
            self.barra_status.config(text=mensagem)
        self.update_idletasks()

    def _erro_carregamento(self, mensagem):
        self.progress_bar.reset()
        self.barra_status.config(text=f"Erro: {mensagem}")  # <-- só barra de status

    # =========================================================================
    # OPERAÇÕES DA TABELA
    # =========================================================================
    def atualizar_tabela(self):
        """Atualiza a tabela com os eventos carregados."""
        for i in self.tree.get_children():
            self.tree.delete(i)

        if not self.eventos:
            self.barra_status.config(text="Nenhum evento encontrado.")
            return

        for ev in self.eventos:
            if isinstance(ev, EventoCompleto):
                self.tree.insert("", "end", values=(
                    ev.nivel,
                    ev.data_hora if ev.data_hora else "",
                    ev.fonte,
                    ev.id_evento,
                    ev.obter_categoria(),
                    ev.computador if ev.computador else ""
                ))
            else:
                self.tree.insert("", "end", values=(
                    ev.get('nivel', ''),
                    ev.get('data', ''),
                    ev.get('fonte', ''),
                    ev.get('id', ''),
                    ev.get('categoria', ''),
                    ev.get('computador', '')
                ))

    def aplicar_filtro_rapido(self):
        """Aplica filtro rápido (nível, ID, texto)."""
        nivel = self.filtro_nivel.get()
        id_text = self.filtro_id.get().strip()
        texto = self.filtro_texto.get().strip().lower()

        for i in self.tree.get_children():
            self.tree.delete(i)

        count = 0
        for ev in self.eventos:
            if isinstance(ev, EventoCompleto):
                if nivel != "Todos" and ev.nivel != nivel:
                    continue
                if id_text and ev.id_evento != id_text:
                    continue
                if texto:
                    desc = ev.obter_descricao().lower()
                    fonte = ev.fonte.lower()
                    if texto not in desc and texto not in fonte and texto not in ev.id_evento:
                        continue
                self.tree.insert("", "end", values=(
                    ev.nivel, ev.data_hora, ev.fonte,
                    ev.id_evento, ev.obter_categoria(), ev.computador
                ))
                count += 1
            else:
                if nivel != "Todos" and ev.get('nivel') != nivel:
                    continue
                if id_text and ev.get('id') != id_text:
                    continue
                if texto:
                    desc = ev.get('descricao', '').lower()
                    fonte = ev.get('fonte', '').lower()
                    if texto not in desc and texto not in fonte and texto not in ev.get('id', ''):
                        continue
                self.tree.insert("", "end", values=(
                    ev.get('nivel', ''), ev.get('data', ''),
                    ev.get('fonte', ''), ev.get('id', ''),
                    ev.get('categoria', ''), ev.get('computador', '')
                ))
                count += 1

        self.filtro_ativo = True if (nivel != "Todos" or id_text or texto) else False
        self.barra_status.config(text=f"Filtro: {count} resultados de {len(self.eventos)} eventos")

    def limpar_filtro_rapido(self):
        """Limpa todos os filtros e restaura a visualização completa."""
        self.filtro_nivel.set("Todos")
        self.filtro_id.delete(0, tk.END)
        self.filtro_texto.delete(0, tk.END)
        self.filtro_ativo = False
        self.atualizar_tabela()
        self.barra_status.config(
            text=f"{self.log_atual}: {self._formatar_numero(len(self.eventos))} eventos")

    def _ordenar_por(self, coluna):
        """Ordena a tabela pela coluna clicada."""
        col_index = {"nivel": 0, "data": 1, "fonte": 2, "id": 3, "categoria": 4, "computador": 5}
        idx = col_index.get(coluna, 0)

        items = [(self.tree.set(child, coluna), child) for child in self.tree.get_children("")]
        items.sort(key=lambda x: x[0].lower())

        for i, (_, child) in enumerate(items):
            self.tree.move(child, "", i)

    def _atualizar_preview(self, e=None):
        """Atualiza a pré-visualização do evento selecionado."""
        sel = self.tree.selection()
        if not sel:
            return

        idx = self.tree.index(sel[0])

        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)

        if idx < len(self.eventos):
            ev = self.eventos[idx]
            if isinstance(ev, EventoCompleto):
                self.preview_text.insert(tk.END, f"ID do Evento: {ev.id_evento}\n")
                self.preview_text.insert(tk.END, f"Fonte: {ev.fonte}\n")
                self.preview_text.insert(tk.END, f"Data: {ev.data_hora}\n")
                self.preview_text.insert(tk.END, f"Computador: {ev.computador}\n")
                self.preview_text.insert(tk.END, f"Keywords: {ev.keywords_nome}\n\n")
                desc = ev.obter_descricao()
                self.preview_text.insert(tk.END, desc[:500] if desc else "Sem descrição")
            else:
                self.preview_text.insert(tk.END, f"ID do Evento: {ev.get('id', '')}\n")
                self.preview_text.insert(tk.END, f"Fonte: {ev.get('fonte', '')}\n")
                self.preview_text.insert(tk.END, f"Data: {ev.get('data', '')}\n")
                self.preview_text.insert(tk.END, f"Descrição: {ev.get('descricao', '')[:500]}")

        self.preview_text.config(state=tk.DISABLED)

    def _menu_contexto_evento(self, e):
        """Menu de contexto ao clicar com botão direito no evento."""
        sel = self.tree.selection()
        if not sel:
            return

        menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 9))
        menu.add_command(label="Exibir", command=self.mostrar_detalhes_janela)
        menu.add_separator()
        menu.add_command(label="Copiar", command=lambda: self._copiar_evento())
        menu.add_command(label="Copiar Tabela", command=lambda: self._copiar_tabela())
        menu.add_separator()
        menu.add_command(label="Salvar Eventos Selecionados...", state=tk.DISABLED)
        menu.add_separator()
        menu.add_command(label="Atualizar", command=self.atualizar)

        try:
            menu.tk_popup(e.x_root, e.y_root)
        finally:
            menu.grab_release()

    def _copiar_evento(self):
        """Copia o evento selecionado para a área de transferência."""
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if idx < len(self.eventos):
            ev = self.eventos[idx]
            texto = f"{ev.nivel}\t{ev.data_hora}\t{ev.fonte}\t{ev.id_evento}\t{ev.obter_categoria()}\t{ev.computador}"
            self.clipboard_clear()
            self.clipboard_append(texto)
            self.barra_status.config(text="Evento copiado para a área de transferência")

    def _copiar_tabela(self):
        """Copia todos os eventos visíveis para a área de transferência."""
        texto = "Nível\tData e Hora\tFonte\tID do Evento\tCategoria da Tarefa\tComputador\n"
        for child in self.tree.get_children():
            valores = self.tree.item(child, "values")
            texto += "\t".join(valores) + "\n"
        self.clipboard_clear()
        self.clipboard_append(texto)
        self.barra_status.config(text=f"{len(self.tree.get_children())} linhas copiadas")

    # =========================================================================
    # EVENTOS DA ÁRVORE DE LOGS
    # =========================================================================
    def _ao_selecionar_log(self, e=None):
        """Quando um log é selecionado na árvore."""
        sel = self.tree_logs.selection()
        if not sel:
            return

        item = sel[0]
        tags = self.tree_logs.item(item, "tags")
        valores = self.tree_logs.item(item, "values")

        if "log" in tags and valores:
            nome_log = valores[0]
            self.progress_bar.reset()
            self.caminho_label.config(text=f"Carregando {nome_log}...")
            self.barra_status.config(text=f"Abrindo {nome_log}...")
            self.carregar_eventos_log(nome_log)

    # =========================================================================
    # FILTRO AVANÇADO
    # =========================================================================
    def filtro_avancado(self):
        """Abre a janela de filtro avançado (réplica do Visualizador de Eventos)."""
        if not self.eventos:
            messagebox.showinfo("Filtro", "Nenhum evento para filtrar.")
            return

        janela = tk.Toplevel(self)
        janela.title("Filtrar Log Atual")
        janela.geometry("550x500")
        janela.minsize(500, 450)
        janela.transient(self)

        frame = ttk.Frame(janela, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Aba 1 - Filtro
        aba1 = ttk.Frame(notebook, padding=10)
        notebook.add(aba1, text="Filtrar")

        ttk.Label(aba1, text="Período:", font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        periodo = ttk.Combobox(aba1, values=[
            "Qualquer período", "Última hora", "Últimas 12 horas",
            "Últimas 24 horas", "Últimos 7 dias", "Últimos 30 dias"
        ], width=25, state="readonly")
        periodo.set("Qualquer período")
        periodo.grid(row=0, column=1, pady=5, padx=5, sticky=tk.W)

        ttk.Label(aba1, text="Nível do Evento:", font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky=tk.NW, pady=5)

        nivel_frame = ttk.Frame(aba1)
        nivel_frame.grid(row=1, column=1, sticky=tk.W, pady=5)

        niveis_vars = {}
        for i, (nivel, cor) in enumerate(NIVEIS_CORES.items()):
            var = tk.BooleanVar(value=True)
            niveis_vars[nivel] = var
            ttk.Checkbutton(nivel_frame, text=nivel, variable=var).grid(
                row=i // 2, column=i % 2, sticky=tk.W, padx=5)

        ttk.Label(aba1, text="IDs do Evento:", font=("Segoe UI", 9)).grid(
            row=2, column=0, sticky=tk.W, pady=5)
        ids_entry = ttk.Entry(aba1, width=40)
        ids_entry.grid(row=2, column=1, pady=5, padx=5)
        ttk.Label(aba1, text="Separados por vírgula. Ex: 4624,4625,1102",
                  font=("Segoe UI", 8)).grid(row=3, column=1, sticky=tk.W)

        ttk.Label(aba1, text="Fonte:", font=("Segoe UI", 9)).grid(
            row=4, column=0, sticky=tk.W, pady=5)
        fonte_entry = ttk.Entry(aba1, width=40)
        fonte_entry.grid(row=4, column=1, pady=5, padx=5)

        ttk.Label(aba1, text="Computador:", font=("Segoe UI", 9)).grid(
            row=5, column=0, sticky=tk.W, pady=5)
        comp_entry = ttk.Entry(aba1, width=40)
        comp_entry.grid(row=5, column=1, pady=5, padx=5)

        # Aba 2 - XML
        aba2 = ttk.Frame(notebook, padding=10)
        notebook.add(aba2, text="XML")

        ttk.Label(aba2, text="Consulta XML/XPath:", font=("Segoe UI", 9)).pack(anchor=tk.W)
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
    # DETALHES
    # =========================================================================
    def mostrar_detalhes_janela(self, e=None):
        sel = self.tree.selection()
        if not sel:
            return

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

        # Geral
        aba_geral = ttk.Frame(notebook, padding=10)
        notebook.add(aba_geral, text="Geral")

        text_widget = tk.Text(aba_geral, wrap=tk.WORD, font=("Segoe UI", 9))
        scrollbar = ttk.Scrollbar(aba_geral, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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

        # Detalhes
        aba_detalhes = ttk.Frame(notebook, padding=10)
        notebook.add(aba_detalhes, text="Detalhes")

        detalhes_paned = ttk.PanedWindow(aba_detalhes, orient=tk.VERTICAL)
        detalhes_paned.pack(fill=tk.BOTH, expand=True)

        tree_detalhes = ttk.Treeview(detalhes_paned, columns=("valor",), show="tree", height=10)
        tree_detalhes.heading("#0", text="Campo")
        tree_detalhes.heading("valor", text="Valor")
        tree_detalhes.column("#0", width=250)
        tree_detalhes.column("valor", width=400)

        sys_root = tree_detalhes.insert("", "end", text="System", open=True)
        tree_detalhes.insert(sys_root, "end", text="Provider", values=(f"Name: {ev.fonte}",))
        tree_detalhes.insert(sys_root, "end", text="EventID", values=(ev.id_evento,))
        tree_detalhes.insert(sys_root, "end", text="Version", values=(ev.version,))
        tree_detalhes.insert(sys_root, "end", text="Level", values=(ev.nivel,))
        tree_detalhes.insert(sys_root, "end", text="Task", values=(ev.task,))
        tree_detalhes.insert(sys_root, "end", text="Opcode", values=(ev.opcode,))
        tree_detalhes.insert(sys_root, "end", text="Keywords", values=(ev.keywords,))
        tree_detalhes.insert(sys_root, "end", text="TimeCreated", values=(ev.data_hora,))
        tree_detalhes.insert(sys_root, "end", text="EventRecordID", values=(ev.event_record_id,))
        tree_detalhes.insert(sys_root, "end", text="Channel", values=(ev.channel,))
        tree_detalhes.insert(sys_root, "end", text="Computer", values=(ev.computador,))
        tree_detalhes.insert(sys_root, "end", text="Security",
                             values=(f"UserID: {ev.user_id}" if ev.user_id else "",))

        if ev.event_data_list:
            ed_root = tree_detalhes.insert("", "end", text="EventData", open=True)
            for name, val in ev.event_data_list:
                if val:
                    tree_detalhes.insert(ed_root, "end", text=name or "(sem nome)", values=(val,))

        tree_detalhes.pack(fill=tk.BOTH, expand=True)
        detalhes_paned.add(tree_detalhes)

        # XML
        xml_frame = ttk.Frame(detalhes_paned)
        detalhes_paned.add(xml_frame)

        ttk.Label(xml_frame, text="XML do Evento:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)

        xml_text = tk.Text(xml_frame, wrap=tk.NONE, font=("Consolas", 8), height=8)
        xml_scroll_y = ttk.Scrollbar(xml_frame, orient="vertical", command=xml_text.yview)
        xml_scroll_x = ttk.Scrollbar(xml_frame, orient="horizontal", command=xml_text.xview)
        xml_text.configure(yscrollcommand=xml_scroll_y.set, xscrollcommand=xml_scroll_x.set)

        xml_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        xml_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        xml_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

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
        janela.geometry(f"+{max(0, x)}+{max(0, y)}")

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

        text_widget = tk.Text(aba_geral, wrap=tk.WORD, font=("Segoe UI", 9))
        scrollbar = ttk.Scrollbar(aba_geral, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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

            xml_text = tk.Text(aba_xml, wrap=tk.NONE, font=("Consolas", 9))
            xml_scroll = ttk.Scrollbar(aba_xml, orient="vertical", command=xml_text.yview)
            xml_text.configure(yscrollcommand=xml_scroll.set)

            xml_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            xml_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            xml_text.insert(tk.END, ev_dict['xml'])
            xml_text.config(state=tk.DISABLED)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="Fechar", command=janela.destroy).pack(side=tk.RIGHT)

        janela.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (janela.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (janela.winfo_height() // 2)
        janela.geometry(f"+{max(0, x)}+{max(0, y)}")

    # =========================================================================
    # PESQUISA
    # =========================================================================
    def pesquisar(self):
        termo = simpledialog.askstring("Localizar", "Localizar:")
        if not termo:
            return
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
        if not arquivo:
            return

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
        if not arquivo:
            return

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
        if not resposta:
            return

        try:
            nome_real = self.logs_disponiveis.get(self.log_atual, self.log_atual)
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
        self.progress_bar.reset()
        self.filtro_nivel.set("Todos")
        self.filtro_id.delete(0, tk.END)
        self.filtro_texto.delete(0, tk.END)
        self.filtro_ativo = False
        self.barra_status.config(text=f"Atualizando {self.log_atual}...")
        self.carregar_eventos_log(self.log_atual)

    def _formatar_numero(self, n):
        """Formata número com separadores."""
        try:
            return f"{int(n):,}".replace(",", ".")
        except:
            return str(n)

    def _fechar(self):
        """Fecha a aplicação."""
        self.destroy()

    def _sobre(self):
        """Exibe diálogo Sobre."""
        messagebox.showinfo(
            "Sobre o Visualizador de Eventos",
            "Visualizador de Eventos do Windows\n\n"
            "Réplica em Python/Tkinter\n"
            "Backend: wevtutil\n\n"
            "Versão 1.0"
        )


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    app = VisualizadorEventosFiel()
    app.mainloop()
