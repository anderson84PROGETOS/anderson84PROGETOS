#!/bin/bash
tcpdump -nStA host $1 -E algo:secret -v 
