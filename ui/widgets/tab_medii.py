from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QFormLayout, QDoubleSpinBox, QInputDialog, QDialog
)
from PyQt6.QtCore import Qt
from database.db import DatabaseManager

class TabMediiStocare(QWidget):
    def __init__(self, db: DatabaseManager, operator: dict):
        super().__init__()
        self.db = db
        self.operator = operator
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel("💽 Inventar Medii de Stocare & Ciclu de Viață (NIST SP 800-88)")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #58a6ff;")
        layout.addWidget(header)

        box_add = QGroupBox("➕ Înregistrare Suport Fizic Nou în Inventar")
        form = QFormLayout()

        row1 = QHBoxLayout()
        self.txt_cod = QLineEdit()
        self.txt_cod.setPlaceholderText("ex: USB-SEC-001")
        self.cb_tip = QComboBox()
        self.cb_tip.addItems(["USB Flash Drive", "HDD Extern Securizat", "SSD Extern", "Card SD", "Mediu Optic CD/DVD", "Bandă LTO"])
        row1.addWidget(QLabel("Cod Inventar *:"), 0)
        row1.addWidget(self.txt_cod, 1)
        row1.addWidget(QLabel("Tip Mediu *:"), 0)
        row1.addWidget(self.cb_tip, 1)
        form.addRow(row1)

        row2 = QHBoxLayout()
        self.txt_sn = QLineEdit()
        self.txt_sn.setPlaceholderText("Serie unică gravată de producător")
        self.cb_clf = QComboBox()
        self.cb_clf.addItems(["Neclasificat", "Secret de Serviciu", "Secret", "Strict Secret", "Strict Secret de Importanță Deosebită"])
        row2.addWidget(QLabel("Serie Hardware (S/N) *:"), 0)
        row2.addWidget(self.txt_sn, 1)
        row2.addWidget(QLabel("Clasificare Maximă Admisă:"), 0)
        row2.addWidget(self.cb_clf, 1)
        form.addRow(row2)

        row3 = QHBoxLayout()
        self.sp_cap = QDoubleSpinBox()
        self.sp_cap.setRange(1, 100000)
        self.sp_cap.setValue(64)
        self.sp_cap.setSuffix(" GB")
        self.txt_loc = QLineEdit()
        self.txt_loc.setPlaceholderText("ex: Casă de bani Birou Securitate, Raft 2")
        row3.addWidget(QLabel("Capacitate:"), 0)
        row3.addWidget(self.sp_cap, 1)
        row3.addWidget(QLabel("Locație Fizică:"), 0)
        row3.addWidget(self.txt_loc, 1)
        form.addRow(row3)

        self.btn_add = QPushButton("📥 Înregistrează Suport în Inventar")
        self.btn_add.setObjectName("btn_primary")
        self.btn_add.clicked.connect(self._add_medium)
        form.addRow("", self.btn_add)

        box_add.setLayout(form)
        layout.addWidget(box_add)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Cod Inventar", "Tip Suport", "Serie Hardware (S/N)", "Capacitate",
            "Nivel Clasificare Max", "Locație Depozitare", "Status Ciclu Viață"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        btn_box = QHBoxLayout()
        
        self.btn_sanitize = QPushButton("🔥 Sanitarizare / Ștergere Sigură (Purge/Clear)")
        self.btn_sanitize.clicked.connect(self._sanitize_action)
        btn_box.addWidget(self.btn_sanitize)

        self.btn_destroy = QPushButton("💥 Casare & Distrugere Fizică (NIST Destroy)")
        self.btn_destroy.setObjectName("btn_danger")
        self.btn_destroy.clicked.connect(self._destroy_action)
        btn_box.addWidget(self.btn_destroy)

        btn_box.addStretch()
        btn_refresh = QPushButton("🔄 Reîmprospătează")
        btn_refresh.clicked.connect(self.load_data)
        btn_box.addWidget(btn_refresh)

        layout.addLayout(btn_box)

    def load_data(self):
        media = self.db.get_all_media()
        self.table.setRowCount(len(media))

        for row, m in enumerate(media):
            self.table.setItem(row, 0, QTableWidgetItem(m['cod_inventar']))
            self.table.setItem(row, 1, QTableWidgetItem(m['tip_mediu']))
            self.table.setItem(row, 2, QTableWidgetItem(m['serie_hardware']))
            self.table.setItem(row, 3, QTableWidgetItem(f"{m['capacitate_gb']} GB"))
            self.table.setItem(row, 4, QTableWidgetItem(m['clasificare_max']))
            self.table.setItem(row, 5, QTableWidgetItem(m['locatie_fizica'] or 'N/A'))
            
            st_item = QTableWidgetItem(m['status'].upper())
            if m['status'] == 'activ':
                st_item.setForeground(Qt.GlobalColor.green)
            elif m['status'] in ('distrus', 'sanitarizat'):
                st_item.setForeground(Qt.GlobalColor.red)
            else:
                st_item.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 6, st_item)

            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, m['id'])

    def _add_medium(self):
        cod = self.txt_cod.text().strip()
        sn = self.txt_sn.text().strip()
        if not cod or not sn:
            QMessageBox.warning(self, "Validare", "Codul de inventar și seria hardware sunt obligatorii!")
            return

        data = {
            'cod_inventar': cod,
            'tip_mediu': self.cb_tip.currentText(),
            'serie_hardware': sn,
            'capacitate_gb': self.sp_cap.value(),
            'clasificare_max': self.cb_clf.currentText(),
            'locatie_fizica': self.txt_loc.text().strip() or None,
            'gestionar': self.operator['nume'],
            'status': 'activ'
        }

        try:
            self.db.add_storage_medium(data, self.operator['nume'])
            QMessageBox.information(self, "Succes", f"Suportul {cod} a fost înregistrat în inventar.")
            self.txt_cod.clear()
            self.txt_sn.clear()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare: {str(e)}")

    def _sanitize_action(self):
        sel = self.table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Atenție", "Selectați un suport din tabel.")
            return
        med_id = self.table.item(sel, 0).data(Qt.ItemDataRole.UserRole)
        cod = self.table.item(sel, 0).text()

        martor, ok = QInputDialog.getText(self, "Sanitarizare Mediu", f"Nume Ofițer / Martor Verificator pentru {cod}:")
        if not ok or not martor.strip():
            return

        try:
            cert_nr = self.db.sanitize_medium(
                med_id, "Purge (DoD 5220.22-M / NIST 800-88)",
                "Suprascriere cu 3 treceri + verificare criptografică",
                self.operator['nume'], martor.strip(), "Comisia de Declasificare și Sanitarizare"
            )
            QMessageBox.information(self, "Sanitarizare Executată", f"Mediul {cod} a fost sanitarizat.\\n\\nCertificat Emis: {cert_nr}")
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Eroare", str(e))

    def _destroy_action(self):
        sel = self.table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Atenție", "Selectați un suport din tabel.")
            return
        med_id = self.table.item(sel, 0).data(Qt.ItemDataRole.UserRole)
        cod = self.table.item(sel, 0).text()

        reply = QMessageBox.question(
            self, "Confirmare Casare & Distrugere",
            f"Sunteți sigur că doriți să înregistrați DISTRUGEREA FIZICĂ (Dezmembrare / Demagnetizare) pentru {cod}?\\n\\nAceastă acțiune este ireversibilă!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        martor, ok = QInputDialog.getText(self, "Distrugere Fizică", f"Nume Martor Securitate pentru casarea {cod}:")
        if not ok or not martor.strip():
            return

        try:
            cert_nr = self.db.sanitize_medium(
                med_id, "Destroy (Distrugere Fizică / Shredding)",
                "Distrugere mecanică particule < 2mm conform DIN 66399 Level H-5",
                self.operator['nume'], martor.strip(), "Comisia de Casare și Distrugere Medii"
            )
            QMessageBox.information(self, "Distrugere Confirmată", f"Suportul {cod} a fost casat și distrus fizic.\\n\\nProces-Verbal Emis: {cert_nr}")
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Eroare", str(e))
