"""
Tab Medii Amprentate - Endpoint Protector Device Control & Registru Medii de Stocare (v3.3)
Gestiune amprente hardware legate de statie, scanare universala (USB, CD/DVD, SATA, SD) si control politici acces.
Conformitate Invariante DFIR P16-P18: Datele hardware sunt imuabile; denumirea de volum si numarul de inregistrare sunt configurabile.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QLineEdit, QComboBox, QGroupBox, QDialog, QFormLayout,
    QDoubleSpinBox, QTextEdit, QMenu, QSplitter, QInputDialog
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
        self.setWindowTitle("🛡️ Înregistrare & Amprentare Mediu de Stocare pe această Stație")
        self.setMinimumWidth(640)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel("🔒 Datele hardware fizice (VID/PID, S/N Firmware) sunt citite direct din sistem și sunt IMUTABILE conform standardelor DFIR.\nCompletați Numărul de Înregistrare din Registrul de Medii de Stocare și Denumirea Personalizată a Volumului.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #58a6ff; background-color: #161b22; border: 1px solid #30363d; padding: 8px; border-radius: 4px;")
        layout.addWidget(info)

        # 1. METADATE ADMINISTRATIVE SI NUMAR DE INREGISTRARE (EDITABIL)
        box_custom = QGroupBox("📋 1. Număr Înregistrare Mediu & Denumire Volum")
        form_custom = QFormLayout(box_custom)

        # Prominent Registration Number (Conform registrului de evidenta a mediilor de stocare HG 585)
        default_nr = f"MED-{self.db.PREFIX_MAP.get('Secret', '0')}-{self.db.conn.execute('SELECT COUNT(*)+1 FROM medii_amprentate').fetchone()[0]:04d}/{datetime_year()}"
        self.txt_cod = QLineEdit(default_nr)
        self.txt_cod.setPlaceholderText("Ex: 0-1045/2026, MAPN-MED-01...")
        form_custom.addRow("Număr Înregistrare Mediu: *", self.txt_cod)

        default_name = self.prefill.get('volume_name') or self.prefill.get('denumire_custom') or f"{self.prefill.get('tip_mediu', 'Stick USB')} {self.prefill.get('producator', '')} {self.prefill.get('capacitate_gb', '')}GB"
        self.txt_denumire = QLineEdit(default_name)
        self.txt_denumire.setPlaceholderText("Ex: Stick Date Operative MApN 01, CD-R Raport Criptat CIFRU...")
        form_custom.addRow("Denumire Volum (Personalizat): *", self.txt_denumire)

        self.cmb_tip_mediu = QComboBox()
        self.cmb_tip_mediu.addItems([
            'Stick USB Flash',
            'SSD Extern (USB / Type-C)',
            'HDD Extern (USB / eSATA)',
            'Unitate Optică (CD / DVD / Blu-Ray)',
            'Card Memorie (SD / MicroSD / MMC)',
            'Disc SATA / Docking Bay',
            'Disc Intern Fix (Sistem Local)'
        ])
        if self.prefill.get('tip_mediu') in [self.cmb_tip_mediu.itemText(i) for i in range(self.cmb_tip_mediu.count())]:
            self.cmb_tip_mediu.setCurrentText(self.prefill.get('tip_mediu'))
        form_custom.addRow("Tip Mediu de Stocare:", self.cmb_tip_mediu)

        self.cmb_clf = QComboBox()
        self.cmb_clf.addItems(self.db.CLASSIFICATION_LEVELS)
        self.cmb_clf.setCurrentText('Secret')
        form_custom.addRow("Nivel Clasificare / Secretizare: *", self.cmb_clf)

        self.cmb_politica = QComboBox()
        self.cmb_politica.addItem("Autorizat Complet (Read / Write)", "autorizat_rw")
        self.cmb_politica.addItem("Doar Citire (Read-Only)", "autorizat_ro")
        self.cmb_politica.addItem("În Așteptare Aprobare INFOSEC", "in_asteptare")
        self.cmb_politica.addItem("Blocat / Revocat", "blocat")
        form_custom.addRow("Politică Acces Stație: *", self.cmb_politica)

        self.cmb_cript = QComboBox()
        self.cmb_cript.addItems(['Fara', 'BitLocker To Go (AES-256)', 'Hardware SED Opal 2.0', 'Criptare Criptografică Omologată ORNISS'])
        form_custom.addRow("Stare Criptare:", self.cmb_cript)

        self.txt_gestionar = QLineEdit(self.operator_name)
        form_custom.addRow("Gestionar / Responsabil:", self.txt_gestionar)

        self.txt_unitate = QLineEdit("MApN / Structura Securitate")
        form_custom.addRow("Unitate Militară:", self.txt_unitate)

        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(45)
        self.txt_obs.setPlaceholderText("Mențiuni conform SecOPs...")
        form_custom.addRow("Observații:", self.txt_obs)

        layout.addWidget(box_custom)

        # 2. DATE TEHNICE HARDWARE EXTRASE DIN WINDOWS (STRICT READ-ONLY 🔒)
        box_hw = QGroupBox("🔒 2. Date Hardware Reale Generate de Windows (Imuabile / Read-Only)")
        form_hw = QFormLayout(box_hw)

        self.txt_hw_model = QLineEdit(f"{self.prefill.get('producator', '')} {self.prefill.get('model', '')}")
        self.txt_hw_model.setReadOnly(True)
        form_hw.addRow("Model Hardware Fabrică: 🔒", self.txt_hw_model)

        vid = self.prefill.get('vid', 'N/A')
        pid = self.prefill.get('pid', 'N/A')
        vid_pid_text = f"VID_{vid} & PID_{pid}" if (vid != "N/A" and not vid.startswith("VEN_")) else f"{vid} : {pid}"
        self.txt_vid_pid = QLineEdit(vid_pid_text)
        self.txt_vid_pid.setReadOnly(True)
        form_hw.addRow("Identificator Hardware (VID : PID): 🔒", self.txt_vid_pid)

        self.txt_sn = QLineEdit(self.prefill.get('serial_number', 'SN-AUTO-01'))
        self.txt_sn.setReadOnly(True)
        form_hw.addRow("Serie Hardware Firmware (S/N): 🔒", self.txt_sn)

        row_fs = QHBoxLayout()
        self.txt_fs = QLineEdit(self.prefill.get('file_system', 'NTFS'))
        self.txt_fs.setReadOnly(True)
        row_fs.addWidget(self.txt_fs)
        row_fs.addWidget(QLabel("Litere Volum:"))
        self.txt_letter = QLineEdit(self.prefill.get('drive_letter', 'N/A'))
        self.txt_letter.setReadOnly(True)
        row_fs.addWidget(self.txt_letter)
        row_fs.addWidget(QLabel("Capacitate:"))
        self.txt_cap = QLineEdit(f"{self.prefill.get('capacitate_gb', 0)} GB")
        self.txt_cap.setReadOnly(True)
        row_fs.addWidget(self.txt_cap)
        form_hw.addRow("Sistem Fișiere, Litere & Mărime: 🔒", row_fs)

        layout.addWidget(box_hw)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Anulare")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Înregistrează & Amprentează pe Stație")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._save_medium)
        btns.addWidget(btn_save)

        layout.addLayout(btns)

    def _save_medium(self):
        if not self.txt_cod.text().strip():
            QMessageBox.warning(self, "Validare", "Numărul de înregistrare al mediului este obligatoriu!")
            return
        if not self.txt_denumire.text().strip():
            QMessageBox.warning(self, "Validare", "Denumirea personalizată a volumului este obligatorie!")
            return

        data = {
            'cod_inventar': self.txt_cod.text().strip(),
            'denumire_custom': self.txt_denumire.text().strip(),
            'tip_mediu': self.cmb_tip_mediu.currentText(),
            'producator': self.prefill.get('producator', 'Generic'),
            'model': self.prefill.get('model', 'Storage Device'),
            'vid': self.prefill.get('vid', '0000'),
            'pid': self.prefill.get('pid', '0000'),
            'serie_hardware': self.prefill.get('serial_number', 'UNKNOWN_SN'),
            'pnp_device_id': self.prefill.get('pnp_device_id', ''),
            'volume_serial': self.prefill.get('volume_serial', ''),
            'capacitate_gb': float(self.prefill.get('capacitate_gb', 0.0)),
            'clasificare_max': self.cmb_clf.currentText(),
            'status_politica': self.cmb_politica.currentData(),
            'stare_criptare': self.cmb_cript.currentText(),
            'gestionar_nume': self.txt_gestionar.text().strip(),
            'gestionar_unitate': self.txt_unitate.text().strip(),
            'observatii': self.txt_obs.toPlainText().strip()
        }
        try:
            self.db.add_amprentat_medium(data, self.operator_name)
            QMessageBox.information(
                self, "Succes",
                f"Mediul de stocare a fost înregistrat și amprentat cu succes!\n\n"
                f"Nr. Înregistrare: {data['cod_inventar']}\n"
                f"Denumire Volum: {data['denumire_custom']}\n"
                f"Serie Hardware: {data['serie_hardware']}\n"
                f"Nivel Clasificare: {data['clasificare_max']}"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare salvare amprentă:\n{str(e)}")


def datetime_year():
    from datetime import datetime
    return datetime.now().year


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
        title = QLabel("🛡️ Registru Medii de Stocare Amprentate (Endpoint Protector Device Control)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #58a6ff;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        btn_scan = QPushButton("🔍 Scanare Live Medii Conectate (USB, CD/DVD, SATA, SD)")
        btn_scan.setObjectName("secondary")
        btn_scan.clicked.connect(self.scan_live_devices)
        header_layout.addWidget(btn_scan)

        btn_add = QPushButton("➕ Înregistrează / Amprentează Mediu Nou")
        btn_add.setObjectName("primary")
        btn_add.clicked.connect(lambda: self.open_enroll_dialog())
        header_layout.addWidget(btn_add)

        main_layout.addLayout(header_layout)

        # Top section: Live Plug & Play Detected Devices Card
        self.box_live = QGroupBox("🔌 Medii de Stocare Conectate în Timp Real (USB Flash, CD/DVD, SSD/HDD Extern, Card SD)")
        live_layout = QVBoxLayout(self.box_live)

        self.table_live = QTableWidget()
        self.table_live.setColumnCount(8)
        self.table_live.setHorizontalHeaderLabels([
            "Volum", "Tip & Model Hardware Fabrică", "VID : PID / Identificator", "Serie Hardware Firmware (Imuabil)", "Mărime / Liber", "Status Amprentare", "Nr. Înregistrare", "Acțiuni"
        ])
        self.table_live.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_live.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_live.setMaximumHeight(160)
        self.table_live.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        live_layout.addWidget(self.table_live)

        main_layout.addWidget(self.box_live)

        # Bottom section: Whitelist Table
        self.box_whitelist = QGroupBox("📋 Baza de Date a Mediilor de Stocare Amprentate pe această Stație")
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
        self.txt_search.setPlaceholderText("Caută după Nr. Înregistrare, Denumire Volum, S/N Hardware, VID/PID, Gestionar...")
        self.txt_search.textChanged.connect(self.load_whitelist)
        filter_bar.addWidget(self.txt_search)

        btn_rename_quick = QPushButton("🏷️ Redenumește Denumire Volum")
        btn_rename_quick.clicked.connect(self._rename_selected)
        filter_bar.addWidget(btn_rename_quick)

        btn_refresh = QPushButton("🔄 Reîmprospătează")
        btn_refresh.clicked.connect(self.refresh_all)
        filter_bar.addWidget(btn_refresh)

        wl_layout.addLayout(filter_bar)

        self.table_whitelist = QTableWidget()
        self.table_whitelist.setColumnCount(9)
        self.table_whitelist.setHorizontalHeaderLabels([
            "Nr. Înregistrare Mediu", "Denumire Volum (Personalizat)", "Tip Mediu & Conexiune", "Model Fabrică & S/N Hardware", "VID : PID / Identificator", "Capacitate", "Nivel Clasificare", "Politică Acces", "Gestionar / Unitate"
        ])
        self.table_whitelist.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
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
            ltr = dev.get('drive_letter', 'N/A')
            icon = "💿" if dev.get('is_optical') else ("🔌" if dev.get('is_removable') else "💻")
            self.table_live.setItem(row, 0, QTableWidgetItem(f"{icon} {ltr}"))
            
            # Show exact hardware model & physical type
            hw_desc = f"{dev.get('producator', '')} {dev.get('model', '')} [{dev.get('tip_mediu', 'Mediu')}]"
            self.table_live.setItem(row, 1, QTableWidgetItem(hw_desc))
            
            vid = dev.get('vid', 'N/A')
            pid = dev.get('pid', 'N/A')
            vid_pid = f"{vid}:{pid}" if vid != "N/A" else "N/A (NVMe/SATA)"
            self.table_live.setItem(row, 2, QTableWidgetItem(vid_pid))
            
            sn_item = QTableWidgetItem(f"🔒 {dev.get('serial_number', '')}")
            sn_item.setFont(QFont("Consolas", 9))
            self.table_live.setItem(row, 3, sn_item)
            
            self.table_live.setItem(row, 4, QTableWidgetItem(f"{dev.get('capacitate_gb', 0)} GB (Lib: {dev.get('liber_gb', 0)} GB)"))

            # Status chip
            status_item = QTableWidgetItem()
            if dev.get('is_amprentat'):
                pol = dev.get('status_politica', 'autorizat_rw')
                _, pol_text = POLICY_COLORS.get(pol, ("#8b949e", pol))
                status_item.setText(f"✅ {pol_text}")
                status_item.setForeground(QColor(POLICY_COLORS.get(pol, ("#8b949e", ""))[0]))
            elif not dev.get('is_removable') and not dev.get('is_optical'):
                status_item.setText("💻 DISC INTERN FIX")
                status_item.setForeground(QColor("#58a6ff"))
            else:
                status_item.setText("⚠️ NEÎNREGISTRAT")
                status_item.setForeground(QColor("#f85149"))
            self.table_live.setItem(row, 5, status_item)

            # Nr. Inregistrare Mediu
            nr_inreg = dev.get('nr_inregistrare_mediu', dev.get('cod_inventar', 'N/A'))
            nr_item = QTableWidgetItem(nr_inreg)
            if dev.get('is_amprentat'):
                nr_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                nr_item.setForeground(QColor("#58a6ff"))
            self.table_live.setItem(row, 6, nr_item)

            # Action button
            if not dev.get('is_amprentat') and (dev.get('is_removable') or dev.get('is_optical')):
                btn_enroll = QPushButton("⚡ Înregistrează")
                btn_enroll.setStyleSheet("background-color: #238636; color: white; padding: 3px 8px; font-weight: bold;")
                btn_enroll.clicked.connect(lambda _, d=dev: self.open_enroll_dialog(d))
                self.table_live.setCellWidget(row, 7, btn_enroll)
            elif not dev.get('is_removable') and not dev.get('is_optical'):
                lbl_int = QLabel("Sistem Local")
                lbl_int.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_int.setStyleSheet("color: #8b949e; font-size: 11px;")
                self.table_live.setCellWidget(row, 7, lbl_int)
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
            # Nr Inregistrare Mediu
            nr_item = QTableWidgetItem(r['cod_inventar'])
            nr_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            nr_item.setForeground(QColor("#58a6ff"))
            self.table_whitelist.setItem(row, 0, nr_item)
            
            # Friendly volume name
            custom_name = r.get('denumire_custom') or r.get('cod_inventar')
            item_custom = QTableWidgetItem(f"🏷️ {custom_name}")
            self.table_whitelist.setItem(row, 1, item_custom)

            # Tip mediu
            self.table_whitelist.setItem(row, 2, QTableWidgetItem(r.get('tip_mediu', 'Stick USB')))

            # Factory hardware model & SN
            hw_info = f"{r.get('producator', '')} {r.get('model', '')} | 🔒 S/N: {r['serie_hardware']}"
            self.table_whitelist.setItem(row, 3, QTableWidgetItem(hw_info))

            vid_pid = f"{r['vid']}:{r['pid']}"
            self.table_whitelist.setItem(row, 4, QTableWidgetItem(vid_pid))
            self.table_whitelist.setItem(row, 5, QTableWidgetItem(f"{r.get('capacitate_gb', 0)} GB"))

            # Clasificare
            clf_item = QTableWidgetItem(r['clasificare_max'])
            if r['clasificare_max'] in CLASSIFICATION_COLORS:
                clf_item.setForeground(QColor(CLASSIFICATION_COLORS[r['clasificare_max']]))
            self.table_whitelist.setItem(row, 6, clf_item)

            # Politica
            pol = r['status_politica']
            _, pol_text = POLICY_COLORS.get(pol, ("#8b949e", pol))
            pol_item = QTableWidgetItem(pol_text)
            pol_item.setForeground(QColor(POLICY_COLORS.get(pol, ("#8b949e", ""))[0]))
            self.table_whitelist.setItem(row, 7, pol_item)

            self.table_whitelist.setItem(row, 8, QTableWidgetItem(f"{r.get('gestionar_nume', '')} ({r.get('gestionar_unitate', '')})"))

            # Store ID in hidden role
            self.table_whitelist.item(row, 0).setData(Qt.ItemDataRole.UserRole, r['id'])

    def open_enroll_dialog(self, dev: dict = None):
        if not dev:
            removables = [d for d in self.detected_devices if d.get('is_removable') or d.get('is_optical')]
            if removables:
                dev = removables[0]
            elif self.detected_devices:
                dev = self.detected_devices[0]
            else:
                dev = {
                    'producator': 'SanDisk', 'model': 'Ultra USB', 'tip_mediu': 'Stick USB Flash',
                    'vid': '0781', 'pid': '5583', 'serial_number': 'SN-MANUAL-01',
                    'capacitate_gb': 32.0, 'file_system': 'FAT32', 'volume_name': 'Stick Nou'
                }
        dlg = DialogAmprentareMediu(self.db, self.operator_name, prefill_dev=dev, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()
            self.media_changed.emit()

    def _rename_selected(self):
        row = self.table_whitelist.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selecție", "Selectați un mediu amprentat din tabel pentru redenumire.")
            return
        med_id = self.table_whitelist.item(row, 0).data(Qt.ItemDataRole.UserRole)
        med = self.db.get_medium_by_id(med_id)
        if not med:
            return

        current_name = med.get('denumire_custom') or med.get('cod_inventar')
        new_name, ok = QInputDialog.getText(
            self, "🏷️ Redenumire Denumire Volum",
            f"Introduceți noua denumire personalizată pentru mediul [Nr. Înreg: {med['cod_inventar']}, S/N: {med['serie_hardware']}]:\n(în loc de '{current_name}')",
            text=current_name
        )
        if ok and new_name.strip() and new_name.strip() != current_name:
            self.db.rename_medium_friendly_name(med_id, new_name.strip(), self.operator_name)
            QMessageBox.information(self, "Redenumit", f"Denumirea volumului a fost actualizată în:\n'{new_name.strip()}'")
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
        
        act_rename = menu.addAction("🏷️ Redenumește Denumire Volum (Friendly Label)")
        menu.addSeparator()
        act_rw = menu.addAction("🟢 Setează: Autorizat Read / Write (Full Access)")
        act_ro = menu.addAction("🔵 Setează: Doar Citire (Read-Only)")
        act_block = menu.addAction("🔴 Setează: Blocat / Revocat pe această Stație")
        menu.addSeparator()
        act_sanitize = menu.addAction("🧹 Sanitizare NIST SP 800-88r2 (Clear / Purge / Destroy)")

        action = menu.exec(self.table_whitelist.viewport().mapToGlobal(pos))
        if action == act_rename:
            self._rename_selected()
        elif action == act_rw:
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
