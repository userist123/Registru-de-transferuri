"""
Tab Medii Amprentate & Device Control Universal (v4.2)
Monitorizeaza in timp real (Live PnP) toate mediile conectate fizic (USB, CD/DVD, SATA, SD, NVMe).
Conform cerintelor de securitate:
- Mediile de stocare pot fi inregistrate EXCLUSIV daca sunt detectate fizic pe statie (fara adaugari manuale fictive).
- "Denumire Volum" este campul principal unde se trece si Numarul de Inregistrare din registrul intern HG 585.
- Toate atributele hardware fizice (VID/PID, S/N Firmware, Capacitate) sunt strict READ-ONLY 🔒.
"""
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QLineEdit, QComboBox, QGroupBox, QDialog, QFormLayout,
    QDoubleSpinBox, QTextEdit, QMenu, QSplitter, QInputDialog, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from database.db import DatabaseManager
from services.device_control_service import DeviceControlService
from services.export_service import ExportService
from ui.theme import get_classification_badge_style, get_policy_badge_style, POLICY_COLORS, CLASSIFICATION_COLORS


class DialogSanitizationCertificatePreview(QDialog):
    """Previzualizare și salvare a Certificatului Oficial de Sanitizare NIST SP 800-88r2."""
    def __init__(self, medium_data: dict, cert_id: str, operator_executant: str, martor: str, metoda: str, parent=None):
        super().__init__(parent)
        self.medium_data = medium_data
        self.cert_id = cert_id
        self.setWindowTitle(f"🛡️ Certificat Sanitizare NIST SP 800-88r2 — {cert_id}")
        self.resize(780, 600)
        
        layout = QVBoxLayout(self)
        self.txt_html = QTextEdit()
        self.txt_html.setReadOnly(True)
        self.html_content = ExportService.generate_sanitization_certificate_html(
            medium_data, operator_executant, martor, f"Certificat ID: {cert_id}", metoda
        )
        self.txt_html.setHtml(self.html_content)
        layout.addWidget(self.txt_html)

        btns = QHBoxLayout()
        btns.addStretch()

        btn_save = QPushButton("💾 Salvează Certificat HTML / PDF")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._save_cert)
        btns.addWidget(btn_save)

        btn_close = QPushButton("Închide")
        btn_close.clicked.connect(self.accept)
        btns.addWidget(btn_close)
        layout.addLayout(btns)

    def _save_cert(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvare Certificat Sanitizare", f"Certificat_Sanitizare_{self.cert_id}.html", "HTML (*.html)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.html_content)
            QMessageBox.information(self, "Salvat", f"Certificatul de sanitizare a fost salvat:\n{path}")


