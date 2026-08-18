#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import quote
import webbrowser

# ---------------------------------------------------------------------------
# MOTORES DE BUSCA
# ---------------------------------------------------------------------------
MOTORES = {
    "Google":     "https://www.google.com/search?q={q}",
    "Bing":       "https://www.bing.com/search?q={q}",
    "DuckDuckGo": "https://duckduckgo.com/?q={q}",
    "Yandex":     "https://yandex.com/search/?text={q}",
    "Brave":      "https://search.brave.com/search?q={q}",
}

# Cores dos botões das abas (só os botões, fundo dos resultados fica preto)
CORES_BOTOES_ABAS = {
    "Todas":                        "#00aa00",
    "PDF":                          "#00cc44",
    "DOC/DOCX":                     "#00bbbb",
    "TXT":                          "#cc00cc",
    "CSV/Dados":                    "#cccc00",
    "Imagens":                      "#0099ff",
    "Áudio/Vídeo":                  "#ff9900",
    "Câmeras":                      "#ff3333",
    "Config/Logs/Backup":           "#44ff44",
    "Login/Erros/Vulnerabilidades": "#ff66ff",
    "Subdomínios/Externos":         "#6666ff",
    "Geral/Curingas":               "#9afad3",
}

# ---------------------------------------------------------------------------
# BASE DE DORKS
# ---------------------------------------------------------------------------
CATEGORIAS = {
        "PDF": [
        ("PDF", 'site:{site} filetype:pdf'),
        ("PDF - index of", 'site:{site} filetype:pdf intitle:"index of"'),
        ("PDF - confidencial", 'site:{site} filetype:pdf intext:confidencial'),
        ("PDF - senha/password", 'site:{site} filetype:pdf intext:senha OR intext:password'),
        ("PDF - download", 'site:{site} filetype:pdf inurl:download'),
        ("PDF - backup", 'site:{site} filetype:pdf inurl:backup'),
        ("PDF - cpf/rg", 'site:{site} filetype:pdf (intext:cpf OR intext:rg)'),
        ("Arquivo PDF", 'site:{site} ext:pdf'),
        ("PDF confidencial", 'filetype:pdf intitle:confidencial site:{site}'),
        ("Confidencial", 'intitle:confidencial filetype:pdf intext:"{site}"'),
        ("Financial report PDF", 'financial report site:{site} filetype:pdf'),
        ("PDF com nome", 'filetype:pdf "{site}"'),
        ("PDF com nome (2)", 'filetype:pdf "{site}"'),
        ("PDF - contrato", 'site:{site} filetype:pdf intext:contrato'),
        ("PDF - acordo", 'site:{site} filetype:pdf intext:acordo OR intext:agreement'),
        ("PDF - proposta", 'site:{site} filetype:pdf intext:proposta'),
        ("PDF - orçamento", 'site:{site} filetype:pdf intext:orçamento OR intext:orcamento'),
        ("PDF - fatura", 'site:{site} filetype:pdf intext:fatura OR intext:invoice'),
        ("PDF - nota fiscal", 'site:{site} filetype:pdf intext:"nota fiscal" OR intext:nfe'),
        ("PDF - recibo", 'site:{site} filetype:pdf intext:recibo'),
        ("PDF - extrato", 'site:{site} filetype:pdf intext:extrato'),
        ("PDF - folha de pagamento", 'site:{site} filetype:pdf intext:"folha de pagamento" OR intext:payroll'),
        ("PDF - holerite", 'site:{site} filetype:pdf intext:holerite'),
        ("PDF - currículo", 'site:{site} filetype:pdf intext:currículo OR intext:curriculo OR intext:resume'),
        ("PDF - relatório", 'site:{site} filetype:pdf intext:relatório OR intext:relatorio OR intext:report'),
        ("PDF - balance sheet", 'site:{site} filetype:pdf intext:"balance sheet" OR intext:balanço'),
        ("PDF - confidential", 'site:{site} filetype:pdf intext:confidential'),
        ("PDF - internal", 'site:{site} filetype:pdf intext:internal OR intext:interno'),
        ("PDF - restricted", 'site:{site} filetype:pdf intext:restricted OR intext:restrito'),
        ("PDF - private", 'site:{site} filetype:pdf intext:private OR intext:privado'),
        ("PDF - secret", 'site:{site} filetype:pdf intext:secret OR intext:segredo'),
        ("PDF - password protected", 'site:{site} filetype:pdf intext:"password protected" OR intext:"protegido por senha"'),
        ("PDF - cpf", 'site:{site} filetype:pdf intext:cpf'),
        ("PDF - cnpj", 'site:{site} filetype:pdf intext:cnpj'),
        ("PDF - rg", 'site:{site} filetype:pdf intext:rg'),
        ("PDF - cnh", 'site:{site} filetype:pdf intext:cnh'),
        ("PDF - email", 'site:{site} filetype:pdf intext:@ OR intext:email'),
        ("PDF - telefone", 'site:{site} filetype:pdf intext:telefone OR intext:phone OR intext:celular'),
        ("PDF - endereço", 'site:{site} filetype:pdf intext:endereço OR intext:endereco OR intext:address'),
        ("PDF - banco", 'site:{site} filetype:pdf intext:banco OR intext:bank'),
        ("PDF - conta", 'site:{site} filetype:pdf intext:conta OR intext:account'),
        ("PDF - agência", 'site:{site} filetype:pdf intext:agência OR intext:agencia'),
        ("PDF - pix", 'site:{site} filetype:pdf intext:pix'),
        ("PDF - cartão", 'site:{site} filetype:pdf intext:cartão OR intext:cartao OR intext:credit card'),
        ("PDF - manual", 'site:{site} filetype:pdf intext:manual'),
        ("PDF - guia", 'site:{site} filetype:pdf intext:guia OR intext:guide'),
        ("PDF - documentação", 'site:{site} filetype:pdf intext:documentação OR intext:documentacao OR intext:documentation'),
        ("PDF - política", 'site:{site} filetype:pdf intext:política OR intext:politica OR intext:policy'),
        ("PDF - termo de uso", 'site:{site} filetype:pdf intext:"termo de uso" OR intext:"terms of use"'),
        ("PDF - index of + confidencial", 'site:{site} intitle:"index of" filetype:pdf (confidencial OR confidential OR senha OR password)'),
        ("PDF - upload", 'site:{site} filetype:pdf inurl:upload'),
        ("PDF - docs", 'site:{site} filetype:pdf inurl:docs OR inurl:documentos'),
        ("PDF - files", 'site:{site} filetype:pdf inurl:files OR inurl:arquivos'),
        ("PDF - public", 'site:{site} filetype:pdf inurl:public'),
        ("PDF - shared", 'site:{site} filetype:pdf inurl:shared OR inurl:compartilhado'),
    ],

        "DOC/DOCX": [
        ("DOC", 'site:{site} filetype:doc'),
        ("DOCX", 'site:{site} filetype:docx'),
        ("DOC ou DOCX", 'site:{site} (filetype:doc OR filetype:docx)'),
        ("DOC - senha", 'site:{site} filetype:doc intext:senha'),
        ("DOCX - contrato", 'site:{site} filetype:docx intext:contrato'),
        ("DOC - backup", 'site:{site} filetype:doc inurl:backup'),
        ("DOCX - folha de pagamento", 'site:{site} filetype:docx intext:folha de pagamento'),
        ("DOC/DOCX - confidencial", 'site:{site} (filetype:doc OR filetype:docx) intitle:"confidencial"'),
        ("Arquivo DOCX", 'site:{site} ext:docx'),
        ("Documentos expostos publicamente", 'site:{site} ext:doc | ext:docx | ext:odt | ext:rtf | ext:sxw | ext:psw | ext:ppt | ext:pptx | ext:pps | ext:csv'),
        ("DOCX - senha", 'site:{site} filetype:docx intext:senha OR intext:password'),
        ("DOC - password", 'site:{site} filetype:doc intext:password'),
        ("DOC/DOCX - login", 'site:{site} (filetype:doc OR filetype:docx) intext:login'),
        ("DOC/DOCX - usuario", 'site:{site} (filetype:doc OR filetype:docx) intext:usuario OR intext:username'),
        ("DOCX - acordo", 'site:{site} filetype:docx intext:acordo OR intext:agreement'),
        ("DOCX - proposta", 'site:{site} filetype:docx intext:proposta'),
        ("DOCX - orçamento", 'site:{site} filetype:docx intext:orçamento OR intext:orcamento'),
        ("DOCX - fatura", 'site:{site} filetype:docx intext:fatura OR intext:invoice'),
        ("DOCX - nota fiscal", 'site:{site} filetype:docx intext:"nota fiscal"'),
        ("DOCX - recibo", 'site:{site} filetype:docx intext:recibo'),
        ("DOCX - extrato", 'site:{site} filetype:docx intext:extrato'),
        ("DOCX - holerite", 'site:{site} filetype:docx intext:holerite'),
        ("DOCX - currículo", 'site:{site} filetype:docx intext:currículo OR intext:curriculo OR intext:resume'),
        ("DOCX - relatório", 'site:{site} filetype:docx intext:relatório OR intext:relatorio OR intext:report'),
        ("DOC/DOCX - confidential", 'site:{site} (filetype:doc OR filetype:docx) intext:confidential'),
        ("DOC/DOCX - internal", 'site:{site} (filetype:doc OR filetype:docx) intext:internal OR intext:interno'),
        ("DOC/DOCX - restricted", 'site:{site} (filetype:doc OR filetype:docx) intext:restricted OR intext:restrito'),
        ("DOC/DOCX - private", 'site:{site} (filetype:doc OR filetype:docx) intext:private OR intext:privado'),
        ("DOC/DOCX - secret", 'site:{site} (filetype:doc OR filetype:docx) intext:secret OR intext:segredo'),
        ("DOC/DOCX - cpf", 'site:{site} (filetype:doc OR filetype:docx) intext:cpf'),
        ("DOC/DOCX - cnpj", 'site:{site} (filetype:doc OR filetype:docx) intext:cnpj'),
        ("DOC/DOCX - rg", 'site:{site} (filetype:doc OR filetype:docx) intext:rg'),
        ("DOC/DOCX - email", 'site:{site} (filetype:doc OR filetype:docx) intext:@ OR intext:email'),
        ("DOC/DOCX - telefone", 'site:{site} (filetype:doc OR filetype:docx) intext:telefone OR intext:phone'),
        ("DOC/DOCX - banco", 'site:{site} (filetype:doc OR filetype:docx) intext:banco OR intext:bank'),
        ("DOC/DOCX - conta", 'site:{site} (filetype:doc OR filetype:docx) intext:conta OR intext:account'),
        ("DOC/DOCX - pix", 'site:{site} (filetype:doc OR filetype:docx) intext:pix'),
        ("DOC/DOCX - cartão", 'site:{site} (filetype:doc OR filetype:docx) intext:cartão OR intext:cartao OR intext:"credit card"'),
        ("DOCX - manual", 'site:{site} filetype:docx intext:manual'),
        ("DOCX - documentação", 'site:{site} filetype:docx intext:documentação OR intext:documentacao'),
        ("DOCX - política", 'site:{site} filetype:docx intext:política OR intext:politica OR intext:policy'),
        ("DOCX - termo", 'site:{site} filetype:docx intext:termo OR intext:"terms of"'),
        ("DOC/DOCX - index of", 'site:{site} intitle:"index of" (filetype:doc OR filetype:docx)'),
        ("DOC/DOCX - index of + senha", 'site:{site} intitle:"index of" (filetype:doc OR filetype:docx) (senha OR password OR confidencial)'),
        ("DOC/DOCX - upload", 'site:{site} (filetype:doc OR filetype:docx) inurl:upload'),
        ("DOC/DOCX - docs", 'site:{site} (filetype:doc OR filetype:docx) inurl:docs OR inurl:documentos'),
        ("DOC/DOCX - files", 'site:{site} (filetype:doc OR filetype:docx) inurl:files OR inurl:arquivos'),
        ("DOC/DOCX - backup", 'site:{site} (filetype:doc OR filetype:docx) inurl:backup'),
        ("DOC/DOCX - shared", 'site:{site} (filetype:doc OR filetype:docx) inurl:shared OR inurl:compartilhado'),
        ("DOCX - ata", 'site:{site} filetype:docx intext:ata OR intext:meeting'),
        ("DOCX - parecer", 'site:{site} filetype:docx intext:parecer'),
        ("DOCX - laudo", 'site:{site} filetype:docx intext:laudo'),
        ("DOCX - procuração", 'site:{site} filetype:docx intext:procuração OR intext:procuracao'),
        ("DOCX - declaração", 'site:{site} filetype:docx intext:declaração OR intext:declaracao'),
    ],

        "TXT": [
        ("TXT", 'site:{site} filetype:txt'),
        ("TXT - senha", 'site:{site} filetype:txt intext:senha'),
        ("TXT - password", 'site:{site} filetype:txt intext:password'),
        ("TXT - usuario", 'site:{site} filetype:txt intext:usuario'),
        ("TXT - backup", 'site:{site} filetype:txt inurl:backup'),
        ("TXT - log", 'site:{site} filetype:txt inurl:log'),
        ("TXT - index of", 'site:{site} filetype:txt intitle:"index of"'),
        ("TXT - chave/token", 'site:{site} filetype:txt intext:chave OR intext:token'),
        ("TXT senha url", 'filetype:txt intext:senha url site:{site}'),
        ("TXT (2)", 'site:{site} filetype:txt'),
        ("TXT - login", 'site:{site} filetype:txt intext:login'),
        ("TXT - user/pass", 'site:{site} filetype:txt (intext:user OR intext:username) (intext:pass OR intext:password)'),
        ("TXT - config", 'site:{site} filetype:txt inurl:config'),
        ("TXT - credentials", 'site:{site} filetype:txt intext:credentials'),
        ("TXT - secret", 'site:{site} filetype:txt intext:secret'),
        ("TXT - api key", 'site:{site} filetype:txt intext:"api key" OR intext:apikey OR intext:"api_key"'),
        ("TXT - token", 'site:{site} filetype:txt intext:token'),
        ("TXT - private key", 'site:{site} filetype:txt intext:"private key" OR intext:privatekey'),
        ("TXT - database", 'site:{site} filetype:txt intext:database OR intext:db_'),
        ("TXT - connection string", 'site:{site} filetype:txt intext:"connection string" OR intext:connectionstring'),
        ("TXT - env", 'site:{site} filetype:txt inurl:env OR intext:.env'),
        ("TXT - robots", 'site:{site} filetype:txt inurl:robots'),
        ("TXT - readme", 'site:{site} filetype:txt inurl:readme'),
        ("TXT - notes", 'site:{site} filetype:txt inurl:notes OR intext:notes'),
        ("TXT - dump", 'site:{site} filetype:txt inurl:dump'),
        ("TXT - export", 'site:{site} filetype:txt inurl:export'),
        ("TXT - admin", 'site:{site} filetype:txt intext:admin'),
        ("TXT - root", 'site:{site} filetype:txt intext:root'),
        ("TXT - ftp", 'site:{site} filetype:txt intext:ftp'),
        ("TXT - ssh", 'site:{site} filetype:txt intext:ssh'),
        ("TXT - mysql", 'site:{site} filetype:txt intext:mysql'),
        ("TXT - postgres", 'site:{site} filetype:txt intext:postgres OR intext:postgresql'),
        ("TXT - email", 'site:{site} filetype:txt intext:@ OR intext:email'),
        ("TXT - cpf", 'site:{site} filetype:txt intext:cpf'),
        ("TXT - cnpj", 'site:{site} filetype:txt intext:cnpj'),
        ("TXT - telefone", 'site:{site} filetype:txt intext:telefone OR intext:phone'),
        ("TXT - index of + senha", 'site:{site} intitle:"index of" filetype:txt (senha OR password)'),
        ("TXT - confidential", 'site:{site} filetype:txt intext:confidential OR intext:confidencial'),
        ("TXT - internal", 'site:{site} filetype:txt intext:internal'),
        ("TXT - debug", 'site:{site} filetype:txt inurl:debug'),
        ("TXT - error log", 'site:{site} filetype:txt inurl:error OR inurl:errors'),
        ("TXT - access log", 'site:{site} filetype:txt inurl:access'),
    ],

        "CSV/Dados": [
        ("CSV", 'site:{site} filetype:csv'),
        ("CSV - cpf", 'site:{site} filetype:csv intext:cpf'),
        ("CSV - cnpj", 'site:{site} filetype:csv intext:cnpj'),
        ("CSV - email", 'site:{site} filetype:csv intext:email'),
        ("CSV - password", 'site:{site} filetype:csv intext:password'),
        ("CSV - export", 'site:{site} filetype:csv inurl:export'),
        ("CSV - backup", 'site:{site} filetype:csv inurl:backup'),
        ("CSV - index of", 'site:{site} filetype:csv intitle:"index of"'),
        ("CSV - download", 'site:{site} filetype:csv inurl:download'),
        ("Arquivos + dados sensiveis", 'site:{site} (filetype:csv OR filetype:xls OR filetype:pdf) (intext:cpf OR intext:cnpj OR intext:email)'),
        ("CSV - senha", 'site:{site} filetype:csv intext:senha'),
        ("CSV - user/pass", 'site:{site} filetype:csv (intext:user OR intext:usuario OR intext:username) (intext:pass OR intext:password OR intext:senha)'),
        ("CSV - login", 'site:{site} filetype:csv intext:login'),
        ("CSV - credentials", 'site:{site} filetype:csv intext:credentials OR intext:credenciais'),
        ("CSV - telefone", 'site:{site} filetype:csv intext:telefone OR intext:phone OR intext:celular'),
        ("CSV - nome", 'site:{site} filetype:csv intext:nome OR intext:name'),
        ("CSV - endereço", 'site:{site} filetype:csv intext:endereço OR intext:endereco OR intext:address'),
        ("CSV - rg", 'site:{site} filetype:csv intext:rg'),
        ("CSV - cnh", 'site:{site} filetype:csv intext:cnh'),
        ("CSV - data nascimento", 'site:{site} filetype:csv intext:"data de nascimento" OR intext:nascimento OR intext:birthday'),
        ("CSV - banco", 'site:{site} filetype:csv intext:banco OR intext:bank'),
        ("CSV - conta", 'site:{site} filetype:csv intext:conta OR intext:account'),
        ("CSV - agência", 'site:{site} filetype:csv intext:agência OR intext:agencia'),
        ("CSV - pix", 'site:{site} filetype:csv intext:pix'),
        ("CSV - cartão", 'site:{site} filetype:csv intext:cartão OR intext:cartao OR intext:"credit card" OR intext:card'),
        ("CSV - salário", 'site:{site} filetype:csv intext:salário OR intext:salario OR intext:salary'),
        ("CSV - folha", 'site:{site} filetype:csv intext:folha OR intext:payroll'),
        ("CSV - clientes", 'site:{site} filetype:csv intext:clientes OR intext:customers'),
        ("CSV - funcionários", 'site:{site} filetype:csv intext:funcionários OR intext:funcionarios OR intext:employees'),
        ("CSV - usuários", 'site:{site} filetype:csv intext:usuários OR intext:usuarios OR intext:users'),
        ("CSV - database", 'site:{site} filetype:csv intext:database OR intext:db_'),
        ("CSV - dump", 'site:{site} filetype:csv inurl:dump OR intext:dump'),
        ("CSV - export + sensível", 'site:{site} filetype:csv inurl:export (cpf OR cnpj OR email OR senha OR password)'),
        ("CSV - backup + sensível", 'site:{site} filetype:csv inurl:backup (cpf OR cnpj OR email OR senha)'),
        ("XLS", 'site:{site} filetype:xls'),
        ("XLSX", 'site:{site} filetype:xlsx'),
        ("XLS ou XLSX", 'site:{site} (filetype:xls OR filetype:xlsx)'),
        ("XLSX - cpf", 'site:{site} filetype:xlsx intext:cpf'),
        ("XLSX - cnpj", 'site:{site} filetype:xlsx intext:cnpj'),
        ("XLSX - email", 'site:{site} filetype:xlsx intext:email'),
        ("XLSX - senha", 'site:{site} filetype:xlsx intext:senha OR intext:password'),
        ("XLSX - clientes", 'site:{site} filetype:xlsx intext:clientes OR intext:customers'),
        ("XLSX - folha de pagamento", 'site:{site} filetype:xlsx intext:"folha de pagamento" OR intext:payroll'),
        ("XLSX - extrato", 'site:{site} filetype:xlsx intext:extrato'),
        ("XLS/XLSX - index of", 'site:{site} intitle:"index of" (filetype:xls OR filetype:xlsx)'),
        ("XLS/XLSX - backup", 'site:{site} (filetype:xls OR filetype:xlsx) inurl:backup'),
        ("XLS/XLSX - export", 'site:{site} (filetype:xls OR filetype:xlsx) inurl:export'),
        ("CSV/XLS - dados pessoais", 'site:{site} (filetype:csv OR filetype:xls OR filetype:xlsx) (intext:cpf OR intext:cnpj OR intext:rg OR intext:email)'),
        ("CSV - lista", 'site:{site} filetype:csv inurl:lista OR inurl:list'),
        ("CSV - mailing", 'site:{site} filetype:csv intext:mailing OR inurl:mailing'),
        ("CSV - contatos", 'site:{site} filetype:csv intext:contatos OR intext:contacts'),
    ],

    "Imagens": [
        ("JPG", 'site:{site} filetype:jpg'),
        ("JPG ou JPEG", 'site:{site} (filetype:jpg OR filetype:jpeg)'),
        ("JPG - upload", 'site:{site} filetype:jpg inurl:upload'),
        ("JPG - galeria", 'site:{site} filetype:jpg inurl:galeria'),
        ("JPG - docs/documentos", 'site:{site} filetype:jpg inurl:docs OR inurl:documentos'),
        ("JPG - upload (extra)", 'site:{site} inurl:upload filetype:jpg'),
        ("PNG", 'site:{site} filetype:png'),
        ("PNG - logo", 'site:{site} filetype:png inurl:logo'),
        ("PNG - upload", 'site:{site} filetype:png inurl:upload'),
        ("PNG - index of /imagens", 'site:{site} filetype:png intitle:"index of" /imagens'),
        ("PNG - imagesize", 'site:{site} filetype:png imagesize:1000x1000'),
        ("GIF", 'site:{site} filetype:gif'),
        ("GIF - banner", 'site:{site} filetype:gif inurl:banner'),
        ("WEBP", 'site:{site} filetype:webp'),
        ("WEBP - img", 'site:{site} filetype:webp inurl:img'),
    ],

    "Áudio/Vídeo": [
        ("MP4", 'site:{site} filetype:mp4'),
        ("MP4 - video", 'site:{site} filetype:mp4 inurl:video'),
        ("MP4 - uploads", 'site:{site} filetype:mp4 inurl:uploads'),
        ("MP4 - media", 'site:{site} filetype:mp4 inurl:media'),
        ("MP4 - index of", 'site:{site} filetype:mp4 intitle:"index of"'),
        ("MP3", 'site:{site} filetype:mp3'),
        ("MP3 - audio", 'site:{site} filetype:mp3 inurl:audio'),
        ("MP3 - podcast", 'site:{site} filetype:mp3 inurl:podcast'),
        ("MP3 - index of", 'site:{site} filetype:mp3 intitle:"index of"'),
        ("WAV", 'site:{site} filetype:wav'),
        ("WAV - audio", 'site:{site} filetype:wav inurl:audio'),
        ("WAV - index of /audio", 'site:{site} filetype:wav intitle:"index of" /audio'),
        ("MOV", 'site:{site} filetype:mov'),
        ("MOV - video", 'site:{site} filetype:mov inurl:video'),
        ("MOV - storage", 'site:{site} filetype:mov inurl:storage'),
        ("Midia - index of", 'site:{site} intitle:"index of" (mp4 OR mp3 OR wav OR mov)'),
    ],

        "Câmeras": [
        ("Câmera - currenttime/top", 'inurl:currenttime inurl:top.htm'),
        ("Câmera - view.shtml", 'inurl:/view.shtml'),
        ("Câmera - lvappl", 'inurl:"lvappl.htm"'),
        ("Câmera - CgiStart", 'inurl:"CgiStart?page="'),
        ("Câmera - AXIS Live View", 'intitle:"Live View/ — AXIS"'),
        ("Câmera - iview", 'inurl:iview/view.shtml'),
        ("Câmera - ViewerFrame", 'inurl:ViewerFrame?M0de='),
        ("Câmera - ViewerFrame Refresh", 'inurl:ViewerFrame?M0de=Refresh'),
        ("Câmera - AXIS CGI", 'inurl:axis-cgi/jpg'),
        ("Câmera - guestimage", 'inurl:guestimage.html'),
        ("WEBCAM 7", '{site} intitle:"WEBCAM 7" -inurl:/admin.html'),
        ("Câmera - AXIS", 'inurl:axis-cgi'),
        ("Câmera - AXIS live", 'intitle:"Live View" inurl:axis'),
        ("Câmera - AXIS Camera", 'intitle:"AXIS" inurl:view'),
        ("Câmera - Vivotek", 'intitle:"Network Camera" inurl:vivotek'),
        ("Câmera - Panasonic", 'inurl:ViewerFrame?Mode='),
        ("Câmera - Sony", 'intitle:"Sony Network Camera"'),
        ("Câmera - Mobotix", 'inurl:/control/userimage.html'),
        ("Câmera - Foscam", 'intitle:"IPCam Client" OR inurl:foscam'),
        ("Câmera - D-Link", 'intitle:"D-Link" inurl:view'),
        ("Câmera - Hikvision", 'inurl:/doc/page/login.asp OR intitle:"Hikvision"'),
        ("Câmera - Hikvision login", 'inurl:"login.asp" intitle:"Hikvision"'),
        ("Câmera - Dahua", 'intitle:"Dahua" inurl:login'),
        ("Câmera - Dahua Web", 'inurl:/doc/page/login.asp intitle:Dahua'),
        ("Câmera - webcamXP", 'intitle:"webcamXP"'),
        ("Câmera - WebcamXP 5", 'intitle:"WebcamXP 5"'),
        ("Câmera - yawcam", 'intitle:"yawcam"'),
        ("Câmera - Blue Iris", 'intitle:"Blue Iris"'),
        ("Câmera - Live View", 'intitle:"Live View"'),
        ("Câmera - Network Camera", 'intitle:"Network Camera"'),
        ("Câmera - IP Camera", 'intitle:"IP Camera"'),
        ("Câmera - Surveillance", 'intitle:"Surveillance" inurl:view'),
        ("Câmera - Camera Viewer", 'intitle:"Camera Viewer"'),
        ("Câmera - webcam", 'inurl:webcam'),
        ("Câmera - cam", 'inurl:/cam/ OR inurl:camera'),
        ("Câmera - stream", 'inurl:stream inurl:camera OR inurl:stream inurl:cam'),
        ("Câmera - mjpg", 'inurl:mjpg OR inurl:mjpeg'),
        ("Câmera - snapshot", 'inurl:snapshot'),
        ("Câmera - image.jpg", 'inurl:image.jpg inurl:camera OR inurl:cam'),
        ("Câmera - view.html", 'inurl:view.html inurl:cam OR inurl:view.htm'),
        ("Câmera - live.html", 'inurl:live.html OR inurl:live.htm'),
        ("Câmera - guest", 'inurl:guest inurl:camera OR inurl:guest inurl:cam'),
        ("Câmera - public", 'inurl:public inurl:camera'),
        ("Câmera - index of cameras", 'intitle:"index of" cameras OR intitle:"index of" camera'),
        ("Câmera - index of cam", 'intitle:"index of" /cam OR intitle:"index of" /camera'),
        ("Câmera - robot cam", 'inurl:robot OR inurl:robots inurl:cam'),
        ("Câmera - multi camera", 'intitle:"Multi Camera" OR intitle:"Multi-Camera"'),
        ("Câmera - NVR", 'intitle:NVR inurl:login'),
        ("Câmera - DVR", 'intitle:DVR inurl:login OR intitle:"Digital Video Recorder"'),
        ("Câmera - Xiongmai", 'intitle:"Xiongmai" OR inurl:xiongmai'),
        ("Câmera - Reolink", 'intitle:"Reolink"'),
        ("Câmera - TP-Link", 'intitle:"TP-Link" inurl:camera'),
        ("Câmera - Wyze", 'intitle:"Wyze"'),
        ("Câmera - site específico", 'site:{site} (inurl:camera OR inurl:cam OR inurl:webcam OR intitle:camera)'),
    ],

        "Config/Logs/Backup": [
        ("Arquivos de configuração expostos", 'site:{site} ext:xml | ext:conf | ext:cnf | ext:reg | ext:inf | ext:rdp | ext:cfg | ext:txt | ext:ora | ext:ini | ext:env'),
        ("Arquivos de banco de dados expostos", 'site:{site} ext:sql | ext:dbf | ext:mdb'),
        ("Arquivos de log expostos", 'site:{site} ext:log'),
        ("Arquivos de backup e antigos", 'site:{site} ext:bkf | ext:bkp | ext:bak | ext:old | ext:backup'),
        ("Backups antigos", 'site:{site} (filetype:bak OR filetype:old OR filetype:tmp)'),
        ("LOG (2)", 'site:{site} filetype:log'),
        ("index of /logs", 'site:{site} index of /logs'),
        ("XML (2)", 'site:{site} filetype:xml'),
        ("Arquivo XML", 'site:{site} ext:xml'),
        ("ENV", 'filetype:env {site}'),
        ("SQL", '{site} filetype:sql'),
        (".git - index of", '{site} intitle:index of .git'),
        ("site .git", 'site:{site} intitle:index of .git'),
        ("git config", 'site:{site} intitle:"index of" "/.git/config"'),
        ("ENV - .env", 'site:{site} filetype:env OR inurl:.env'),
        ("ENV - exposed", 'site:{site} inurl:.env "DB_PASSWORD" OR inurl:.env "APP_KEY"'),
        ("Config - wp-config", 'site:{site} inurl:wp-config.php'),
        ("Config - config.php", 'site:{site} inurl:config.php'),
        ("Config - configuration.php", 'site:{site} inurl:configuration.php'),
        ("Config - settings.php", 'site:{site} inurl:settings.php'),
        ("Config - database.php", 'site:{site} inurl:database.php'),
        ("Config - local.xml", 'site:{site} inurl:local.xml'),
        ("Config - web.config", 'site:{site} inurl:web.config'),
        ("Config - applicationHost.config", 'site:{site} inurl:applicationHost.config'),
        ("Config - php.ini", 'site:{site} inurl:php.ini'),
        ("Config - .htaccess", 'site:{site} inurl:.htaccess'),
        ("Config - robots.txt", 'site:{site} inurl:robots.txt'),
        ("Config - crossdomain.xml", 'site:{site} inurl:crossdomain.xml'),
        ("Config - clientaccesspolicy.xml", 'site:{site} inurl:clientaccesspolicy.xml'),
        ("Log - access.log", 'site:{site} inurl:access.log OR filetype:log inurl:access'),
        ("Log - error.log", 'site:{site} inurl:error.log OR filetype:log inurl:error'),
        ("Log - debug.log", 'site:{site} inurl:debug.log'),
        ("Log - laravel", 'site:{site} inurl:storage/logs OR inurl:laravel.log'),
        ("Log - apache", 'site:{site} inurl:apache filetype:log'),
        ("Log - nginx", 'site:{site} inurl:nginx filetype:log'),
        ("Backup - .bak", 'site:{site} filetype:bak'),
        ("Backup - .old", 'site:{site} filetype:old'),
        ("Backup - .backup", 'site:{site} filetype:backup'),
        ("Backup - .sql.bak", 'site:{site} filetype:sql.bak OR inurl:.sql.bak'),
        ("Backup - .zip backup", 'site:{site} filetype:zip inurl:backup'),
        ("Backup - .tar.gz", 'site:{site} filetype:gz OR filetype:tar inurl:backup'),
        ("Backup - database backup", 'site:{site} (filetype:sql OR filetype:bak) inurl:backup'),
        ("Backup - full backup", 'site:{site} inurl:backup filetype:zip OR inurl:backup filetype:tar'),
        ("SQL - dump", 'site:{site} filetype:sql inurl:dump OR filetype:sql intext:dump'),
        ("SQL - database", 'site:{site} filetype:sql intext:database OR intext:CREATE TABLE'),
        ("SQL - password", 'site:{site} filetype:sql intext:password OR intext:senha'),
        ("Git - HEAD", 'site:{site} inurl:.git/HEAD'),
        ("Git - config", 'site:{site} inurl:.git/config'),
        ("Git - index", 'site:{site} inurl:.git/index'),
        ("Git - objects", 'site:{site} intitle:"index of" .git/objects'),
        ("SVN - entries", 'site:{site} inurl:.svn/entries'),
        ("SVN - wc.db", 'site:{site} inurl:.svn/wc.db'),
        ("DS_Store", 'site:{site} inurl:.DS_Store'),
        ("Thumbs.db", 'site:{site} inurl:Thumbs.db'),
        ("Backup - index of backup", 'site:{site} intitle:"index of" backup'),
        ("Backup - index of bak", 'site:{site} intitle:"index of" bak OR intitle:"index of" .bak'),
        ("Logs - index of logs", 'site:{site} intitle:"index of" logs OR intitle:"index of" /log'),        
        ("Config - index of config", 'site:{site} intitle:"index of" config OR intitle:"index of" conf'),
        ("Credentials in config", 'site:{site} (filetype:env OR filetype:ini OR filetype:conf OR filetype:cfg) (intext:password OR intext:senha OR intext:pwd)'),
        ("AWS keys", 'site:{site} filetype:env intext:AWS_ACCESS_KEY OR intext:AWS_SECRET'),
        ("API keys in config", 'site:{site} (filetype:env OR filetype:json OR filetype:yml) (intext:api_key OR intext:apikey OR intext:secret_key)'),
    ],

        "Login/Erros/Vulnerabilidades": [
        ("Páginas de login", 'site:{site} inurl:login | inurl:signin | intitle:Login | intitle:"sign in" | inurl:auth'),
        ("Login -Painel", 'site:{site} intitle:Login -Painel'),
        ("Páginas de cadastro", 'site:{site} inurl:signup | inurl:register | intitle:Signup'),
        ("Erros SQL", 'site:{site} intext:"sql syntax near" | intext:"syntax error has occurred" | intext:"incorrect syntax near" | intext:"unexpected end of SQL command" | intext:"Warning: mysql_connect()" | intext:"Warning: mysql_query()" | intext:"Warning: pg_connect()"'),
        ("Erros/advertências PHP", 'site:{site} "PHP Parse error" | "PHP Warning" | "PHP Error"'),
        ("phpinfo()", 'site:{site} ext:php intitle:phpinfo "published by the PHP Group"'),
        ("Vulnerabilidades de listagem de diretórios", 'site:{site} intitle:index.of'),
        ("Diretorios abertos", 'site:{site} intitle:"index of" (pdf OR csv OR xls OR zip)'),
        ("index of - senha", 'intitle:"index of" intext:{site}'),
        ("Achar inurl e index.php", '"{site}" + inurl=index.php?id=1'),
        ("contact-form-7 (1)", 'site:{site}/wp-content/plugins/contact-form-7'),
        ("contact-form-7 (2)", 'site:{site} /wp-content/plugins/contact-form-7'),
        ("Login - admin", 'site:{site} inurl:admin OR intitle:admin inurl:login'),
        ("Login - administrador", 'site:{site} inurl:administrador OR intitle:administrador'),
        ("Login - painel", 'site:{site} inurl:painel OR intitle:painel'),
        ("Login - dashboard", 'site:{site} inurl:dashboard OR intitle:dashboard'),
        ("Login - wp-login", 'site:{site} inurl:wp-login.php'),
        ("Login - wp-admin", 'site:{site} inurl:wp-admin'),
        ("Login - administrator", 'site:{site} inurl:administrator'),
        ("Login - cpanel", 'site:{site} inurl:cpanel OR intitle:cpanel'),
        ("Login - webmail", 'site:{site} inurl:webmail OR intitle:webmail'),
        ("Login - phpmyadmin", 'site:{site} inurl:phpmyadmin OR intitle:phpmyadmin'),
        ("Login - adminer", 'site:{site} inurl:adminer.php OR intitle:Adminer'),
        ("Login - roundcube", 'site:{site} inurl:roundcube OR intitle:Roundcube'),
        ("Login - portal", 'site:{site} inurl:portal inurl:login OR intitle:portal inurl:login'),
        ("Login - cliente", 'site:{site} inurl:cliente inurl:login OR intitle:"área do cliente"'),
        ("Login - aluno", 'site:{site} inurl:aluno inurl:login OR intitle:aluno'),
        ("Login - professor", 'site:{site} inurl:professor inurl:login'),
        ("Erro - SQL Injection", 'site:{site} intext:"You have an error in your SQL syntax"'),
        ("Erro - mysql_fetch", 'site:{site} intext:"mysql_fetch_array()" OR intext:"mysql_fetch_assoc()"'),
        ("Erro - Warning mysql", 'site:{site} intext:"Warning: mysql_"'),
        ("Erro - mysqli", 'site:{site} intext:"mysqli_" OR intext:"Warning: mysqli_"'),
        ("Erro - PostgreSQL", 'site:{site} intext:"pg_query()" OR intext:"Warning: pg_"'),
        ("Erro - ODBC", 'site:{site} intext:"ODBC SQL Server Driver" OR intext:"Microsoft OLE DB"'),
        ("Erro - Oracle", 'site:{site} intext:"ORA-" OR intext:"Oracle error"'),
        ("Erro - PHP Notice", 'site:{site} "PHP Notice" OR "Notice: Undefined"'),
        ("Erro - Fatal error", 'site:{site} "Fatal error:" OR "PHP Fatal error"'),
        ("Erro - Warning", 'site:{site} "Warning:" site:{site} ext:php'),
        ("phpinfo - full", 'site:{site} intitle:phpinfo OR inurl:phpinfo.php'),
        ("Test pages", 'site:{site} inurl:test OR inurl:teste OR intitle:test'),
        ("Debug mode", 'site:{site} intext:"debug" inurl:index OR intext:"DEBUG"'),
        ("Stack trace", 'site:{site} intext:"stack trace" OR intext:"Stack trace"'),
        ("Exception", 'site:{site} intext:"Exception in" OR intext:"Uncaught Exception"'),
        ("Directory listing", 'site:{site} intitle:"Index of /" OR intitle:"Directory Listing"'),
        ("Index of admin", 'site:{site} intitle:"index of" admin'),
        ("Index of backup", 'site:{site} intitle:"index of" backup'),
        ("Index of config", 'site:{site} intitle:"index of" config'),
        ("Index of private", 'site:{site} intitle:"index of" private OR intitle:"index of" secret'),
        ("IDOR potencial", 'site:{site} inurl:id= OR inurl:user_id= OR inurl:account='),
        ("LFI potencial", 'site:{site} inurl:page= OR inurl:file= OR inurl:include= OR inurl:path='),
        ("Open redirect", 'site:{site} inurl:redirect= OR inurl:url= OR inurl:next= OR inurl:return='),
        ("XSS refletido", 'site:{site} inurl:q= OR inurl:s= OR inurl:search= OR inurl:query='),
        ("WordPress plugins", 'site:{site} inurl:wp-content/plugins'),
        ("WordPress themes", 'site:{site} inurl:wp-content/themes'),
        ("WordPress uploads", 'site:{site} inurl:wp-content/uploads'),
        ("Joomla", 'site:{site} inurl:administrator OR inurl:components/com_'),
        ("Drupal", 'site:{site} inurl:user/login OR inurl:sites/default/files'),
    ],

        "Subdomínios/Externos": [
        ("Encontrar Subdomínios", 'site:*.{site}'),
        ("Encontrar Sub-Subdomínios", 'site:*.*.{site}'),
        ("Pesquisar no Wayback Machine", 'https://web.archive.org/web/*/{site}/*'),
        ("Mostrar apenas IPs (abre várias abas)", '({site}) (site:*.*.29.* | site:*.*.28.* | site:*.*.27.* | site:*.*.26.* | site:*.*.25.* | site:*.*.24.* | site:*.*.23.* | site:*.*.22.* | site:*.*.21.* | site:*.*.20.* | site:*.*.19.* | site:*.*.18.* | site:*.*.17.* | site:*.*.16.* | site:*.*.15.* | site:*.*.14.* | site:*.*.13.* | site:*.*.12.* | site:*.*.11.* | site:*.*.10.* | site:*.*.9.* | site:*.*.8.* | site:*.*.7.* | site:*.*.6.* | site:*.*.5.* | site:*.*.4.* | site:*.*.3.* | site:*.*.2.* | site:*.*.1.* | site:*.*.0.*)'),
        ("Pesquisar em pastebin.com / sites de postagem", 'site:pastebin.com | site:paste2.org | site:pastehtml.com | site:slexy.org | site:snipplr.com | site:snipt.net | site:textsnip.com | site:bitpaste.app | site:justpaste.it | site:heypasteit.com | site:hastebin.com | site:dpaste.org | site:dpaste.com | site:codepad.org | site:jsitor.com | site:codepen.io | site:jsfiddle.net | site:dotnetfiddle.net | site:phpfiddle.org | site:ide.geeksforgeeks.org | site:repl.it | site:ideone.com | site:paste.debian.net | site:paste.org | site:paste.org.ru | site:codebeautify.org | site:codeshare.io | site:trello.com {site}'),
        ("Pesquisar em github.com e gitlab.com", 'site:github.com | site:gitlab.com {site}'),
        ("Pesquisar no stackoverflow.com", 'site:stackoverflow.com {site}'),
        ("Google Docs - documentos vazados", 'site:docs.{site}/document/d'),
        ("Google Docs - apresentações vazadas", 'site:docs.{site}/presentation/d'),
        ("Google Docs - desenhos vazados", 'site:docs.{site}/drawings/d'),
        ("Google Docs - qualquer arquivo (img/vídeo/zip/pdf)", 'site:docs.{site}/file/d'),
        ("Google Drive - pastas expostas", 'site:docs.{site}/folder/d'),
        ("Google Docs - itens secretos", 'site:docs.{site}/open intext:secreto'),
        ("Google Drive", 'site:drive.google.com {site}'),
        ("Google Drive (2)", 'site:drive.google.com "{site}"'),        
        ("Servidores Scribd", 'servidores site:scribd.com AND:{site}'),
        ("Jusbrasil", 'site:jusbrasil.com.br "{site}"'),
        ("Instagram (intext)", 'site:instagram.com intext:"{site}"'),
        ("Instagram", 'site:instagram.com intext:{site}'),
        ("Subdomínios - mail", 'site:mail.{site} OR site:webmail.{site}'),
        ("Subdomínios - ftp", 'site:ftp.{site}'),
        ("Subdomínios - cpanel", 'site:cpanel.{site} OR site:cpanel.{site}:2083'),
        ("Subdomínios - admin", 'site:admin.{site} OR site:administrador.{site}'),
        ("Subdomínios - dev", 'site:dev.{site} OR site:development.{site}'),
        ("Subdomínios - test", 'site:test.{site} OR site:teste.{site} OR site:staging.{site}'),
        ("Subdomínios - api", 'site:api.{site}'),
        ("Subdomínios - portal", 'site:portal.{site}'),
        ("Subdomínios - blog", 'site:blog.{site}'),
        ("Subdomínios - shop", 'site:shop.{site} OR site:loja.{site}'),
        ("Wayback - só snapshots", 'https://web.archive.org/web/*/{site}*'),
        ("Wayback - CDX API", 'https://web.archive.org/cdx/search/cdx?url={site}&output=json&fl=original,timestamp'),
        ("GitHub - código", 'site:github.com "{site}"'),
        ("GitHub - senha/password", 'site:github.com "{site}" (password OR senha OR secret OR api_key)'),
        ("GitLab - código", 'site:gitlab.com "{site}"'),
        ("Bitbucket", 'site:bitbucket.org "{site}"'),
        ("Pastebin - senha", 'site:pastebin.com "{site}" (password OR senha OR credentials)'),
        ("Pastebin - email", 'site:pastebin.com "{site}" email'),
        ("Pastebin - database", 'site:pastebin.com "{site}" (database OR dump OR sql)'),
        ("Trello", 'site:trello.com "{site}"'),
        ("Notion", 'site:notion.so "{site}" OR site:notion.site "{site}"'),
        ("Slack", 'site:slack.com "{site}"'),
        ("Discord", 'site:discord.com "{site}" OR site:discord.gg "{site}"'),
        ("LinkedIn", 'site:linkedin.com "{site}"'),
        ("Twitter / X", 'site:twitter.com "{site}" OR site:x.com "{site}"'),
        ("Facebook", 'site:facebook.com "{site}"'),
        ("YouTube", 'site:youtube.com "{site}"'),
        ("Reddit", 'site:reddit.com "{site}"'),
        ("Medium", 'site:medium.com "{site}"'),
        ("Scribd - documentos", 'site:scribd.com "{site}"'),
        ("SlideShare", 'site:slideshare.net "{site}"'),
        ("Issuu", 'site:issuu.com "{site}"'),
        ("Dropbox", 'site:dropbox.com "{site}" OR site:dropbox.com/s/ "{site}"'),
        ("OneDrive", 'site:onedrive.live.com "{site}" OR site:1drv.ms "{site}"'),
        ("Google Sites", 'site:sites.google.com "{site}"'),
        ("Google Sheets", 'site:docs.google.com/spreadsheets "{site}"'),
        ("Google Forms", 'site:docs.google.com/forms "{site}"'),
        ("Public WWW", 'site:publicwww.com "{site}"'),
        ("Censys", 'site:search.censys.io "{site}"'),
        ("Shodan", 'site:www.shodan.io "{site}"'),
        ("VirusTotal", 'site:virustotal.com "{site}"'),
        ("URLScan", 'site:urlscan.io "{site}"'),
        ("SecurityTrails", 'site:securitytrails.com "{site}"'),
        ("ViewDNS", 'site:viewdns.info "{site}"'),
        ("CRT.sh (certificados)", 'site:crt.sh "{site}"'),
        ("Certificados SSL", 'site:crt.sh q=%.{site}'),
    ],

        "Geral/Curingas": [
        ("Todos os documentos", 'site:{site} (filetype:pdf OR filetype:doc OR filetype:docx OR filetype:txt OR filetype:csv)'),
        ("PDF/XLSX/DOCX/TXT", '\'{site}\' filetype:pdf OR filetype:xlsx OR filetype:docx OR filetype:txt'),
        ("Achar intext", 'intext:{site}'),
        ("Achar inurl", 'inurl:{site}'),
        ("Nome de pessoa", 'intext:"{site}"'),
        ("Nome do IP", 'IP:{site}'),
        ("intitle nome", 'intitle:"{site}"'),
        ("inurl email", 'inurl: {site}'),
        ("Achar email", '"{site}"'),
        ("intext nome", 'intext:"{site}"'),
        ("Achar link", 'link:{site}'),
        ("Extrair dados", '"{site}"'),
        ("robots.txt", '{site} robots.txt'),
        ("intext:1 (exemplo genérico)", 'intext:1'),
        ("allintext", 'allintext:"{site}"'),
        ("allinurl", 'allinurl:{site}'),
        ("allintitle", 'allintitle:"{site}"'),
        ("allinanchor", 'allinanchor:"{site}"'),
        ("inanchor", 'inanchor:"{site}"'),
        ("related", 'related:{site}'),
        ("info", 'info:{site}'),
        ("Credit card (pastebin)", 'site:pastebin.com {site} credit card'),
        ("cache", 'cache:{site}'),
        ("cache + senha", 'cache:{site} senha OR password OR secret'),
        ("define", 'define:{site}'),
        ("AROUND operador", '"{site}" AROUND(5) (senha OR password OR secret OR leak)'),
        ("AROUND email", '"{site}" AROUND(3) (@ OR email OR contato)'),
        ("site -www", 'site:{site} -www'),
        ("site sem www e blog", 'site:{site} -www -blog -shop'),
        ("OR amplo", '"{site}" OR "{site}"'),
        ("aspas exatas", '"{site}"'),
        ("wildcard *", '"{site}" * (password OR senha OR token)'),
        ("minus ruído", 'site:{site} -inurl:blog -inurl:news -inurl:wp-content'),
        ("ZIP", 'site:{site} filetype:zip'),
        ("RAR", 'site:{site} filetype:rar'),
        ("7Z", 'site:{site} filetype:7z'),
        ("TAR / GZ", 'site:{site} (filetype:tar OR filetype:gz OR filetype:tgz)'),
        ("ISO / IMG", 'site:{site} (filetype:iso OR filetype:img)'),
        ("ZIP/RAR/7Z/TAR", 'site:{site} (filetype:zip OR filetype:rar OR filetype:7z OR filetype:tar OR filetype:gz)'),
        ("ZIP - download", 'site:{site} filetype:zip inurl:download'),
        ("ZIP - files", 'site:{site} filetype:zip inurl:files OR inurl:arquivos'),
        ("ZIP - export", 'site:{site} filetype:zip inurl:export'),
        ("ZIP - dump", 'site:{site} filetype:zip inurl:dump'),
        ("ZIP - private", 'site:{site} filetype:zip (inurl:private OR inurl:interno OR inurl:secret)'),
        ("ZIP - index of", 'site:{site} intitle:"index of" (zip OR rar OR 7z OR tar)'),
        ("EXE / MSI", 'site:{site} (filetype:exe OR filetype:msi OR filetype:dmg)'),
        ("APK", 'site:{site} filetype:apk'),
        ("IPA", 'site:{site} filetype:ipa'),
        ("DEB / RPM", 'site:{site} (filetype:deb OR filetype:rpm)'),
        ("PPT", 'site:{site} filetype:ppt'),
        ("PPTX", 'site:{site} filetype:pptx'),
        ("PPT/PPTX", 'site:{site} (filetype:ppt OR filetype:pptx OR filetype:pps OR filetype:ppsx)'),
        ("PPTX - confidencial", 'site:{site} (filetype:ppt OR filetype:pptx) (confidencial OR confidential OR internal)'),
        ("ODT / ODS / ODP", 'site:{site} (filetype:odt OR filetype:ods OR filetype:odp)'),
        ("RTF", 'site:{site} filetype:rtf'),
        ("PAGES / NUMBERS / KEY", 'site:{site} (filetype:pages OR filetype:numbers OR filetype:key)'),
        ("ONE (OneNote)", 'site:{site} filetype:one'),
        ("PUB", 'site:{site} filetype:pub'),
        ("VSD / VSDX (Visio)", 'site:{site} (filetype:vsd OR filetype:vsdx)'),
        ("PHP", 'site:{site} filetype:php'),
        ("ASP / ASPX", 'site:{site} (filetype:asp OR filetype:aspx)'),
        ("JSP", 'site:{site} filetype:jsp'),
        ("PY", 'site:{site} filetype:py'),
        ("RB", 'site:{site} filetype:rb'),
        ("JS", 'site:{site} filetype:js'),
        ("CSS", 'site:{site} filetype:css'),
        ("JAVA", 'site:{site} filetype:java'),
        ("C / CPP / H", 'site:{site} (filetype:c OR filetype:cpp OR filetype:h)'),
        ("GO / RS", 'site:{site} (filetype:go OR filetype:rs)'),
        ("SH / BAT / PS1", 'site:{site} (filetype:sh OR filetype:bat OR filetype:ps1 OR filetype:cmd)'),
        ("PL / CGI", 'site:{site} (filetype:pl OR inurl:cgi-bin)'),
        ("Source maps", 'site:{site} filetype:map OR inurl:.js.map'),
        ("Minified JS", 'site:{site} inurl:.min.js'),
        ("JS - api key", 'site:{site} filetype:js (apikey OR api_key OR secret OR token OR password)'),
        ("JS - endpoint", 'site:{site} filetype:js (intext:"/api/" OR intext:endpoint OR intext:baseURL)'),
        ("HTML comentários", 'site:{site} filetype:html (intext:"<!--" AND (password OR todo OR fixme OR secret))'),
        ("TODO / FIXME", 'site:{site} (intext:TODO OR intext:FIXME OR intext:HACK OR intext:XXX) (password OR key OR token)'),
        ("JSON", 'site:{site} filetype:json'),
        ("JSON - swagger", 'site:{site} (filetype:json OR inurl:swagger) (swagger OR openapi)'),
        ("YAML / YML", 'site:{site} (filetype:yml OR filetype:yaml)'),
        ("XML - wsdl", 'site:{site} (filetype:wsdl OR inurl:wsdl OR filetype:xml inurl:soap)'),
        ("Properties", 'site:{site} filetype:properties'),
        ("TOML", 'site:{site} filetype:toml'),
        ("INI extra", 'site:{site} filetype:ini'),
        ("package.json", 'site:{site} inurl:package.json'),
        ("composer.json", 'site:{site} inurl:composer.json'),
        ("requirements.txt", 'site:{site} inurl:requirements.txt'),
        ("Gemfile", 'site:{site} inurl:Gemfile'),
        ("pom.xml", 'site:{site} inurl:pom.xml'),
        ("build.gradle", 'site:{site} inurl:build.gradle'),
        ("Dockerfile", 'site:{site} inurl:Dockerfile OR filetype:dockerfile'),
        ("docker-compose", 'site:{site} inurl:docker-compose.yml OR inurl:docker-compose.yaml'),
        ("Kubernetes", 'site:{site} (inurl:k8s OR filetype:yaml intext:kind: Deployment)'),
        ("Terraform", 'site:{site} (filetype:tf OR inurl:terraform OR inurl:.tfvars)'),
        ("Ansible", 'site:{site} (inurl:ansible OR inurl:playbook.yml)'),
        ("Jenkinsfile", 'site:{site} inurl:Jenkinsfile'),
        (".gitlab-ci.yml", 'site:{site} inurl:.gitlab-ci.yml'),
        ("github workflow", 'site:{site} inurl:.github/workflows'),
        ("Makefile", 'site:{site} inurl:Makefile'),
        ("webpack / vite", 'site:{site} (inurl:webpack.config OR inurl:vite.config)'),
        ("tsconfig", 'site:{site} inurl:tsconfig.json'),
        (".npmrc / .yarnrc", 'site:{site} (inurl:.npmrc OR inurl:.yarnrc)'),
        (".dockerignore", 'site:{site} inurl:.dockerignore'),
        ("Procfile", 'site:{site} inurl:Procfile'),
        ("PEM / KEY", 'site:{site} (filetype:pem OR filetype:key)'),
        ("CRT / CER / CSR", 'site:{site} (filetype:crt OR filetype:cer OR filetype:csr)'),
        ("P12 / PFX / JKS", 'site:{site} (filetype:p12 OR filetype:pfx OR filetype:jks OR filetype:keystore)'),
        ("PPK (PuTTY)", 'site:{site} filetype:ppk'),
        ("id_rsa / known_hosts", 'site:{site} (inurl:id_rsa OR inurl:id_dsa OR inurl:known_hosts OR inurl:authorized_keys)'),
        ("GPG / ASC", 'site:{site} (filetype:gpg OR filetype:asc OR filetype:pgp)'),
        ("security.txt", 'site:{site} inurl:/.well-known/security.txt OR inurl:security.txt'),
        ("well-known", 'site:{site} inurl:/.well-known/'),
        ("sitemap.xml", 'site:{site} inurl:sitemap.xml OR inurl:sitemap_index.xml'),
        ("humans.txt", 'site:{site} inurl:humans.txt'),
        ("ads.txt / app-ads", 'site:{site} (inurl:ads.txt OR inurl:app-ads.txt)'),
        ("manifest.json", 'site:{site} inurl:manifest.json OR inurl:site.webmanifest'),
        ("favicon", 'site:{site} inurl:favicon.ico'),
        ("crossdomain extra", 'site:{site} inurl:crossdomain.xml'),
        ("browserconfig", 'site:{site} inurl:browserconfig.xml'),
        ("service-worker", 'site:{site} (inurl:service-worker.js OR inurl:sw.js)'),
        ("openid / oauth well-known", 'site:{site} (inurl:/.well-known/openid-configuration OR inurl:/.well-known/oauth)'),
        ("change-password well-known", 'site:{site} inurl:/.well-known/change-password'),
        ("mta-sts", 'site:{site} inurl:/.well-known/mta-sts.txt'),
        ("assetlinks / apple-app", 'site:{site} (inurl:assetlinks.json OR inurl:apple-app-site-association)'),
        ("Swagger / OpenAPI", 'site:{site} (inurl:swagger OR inurl:openapi OR intitle:Swagger)'),
        ("Swagger UI", 'site:{site} inurl:swagger-ui OR intitle:"Swagger UI"'),
        ("Redoc", 'site:{site} inurl:redoc OR intitle:ReDoc'),
        ("GraphQL", 'site:{site} (inurl:graphql OR inurl:graphiql OR intitle:GraphiQL)'),
        ("GraphQL playground", 'site:{site} (intitle:"GraphQL Playground" OR inurl:playground)'),
        ("API docs", 'site:{site} (inurl:api-docs OR inurl:apidocs OR intitle:"API Documentation")'),
        ("WADL", 'site:{site} (filetype:wadl OR inurl:application.wadl)'),
        ("Postman collection", 'site:{site} (inurl:postman OR filetype:json intext:info._postman_id)'),
        ("API v1/v2", 'site:{site} (inurl:/api/v1 OR inurl:/api/v2 OR inurl:/api/v3)'),
        ("REST endpoint", 'site:{site} (inurl:/rest/ OR inurl:/api/)'),
        ("RPC / SOAP", 'site:{site} (inurl:soap OR inurl:xmlrpc OR inurl:/rpc/)'),
        ("Webhook", 'site:{site} inurl:webhook'),
        ("Callback / oauth", 'site:{site} (inurl:callback OR inurl:oauth OR inurl:authorize)'),
        ("Token endpoint", 'site:{site} (inurl:token OR inurl:oauth/token)'),
        ("Health / status", 'site:{site} (inurl:health OR inurl:healthz OR inurl:ready OR inurl:status)'),
        ("Metrics / prometheus", 'site:{site} (inurl:metrics OR inurl:prometheus OR inurl:/actuator/)'),
        ("Actuator", 'site:{site} inurl:/actuator'),
        ("Spring Boot", 'site:{site} (inurl:/actuator/env OR inurl:/actuator/heapdump OR inurl:/actuator/mappings)'),
        ("phpinfo extra", 'site:{site} (inurl:info.php OR inurl:phpinfo OR inurl:test.php)'),
        ("server-status", 'site:{site} (inurl:server-status OR inurl:server-info)'),
        ("elmah / errors", 'site:{site} (inurl:elmah.axd OR inurl:trace.axd)'),
        ("Trace.axd", 'site:{site} inurl:trace.axd'),
        ("elmah.axd", 'site:{site} inurl:elmah'),
        ("Staging", 'site:{site} (inurl:staging OR inurl:stg OR intitle:staging)'),
        ("UAT", 'site:{site} (inurl:uat OR intitle:uat)'),
        ("QA", 'site:{site} (inurl:qa OR inurl:homolog OR inurl:homologacao)'),
        ("Dev", 'site:{site} (inurl:dev OR inurl:development) -inurl:developer'),
        ("Beta / alpha", 'site:{site} (inurl:beta OR inurl:alpha OR intitle:beta)'),
        ("Demo / sandbox", 'site:{site} (inurl:demo OR inurl:sandbox OR intitle:demo)'),
        ("Preview / old", 'site:{site} (inurl:preview OR inurl:old OR inurl:legacy OR inurl:arquivo)'),
        ("v1 / v2 path", 'site:{site} (inurl:/v1/ OR inurl:/v2/ OR inurl:/old/)'),
        ("tmp / temp", 'site:{site} (inurl:tmp OR inurl:temp OR inurl:tmpfile)'),
        ("cache path", 'site:{site} inurl:cache'),
        ("draft", 'site:{site} (inurl:draft OR intitle:draft OR intext:rascunho)'),
        ("S3 bucket ref", 'site:{site} (inurl:s3.amazonaws.com OR inurl:s3- OR intext:.s3.amazonaws.com)'),
        ("Azure blob", 'site:{site} (inurl:blob.core.windows.net OR inurl:azureedge.net)'),
        ("GCS", 'site:{site} (inurl:storage.googleapis.com OR inurl:storage.cloud.google.com)'),
        ("DigitalOcean spaces", 'site:{site} inurl:digitaloceanspaces.com'),
        ("CloudFront", 'site:{site} inurl:cloudfront.net'),
        ("Firebase", 'site:{site} (inurl:firebaseio.com OR inurl:firebaseapp.com)'),
        ("Supabase", 'site:{site} inurl:supabase'),
        ("Heroku", 'site:{site} inurl:herokuapp.com'),
        ("Vercel / Netlify", 'site:{site} (inurl:vercel.app OR inurl:netlify.app)'),
        ("ngrok / localtunnel", 'site:{site} (inurl:ngrok OR inurl:loca.lt)'),
        ("Emails @domínio", 'site:{site} "@{site}"'),
        ("Emails mailto", 'site:{site} intext:mailto:'),
        ("Emails filetype misto", '"{site}" (@gmail.com OR @hotmail.com OR @outlook.com OR @yahoo.com)'),
        ("Contato", 'site:{site} (inurl:contato OR inurl:contact OR intitle:contato)'),
        ("Equipe / time", 'site:{site} (inurl:equipe OR inurl:team OR inurl:staff OR inurl:quem-somos)'),
        ("Sobre / about", 'site:{site} (inurl:about OR inurl:sobre)'),
        ("Telefone", 'site:{site} (intext:telefone OR intext:"+55" OR intext:whatsapp)'),
        ("CNPJ na página", 'site:{site} (intext:cnpj OR intext:"14.xxx")'),
        ("LinkedIn employees", 'site:linkedin.com/in "{site}"'),
        ("Currículo externo", '"{site}" (currículo OR curriculo OR resume OR "curriculum vitae") filetype:pdf'),
        ("Vagas / careers", 'site:{site} (inurl:vagas OR inurl:careers OR inurl:jobs OR inurl:trabalhe)'),
        ("Vagas stack", 'site:{site} (inurl:vagas OR inurl:careers) (python OR java OR aws OR kubernetes OR php)'),
        ("Imprensa", 'site:{site} (inurl:imprensa OR inurl:press OR inurl:newsroom)'),
        ("Investidores", 'site:{site} (inurl:investidores OR inurl:investor OR inurl:ri)'),
        ("Relatório anual", 'site:{site} ("relatório anual" OR "annual report" OR "demonstrações financeiras")'),
        ("Política de privacidade", 'site:{site} (inurl:privacidade OR inurl:privacy OR intitle:"política de privacidade")'),
        ("Termos de uso", 'site:{site} (inurl:termos OR inurl:terms OR intitle:"termos de uso")'),
        ("Cookies", 'site:{site} (inurl:cookies OR intitle:"política de cookies")'),
        ("LGPD / GDPR", 'site:{site} (intext:LGPD OR intext:GDPR OR inurl:lgpd)'),
        ("Status page", 'site:{site} (inurl:status OR intitle:"status" intext:uptime)'),
        ("Changelog", 'site:{site} (inurl:changelog OR inurl:releases OR intitle:changelog)'),
        ("FAQ", 'site:{site} (inurl:faq OR inurl:ajuda OR inurl:help)'),
        ("WordPress", 'site:{site} (inurl:wp-content OR inurl:wp-includes OR inurl:xmlrpc.php)'),
        ("xmlrpc.php", 'site:{site} inurl:xmlrpc.php'),
        ("wp-json", 'site:{site} inurl:wp-json/wp/v2'),
        ("readme.html WP", 'site:{site} inurl:readme.html intitle:WordPress'),
        ("license.txt WP", 'site:{site} inurl:license.txt WordPress'),
        ("Joomla fingerprint", 'site:{site} (inurl:/components/ OR inurl:/modules/ OR inurl:option=com_)'),
        ("Drupal fingerprint", 'site:{site} (inurl:/sites/default/ OR inurl:/node/ OR intext:"Powered by Drupal")'),
        ("Magento", 'site:{site} (inurl:/downloader/ OR inurl:mage OR intext:"Magento")'),
        ("PrestaShop", 'site:{site} (inurl:/modules/ OR intext:PrestaShop)'),
        ("Shopify", 'site:{site} (inurl:myshopify.com OR intext:"cdn.shopify.com")'),
        ("Ghost / Ghost CMS", 'site:{site} (inurl:ghost OR intext:"Ghost")'),
        ("Moodle", 'site:{site} (inurl:/moodle/ OR intitle:Moodle)'),
        ("Grafana", 'site:{site} (intitle:Grafana OR inurl:/login intitle:Grafana)'),
        ("Kibana", 'site:{site} (intitle:Kibana OR inurl:app/kibana)'),
        ("Jenkins", 'site:{site} (intitle:"Dashboard [Jenkins]" OR inurl:jenkins)'),
        ("GitLab self-hosted", 'site:{site} (intitle:GitLab OR inurl:users/sign_in)'),
        ("Bitbucket Server", 'site:{site} intitle:"Bitbucket"'),
        ("SonarQube", 'site:{site} (intitle:SonarQube OR inurl:sonar)'),
        ("Nexus / Artifactory", 'site:{site} (intitle:Nexus OR intitle:Artifactory)'),
        ("Portainer", 'site:{site} intitle:Portainer'),
        ("phpLDAPadmin", 'site:{site} intitle:phpLDAPadmin'),
        ("Webmin", 'site:{site} intitle:Webmin'),
        ("cPanel leftover", 'site:{site} (inurl:2082 OR inurl:2083 OR intitle:cPanel)'),
        ("Roundcube leftover", 'site:{site} intitle:Roundcube'),
        ("OWA / Exchange", 'site:{site} (inurl:owa OR inurl:ecp OR intitle:"Outlook Web")'),
        ("Citrix / VPN", 'site:{site} (intitle:Citrix OR inurl:vpn OR intitle:"NetScaler")'),
        ("Fortinet / SSL VPN", 'site:{site} (inurl:remote/login OR intitle:"FortiGate")'),
        ("Pulse / Ivanti", 'site:{site} (inurl:dana-na OR intitle:"Pulse Connect")'),
        ("Parâmetro id", 'site:{site} inurl:id='),
        ("Parâmetro page", 'site:{site} inurl:page='),
        ("Parâmetro file", 'site:{site} inurl:file='),
        ("Parâmetro doc", 'site:{site} inurl:doc='),
        ("Parâmetro folder", 'site:{site} inurl:folder= OR inurl:dir='),
        ("Parâmetro cat", 'site:{site} inurl:cat= OR inurl:category='),
        ("Parâmetro lang", 'site:{site} inurl:lang= OR inurl:locale='),
        ("Parâmetro debug", 'site:{site} inurl:debug= OR inurl:dbg= OR inurl:test='),
        ("Parâmetro token", 'site:{site} inurl:token= OR inurl:access_token='),
        ("Parâmetro key", 'site:{site} inurl:key= OR inurl:api_key='),
        ("Parâmetro callback", 'site:{site} inurl:callback= OR inurl:jsonp='),
        ("Parâmetro dest", 'site:{site} inurl:dest= OR inurl:destination= OR inurl:redir='),
        ("Parâmetro img", 'site:{site} inurl:img= OR inurl:image= OR inurl:src='),
        ("Parâmetro template", 'site:{site} inurl:template= OR inurl:layout= OR inurl:view='),
        ("Parâmetro download", 'site:{site} inurl:download= OR inurl:dl='),
        ("Open params extra", 'site:{site} (inurl:continue= OR inurl:returnUrl= OR inurl:return_to=)'),
        ("Index of raiz", 'site:{site} intitle:"index of /"'),
        ("Index of parent", 'site:{site} intitle:"index of" "parent directory"'),
        ("Index of pub", 'site:{site} intitle:"index of" /pub OR intitle:"index of" /public'),
        ("Index of data", 'site:{site} intitle:"index of" /data OR intitle:"index of" /dados'),
        ("Index of tmp", 'site:{site} intitle:"index of" /tmp OR intitle:"index of" /temp'),
        ("Index of upload", 'site:{site} intitle:"index of" /upload OR intitle:"index of" /uploads'),
        ("Index of images", 'site:{site} intitle:"index of" /images OR intitle:"index of" /img'),
        ("Index of includes", 'site:{site} intitle:"index of" /includes OR intitle:"index of" /inc'),
        ("Index of src", 'site:{site} intitle:"index of" /src OR intitle:"index of" /source'),
        ("Index of vendor", 'site:{site} intitle:"index of" /vendor OR intitle:"index of" /node_modules'),
        ("Index of .well-known", 'site:{site} intitle:"index of" .well-known'),
        ("Index of mail", 'site:{site} intitle:"index of" /mail OR intitle:"index of" /email'),
        ("Index of users", 'site:{site} intitle:"index of" /users OR intitle:"index of" /user'),
        ("Index of private", 'site:{site} intitle:"index of" /private OR intitle:"index of" /interno'),
        ("Google cache raw", 'cache:{site}'),
        ("site no cache", 'site:{site} cache'),
        ("Wayback via Google", 'site:web.archive.org "{site}"'),
        ("Cached pages extra", 'site:{site} "cached" OR inurl:cached'),
        ("Cópia / mirror", 'site:{site} (inurl:mirror OR inurl:copia OR inurl:copy)'),
        ("Jupyter / IPYNB", 'site:{site} (filetype:ipynb OR inurl:.ipynb)'),
        ("R / RMD", 'site:{site} (filetype:r OR filetype:rmd)'),
        ("Parquet / feather", 'site:{site} (filetype:parquet OR inurl:parquet)'),
        ("SQLite db", 'site:{site} (filetype:sqlite OR filetype:sqlite3 OR filetype:db)'),
        ("Android assetlinks", 'site:{site} inurl:.well-known/assetlinks.json'),
        ("iOS AASA", 'site:{site} inurl:apple-app-site-association'),
        ("Deep link / intent", 'site:{site} (inurl:intent:// OR intext:"android-app://")'),
        ("App store refs", '"{site}" (site:play.google.com OR site:apps.apple.com)'),
        ("Whois menções", '"{site}" (whois OR "name server" OR nameserver OR "dns")'),
        ("ASN / netblock", '"{site}" (ASN OR "netblock" OR "ip range")'),
        ("MX / SPF / DMARC", 'site:{site} (intext:v=spf1 OR intext:v=DMARC1 OR intext:"MX")'),
        ("DKIM", 'site:{site} (intext:DKIM OR intext:k=rsa)'),
        ("CVE menções", '"{site}" (CVE- OR vulnerability OR vulnerabilidade)'),
        ("Breach / leak", '"{site}" (breach OR leak OR vazamento OR "data dump" OR dumped)'),
        ("Paste genérico extra", '"{site}" (paste OR leaked OR "shared secretly")'),
        ("Documento interno genérico", 'site:{site} (intitle:interno OR intitle:internal OR intitle:restricted)'),
        ("Confidential genérico", 'site:{site} (intitle:confidential OR intitle:confidencial OR intitle:secreto)'),
        ("Do not distribute", 'site:{site} ("do not distribute" OR "não distribuir" OR "uso interno" OR "internal use only")'),
        ("Draft watermark", 'site:{site} (intitle:draft OR intext:rascunho OR intext:"não oficial")'),
        ("Senha em URL", 'site:{site} (inurl:password= OR inurl:passwd= OR inurl:pwd= OR inurl:senha=)'),
        ("Basic auth leftover", 'site:{site} (inurl:http://*:*@ OR intext:"Authorization: Basic")'),
        ("FTP em claro", 'site:{site} (inurl:ftp:// OR intext:ftp://)'),
        ("Connection strings web", 'site:{site} (intext:"mongodb://" OR intext:"postgres://" OR intext:"mysql://" OR intext:"redis://")'),
        ("JWT leftover", 'site:{site} (intext:eyJhbGci OR intext:"Bearer eyJ")'),
        ("Private key block", 'site:{site} (intext:"BEGIN RSA PRIVATE KEY" OR intext:"BEGIN OPENSSH PRIVATE KEY" OR intext:"BEGIN PRIVATE KEY")'),
        ("AWS AKIA", 'site:{site} (intext:AKIA OR intext:ASIA)'),
        ("Google API key", 'site:{site} (intext:AIza OR intext:"AAAA")'),
        ("Slack token", 'site:{site} (intext:xoxb- OR intext:xoxp- OR intext:xoxs-)'),
        ("GitHub token", 'site:{site} (intext:ghp_ OR intext:gho_ OR intext:github_pat_)'),
        ("Stripe key", 'site:{site} (intext:sk_live_ OR intext:rk_live_ OR intext:pk_live_)'),
        ("Sendgrid / Mailgun", 'site:{site} (intext:SG. OR intext:key- OR intext:"mailgun")'),
        ("Twilio", 'site:{site} (intext:SK AND intext:AC) (twilio OR accountsid)'),
        ("Firebase config", 'site:{site} (intext:apiKey AND intext:authDomain AND intext:projectId)'),
    ],
}

# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------------------

def encontrar_chrome():
    """
    Windows 10 → Google Chrome
    Kali Linux → Firefox
    macOS       → Google Chrome
    """

    # =========================================================
    # WINDOWS → GOOGLE CHROME
    # =========================================================
    if sys.platform.startswith("win"):

        candidatos = [
            os.path.expandvars(
                r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
            ),
        ]

        for caminho in candidatos:
            if os.path.isfile(caminho):
                return caminho

    # =========================================================
    # KALI / LINUX → FIREFOX
    # =========================================================
    elif sys.platform.startswith("linux"):

        candidatos = [
            "/usr/bin/firefox",
            "/usr/bin/firefox-esr",
            "/usr/local/bin/firefox",
            "/snap/bin/firefox",
        ]

        for caminho in candidatos:
            if os.path.isfile(caminho):
                return caminho

        # Procura Firefox no PATH
        for comando in ("firefox", "firefox-esr"):

            try:
                resultado = subprocess.run(
                    ["which", comando],
                    capture_output=True,
                    text=True
                )

                caminho = resultado.stdout.strip()

                if caminho:
                    return caminho

            except Exception:
                pass

    # =========================================================
    # macOS → GOOGLE CHROME
    # =========================================================
    elif sys.platform == "darwin":

        caminho = (
            "/Applications/"
            "Google Chrome.app/"
            "Contents/"
            "MacOS/"
            "Google Chrome"
        )

        if os.path.isfile(caminho):
            return caminho

    return None


