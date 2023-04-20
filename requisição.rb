require 'open3'

print "\nDigite a URL do website: "
url = gets.chomp

puts ""
command = "curl -s --head -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36' #{url}"

Open3.popen3(command) do |stdin, stdout, stderr, wait_thr|
  exit_status = wait_thr.value.exitstatus

  if exit_status == 0
    puts "Requisição enviada com sucesso!"
    puts "Resposta do servidor:"
    puts stdout.read
  else
    puts "Erro ao enviar requisição."
    puts "Mensagem de erro:"
    puts stderr.read
  end
end
