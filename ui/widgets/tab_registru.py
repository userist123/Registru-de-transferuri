from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
                              QTableWidget, QTableWidgetItem, QPushButton, QMessageBox,
                              QInputDialog, QFileDialog, QHeaderView, QLabel)
from ui.theme import CLASSIFICATION_COLORS
from services.export_service import ExportService
from PyQt6.QtGui import QColor


class TabRegistru(QWidget):
    def __init__(self, db_manager, operator):
        super().__init__()
        self.db = db_manager
        self.operator = operator
        self.current_transfers = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        filter_row = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("Căutare instituție, persoană, serie, nr. registru...")
        self.inp_search.textChanged.connect(self.refresh)

        self.combo_clasificare = QComboBox()
        self.combo_clasificare.addItems(["Toate clasificările", "Neclasificat", "Secret de Serviciu",
                                          "Secret", "Strict Secret", "Strict Secret de Importanță Deosebită"])
        self.combo_clasificare.currentIndexChanged.connect(self.refresh)

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Toate statusurile", "activ", "anulat", "arhivat", "suspendat"])
        self.combo_status.currentIndexChanged.connect(self.refresh)

        filter_row.addWidget(self.inp_search)
        filter_row.addWidget(self.combo_clasificare)
        filter_row.addWidget(self.combo_status)
        layout.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Nr. Registru", "Data", "Clasificare", "Sursă", "Destinație", "Persoană", "Status", "Semnat"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        action_row = QHBoxLayout()
        btn_sign = QPushButton("✍️ Semnează Selectat")
        btn_sign.clicked.connect(self._sign_selected)
        btn_cancel = QPushButton("❌ Anulează Selectat")
        btn_cancel.setObjectName("danger")
        btn_cancel.clicked.connect(self._cancel_selected)
        btn_csv = QPushButton("📤 Export CSV")
        btn_csv.clicked.connect(self._export_csv)
        btn_html = QPushButton("🖨️ Raport HTML/PDF")
        btn_html.clicked.connect(self._export_html)

        action_row.addWidget(btn_sign)
        action_row.addWidget(btn_cancel)
        action_row.addWidget(btn_csv)
        action_row.addWidget(btn_html)
        layout.addLayout(action_row)

        self.label_count = QLabel("")
        self.label_count.setObjectName("muted")
        layout.addWidget(self.label_count)

    def refresh(self):
        search = self.inp_search.text().strip()
        clasificare = self.combo_clasificare.currentText()
        clasificare = "" if clasificare == "Toate clasificările" else clasificare
        status = self.combo_status.currentText()
        status = "" if status == "Toate statusurile" else status

        self.current_transfers = self.db.get_all_transfers(search, clasificare, status)
        self.table.setRowCount(len(self.current_transfers))

        for i, t in enumerate(self.current_transfers):
            values = [
                t.get('nr', ''), t.get('date_created', '')[:10], t.get('clasificare', ''),
                t.get('src_institutie', ''), t.get('dst_institutie', ''), t.get('pers_nume', ''),
                t.get('status', ''), "DA" if t.get('semnat_operator') else "NU"
            ]
            color = CLASSIFICATION_COLORS.get(t.get('clasificare', ''), None)
            for j, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                if j == 2 and color:
                    item.setForeground(QColor(color))
                self.table.setItem(i, j, item)

        self.label_count.setText(f"{len(self.current_transfers)} înregistrări afișate")

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
        pin, ok = QInputDialog.getText(self, "Confirmare Semnătură", "Reintroduceți PIN-ul pentru semnare:",
                                        QLineEdit.EchoMode.Password)
        if not ok or not pin:
            return
        result = self.db.authenticate_operator(self.operator['id'], pin)
        if not result:
            QMessageBox.critical(self, "Eroare", "PIN incorect. Semnătura nu a fost aplicată.")
            return
        self.db.semneaza_transfer(transfer['id'], self.operator['nume'], self.operator['id'])
        QMessageBox.information(self, "Succes", f"Transfer {transfer['nr']} semnat cu succes.")
        self.refresh()

    def _cancel_selected(self):
        transfer = self._get_selected_transfer()
        if not transfer:
            QMessageBox.warning(self, "Selecție", "Selectați o înregistrare din tabel.")
            return
        motiv, ok = QInputDialog.getText(self, "Anulare Înregistrare", "Introduceți motivul anulării (obligatoriu):")
        if not ok or not motiv.strip():
            QMessageBox.warning(self, "Validare", "Motivul anulării este obligatoriu.")
            return
        self.db.anuleaza_transfer(transfer['id'], motiv.strip(), self.operator['nume'], self.operator['id'])
        QMessageBox.information(self, "Anulat", f"Transfer {transfer['nr']} anulat.")
        self.refresh()

    def _export_csv(self):
        if not self.current_transfers:
            QMessageBox.warning(self, "Export", "Nu există date de exportat.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "registru_export.csv", "CSV (*.csv)")
        if path:
            ExportService.export_csv(self.current_transfers, path)
            QMessageBox.information(self, "Export", f"Export finalizat: {path}")

    def _export_html(self):
        if not self.current_transfers:
            QMessageBox.warning(self, "Export", "Nu există date de exportat.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Raport HTML", "raport_registru.html", "HTML (*.html)")
        if path:
            ExportService.export_html_report(self.current_transfers, path)
            QMessageBox.information(self, "Raport", f"Raport generat: {path}")