def url_para_dork(dork, motor=None):

    dork = dork.strip()

    # Se já for uma URL
    if dork.lower().startswith(("http://", "https://")):
        return dork

    # Codifica a Dork
    q = quote(dork)

    # Usa o motor selecionado
    if motor is None:
        motor = combo_motor.get()

    # Pega o template
    template = MOTORES.get(
        motor,
        MOTORES["Google"]
    )

    return template.format(q=q)


def abrir_no_chrome(dork, motor=None):

    url = url_para_dork(dork, motor)

    # Mantém o nome da variável para não quebrar
    # o restante do seu código
    chrome = encontrar_chrome()

    if chrome:

        try:
            subprocess.Popen(
                [chrome, url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        except Exception:
            webbrowser.open(url)

    else:
        webbrowser.open(url)

# ---------------------------------------------------------------------------
# LÓGICA
# ---------------------------------------------------------------------------
dorks_por_aba = {}
dorks_visiveis = {}
listboxes = {}
botoes_abas = {}
aba_atual = "Todas"

def set_status(msg):
    try:
        status_var.set(msg)
    except NameError:
        pass

def normalizar_site(texto):
    site = texto.strip()
    for prefixo in ("https://", "http://", "www."):
        if site.lower().startswith(prefixo):
            site = site[len(prefixo):]
    return site.rstrip("/").strip()

def aplicar_lista_na_aba(nome, lista):
    lb = listboxes.get(nome)
    if lb is None:
        return
    lb.delete(0, tk.END)
    dorks_visiveis[nome] = list(lista)
    for rotulo, dork in lista:
        lb.insert(tk.END, f"{rotulo}: {dork}")

def pesquisar(event=None):
    try:
        termo = entry_pesquisa.get().strip().lower()
    except NameError:
        return

    nome = aba_atual
    origem = dorks_por_aba.get(nome, [])

    if not origem:
        if termo:
            set_status("Nada para pesquisar. Gere as dorks primeiro.")
        return

    if not termo:
        aplicar_lista_na_aba(nome, origem)
        set_status(f"✔ Aba {nome} · {len(origem)} dorks (pesquisa limpa)")
        return

    filtradas = [
        (rotulo, dork)
        for rotulo, dork in origem
        if termo in rotulo.lower() or termo in dork.lower()
    ]
    aplicar_lista_na_aba(nome, filtradas)
    set_status(f"🔍 '{termo}' · {len(filtradas)} de {len(origem)} dorks na aba {nome}")

def gerar(event=None):
    global aba_atual

    site = normalizar_site(entry_site.get())

    for nome, lb in listboxes.items():
        lb.delete(0, tk.END)
        dorks_por_aba[nome] = []
        dorks_visiveis[nome] = []

    todas = []

    for cat, lista_dorks in CATEGORIAS.items():
        if cat not in dorks_por_aba:
            dorks_por_aba[cat] = []

        for rotulo, template in lista_dorks:
            try:
                dork = template.format(site=site)
            except Exception:
                dork = template

            dorks_por_aba[cat].append((rotulo, dork))
            todas.append((rotulo, dork))

    dorks_por_aba["Todas"] = todas

    for nome, lista in dorks_por_aba.items():
        dorks_visiveis[nome] = list(lista)
        aplicar_lista_na_aba(nome, lista)

    if aba_atual not in listboxes:
        aba_atual = "Todas"

    mostrar_aba(aba_atual)

def sincronizar_campo(event=None):
    global aba_atual

    lb = listboxes.get(aba_atual)
    if lb is None:
        return

    selecionadas = lb.curselection()
    if not selecionadas:
        return

    indice = selecionadas[0]
    lista = dorks_visiveis.get(aba_atual, [])
    if indice >= len(lista):
        return

    _, dork = lista[indice]
    entry_dork.delete(0, tk.END)
    entry_dork.insert(0, dork)

def mostrar_aba(nome):
    global aba_atual

    if nome not in listboxes:
        return

    aba_atual = nome

    for lb in listboxes.values():
        lb.pack_forget()

    listboxes[nome].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    for n, btn in botoes_abas.items():
        if n == nome:
            btn.configure(relief="sunken", bg="#ffffff", fg="#000000")
        else:
            btn.configure(
                relief="raised",
                bg=CORES_BOTOES_ABAS.get(n, "#00aa00"),
                fg="#000000",
            )

    try:
        motor = combo_motor.get()
    except Exception:
        motor = ""

    quantidade = len(dorks_por_aba.get(nome, []))
    if nome == "Todas":
        set_status(f"✔ Aba Todas · {quantidade} dorks no total · motor: {motor}")
    else:
        set_status(f"✔ Aba {nome} · {quantidade} dorks nesta categoria · motor: {motor}")

    pesquisar()

def abrir_do_campo(event=None, motor=None):
    dork = entry_dork.get().strip()
    if not dork:
        messagebox.showinfo("Info", "O campo de dork está vazio.\nSelecione uma dork na lista primeiro.")
        return

    motor_usado = motor or combo_motor.get()

    janela = tk.Toplevel(root)
    janela.title("Abrir no navegador?")
    janela.geometry("1200x400")
    janela.minsize(600, 300)
    janela.transient(root)
    janela.grab_set()

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1000) // 2
    y = (janela.winfo_screenheight() - 400) // 2
    janela.geometry(f"1000x400+{x}+{y}")

    frame = ttk.Frame(janela)
    frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

    ttk.Label(frame, text="🌐 Abrir no navegador?",
              font=("Consolas", 16, "bold")).pack(pady=(5, 10))

    ttk.Label(frame, text="Deseja abrir esta busca?",
              font=("Consolas", 11)).pack(pady=(0, 8))

    frame_texto = ttk.Frame(frame)
    frame_texto.pack(fill=tk.BOTH, expand=True, pady=5)

    texto = tk.Text(
        frame_texto, font=("Consolas", 11),
        wrap=tk.WORD, height=8,
        relief=tk.FLAT, borderwidth=1
    )
    scroll = ttk.Scrollbar(frame_texto, orient=tk.VERTICAL, command=texto.yview)
    texto.configure(yscrollcommand=scroll.set)

    texto.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)

    texto.insert("1.0", dork)
    texto.config(state=tk.DISABLED)

    ttk.Label(
        frame, text=f"Motor: {motor_usado}",
        font=("Consolas", 11, "bold")
    ).pack(pady=8)

    botoes = ttk.Frame(frame)
    botoes.pack(pady=(5, 10))

    def confirmar():
        try:
            janela.grab_release()
        except tk.TclError:
            pass
        janela.destroy()
        abrir_no_chrome(dork, motor_usado)
        set_status(f"✔ Aberta em {motor_usado}: {dork}")
        pular_proxima()

    def cancelar():
        try:
            janela.grab_release()
        except tk.TclError:
            pass
        janela.destroy()
        set_status(f"✖ Não aberta: {dork}")

    ttk.Button(
        botoes, text="🌐 Abrir", command=confirmar
    ).pack(side=tk.LEFT, padx=10, ipadx=20, ipady=5)

    ttk.Button(
        botoes, text="✖ Cancelar", command=cancelar
    ).pack(side=tk.LEFT, padx=10, ipadx=20, ipady=5)

    janela.bind("<Return>", lambda e: confirmar())
    janela.bind("<Escape>", lambda e: cancelar())
    janela.protocol("WM_DELETE_WINDOW", cancelar)
    janela.after(50, lambda: janela.focus_force())


