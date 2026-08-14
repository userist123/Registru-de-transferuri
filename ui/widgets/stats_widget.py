"""
Stats Widget - Statistici și rapoarte
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QPushButton, QDateEdit, QTextEdit
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime

from database.db import DatabaseManager

class StatsWidget(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.load_stats()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        header = QLabel("📊 Statistici")
        header.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 15px;")
        layout.addWidget(header)
        
        # KPIs
        kpi_layout = QHBoxLayout()
        
        self.kpi_total = self._create_kpi("Total", "0", "#3b82f6")
        kpi_layout.addWidget(self.kpi_total)
        
        self.kpi_nesecret = self._create_kpi("Nesecret", "0", "#10b981")
        kpi_layout.addWidget(self.kpi_nesecret)
        
        self.kpi_secret = self._create_kpi("Secret", "0", "#ef4444")
        kpi_layout.addWidget(self.kpi_secret)
        
        self.kpi_ss = self._create_kpi("Strict Secret", "0", "#7c3aed")
        kpi_layout.addWidget(self.kpi_ss)
        
        layout.addLayout(kpi_layout)
        
        # Details
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        layout.addWidget(self.details_text)
        
        layout.addStretch()
    
    def _create_kpi(self, title: str, value: str, color: str) -> QGroupBox:
        box = QGroupBox()
        box.setStyleSheet(f"border: 2px solid {color}; border-radius: 8px; padding: 15px;")
        
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24pt; font-weight: bold; color: {color};")
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
        stats = self.db.get_stats()
        
        self._update_kpi(self.kpi_total, str(stats['total']))
        
        by_clf = stats['by_clasificare']
        self._update_kpi(self.kpi_nesecret, str(by_clf.get('Nesecret', 0)))
        self._update_kpi(self.kpi_secret, str(by_clf.get('Secret', 0)))
        self._update_kpi(self.kpi_ss, str(by_clf.get('Strict Secret', 0)))
        
        details = f"Total: {stats['total']}\n\nPe clasificare:\n"
        for clf, count in by_clf.items():
            details += f"  {clf}: {count}\n"
        
        self.details_text.setPlainText(details)

