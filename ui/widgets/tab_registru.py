"""
Tab Registru Transferuri Militar - Evidență, Procese-Verbale HG 585 & Verificator Integritate la Recepție (v4.1)
"""
import os, hashlib
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QTextEdit, QSplitter, QMessageBox,
    QFileDialog, QInputDialog, QDialog, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from database.db import DatabaseManager
from services.export_service import ExportService
from ui.theme import get_classification_badge_style, CLASSIFICATION_COLORS, NATO_COLORS


class DialogProcesVerbalPreview(QDialog):
    """Fereastră de previzualizare și tipărire a Procesului-Verbal Oficial HG 585."""
    def __init__(self, transfer_data: dict, parent=None):
        super().__init__(parent)
        self.transfer_data = transfer_data
        self.setWindowTitle(f"📄 Proces-Verbal Predare-Primire {transfer_data.get('nr')} (HG 585/2002)")
        self.resize(850, 680)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.txt_html = QTextEdit()
        self.txt_html.setReadOnly(True)
        self.html_content = ExportService.generate_proces_verbal_html(self.transfer_data)
        self.txt_html.setHtml(self.html_content)
        layout.addWidget(self.txt_html)

        btns = QHBoxLayout()
        btns.addStretch()

        btn_save = QPushButton("💾 Salvează ca Fișier HTML / PDF")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._save_file)
        btns.addWidget(btn_save)

        btn_close = QPushButton("Închide")
        btn_close.clicked.connect(self.accept)
        btns.addWidget(btn_close)

        layout.addLayout(btns)

    def _save_file(self):
        default_name = f"PV_Predare_Primire_{self.transfer_data.get('nr', 'DOC').replace('/', '_').replace('-', '_')}.html"
        path, _ = QFileDialog.getSaveFileName(self, "Salvare Proces-Verbal Oficial", default_name, "HTML (*.html)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.html_content)
            QMessageBox.information(self, "Salvat", f"Procesul-Verbal a fost salvat cu succes:\n{path}")


class DialogVerifyReceiverPackage(QDialog):
    """
    Instrument de recepție și validare a integrității pachetului primit de către unitatea destinatară.
    Calculează suma SHA-256 bit-cu-bit și confirmă absența oricărei alterări a datelor.
    """
    def __init__(self, transfer_data: dict, operator_name: str, parent=None):
        super().__init__(parent)
        self.transfer_data = transfer_data
        self.operator_name = operator_name
        self.setWindowTitle(f"🔍 Verificator Pachet Recepționat — {transfer_data.get('nr')}")
        self.resize(650, 420)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel(
            f"<b>Recepție Pachet Transfer Militar:</b> {self.transfer_data.get('nr')}<br>"
            f"<b>Fișier Așteptat:</b> <code>{self.transfer_data.get('arhiva_nume')}</code> ({self.transfer_data.get('clasificare')})<br>"
            f"<b>Hash Înregistrat în Registru (SHA-256):</b><br>"
            f"<code style='color: #58a6ff;'>{self.transfer_data.get('arhiva_hash')}</code>"
        )
        info.setStyleSheet("background-color: #161b22; padding: 12px; border-radius: 6px; border: 1px solid #30363d;")
        layout.addWidget(info)

        # File picker
        h_pick = QHBoxLayout()
        self.txt_selected_file = QLineEdit()
        self.txt_selected_file.setPlaceholderText("Selectați fișierul primit de pe suportul amovibil...")
        self.txt_selected_file.setReadOnly(True)
        h_pick.addWidget(self.txt_selected_file, stretch=1)

        btn_pick = QPushButton("📁 Alege Fișier & Calculează Hash")
        btn_pick.setObjectName("secondary")
        btn_pick.clicked.connect(self._pick_and_verify)
        h_pick.addWidget(btn_pick)
        layout.addLayout(h_pick)

        # Result badge
        self.lbl_result = QLabel("Așteptare selectare fișier pentru verificare...")
        self.lbl_result.setStyleSheet("padding: 12px; border-radius: 6px; background-color: #21262d; color: #8b949e; font-weight: bold; font-size: 13px;")
        layout.addWidget(self.lbl_result)

        layout.addStretch()

        btns = QHBoxLayout()
        btns.addStretch()
        btn_close = QPushButton("Închide")
        btn_close.clicked.connect(self.reject)
        btns.addWidget(btn_close)
        layout.addLayout(btns)

    def _pick_and_verify(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selectare Fișier Recepționat pentru Verificare")
        if not file_path:
            return

        self.txt_selected_file.setText(file_path)
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            calc_hash = hasher.hexdigest().upper()
            expected_hash = (self.transfer_data.get('arhiva_hash') or '').strip().upper()

            if calc_hash == expected_hash:
                self.lbl_result.setText(
                    "✅ INTEGRITATE VERIFICATĂ & CONFIRMATĂ 100%!<br>"
                    f"Hash Calculat: <code>{calc_hash}</code><br>"
                    "Pachetul este identic bit-cu-bit cu cel înregistrat la predare. Fără alterări sau coruperi."
                )
                self.lbl_result.setStyleSheet("background-color: #0f2d1a; color: #3fb950; border: 1px solid #238636; padding: 12px; border-radius: 6px; font-size: 12px;")
            else:
                self.lbl_result.setText(
                    "❌ ALERTĂ SECURITATE: DISCREPANȚĂ HASH SHA-256!<br>"
                    f"Hash Calculat: <code>{calc_hash}</code><br>"
                    f"Hash Așteptat: <code>{expected_hash}</code><br>"
                    "<b>ATENȚIE:</b> Fișierul a fost modificat, corupt sau înlocuit!"
                )
                self.lbl_result.setStyleSheet("background-color: #3b1219; color: #f85149; border: 1px solid #da3633; padding: 12px; border-radius: 6px; font-size: 12px;")
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Nu s-a putut citi fișierul:\n{e}")


class TabRegistru(QWidget):
    def __init__(self, db: DatabaseManager, operator: dict):
        super().__init__()
        self.db = db
        self.operator = operator
        self.current_transfers = []
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # 1. Filters & Search Box
        filter_box = QGroupBox("🔍 Filtrare & Căutare Registru Transferuri")
        filter_layout = QHBoxLayout(filter_box)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("Caută după Nr. Înreg., Instituție, Persoană, S/N, Arhivă...")
        self.inp_search.textChanged.connect(self.refresh)
        filter_layout.addWidget(self.inp_search, stretch=2)

        self.combo_clasificare = QComboBox()
        self.combo_clasificare.addItem("Toate nivelurile", "")
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
        self.txt_inspector.setMaximumHeight(140)
        self.txt_inspector.setStyleSheet("background-color: #0d1117; font-family: 'Consolas', monospace; font-size: 12px;")
        insp_layout.addWidget(self.txt_inspector)
        splitter.addWidget(self.inspector_box)

        splitter.setSizes([340, 160])
        main_layout.addWidget(splitter)

        # 3. Action Buttons Bar
        action_row = QHBoxLayout()
        
        btn_pv = QPushButton("📄 Proces-Verbal Predare-Primire (HG 585)")
        btn_pv.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold;")
        btn_pv.clicked.connect(self._preview_pv)
        action_row.addWidget(btn_pv)

        btn_verify_recv = QPushButton("🔍 Verifică Pachet la Recepție (SHA-256)")
        btn_verify_recv.setStyleSheet("background-color: #238636; color: white; font-weight: bold;")
        btn_verify_recv.clicked.connect(self._verify_received_package)
        action_row.addWidget(btn_verify_recv)

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

        btn_html = QPushButton("🖨️ Raport Registru HTML")
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
            nr_item = QTableWidgetItem(t.get('nr', ''))
            nr_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(i, 0, nr_item)

            dt_str = t.get('date_created', '')
            self.table.setItem(i, 1, QTableWidgetItem(dt_str[:16].replace('T', ' ')))

            dir_str = t.get('directie_transfer', 'iesire').upper()
            dir_icon = "📤" if dir_str == "IESIRE" else ("📥" if dir_str == "INTRARE" else "🔄")
            self.table.setItem(i, 2, QTableWidgetItem(f"{dir_icon} {dir_str}"))

            clf = t.get('clasificare', 'Neclasificat')
            clf_item = QTableWidgetItem(clf)
            if clf in CLASSIFICATION_COLORS:
                clf_item.setForeground(QColor(CLASSIFICATION_COLORS[clf]))
            self.table.setItem(i, 3, clf_item)

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

    def _preview_pv(self):
        transfer = self._get_selected_transfer()
        if not transfer:
            QMessageBox.warning(self, "Selecție", "Selectați un transfer din tabel pentru a genera Procesul-Verbal.")
            return
        dlg = DialogProcesVerbalPreview(transfer, parent=self)
        dlg.exec()

    def _verify_received_package(self):
        transfer = self._get_selected_transfer()
        if not transfer:
            QMessageBox.warning(self, "Selecție", "Selectați un transfer din tabel pentru a verifica pachetul recepționat.")
            return
        dlg = DialogVerifyReceiverPackage(transfer, self.operator.get('nume', 'Operator'), parent=self)
        dlg.exec()

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
