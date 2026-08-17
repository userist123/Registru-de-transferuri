"""
Tab Registru Transferuri Militare - Vizualizare, Filtrare Multi-Criteriala & Audit Integritate
Conformitate: HG 585/2002, NATO AC/35, Decizia 2013/488/UE.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox,
    QInputDialog, QFileDialog, QHeaderView, QLabel, QGroupBox,
    QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from ui.theme import CLASSIFICATION_COLORS, NATO_COLORS
from services.export_service import ExportService


class TabRegistru(QWidget):
    def __init__(self, db_manager, operator):
        super().__init__()
        self.db = db_manager
        self.operator = operator
        self.current_transfers = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # 1. Filter Bar
        filter_box = QGroupBox("🔍 Filtrare Registru Date Militare")
        filter_layout = QHBoxLayout(filter_box)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("Caută după nr. registru, instituție, persoană, serie mediu, curier...")
        self.inp_search.textChanged.connect(self.refresh)
        filter_layout.addWidget(self.inp_search, stretch=2)

        self.combo_clasificare = QComboBox()
        self.combo_clasificare.addItem("Toate clasificările", "")
        for clf in self.db.CLASSIFICATION_LEVELS:
            self.combo_clasificare.addItem(clf, clf)
        self.combo_clasificare.currentIndexChanged.connect(self.refresh)
        filter_layout.addWidget(self.combo_clasificare)

        self.combo_directie = QComboBox()
        self.combo_directie.addItem("Toate direcțiile", "")
        self.combo_directie.addItem("📤 Ieșire (Outbound)", "iesire")
        self.combo_directie.addItem("📥 Intrare (Inbound)", "intrare")
        self.combo_directie.addItem("🔄 Tranzit", "tranzit")
        self.combo_directie.currentIndexChanged.connect(self.refresh)
        filter_layout.addWidget(self.combo_directie)

        self.combo_status = QComboBox()
        self.combo_status.addItem("Toate statusurile", "")
        self.combo_status.addItem("Active", "activ")
        self.combo_status.addItem("Anulate", "anulat")
        self.combo_status.currentIndexChanged.connect(self.refresh)
        filter_layout.addWidget(self.combo_status)

        btn_ref = QPushButton("🔄 Reîmprospătează")
        btn_ref.clicked.connect(self.refresh)
        filter_layout.addWidget(btn_ref)

        main_layout.addWidget(filter_box)

        # 2. Main Table & Inspector (Splitter)
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Nr. Registru (HG 585)", "Data & Ora", "Direcție", "Clasificare Națională", "Echivalent NATO",
            "Sursă", "Destinație", "Persoană / Curier", "Mediu / Serie", "Status & Semnături"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.table)

        # Inspector Card
        self.inspector_box = QGroupBox("📋 Detalii Înregistrare & Verificare Criptografică Integritate")
        insp_layout = QVBoxLayout(self.inspector_box)
        self.txt_inspector = QTextEdit()
        self.txt_inspector.setReadOnly(True)
        self.txt_inspector.setMaximumHeight(150)
        self.txt_inspector.setStyleSheet("background-color: #0d1117; font-family: 'Consolas', monospace; font-size: 12px;")
        insp_layout.addWidget(self.txt_inspector)
        splitter.addWidget(self.inspector_box)

        splitter.setSizes([350, 150])
        main_layout.addWidget(splitter)

        # 3. Action Buttons Bar
        action_row = QHBoxLayout()
        
        btn_sign = QPushButton("✍️ Semnează Formal Transfer")
        btn_sign.setObjectName("secondary")
        btn_sign.clicked.connect(self._sign_selected)
        action_row.addWidget(btn_sign)

        btn_cancel = QPushButton("❌ Anulează Transfer")
        btn_cancel.setObjectName("danger")
        btn_cancel.clicked.connect(self._cancel_selected)
        action_row.addWidget(btn_cancel)

        action_row.addStretch()

        btn_csv = QPushButton("📤 Export CSV Securizat")
        btn_csv.clicked.connect(self._export_csv)
        action_row.addWidget(btn_csv)

        btn_html = QPushButton("🖨️ Generare Raport Oficial HTML/PDF")
        btn_html.setObjectName("primary")
        btn_html.clicked.connect(self._export_html)
        action_row.addWidget(btn_html)

        main_layout.addLayout(action_row)

        self.label_count = QLabel("")
        self.label_count.setStyleSheet("color: #8b949e; font-size: 11px;")
        main_layout.addWidget(self.label_count)

    def refresh(self):
        search = self.inp_search.text().strip()
        clasificare = self.combo_clasificare.currentData()
        directie = self.combo_directie.currentData()
        status = self.combo_status.currentData()

        self.current_transfers = self.db.get_all_transfers(search, clasificare, directie, status)
        self.table.setRowCount(len(self.current_transfers))

        for i, t in enumerate(self.current_transfers):
            # Nr registru
            nr_item = QTableWidgetItem(t.get('nr', ''))
            nr_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(i, 0, nr_item)

            # Data
            dt_str = t.get('date_created', '')
            self.table.setItem(i, 1, QTableWidgetItem(dt_str[:16].replace('T', ' ')))

            # Directie
            dir_str = t.get('directie_transfer', 'iesire').upper()
            dir_icon = "📤" if dir_str == "IESIRE" else ("📥" if dir_str == "INTRARE" else "🔄")
            self.table.setItem(i, 2, QTableWidgetItem(f"{dir_icon} {dir_str}"))

            # Clasificare
            clf = t.get('clasificare', 'Neclasificat')
            clf_item = QTableWidgetItem(clf)
            if clf in CLASSIFICATION_COLORS:
                clf_item.setForeground(QColor(CLASSIFICATION_COLORS[clf]))
            self.table.setItem(i, 3, clf_item)

            # NATO
            nato_clf = t.get('clasificare_nato', 'NATO UNCLASSIFIED')
            nato_item = QTableWidgetItem(nato_clf)
            if nato_clf in NATO_COLORS:
                nato_item.setForeground(QColor(NATO_COLORS[nato_clf]))
            self.table.setItem(i, 4, nato_item)

            self.table.setItem(i, 5, QTableWidgetItem(t.get('src_institutie', '')))
            self.table.setItem(i, 6, QTableWidgetItem(t.get('dst_institutie', '')))
            
            pers = t.get('pers_nume', '')
            if t.get('curier_militar_nume'):
                pers += f" (Curier: {t.get('curier_militar_nume')})"
            self.table.setItem(i, 7, QTableWidgetItem(pers))

            med_str = f"{t.get('transfer_medium', '')} (SN:{t.get('transfer_sn', 'N/A')})"
            self.table.setItem(i, 8, QTableWidgetItem(med_str))

            # Status & Semnat
            st_text = t.get('status', 'activ').upper()
            if t.get('semnat_operator'):
                st_text += " | ✍️ SEMNAT"
            if t.get('four_eyes_aprobator'):
                st_text += " | 👥 4-EYES"
            self.table.setItem(i, 9, QTableWidgetItem(st_text))

        self.label_count.setText(f"{len(self.current_transfers)} transferuri militare înregistrate.")
        if not self.current_transfers:
            self.txt_inspector.setPlainText("Selectați o înregistrare pentru detalii.")

    def _on_selection_changed(self):
        transfer = self._get_selected_transfer()
        if not transfer:
            self.txt_inspector.setPlainText("Selectați o înregistrare pentru detalii.")
            return

        # Compute integrity status
        expected_hash = self.db.calculate_record_hash(transfer)
        is_valid = (expected_hash == transfer.get('hash_inregistrare'))

        details = (
            f"=== TRANSFER REGISTRU: {transfer.get('nr')} ===\n"
            f"Clasificare: {transfer.get('clasificare')} | NATO: {transfer.get('clasificare_nato')} | EU: {transfer.get('clasificare_eu')}\n"
            f"Direcție: {transfer.get('directie_transfer', 'iesire').upper()} | Data Creare: {transfer.get('date_created')} | Operator: {transfer.get('operator')}\n"
            f"Traseu: [{transfer.get('src_institutie')} / {transfer.get('src_pc_nume')}] ➔ [{transfer.get('dst_institutie')} / {transfer.get('dst_pc_nume') or 'N/A'}]\n"
            f"Persoană Predare/Primire: {transfer.get('pers_nume')} ({transfer.get('pers_functie', 'N/A')} - Leg: {transfer.get('pers_legitimatie', 'N/A')})\n"
            f"Curier Militar: {transfer.get('curier_militar_nume') or 'Fără'} | Permis: {transfer.get('curier_militar_legitimatie') or 'N/A'}\n"
            f"Mediu Transfer: {transfer.get('transfer_medium')} | Serie S/N: {transfer.get('transfer_sn')} | VID:PID: {transfer.get('transfer_vid', '')}:{transfer.get('transfer_pid', '')}\n"
            f"Pachet Date: {transfer.get('arhiva_nume')} ({transfer.get('arhiva_tip')}, {transfer.get('arhiva_dim_gb', 0)} GB, {transfer.get('arhiva_fisiere', 1)} fișiere)\n"
            f"Hash SHA-256 Pachet: {transfer.get('arhiva_hash')}\n"
            f"Antivirus Offline: {transfer.get('antivirus_detalii')}\n"
            f"Bază Legală: {transfer.get('baza_legala', 'N/A')} | Nr. Aprobare: {transfer.get('nr_aprobare', 'N/A')} | Restricții: {transfer.get('restrictii', 'N/A')}\n"
            f"Aprobare Four-Eyes (4 Ochi): {transfer.get('four_eyes_aprobator') or 'N/A'} ({transfer.get('four_eyes_functie', '')} la {transfer.get('four_eyes_aprobat_la', '')})\n"
            f"Semnătură Formală: {'DA (de ' + str(transfer.get('semnat_de')) + ' la ' + str(transfer.get('semnat_la')) + ')' if transfer.get('semnat_operator') else 'NESEMNAT'}\n"
            f"Hash Înregistrare SHA-256: {transfer.get('hash_inregistrare')} [{ '✅ INTEGRITATE VALIDĂ' if is_valid else '❌ ALTERAT' }]\n"
        )
        self.txt_inspector.setPlainText(details)

    def _get_selected_transfer(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.current_transfers):
            return None
        return self.current_transfers[row]

    def _sign_selected(self):
        transfer = self._get_selected_transfer()
        if not transfer:
            QMessageBox.warning(self, "Selecție", "Selectați o înregistrare din tabel.")
            return
        pin, ok = QInputDialog.getText(self, "Confirmare Semnătură", "Introduceți PIN-ul operatorului pentru semnare oficială:",
                                        QLineEdit.EchoMode.Password)
        if not ok or not pin:
            return
        result = self.db.authenticate_operator(self.operator['id'], pin)
        if not result:
            QMessageBox.critical(self, "Eroare", "PIN incorect. Semnătura nu a fost aplicată.")
            return
        self.db.semneaza_transfer(transfer['id'], self.operator['nume'], self.operator['id'])
        QMessageBox.information(self, "Succes", f"Transferul {transfer['nr']} a fost semnat oficial.")
        self.refresh()

    def _cancel_selected(self):
        transfer = self._get_selected_transfer()
        if not transfer:
            QMessageBox.warning(self, "Selecție", "Selectați o înregistrare din tabel.")
            return
        motiv, ok = QInputDialog.getText(self, "Anulare Înregistrare", "Introduceți motivul anulării (obligatoriu conform HG 585):")
        if not ok or not motiv.strip():
            QMessageBox.warning(self, "Validare", "Motivul anulării este obligatoriu.")
            return
        self.db.anuleaza_transfer(transfer['id'], motiv.strip(), self.operator['nume'], self.operator['id'])
        QMessageBox.information(self, "Anulat", f"Transferul {transfer['nr']} a fost anulat.")
        self.refresh()

    def _export_csv(self):
        if not self.current_transfers:
            QMessageBox.warning(self, "Export", "Nu există date de exportat.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV Securizat", "registru_transferuri_militar.csv", "CSV (*.csv)")
        if path:
            ExportService.export_csv(self.current_transfers, path)
            QMessageBox.information(self, "Export", f"Export CSV finalizat cu succes:\n{path}")

    def _export_html(self):
        if not self.current_transfers:
            QMessageBox.warning(self, "Export", "Nu există date de exportat.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Raport Oficial Registru", "raport_registru_transferuri.html", "HTML (*.html)")
        if path:
            ExportService.export_html_report(self.current_transfers, path)
            QMessageBox.information(self, "Raport Generat", f"Raportul oficial a fost generat cu succes:\n{path}")
