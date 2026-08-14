from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from configparser import ConfigParser
from database.db import DatabaseManager
from ui.widgets.tab_inregistrare import TabInregistrare
from ui.widgets.tab_registru import TabRegistru
from ui.widgets.tab_medii import TabMediiStocare
from ui.widgets.tab_audit import TabAudit
from ui.widgets.tab_admin import TabAdmin
from ui.theme import DARK_THEME

class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager, operator: dict, config: ConfigParser):
        super().__init__()
        self.db = db
        self.operator = operator
        self.config = config
        self.setup_ui()
        self.setStyleSheet(DARK_THEME)

    def setup_ui(self):
        inst_nume = self.config.get('General', 'institutie', fallback='Ministerul Apărării Naționale')
        self.setWindowTitle(f"Registru Transferuri Media v3.0 - {inst_nume}")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        
        self.tab_inreg = TabInregistrare(self.db, self.operator, self.config)
        self.tab_reg = TabRegistru(self.db, self.operator, self.config)
        self.tab_medii = TabMediiStocare(self.db, self.operator)
        self.tab_audit = TabAudit(self.db, self.operator)
        self.tab_admin = TabAdmin(self.db, self.operator, self.config)

        self.tabs.addTab(self.tab_inreg, "📝 Înregistrare Transfer")
        self.tabs.addTab(self.tab_reg, "📋 Registru Transferuri")
        self.tabs.addTab(self.tab_medii, "💽 Inventar Medii & Distrugere")
        self.tabs.addTab(self.tab_audit, "🛡️ Jurnal Audit Criptografic")
        self.tabs.addTab(self.tab_admin, "⚙️ Administrare & Backup")

        self.tab_inreg.transfer_saved.connect(self._on_transfer_saved)

        self.setCentralWidget(self.tabs)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.lbl_op_info = QLabel(f"👤 Operator Conectat: <b>{self.operator['nume']}</b> ({self.operator['rol'].upper()}) | Nivel Clearance: <span style='color: #58a6ff;'><b>{self.operator['autorizatie']}</b></span>")
        self.status.addWidget(self.lbl_op_info)

        self.lbl_sec_info = QLabel("🔒 Sistem Conformitate: HG 585/2002 | Legea 182/2002 | NIST SP 800-88")
        self.lbl_sec_info.setStyleSheet("color: #8b949e; margin-right: 15px;")
        self.status.addPermanentWidget(self.lbl_sec_info)

    def _on_transfer_saved(self, transfer_id: str):
        self.tab_reg.load_data()
        self.tab_audit.load_data()

    def closeEvent(self, event):
        self.db._log_audit(None, "LOGOUT", self.operator['nume'], f"Deconectare operator {self.operator['nume']}", op_id=self.operator['id'])
        self.db.close()
        event.accept()
