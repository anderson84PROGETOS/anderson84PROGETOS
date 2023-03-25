<?php
echo"\n";
$url = readline("Digite a URL do website para verificar o cabeçalho HEAD: "); 
echo"\n";
$user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36";
$command = "curl -s --head -A \"$user_agent\" $url";
$output = shell_exec($command);
echo $output;
?>
