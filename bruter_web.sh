#!/bin/bash

for palavra in `cat /usr/share/wordlists/dirb/small.txt`;
do

arq=`curl -I -o /dev/null -L -s -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2 Safari/537.36" -w "%{http_code}" $1/$palavra`;


dir=`curl -I -o /dev/null -L -s -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2 Safari/537.36" -w "%{http_code}" $1/$palavra/`;
 

if [ "$arq" == 200 ]; then
	echo -e "ARQUIVO ENCONTRADO: $1/$palavra"
elif [ "$dir" == 200 ]; then
	echo -e "ARQUIVO ENCONTRADO: $1/$palavra/"
else 
	echo -ne "PROCURANDO URL: $1/$palavra\e[K\r"

fi

done
