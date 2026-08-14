# Registru Transferuri Media v2.0

Aplicație desktop PyQt6 pentru evidența transferurilor pe medii de stocare conform HG 585/2002.

## Instalare

1. Instalare Python 3.11+ și pip
2. Instalare dependențe:
   ```bash
   pip install -r requirements.txt
   ```

3. Rulare aplicație:
   ```bash
   python3 main.py
   ```

## Funcționalități

✅ Înregistrare transferuri cu metadate complete
✅ Bază de date SQLite locală  
✅ Numerotare automată REG-YYYY-NNNN
✅ Autocomplete pentru instituții și operatori
✅ Statistici în timp real
✅ Hash SHA-256 pentru integritate
✅ Audit log complet
✅ Dark mode profesional

## Structură

```
registru-transferuri/
├── main.py                 # Entry point
├── config.ini              # Configurare
├── transferuri.db          # Bază de date (generat automat)
├── database/
│   ├── schema.sql          # Schema DB
│   └── db.py               # DatabaseManager
└── ui/
    ├── main_window.py      # Fereastra principală
    └── widgets/            # Componente UI
```

## Cerințe Legale

Conform:
- HG 585/2002 - Protecția informațiilor clasificate
- Legea 182/2002 - Informații secrete de stat
- HG 781/2002 - Informații secrete de serviciu
- Legea 135/2007 - Arhivare electronică

## Suport

Aplicație dezvoltată conform specificațiilor tehnice și juridice românești.
