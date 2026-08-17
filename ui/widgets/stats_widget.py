"""
Stats Widget - Statistici de Securitate, Conformitate Militara & Device Control
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QTextEdit, QGridLayout
)
from PyQt6.QtCore import Qt
from database.db import DatabaseManager


class StatsWidget(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.load_stats()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        header = QLabel("📊 Statistici de Securitate & Conformitate Militară (HG 585 / NATO / Device Control)")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #58a6ff;")
        layout.addWidget(header)
        
        # Grid KPIs
        grid_kpi = QGridLayout()
        
        self.kpi_total = self._create_kpi("Total Transferuri", "0", "#58a6ff")
        grid_kpi.addWidget(self.kpi_total, 0, 0)
        
        self.kpi_secret = self._create_kpi("Secret / NATO CONFIDENTIAL", "0", "#f59e0b")
        grid_kpi.addWidget(self.kpi_secret, 0, 1)
        
        self.kpi_ss = self._create_kpi("Strict Secret / NATO SECRET", "0", "#ef4444")
        grid_kpi.addWidget(self.kpi_ss, 0, 2)
        
        self.kpi_ssid = self._create_kpi("SSID / COSMIC TOP SECRET", "0", "#9333ea")
        grid_kpi.addWidget(self.kpi_ssid, 0, 3)

        self.kpi_media_total = self._create_kpi("Medii Amprentate", "0", "#238636")
        grid_kpi.addWidget(self.kpi_media_total, 1, 0)

        self.kpi_media_blocked = self._create_kpi("Medii Blocate/Revocate", "0", "#da3633")
        grid_kpi.addWidget(self.kpi_media_blocked, 1, 1)

        self.kpi_sanitizari = self._create_kpi("Sanitizări NIST 800-88", "0", "#1f6feb")
        grid_kpi.addWidget(self.kpi_sanitizari, 1, 2)

        self.kpi_audit = self._create_kpi("Evenimente Audit SHA-256", "0", "#8b949e")
        grid_kpi.addWidget(self.kpi_audit, 1, 3)
        
        layout.addLayout(grid_kpi)
        
        # Detailed Analytics Card
        box_det = QGroupBox("📜 Sinteză Analitică & Jurnal de Conformitate")
        v_det = QVBoxLayout(box_det)
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet("background-color: #0d1117; font-family: 'Consolas', monospace; font-size: 12px; color: #e6edf3;")
        v_det.addWidget(self.details_text)
        layout.addWidget(box_det)
    
    def _create_kpi(self, title: str, value: str, color: str) -> QGroupBox:
        box = QGroupBox()
        box.setStyleSheet(f"border: 1px solid {color}; border-radius: 6px; padding: 10px; background-color: #161b22;")
        
        layout = QVBoxLayout()
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #8b949e; font-size: 11px; font-weight: bold;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setObjectName("value")
        layout.addWidget(value_label)
        
        box.setLayout(layout)
        return box
    
    def _update_kpi(self, kpi_widget: QGroupBox, value: str):
        value_label = kpi_widget.findChild(QLabel, "value")
        if value_label:
            value_label.setText(value)
    
    def load_stats(self):
        stats = self.db.get_statistics()
        
        self._update_kpi(self.kpi_total, str(stats.get('total_transferuri', 0)))
        
        by_clf = stats.get('pe_clasificare', {})
        self._update_kpi(self.kpi_secret, str(by_clf.get('Secret', 0)))
        self._update_kpi(self.kpi_ss, str(by_clf.get('Strict Secret', 0)))
        self._update_kpi(self.kpi_ssid, str(by_clf.get('Strict Secret de Importanță Deosebită', 0)))
        
        self._update_kpi(self.kpi_media_total, str(stats.get('media_total', 0)))
        self._update_kpi(self.kpi_media_blocked, str(stats.get('media_blocked', 0)))
        self._update_kpi(self.kpi_sanitizari, str(stats.get('sanitizari_efectuate', 0)))
        self._update_kpi(self.kpi_audit, str(stats.get('audit_events', 0)))
        
        details = (
            f"=== RAPORT DE CONFORMITATE STATISTICA - {self.db.local_host} ===\n\n"
            f"1. EVIDENȚĂ TRANSFERURI DATE MILITARE:\n"
            f"   - Total Transferuri Înregistrate: {stats.get('total_transferuri', 0)}\n"
            f"   - Transferuri Active: {stats.get('transferuri_active', 0)}\n"
            f"   - Repartiție pe Direcții: {stats.get('pe_directie', {})}\n\n"
            f"2. REPARTIȚIE PE NIVELURI DE CLASIFICARE (HG 585/2002 / NATO AC/35):\n"
        )
        for clf, count in by_clf.items():
            nato_eq = self.db.NATO_MAP.get(clf, 'N/A')
            details += f"   * {clf.ljust(38)} [{nato_eq.ljust(22)}]: {count}\n"
        
        details += (
            f"\n3. CONTROL MEDII AMPRENTATE (ENDPOINT PROTECTOR MODEL):\n"
            f"   - Total Medii Înregistrate pe Stație : {stats.get('media_total', 0)}\n"
            f"   - Autorizate Read/Write (Full Access): {stats.get('media_rw', 0)}\n"
            f"   - Autorizate Read-Only               : {stats.get('media_ro', 0)}\n"
            f"   - Blocate / Revocate de Securitate   : {stats.get('media_blocked', 0)}\n"
            f"   - Proceduri Sanitizare NIST 800-88r2 : {stats.get('sanitizari_efectuate', 0)}\n\n"
            f"4. INTEGRITATE & AUDIT CRIPTOGRAFIC:\n"
            f"   - Evenimente Jurnalizate în Hash-Chain: {stats.get('audit_events', 0)}\n"
            f"   - Status Lanț Tamper-Evident          : VERIFICABIL LA CERERE (SHA-256)\n"
        )
        
        self.details_text.setPlainText(details)
