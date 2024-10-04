import win32evtlog
import datetime

def monitor_security_logs():
    # Nome do log de segurança
    log_type = 'Security'
    
    # Conexão ao log de eventos
    h_event_log = win32evtlog.OpenEventLog(None, log_type)
    
    # Número de entradas que você deseja ler
    num_events = 10
    total_events = win32evtlog.GetNumberOfEventLogRecords(h_event_log)

    print(f"\nTotal de eventos no log de segurança: {total_events}\n")

    # Lendo os eventos
    events = win32evtlog.ReadEventLog(h_event_log, win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ, 0)

    found_suspicious_event = False  # Variável para verificar se algum evento suspeito foi encontrado

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
    
    # IDs de eventos a serem monitorados
    suspicious_event_ids = event_descriptions.keys()
    
    # Lê os eventos e verifica se há eventos suspeitos
    for event in events:
        if num_events <= 0:
            break
        
        event_id = event.EventID
        event_time = event.TimeGenerated
        event_source = event.SourceName
        event_message = event.StringInserts

        # Verifique se o ID do evento indica uma atividade suspeita
        if event_id in suspicious_event_ids:
            found_suspicious_event = True  # Evento suspeito encontrado
            print(f"Evento Suspeito Detectado:")
            print(f"ID do Evento: {event_id} - {event_descriptions[event_id]}")  # Adicionando descrição
            print(f"Data e Hora: {datetime.datetime.fromtimestamp(event_time)}")
            print(f"Fonte do Evento: {event_source}")
            print(f"Mensagem do Evento: {', '.join(event_message) if event_message else 'N/A'}\n")
            
            num_events -= 1  # Decrementar o número de eventos lidos

    # Exibir se algo foi encontrado ou não
    if found_suspicious_event:
        print("\nEventos suspeitos foram Encontrados.\n")
    else:
        print("\nNenhum evento suspeito Encontrado.\n")

    # Pergunta se o usuário deseja salvar o log
    save_log = input("Deseja salvar o log? (s/n): ").strip().lower()

    if save_log == 's':
        # Solicita o nome do arquivo para salvar o log
        log_file_name = input("\nDigite o nome do arquivo (com extensão .txt): ").strip()
        with open(log_file_name, 'w', encoding='utf-8') as log_file:
            log_file.write(f"Total de eventos no log de segurança: {total_events}\n\n")

            for event in events:
                if num_events <= 0:
                    break
                
                event_id = event.EventID
                event_time = event.TimeGenerated
                event_source = event.SourceName
                event_message = event.StringInserts

                # Verifique se o ID do evento indica uma atividade suspeita
                if event_id in suspicious_event_ids:
                    log_file.write(f"Evento Suspeito Detectado:\n")
                    log_file.write(f"ID do Evento: {event_id} - {event_descriptions[event_id]}\n")  # Adicionando descrição
                    log_file.write(f"Data e Hora: {datetime.datetime.fromtimestamp(event_time)}\n")
                    log_file.write(f"Fonte do Evento: {event_source}\n")
                    log_file.write(f"Mensagem do Evento: {', '.join(event_message) if event_message else 'N/A'}\n\n")
                    
                    num_events -= 1  # Decrementar o número de eventos lidos
        
        print(f"\nEventos foram registrados Em: {log_file_name}")
    else:
        print("\nO log não será salvo.\n")

    win32evtlog.CloseEventLog(h_event_log)

if __name__ == "__main__":
    monitor_security_logs()

input("\nAPERTE ENTER PARA SAIR\n")
