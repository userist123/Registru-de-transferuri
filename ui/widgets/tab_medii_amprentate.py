"""
Tab Medii Amprentate - Endpoint Protector Device Control & Whitelist
Gestiune amprente hardware legate de statie, scanare PnP live si control politici acces.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QLineEdit, QComboBox, QGroupBox, QDialog, QFormLayout,
    QDoubleSpinBox, QTextEdit, QMenu, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from database.db import DatabaseManager
from services.device_control_service import DeviceControlService
from ui.theme import get_classification_badge_style, get_policy_badge_style, POLICY_COLORS, CLASSIFICATION_COLORS


class DialogAmprentareMediu(QDialog):
    def __init__(self, db: DatabaseManager, operator_name: str, prefill_dev: dict = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.operator_name = operator_name
        self.prefill = prefill_dev or {}
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("🛡️ Amprentare Mediu de Stocare pe această Stație")
        self.setMinimumWidth(550)
        layout = QVBoxLayout(self)

        info = QLabel("Amprentarea leagă identitatea hardware unică a mediului de această stație de lucru militară.")
        info.setStyleSheet("color: #8b949e; margin-bottom: 10px;")
        layout.addWidget(info)

        form = QFormLayout()

        self.txt_cod = QLineEdit()
        self.txt_cod.setPlaceholderText("Auto-generat dacă este lăsat gol (ex: AMP-2026-A1B2)")
        form.addRow("Cod Inventar Militar:", self.txt_cod)

        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(['Stick USB', 'SSD Extern', 'HDD Extern', 'Mediu Optic Securizat (CD/DVD/BD)', 'Card SD / MicroSD', 'Alt Mediu Amovibil'])
        if self.prefill.get('tip_mediu'):
            self.cmb_tip.setCurrentText(self.prefill['tip_mediu'])
        form.addRow("Tip Mediu:", self.cmb_tip)

        self.txt_prod = QLineEdit(self.prefill.get('producator', ''))
        form.addRow("Producător:", self.txt_prod)

        self.txt_model = QLineEdit(self.prefill.get('model', ''))
        form.addRow("Model Hardware:", self.txt_model)

        self.txt_vid = QLineEdit(self.prefill.get('vid', '0781'))
        self.txt_vid.setMaxLength(4)
        form.addRow("Vendor ID (VID): *", self.txt_vid)

        self.txt_pid = QLineEdit(self.prefill.get('pid', '5583'))
        self.txt_pid.setMaxLength(4)
        form.addRow("Product ID (PID): *", self.txt_pid)

        self.txt_sn = QLineEdit(self.prefill.get('serial_number', ''))
        form.addRow("Serie Hardware (S/N): *", self.txt_sn)

        self.spn_cap = QDoubleSpinBox()
        self.spn_cap.setRange(0.1, 100000.0)
        self.spn_cap.setValue(float(self.prefill.get('capacitate_gb', 32.0)))
        self.spn_cap.setSuffix(" GB")
        form.addRow("Capacitate:", self.spn_cap)

        self.cmb_clf = QComboBox()
        self.cmb_clf.addItems(self.db.CLASSIFICATION_LEVELS)
        self.cmb_clf.setCurrentText('Secret')
        form.addRow("Plafon Maxim Clasificare (HG 585): *", self.cmb_clf)

        self.cmb_politica = QComboBox()
        self.cmb_politica.addItem("Autorizat Complet (Read / Write)", "autorizat_rw")
        self.cmb_politica.addItem("Doar Citire (Read-Only)", "autorizat_ro")
        self.cmb_politica.addItem("În Așteptare Aprobare INFOSEC", "in_asteptare")
        self.cmb_politica.addItem("Blocat / Revocat", "blocat")
        form.addRow("Politică Acces Inițială: *", self.cmb_politica)

        self.cmb_cript = QComboBox()
        self.cmb_cript.addItems(['Fara', 'BitLocker To Go (AES-256)', 'Hardware SED Opal 2.0', 'Criptare Criptografică Omologată ORNISS'])
        form.addRow("Stare Criptare:", self.cmb_cript)

        self.txt_gestionar = QLineEdit(self.operator_name)
        form.addRow("Gestionar / Responsabil:", self.txt_gestionar)

        self.txt_unitate = QLineEdit("MApN / Structura Securitate")
        form.addRow("Unitate Militară:", self.txt_unitate)

        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(60)
        self.txt_obs.setPlaceholderText("Mențiuni conform SecOPs...")
        form.addRow("Observații:", self.txt_obs)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Anulare")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Înregistrează & Amprentează")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._save_medium)
        btns.addWidget(btn_save)

        layout.addLayout(btns)

    def _save_medium(self):
        if not self.txt_vid.text().strip() or not self.txt_pid.text().strip() or not self.txt_sn.text().strip():
            QMessageBox.warning(self, "Validare", "VID, PID și Seria Hardware sunt obligatorii pentru amprentare!")
            return

        data = {
            'cod_inventar': self.txt_cod.text().strip() or None,
            'tip_mediu': self.cmb_tip.currentText(),
            'producator': self.txt_prod.text().strip(),
            'model': self.txt_model.text().strip(),
            'vid': self.txt_vid.text().strip(),
            'pid': self.txt_pid.text().strip(),
            'serie_hardware': self.txt_sn.text().strip(),
            'capacitate_gb': self.spn_cap.value(),
            'clasificare_max': self.cmb_clf.currentText(),
            'status_politica': self.cmb_politica.currentData(),
            'stare_criptare': self.cmb_cript.currentText(),
            'gestionar_nume': self.txt_gestionar.text().strip(),
            'gestionar_unitate': self.txt_unitate.text().strip(),
            'observatii': self.txt_obs.toPlainText().strip()
        }
        try:
            self.db.add_amprentat_medium(data, self.operator_name)
            QMessageBox.information(self, "Succes", f"Mediul cu seria {data['serie_hardware']} a fost amprentat pe stație!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare salvare amprentă:\n{str(e)}")


class TabMediiAmprentate(QWidget):
    media_changed = pyqtSignal()

    def __init__(self, db: DatabaseManager, operator_name: str):
        super().__init__()
        self.db = db
        self.operator_name = operator_name
        self.detector = DeviceControlService(db)
        self.detected_devices = []
        self.setup_ui()
        self.refresh_all()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Header bar
        header_layout = QHBoxLayout()
        title = QLabel("🛡️ Control Medii de Stocare Amprentate (Device Control Whitelist)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #58a6ff;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        btn_scan = QPushButton("🔍 Scanare Live Dispozitive Conectate")
        btn_scan.setObjectName("secondary")
        btn_scan.clicked.connect(self.scan_live_devices)
        header_layout.addWidget(btn_scan)

        btn_add = QPushButton("➕ Amprentează Mediu Nou Manual")
        btn_add.setObjectName("primary")
        btn_add.clicked.connect(self.open_enroll_dialog)
        header_layout.addWidget(btn_add)

        main_layout.addLayout(header_layout)

        # Top section: Live Plug & Play Detected Devices Card
        self.box_live = QGroupBox("🔌 Dispozitive Conectate Fizic în Timp Real (PnP Scanner)")
        live_layout = QVBoxLayout(self.box_live)

        self.table_live = QTableWidget()
        self.table_live.setColumnCount(8)
        self.table_live.setHorizontalHeaderLabels([
            "Literă Volum", "Model & Producător", "VID : PID", "Serie Hardware", "Capacitate / Liber", "Status Amprentă", "Plafon Clasificare", "Acțiuni"
        ])
        self.table_live.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_live.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_live.setMaximumHeight(140)
        self.table_live.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        live_layout.addWidget(self.table_live)

        main_layout.addWidget(self.box_live)

        # Bottom section: Whitelist Table
        self.box_whitelist = QGroupBox("📋 Baza de Date a Mediilor Amprentate pe această Stație")
        wl_layout = QVBoxLayout(self.box_whitelist)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("Filtru Politică:"))
        self.cmb_filter_policy = QComboBox()
        self.cmb_filter_policy.addItem("Toate Politicile", "toate")
        self.cmb_filter_policy.addItem("Autorizate R/W", "autorizat_rw")
        self.cmb_filter_policy.addItem("Doar Citire (R/O)", "autorizat_ro")
        self.cmb_filter_policy.addItem("Blocate / Revocate", "blocat")
        self.cmb_filter_policy.addItem("În Așteptare", "in_asteptare")
        self.cmb_filter_policy.currentIndexChanged.connect(self.load_whitelist)
        filter_bar.addWidget(self.cmb_filter_policy)

        filter_bar.addWidget(QLabel("Căutare:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Caută după cod inventar, serie, model, gestionar...")
        self.txt_search.textChanged.connect(self.load_whitelist)
        filter_bar.addWidget(self.txt_search)

        btn_refresh = QPushButton("🔄 Reîmprospătează")
        btn_refresh.clicked.connect(self.refresh_all)
        filter_bar.addWidget(btn_refresh)

        wl_layout.addLayout(filter_bar)

        self.table_whitelist = QTableWidget()
        self.table_whitelist.setColumnCount(9)
        self.table_whitelist.setHorizontalHeaderLabels([
            "Cod Inventar", "Tip & Model", "VID : PID", "Serie Hardware", "Capacitate", "Plafon Clasificare", "Politică Acces", "Criptare", "Gestionar / Unitate"
        ])
        self.table_whitelist.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_whitelist.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_whitelist.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_whitelist.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_whitelist.customContextMenuRequested.connect(self._show_context_menu)
        wl_layout.addWidget(self.table_whitelist)

        main_layout.addWidget(self.box_whitelist)

    def refresh_all(self):
        self.scan_live_devices()
        self.load_whitelist()

    def scan_live_devices(self):
        self.detected_devices = self.detector.scan_connected_devices()
        self.table_live.setRowCount(len(self.detected_devices))
        
        for row, dev in enumerate(self.detected_devices):
            self.table_live.setItem(row, 0, QTableWidgetItem(dev.get('drive_letter', 'N/A')))
            self.table_live.setItem(row, 1, QTableWidgetItem(f"{dev.get('producator', '')} {dev.get('model', '')}"))
            self.table_live.setItem(row, 2, QTableWidgetItem(f"{dev.get('vid', '')}:{dev.get('pid', '')}"))
            self.table_live.setItem(row, 3, QTableWidgetItem(dev.get('serial_number', '')))
            self.table_live.setItem(row, 4, QTableWidgetItem(f"{dev.get('capacitate_gb', 0)} GB (Lib: {dev.get('liber_gb', 0)} GB)"))

            # Status chip
            status_item = QTableWidgetItem()
            if dev.get('is_amprentat'):
                pol = dev.get('status_politica', 'autorizat_rw')
                _, pol_text = POLICY_COLORS.get(pol, ("#8b949e", pol))
                status_item.setText(f"✅ {pol_text}")
                status_item.setForeground(QColor(POLICY_COLORS.get(pol, ("#8b949e", ""))[0]))
            else:
                status_item.setText("⚠️ NEAMPRENTAT")
                status_item.setForeground(QColor("#f85149"))
            self.table_live.setItem(row, 5, status_item)

            # Plafon
            clf_item = QTableWidgetItem(dev.get('clasificare_max', 'N/A'))
            if dev.get('clasificare_max') in CLASSIFICATION_COLORS:
                clf_item.setForeground(QColor(CLASSIFICATION_COLORS[dev['clasificare_max']]))
            self.table_live.setItem(row, 6, clf_item)

            # Action button
            if not dev.get('is_amprentat'):
                btn_enroll = QPushButton("⚡ Amprentează")
                btn_enroll.setStyleSheet("background-color: #238636; color: white; padding: 3px 8px;")
                btn_enroll.clicked.connect(lambda _, d=dev: self.open_enroll_dialog(d))
                self.table_live.setCellWidget(row, 7, btn_enroll)
            else:
                lbl_ok = QLabel("Autorizat")
                lbl_ok.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_ok.setStyleSheet("color: #3fb950; font-weight: bold;")
                self.table_live.setCellWidget(row, 7, lbl_ok)

    def load_whitelist(self):
        policy = self.cmb_filter_policy.currentData()
        search = self.txt_search.text().strip()
        records = self.db.get_amprentate_media(status_politica=policy, search=search)
        
        self.table_whitelist.setRowCount(len(records))
        for row, r in enumerate(records):
            self.table_whitelist.setItem(row, 0, QTableWidgetItem(r['cod_inventar']))
            self.table_whitelist.setItem(row, 1, QTableWidgetItem(f"{r.get('producator', '')} {r.get('model', '')} ({r['tip_mediu']})"))
            self.table_whitelist.setItem(row, 2, QTableWidgetItem(f"{r['vid']}:{r['pid']}"))
            self.table_whitelist.setItem(row, 3, QTableWidgetItem(r['serie_hardware']))
            self.table_whitelist.setItem(row, 4, QTableWidgetItem(f"{r.get('capacitate_gb', 0)} GB"))

            # Clasificare
            clf_item = QTableWidgetItem(r['clasificare_max'])
            if r['clasificare_max'] in CLASSIFICATION_COLORS:
                clf_item.setForeground(QColor(CLASSIFICATION_COLORS[r['clasificare_max']]))
            self.table_whitelist.setItem(row, 5, clf_item)

            # Politica
            pol = r['status_politica']
            _, pol_text = POLICY_COLORS.get(pol, ("#8b949e", pol))
            pol_item = QTableWidgetItem(pol_text)
            pol_item.setForeground(QColor(POLICY_COLORS.get(pol, ("#8b949e", ""))[0]))
            self.table_whitelist.setItem(row, 6, pol_item)

            self.table_whitelist.setItem(row, 7, QTableWidgetItem(r.get('stare_criptare', 'Fara')))
            self.table_whitelist.setItem(row, 8, QTableWidgetItem(f"{r.get('gestionar_nume', '')} ({r.get('gestionar_unitate', '')})"))

            # Store ID in hidden role
            self.table_whitelist.item(row, 0).setData(Qt.ItemDataRole.UserRole, r['id'])

    def open_enroll_dialog(self, dev: dict = None):
        dlg = DialogAmprentareMediu(self.db, self.operator_name, prefill_dev=dev, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()
            self.media_changed.emit()

    def _show_context_menu(self, pos):
        item = self.table_whitelist.itemAt(pos)
        if not item:
            return
        row = item.row()
        med_id = self.table_whitelist.item(row, 0).data(Qt.ItemDataRole.UserRole)
        med = self.db.get_medium_by_id(med_id)
        if not med:
            return

        menu = QMenu(self)
        
        act_rw = menu.addAction("🟢 Setează: Autorizat Read / Write (Full Access)")
        act_ro = menu.addAction("🔵 Setează: Doar Citire (Read-Only)")
        act_block = menu.addAction("🔴 Setează: Blocat / Revocat pe această Stație")
        menu.addSeparator()
        act_sanitize = menu.addAction("🧹 Sanitizare NIST SP 800-88r2 (Clear / Purge / Destroy)")

        action = menu.exec(self.table_whitelist.viewport().mapToGlobal(pos))
        if action == act_rw:
            self.db.update_medium_policy(med_id, 'autorizat_rw', self.operator_name, "Modificare manuala operator")
            self.refresh_all()
        elif action == act_ro:
            self.db.update_medium_policy(med_id, 'autorizat_ro', self.operator_name, "Modificare restrictie Read-Only")
            self.refresh_all()
        elif action == act_block:
            self.db.update_medium_policy(med_id, 'blocat', self.operator_name, "Revocare / Blocare de securitate")
            self.refresh_all()
        elif action == act_sanitize:
            self._open_sanitize_dialog(med)

    def _open_sanitize_dialog(self, med: dict):
        metode = ['Clear (Suprascriere 1-Pass)', 'Purge (Crypto-Erase / Multi-Pass)', 'Destroy (Distrugere Fizică DIN 66399)']
        from PyQt6.QtWidgets import QInputDialog
        metoda_full, ok = QInputDialog.getItem(self, "Sanitizare NIST SP 800-88r2", "Selectează metoda conform nivelului de clasificare:", metode, 0, False)
        if ok and metoda_full:
            metoda = metoda_full.split(' ')[0]
            martor, ok_m = QInputDialog.getText(self, "Martor Verificator", "Introduceți numele martorului / ofițerului de securitate:")
            if ok_m and martor:
                try:
                    cert = self.db.sanitize_media(
                        med['id'], metoda, f"Sanitizare {metoda} executata pe statia {self.db.local_host}",
                        self.operator_name, martor, "Sef Structura Securitate"
                    )
                    QMessageBox.information(self, "Sanitizare Finalizată", f"Certificat generat cu succes:\n{cert}\n\nJurnalizat în lanțul de audit!")
                    self.refresh_all()
                except Exception as e:
                    QMessageBox.critical(self, "Eroare", f"Eroare sanitizare:\n{str(e)}")