def pular_proxima():
    lb = listboxes.get(aba_atual)
    if not lb:
        return

    selecionadas = lb.curselection()
    if selecionadas:
        prox = selecionadas[0] + 1
        if prox < lb.size():
            lb.selection_clear(0, tk.END)
            lb.selection_set(prox)
            lb.activate(prox)
            lb.see(prox)
            sincronizar_campo()


def copiar_campo():
    dork = entry_dork.get().strip()
    if not dork:
        messagebox.showinfo("Info", "O campo está vazio.")
        return

    root.clipboard_clear()
    root.clipboard_append(dork)
    set_status(f"✔ Copiada: {dork}")


def copiar_todas():
    dorks = dorks_visiveis.get(aba_atual, [])
    if not dorks:
        return

    texto = "\n".join(f"{rotulo}: {dork}" for rotulo, dork in dorks)
    root.clipboard_clear()
    root.clipboard_append(texto)
    set_status(f"✔ {len(dorks)} dorks da aba '{aba_atual}' copiadas.")


def limpar():
    for entry in (entry_site, entry_dork, entry_pesquisa):
        entry.delete(0, tk.END)

    for lb in listboxes.values():
        lb.delete(0, tk.END)

    for k in dorks_por_aba:
        dorks_por_aba[k] = []
        dorks_visiveis[k] = []

    set_status("Pronto. Digite o domínio (ou deixe vazio) e clique em Gerar Dorks.")


