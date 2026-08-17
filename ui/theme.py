"""
Tema Tactica Militara si Scheme de Culori pentru Clasificari HG 585 / NATO / EU
"""

DARK_STYLE = """
/* Background & Base Font */
QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}

/* Header & Cards */
QGroupBox {
    border: 1px solid #30363d;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: 600;
    color: #58a6ff;
    background-color: #161b22;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #161b22;
}

/* Inputs & Form Controls */
QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 7px 10px;
    color: #f0f6fc;
    selection-background-color: #1f6feb;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QSpinBox:focus {
    border: 1px solid #58a6ff;
    background-color: #111822;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
    color: #f0f6fc;
}

/* Buttons */
QPushButton {
    background-color: #21262d;
    border: 1px solid #363b42;
    border-radius: 5px;
    padding: 8px 16px;
    color: #c9d1d9;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #161b22;
}
QPushButton#primary {
    background-color: #238636;
    border: 1px solid #2ea043;
    color: #ffffff;
}
QPushButton#primary:hover {
    background-color: #2ea043;
}
QPushButton#secondary {
    background-color: #1f6feb;
    border: 1px solid #388bfd;
    color: #ffffff;
}
QPushButton#secondary:hover {
    background-color: #388bfd;
}
QPushButton#warning {
    background-color: #d29922;
    border: 1px solid #bb8009;
    color: #0d1117;
}
QPushButton#danger {
    background-color: #da3633;
    border: 1px solid #f85149;
    color: #ffffff;
}
QPushButton#danger:hover {
    background-color: #b62324;
}

/* Tables & Grids */
QTableWidget {
    background-color: #0d1117;
    gridline-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 4px;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
}
QTableWidget::item {
    padding: 6px 10px;
}
QTableWidget::item:selected {
    background-color: #1f6feb;
}
QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #30363d;
    border-right: 1px solid #21262d;
    font-weight: 700;
    font-size: 12px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #30363d;
    background-color: #161b22;
    top: -1px;
}
QTabBar::tab {
    background: #0d1117;
    color: #8b949e;
    padding: 10px 20px;
    border: 1px solid #30363d;
    border-bottom: none;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}
QTabBar::tab:hover {
    color: #f0f6fc;
    background: #161b22;
}
QTabBar::tab:selected {
    background: #161b22;
    color: #58a6ff;
    border-top: 2px solid #58a6ff;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #0d1117;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #484f58;
}
"""

CLASSIFICATION_COLORS = {
    "Strict Secret de Importanță Deosebită": "#9333ea",
    "Strict Secret de Importanta Deosebita": "#9333ea",
    "Strict Secret": "#ef4444",
    "Secret": "#f59e0b",
    "Secret de Serviciu": "#3b82f6",
    "Neclasificat": "#10b981",
}

NATO_COLORS = {
    "COSMIC TOP SECRET": "#9333ea",
    "NATO SECRET": "#ef4444",
    "NATO CONFIDENTIAL": "#f59e0b",
    "NATO RESTRICTED": "#3b82f6",
    "NATO UNCLASSIFIED": "#10b981",
}

POLICY_COLORS = {
    "autorizat_rw": ("#238636", "AUTORIZAT (R/W)"),
    "autorizat_ro": ("#1f6feb", "DOAR CITIRE (R/O)"),
    "blocat": ("#da3633", "BLOCAT / REVOCAT"),
    "in_asteptare": ("#d29922", "ÎN AȘTEPTARE APROBARE"),
    "neamprentat": ("#8b949e", "NEAMPRENTAT")
}

def get_classification_badge_style(clasificare: str) -> str:
    color = CLASSIFICATION_COLORS.get(clasificare, "#6b7280")
    return f"""
        background-color: {color}22;
        color: {color};
        border: 1px solid {color};
        border-radius: 4px;
        padding: 3px 8px;
        font-weight: bold;
        font-size: 11px;
    """

def get_policy_badge_style(policy: str) -> str:
    color, _ = POLICY_COLORS.get(policy, ("#8b949e", "NECUNOSCUT"))
    return f"""
        background-color: {color}22;
        color: {color};
        border: 1px solid {color};
        border-radius: 4px;
        padding: 3px 8px;
        font-weight: bold;
        font-size: 11px;
    """
