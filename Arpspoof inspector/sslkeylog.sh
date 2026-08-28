#!/bin/bash

# ==========================================================
# SSLKEYLOGFILE + WIRESHARK
# Chromium - Kali Linux
# ==========================================================

set -u

SSL_DIR="/root/SSLKEY"
SSL_LOG="$SSL_DIR/sslkeylog.log"

echo
echo "=================================================="
echo "       SSLKEYLOGFILE - WIRESHARK / CHROMIUM"
echo "=================================================="
echo

# ----------------------------------------------------------
# Root
# ----------------------------------------------------------

if [ "$EUID" -ne 0 ]; then
    echo "[!] Execute como root."
    exit 1
fi

# ----------------------------------------------------------
# Preparar SSLKEYLOGFILE
# ----------------------------------------------------------

mkdir -p "$SSL_DIR"
touch "$SSL_LOG"
chmod 600 "$SSL_LOG"

: > "$SSL_LOG"

export SSLKEYLOGFILE="$SSL_LOG"

echo "[OK] SSLKEYLOGFILE:"
echo "     $SSLKEYLOGFILE"
echo

# ----------------------------------------------------------
# Verificar Chromium
# ----------------------------------------------------------

if ! command -v chromium >/dev/null 2>&1; then
    echo "[!] Chromium não encontrado."
    exit 1
fi

# ----------------------------------------------------------
# Fechar Chromium anterior
# ----------------------------------------------------------

echo "[+] Fechando Chromium anterior..."

pkill -TERM chromium 2>/dev/null || true
sleep 2
pkill -KILL chromium 2>/dev/null || true
sleep 1

# ----------------------------------------------------------
# Preparar perfil temporário
# ----------------------------------------------------------

CHROMIUM_PROFILE="/tmp/chromium-sslkey"

echo "[+] Criando perfil temporário..."

rm -rf "$CHROMIUM_PROFILE"
mkdir -p "$CHROMIUM_PROFILE"

# ----------------------------------------------------------
# Iniciar Chromium
# ----------------------------------------------------------

echo "[+] Iniciando Chromium..."
echo

SSLKEYLOGFILE="$SSL_LOG" \
chromium \
    --no-sandbox \
    --user-data-dir="$CHROMIUM_PROFILE" \
    >/tmp/chromium-sslkey.log 2>&1 &

LAUNCH_PID=$!

# ----------------------------------------------------------
# Aguardar Chromium
# ----------------------------------------------------------

echo
echo "[+] PID inicial: $LAUNCH_PID"
echo "[+] Aguardando o Chromium..."
echo

sleep 5

if ! kill -0 "$LAUNCH_PID" 2>/dev/null; then

    echo "[!] O Chromium encerrou."

    echo
    echo "========== LOG =========="
    cat /tmp/chromium-sslkey.log 2>/dev/null

    exit 1
fi

echo "[OK] Chromium iniciado."
echo

# ----------------------------------------------------------
# Verificar SSLKEYLOGFILE
# ----------------------------------------------------------

echo "[+] Verificando SSLKEYLOGFILE..."

ENV_OK=$(tr '\0' '\n' < "/proc/$LAUNCH_PID/environ" 2>/dev/null |
    grep '^SSLKEYLOGFILE=' || true)

if [ -n "$ENV_OK" ]; then

    echo
    echo "=================================================="
    echo "             SSLKEYLOGFILE OK"
    echo "=================================================="
    echo
    echo "$ENV_OK"
    echo

else

    echo
    echo "[!] Não foi possível verificar a variável no PID inicial."
    echo "[!] Isso não significa necessariamente que falhou."
    echo

fi

# ----------------------------------------------------------
# Monitorar arquivo
# ----------------------------------------------------------

echo "=================================================="
echo "       MONITORANDO SSLKEYLOGFILE"
echo "=================================================="
echo
echo "Arquivo:"
echo "$SSL_LOG"
echo
echo "Abra um site HTTPS no Chromium."
echo
echo "Aguardando chaves TLS..."
echo

while true; do

    if [ -f "$SSL_LOG" ]; then

        SIZE=$(stat -c%s "$SSL_LOG" 2>/dev/null || echo 0)

        if [ "$SIZE" -gt 0 ]; then

            echo
            echo "=================================================="
            echo "           CHAVES TLS DETECTADAS!"
            echo "=================================================="
            echo
            echo "Arquivo:"
            echo "$SSL_LOG"
            echo
            echo "Tamanho:"
            echo "$SIZE bytes"
            echo
            echo "Quantidade de linhas:"
            wc -l "$SSL_LOG"
            echo
            echo "Conteúdo inicial:"
            head -n 5 "$SSL_LOG"
            echo
            echo "=================================================="
            echo
            echo "No Wireshark, configure:"
            echo
            echo "$SSL_LOG"
            echo
            echo "=================================================="
            echo

            exit 0
        fi
    fi

    sleep 2

done

