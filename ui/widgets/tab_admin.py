from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QFormLayout, QFileDialog
)
from PyQt6.QtCore import Qt
from database.db import DatabaseManager
from services.backup_service import BackupService
from configparser import ConfigParser

class TabAdmin(QWidget):
    def __init__(self, db: DatabaseManager, operator: dict, config: ConfigParser):
        super().__init__()
        self.db = db
        self.operator = operator
        self.config = config
        self.backup_service = BackupService(str(self.db.db_path))
        self.setup_ui()
        self.load_operators()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        header = QLabel("⚙️ Administrare Sistem, Operatori & Backup")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #58a6ff;")
        layout.addWidget(header)

        box_op = QGroupBox("👥 Management Operatori & Autorizații")
        op_layout = QVBoxLayout()

        if self.operator.get('rol') == 'admin':
            add_form = QFormLayout()
            row1 = QHBoxLayout()
            self.txt_op_nume = QLineEdit()
            self.txt_op_nume.setPlaceholderText("ex: Mr. Popa Dan")
            self.txt_op_func = QLineEdit()
            self.txt_op_func.setPlaceholderText("ex: Administrator Rețea")
            row1.addWidget(QLabel("Nume Operator:"))
            row1.addWidget(self.txt_op_nume)
            row1.addWidget(QLabel("Funcție:"))
            row1.addWidget(self.txt_op_func)
            add_form.addRow(row1)

            row2 = QHBoxLayout()
            self.cb_op_clf = QComboBox()
            self.cb_op_clf.addItems([\"Neclasificat\", \"Secret de Serviciu\", \"Secret\", \"Strict Secret\", \"Strict Secret de Importanță Deosebită\"])
            self.cb_op_rol = QComboBox()
            self.cb_op_rol.addItems([\"operator\", \"operator_senior\", \"gestionar\", \"ofiter_securitate\", \"admin\"])
            self.txt_op_pin = QLineEdit()
            self.txt_op_pin.setEchoMode(QLineEdit.EchoMode.Password)
            self.txt_op_pin.setPlaceholderText(\"PIN 6 cifre\")
            row2.addWidget(QLabel(\"Nivel Clearance:\"))
            row2.addWidget(self.cb_op_clf)
            row2.addWidget(QLabel(\"Rol:\"))
            row2.addWidget(self.cb_op_rol)
            row2.addWidget(QLabel(\"PIN Initial:\"))
            row2.addWidget(self.txt_op_pin)
            add_form.addRow(row2)

            self.btn_add_op = QPushButton(\"➕ Adaugă Operator\")
            self.btn_add_op.setObjectName(\"btn_primary\")
            self.btn_add_op.clicked.connect(self._add_operator)
            add_form.addRow(\"\", self.btn_add_op)
            op_layout.addLayout(add_form)

        self.table_ops = QTableWidget()
        self.table_ops.setColumnCount(5)
        self.table_ops.setHorizontalHeaderLabels([\"Nume & Prenume\", \"Funcție\", \"Nivel Clearance\", \"Rol Sistem\", \"Stare\"])
        self.table_ops.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        op_layout.addWidget(self.table_ops)
        box_op.setLayout(op_layout)
        layout.addWidget(box_op)

        box_backup = QGroupBox(\"💾 Salvare de Siguranță & Arhivare (Backup)\")
        backup_layout = QVBoxLayout()
        
        info_backup = QLabel(\"Salvarea de siguranță conține întreaga bază de date criptografică, transferurile și jurnalele de audit.\")
        info_backup.setStyleSheet(\"color: #8b949e;\")
        backup_layout.addWidget(info_backup)

        btn_row = QHBoxLayout()
        self.btn_create_backup = QPushButton(\"📦 Creează Backup Imediat\")
        self.btn_create_backup.setObjectName(\"btn_primary\")
        self.btn_create_backup.clicked.connect(self._create_backup)
        btn_row.addWidget(self.btn_create_backup)

        self.btn_open_backup_folder = QPushButton(\"📂 Deschide Director Backup-uri\")
        self.btn_open_backup_folder.clicked.connect(self._open_backup_folder)
        btn_row.addWidget(self.btn_open_backup_folder)

        backup_layout.addLayout(btn_row)
        box_backup.setLayout(backup_layout)
        layout.addWidget(box_backup)

    def load_operators(self):
        ops = self.db.conn.execute(\"SELECT nume, functie, autorizatie, rol, activ FROM operatori ORDER BY nume ASC\").fetchall()
        self.table_ops.setRowCount(len(ops))
        for row, o in enumerate(ops):
            self.table_ops.setItem(row, 0, QTableWidgetItem(o['nume']))
            self.table_ops.setItem(row, 1, QTableWidgetItem(o['functie'] or 'N/A'))
            self.table_ops.setItem(row, 2, QTableWidgetItem(o['autorizatie']))
            self.table_ops.setItem(row, 3, QTableWidgetItem(o['rol'].upper()))
            st_item = QTableWidgetItem(\"ACTIV\" if o['activ'] else \"INACTIV\")
            st_item.setForeground(Qt.GlobalColor.green if o['activ'] else Qt.GlobalColor.red)
            self.table_ops.setItem(row, 4, st_item)

    def _add_operator(self):
        nume = self.txt_op_nume.text().strip()
        pin = self.txt_op_pin.text().strip()
        if not nume or not pin:
            QMessageBox.warning(self, \"Validare\", \"Numele și PIN-ul sunt obligatorii!\")
            return

        try:
            self.db.add_operator(
                nume, self.txt_op_func.text().strip(),
                self.cb_op_clf.currentText(), self.cb_op_rol.currentText(),
                pin, self.operator['nume']
            )
            QMessageBox.information(self, \"Succes\", f\"Operatorul {nume} a fost creat cu succes.\")
            self.txt_op_nume.clear()
            self.txt_op_func.clear()
            self.txt_op_pin.clear()
            self.load_operators()
        except Exception as e:
            QMessageBox.critical(self, \"Eroare\", str(e))

    def _create_backup(self):
        try:
            path = self.backup_service.create_backup(self.operator['nume'])
            self.db._log_audit(None, \"BACKUP\", self.operator['nume'], f\"Backup creat la {path.name}\")
            QMessageBox.information(self, \"Backup Reușit\", f\"Baza de date a fost salvată în siguranță:\\n\\n{path.name}\")
        except Exception as e:
            QMessageBox.critical(self, \"Eroare Backup\", str(e))

    def _open_backup_folder(self):
        import os, subprocess, platform
        p = str(self.backup_service.backup_dir.resolve())
        try:
            if platform.system() == \"Windows\":
                os.startfile(p)
            elif platform.system() == \"Darwin\":
                subprocess.Popen([\"open\", p])
            else:
                subprocess.Popen([\"xdg-open\", p])
        except Exception:
            QMessageBox.information(self, \"Cale Backup\", f\"Directorul de backup este:\\n{p}\")
