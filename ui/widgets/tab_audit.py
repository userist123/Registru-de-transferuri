from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                              QPushButton, QMessageBox, QHeaderView, QLabel)
from PyQt6.QtGui import QColor


class TabAudit(QWidget):
    def __init__(self, db_manager, operator):
        super().__init__()
        self.db = db_manager
        self.operator = operator
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        btn_verify = QPushButton("🔗 Verifică Integritatea Lanțului Criptografic")
        btn_verify.setObjectName("primary")
        btn_verify.clicked.connect(self._verify_chain)
        btn_refresh = QPushButton("🔄 Reîmprospătează")
        btn_refresh.clicked.connect(self.refresh)
        top_row.addWidget(btn_verify)
        top_row.addWidget(btn_refresh)
        layout.addLayout(top_row)

        self.label_status = QLabel("")
        layout.addWidget(self.label_status)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Secv.", "Timestamp", "Acțiune", "Operator", "Detalii", "Hash Intrare"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh(self):
        rows = self.db.conn.execute(
            "SELECT * FROM audit_log ORDER BY sequence_nr DESC LIMIT 500"
        ).fetchall()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            values = [r['sequence_nr'], r['timestamp'][:19], r['actiune'], r['operator'],
                      r['detalii'] or '', r['entry_hash'][:16] + "..."]
            for j, val in enumerate(values):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))

    def _verify_chain(self):
        valid, count, error = self.db.verify_audit_chain()
        if valid:
            self.label_status.setText(f"✅ Lanț de audit VALID — {count} evenimente verificate, fără alterări.")
            self.label_status.setStyleSheet("color: #437a22; font-weight: 600;")
            QMessageBox.information(self, "Integritate Confirmată",
                                     f"Lanțul criptografic de audit este integru.\n{count} evenimente verificate.")
        else:
            self.label_status.setText(f"⚠️ ALERTĂ: {error}")
            self.label_status.setStyleSheet("color: #a13544; font-weight: 700;")
            QMessageBox.critical(self, "COMPROMITERE DETECTATĂ", f"Lanțul de audit a fost alterat!\n\n{error}")
