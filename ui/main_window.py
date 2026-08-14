from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QLabel
from ui.widgets.tab_inregistrare import TabInregistrare
from ui.widgets.tab_registru import TabRegistru
from ui.widgets.tab_medii import TabMedii
from ui.widgets.tab_audit import TabAudit
from ui.widgets.tab_admin import TabAdmin


class MainWindow(QMainWindow):
    def __init__(self, db_manager, operator, config):
        super().__init__()
        self.db = db_manager
        self.operator = operator
        self.config = config

        self.setWindowTitle(f"Registru Transferuri Media v3.1 — {operator['nume']} ({operator['rol']})")
        self.resize(1280, 800)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab_inregistrare = TabInregistrare(self.db, self.operator, self.config)
        self.tab_registru = TabRegistru(self.db, self.operator)
        self.tab_medii = TabMedii(self.db, self.operator)
        self.tab_audit = TabAudit(self.db, self.operator)

        self.tabs.addTab(self.tab_inregistrare, "📝 Înregistrare")
        self.tabs.addTab(self.tab_registru, "📋 Registru")
        self.tabs.addTab(self.tab_medii, "💾 Inventar Medii")
        self.tabs.addTab(self.tab_audit, "🔍 Audit")

        if operator.get('rol') == 'admin':
            self.tab_admin = TabAdmin(self.db, self.operator)
            self.tabs.addTab(self.tab_admin, "⚙️ Administrare")

        self.tab_inregistrare.transfer_saved.connect(self.tab_registru.refresh)

        status = QStatusBar()
        stats = self.db.get_statistics()
        status.addWidget(QLabel(
            f"Total: {stats['total_transferuri']} | Active: {stats['transferuri_active']} | "
            f"Medii: {stats['media_total']} | Evenimente Audit: {stats['audit_events']}"
        ))
        self.setStatusBar(status)
