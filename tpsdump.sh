#!/bin/bash
echo ""
tcpdump -XXAxx src $1 -v
