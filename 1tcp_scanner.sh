#!/bin/bash

# Usage function
usage() {
    echo "Usage: $0 <protocol> <Host> <start_port> <end_port>"
    echo "Example: $0 tcp google.com 1 80"
    exit 1
}

# Check if the number of arguments is correct
if [ "$#" -ne 4 ]; then
    usage
fi

# Loop through ports
for porta in $(seq "$3" "$4"); do
    timeout 1 bash -c "</dev/$1/$2/$porta" &>/dev/null && echo "Port $porta/$1 ------> OPEN"
    echo -ne "Scanning.... $porta/$1\e[K\r"
done
