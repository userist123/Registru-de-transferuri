"""
Tab Administrare Sistem & Gestiune Operatori Militari (v4.3)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QHeaderView, QInputDialog, QFileDialog,
    QLabel, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from services.backup_service import BackupService


ROLURI = [
    "operator",
    "operator_senior",
    "gestionar",
    "ofiter_securitate",
    "auditor",
    "admin"
]


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
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # 1. Card: Adaugare Operator
        grp_add = QGroupBox("👤 1. Înregistrare Operator Militar Nou")
        form = QFormLayout(grp_add)
        
        self.inp_nume = QLineEdit()
        self.inp_nume.setPlaceholderText("Ex: Cpt. Popescu Dan")
        form.addRow("Nume Complet & Grad *: ", self.inp_nume)

        self.inp_functie = QLineEdit()
        self.inp_functie.setPlaceholderText("Ex: Ofițer Securitate IT / Responsabil Transferuri")
        form.addRow("Funcție & Responsabilitate: ", self.inp_functie)

        self.inp_unitate = QLineEdit("MApN / Structura Securitate")
        form.addRow("Unitate Militară: ", self.inp_unitate)

        self.inp_autorizatie = QComboBox()
        self.inp_autorizatie.addItems(self.db.CLASSIFICATION_LEVELS)
        self.inp_autorizatie.setCurrentText('Secret')
        form.addRow("Nivel Autorizare (Clearance HG 585): ", self.inp_autorizatie)

        self.inp_rol = QComboBox()
        self.inp_rol.addItems(ROLURI)
        form.addRow("Rol în Sistem: ", self.inp_rol)

        self.inp_pin = QLineEdit()
        self.inp_pin.setMaxLength(6)
        self.inp_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pin.setPlaceholderText("PIN numeric de 6 cifre")
        form.addRow("PIN Autentificare (6 cifre) *: ", self.inp_pin)

        btn_add = QPushButton("➕ Înregistrează Operator în Baza de Date")
        btn_add.setObjectName("primary")
        btn_add.clicked.connect(self._add_operator)
        form.addRow(btn_add)
        splitter.addWidget(grp_add)

        # 2. Card: Lista Operatori & Actiuni Gestiune
        grp_table = QGroupBox("👥 2. Operatori Înregistrați & Gestiune Conturi")
        v_table = QVBoxLayout(grp_table)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Nume Operator", "Funcție", "Unitate", "Rol Sistem", "Clearance Național / NATO"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        v_table.addWidget(self.table)

        h_ops_actions = QHBoxLayout()
        btn_reset_pin = QPushButton("🔑 Resetează PIN Operator")
        btn_reset_pin.setObjectName("secondary")
        btn_reset_pin.clicked.connect(self._reset_operator_pin)
        h_ops_actions.addWidget(btn_reset_pin)

        btn_deact = QPushButton("🚫 Dezactivează Cont Operator")
        btn_deact.setObjectName("danger")
        btn_deact.clicked.connect(self._deactivate_operator)
        h_ops_actions.addWidget(btn_deact)

        btn_refresh = QPushButton("🔄 Reîmprospătează")
        btn_refresh.clicked.connect(self.refresh)
        h_ops_actions.addWidget(btn_refresh)
        v_table.addLayout(h_ops_actions)

        splitter.addWidget(grp_table)

        # 3. Card: Backup & Parametri Sistem
        grp_backup = QGroupBox("💾 3. Salvare & Restaurare Backup Criptat")
        backup_row = QHBoxLayout(grp_backup)
        
        btn_backup = QPushButton("💾 Creează Backup Bază de Date")
        btn_backup.setObjectName("primary")
        btn_backup.clicked.connect(self._create_backup)
        backup_row.addWidget(btn_backup)

        btn_restore = QPushButton("📥 Restaurează din Backup")
        btn_restore.clicked.connect(self._restore_backup)
        backup_row.addWidget(btn_restore)

        lbl_station = QLabel(f"🔒 Stație Lucru Host ID: <b>{self.db.local_host}</b> | Regim: AIR-GAPPED IZOLAT")
        lbl_station.setStyleSheet("color: #58a6ff; font-size: 11px; padding-left: 15px;")
        backup_row.addWidget(lbl_station, stretch=1)

        splitter.addWidget(grp_backup)
        layout.addWidget(splitter)

    def _add_operator(self):
        nume = self.inp_nume.text().strip()
        pin = self.inp_pin.text().strip()
        if not nume or len(pin) != 6 or not pin.isdigit():
            QMessageBox.warning(self, "Validare", "Numele este obligatoriu și PIN-ul trebuie să conțină exact 6 cifre numerice.")
            return
        try:
            self.db.add_operator(
                nume, self.inp_functie.text().strip(),
                self.inp_unitate.text().strip(),
                self.inp_autorizatie.currentText(), self.inp_rol.currentText(),
                pin, self.operator['nume']
            )
            QMessageBox.information(self, "Succes", f"Operatorul [{nume}] a fost înregistrat cu succes.")
            self.inp_nume.clear()
            self.inp_functie.clear()
            self.inp_pin.clear()
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Nu s-a putut adăuga operatorul: {e}")

    def refresh(self):
        ops = self.db.get_active_operators()
        self.table.setRowCount(len(ops))
        for i, op in enumerate(ops):
            clf_str = f"{op.get('autorizatie', '')} ({op.get('autorizatie_nato', '')})"
            values = [op.get('nume', ''), op.get('functie', ''), op.get('unitate_militara', ''), op.get('rol', ''), clf_str]
            for j, val in enumerate(values):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, op['id'])

    def _get_selected_op_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _reset_operator_pin(self):
        op_id = self._get_selected_op_id()
        if not op_id:
            QMessageBox.warning(self, "Selecție", "Selectați un operator din tabel.")
            return

        new_pin, ok = QInputDialog.getText(
            self, "Resetare PIN", "Introduceți noul PIN numeric de 6 cifre pentru operator:",
            QLineEdit.EchoMode.Password
        )
        if ok and new_pin:
            if len(new_pin) != 6 or not new_pin.isdigit():
                QMessageBox.warning(self, "Eroare", "PIN-ul trebuie să aibă exact 6 cifre numerice.")
                return
            self.db.update_operator_pin(op_id, new_pin, self.operator['nume'])
            QMessageBox.information(self, "Succes", "PIN-ul operatorului a fost resetat cu succes.")

    def _deactivate_operator(self):
        op_id = self._get_selected_op_id()
        if not op_id:
            QMessageBox.warning(self, "Selecție", "Selectați un operator din tabel.")
            return
        if op_id == self.operator.get('id'):
            QMessageBox.warning(self, "Interzis", "Nu vă puteți dezactiva propriul cont de administrator logat!")
            return

        reply = QMessageBox.question(
            self, "Confirmare Dezactivare",
            "Sunteți sigur că doriți să revocați accesul acestui operator militar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.deactivate_operator(op_id, self.operator['nume'])
            QMessageBox.information(self, "Dezactivat", "Contul de operator a fost revocat.")
            self.refresh()

    def _create_backup(self):
        try:
            path = self.backup_service.create_backup()
            QMessageBox.information(self, "Backup Creat", f"Backup salvat la:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Eroare Backup", str(e))

    def _restore_backup(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selectare Fișier Backup SQLite", "", "Database Backup (*.db *.sqlite3 *.bak)")
        if path:
            reply = QMessageBox.question(
                self, "Confirmare Restaurare",
                "Atenție: Restaurarea bazei de date va suprascrie datele curente.\nContinuați?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.backup_service.restore_backup(path)
                    QMessageBox.information(self, "Succes", "Baza de date a fost restaurată. Aplicația se va sincroniza.")
                    self.refresh()
                except Exception as e:
                    QMessageBox.critical(self, "Eroare Restaurare", str(e))
