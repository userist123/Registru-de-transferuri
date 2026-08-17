"""
Fereastra Principală - Registru Militar Transferuri Media & Device Control v3.1
Conformitate: HG 585/2002, NATO AC/35, Decizia 2013/488/UE, NIST SP 800-88r2
"""
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QLabel, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from ui.widgets.tab_inregistrare import TabInregistrare
from ui.widgets.tab_registru import TabRegistru
from ui.widgets.tab_medii_amprentate import TabMediiAmprentate
from ui.widgets.stats_widget import StatsWidget
from ui.widgets.tab_audit import TabAudit
from ui.widgets.tab_admin import TabAdmin
from ui.widgets.tab_cognitive_vault import TabCognitiveVault
from ui.theme import get_classification_badge_style, CLASSIFICATION_COLORS, NATO_COLORS


class MainWindow(QMainWindow):
    def __init__(self, db_manager, operator, config):
        super().__init__()
        self.db = db_manager
        self.operator = operator
        self.config = config

        institutie = self.config.get('General', 'institutie', fallback='MINISTERUL APĂRĂRII NAȚIONALE')
        self.setWindowTitle(f"📋 Registru Militar Transferuri Date & Device Control v3.1 — {institutie}")
        self.resize(1380, 860)
        self.setMinimumSize(1150, 720)

        self._setup_ui(institutie)
        self._setup_live_timer()

    def _setup_ui(self, institutie: str):
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. TACTICAL MILITARY HEADER
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border-bottom: 2px solid #30363d;
                padding: 10px 16px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)

        # Left title & station
        v_title = QVBoxLayout()
        v_title.setSpacing(2)
        lbl_inst = QLabel(f"🇷🇴 ROMÂNIA — {institutie.upper()}")
        lbl_inst.setStyleSheet("font-size: 11px; font-weight: bold; color: #8b949e; letter-spacing: 1px;")
        v_title.addWidget(lbl_inst)

        lbl_app = QLabel("SISTEM MILITAR DE EVIDENȚĂ A TRANSFERURILOR DE DATE & DEVICE CONTROL")
        lbl_app.setStyleSheet("font-size: 15px; font-weight: 800; color: #f0f6fc;")
        v_title.addWidget(lbl_app)

        lbl_sec_context = QLabel(f"Stație: {self.db.local_host} | Regim: AIR-GAPPED IZOLAT | Standarde: HG 585/2002 • NATO AC/35 • EUCI")
        lbl_sec_context.setStyleSheet("font-size: 11px; color: #58a6ff;")
        v_title.addWidget(lbl_sec_context)

        header_layout.addLayout(v_title, stretch=2)

        # Right operator clearance badge & lock
        h_op_info = QHBoxLayout()
        h_op_info.setSpacing(12)

        v_op = QVBoxLayout()
        v_op.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        v_op.setSpacing(2)

        lbl_op_name = QLabel(f"👤 {self.operator['nume']} ({self.operator.get('functie', 'Operator')})")
        lbl_op_name.setStyleSheet("font-size: 13px; font-weight: bold; color: #f0f6fc;")
        v_op.addWidget(lbl_op_name)

        op_clf = self.operator.get('autorizatie', 'Neclasificat')
        op_nato = self.operator.get('autorizatie_nato', 'NATO UNCLASSIFIED')
        lbl_clearance = QLabel(f"Clearance: {op_clf} [{op_nato}]")
        lbl_clearance.setStyleSheet(get_classification_badge_style(op_clf))
        v_op.addWidget(lbl_clearance)

        h_op_info.addLayout(v_op)

        header_layout.addLayout(h_op_info)
        main_layout.addWidget(header_frame)

        # 2. MAIN TABS
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.tab_registru = TabRegistru(self.db, self.operator)
        self.tab_inregistrare = TabInregistrare(self.db, self.operator['nume'], self.config)
        self.tab_medii = TabMediiAmprentate(self.db, self.operator['nume'])
        self.stats_widget = StatsWidget(self.db)
        self.tab_audit = TabAudit(self.db, self.operator)
        self.tab_cognitive = TabCognitiveVault(self.db, self.operator)

        self.tabs.addTab(self.tab_registru, "📋 Registru Transferuri (Live)")
        self.tabs.addTab(self.tab_inregistrare, "➕ Înregistrare Transfer Nou")
        self.tabs.addTab(self.tab_medii, "🛡️ Medii Amprentate (Device Control)")
        self.tabs.addTab(self.tab_cognitive, "🧠 Seif Cognitiv & Oracol INFOSEC")
        self.tabs.addTab(self.stats_widget, "📊 Statistici & Conformitate")
        self.tabs.addTab(self.tab_audit, "📜 Jurnal Audit SHA-256")

        if self.operator.get('rol') in ['admin', 'ofiter_securitate']:
            self.tab_admin = TabAdmin(self.db, self.operator)
            self.tabs.addTab(self.tab_admin, "⚙️ Administrare & Operatori")

        # Connect inter-tab signals
        self.tab_inregistrare.transfer_saved.connect(self._on_transfer_saved)
        self.tab_medii.media_changed.connect(self.tab_inregistrare.refresh_available_media)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        main_layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        # 3. STATUS BAR
        self.status_bar = QStatusBar()
        self.lbl_status_stats = QLabel()
        self.lbl_status_stats.setStyleSheet("font-size: 12px; color: #8b949e; padding-left: 10px;")
        self.status_bar.addWidget(self.lbl_status_stats, stretch=1)

        self.lbl_usb_status = QLabel("🔌 Scanner USB: Activ")
        self.lbl_usb_status.setStyleSheet("font-size: 11px; color: #3fb950; font-weight: bold; padding-right: 15px;")
        self.status_bar.addPermanentWidget(self.lbl_usb_status)

        self.setStatusBar(self.status_bar)
        self._update_status_counts()

    def _setup_live_timer(self):
        # Refresh status bar every 15 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_status_counts)
        self.timer.start(15000)

    def _on_transfer_saved(self, tid: str):
        self.tab_registru.refresh()
        self.stats_widget.load_stats()
        self.tab_audit.refresh()
        self._update_status_counts()
        self.tabs.setCurrentIndex(0) # Switch to registry tab

    def _on_tab_changed(self, index: int):
        if index == 0:
            self.tab_registru.refresh()
        elif index == 1:
            self.tab_inregistrare.refresh_available_media()
        elif index == 2:
            self.tab_medii.refresh_all()
        elif index == 3:
            self.tab_cognitive.refresh_transfers()
        elif index == 4:
            self.stats_widget.load_stats()
        elif index == 5:
            self.tab_audit.refresh()
        self._update_status_counts()

    def _update_status_counts(self):
        stats = self.db.get_statistics()
        self.lbl_status_stats.setText(
            f"📊 Transferuri Totale: {stats.get('total_transferuri', 0)} | "
            f"Active: {stats.get('transferuri_active', 0)} | "
            f"Medii Amprentate: {stats.get('media_total', 0)} (RW: {stats.get('media_rw', 0)}, Blocate: {stats.get('media_blocked', 0)}) | "
            f"Evenimente Audit SHA-256: {stats.get('audit_events', 0)}"
        )
