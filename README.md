# Registru Transferuri Media v3.1

Aplicație desktop PyQt6 pentru evidența transferurilor pe medii de stocare, conformă cu HG 585/2002.

## Noutăți v3.1 față de v2.0

- Autentificare cu PIN criptat (SHA-256 + salt) — fără operator hardcodat
- Numerotare automată `PREFIX-AN-NIVEL-NNNN` conform HG 585/2002 Art. 41, cu suport pentru toate cele 5 niveluri de clasificare
- Lanț criptografic imuabil de audit (hash chain tamper-evident), cu verificare de integritate la un click
- Hash de integritate calculat pe toate câmpurile canonice ale înregistrării (nu doar pe 2 câmpuri)
- Tab dedicat de vizualizare/căutare/filtrare a registrului existent
- Semnare formală a transferurilor cu re-confirmare PIN
- Anulare înregistrări cu motiv obligatoriu
- Inventar medii de stocare fizice + sanitizare/casare conform NIST SP 800-88 Rev. 2 / IEEE 2883-2022
- Export CSV (UTF-8 BOM) și raport oficial HTML/PDF cu casete de semnătură
- Backup automat SQLite cu rotație (păstrează ultimele 30 versiuni)
- Management operatori și roluri din tab dedicat de administrare

## Instalare

```bash
pip install -r requirements.txt
python main.py
```

## Cerințe Legale

Conform HG 585/2002, Legea 182/2002, HG 781/2002, Legea 135/2007, NIST SP 800-88 Rev. 2, IEEE 2883-2022.

## Cont Implicit

- Administrator Sistem — PIN: 123456
- Operator Registru — PIN: 111111

**Schimbați aceste PIN-uri implicite imediat după prima autentificare, din tab-ul Administrare.**
