"""
Stats Widget - Statistici de Securitate, Conformitate Militară & Device Control (v4.3)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QTextEdit, QGridLayout, QProgressBar
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
        
        header = QLabel("📊 Statistici de Securitate, Conformitate & Control Dispozitive (HG 585 / NATO / NIST)")
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

        self.kpi_volum = self._create_kpi("Volum Date Transferat", "0.0 GB", "#38bdf8")
        grid_kpi.addWidget(self.kpi_volum, 1, 2)

        self.kpi_audit = self._create_kpi("Evenimente Audit SHA-256", "0", "#8b949e")
        grid_kpi.addWidget(self.kpi_audit, 1, 3)
        
        layout.addLayout(grid_kpi)
        
        # Detailed Analytics Card
        box_det = QGroupBox("📜 Sinteză Analitică & Jurnal de Conformitate INFOSEC")
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
        value_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
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
        
        # Calculate total GB volume
        vol_gb = self.db.conn.execute("SELECT COALESCE(SUM(arhiva_dim_gb), 0) FROM transferuri WHERE status='activ'").fetchone()[0]
        self._update_kpi(self.kpi_volum, f"{vol_gb:.2f} GB")

        self._update_kpi(self.kpi_audit, str(stats.get('audit_events', 0)))
        
        # Calculate direction stats
        by_dir = stats.get('pe_directie', {})
        dir_iesire = by_dir.get('iesire', 0)
        dir_intrare = by_dir.get('intrare', 0)
        dir_tranzit = by_dir.get('tranzit', 0)
        
        # Four-eyes count
        four_eyes_count = self.db.conn.execute("SELECT COUNT(*) FROM transferuri WHERE four_eyes_aprobator IS NOT NULL AND four_eyes_aprobator != ''").fetchone()[0]
        signed_count = self.db.conn.execute("SELECT COUNT(*) FROM transferuri WHERE semnat_operator=1").fetchone()[0]
        sanitized_count = self.db.conn.execute("SELECT COUNT(*) FROM actiuni_sanitizare").fetchone()[0]
        
        details = (
            f"=== RAPORT SINTETIC DE SECURITATE & CONFORMITATE MILITARĂ ===\n"
            f"Stație Lucru Locală: {self.db.local_host} | Regim: AIR-GAPPED IZOLAT\n"
            f"Generat la: {self.db.conn.execute('SELECT datetime(\"now\", \"localtime\")').fetchone()[0]}\n\n"
            f"1. FLUX TRANSFERURI:\n"
            f"   • Total Înregistrări: {stats.get('total_transferuri', 0)} (Active: {stats.get('transferuri_active', 0)}, Anulate: {stats.get('transferuri_anulate', 0)})\n"
            f"   • Ieșire (Outbound): {dir_iesire} transferuri\n"
            f"   • Intrare (Inbound): {dir_intrare} transferuri\n"
            f"   • Tranzit: {dir_tranzit} transferuri\n"
            f"   • Volum Total Date Vehiculat: {vol_gb:.2f} GB\n\n"
            f"2. DISTRIBUȚIE DUPĂ NIVELUL DE CLASIFICARE (HG 585 / NATO AC/35 / EUCI):\n"
            f"   • Neclasificat (NATO UNCLASSIFIED): {by_clf.get('Neclasificat', 0)}\n"
            f"   • Secret de Serviciu (NATO RESTRICTED): {by_clf.get('Secret de Serviciu', 0)}\n"
            f"   • Secret (NATO CONFIDENTIAL): {by_clf.get('Secret', 0)}\n"
            f"   • Strict Secret (NATO SECRET): {by_clf.get('Strict Secret', 0)}\n"
            f"   • Strict Secret de Importanță Deosebită (COSMIC TOP SECRET): {by_clf.get('Strict Secret de Importanță Deosebită', 0)}\n\n"
            f"3. CONTROL MEDII DE STOCARE (ENDPOINT PROTECTOR MODEL):\n"
            f"   • Total Medii Amprentate în Whitelist: {stats.get('media_total', 0)}\n"
            f"   • Autorizate Read/Write (Full): {stats.get('media_rw', 0)}\n"
            f"   • Restricționate Read-Only (Doar Citire): {stats.get('media_ro', 0)}\n"
            f"   • Blocate / Revocate de Securitate: {stats.get('media_blocked', 0)}\n"
            f"   • Operațiuni de Sanitizare NIST SP 800-88r2 Executate: {sanitized_count}\n\n"
            f"4. AUDIT & PRINCIPIUL CELOR 4 OCHI (FOUR-EYES PRINCIPLE):\n"
            f"   • Transferuri Semnate Formal de Operator: {signed_count}\n"
            f"   • Transferuri Aprobate Four-Eyes (Contrasemnate): {four_eyes_count}\n"
            f"   • Evenimente Înregistrate în Lanțul Criptografic SHA-256: {stats.get('audit_events', 0)}\n"
        )
        self.details_text.setPlainText(details)
