from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QGroupBox, QFormLayout,
    QSpinBox, QDoubleSpinBox, QTextEdit, QFileDialog, QScrollArea, QCompleter
)
from PyQt6.QtCore import Qt, pyqtSignal
from configparser import ConfigParser
from database.db import DatabaseManager
import hashlib

class TabInregistrare(QWidget):
    transfer_saved = pyqtSignal(str)

    CLASIFICARI = [
        "Neclasificat",
        "Secret de Serviciu",
        "Secret",
        "Strict Secret",
        "Strict Secret de Importanță Deosebită"
    ]

    MEDII_TRANSFER = [
        "USB Flash Drive Criptat",
        "HDD Extern Securizat",
        "SSD Extern FIPS 140-3",
        "Mediu Optic CD/DVD-R",
        "Bandă Magnetică LTO",
        "Card SD Securizat"
    ]

    def __init__(self, db: DatabaseManager, operator: dict, config: ConfigParser):
        super().__init__()
        self.db = db
        self.operator = operator
        self.config = config
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)

        header = QLabel("📝 Înregistrare Transfer Media Nou")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #58a6ff; padding: 5px;")
        layout.addWidget(header)

        # 1. SURSĂ
        box_src = QGroupBox("📤 Instituție & Stație Sursă (Predător)")
        src_layout = QFormLayout()
        
        self.src_institutie = self._completer_field('institutie')
        self.src_institutie.setPlaceholderText("ex: Ministerul Apărării Naționale / UM 01234")
        src_layout.addRow("Instituție Sursă *:", self.src_institutie)

        self.src_pc = self._completer_field('pc')
        self.src_pc.setPlaceholderText("ex: WS-OPERATIV-01 (Identificator intern PC)")
        src_layout.addRow("Stație / Sistem Sursă *:", self.src_pc)

        self.src_medium = QComboBox()
        self.src_medium.addItems(["HDD Intern Criptat", "SSD Intern BitLocker", "Server Local Stocare", "Stație Izolată Air-Gap"])
        src_layout.addRow("Suport Sursă *:", self.src_medium)

        self.src_sn = QLineEdit()
        self.src_sn.setPlaceholderText("Serie hardware suport sursă (opțional)")
        src_layout.addRow("S/N Suport Sursă:", self.src_sn)
        box_src.setLayout(src_layout)
        layout.addWidget(box_src)

        # 2. PERSOANĂ RESPONSABILĂ
        box_pers = QGroupBox("👤 Date Persoană / Gestionar Predător")
        pers_layout = QFormLayout()

        self.pers_nume = self._completer_field('persoana')
        self.pers_nume.setPlaceholderText("ex: Cpt. Popescu Ion")
        pers_layout.addRow("Nume & Prenume *:", self.pers_nume)

        self.pers_functie = QLineEdit()
        self.pers_functie.setPlaceholderText("ex: Șef Birou Comunicații și Informatică")
        pers_layout.addRow("Funcție / Grad:", self.pers_functie)

        self.pers_legitimatie = QLineEdit()
        self.pers_legitimatie.setPlaceholderText("Serie/Nr. Legitimatie Serviciu")
        pers_layout.addRow("Legitimație / ID:", self.pers_legitimatie)

        self.pers_autorizatie = QComboBox()
        self.pers_autorizatie.addItems(self.CLASIFICARI)
        self.pers_autorizatie.setCurrentIndex(2)
        pers_layout.addRow("Nivel Autorizare (Clearance) *:", self.pers_autorizatie)
        box_pers.setLayout(pers_layout)
        layout.addWidget(box_pers)

        # 3. SUPORT / MEDIU DE TRANSFER
        box_trans = QGroupBox("💾 Suport Fizic de Transfer (Mediu Amovibil)")
        trans_layout = QFormLayout()

        self.transfer_medium = QComboBox()
        self.transfer_medium.addItems(self.MEDII_TRANSFER)
        trans_layout.addRow("Tip Mediu Amovibil *:", self.transfer_medium)

        self.transfer_sn = QLineEdit()
        self.transfer_sn.setPlaceholderText("Număr de serie fizic gravat pe suport")
        trans_layout.addRow("Serie Hardware (S/N) *:", self.transfer_sn)

        self.transfer_label = QLineEdit()
        self.transfer_label.setPlaceholderText("Etichetă fizică de inventar (ex: USB-SEC-042)")
        trans_layout.addRow("Etichetă / Cod Suport:", self.transfer_label)

        cap_layout = QHBoxLayout()
        self.transfer_cap = QDoubleSpinBox()
        self.transfer_cap.setRange(0, 10000)
        self.transfer_cap.setSuffix(" GB")
        self.transfer_cap.setValue(32)
        cap_layout.addWidget(QLabel("Capacitate Totală:"))
        cap_layout.addWidget(self.transfer_cap)

        self.transfer_free = QDoubleSpinBox()
        self.transfer_free.setRange(0, 10000)
        self.transfer_free.setSuffix(" GB")
        self.transfer_free.setValue(30)
        cap_layout.addWidget(QLabel("Spațiu Liber:"))
        cap_layout.addWidget(self.transfer_free)
        trans_layout.addRow("Dimensiuni Mediu:", cap_layout)
        box_trans.setLayout(trans_layout)
        layout.addWidget(box_trans)

        # 4. DESTINAȚIE
        box_dst = QGroupBox("📥 Instituție & Sistem Destinație (Primitor)")
        dst_layout = QFormLayout()

        self.dst_institutie = self._completer_field('institutie')
        self.dst_institutie.setPlaceholderText("ex: Statul Major al Apărării / Structura Centrală")
        dst_layout.addRow("Instituție Destinație *:", self.dst_institutie)

        self.dst_pc = self._completer_field('pc')
        self.dst_pc.setPlaceholderText("ex: SRV-ARHIVA-SEC-01 (opțional)")
        dst_layout.addRow("Sistem / PC Destinație:", self.dst_pc)
        box_dst.setLayout(dst_layout)
        layout.addWidget(box_dst)

        # 5. CONȚINUT & CLASIFICARE & HASH
        box_content = QGroupBox("🔒 Conținut, Nivel de Clasificare & Integritate")
        content_layout = QFormLayout()

        self.clasificare = QComboBox()
        self.clasificare.addItems(self.CLASIFICARI)
        self.clasificare.currentIndexChanged.connect(self._on_clasificare_changed)
        content_layout.addRow("Nivel Clasificare (HG 585/2002) *:", self.clasificare)

        self.lbl_preview_nr = QLabel()
        self.lbl_preview_nr.setStyleSheet("font-weight: bold; color: #58a6ff;")
        self._on_clasificare_changed()
        content_layout.addRow("Format Număr Registru:", self.lbl_preview_nr)

        self.baza_legala = QLineEdit()
        self.baza_legala.setText("HG 585/2002 Art. 60-65, Legea 182/2002")
        content_layout.addRow("Bază Legală / Ordin:", self.baza_legala)

        self.nr_aprobare = QLineEdit()
        self.nr_aprobare.setPlaceholderText("ex: Aprobare CSTIC/ORNISS nr. 1234/2026")
        content_layout.addRow("Nr. Aprobare Transfer:", self.nr_aprobare)

        self.arhiva_nume = QLineEdit()
        self.arhiva_nume.setPlaceholderText("ex: Date_Misiune_2026.enc sau Nume_Pachet.tar.gz")
        content_layout.addRow("Denumire Pachet / Arhivă:", self.arhiva_nume)

        hash_box = QHBoxLayout()
        self.arhiva_hash = QLineEdit()
        self.arhiva_hash.setPlaceholderText("Hash SHA-256 al fișierului transferat")
        self.btn_calc_hash = QPushButton("📁 Alege Fișier & Calculează Hash")
        self.btn_calc_hash.clicked.connect(self._calculate_file_hash)
        hash_box.addWidget(self.arhiva_hash)
        hash_box.addWidget(self.btn_calc_hash)
        content_layout.addRow("Amprentă Digitală SHA-256:", hash_box)

        self.observatii = QTextEdit()
        self.observatii.setPlaceholderText("Mențiuni suplimentare privind regimul de securitate...")
        self.observatii.setMaximumHeight(70)
        content_layout.addRow("Observații:", self.observatii)

        box_content.setLayout(content_layout)
        layout.addWidget(box_content)

        btn_box = QHBoxLayout()
        self.btn_reset = QPushButton("Curăță Formular")
        self.btn_reset.clicked.connect(self.reset_form)
        
        self.btn_save = QPushButton("💾 Salvează & Generează Număr Registru")
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.setFixedHeight(40)
        self.btn_save.clicked.connect(self._save_transfer)

        btn_box.addWidget(self.btn_reset)
        btn_box.addWidget(self.btn_save)
        layout.addLayout(btn_box)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _on_clasificare_changed(self):
        clf = self.clasificare.currentText()
        prefix_sec = DatabaseManager.PREFIX_MAP.get(clf, 'NC')
        an = self.config.get('General', 'prefix_nr', fallback='MAPN')
        self.lbl_preview_nr.setText(f"{an}-YYYY-{prefix_sec}-NNNN (Conform Art. 41 HG 585/2002)")

    def _completer_field(self, category: str) -> QLineEdit:
        field = QLineEdit()
        items = self.db.get_autocomplete(category)
        if items:
            completer = QCompleter(items)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            field.setCompleter(completer)
        return field

    def _calculate_file_hash(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selectare Fișier pentru Calcul Integritate SHA-256")
        if file_path:
            try:
                hasher = hashlib.sha256()
                with open(file_path, 'rb') as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
                h = hasher.hexdigest()
                self.arhiva_hash.setText(h)
                if not self.arhiva_nume.text():
                    from pathlib import Path
                    self.arhiva_nume.setText(Path(file_path).name)
                QMessageBox.information(self, "Integritate Calculată", f"Hash SHA-256 generat cu succes:\\n\\n{h}")
            except Exception as e:
                QMessageBox.critical(self, "Eroare Hash", f"Nu s-a putut citi fișierul:\\n{str(e)}")

    def _save_transfer(self):
        if not self.src_institutie.text().strip():
            QMessageBox.warning(self, "Validare", "Instituția sursă este obligatorie!")
            return
        if not self.src_pc.text().strip():
            QMessageBox.warning(self, "Validare", "Stația / sistemul sursă este obligatoriu!")
            return
        if not self.pers_nume.text().strip():
            QMessageBox.warning(self, "Validare", "Numele persoanei predătoare este obligatoriu!")
            return
        if not self.transfer_sn.text().strip():
            QMessageBox.warning(self, "Validare", "Seria hardware a mediului de transfer este obligatorie!")
            return
        if not self.dst_institutie.text().strip():
            QMessageBox.warning(self, "Validare", "Instituția destinație este obligatorie!")
            return

        prefix_inst = self.config.get('General', 'prefix_nr', fallback='MAPN')
        clf = self.clasificare.currentText()

        data = {
            'src_institutie': self.src_institutie.text().strip(),
            'src_pc_nume': self.src_pc.text().strip(),
            'src_medium': self.src_medium.currentText(),
            'src_sn': self.src_sn.text().strip() or None,
            'pers_nume': self.pers_nume.text().strip(),
            'pers_functie': self.pers_functie.text().strip() or None,
            'pers_legitimatie': self.pers_legitimatie.text().strip() or None,
            'pers_autorizatie': self.pers_autorizatie.currentText(),
            'transfer_medium': self.transfer_medium.currentText(),
            'transfer_sn': self.transfer_sn.text().strip(),
            'transfer_label': self.transfer_label.text().strip() or None,
            'transfer_cap_gb': self.transfer_cap.value(),
            'transfer_free_gb': self.transfer_free.value(),
            'dst_institutie': self.dst_institutie.text().strip(),
            'dst_pc_nume': self.dst_pc.text().strip() or None,
            'arhiva_nume': self.arhiva_nume.text().strip() or None,
            'arhiva_hash': self.arhiva_hash.text().strip() or None,
            'clasificare': clf,
            'baza_legala': self.baza_legala.text().strip() or None,
            'nr_aprobare': self.nr_aprobare.text().strip() or None,
            'status': 'activ',
            'observatii': self.observatii.toPlainText().strip() or None
        }

        try:
            tid = self.db.insert_transfer(data, self.operator['nume'], self.operator['id'], prefix_inst)
            rec = self.db.get_transfer_by_id(tid)
            QMessageBox.information(
                self, "Salvat cu Succes",
                f"Înregistrarea a fost creată conform normelor:\\n\\n"
                f"📋 Număr Registru: {rec['nr']}\\n"
                f"🔒 Clasificare: {rec['clasificare']}\\n"
                f"🛡️ Hash Integritate: {rec['hash_inregistrare'][:20]}...\\n\\n"
                f"Înregistrarea este acum disponibilă în tab-ul Registru Transferuri."
            )
            self.reset_form()
            self.transfer_saved.emit(tid)
        except Exception as e:
            QMessageBox.critical(self, "Eroare la Salvare", f"Eroare internă:\\n{str(e)}")

    def reset_form(self):
        for w in self.findChildren(QLineEdit):
            w.clear()
        for w in self.findChildren(QTextEdit):
            w.clear()
        self.baza_legala.setText("HG 585/2002 Art. 60-65, Legea 182/2002")
        self.transfer_cap.setValue(32)
        self.transfer_free.setValue(30)
        self.clasificare.setCurrentIndex(0)
