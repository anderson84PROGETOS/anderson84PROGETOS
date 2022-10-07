#!/bin/bash
echo
curl -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36" -L -s $1 | grep -Poi 'http\K.*?(?=")' | awk -F/ '{print $3}' | sort -n | uniq
