from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                              QComboBox, QDoubleSpinBox, QPushButton, QTableWidget,
                              QTableWidgetItem, QMessageBox, QGroupBox, QHeaderView,
                              QInputDialog, QTextEdit)


TIPURI_MEDIU = ["USB Flash", "HDD Extern", "SSD Extern", "Optic (CD/DVD)", "Card SD", "Volum Criptat/Virtual"]
CLASIFICARI = ["Neclasificat", "Secret de Serviciu", "Secret", "Strict Secret", "Strict Secret de Importanță Deosebită"]
METODE_SANITIZARE = ["Clear", "Purge", "Cryptographic Erase", "Destroy"]


class TabMedii(QWidget):
    def __init__(self, db_manager, operator):
        super().__init__()
        self.db = db_manager
        self.operator = operator
        self.current_media = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        grp_add = QGroupBox("Adaugă Mediu Nou în Inventar")
        form = QFormLayout(grp_add)
        self.inp_cod = QLineEdit()
        self.inp_cod.setPlaceholderText("Ex: INV-2026-0001")
        self.inp_tip = QComboBox()
        self.inp_tip.addItems(TIPURI_MEDIU)
        self.inp_producator = QLineEdit()
        self.inp_model = QLineEdit()
        self.inp_serie = QLineEdit()
        self.inp_capacitate = QDoubleSpinBox()
        self.inp_capacitate.setMaximum(999999)
        self.inp_capacitate.setSuffix(" GB")
        self.inp_clasificare_max = QComboBox()
        self.inp_clasificare_max.addItems(CLASIFICARI)
        self.inp_locatie = QLineEdit()

        form.addRow("Cod Inventar *:", self.inp_cod)
        form.addRow("Tip Mediu:", self.inp_tip)
        form.addRow("Producător:", self.inp_producator)
        form.addRow("Model:", self.inp_model)
        form.addRow("Serie Hardware *:", self.inp_serie)
        form.addRow("Capacitate:", self.inp_capacitate)
        form.addRow("Clasificare Max.:", self.inp_clasificare_max)
        form.addRow("Locație Fizică:", self.inp_locatie)

        btn_add = QPushButton("➕ Adaugă în Inventar")
        btn_add.setObjectName("primary")
        btn_add.clicked.connect(self._add_media)
        form.addRow(btn_add)

        layout.addWidget(grp_add)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Cod Inventar", "Tip", "Producător/Model", "Serie H/W", "Clasificare Max.", "Status", "Locație"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        action_row = QHBoxLayout()
        btn_sanitize = QPushButton("🗑️ Sanitizare / Casare (NIST SP 800-88)")
        btn_sanitize.setObjectName("danger")
        btn_sanitize.clicked.connect(self._sanitize_selected)
        action_row.addWidget(btn_sanitize)
        layout.addLayout(action_row)

    def _add_media(self):
        if not self.inp_cod.text().strip() or not self.inp_serie.text().strip():
            QMessageBox.warning(self, "Validare", "Codul de inventar și seria hardware sunt obligatorii.")
            return
        data = {
            'cod_inventar': self.inp_cod.text().strip(),
            'tip_mediu': self.inp_tip.currentText(),
            'producator': self.inp_producator.text().strip(),
            'model': self.inp_model.text().strip(),
            'serie_hardware': self.inp_serie.text().strip(),
            'capacitate_gb': self.inp_capacitate.value(),
            'clasificare_max': self.inp_clasificare_max.currentText(),
            'status': 'activ',
            'locatie_fizica': self.inp_locatie.text().strip(),
            'gestionar': self.operator['nume'],
        }
        try:
            self.db.add_storage_media(data)
            QMessageBox.information(self, "Succes", "Mediu adăugat în inventar.")
            for f in [self.inp_cod, self.inp_producator, self.inp_model, self.inp_serie, self.inp_locatie]:
                f.clear()
            self.inp_capacitate.setValue(0)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Cod inventar sau serie deja existente: {e}")

    def refresh(self):
        self.current_media = self.db.get_all_media()
        self.table.setRowCount(len(self.current_media))
        for i, m in enumerate(self.current_media):
            values = [
                m.get('cod_inventar', ''), m.get('tip_mediu', ''),
                f"{m.get('producator','')} {m.get('model','')}".strip(),
                m.get('serie_hardware', ''), m.get('clasificare_max', ''),
                m.get('status', ''), m.get('locatie_fizica', '')
            ]
            for j, val in enumerate(values):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))

    def _sanitize_selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.current_media):
            QMessageBox.warning(self, "Selecție", "Selectați un mediu din tabel.")
            return
        media = self.current_media[row]
        if media['status'] in ('sanitarizat', 'distrus'):
            QMessageBox.information(self, "Info", "Acest mediu a fost deja sanitizat/distrus.")
            return

        metoda, ok = QInputDialog.getItem(self, "Metodă Sanitizare",
                                           "Selectați metoda conform NIST SP 800-88 Rev.2:",
                                           METODE_SANITIZARE, 0, False)
        if not ok:
            return
        martor, ok2 = QInputDialog.getText(self, "Martor Verificator", "Nume martor verificator (obligatoriu):")
        if not ok2 or not martor.strip():
            QMessageBox.warning(self, "Validare", "Martorul verificator este obligatoriu.")
            return

        procedura = f"Sanitizare {metoda} executată pe mediu S/N {media['serie_hardware']} conform NIST SP 800-88 Rev.2 / IEEE 2883-2022."
        cert = self.db.sanitize_media(media['id'], metoda, procedura, self.operator['nume'], martor.strip())
        QMessageBox.information(self, "Certificat Emis", f"Sanitizare finalizată.\nCertificat nr.: {cert}")
        self.refresh()
