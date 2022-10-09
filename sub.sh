#!/bin/bash
echo ""
for palavra in $(cat sub.txt); do host $palavra.$1;done | grep "has address"