def mostrar_menu_contexto(event):
    lb = listboxes.get(aba_atual)
    if not lb:
        return

    index = lb.nearest(event.y)
    if 0 <= index < lb.size():
        lb.selection_clear(0, tk.END)
        lb.selection_set(index)
        lb.activate(index)
        sincronizar_campo()

    menu = tk.Menu(
        root,
        tearoff=0,
        bg="#111111",
        fg="#00ff00",
        activebackground="#003300",
        activeforeground="#00ff00",
        font=("Consolas", 10)
    )

    menu.add_command(
        label="🌐 Abrir com motor atual",
        command=abrir_do_campo
    )
    menu.add_separator()

    for nome in ("Google", "Bing", "DuckDuckGo", "Yandex", "Brave"):
        menu.add_command(
            label=nome,
            command=lambda m=nome: abrir_do_campo(motor=m)
        )

    menu.add_separator()
    menu.add_command(label="📋 Copiar dork", command=copiar_campo)

    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()

# ---------------------------------------------------------------------------
# INTERFACE
# ---------------------------------------------------------------------------
root = tk.Tk()

root.title("Google Hacking Dork PRO")

# =========================================================
# JANELA MAXIMIZADA — WINDOWS 10 E KALI LINUX
# =========================================================

try:
    if sys.platform.startswith("win"):
        # Windows 10
        root.state("zoomed")

    elif sys.platform.startswith("linux"):
        # Kali Linux / Linux
        try:
            root.state("zoomed")
        except tk.TclError:
            root.attributes("-zoomed", True)

    else:
        # Outros sistemas
        try:
            root.state("zoomed")
        except tk.TclError:
            pass

