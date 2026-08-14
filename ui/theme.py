DARK_THEME = """
QMainWindow, QDialog, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', Tahoma, sans-serif;
    font-size: 13px;
}

/* Tab Bar */
QTabWidget::pane {
    border: 1px solid #30363d;
    background: #161b22;
    border-radius: 6px;
}

QTabBar::tab {
    background: #0d1117;
    color: #8b949e;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}

QTabBar::tab:selected {
    color: #58a6ff;
    background: #161b22;
    border-bottom: 2px solid #58a6ff;
}

QTabBar::tab:hover:!selected {
    background: #21262d;
    color: #c9d1d9;
}

/* Form Controls */
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 7px 10px;
    color: #f0f6fc;
    selection-background-color: #1f6feb;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #58a6ff;
    background-color: #161b22;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid #30363d;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #30363d;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 18px;
    font-weight: bold;
    color: #58a6ff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px 0 6px;
    background: #161b22;
}

/* Buttons */
QPushButton {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 18px;
    color: #f0f6fc;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
}

QPushButton:pressed {
    background-color: #161b22;
}

QPushButton#btn_primary {
    background-color: #238636;
    border-color: #2ea043;
    color: #ffffff;
}

QPushButton#btn_primary:hover {
    background-color: #2ea043;
}

QPushButton#btn_danger {
    background-color: #da3633;
    border-color: #f85149;
    color: #ffffff;
}

QPushButton#btn_danger:hover {
    background-color: #f85149;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #0d1117;
    alternate-background-color: #161b22;
    gridline-color: #30363d;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #f0f6fc;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    padding: 8px;
    border: 1px solid #30363d;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 11px;
}

/* ScrollBars */
QScrollBar:vertical {
    background: #0d1117;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background: #58a6ff;
}

/* StatusBar */
QStatusBar {
    background: #161b22;
    color: #8b949e;
    border-top: 1px solid #30363d;
}
"""

CLASIFICARE_COLORS = {
    "Neclasificat": "#8b949e",
    "Secret de Serviciu": "#d29922",
    "Secret": "#f85149",
    "Strict Secret": "#a371f7",
    "Strict Secret de Importanță Deosebită": "#ff7b72"
}
