#!/bin/bash
echo "========================================"
echo "  REGISTRU TRANSFERURI MEDIA v2.0"
echo "========================================"
echo ""

echo "[1/2] Verificare Python..."
if ! command -v python3 &> /dev/null; then
    echo "EROARE: Python 3 nu este instalat!"
    echo "Instaleaza cu: sudo apt install python3"
    exit 1
fi

echo "[2/2] Pornire aplicatie..."
python3 main.py