class DialogAmprentareMediu(QDialog):
    def __init__(self, db: DatabaseManager, operator_name: str, detected_dev: dict, parent=None):
        super().__init__(parent)
        self.db = db
        self.operator_name = operator_name
        self.dev = detected_dev
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("🛡️ Înregistrare & Amprentare Mediu Fizic Conectat")
        self.setMinimumWidth(640)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel(
            "🔒 <b>Înregistrare Mediu Conectat Fizic:</b><br>"
            "Datele hardware fizice (VID/PID, S/N Firmware, Capacitate) sunt citite direct din sistem și sunt <b>IMUTABILE</b>.<br>"
            "Completați <b>Denumirea Volumului / Numărul de Înregistrare</b> conform Registrului de Medii de Stocare HG 585."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #58a6ff; background-color: #161b22; border: 1px solid #30363d; padding: 10px; border-radius: 4px;")
        layout.addWidget(info)

        # 1. METADATE ADMINISTRATIVE SI NUMAR DE INREGISTRARE / DENUMIRE VOLUM (EDITABIL)
        box_custom = QGroupBox("📋 1. Denumire Volum & Număr Înregistrare Mediu (HG 585)")
        form_custom = QFormLayout(box_custom)

        # Unified Volume Name / Registration Number
        default_label = self.dev.get('volume_name') or self.dev.get('denumire_custom') or f"0-1045/{datetime.now().year}"
        self.txt_denumire = QLineEdit(default_label)
        self.txt_denumire.setPlaceholderText("Ex: 0-1045/2026 sau Stick Operativ MApN 01 (0-1045/2026)")
        form_custom.addRow("Denumire Volum / Nr. Înregistrare: *", self.txt_denumire)

        self.cmb_clf = QComboBox()
        self.cmb_clf.addItems(self.db.CLASSIFICATION_LEVELS)
        self.cmb_clf.setCurrentText('Secret')
        form_custom.addRow("Plafon Maxim Clasificare: *", self.cmb_clf)

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
        self.txt_obs.setMaximumHeight(40)
        self.txt_obs.setPlaceholderText("Mențiuni conform SecOPs...")
        form_custom.addRow("Observații:", self.txt_obs)

        layout.addWidget(box_custom)

        # 2. DATE TEHNICE HARDWARE EXTRASE DIN WINDOWS (STRICT READ-ONLY 🔒)
        box_hw = QGroupBox("🔒 2. Date Hardware Reale Citite din Sistem (Imuabile / Read-Only)")
        form_hw = QFormLayout(box_hw)

        self.txt_hw_model = QLineEdit(f"{self.dev.get('producator', '')} {self.dev.get('model', '')}")
        self.txt_hw_model.setReadOnly(True)
        form_hw.addRow("Model Fabrică & Producător: 🔒", self.txt_hw_model)

        self.txt_hw_tip = QLineEdit(self.dev.get('tip_mediu', 'Stick USB Flash'))
        self.txt_hw_tip.setReadOnly(True)
        form_hw.addRow("Tip Mediu & Interfață: 🔒", self.txt_hw_tip)

        self.txt_hw_sn = QLineEdit(self.dev.get('serial_number', 'N/A'))
        self.txt_hw_sn.setReadOnly(True)
        form_hw.addRow("Serie Hardware Firmware (S/N): 🔒", self.txt_hw_sn)

        vid = self.dev.get('vid', 'N/A')
        pid = self.dev.get('pid', 'N/A')
        self.txt_hw_vid_pid = QLineEdit(f"VID_{vid} & PID_{pid}" if vid != "N/A" else f"{vid}:{pid}")
        self.txt_hw_vid_pid.setReadOnly(True)
        form_hw.addRow("Identificator Hardware (VID : PID): 🔒", self.txt_hw_vid_pid)

        self.txt_hw_cap = QLineEdit(f"{self.dev.get('capacitate_gb', 0)} GB (Partiții: {self.dev.get('drive_letter', 'N/A')})")
        self.txt_hw_cap.setReadOnly(True)
        form_hw.addRow("Capacitate & Literă Volum: 🔒", self.txt_hw_cap)

        layout.addWidget(box_hw)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Anulează")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Salvează & Amprentează în Registru")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_save)

        layout.addLayout(btns)

    def _save(self):
        val = self.txt_denumire.text().strip()
        if not val:
            QMessageBox.warning(self, "Validare", "Denumirea volumului / Numărul de înregistrare este obligatoriu!")
            return

        data = {
            'cod_inventar': val,
            'denumire_custom': val,
            'tip_mediu': self.dev.get('tip_mediu', 'Stick USB Flash'),
            'producator': self.dev.get('producator', 'Generat Hardware'),
            'model': self.dev.get('model', 'Model Dispozitiv'),
            'vid': self.dev.get('vid', 'N/A'),
            'pid': self.dev.get('pid', 'N/A'),
            'serie_hardware': self.dev.get('serial_number', 'SN-AUTO'),
            'pnp_device_id': self.dev.get('pnp_device_id', ''),
            'volume_serial': self.dev.get('volume_serial', ''),
            'capacitate_gb': float(self.dev.get('capacitate_gb', 0.0)),
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
                f"Nr. Înregistrare / Denumire: {data['cod_inventar']}\n"
                f"Serie Hardware Firmware: {data['serie_hardware']}\n"
                f"Identificator: {data['vid']}:{data['pid']}\n"
                f"Plafon Clasificare: {data['clasificare_max']}"
            )
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
        self._setup_live_polling()

    def _setup_live_polling(self):
        """Timer de scanare automata in timp real a mediilor USB, SATA, CD/DVD, SD conectate."""
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.scan_live_devices_silent)
        self.poll_timer.start(3000) # La fiecare 3 secunde scaneaza automat

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Header bar
        header_layout = QHBoxLayout()
        title = QLabel("🛡️ Registru Medii de Stocare Amprentate (Endpoint Protector Live Control)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #58a6ff;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.lbl_pnp_status = QLabel("🟢 Monitorizare Live PnP: Activă (USB / SATA / CD-DVD / SD)")
        self.lbl_pnp_status.setStyleSheet("font-size: 11px; color: #3fb950; font-weight: bold; padding-right: 10px;")
        header_layout.addWidget(self.lbl_pnp_status)

        btn_scan = QPushButton("🔄 Re-scanează Acum")
        btn_scan.clicked.connect(self.scan_live_devices)
        header_layout.addWidget(btn_scan)

        main_layout.addLayout(header_layout)

        # Top section: Live Plug & Play Detected Devices Card
        self.box_live = QGroupBox("🔌 Medii de Stocare Conectate Fizic în Timp Real (Auto-Detectate)")
        live_layout = QVBoxLayout(self.box_live)

        self.table_live = QTableWidget()
        self.table_live.setColumnCount(8)
        self.table_live.setHorizontalHeaderLabels([
            "Volum", "Tip & Model Hardware Fabrică", "VID : PID / Identificator", "Serie Hardware Firmware (Imuabil)", "Mărime / Liber", "Status Amprentare", "Nr. Înregistrare / Denumire", "Acțiuni"
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
        self.txt_search.setPlaceholderText("Caută după Denumire Volum, Nr. Înregistrare, S/N Hardware, VID/PID...")
        self.txt_search.textChanged.connect(self.load_whitelist)
        filter_bar.addWidget(self.txt_search)

        btn_rename_quick = QPushButton("🏷️ Modifică Denumire Volum / Nr. Înregistrare")
        btn_rename_quick.clicked.connect(self._rename_selected)
        filter_bar.addWidget(btn_rename_quick)

        btn_refresh = QPushButton("🔄 Reîmprospătează")
        btn_refresh.clicked.connect(self.refresh_all)
        filter_bar.addWidget(btn_refresh)

        wl_layout.addLayout(filter_bar)

        self.table_whitelist = QTableWidget()
        self.table_whitelist.setColumnCount(9)
        self.table_whitelist.setHorizontalHeaderLabels([
            "Denumire Volum & Nr. Înregistrare", "Tip Mediu & Conexiune", "Model Fabrică", "Serie Hardware Firmware (S/N)", "VID : PID / Identificator", "Capacitate", "Plafon Clasificare", "Politică Acces", "Gestionar / Unitate"
        ])
        self.table_whitelist.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_whitelist.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_whitelist.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_whitelist.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_whitelist.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_whitelist.customContextMenuRequested.connect(self._show_context_menu)
        wl_layout.addWidget(self.table_whitelist)

        main_layout.addWidget(self.box_whitelist)

    def refresh_all(self):
        self.scan_live_devices()
        self.load_whitelist()

    def scan_live_devices_silent(self):
        """Scanare in background fara mesaje de popup pentru monitorizare real-time continua."""
        devs = self.detector.scan_connected_devices()
        if len(devs) != len(self.detected_devices):
            self.detected_devices = devs
            self._render_live_table()
            self.media_changed.emit()

    def scan_live_devices(self):
        self.detected_devices = self.detector.scan_connected_devices()
        self._render_live_table()

    def _render_live_table(self):
        self.table_live.setRowCount(len(self.detected_devices))
        for row, dev in enumerate(self.detected_devices):
            # Literă / Volum
            vol_str = dev.get('drive_letter') or 'Fără literă'
            vol_item = QTableWidgetItem(vol_str)
            vol_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table_live.setItem(row, 0, vol_item)

            # Tip & Model Fabrică
            model_item = QTableWidgetItem(f"{dev.get('producator', '')} {dev.get('model', '')} [{dev.get('tip_mediu', 'Mediu')}]")
            self.table_live.setItem(row, 1, model_item)

            # VID:PID
            vid = dev.get('vid', 'N/A')
            pid = dev.get('pid', 'N/A')
            vid_pid_text = f"VID_{vid} & PID_{pid}" if (vid != "N/A" and not vid.startswith("VEN_")) else f"{vid}:{pid}"
            self.table_live.setItem(row, 2, QTableWidgetItem(vid_pid_text))

            # Serie Hardware S/N (Imuabil 🔒)
            sn_item = QTableWidgetItem(f"🔒 {dev.get('serial_number', 'N/A')}")
            sn_item.setFont(QFont("Consolas", 8))
            self.table_live.setItem(row, 3, sn_item)

            # Mărime & Liber
            cap_item = QTableWidgetItem(f"{dev.get('capacitate_gb', 0)} GB (Liber: {dev.get('liber_gb', 0)} GB)")
            self.table_live.setItem(row, 4, cap_item)

            # Status Amprentare
            status_item = QTableWidgetItem()
            if dev.get('is_amprentat'):
                pol = dev.get('status_politica', 'autorizat_rw').upper()
                status_item.setText(f"✅ AMPRENTAT ({pol})")
                status_item.setForeground(QColor("#3fb950"))
            elif not dev.get('is_removable') and not dev.get('is_optical'):
                status_item.setText("💻 DISC INTERN (Sistem)")
                status_item.setForeground(QColor("#58a6ff"))
            else:
                status_item.setText("⚠️ NOU DETECTAT - NEÎNREGISTRAT")
                status_item.setForeground(QColor("#f85149"))
            self.table_live.setItem(row, 5, status_item)

            # Denumire / Nr Inregistrare
            custom_name = dev.get('denumire_custom') or dev.get('cod_inventar') or dev.get('volume_name') or 'N/A'
            nr_item = QTableWidgetItem(custom_name)
            if dev.get('is_amprentat'):
                nr_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                nr_item.setForeground(QColor("#58a6ff"))
            self.table_live.setItem(row, 6, nr_item)

            # Action button
            if not dev.get('is_amprentat') and (dev.get('is_removable') or dev.get('is_optical')):
                btn_enroll = QPushButton("⚡ Înregistrează / Amprentează")
                btn_enroll.setStyleSheet("background-color: #238636; color: white; padding: 4px 10px; font-weight: bold;")
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
            # Denumire Volum & Nr. Inregistrare Mediu
            custom_name = r.get('denumire_custom') or r.get('cod_inventar')
            nr_item = QTableWidgetItem(f"🏷️ {custom_name}")
            nr_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            nr_item.setForeground(QColor("#58a6ff"))
            self.table_whitelist.setItem(row, 0, nr_item)

            # Tip mediu
            self.table_whitelist.setItem(row, 1, QTableWidgetItem(r.get('tip_mediu', 'Stick USB')))

            # Model Fabrica
            self.table_whitelist.setItem(row, 2, QTableWidgetItem(f"{r.get('producator', '')} {r.get('model', '')}"))

            # S/N Hardware
            sn_item = QTableWidgetItem(f"🔒 {r['serie_hardware']}")
            sn_item.setFont(QFont("Consolas", 8))
            self.table_whitelist.setItem(row, 3, sn_item)

            # VID:PID
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

    def open_enroll_dialog(self, dev: dict):
        if not dev:
            return
        dlg = DialogAmprentareMediu(self.db, self.operator_name, detected_dev=dev, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()
            self.media_changed.emit()

    def _rename_selected(self):
        row = self.table_whitelist.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selecție", "Selectați un mediu din tabelul bazei de date.")
            return

        med_id = self.table_whitelist.item(row, 0).data(Qt.ItemDataRole.UserRole)
        med = self.db.get_medium_by_id(med_id)
        if not med:
            return

        current_name = med.get('denumire_custom') or med.get('cod_inventar')
        new_name, ok = QInputDialog.getText(
            self, "🏷️ Modifică Denumire Volum / Nr. Înregistrare",
            f"Introduceți noua denumire / număr de înregistrare pentru mediul [S/N: {med['serie_hardware']}]:",
            text=current_name
        )
        if ok and new_name.strip() and new_name.strip() != current_name:
            self.db.rename_medium_friendly_name(med_id, new_name.strip(), self.operator_name)
            QMessageBox.information(self, "Actualizat", f"Denumirea volumului / Numărul de înregistrare a fost actualizat în:\n'{new_name.strip()}'")
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
        
        act_rename = menu.addAction("🏷️ Modifică Denumire Volum / Nr. Înregistrare")
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
                    self.refresh_all()
                    self.media_changed.emit()
                    dlg_cert = DialogSanitizationCertificatePreview(
                        med, cert, self.operator_name, martor, metoda_full, parent=self
                    )
                    dlg_cert.exec()
                except Exception as e:
                    QMessageBox.critical(self, "Eroare", f"Eroare sanitizare:\n{str(e)}")
