"""Fereastra principală"""
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QStatusBar
from PyQt6.QtCore import Qt
from ui.widgets.tab_inregistrare import TabInregistrare
from ui.widgets.stats_widget import StatsWidget

class MainWindow(QMainWindow):
    def __init__(self, db, config, operator: str):
        super().__init__()
        self.db = db
        self.config = config
        self.operator = operator
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle(f"Registru Transferuri - {self.config.get('General', 'institutie')}")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        
        central = QWidget()
        layout = QVBoxLayout(central)
        
        header = QLabel(f"📋 Registru Transferuri - Operator: {self.operator}")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 15px; background: #1a1d27; color: #e8eaf0;")
        layout.addWidget(header)
        
        tabs = QTabWidget()
        
        self.tab_inregistrare = TabInregistrare(self.db, self.operator, self.config)
        self.tab_inregistrare.transfer_saved.connect(self._on_saved)
        
        self.stats_widget = StatsWidget(self.db)
        
        tabs.addTab(self.tab_inregistrare, "📝 Înregistrare Nouă")
        tabs.addTab(self.stats_widget, "📊 Statistici")
        
        layout.addWidget(tabs)
        
        self.setCentralWidget(central)
        
        sb = QStatusBar()
        sb.showMessage("Aplicație pornită - baza de date conectată")
        self.setStatusBar(sb)
        
        self._apply_dark_theme()
    
    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #0f1117; color: #e8eaf0; font-size: 13px; }
            QTabWidget::pane { border: 1px solid #2e3144; background: #1a1d27; }
            QTabBar::tab { background: #0f1117; color: #8b91a8; padding: 8px 18px; border-bottom: 2px solid transparent; }
            QTabBar::tab:selected { color: #e8eaf0; border-bottom: 2px solid #4f7ef8; background: #1a1d27; }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background: #252836; border: 1px solid #2e3144; border-radius: 4px; padding: 6px; color: #e8eaf0;
            }
            QPushButton {
                background: #252836; border: 1px solid #2e3144; border-radius: 4px;
                padding: 7px 16px; color: #e8eaf0;
            }
            QPushButton:hover { background: #2e3350; border-color: #4f7ef8; }
            QGroupBox { border: 1px solid #2e3144; border-radius: 6px; margin-top: 8px; padding-top: 10px; color: #8b91a8; }
        """)
    
    def _on_saved(self, transfer_id: str):
        self.stats_widget.load_stats()
        self.statusBar().showMessage(f"Transfer salvat: {transfer_id[:8]}...", 3000)
