#!/bin/bash
echo ""
for server in $(host -t ns $1 | cut -d "" -f4);
do
host -l $1 $server
done
