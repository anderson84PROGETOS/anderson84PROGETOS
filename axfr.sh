#!/bin/bash
dominio=$1

for ns in `dig ns $dominio +short`;
do
	dig axfr $dominio @$ns
done
