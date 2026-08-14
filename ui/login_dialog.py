from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from database.db import DatabaseManager
from ui.theme import DARK_THEME

class LoginDialog(QDialog):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.authenticated_operator = None
        self.setup_ui()
        self.setStyleSheet(DARK_THEME)

    def setup_ui(self):
        self.setWindowTitle("Autentificare Operator - Registru Media")
        self.setFixedSize(440, 360)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel("🔐 Autentificare Operator")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #58a6ff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Sistem de Evidență Suporți Clasificați conform HG 585/2002")
        subtitle.setStyleSheet("font-size: 10pt; color: #8b949e;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #30363d;")
        layout.addWidget(line)

        lbl_op = QLabel("Selectați Operatorul:")
        lbl_op.setStyleSheet("font-weight: 600;")
        layout.addWidget(lbl_op)

        self.cb_operators = QComboBox()
        self.operators_list = self.db.get_active_operators()
        for op in self.operators_list:
            self.cb_operators.addItem(f"{op['nume']} ({op['autorizatie']})", op['id'])
        layout.addWidget(self.cb_operators)

        lbl_pin = QLabel("Cod PIN de Securitate:")
        lbl_pin.setStyleSheet("font-weight: 600;")
        layout.addWidget(lbl_pin)

        self.txt_pin = QLineEdit()
        self.txt_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pin.setPlaceholderText("Introduceți PIN-ul de 6 cifre")
        self.txt_pin.returnPressed.connect(self.attempt_login)
        layout.addWidget(self.txt_pin)

        layout.addSpacing(10)

        btn_layout = QHBoxLayout()
        self.btn_login = QPushButton("Autentificare")
        self.btn_login.setObjectName("btn_primary")
        self.btn_login.clicked.connect(self.attempt_login)
        
        self.btn_cancel = QPushButton("Ieșire")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_login)
        layout.addLayout(btn_layout)

    def attempt_login(self):
        op_id = self.cb_operators.currentData()
        pin = self.txt_pin.text().strip()

        if not pin:
            QMessageBox.warning(self, "Eroare", "Vă rugăm să introduceți codul PIN.")
            return

        op = self.db.authenticate_operator(op_id, pin)
        if op:
            self.authenticated_operator = op
            self.accept()
        else:
            QMessageBox.critical(self, "Eșec Autentificare", "Codul PIN este incorect sau contul este inactiv.")
            self.txt_pin.clear()
            self.txt_pin.setFocus()
