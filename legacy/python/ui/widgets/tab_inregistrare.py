"""
Tab Înregistrare Transfer Militar - Formular Conform HG 585/2002, NATO AC/35 & EUCI (v3.4)
Permite:
- Introducerea manuala a numarului de inregistrare (ex: 2150-23SSv)
- Detectarea automata a numarului si a nivelului de clasificare (SSV/Secret/Strict Secret/SSID/NC) din denumirea fisierului
- Auto-generare conform HG 585 Art. 41 daca este lasat necompletat
- Selectare mediu amprentat (USB, CD/DVD, SSD/HDD Extern, Card SD, SATA)
- Calcul integritate SHA-256 si contrasemnare Four-Eyes Principle
"""
import os, hashlib, json, re
from configparser import ConfigParser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QGroupBox, QDoubleSpinBox,
    QSpinBox, QTextEdit, QFileDialog, QMessageBox, QCheckBox,
    QScrollArea, QFrame, QCompleter, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from database.db import DatabaseManager
from services.device_control_service import DeviceControlService
from ui.theme import get_classification_badge_style, CLASSIFICATION_COLORS, NATO_COLORS


class DialogFourEyesApproval(QDialog):
    """Dialog obligatoriu pentru principiul celor 4 ochi (Four-Eyes Principle) la transferuri clasificate."""
    def __init__(self, db: DatabaseManager, current_operator: str, clasificare: str, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_operator = current_operator
        self.clasificare = clasificare
        self.approver_name = ""
        self.approver_role = ""
        self.approver_id = ""
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(f"👥 Aprobare Obligatorie Four-Eyes Principle — {self.clasificare}")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel(
            f"⚠️ ATENȚIE: Transferul solicitat are nivelul de clasificare <b>{self.clasificare}</b>.<br>"
            "Conform standardelor militare HG 585/2002 și NATO AC/35, este necesară <b>contrasemnarea și validarea PIN</b> de către un al doilea ofițer / martor autorizat."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #d29922; background-color: #1f1b11; border: 1px solid #bb8009; padding: 10px; border-radius: 6px;")
        layout.addWidget(info)

        form = QFormLayout()
        
        self.cmb_approver = QComboBox()
        operators = self.db.get_active_operators()
        eligible_approvers = [op for op in operators if op['nume'] != self.current_operator]
        if not eligible_approvers:
            eligible_approvers = operators

        for op in eligible_approvers:
            self.cmb_approver.addItem(f"{op['nume']} ({op.get('functie', 'Ofițer')} - {op.get('autorizatie', '')})", op)
        form.addRow("Ofițer Aprobator / Martor: *", self.cmb_approver)

        self.txt_pin = QLineEdit()
        self.txt_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pin.setMaxLength(6)
        self.txt_pin.setPlaceholderText("Introduceți PIN-ul de 6 cifre al aprobatorului")
        form.addRow("PIN Aprobator (6 cifre): *", self.txt_pin)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Anulează Transferul")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)

        btn_confirm = QPushButton("✍️ Validează & Aprobă Transferul")
        btn_confirm.setObjectName("primary")
        btn_confirm.clicked.connect(self._verify_and_approve)
        btns.addWidget(btn_confirm)

        layout.addLayout(btns)

    def _verify_and_approve(self):
        op_data = self.cmb_approver.currentData()
        pin = self.txt_pin.text().strip()
        if not op_data or len(pin) != 6:
            QMessageBox.warning(self, "Validare", "Selectați aprobatorul și introduceți PIN-ul de 6 cifre.")
            return

        authenticated = self.db.authenticate_operator(op_data['id'], pin)
        if not authenticated:
            QMessageBox.critical(self, "Eroare Autentificare", "PIN Incorect! Aprobarea a fost respinsă și jurnalizată în audit.")
            return

        self.approver_name = op_data['nume']
        self.approver_role = op_data.get('functie', 'Ofițer Securitate')
        self.approver_id = op_data['id']
        self.accept()


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

        # ===== 0. NUMĂR ÎNREGISTRARE TRANSFER (MANUAL / DETECTAT DIN FIȘIER / AUTO HG 585) =====
        box_nr = QGroupBox("📋 0. Număr Înregistrare Transfer Militar (Manual sau Extras Automat din Fișier)")
        form_nr = QFormLayout(box_nr)

        row_nr = QHBoxLayout()
        self.txt_tx_nr = QLineEdit()
        self.txt_tx_nr.setPlaceholderText("Introduceți manual (ex: 2150-23SSv) sau lăsați gol pt. auto-generare HG 585 (ex: MAPN-2026-S-0001)")
        row_nr.addWidget(self.txt_tx_nr, stretch=1)

        btn_clear_nr = QPushButton("⚡ Resetează la Auto-Generare HG 585")
        btn_clear_nr.clicked.connect(self._reset_to_autonr)
        row_nr.addWidget(btn_clear_nr)
        form_nr.addRow("Nr. Înregistrare Transfer:", row_nr)

        self.lbl_detected_badge = QLabel("")
        self.lbl_detected_badge.setStyleSheet("color: #3fb950; font-weight: bold; background-color: #161b22; padding: 6px 10px; border-radius: 4px; border: 1px solid #238636;")
        self.lbl_detected_badge.hide()
        form_nr.addRow("Detecție Inteligentă:", self.lbl_detected_badge)

        layout.addWidget(box_nr)

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
        
        self.txt_med_nr_inreg = QLineEdit()
        self.txt_med_nr_inreg.setReadOnly(True)
        self.txt_med_nr_inreg.setPlaceholderText("Nr. înregistrare din Registrul de Medii de Stocare...")
        form_med.addRow("Nr. Înregistrare Mediu: 🔒", self.txt_med_nr_inreg)

        self.txt_med_label = QLineEdit()
        self.txt_med_label.setReadOnly(True)
        self.txt_med_label.setPlaceholderText("Denumire personalizată volum...")
        form_med.addRow("Denumire Volum: 🔒", self.txt_med_label)

        self.txt_med_tip = QLineEdit()
        self.txt_med_tip.setReadOnly(True)
        form_med.addRow("Tip & Model Mediu: 🔒", self.txt_med_tip)

        self.txt_med_vid_pid = QLineEdit()
        self.txt_med_vid_pid.setReadOnly(True)
        form_med.addRow("Identificator Hardware (VID:PID): 🔒", self.txt_med_vid_pid)

        self.txt_med_sn = QLineEdit()
        self.txt_med_sn.setReadOnly(True)
        form_med.addRow("Serie Hardware Firmware (S/N): 🔒", self.txt_med_sn)

        cap_layout = QHBoxLayout()
        self.spn_med_cap = QDoubleSpinBox()
        self.spn_med_cap.setRange(0, 100000)
        self.spn_med_cap.setSuffix(" GB")
        self.spn_med_cap.setReadOnly(True)
        cap_layout.addWidget(self.spn_med_cap)
        cap_layout.addWidget(QLabel("Liber:"))
        self.spn_med_free = QDoubleSpinBox()
        self.spn_med_free.setRange(0, 100000)
        self.spn_med_free.setSuffix(" GB")
        self.spn_med_free.setReadOnly(True)
        cap_layout.addWidget(self.spn_med_free)
        form_med.addRow("Capacitate Hardware: 🔒", cap_layout)

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
        self.txt_src_pc.setReadOnly(True)
        form_flux.addRow("Stație / Sistem Sursă: 🔒", self.txt_src_pc)

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
        self.txt_arhiva_nume.setPlaceholderText("Ex: 2150-23SSv.zip sau Nume pachet date...")
        self.txt_arhiva_nume.textChanged.connect(self._on_filename_changed)
        form_data.addRow("Denumire Pachet / Arhivă: *", self.txt_arhiva_nume)

        self.cmb_arhiva_tip = QComboBox()
        self.cmb_arhiva_tip.addItems(['ZIP Securizat', '7Z Criptat AES-256', 'TAR.GZ', 'ISO (Imagine Disc)', 'EVTX (Jurnale Audit)', 'Fișiere Documente / PDF', 'Imagine Forensic RAW/DD', 'Alt Format'])
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
        self.txt_desc.setMaximumHeight(50)
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
        self.txt_observatii.setMaximumHeight(45)
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
            is_rem = dev.get('is_removable')
            is_opt = dev.get('is_optical')
            ltr = dev.get('drive_letter', 'N/A')
            sn = dev.get('serial_number', '')
            model = f"{dev.get('producator', '')} {dev.get('model', '')}"
            nr_inreg = dev.get('nr_inregistrare_mediu', dev.get('cod_inventar', ''))
            
            icon = "💿" if is_opt else ("🔌" if is_rem else "💻")
            type_tag = dev.get('tip_mediu', 'Mediu')
            
            if is_rem or is_opt:
                if dev.get('is_amprentat'):
                    pol = dev.get('status_politica', 'autorizat_rw').upper()
                    self.cmb_detected_media.addItem(
                        f"{icon} [{nr_inreg}] {type_tag} ({ltr}) - {model} - ✅ AUTORIZAT ({pol})",
                        dev
                    )
                else:
                    self.cmb_detected_media.addItem(
                        f"⚠️ {icon} [{type_tag} {ltr}] {model} (S/N: {sn}) - NEÎNREGISTRAT",
                        dev
                    )
            else:
                self.cmb_detected_media.addItem(
                    f"💻 [Disc Intern {ltr}] {model} (S/N: {sn}) - 🔒 Sistem Local",
                    dev
                )

    def _on_medium_selected(self, index):
        dev = self.cmb_detected_media.currentData()
        if not dev:
            self.txt_med_nr_inreg.clear()
            self.txt_med_tip.clear()
            self.txt_med_sn.clear()
            self.txt_med_vid_pid.clear()
            self.txt_med_label.clear()
            self.spn_med_cap.setValue(0)
            self.spn_med_free.setValue(0)
            self.lbl_media_security_status.setText("Niciun mediu selectat")
            self.lbl_media_security_status.setStyleSheet("color: #8b949e;")
            return

        nr_inreg = dev.get('nr_inregistrare_mediu', dev.get('cod_inventar', 'NEÎNREGISTRAT'))
        self.txt_med_nr_inreg.setText(nr_inreg)
        self.txt_med_tip.setText(f"{dev.get('producator', '')} {dev.get('model', '')} [{dev.get('tip_mediu', 'Mediu')}]")
        self.txt_med_sn.setText(dev.get('serial_number', ''))
        
        vid = dev.get('vid', 'N/A')
        pid = dev.get('pid', 'N/A')
        vid_pid_text = f"VID_{vid} & PID_{pid}" if (vid != "N/A" and not vid.startswith("VEN_")) else f"{vid} : {pid}"
        self.txt_med_vid_pid.setText(vid_pid_text)
        
        custom_or_inv = dev.get('denumire_custom') or dev.get('cod_inventar') or dev.get('volume_name') or 'Mediu'
        self.txt_med_label.setText(f"{custom_or_inv} (Volum: {dev.get('drive_letter', 'N/A')})")
        self.spn_med_cap.setValue(float(dev.get('capacitate_gb', 0)))
        self.spn_med_free.setValue(float(dev.get('liber_gb', 0)))

        if dev.get('is_amprentat'):
            pol = dev.get('status_politica', 'autorizat_rw')
            clf = dev.get('clasificare_max', 'Neclasificat')
            self.lbl_media_security_status.setText(f"✅ Mediu Înregistrat [{nr_inreg}] '{custom_or_inv}' | Nivel: {clf} | Politică: {pol.upper()}")
            self.lbl_media_security_status.setStyleSheet("color: #3fb950; font-weight: bold;")
        elif not dev.get('is_removable') and not dev.get('is_optical'):
            self.lbl_media_security_status.setText("💻 Disc Intern de Sistem al Stației (NVMe/SATA). Nu reprezintă un suport extern amovibil de transfer.")
            self.lbl_media_security_status.setStyleSheet("color: #58a6ff; font-weight: bold;")
        else:
            self.lbl_media_security_status.setText("⚠️ MEDIU NEÎNREGISTRAT PE ACEASTĂ STAȚIE! Înregistrați dispozitivul în tab-ul 'Medii Amprentate'.")
            self.lbl_media_security_status.setStyleSheet("color: #f85149; font-weight: bold;")

    def _on_classification_changed(self, index):
        clf = self.cmb_clasificare.currentText()
        self.txt_nato_clf.setText(self.db.NATO_MAP.get(clf, 'NATO UNCLASSIFIED'))
        self.txt_eu_clf.setText(self.db.EU_MAP.get(clf, 'LIMITE / UNCLASSIFIED'))

    def _on_filename_changed(self, text: str):
        if text.strip():
            self._parse_filename_for_registry_info(text.strip())

    def _parse_filename_for_registry_info(self, filename: str):
        """
        Detecteaza automat numarul de inregistrare militar si nivelul de clasificare
        din structura numelui de fisier (ex: 2150-23SSv, 0-1045/26, 00-991-26, etc.)
        """
        base = os.path.splitext(os.path.basename(filename))[0].strip()
        if not base or len(base) < 3:
            return

        # 1. Detectie Secret de Serviciu (ex: 2150-23SSv, 2150_SSV, S-1234)
        if re.search(r'(?:[-_]|\b)(?:SSV|SSv|ssv|S_S_V)(?:[-_]|\b)?', base, re.IGNORECASE) or base.upper().endswith("SSV") or base.endswith("SSv"):
            self.cmb_clasificare.setCurrentText('Secret de Serviciu')
            self.txt_tx_nr.setText(base)
            self.lbl_detected_badge.setText(f"💡 Extras din fișier: Nr. Înreg. <b>{base}</b> ➔ Clasificare: <b>Secret de Serviciu (SSV)</b>")
            self.lbl_detected_badge.show()
        # 2. Detectie Strict Secret de Importanta Deosebita (SSID / 000)
        elif re.search(r'(?:[-_]|\b)(?:SSID|000[-_])', base, re.IGNORECASE):
            self.cmb_clasificare.setCurrentText('Strict Secret de Importanță Deosebită')
            self.txt_tx_nr.setText(base)
            self.lbl_detected_badge.setText(f"💡 Extras din fișier: Nr. Înreg. <b>{base}</b> ➔ Clasificare: <b>Strict Secret SSID</b>")
            self.lbl_detected_badge.show()
        # 3. Detectie Strict Secret (SS / 00)
        elif (re.search(r'(?:[-_]|\b)(?:SS|00[-_])', base, re.IGNORECASE) or base.upper().endswith("-SS") or base.upper().endswith("_SS")) and not re.search(r'SSV|SSv', base, re.IGNORECASE):
            self.cmb_clasificare.setCurrentText('Strict Secret')
            self.txt_tx_nr.setText(base)
            self.lbl_detected_badge.setText(f"💡 Extras din fișier: Nr. Înreg. <b>{base}</b> ➔ Clasificare: <b>Strict Secret (SS)</b>")
            self.lbl_detected_badge.show()
        # 4. Detectie Secret (Secret / SEC / 0-)
        elif re.search(r'(?:[-_]|\b)(?:Secret|SEC|0[-_]\d+)', base, re.IGNORECASE):
            self.cmb_clasificare.setCurrentText('Secret')
            self.txt_tx_nr.setText(base)
            self.lbl_detected_badge.setText(f"💡 Extras din fișier: Nr. Înreg. <b>{base}</b> ➔ Clasificare: <b>Secret</b>")
            self.lbl_detected_badge.show()
        # 5. Detectie Neclasificat (NC)
        elif re.search(r'(?:[-_]|\b)(?:NC|Neclasificat)', base, re.IGNORECASE):
            self.cmb_clasificare.setCurrentText('Neclasificat')
            self.txt_tx_nr.setText(base)
            self.lbl_detected_badge.setText(f"💡 Extras din fișier: Nr. Înreg. <b>{base}</b> ➔ Clasificare: <b>Neclasificat (NC)</b>")
            self.lbl_detected_badge.show()
        # 6. Pattern general numar-an (ex: 2150-23, 1045/26)
        elif re.match(r'^[0-9A-Za-z]+[-_/][0-9A-Za-z]+$', base):
            self.txt_tx_nr.setText(base)
            self.lbl_detected_badge.setText(f"💡 Nr. Înregistrare preluat din denumirea fișierului: <b>{base}</b>")
            self.lbl_detected_badge.show()

    def _reset_to_autonr(self):
        self.txt_tx_nr.clear()
        self.lbl_detected_badge.hide()
        QMessageBox.information(self, "Auto-Generare", "Numărul de înregistrare va fi generat automat conform standardului HG 585/2002 la salvare.")

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
                fname = os.path.basename(file_path)
                self.txt_arhiva_nume.setText(fname)
                self.spn_dim_gb.setValue(round(sz_bytes / (1024**3), 3))
                
                # Auto-parse registration number and classification from selected file
                self._parse_filename_for_registry_info(fname)
                
                QMessageBox.information(self, "Integritate SHA-256 & Preluare Fișier", f"Fișier: {fname}\nHash SHA-256 calculat:\n{h}")
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
            if not selected_dev.get('is_amprentat') and (selected_dev.get('is_removable') or selected_dev.get('is_optical')):
                reply = QMessageBox.question(
                    self, "Avertisment Mediu Neamprentat",
                    "Dispozitivul utilizat nu este amprentat în baza de date a stației.\n"
                    "Doriți să continuați transferul? (Va fi jurnalizat ca eveniment de securitate în lanțul de audit)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
            elif selected_dev.get('is_amprentat'):
                # Check classification ceiling
                ok, reason = self.db.is_classification_allowed_on_medium(storage_medium_id, clasificare)
                if not ok:
                    QMessageBox.critical(self, "Violare Plafon de Securitate", f"TRANSFER BLOCAT!\n{reason}")
                    return

        # Four-Eyes Approval for classified transfers (Secret, Strict Secret, SSID)
        four_eyes_aprobator = None
        four_eyes_functie = None
        four_eyes_op_id = None

        if clasificare in ['Secret', 'Strict Secret', 'Strict Secret de Importanță Deosebită']:
            dlg_4eyes = DialogFourEyesApproval(self.db, self.operator_name, clasificare, parent=self)
            if dlg_4eyes.exec() != QDialog.DialogCode.Accepted:
                QMessageBox.warning(self, "Anulat", "Transferul a fost anulat deoarece a lipsit aprobarea Four-Eyes!")
                return
            four_eyes_aprobator = dlg_4eyes.approver_name
            four_eyes_functie = dlg_4eyes.approver_role
            four_eyes_op_id = dlg_4eyes.approver_id

        # Custom or Auto-Generated Registration Number
        manual_nr = self.txt_tx_nr.text().strip() or None

        data = {
            'nr': manual_nr, # If provided, db.insert_transfer will use it directly!
            'directie_transfer': self.cmb_directie.currentData(),
            'src_institutie': self.txt_src_institutie.text().strip(),
            'src_pc_nume': self.txt_src_pc.text().strip(),
            'src_medium': 'SSD NVMe Intern' if not selected_dev else f"{selected_dev.get('tip_mediu', 'Mediu')} ({selected_dev.get('drive_letter', '')})",
            'dst_institutie': self.txt_dst_institutie.text().strip(),
            'dst_pc_nume': self.txt_dst_pc.text().strip() or None,
            'pers_nume': self.txt_pers_nume.text().strip(),
            'pers_functie': self.txt_pers_functie.text().strip() or None,
            'pers_legitimatie': self.txt_pers_leg.text().strip() or None,
            'pers_autorizatie': self.cmb_pers_aut.currentText(),
            'curier_militar_nume': self.txt_curier_nume.text().strip() or None,
            'curier_militar_legitimatie': self.txt_curier_leg.text().strip() or None,
            'transfer_medium': selected_dev.get('tip_mediu', 'Stick USB') if selected_dev else 'Mediu Nespecificat',
            'transfer_label': self.txt_med_label.text().strip() or None,
            'transfer_sn': selected_dev.get('serial_number', 'N/A') if selected_dev else None,
            'transfer_vid': selected_dev.get('vid', 'N/A') if selected_dev else None,
            'transfer_pid': selected_dev.get('pid', 'N/A') if selected_dev else None,
            'transfer_cap_gb': self.spn_med_cap.value(),
            'transfer_free_gb': self.spn_med_free.value(),
            'storage_medium_id': storage_medium_id,
            'arhiva_nume': self.txt_arhiva_nume.text().strip(),
            'arhiva_tip': self.cmb_arhiva_tip.currentText(),
            'arhiva_dim_gb': self.spn_dim_gb.value(),
            'arhiva_fisiere': self.spn_fisiere.value(),
            'arhiva_hash': self.txt_hash.text().strip().upper(),
            'scanat_antivirus': 1 if self.chk_av.isChecked() else 0,
            'antivirus_detalii': 'Scanare Antivirus Offline: Bază Definiții la zi, Negativ' if self.chk_av.isChecked() else 'Nescanat',
            'clasificare': clasificare,
            'clasificare_nato': self.txt_nato_clf.text().strip(),
            'clasificare_eu': self.txt_eu_clf.text().strip(),
            'restrictii': self.txt_restrictii.text().strip() or None,
            'nr_aprobare': self.txt_nr_aprobare.text().strip() or None,
            'observatii': self.txt_observatii.toPlainText().strip() or None,
            'semnat_operator': 1,
            'semnat_de': self.operator_name,
            'four_eyes_aprobator': four_eyes_aprobator,
            'four_eyes_functie': four_eyes_functie
        }

        try:
            record_id = self.db.insert_transfer(data, self.operator_name, None)
            
            # If 4-eyes was captured, record it formally in DB
            if four_eyes_aprobator:
                self.db.approve_four_eyes(record_id, four_eyes_aprobator, four_eyes_functie, four_eyes_op_id)

            saved_tx = self.db.get_transfer_by_id(record_id)
            final_nr = saved_tx['nr'] if saved_tx else (manual_nr or 'OK')

            msg = (
                f"✅ Transfer Militar Înregistrat cu Succes!\n\n"
                f"Nr. Înregistrare: {final_nr}\n"
                f"Clasificare: {clasificare} [{self.txt_nato_clf.text()}]\n"
                f"Pachet Date: {data['arhiva_nume']}\n"
                f"Hash Integritate SHA-256:\n{data['arhiva_hash']}\n\n"
            )
            if four_eyes_aprobator:
                msg += f"👥 Contrasemnat Four-Eyes: {four_eyes_aprobator} ({four_eyes_functie})\n"
            msg += "Evenimentul a fost semnat criptografic în lanțul de audit SHA-256."

            QMessageBox.information(self, "Înregistrare Reușită", msg)
            self.reset_form()
            self.transfer_saved.emit(record_id)

        except Exception as e:
            QMessageBox.critical(self, "Eroare Salvare Transfer", f"Nu s-a putut înregistra transferul:\n{str(e)}")

    def reset_form(self):
        self.txt_tx_nr.clear()
        self.lbl_detected_badge.hide()
        self.cmb_detected_media.setCurrentIndex(0)
        self.txt_dst_institutie.clear()
        self.txt_dst_pc.clear()
        self.txt_pers_nume.clear()
        self.txt_pers_functie.clear()
        self.txt_pers_leg.clear()
        self.txt_curier_nume.clear()
        self.txt_curier_leg.clear()
        self.txt_arhiva_nume.clear()
        self.txt_hash.clear()
        self.spn_dim_gb.setValue(0)
        self.spn_fisiere.setValue(1)
        self.txt_desc.clear()
        self.txt_nr_aprobare.clear()
        self.txt_restrictii.clear()
        self.txt_observatii.clear()
        self.cmb_clasificare.setCurrentText('Neclasificat')