except tk.TclError:
    pass

root.geometry("1150x750")
root.minsize(850, 580)
root.configure(bg="#000000")

style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background="#000000")
style.configure("TLabel", background="#000000", foreground="#00ff00", font=("Consolas", 10))
style.configure(
    "TButton",
    background="#00aa00",
    foreground="#000000",
    font=("Consolas", 10, "bold"),
    borderwidth=2,
    relief="raised",
)
style.map(
    "TButton",
    background=[("active", "#00ff00"), ("pressed", "#007700")],
    foreground=[("active", "#000000"), ("pressed", "#ffffff")],
)
style.configure(
    "TCombobox",
    fieldbackground="#001100",
    background="#003300",
    foreground="#00ff00",
    arrowcolor="#00ff00",
)
style.map("TCombobox", fieldbackground=[("readonly", "#001100")])
style.configure("TEntry", fieldbackground="#001100", foreground="#00ff00", insertcolor="#00ff00")

# --- Topo ---
frame_top = ttk.Frame(root, padding=10)
frame_top.pack(fill=tk.X)

ttk.Label(frame_top, text=">> Alvo:").pack(side=tk.LEFT)
entry_site = ttk.Entry(frame_top, width=28, font=("Consolas", 11))
entry_site.pack(side=tk.LEFT, padx=(6, 10))
entry_site.bind("<Return>", gerar)

