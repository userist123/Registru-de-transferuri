"""
Tab Punte Cognitivă & Oracol de Securitate INFOSEC (AI Memory Vault Bridge v1.0)
Integrează Registrul Militar de Transferuri cu Seiful de Memorie Cognitivă (AI_Memory_Vault_CODEX_READY):
- Oracol cognitiv offline pentru proceduri HG 585/2002, NATO AC/35, EUCI și NIST SP 800-88r2
- Sinteză automată a transferurilor finalizate în baza de memorie persistentă (conformitate P0-P15)
- Explorator semantic și căutare asociativă în Seiful de Cunoștințe
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QSplitter,
    QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from database.db import DatabaseManager
from services.cognitive_bridge_service import CognitiveBridgeService
from ui.theme import get_classification_badge_style, CLASSIFICATION_COLORS


class TabCognitiveVault(QWidget):
    def __init__(self, db_manager: DatabaseManager, operator: dict):
        super().__init__()
        self.db = db_manager
        self.operator = operator
        self.bridge = CognitiveBridgeService(db_manager)
        self.setup_ui()
        self.refresh_transfers()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # 1. Connection & Header Banner
        banner_frame = QFrame()
        banner_frame.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 10px 14px;
            }
        """)
        h_banner = QHBoxLayout(banner_frame)
        h_banner.setContentsMargins(0, 0, 0, 0)

        v_ban_title = QVBoxLayout()
        lbl_title = QLabel("🧠 Punte Cognitivă & Oracol Securitate (AI Memory Vault OS)")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #58a6ff;")
        v_ban_title.addWidget(lbl_title)

        status_text = "🟢 Conectat la Seiful de Memorie (AI_Memory_Vault_CODEX_READY | Mod WAL)" if self.bridge.is_connected() else "🟡 Mod Offline Fallback (Seif Local Activ)"
        lbl_status = QLabel(status_text)
        lbl_status.setStyleSheet("font-size: 11px; color: #3fb950; font-weight: bold;" if self.bridge.is_connected() else "font-size: 11px; color: #d29922;")
        v_ban_title.addWidget(lbl_status)
        h_banner.addLayout(v_ban_title, stretch=1)

        btn_reconnect = QPushButton("🔄 Re-sincronizează Seif")
        btn_reconnect.clicked.connect(self._reconnect_vault)
        h_banner.addWidget(btn_reconnect)

        main_layout.addWidget(banner_frame)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # 2. Card: Asistent Cognitiv & Oracol INFOSEC
        box_oracle = QGroupBox("🔮 Asistent Cognitiv INFOSEC & Interogare Proceduri Militare (Air-Gapped)")
        v_oracle = QVBoxLayout(box_oracle)

        # Quick prompt buttons
        h_chips = QHBoxLayout()
        h_chips.setSpacing(8)

        btn_chip1 = QPushButton("🛡️ Sanitizare NIST SP 800-88r2")
        btn_chip1.clicked.connect(lambda: self._ask_quick("procedura de sanitizare nist 800-88r2"))
        h_chips.addWidget(btn_chip1)

        btn_chip2 = QPushButton("📋 Numerotare HG 585 Art. 41")
        btn_chip2.clicked.connect(lambda: self._ask_quick("reguli numerotare hg 585 art 41"))
        h_chips.addWidget(btn_chip2)

        btn_chip3 = QPushButton("🌐 Grilă Clasificare NATO & UE")
        btn_chip3.clicked.connect(lambda: self._ask_quick("clasificare nato si ue echivalenta"))
        h_chips.addWidget(btn_chip3)

        btn_chip4 = QPushButton("👥 Principiul celor 4 Ochi")
        btn_chip4.clicked.connect(lambda: self._ask_quick("principiul celor 4 ochi four eyes"))
        h_chips.addWidget(btn_chip4)

        btn_chip5 = QPushButton("🔒 Politici Device Control VID/PID")
        btn_chip5.clicked.connect(lambda: self._ask_quick("reguli amprentare dispozitive vid pid"))
        h_chips.addWidget(btn_chip5)

        h_chips.addStretch()
        v_oracle.addLayout(h_chips)

        # Question input
        h_ask = QHBoxLayout()
        self.inp_question = QLineEdit()
        self.inp_question.setPlaceholderText("Adresați o întrebare despre proceduri de securitate, HG 585/2002, NATO AC/35 sau sanitizare...")
        self.inp_question.returnPressed.connect(self._ask_oracle)
        h_ask.addWidget(self.inp_question, stretch=1)

        btn_ask = QPushButton("🔎 Întreabă Oracolul")
        btn_ask.setObjectName("primary")
        btn_ask.clicked.connect(self._ask_oracle)
        h_ask.addWidget(btn_ask)
        v_oracle.addLayout(h_ask)

        # Answer display
        self.txt_answer = QTextEdit()
        self.txt_answer.setReadOnly(True)
        self.txt_answer.setMaximumHeight(140)
        self.txt_answer.setStyleSheet("background-color: #0d1117; font-size: 13px; padding: 8px; border: 1px solid #30363d; border-radius: 4px;")
        self.txt_answer.setHtml("<i>Alegeți o întrebare rapidă de mai sus sau introduceți o căutare pentru a consulta normele militare și procedurile din Seiful de Memorie.</i>")
        v_oracle.addWidget(self.txt_answer)

        splitter.addWidget(box_oracle)

        # 3. Card: Sinteza Transferuri in Seiful de Memorie
        box_sync = QGroupBox("📥 Sinteză Transferuri în Memoria Permanentă a Seifului (Propunere Canonică P0-P15)")
        v_sync = QVBoxLayout(box_sync)

        self.table_transfers = QTableWidget()
        self.table_transfers.setColumnCount(7)
        self.table_transfers.setHorizontalHeaderLabels([
            "Nr. Înregistrare", "Data", "Nivel Clasificare", "Pachet Date", "Hash SHA-256", "Mediu / S/N", "Acțiune Sinteză"
        ])
        self.table_transfers.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_transfers.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_transfers.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        v_sync.addWidget(self.table_transfers)

        splitter.addWidget(box_sync)
        splitter.setSizes([260, 320])

        main_layout.addWidget(splitter)

    def _reconnect_vault(self):
        self.bridge._init_vault_connection()
        QMessageBox.information(
            self, "Status Seif",
            f"Stare Conexiune: {'CONECTAT' if self.bridge.is_connected() else 'OFFLINE'}\n"
            f"Locație Seif: {self.bridge.vault_path}"
        )

    def _ask_quick(self, query: str):
        self.inp_question.setText(query)
        self._ask_oracle()

    def _ask_oracle(self):
        q = self.inp_question.text().strip()
        if not q:
            return
        answer = self.bridge.ask_security_oracle(q)
        self.txt_answer.setHtml(answer)

    def refresh_transfers(self):
        transfers = self.db.get_all_transfers()
        self.table_transfers.setRowCount(len(transfers))

        for i, t in enumerate(transfers):
            # Nr
            nr_item = QTableWidgetItem(t.get('nr', ''))
            nr_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table_transfers.setItem(i, 0, nr_item)

            # Data
            self.table_transfers.setItem(i, 1, QTableWidgetItem(t.get('date_created', '')[:16].replace('T', ' ')))

            # Clasificare
            clf = t.get('clasificare', 'Neclasificat')
            clf_item = QTableWidgetItem(clf)
            if clf in CLASSIFICATION_COLORS:
                clf_item.setForeground(QColor(CLASSIFICATION_COLORS[clf]))
            self.table_transfers.setItem(i, 2, clf_item)

            # Pachet date
            self.table_transfers.setItem(i, 3, QTableWidgetItem(t.get('arhiva_nume', 'N/A')))

            # Hash
            h_str = t.get('arhiva_hash', '')
            self.table_transfers.setItem(i, 4, QTableWidgetItem(f"{h_str[:12]}...{h_str[-8:]}" if len(h_str) > 20 else h_str))

            # Mediu
            med_str = f"{t.get('transfer_medium', '')} (SN: {t.get('transfer_sn', 'N/A')})"
            self.table_transfers.setItem(i, 5, QTableWidgetItem(med_str))

            # Sinteza button
            btn_synth = QPushButton("⚡ Sintetizează în Seif")
            btn_synth.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 3px 8px;")
            btn_synth.clicked.connect(lambda _, tid=t['id']: self._synthesize_transfer(tid))
            self.table_transfers.setCellWidget(i, 6, btn_synth)

    def _synthesize_transfer(self, transfer_id: str):
        success, msg = self.bridge.synthesize_transfer_to_vault_memory(transfer_id, self.operator.get('nume', 'Operator'))
        if success:
            QMessageBox.information(self, "Sinteză Reușită", msg)
        else:
            QMessageBox.critical(self, "Eroare Sinteză", msg)
