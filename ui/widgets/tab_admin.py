from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                              QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
                              QMessageBox, QGroupBox, QHeaderView)
from services.backup_service import BackupService


ROLURI = ["operator", "operator_senior", "gestionar", "ofiter_securitate", "auditor", "admin"]
CLASIFICARI = ["Neclasificat", "Secret de Serviciu", "Secret", "Strict Secret", "Strict Secret de Importanță Deosebită"]


class TabAdmin(QWidget):
    def __init__(self, db_manager, operator):
        super().__init__()
        self.db = db_manager
        self.operator = operator
        self.backup_service = BackupService(str(self.db.db_path))
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        grp_add = QGroupBox("Adaugă Operator Nou")
        form = QFormLayout(grp_add)
        self.inp_nume = QLineEdit()
        self.inp_functie = QLineEdit()
        self.inp_autorizatie = QComboBox()
        self.inp_autorizatie.addItems(CLASIFICARI)
        self.inp_rol = QComboBox()
        self.inp_rol.addItems(ROLURI)
        self.inp_pin = QLineEdit()
        self.inp_pin.setMaxLength(6)
        self.inp_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pin.setPlaceholderText("PIN de 6 cifre")

        form.addRow("Nume Complet *:", self.inp_nume)
        form.addRow("Funcție:", self.inp_functie)
        form.addRow("Nivel Autorizare:", self.inp_autorizatie)
        form.addRow("Rol:", self.inp_rol)
        form.addRow("PIN Inițial *:", self.inp_pin)

        btn_add = QPushButton("➕ Adaugă Operator")
        btn_add.setObjectName("primary")
        btn_add.clicked.connect(self._add_operator)
        form.addRow(btn_add)
        layout.addWidget(grp_add)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Nume", "Funcție", "Rol", "Autorizare"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        grp_backup = QGroupBox("Backup Bază de Date")
        backup_row = QHBoxLayout(grp_backup)
        btn_backup = QPushButton("💾 Creează Backup Acum")
        btn_backup.clicked.connect(self._create_backup)
        backup_row.addWidget(btn_backup)
        layout.addWidget(grp_backup)

    def _add_operator(self):
        if not self.inp_nume.text().strip() or len(self.inp_pin.text().strip()) != 6:
            QMessageBox.warning(self, "Validare", "Numele este obligatoriu și PIN-ul trebuie să aibă exact 6 cifre.")
            return
        try:
            self.db.add_operator(
                self.inp_nume.text().strip(), self.inp_functie.text().strip(),
                self.inp_autorizatie.currentText(), self.inp_rol.currentText(),
                self.inp_pin.text().strip(), self.operator['nume']
            )
            QMessageBox.information(self, "Succes", "Operator adăugat cu succes.")
            self.inp_nume.clear(); self.inp_functie.clear(); self.inp_pin.clear()
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Nu s-a putut adăuga operatorul: {e}")

    def refresh(self):
        ops = self.db.get_active_operators()
        self.table.setRowCount(len(ops))
        for i, op in enumerate(ops):
            for j, key in enumerate(['nume', 'functie', 'rol', 'autorizatie']):
                self.table.setItem(i, j, QTableWidgetItem(str(op.get(key, ''))))

    def _create_backup(self):
        try:
            path = self.backup_service.create_backup()
            QMessageBox.information(self, "Backup Creat", f"Backup salvat la:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Eroare Backup", str(e))
