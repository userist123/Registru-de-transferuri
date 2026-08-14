from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit,
                              QPushButton, QMessageBox)
from PyQt6.QtCore import Qt


class LoginDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.authenticated_operator = None
        self.setWindowTitle("Autentificare Operator — Registru Transferuri Media")
        self.setFixedSize(380, 260)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("🔐 Autentificare Sistem")
        title.setObjectName("heading")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(QLabel("Operator:"))
        self.combo_operator = QComboBox()
        for op in self.db.get_active_operators():
            self.combo_operator.addItem(f"{op['nume']} ({op['rol']})", op['id'])
        layout.addWidget(self.combo_operator)

        layout.addWidget(QLabel("PIN (6 cifre):"))
        self.input_pin = QLineEdit()
        self.input_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pin.setMaxLength(6)
        self.input_pin.returnPressed.connect(self._attempt_login)
        layout.addWidget(self.input_pin)

        self.label_error = QLabel("")
        self.label_error.setStyleSheet("color: #a13544;")
        layout.addWidget(self.label_error)

        btn = QPushButton("Autentificare")
        btn.setObjectName("primary")
        btn.clicked.connect(self._attempt_login)
        layout.addWidget(btn)

    def _attempt_login(self):
        operator_id = self.combo_operator.currentData()
        pin = self.input_pin.text().strip()
        if not pin:
            self.label_error.setText("Introduceți PIN-ul.")
            return

        result = self.db.authenticate_operator(operator_id, pin)
        if result:
            self.authenticated_operator = result
            self.accept()
        else:
            self.label_error.setText("PIN incorect. Încercați din nou.")
            self.input_pin.clear()
