from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from database.db import DatabaseManager

class TabAudit(QWidget):
    def __init__(self, db: DatabaseManager, operator: dict):
        super().__init__()
        self.db = db
        self.operator = operator
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel("🛡️ Jurnal de Audit Criptografic (Tamper-Evident Hash Chain)")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #58a6ff;")
        layout.addWidget(header)

        status_bar = QHBoxLayout()
        self.lbl_status = QLabel("Stare Lanț Criptografic: Neverificat")
        self.lbl_status.setStyleSheet("font-weight: bold; font-size: 12px; color: #f0f6fc; padding: 6px; background: #21262d; border-radius: 4px;")
        status_bar.addWidget(self.lbl_status, 1)

        self.btn_verify = QPushButton("🔐 Verifică Integritatea Lanțului de Audit")
        self.btn_verify.setObjectName("btn_primary")
        self.btn_verify.clicked.connect(self.verify_chain)
        status_bar.addWidget(self.btn_verify)

        layout.addLayout(status_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Seq #", "Data / Ora", "Acțiune", "Operator", "Detalii Eveniment", "Amprentă Criptografică (SHA-256)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def load_data(self):
        rows = self.db.conn.execute("SELECT * FROM audit_log ORDER BY sequence_nr DESC LIMIT 200").fetchall()
        self.table.setRowCount(len(rows))

        for row_idx, r in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(r['sequence_nr'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(r['timestamp'][:19].replace('T', ' ')))
            
            act_item = QTableWidgetItem(r['actiune'])
            if 'FAIL' in r['actiune'] or 'CANCEL' in r['actiune']:
                act_item.setForeground(Qt.GlobalColor.red)
            elif 'SIGN' in r['actiune'] or 'CREATE' in r['actiune']:
                act_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row_idx, 2, act_item)

            self.table.setItem(row_idx, 3, QTableWidgetItem(r['operator']))
            self.table.setItem(row_idx, 4, QTableWidgetItem(r['detalii'] or ''))
            
            hash_item = QTableWidgetItem(r['entry_hash'][:16] + "...")
            hash_item.setToolTip(r['entry_hash'])
            self.table.setItem(row_idx, 5, hash_item)

    def verify_chain(self):
        valid, count, err = self.db.verify_audit_chain()
        if valid:
            self.lbl_status.setText(f"✅ Integritate Verificată: Toate cele {count} evenimente sunt autentice și nealterate.")
            self.lbl_status.setStyleSheet("font-weight: bold; font-size: 12px; color: #10b981; padding: 6px; background: #064e3b; border-radius: 4px;")
            QMessageBox.information(
                self, "Verificare Criptografică Reușită",
                f"Lanțul criptografic de audit este 100% INTACT.\\n\\n"
                f"Total evenimente verificate: {count}\\n"
                f"Nicio intrare nu a fost ștearsă, modificată sau reordonată."
            )
        else:
            self.lbl_status.setText(f"❌ ATENȚIE: Corupere detectată! {err}")
            self.lbl_status.setStyleSheet("font-weight: bold; font-size: 12px; color: #f87171; padding: 6px; background: #7f1d1d; border-radius: 4px;")
            QMessageBox.critical(
                self, "ALERTĂ DE SECURITATE",
                f"S-a detectat o anomalie în lanțul de audit!\\n\\n{err}\\n\\nPosibilă încercare de manipulare a bazei de date."
            )