ttk.Label(frame_top, text="Motor:").pack(side=tk.LEFT)
combo_motor = ttk.Combobox(frame_top, values=list(MOTORES.keys()), state="readonly", width=12)
combo_motor.current(0)
combo_motor.pack(side=tk.LEFT, padx=(6, 10))

ttk.Button(frame_top, text="⚡ Gerar Dorks", command=gerar).pack(side=tk.LEFT)
ttk.Label(frame_top, text="(pode deixar vazio)", foreground="#00aa00").pack(side=tk.LEFT, padx=10)

# --- Botões das abas ---
frame_abas = tk.Frame(root, bg="#000000")
frame_abas.pack(fill=tk.X, padx=10, pady=(5, 0))

nomes_abas = ["Todas"] + list(CATEGORIAS.keys())

for nome in nomes_abas:
    cor = CORES_BOTOES_ABAS.get(nome, "#00aa00")
    btn = tk.Button(
        frame_abas,
        text=nome,
        bg=cor,
        fg="#000000",
        font=("Consolas", 9, "bold"),
        relief="raised",
        bd=2,
        padx=8,
        pady=4,
        command=lambda n=nome: mostrar_aba(n),
    )
    btn.pack(side=tk.LEFT, padx=2, pady=2)
    botoes_abas[nome] = btn

