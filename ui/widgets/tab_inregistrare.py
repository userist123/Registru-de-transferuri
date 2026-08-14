"""
Tab Înregistrare - Formular transfer nou
"""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from configparser import ConfigParser
from database.db import DatabaseManager
import hashlib

class TabInregistrare(QWidget):
    transfer_saved = pyqtSignal(str)
    
    def __init__(self, db: DatabaseManager, operator_name: str, config: ConfigParser):
        super().__init__()
        self.db = db
        self.operator_name = operator_name
        self.config = config
        self.setup_ui()
    
    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Header
        header = QLabel("📝 Înregistrare Transfer Nou")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 15px;")
        layout.addWidget(header)
        
        # ===== SURSĂ =====
        sursa_box = QGroupBox("📤 Sursă")
        sursa_layout = QFormLayout()
        
        self.src_institutie = self._completer_field('institutie')
        sursa_layout.addRow("Instituție:", self.src_institutie)
        
        self.src_pc = self._completer_field('pc_nume')
        sursa_layout.addRow("PC/Sistem:", self.src_pc)
        
        self.src_medium = QComboBox()
        self.src_medium.addItems(['HDD Extern', 'SSD Extern', 'Stick USB', 'DVD/CD', 'Card SD', 'Altul'])
        sursa_layout.addRow("Tip mediu:", self.src_medium)
        
        self.src_sn = QLineEdit()
        sursa_layout.addRow("Serie SN:", self.src_sn)
        
        sursa_box.setLayout(sursa_layout)
        layout.addWidget(sursa_box)
        
        # ===== PERSOANĂ =====
        pers_box = QGroupBox("👤 Persoană Primitor")
        pers_layout = QFormLayout()
        
        self.pers_nume = self._completer_field('persoana')
        pers_layout.addRow("Nume complet *:", self.pers_nume)
        
        self.pers_functie = self._completer_field('functie')
        pers_layout.addRow("Funcție:", self.pers_functie)
        
        self.pers_legitimatie = QLineEdit()
        pers_layout.addRow("Nr. legitimație:", self.pers_legitimatie)
        
        self.pers_autorizatie = QComboBox()
        self.pers_autorizatie.addItems(['Nesecurizat', 'Acces Secret de Serviciu', 'Acces Secret', 'Acces Strict Secret'])
        pers_layout.addRow("Autorizație *:", self.pers_autorizatie)
        
        pers_box.setLayout(pers_layout)
        layout.addWidget(pers_box)
        
        # ===== MEDIU TRANSFER =====
        mediu_box = QGroupBox("💾 Mediu de Transfer")
        mediu_layout = QFormLayout()
        
        self.transfer_medium = QComboBox()
        self.transfer_medium.addItems(['HDD Extern', 'SSD Extern', 'Stick USB', 'DVD/CD', 'Card SD', 'Altul'])
        mediu_layout.addRow("Tip mediu *:", self.transfer_medium)
        
        self.transfer_sn = QLineEdit()
        mediu_layout.addRow("Serie SN:", self.transfer_sn)
        
        self.transfer_label = QLineEdit()
        mediu_layout.addRow("Label:", self.transfer_label)
        
        cap_layout = QHBoxLayout()
        self.transfer_cap = QDoubleSpinBox()
        self.transfer_cap.setRange(0, 10000)
        self.transfer_cap.setSuffix(" GB")
        cap_layout.addWidget(self.transfer_cap)
        
        self.transfer_free = QDoubleSpinBox()
        self.transfer_free.setRange(0, 10000)
        self.transfer_free.setSuffix(" GB")
        cap_layout.addWidget(QLabel("Liber:"))
        cap_layout.addWidget(self.transfer_free)
        
        mediu_layout.addRow("Capacitate:", cap_layout)
        
        mediu_box.setLayout(mediu_layout)
        layout.addWidget(mediu_box)
        
        # ===== DESTINAȚIE =====
        dest_box = QGroupBox("📥 Destinație")
        dest_layout = QFormLayout()
        
        self.dst_institutie = self._completer_field('institutie')
        dest_layout.addRow("Instituție *:", self.dst_institutie)
        
        self.dst_pc = QLineEdit()
        dest_layout.addRow("PC/Sistem:", self.dst_pc)
        
        dest_box.setLayout(dest_layout)
        layout.addWidget(dest_box)
        
        # ===== ARHIVĂ =====
        arhiva_box = QGroupBox("📦 Arhivă (Opțional)")
        arhiva_layout = QFormLayout()
        
        self.arhiva_nume = QLineEdit()
        arhiva_layout.addRow("Nume fișier:", self.arhiva_nume)
        
        self.arhiva_tip = QComboBox()
        self.arhiva_tip.addItems(['ZIP', 'RAR', '7Z', 'ISO', 'EVTX', 'Altul'])
        arhiva_layout.addRow("Tip:", self.arhiva_tip)
        
        self.arhiva_dim = QDoubleSpinBox()
        self.arhiva_dim.setRange(0, 10000)
        self.arhiva_dim.setSuffix(" GB")
        arhiva_layout.addRow("Dimensiune:", self.arhiva_dim)
        
        self.arhiva_fisiere = QSpinBox()
        self.arhiva_fisiere.setRange(0, 1000000)
        arhiva_layout.addRow("Nr. fișiere:", self.arhiva_fisiere)
        
        hash_layout = QHBoxLayout()
        self.arhiva_hash = QLineEdit()
        hash_layout.addWidget(self.arhiva_hash)
        btn_hash = QPushButton("Calculează")
        btn_hash.clicked.connect(self._calculate_hash)
        hash_layout.addWidget(btn_hash)
        arhiva_layout.addRow("Hash SHA-256:", hash_layout)
        
        self.arhiva_desc = QTextEdit()
        self.arhiva_desc.setMaximumHeight(80)
        arhiva_layout.addRow("Descriere:", self.arhiva_desc)
        
        arhiva_box.setLayout(arhiva_layout)
        layout.addWidget(arhiva_box)
        
        # ===== CLASIFICARE =====
        clf_box = QGroupBox("⚖️ Clasificare & Conformitate")
        clf_layout = QFormLayout()
        
        self.clasificare = QComboBox()
        self.clasificare.addItems(['Nesecret', 'Secret de Serviciu', 'Secret', 'Strict Secret'])
        clf_layout.addRow("Clasificare *:", self.clasificare)
        
        self.restrictii = QLineEdit()
        clf_layout.addRow("Restricții:", self.restrictii)
        
        self.aprobare_mult = QLineEdit()
        clf_layout.addRow("Aprobare multiplicare:", self.aprobare_mult)
        
        self.baza_legala = QLineEdit()
        self.baza_legala.setPlaceholderText("Ex: HG 585/2002 Art. 73")
        clf_layout.addRow("Bază legală:", self.baza_legala)
        
        clf_box.setLayout(clf_layout)
        layout.addWidget(clf_box)
        
        # ===== OBSERVAȚII =====
        obs_box = QGroupBox("📝 Observații")
        obs_layout = QVBoxLayout()
        
        self.observatii = QTextEdit()
        self.observatii.setMaximumHeight(100)
        self.observatii.setPlaceholderText("Observații suplimentare...")
        obs_layout.addWidget(self.observatii)
        
        obs_box.setLayout(obs_layout)
        layout.addWidget(obs_box)
        
        # ===== BUTOANE =====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_reset = QPushButton("🔄 Resetare")
        btn_reset.clicked.connect(self.reset_form)
        btn_layout.addWidget(btn_reset)
        
        btn_save = QPushButton("💾 Salvare")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 10px 30px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        btn_save.clicked.connect(self._save_transfer)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
    
    def _completer_field(self, category: str) -> QLineEdit:
        """Creează LineEdit cu autocomplete."""
        field = QLineEdit()
        completer = QCompleter(self.db.get_autocomplete(category))
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        field.setCompleter(completer)
        return field
    
    def _calculate_hash(self):
        """Calculează hash-ul unui fișier."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Selectare fișier arhivă")
        if file_path:
            try:
                hasher = hashlib.sha256()
                with open(file_path, 'rb') as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
                
                self.arhiva_hash.setText(hasher.hexdigest())
                QMessageBox.information(self, "Succes", f"Hash calculat pentru:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Eroare", f"Eroare calcul hash:\n{str(e)}")
    
    def _save_transfer(self):
        """Salvează transferul în bază de date."""
        # Validare câmpuri obligatorii
        if not self.src_institutie.text():
            QMessageBox.warning(self, "Validare", "Instituția sursă este obligatorie!")
            return
        
        if not self.src_pc.text():
            QMessageBox.warning(self, "Validare", "PC/Sistem sursă este obligatoriu!")
            return
        
        if not self.pers_nume.text():
            QMessageBox.warning(self, "Validare", "Numele persoanei este obligatoriu!")
            return
        
        if not self.dst_institutie.text():
            QMessageBox.warning(self, "Validare", "Instituția destinație este obligatorie!")
            return
        
        try:
            # Generare număr registru
            prefix = self.config.get('General', 'prefix_nr', fallback='MAPN')
            nr = self.db.get_next_nr(prefix)
            
            # Construire dicționar date
            data = {
                'nr': nr,
                'src_institutie': self.src_institutie.text(),
                'src_pc_nume': self.src_pc.text(),
                'src_medium': self.src_medium.currentText(),
                'src_sn': self.src_sn.text() or None,
                'src_path': None,
                
                'pers_nume': self.pers_nume.text(),
                'pers_functie': self.pers_functie.text() or None,
                'pers_legitimatie': self.pers_legitimatie.text() or None,
                'pers_autorizatie': self.pers_autorizatie.currentText(),
                
                'transfer_medium': self.transfer_medium.currentText(),
                'transfer_sn': self.transfer_sn.text() or None,
                'transfer_label': self.transfer_label.text() or None,
                'transfer_cap_gb': self.transfer_cap.value() or None,
                'transfer_free_gb': self.transfer_free.value() or None,
                
                'dst_institutie': self.dst_institutie.text(),
                'dst_pc_nume': self.dst_pc.text() or None,
                'dst_medium': None,
                'dst_sn': None,
                'dst_path': None,
                
                'arhiva_nume': self.arhiva_nume.text() or None,
                'arhiva_tip': self.arhiva_tip.currentText() if self.arhiva_nume.text() else None,
                'arhiva_dim_gb': self.arhiva_dim.value() if self.arhiva_nume.text() else None,
                'arhiva_fisiere': self.arhiva_fisiere.value() if self.arhiva_nume.text() else None,
                'arhiva_hash': self.arhiva_hash.text() or None,
                'arhiva_descriere': self.arhiva_desc.toPlainText() or None,
                
                'clasificare': self.clasificare.currentText(),
                'restrictii': self.restrictii.text() or None,
                'aprobare_mult': self.aprobare_mult.text() or None,
                'baza_legala': self.baza_legala.text() or None,
                
                'log_medium': None,
                'log_path': None,
                
                'status': 'active',
                'observatii': self.observatii.toPlainText() or None,
                'semnat_operator': 0,
                'data_verif_anual': None,
                'verificat_de': None
            }
            
            # Salvare
            transfer_id = self.db.insert_transfer(data, self.operator_name)
            
            # Emit signal
            self.transfer_saved.emit(transfer_id)
            
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare salvare:\n{str(e)}")
    
    def reset_form(self):
        """Resetează formularul."""
        # Reset câmpuri text
        for widget in self.findChildren(QLineEdit):
            widget.clear()
        
        for widget in self.findChildren(QTextEdit):
            widget.clear()
        
        # Reset spinboxes
        for widget in self.findChildren((QSpinBox, QDoubleSpinBox)):
            widget.setValue(0)
        
        # Reset comboboxes la primul item
        for widget in self.findChildren(QComboBox):
            widget.setCurrentIndex(0)

