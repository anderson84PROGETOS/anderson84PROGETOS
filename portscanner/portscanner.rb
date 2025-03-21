#!/usr/bin/env ruby

require 'socket'
require 'timeout'
require 'thread'
require 'colorize'

# Função para resolver nome de domínio para IP
def resolve_to_ip(target)
  begin
    return Socket.getaddrinfo(target, nil, :INET)[0][3]
  rescue SocketError
    puts "Erro: Não foi possível resolver o domínio '#{target}' para um IP".red
    exit
  end
end

# Função para verificar se uma porta está aberta
def scan_port(ip, port)
  begin
    Timeout::timeout(1) do
      socket = TCPSocket.new(ip, port)
      socket.close
      return true
    end
  rescue Timeout::Error, Errno::ECONNREFUSED, Errno::EHOSTUNREACH
    return false
  end
end

# Função para parsear o intervalo de portas no formato "21-65665"
def parse_port_range(input)
  if input =~ /\A(\d+)-(\d+)\z/
    start_port = $1.to_i
    end_port = $2.to_i
    return [start_port, end_port] if start_port <= end_port && start_port >= 21 && end_port <= 65665
  end
  return nil
end

# Função principal
def main(target, start_port, end_port)
  # Texto ASCII com cor azul
  ascii_art = ["\n",
    "██████╗  ██████╗ ██████╗ ████████╗    ███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗ ",
    "██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝    ██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗",
    "██████╔╝██║   ██║██████╔╝   ██║       ███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝",
    "██╔═══╝ ██║   ██║██╔══██╗   ██║       ╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗",
    "██║     ╚██████╔╝██║  ██║   ██║       ███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║",
    "╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝       ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝",
    "                                                                                                  "
  ]
  ascii_art.each { |line| puts line.blue }
  
  if target.nil? || target.empty?
    print "\nDigite o IP ou nome do website: ".green
    target = gets.chomp
  end

  target_ip = target =~ /\A\d+\.\d+\.\d+\.\d+\z/ ? target : resolve_to_ip(target)
  puts "\n\nIP: #{target_ip}".yellow # Exibe o IP após a resolução

  if start_port.nil? || end_port.nil? || start_port <= 0 || end_port <= 0
    print "\n\nDigite o intervalo de portas (ex: 21-80 ou 21-65665): ".blue    
    range_input = gets.chomp
    puts "\n\nAguarde...\n\n".yellow
    
    if ports = parse_port_range(range_input)
      start_port, end_port = ports
    else
      # Definindo todas as portas como padrão
      start_port = 21
      end_port = 65665
    end
  end

  if target_ip.empty? || start_port > end_port
    puts "Erro: Entrada inválida! Uso: ruby #{$0} [IP ou website] [porta_inicial] [porta_final]".red
    exit
  end

  open_ports = []
  max_threads = 100 # Limite de threads simultâneas

  # Dividindo o intervalo em lotes
  (start_port..end_port).each_slice(max_threads) do |batch|
    threads = []
    batch.each do |port|
      threads << Thread.new do
        if scan_port(target_ip, port)
          Thread.current[:open] = port
        end
      end
    end

    threads.each do |thread|
      thread.join
      if thread[:open]
        open_ports << thread[:open]
        puts "Porta #{thread[:open].to_s.ljust(6)} aberta".green
      end
    end
  end

  # Adicionando a mensagem final para pressionar Enter
  print "\n\n========== PRESSIONE ENTER PARA SAIR ==========".light_red.bold
  gets # Aguarda o usuário pressionar Enter
end

# Pega argumentos da linha de comando ou usa valores padrão
target = ARGV[0]
start_port = ARGV[1] ? ARGV[1].to_i : nil
end_port = ARGV[2] ? ARGV[2].to_i : nil

begin
  main(target, start_port, end_port)
rescue Interrupt
  puts "\nScan interrompido pelo usuário".red
rescue => e
  puts "Erro: #{e.message}".red
end
