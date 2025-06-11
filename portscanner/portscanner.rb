#!/usr/bin/env ruby

require 'socket'
require 'timeout'
require 'thread'
require 'colorize'

def resolve_to_ip(target)
  begin
    return Socket.getaddrinfo(target, nil, :INET)[0][3]
  rescue SocketError
    puts "Erro: Não foi possível resolver o domínio '#{target}' para um IP".red
    exit
  end
end

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

def parse_ports(input)
  ports = []

  # Ex: "21,22,23,80,443"
  if input =~ /^[\d,\s]+$/
    ports = input.split(',').map(&:strip).map(&:to_i).select { |p| p > 0 && p <= 65535 }
  # Ex: "20-1000"
  elsif input =~ /\A(\d+)-(\d+)\z/
    start_port = $1.to_i
    end_port = $2.to_i
    ports = (start_port..end_port).to_a if start_port <= end_port && start_port >= 1 && end_port <= 65535
  else
    puts "Entrada inválida de portas. Use formato '21-80' ou '21,22,23'.".red
    exit
  end

  ports
end

def main(target, ports)
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
  puts "\n\nIP: #{target_ip}".yellow

  if ports.nil? || ports.empty?
    print "\nDigite o intervalo ou lista de portas (ex: 21-65665 ou 21,22,23,53,80,111,443): ".blue
    ports_input = gets.chomp
    ports = parse_ports(ports_input)
  end

  puts "\n\nAguarde...\n\n".yellow
  open_ports = []
  max_threads = 100

  ports.each_slice(max_threads) do |batch|
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

  print "\n\n========== PRESSIONE ENTER PARA SAIR ==========".light_red.bold
  gets
end

# Entrada via argumentos
target = ARGV[0]
ports = ARGV[1] ? parse_ports(ARGV[1]) : nil

begin
  main(target, ports)
rescue Interrupt
  puts "\nScan interrompido pelo usuário".red
rescue => e
  puts "Erro: #{e.message}".red
end

