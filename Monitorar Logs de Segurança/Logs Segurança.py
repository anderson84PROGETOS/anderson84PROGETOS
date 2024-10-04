import win32evtlog
import datetime
import tkinter as tk
from tkinter import scrolledtext
from tkinter import filedialog

# Descrições dos IDs de eventos a serem monitorados
event_descriptions = {
    4625: "Falha de logon.",
    4648: "Tentativa de logon usando credenciais explícitas.",
    4634: "Logoff.",
    4672: "Uma conta de usuário foi conectada com permissões especiais.",
    4740: "Conta de usuário foi bloqueada.",
    4624: "Logon bem-sucedido.",
    4768: "Um ticket Kerberos foi solicitado.",
    4769: "Um ticket Kerberos foi concedido.",
    4776: "Logon de serviço realizado.",
    4647: "Logoff iniciado.",
    4697: "Um serviço foi instalado no sistema.",
    4738: "A conta de um usuário foi modificada.",
    10100: "Falha crítica no IPv6 do Windows.",  # ID do evento para falha crítica no IPv6
    10101: "Falha crítica no IPv6 do Windows."   # Outro ID relacionado, se necessário
}

def monitor_security_logs():
    # Nome do log de segurança
    log_type = 'Security'
    
    # Conexão ao log de eventos
    h_event_log = win32evtlog.OpenEventLog(None, log_type)
    
    # Número de entradas que você deseja ler
    num_events = 10
    total_events = win32evtlog.GetNumberOfEventLogRecords(h_event_log)

    # Limpar o campo de texto
    output_text.delete(1.0, tk.END)  # Limpa o campo de texto

    output_text.insert(tk.END, f"Total de eventos no log de segurança: {total_events}\n\n")

    # Exibir as falhas que estão sendo monitoradas
    output_text.insert(tk.END, "Eventos Monitorados\n\n")
    for event_id, description in event_descriptions.items():
        output_text.insert(tk.END, f"ID do Evento: {event_id} - {description}\n")
    output_text.insert(tk.END, "\n")  # Adicionar uma linha em branco

    # Lendo os eventos
    events = win32evtlog.ReadEventLog(h_event_log, win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ, 0)
    
    # IDs de eventos a serem monitorados
    suspicious_event_ids = event_descriptions.keys()
    
    found_events = 0  # Contador de eventos suspeitos encontrados
    
    for event in events:
        if num_events <= 0:
            break
        
        event_id = event.EventID
        event_time = event.TimeGenerated
        event_source = event.SourceName
        event_message = event.StringInserts

        # Verifique se o ID do evento indica uma atividade suspeita
        if event_id in suspicious_event_ids:
            # Formatação da data e hora
            formatted_time = event_time.strftime("%Y-%m-%d %H:%M:%S")  # Formato desejado

            output_text.insert(tk.END, f"\nEvento Suspeito Detectado\n======================\n")
            output_text.insert(tk.END, f"ID do Evento: {event_id} - {event_descriptions[event_id]}\n")  # Adicionando descrição
            output_text.insert(tk.END, f"Data e Hora: {formatted_time}\n")
            output_text.insert(tk.END, f"Fonte do Evento: {event_source}\n")
            output_text.insert(tk.END, f"Mensagem do Evento: {', '.join(event_message) if event_message else 'N/A'}\n\n")
            
            found_events += 1  # Incrementar contador de eventos encontrados
            num_events -= 1  # Decrementar o número de eventos lidos

    # Verifica se nenhum evento suspeito foi encontrado
    if found_events == 0:
        output_text.insert(tk.END, "Nenhuma falha Encontrada. Zero falhas Detectadas. Tudo OK\n")
    else:
        output_text.insert(tk.END, f"Total de falhas Encontradas: {found_events}\n")

    win32evtlog.CloseEventLog(h_event_log)

def save_log():
    # Obtém o conteúdo do campo de texto
    log_content = output_text.get(1.0, tk.END)

    # Abre a caixa de diálogo para salvar o arquivo
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                               filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    
    if file_path:  # Verifica se o usuário não cancelou
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(log_content)

# Criação da janela principal
root = tk.Tk()
root.geometry("1250x900")
root.title("Monitor de Logs de Segurança")

# Configuração do layout
frame = tk.Frame(root)
frame.pack(pady=10)

# Botão para monitorar logs
monitor_button = tk.Button(frame, text="Monitorar Logs de Segurança", command=monitor_security_logs, font=("TkDefaultFont", 11, "bold"), bg='#07f5c1')
monitor_button.pack(pady=5)

# Botão para salvar os logs
save_button = tk.Button(frame, text="Salvar Log", command=save_log, font=("TkDefaultFont", 11, "bold"), bg='#fa2355')
save_button.pack(pady=5)

# Campo de texto para exibir os logs
output_text = scrolledtext.ScrolledText(root, width=140, height=40, wrap=tk.WORD, font=("TkDefaultFont", 11, "bold"))
output_text.pack(pady=10)

# Iniciar o loop da interface gráfica
root.mainloop()
