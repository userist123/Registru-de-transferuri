DARK_STYLE = """
QWidget { background-color: #1a1d21; color: #e6e6e6; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #23272e; border: 1px solid #3a3f47; border-radius: 4px; padding: 6px; color: #f0f0f0;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #4f98a3; }
QPushButton {
    background-color: #2c3138; border: 1px solid #3a3f47; border-radius: 4px; padding: 8px 16px; color: #f0f0f0;
}
QPushButton:hover { background-color: #363c44; }
QPushButton#primary { background-color: #01696f; border: none; font-weight: 600; }
QPushButton#primary:hover { background-color: #0c4e54; }
QPushButton#danger { background-color: #a12c7b; border: none; }
QPushButton#danger:hover { background-color: #7d1e5e; }
QTableWidget { background-color: #1f2228; gridline-color: #3a3f47; border: 1px solid #3a3f47; }
QHeaderView::section { background-color: #23272e; padding: 6px; border: none; font-weight: 600; }
QTabWidget::pane { border: 1px solid #3a3f47; }
QTabBar::tab { background: #23272e; padding: 10px 18px; border: 1px solid #3a3f47; }
QTabBar::tab:selected { background: #01696f; color: white; }
QLabel#heading { font-size: 18px; font-weight: 700; color: #f0f0f0; }
QLabel#muted { color: #797876; }
"""

CLASSIFICATION_COLORS = {
    "Strict Secret de Importanță Deosebită": "#a12c7b",
    "Strict Secret": "#a13544",
    "Secret": "#da7101",
    "Secret de Serviciu": "#d19900",
    "Neclasificat": "#437a22",
}
