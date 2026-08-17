"""
Tab Înregistrare Transfer Militar - Formular Transfer Date Informatice
Conform HG 585/2002, NATO AC/35, Decizia 2013/488/UE si Endpoint Protector Device Control.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox,
    QPushButton, QFormLayout, QScrollArea, QMessageBox, QFileDialog,
    QCheckBox, QCompleter, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from configparser import ConfigParser
import hashlib, os, secrets
from datetime import datetime
from database.db import DatabaseManager
from services.device_control_service import DeviceControlService
from ui.theme import get_classification_badge_style, CLASSIFICATION_COLORS, NATO_COLORS


class DialogFourEyesApproval(QDialog):
    def __init__(self, db: DatabaseManager, transfer_nr: str, clasificare: str, parent=None):
        super().__init__(parent)
        self.db = db
        self.transfer_nr = transfer_nr
        self.clasificare = clasificare
        self.approved_by = None
        self.functie = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("🔐 Aprobare Principiul Celor 4 Ochi (Four-Eyes Principle)")
        self.setMinimumWidth(450)
        layout = QVBoxLayout(self)

        lbl_alert = QLabel(f"⚠️ Transferul clasificate [{self.clasificare}] ({self.transfer_nr})\nnecesită validarea și contrasemnarea unui al doilea ofițer / martor autorizat conform HG 585/2002 și NATO AC/35.")
        lbl_alert.setWordWrap(True)
        lbl_alert.setStyleSheet("color: #d29922; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_alert)

        form = QFormLayout()

        self.cmb_op = QComboBox()
        self.ops = self.db.get_active_operators()
        for op in self.ops:
            self.cmb_op.addItem(f"{op['nume']} ({op['functie']} - {op['autorizatie']})", op['id'])
        form.addRow("Ofițer / Martor Verificator:", self.cmb_op)

        self.txt_pin = QLineEdit()
        self.txt_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pin.setPlaceholderText("PIN 6 cifre martor")
        form.addRow("PIN Confirmare:", self.txt_pin)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Anulare Transfer")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)

        btn_ok = QPushButton("✅ Aprobă & Semnează Transfer")
        btn_ok.setObjectName("primary")
        btn_ok.clicked.connect(self._verify_pin)
        btns.addWidget(btn_ok)

        layout.addLayout(btns)

    def _verify_pin(self):
        op_id = self.cmb_op.currentData()
        pin = self.txt_pin.text().strip()
        auth = self.db.authenticate_operator(op_id, pin)
        if auth:
            self.approved_by = auth['nume']
            self.functie = auth['functie']
            self.accept()
        else:
            QMessageBox.critical(self, "Autentificare Eșuată", "PIN incorect pentru martorul selectat!")


class TabInregistrare(QWidget):
    transfer_saved = pyqtSignal(str)

    def __init__(self, db: DatabaseManager, operator_name: str, config: ConfigParser):
        super().__init__()
        self.db = db
        self.operator_name = operator_name
        self.config = config
        self.detector = DeviceControlService(db)
        self.connected_media = []
        self.setup_ui()
        self.refresh_available_media()

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Header
        header_bar = QHBoxLayout()
        header = QLabel("📝 Înregistrare Transfer Date Informatice (Sistem Militar)")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #58a6ff;")
        header_bar.addWidget(header)

        header_bar.addStretch()

        btn_refresh_dev = QPushButton("🔄 Reîmprospătează Medii Conectate")
        btn_refresh_dev.clicked.connect(self.refresh_available_media)
        header_bar.addWidget(btn_refresh_dev)

        layout.addLayout(header_bar)

        # ===== 1. SELECTOR MEDIU AMPRENTAT CONECTAT =====
        box_mediu = QGroupBox("💾 1. Mediu de Transfer Amprentat (Device Control Whitelist)")
        layout_mediu = QVBoxLayout(box_mediu)

        row_sel = QHBoxLayout()
        row_sel.addWidget(QLabel("Mediu Conectat Detectat:"))
        self.cmb_detected_media = QComboBox()
        self.cmb_detected_media.currentIndexChanged.connect(self._on_medium_selected)
        row_sel.addWidget(self.cmb_detected_media, stretch=1)
        layout_mediu.addLayout(row_sel)

        form_med = QFormLayout()
        
        self.txt_med_tip = QLineEdit()
        self.txt_med_tip.setReadOnly(True)
        form_med.addRow("Tip & Model Mediu:", self.txt_med_tip)

        self.txt_med_sn = QLineEdit()
        self.txt_med_sn.setReadOnly(True)
        form_med.addRow("Serie Hardware S/N:", self.txt_med_sn)

        self.txt_med_vid_pid = QLineEdit()
        self.txt_med_vid_pid.setReadOnly(True)
        form_med.addRow("VID : PID:", self.txt_med_vid_pid)

        self.txt_med_label = QLineEdit()
        self.txt_med_label.setPlaceholderText("Etichetă militară / Cod inventar...")
        form_med.addRow("Cod Inventar / Etichetă:", self.txt_med_label)

        cap_layout = QHBoxLayout()
        self.spn_med_cap = QDoubleSpinBox()
        self.spn_med_cap.setRange(0, 100000)
        self.spn_med_cap.setSuffix(" GB")
        cap_layout.addWidget(self.spn_med_cap)
        cap_layout.addWidget(QLabel("Liber:"))
        self.spn_med_free = QDoubleSpinBox()
        self.spn_med_free.setRange(0, 100000)
        self.spn_med_free.setSuffix(" GB")
        cap_layout.addWidget(self.spn_med_free)
        form_med.addRow("Capacitate:", cap_layout)

        self.lbl_media_security_status = QLabel("Niciun mediu selectat")
        self.lbl_media_security_status.setStyleSheet("font-weight: bold; color: #8b949e;")
        form_med.addRow("Status Securitate:", self.lbl_media_security_status)

        layout_mediu.addLayout(form_med)
        layout.addWidget(box_mediu)

        # ===== 2. FLUX & UNITĂȚI SURSĂ / DESTINAȚIE =====
        box_flux = QGroupBox("📤 2. Direcție Transfer, Sursă & Destinație")
        form_flux = QFormLayout(box_flux)

        self.cmb_directie = QComboBox()
        self.cmb_directie.addItem("Ieșire din Stație (Outbound - Transfer către altă unitate/sistem)", "iesire")
        self.cmb_directie.addItem("Intrare în Stație (Inbound - Preluare de pe mediu extern)", "intrare")
        self.cmb_directie.addItem("Tranzit / Procesare Internă", "tranzit")
        form_flux.addRow("Direcție Flux Transfer: *", self.cmb_directie)

        self.txt_src_institutie = self._completer_field('src_institutie')
        self.txt_src_institutie.setText(self.config.get('General', 'institutie', fallback='MApN / U.M. 01234'))
        form_flux.addRow("Unitate / Instituție Sursă: *", self.txt_src_institutie)

        self.txt_src_pc = QLineEdit(self.db.local_host)
        form_flux.addRow("Stație / Sistem Sursă: *", self.txt_src_pc)

        self.txt_dst_institutie = self._completer_field('dst_institutie')
        self.txt_dst_institutie.setPlaceholderText("Ex: MApN / Statul Major al Apărării / U.M. 02468")
        form_flux.addRow("Unitate / Instituție Destinație: *", self.txt_dst_institutie)

        self.txt_dst_pc = QLineEdit()
        self.txt_dst_pc.setPlaceholderText("Ex: STATIE-RECEPTIE-01 (Opțional)")
        form_flux.addRow("Stație Destinație:", self.txt_dst_pc)

        layout.addWidget(box_flux)

        # ===== 3. PERSOANE & LANȚ DE CUSTODIE =====
        box_pers = QGroupBox("👤 3. Lanț de Custodie & Curier Militar")
        form_pers = QFormLayout(box_pers)

        self.txt_pers_nume = self._completer_field('pers_nume')
        self.txt_pers_nume.setPlaceholderText("Nume complet persoană predare/primire")
        form_pers.addRow("Persoană Responsabilă: *", self.txt_pers_nume)

        self.txt_pers_functie = QLineEdit()
        self.txt_pers_functie.setPlaceholderText("Ex: Ofițer Comunicații / Specialist IT")
        form_pers.addRow("Funcție & Grad:", self.txt_pers_functie)

        self.txt_pers_leg = QLineEdit()
        self.txt_pers_leg.setPlaceholderText("Serie și număr legitimație militară / de serviciu")
        form_pers.addRow("Nr. Legitimație:", self.txt_pers_leg)

        self.cmb_pers_aut = QComboBox()
        self.cmb_pers_aut.addItems(self.db.CLASSIFICATION_LEVELS)
        self.cmb_pers_aut.setCurrentText('Secret')
        form_pers.addRow("Nivel Autorizație Acces (Clearance): *", self.cmb_pers_aut)

        self.txt_curier_nume = self._completer_field('curier_militar_nume')
        self.txt_curier_nume.setPlaceholderText("Dacă transportul se face prin curier militar...")
        form_pers.addRow("Curier Militar / Delegat:", self.txt_curier_nume)

        self.txt_curier_leg = QLineEdit()
        form_pers.addRow("Permis Transport Curier:", self.txt_curier_leg)

        layout.addWidget(box_pers)

        # ===== 4. CONȚINUT DATE & CALCUL HASH SHA-256 =====
        box_data = QGroupBox("📦 4. Conținut Date, Integritate Criptografică & Scanare Antivirus")
        form_data = QFormLayout(box_data)

        self.txt_arhiva_nume = QLineEdit()
        self.txt_arhiva_nume.setPlaceholderText("Nume pachet date / arhivă / documente...")
        form_data.addRow("Denumire Pachet / Arhivă: *", self.txt_arhiva_nume)

        self.cmb_arhiva_tip = QComboBox()
        self.cmb_arhiva_tip.addItems(['ZIP Securizat', '7Z Criptat AES-256', 'TAR.GZ', 'ISO', 'EVTX (Jurnale)', 'Fișiere Documente / PDF', 'Imagine Forensic RAW/DD', 'Alt Format'])
        form_data.addRow("Tip Conținut:", self.cmb_arhiva_tip)

        row_dim = QHBoxLayout()
        self.spn_dim_gb = QDoubleSpinBox()
        self.spn_dim_gb.setRange(0, 10000)
        self.spn_dim_gb.setSuffix(" GB")
        row_dim.addWidget(self.spn_dim_gb)
        row_dim.addWidget(QLabel("Număr Fișiere:"))
        self.spn_fisiere = QSpinBox()
        self.spn_fisiere.setRange(1, 10000000)
        self.spn_fisiere.setValue(1)
        row_dim.addWidget(self.spn_fisiere)
        form_data.addRow("Dimensiune & Volum:", row_dim)

        row_hash = QHBoxLayout()
        self.txt_hash = QLineEdit()
        self.txt_hash.setPlaceholderText("Sumă SHA-256 (calculată automat la selectare)")
        row_hash.addWidget(self.txt_hash, stretch=1)
        btn_calc_hash = QPushButton("📁 Alege Fișier & Calculează SHA-256")
        btn_calc_hash.setObjectName("secondary")
        btn_calc_hash.clicked.connect(self._select_file_and_hash)
        row_hash.addWidget(btn_calc_hash)
        form_data.addRow("Hash Integritate SHA-256: *", row_hash)

        self.chk_av = QCheckBox("Confirmare Scanare Antivirus Offline Efectuată (Fără amenințări detectate)")
        self.chk_av.setChecked(True)
        form_data.addRow("Securitate Anti-Malware:", self.chk_av)

        self.txt_desc = QTextEdit()
        self.txt_desc.setMaximumHeight(60)
        self.txt_desc.setPlaceholderText("Scurtă descriere a documentelor/datelor transferate...")
        form_data.addRow("Descriere Conținut:", self.txt_desc)

        layout.addWidget(box_data)

        # ===== 5. CLASIFICARE & CONFORMITATE JURIDICĂ =====
        box_clf = QGroupBox("⚖️ 5. Clasificare (HG 585 / NATO / EUCI) & Temei Legal")
        form_clf = QFormLayout(box_clf)

        self.cmb_clasificare = QComboBox()
        self.cmb_clasificare.addItems(self.db.CLASSIFICATION_LEVELS)
        self.cmb_clasificare.currentIndexChanged.connect(self._on_classification_changed)
        form_clf.addRow("Clasificare Națională (HG 585/2002): *", self.cmb_clasificare)

        row_nato = QHBoxLayout()
        self.txt_nato_clf = QLineEdit("NATO UNCLASSIFIED")
        self.txt_nato_clf.setReadOnly(True)
        row_nato.addWidget(self.txt_nato_clf)
        row_nato.addWidget(QLabel("Echivalent UE:"))
        self.txt_eu_clf = QLineEdit("LIMITE / UNCLASSIFIED")
        self.txt_eu_clf.setReadOnly(True)
        row_nato.addWidget(self.txt_eu_clf)
        form_clf.addRow("Echivalență Internațională:", row_nato)

        self.txt_baza_legala = QLineEdit("HG 585/2002 Art. 60-73")
        form_clf.addRow("Bază Legală:", self.txt_baza_legala)

        self.txt_nr_aprobare = QLineEdit()
        self.txt_nr_aprobare.setPlaceholderText("Nr. Ordin / Aviz diseminare (dacă este cazul)")
        form_clf.addRow("Nr. Aprobare / Aviz:", self.txt_nr_aprobare)

        self.txt_restrictii = QLineEdit()
        self.txt_restrictii.setPlaceholderText("Ex: Fără multiplicare, Acces exclusiv în încăperea CIFRU")
        form_clf.addRow("Restricții de Diseminare:", self.txt_restrictii)

        layout.addWidget(box_clf)

        # ===== 6. OBSERVAȚII & BUTOANE =====
        box_obs = QGroupBox("📝 Observații Suplimentare")
        v_obs = QVBoxLayout(box_obs)
        self.txt_observatii = QTextEdit()
        self.txt_observatii.setMaximumHeight(50)
        v_obs.addWidget(self.txt_observatii)
        layout.addWidget(box_obs)

        # Action buttons
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        btn_reset = QPushButton("🔄 Resetare Formular")
        btn_reset.clicked.connect(self.reset_form)
        btn_bar.addWidget(btn_reset)

        btn_save = QPushButton("💾 Înregistrează & Semnează Transfer Militar")
        btn_save.setObjectName("primary")
        btn_save.setStyleSheet("padding: 10px 30px; font-size: 14px; font-weight: bold;")
        btn_save.clicked.connect(self._save_transfer)
        btn_bar.addWidget(btn_save)

        layout.addLayout(btn_bar)

        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def refresh_available_media(self):
        self.connected_media = self.detector.scan_connected_devices()
        self.cmb_detected_media.clear()
        
        self.cmb_detected_media.addItem("-- Selectează un mediu conectat / amprentat --", None)
        for idx, dev in enumerate(self.connected_media):
            status_tag = "✅ AUTORIZAT" if dev.get('is_amprentat') else "⚠️ NEAMPRENTAT"
            self.cmb_detected_media.addItem(
                f"[{dev.get('drive_letter', 'N/A')}] {dev.get('model', 'Dispozitiv')} (S/N: {dev.get('serial_number', '')}) - {status_tag}",
                dev
            )

    def _on_medium_selected(self, index):
        dev = self.cmb_detected_media.currentData()
        if not dev:
            self.txt_med_tip.clear()
            self.txt_med_sn.clear()
            self.txt_med_vid_pid.clear()
            self.txt_med_label.clear()
            self.spn_med_cap.setValue(0)
            self.spn_med_free.setValue(0)
            self.lbl_media_security_status.setText("Niciun mediu selectat")
            self.lbl_media_security_status.setStyleSheet("color: #8b949e;")
            return

        self.txt_med_tip.setText(f"{dev.get('producator', '')} {dev.get('model', '')} ({dev.get('tip_mediu', 'Stick USB')})")
        self.txt_med_sn.setText(dev.get('serial_number', ''))
        self.txt_med_vid_pid.setText(f"{dev.get('vid', '')}:{dev.get('pid', '')}")
        self.txt_med_label.setText(dev.get('cod_inventar', ''))
        self.spn_med_cap.setValue(float(dev.get('capacitate_gb', 0)))
        self.spn_med_free.setValue(float(dev.get('liber_gb', 0)))

        if dev.get('is_amprentat'):
            pol = dev.get('status_politica', 'autorizat_rw')
            clf = dev.get('clasificare_max', 'Neclasificat')
            self.lbl_media_security_status.setText(f"✅ Mediu Amprentat [{dev.get('cod_inventar')}] | Plafon Maxim: {clf} | Politică: {pol.upper()}")
            self.lbl_media_security_status.setStyleSheet("color: #3fb950; font-weight: bold;")
        else:
            self.lbl_media_security_status.setText("⚠️ MEDIU NEAMPRENTAT PE ACEASTĂ STAȚIE! Transferul poate fi restricționat conform SecOPs.")
            self.lbl_media_security_status.setStyleSheet("color: #f85149; font-weight: bold;")

    def _on_classification_changed(self, index):
        clf = self.cmb_clasificare.currentText()
        self.txt_nato_clf.setText(self.db.NATO_MAP.get(clf, 'NATO UNCLASSIFIED'))
        self.txt_eu_clf.setText(self.db.EU_MAP.get(clf, 'LIMITE / UNCLASSIFIED'))

    def _completer_field(self, category: str) -> QLineEdit:
        field = QLineEdit()
        suggs = self.db.get_autocomplete_suggestions(category)
        if suggs:
            completer = QCompleter(suggs)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            field.setCompleter(completer)
        return field

    def _select_file_and_hash(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selectare Fișier / Arhivă pentru Transfer")
        if file_path:
            try:
                hasher = hashlib.sha256()
                sz_bytes = os.path.getsize(file_path)
                with open(file_path, 'rb') as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
                h = hasher.hexdigest().upper()
                self.txt_hash.setText(h)
                self.txt_arhiva_nume.setText(os.path.basename(file_path))
                self.spn_dim_gb.setValue(round(sz_bytes / (1024**3), 3))
                QMessageBox.information(self, "Integritate SHA-256", f"Hash calculat cu succes:\n{h}")
            except Exception as e:
                QMessageBox.critical(self, "Eroare Calcul Hash", f"Eroare la citirea fișierului:\n{str(e)}")

    def _save_transfer(self):
        # Validation
        if not self.txt_src_institutie.text().strip():
            QMessageBox.warning(self, "Validare", "Instituția sursă este obligatorie!")
            return
        if not self.txt_dst_institutie.text().strip():
            QMessageBox.warning(self, "Validare", "Instituția destinație este obligatorie!")
            return
        if not self.txt_pers_nume.text().strip():
            QMessageBox.warning(self, "Validare", "Numele persoanei responsabile este obligatoriu!")
            return
        if not self.txt_arhiva_nume.text().strip():
            QMessageBox.warning(self, "Validare", "Denumirea pachetului / arhivei este obligatorie!")
            return
        if not self.txt_hash.text().strip():
            QMessageBox.warning(self, "Validare", "Suma de control SHA-256 este obligatorie pentru integritate!")
            return

        clasificare = self.cmb_clasificare.currentText()
        selected_dev = self.cmb_detected_media.currentData()

        # Device Control Policy Enforcement
        storage_medium_id = None
        if selected_dev:
            storage_medium_id = selected_dev.get('medium_id')
            if not selected_dev.get('is_amprentat'):
                reply = QMessageBox.question(
                    self, "Avertisment Mediu Neamprentat",
                    "Dispozitivul utilizat nu este amprentat în baza de date a stației.\n"
                    "Doriți să continuați în regim de excepție militară (se va jurnaliza în audit)?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

        # Four-Eyes Principle check for classified levels
        four_eyes_aprobator = None
        four_eyes_functie = None
        if clasificare in ['Secret', 'Strict Secret', 'Strict Secret de Importanță Deosebită']:
            prefix = self.config.get('General', 'prefix_nr', fallback='MAPN')
            sim_nr = f"{prefix}-{datetime.now().year}-{self.db.PREFIX_MAP.get(clasificare, 'NC')}-XXXX"
            dlg_fe = DialogFourEyesApproval(self.db, sim_nr, clasificare, parent=self)
            if dlg_fe.exec() != QDialog.DialogCode.Accepted:
                QMessageBox.warning(self, "Transfer Anulat", "Aprobarea celui de-al doilea ofițer (Four-Eyes) este obligatorie pentru informații clasificate!")
                return
            four_eyes_aprobator = dlg_fe.approved_by
            four_eyes_functie = dlg_fe.functie

        prefix_inst = self.config.get('General', 'prefix_nr', fallback='MAPN')
        nr = self.db.get_next_nr(prefix_inst, clasificare)

        data = {
            'nr': nr,
            'directie_transfer': self.cmb_directie.currentData(),
            'src_institutie': self.txt_src_institutie.text().strip(),
            'src_pc_nume': self.txt_src_pc.text().strip(),
            'src_medium': self.txt_med_tip.text().strip() or 'Stick USB',
            'src_sn': self.txt_med_sn.text().strip() or None,
            'pers_nume': self.txt_pers_nume.text().strip(),
            'pers_functie': self.txt_pers_functie.text().strip() or None,
            'pers_legitimatie': self.txt_pers_leg.text().strip() or None,
            'pers_autorizatie': self.cmb_pers_aut.currentText(),
            'curier_militar_nume': self.txt_curier_nume.text().strip() or None,
            'curier_militar_legitimatie': self.txt_curier_leg.text().strip() or None,
            'transfer_medium': self.txt_med_tip.text().strip() or 'Mediu Amovibil',
            'transfer_sn': self.txt_med_sn.text().strip() or None,
            'transfer_label': self.txt_med_label.text().strip() or None,
            'transfer_vid': self.txt_med_vid_pid.text().split(':')[0] if ':' in self.txt_med_vid_pid.text() else None,
            'transfer_pid': self.txt_med_vid_pid.text().split(':')[1] if ':' in self.txt_med_vid_pid.text() else None,
            'transfer_cap_gb': self.spn_med_cap.value() or None,
            'transfer_free_gb': self.spn_med_free.value() or None,
            'storage_medium_id': storage_medium_id,
            'dst_institutie': self.txt_dst_institutie.text().strip(),
            'dst_pc_nume': self.txt_dst_pc.text().strip() or None,
            'arhiva_nume': self.txt_arhiva_nume.text().strip(),
            'arhiva_tip': self.cmb_arhiva_tip.currentText(),
            'arhiva_dim_gb': self.spn_dim_gb.value() or None,
            'arhiva_fisiere': self.spn_fisiere.value(),
            'arhiva_hash': self.txt_hash.text().strip(),
            'arhiva_descriere': self.txt_desc.toPlainText().strip() or None,
            'scanat_antivirus': 1 if self.chk_av.isChecked() else 0,
            'clasificare': clasificare,
            'clasificare_nato': self.txt_nato_clf.text(),
            'clasificare_eu': self.txt_eu_clf.text(),
            'baza_legala': self.txt_baza_legala.text().strip() or None,
            'nr_aprobare': self.txt_nr_aprobare.text().strip() or None,
            'restrictii': self.txt_restrictii.text().strip() or None,
            'four_eyes_aprobator': four_eyes_aprobator,
            'four_eyes_functie': four_eyes_functie,
            'four_eyes_aprobat_la': datetime.now().isoformat() if four_eyes_aprobator else None,
            'status': 'activ',
            'observatii': self.txt_observatii.toPlainText().strip() or None
        }

        try:
            tid = self.db.insert_transfer(data, self.operator_name, prefix_institutie=prefix_inst)
            QMessageBox.information(
                self, "Transfer Înregistrat",
                f"Transferul a fost înregistrat cu succes!\n\n"
                f"Număr Registru: {nr}\n"
                f"Clasificare: {clasificare} ({self.txt_nato_clf.text()})\n"
                f"Hash SHA-256 legat în lanțul de audit."
            )
            self.reset_form()
            self.transfer_saved.emit(tid)
        except Exception as e:
            QMessageBox.critical(self, "Eroare Înregistrare", f"Eroare la salvare:\n{str(e)}")

    def reset_form(self):
        for widget in self.findChildren(QLineEdit):
            if widget not in (self.txt_src_pc, self.txt_src_institutie, self.txt_baza_legala, self.txt_nato_clf, self.txt_eu_clf):
                widget.clear()
        for widget in self.findChildren(QTextEdit):
            widget.clear()
        self.spn_dim_gb.setValue(0)
        self.spn_fisiere.setValue(1)
        self.cmb_clasificare.setCurrentIndex(0)
        self.refresh_available_media()
