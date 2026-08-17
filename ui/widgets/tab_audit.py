"""
Tab Jurnal Audit Criptografic SHA-256 Chained (v4.3)
Monitorizeaza, filtreaza si verifica integritatea lantului de audit tamper-evident.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView, QLabel, QLineEdit,
    QComboBox, QGroupBox, QTextEdit, QSplitter, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from database.db import DatabaseManager


class TabAudit(QWidget):
    def __init__(self, db_manager: DatabaseManager, operator: dict):
        super().__init__()
        self.db = db_manager
        self.operator = operator
        self.current_rows = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 1. Header & Verification Bar
        top_box = QGroupBox("🛡️ Verificare & Filtrare Jurnal de Audit Tamper-Evident (SHA-256)")
        v_top = QVBoxLayout(top_box)

        h_ctrl = QHBoxLayout()
        btn_verify = QPushButton("🔗 Verifică Integritatea Criptografică a Lanțului")
        btn_verify.setObjectName("primary")
        btn_verify.clicked.connect(self._verify_chain)
        h_ctrl.addWidget(btn_verify)

        btn_export = QPushButton("📤 Exportă Jurnal Audit (JSONL)")
        btn_export.clicked.connect(self._export_audit_jsonl)
        h_ctrl.addWidget(btn_export)

        btn_refresh = QPushButton("🔄 Reîmprospătează")
        btn_refresh.clicked.connect(self.refresh)
        h_ctrl.addWidget(btn_refresh)

        v_top.addLayout(h_ctrl)

        # Filter row
        h_filter = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("Filtrează după Acțiune, Operator sau Detalii...")
        self.inp_search.textChanged.connect(self.refresh)
        h_filter.addWidget(self.inp_search, stretch=2)

        self.cmb_actiune = QComboBox()
        self.cmb_actiune.addItem("Toate Acțiunile", "")
        for act in ["CREATE_TRANSFER", "FOUR_EYES_APPROVAL", "SIGN_TRANSFER", "CANCEL_TRANSFER", "LOGIN", "SANITIZE_MEDIA", "UPDATE_POLICY", "RENAME_MEDIA", "CREATE_OPERATOR", "RESET_PIN"]:
            self.cmb_actiune.addItem(act, act)
        self.cmb_actiune.currentIndexChanged.connect(self.refresh)
        h_filter.addWidget(self.cmb_actiune)

        v_top.addLayout(h_filter)

        self.label_status = QLabel("")
        v_top.addWidget(self.label_status)

        layout.addWidget(top_box)

        # 2. Main Audit Table & Inspector (Splitter)
        splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Secv.", "Timestamp", "Acțiune", "Operator", "Detalii Eveniment", "Hash Intrare (SHA-256)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.table)

        # Inspector Card
        box_insp = QGroupBox("📋 Inspector Criptografic Eveniment Audit (Chain Block Details)")
        v_insp = QVBoxLayout(box_insp)
        self.txt_inspector = QTextEdit()
        self.txt_inspector.setReadOnly(True)
        self.txt_inspector.setMaximumHeight(130)
        self.txt_inspector.setStyleSheet("background-color: #0d1117; font-family: 'Consolas', monospace; font-size: 12px; color: #e6edf3;")
        v_insp.addWidget(self.txt_inspector)
        splitter.addWidget(box_insp)

        splitter.setSizes([340, 140])
        layout.addWidget(splitter)

    def refresh(self):
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        
        search = self.inp_search.text().strip()
        if search:
            query += " AND (actiune LIKE ? OR operator LIKE ? OR detalii LIKE ?)"
            like = f"%{search}%"
            params += [like, like, like]
            
        act = self.cmb_actiune.currentData()
        if act:
            query += " AND actiune=?"
            params.append(act)
            
        query += " ORDER BY sequence_nr DESC LIMIT 500"
        self.current_rows = [dict(r) for r in self.db.conn.execute(query, params).fetchall()]
        
        self.table.setRowCount(len(self.current_rows))
        for i, r in enumerate(self.current_rows):
            secv_item = QTableWidgetItem(f"#{r['sequence_nr']}")
            secv_item.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            self.table.setItem(i, 0, secv_item)

            self.table.setItem(i, 1, QTableWidgetItem(r['timestamp'][:19].replace('T', ' ')))
            
            act_item = QTableWidgetItem(r['actiune'])
            act_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(i, 2, act_item)

            self.table.setItem(i, 3, QTableWidgetItem(r['operator']))
            self.table.setItem(i, 4, QTableWidgetItem(r['detalii'] or ''))
            
            h_str = r.get('entry_hash', '')
            h_short = f"{h_str[:12]}...{h_str[-8:]}" if len(h_str) > 20 else h_str
            self.table.setItem(i, 5, QTableWidgetItem(h_short))

    def _on_selection_changed(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.current_rows):
            self.txt_inspector.setPlainText("Selectați un eveniment pentru detalii criptografice.")
            return

        ev = self.current_rows[row]
        details = (
            f"=== BLOC AUDIT SECVENȚA #{ev.get('sequence_nr')} ===\n"
            f"Timestamp: {ev.get('timestamp')} | Acțiune: {ev.get('actiune')}\n"
            f"Operator: {ev.get('operator')} (ID: {ev.get('operator_id') or 'N/A'})\n"
            f"Referință Obiect: {ev.get('entity_id') or 'Sistem'}\n"
            f"Detalii: {ev.get('detalii')}\n"
            f"Hash Precedent (Chain Prev): {ev.get('previous_hash') or 'GENESIS_BLOCK'}\n"
            f"Hash Curent (Entry SHA-256): {ev.get('entry_hash')}\n"
        )
        self.txt_inspector.setPlainText(details)

    def _verify_chain(self):
        valid, count, error = self.db.verify_audit_chain()
        if valid:
            self.label_status.setText(f"✅ Lanț de audit VALID — {count} evenimente verificate criptografic, fără alterări.")
            self.label_status.setStyleSheet("color: #3fb950; font-weight: bold;")
            QMessageBox.information(self, "Integritate Confirmată",
                                     f"Lanțul criptografic de audit este 100% integru.\n{count} blocuri verificate fără discontinuități.")
        else:
            self.label_status.setText(f"⚠️ ALERTĂ: {error}")
            self.label_status.setStyleSheet("color: #f85149; font-weight: bold;")
            QMessageBox.critical(self, "COMPROMITERE DETECTATĂ", f"Lanțul de audit a fost alterat!\n\n{error}")

    def _export_audit_jsonl(self):
        rows = self.db.conn.execute("SELECT * FROM audit_log ORDER BY sequence_nr ASC").fetchall()
        if not rows:
            QMessageBox.warning(self, "Export", "Nu există evenimente de exportat.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export Jurnal Audit JSONL", "jurnal_audit_militar.jsonl", "JSON Lines (*.jsonl)")
        if path:
            import json
            with open(path, 'w', encoding='utf-8') as f:
                for r in rows:
                    f.write(json.dumps(dict(r), ensure_ascii=False) + "\n")
            QMessageBox.information(self, "Export Reușit", f"Jurnalul de audit a fost exportat cu succes:\n{path}")
