#!/bin/bash
echo ""
http --headers $1 
echo ""
host -t A $1
echo ""