# --- Área de resultados ---
frame_lista = tk.Frame(root, bg="#000000")
frame_lista.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

scroll = tk.Scrollbar(frame_lista, bg="#003300")
scroll.pack(side=tk.RIGHT, fill=tk.Y)

def criar_listbox():
    lb = tk.Listbox(
        frame_lista,
        yscrollcommand=scroll.set,
        selectmode=tk.SINGLE,
        font=("Consolas", 9),
        activestyle="dotbox",
        bg="#000000",
        fg="#00ff00",
        selectbackground="#003300",
        selectforeground="#ffffff",
        highlightthickness=0,
        borderwidth=0,
        relief="flat",
    )
    lb.bind("<<ListboxSelect>>", sincronizar_campo)
    lb.bind("<Double-Button-1>", lambda e: abrir_do_campo())
    lb.bind("<Button-3>", mostrar_menu_contexto)
    return lb

listboxes["Todas"] = criar_listbox()
dorks_por_aba["Todas"] = []
dorks_visiveis["Todas"] = []

for nome_cat in CATEGORIAS.keys():
    listboxes[nome_cat] = criar_listbox()
    dorks_por_aba[nome_cat] = []
    dorks_visiveis[nome_cat] = []

scroll.config(command=lambda *args: listboxes[aba_atual].yview(*args))

# --- Campo da dork ---
frame_campo = ttk.Frame(root, padding=(10, 6, 10, 0))
frame_campo.pack(fill=tk.X)

ttk.Label(frame_campo, text="Dork selecionada:").pack(side=tk.LEFT)
entry_dork = ttk.Entry(frame_campo, width=30, font=("Consolas", 11))
entry_dork.pack(side=tk.LEFT, padx=(8, 8), fill=tk.X, expand=True)
entry_dork.bind("<Return>", lambda e: abrir_do_campo())

# --- Botões inferiores ---
frame_botoes = ttk.Frame(root, padding=10)
frame_botoes.pack(fill=tk.X)

ttk.Button(frame_botoes, text="🌐 Abrir no navegador selecionado", command=lambda: abrir_do_campo()).pack(side=tk.LEFT, padx=(0, 6))
ttk.Button(frame_botoes, text="📋 Copiar", command=copiar_campo).pack(side=tk.LEFT, padx=6)
ttk.Button(frame_botoes, text="📄 Copiar Todas (aba)", command=copiar_todas).pack(side=tk.LEFT, padx=6)

ttk.Label(frame_botoes, text="Pesquisar:").pack(side=tk.LEFT, padx=(12, 4))
entry_pesquisa = ttk.Entry(frame_botoes, width=22, font=("Consolas", 10))
entry_pesquisa.pack(side=tk.LEFT, padx=(0, 4))
entry_pesquisa.bind("<Return>", pesquisar)
# Pesquisar altomaticamente Scem clicar no botao Pesquisar
entry_pesquisa.bind("<KeyRelease>", pesquisar)

ttk.Button(frame_botoes, text="🔍 Pesquisar", command=pesquisar).pack(side=tk.LEFT, padx=(0, 6))

ttk.Button(frame_botoes, text="Limpar", command=limpar).pack(side=tk.LEFT, padx=6)
ttk.Button(frame_botoes, text="Sair", command=root.destroy).pack(side=tk.RIGHT)

# --- Status ---
status_var = tk.StringVar(
    value="Pronto. Digite o domínio (ou deixe vazio) e clique em Gerar Dorks. Botão direito = escolher motor."
)
status_label = tk.Label(
    root,
    textvariable=status_var,
    bg="#001100",
    fg="#00ff00",
    anchor=tk.W,
    padx=8,
    pady=6,
    font=("Consolas", 9),
)
status_label.pack(fill=tk.X, side=tk.BOTTOM)

mostrar_aba("Todas")
root.mainloop()
