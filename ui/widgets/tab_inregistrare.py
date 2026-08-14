from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
                              QPushButton, QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
                              QGroupBox, QHBoxLayout, QCompleter)
from PyQt6.QtCore import pyqtSignal


CLASIFICARI = [
    "Neclasificat", "Secret de Serviciu", "Secret",
    "Strict Secret", "Strict Secret de Importanță Deosebită"
]
MEDII = ["USB Flash", "HDD Extern", "SSD Extern", "Optic (CD/DVD)", "Card SD", "Volum Criptat/Virtual"]


class TabInregistrare(QWidget):
    transfer_saved = pyqtSignal()

    def __init__(self, db_manager, operator, config):
        super().__init__()
        self.db = db_manager
        self.operator = operator
        self.config = config
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.inp_src_institutie = self._autocomplete_field("src_institutie")
        self.inp_src_pc = QLineEdit()
        self.inp_src_medium = QLineEdit()
        self.inp_src_sn = QLineEdit()

        self.inp_pers_nume = self._autocomplete_field("pers_nume")
        self.inp_pers_functie = QLineEdit()
        self.inp_pers_legitimatie = QLineEdit()

        self.inp_transfer_medium = QComboBox()
        self.inp_transfer_medium.addItems(MEDII)
        self.inp_transfer_sn = QLineEdit()
        self.inp_transfer_label = QLineEdit()
        self.inp_transfer_cap = QDoubleSpinBox()
        self.inp_transfer_cap.setMaximum(999999)
        self.inp_transfer_cap.setSuffix(" GB")

        self.inp_dst_institutie = self._autocomplete_field("dst_institutie")
        self.inp_dst_pc = QLineEdit()

        self.inp_arhiva_nume = QLineEdit()
        self.inp_arhiva_dim = QDoubleSpinBox()
        self.inp_arhiva_dim.setMaximum(999999)
        self.inp_arhiva_dim.setSuffix(" GB")
        self.inp_arhiva_fisiere = QSpinBox()
        self.inp_arhiva_fisiere.setMaximum(999999)

        self.inp_clasificare = QComboBox()
        self.inp_clasificare.addItems(CLASIFICARI)
        self.inp_baza_legala = QLineEdit()
        self.inp_baza_legala.setPlaceholderText("Ex: HG 585/2002 Art. 41")
        self.inp_nr_aprobare = QLineEdit()

        self.inp_observatii = QTextEdit()
        self.inp_observatii.setMaximumHeight(60)

        grp_sursa = QGroupBox("1. Sursă")
        f1 = QFormLayout(grp_sursa)
        f1.addRow("Instituție Sursă *:", self.inp_src_institutie)
        f1.addRow("Denumire PC:", self.inp_src_pc)
        f1.addRow("Mediu Sursă:", self.inp_src_medium)
        f1.addRow("Serie Sursă:", self.inp_src_sn)

        grp_pers = QGroupBox("2. Persoană Responsabilă")
        f2 = QFormLayout(grp_pers)
        f2.addRow("Nume *:", self.inp_pers_nume)
        f2.addRow("Funcție:", self.inp_pers_functie)
        f2.addRow("Legitimație:", self.inp_pers_legitimatie)

        grp_transfer = QGroupBox("3. Mediu de Transfer")
        f3 = QFormLayout(grp_transfer)
        f3.addRow("Tip Mediu *:", self.inp_transfer_medium)
        f3.addRow("Serie Hardware:", self.inp_transfer_sn)
        f3.addRow("Etichetă:", self.inp_transfer_label)
        f3.addRow("Capacitate:", self.inp_transfer_cap)

        grp_dst = QGroupBox("4. Destinație")
        f4 = QFormLayout(grp_dst)
        f4.addRow("Instituție Destinație *:", self.inp_dst_institutie)
        f4.addRow("Denumire PC:", self.inp_dst_pc)

        grp_arhiva = QGroupBox("5. Conținut / Arhivă")
        f5 = QFormLayout(grp_arhiva)
        f5.addRow("Nume Arhivă:", self.inp_arhiva_nume)
        f5.addRow("Dimensiune:", self.inp_arhiva_dim)
        f5.addRow("Nr. Fișiere:", self.inp_arhiva_fisiere)

        grp_sec = QGroupBox("6. Securitate & Conformitate")
        f6 = QFormLayout(grp_sec)
        f6.addRow("Clasificare *:", self.inp_clasificare)
        f6.addRow("Bază Legală:", self.inp_baza_legala)
        f6.addRow("Nr. Aprobare:", self.inp_nr_aprobare)
        f6.addRow("Observații:", self.inp_observatii)

        for g in [grp_sursa, grp_pers, grp_transfer, grp_dst, grp_arhiva, grp_sec]:
            layout.addWidget(g)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("💾 Înregistrează Transfer")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._save_transfer)
        btn_clear = QPushButton("🔄 Golește Formular")
        btn_clear.clicked.connect(self._clear_form)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_clear)
        layout.addLayout(btn_row)

    def _autocomplete_field(self, categorie: str) -> QLineEdit:
        field = QLineEdit()
        suggestions = self.db.get_autocomplete_suggestions(categorie)
        if suggestions:
            field.setCompleter(QCompleter(suggestions))
        return field

    def _save_transfer(self):
        if not self.inp_src_institutie.text().strip():
            QMessageBox.warning(self, "Validare", "Instituția sursă este obligatorie.")
            return
        if not self.inp_pers_nume.text().strip():
            QMessageBox.warning(self, "Validare", "Numele persoanei responsabile este obligatoriu.")
            return
        if not self.inp_dst_institutie.text().strip():
            QMessageBox.warning(self, "Validare", "Instituția destinație este obligatorie.")
            return

        data = {
            'src_institutie': self.inp_src_institutie.text().strip(),
            'src_pc_nume': self.inp_src_pc.text().strip() or "N/A",
            'src_medium': self.inp_src_medium.text().strip() or "N/A",
            'src_sn': self.inp_src_sn.text().strip(),
            'pers_nume': self.inp_pers_nume.text().strip(),
            'pers_functie': self.inp_pers_functie.text().strip(),
            'pers_legitimatie': self.inp_pers_legitimatie.text().strip(),
            'pers_autorizatie': self.inp_clasificare.currentText(),
            'transfer_medium': self.inp_transfer_medium.currentText(),
            'transfer_sn': self.inp_transfer_sn.text().strip(),
            'transfer_label': self.inp_transfer_label.text().strip(),
            'transfer_cap_gb': self.inp_transfer_cap.value(),
            'dst_institutie': self.inp_dst_institutie.text().strip(),
            'dst_pc_nume': self.inp_dst_pc.text().strip(),
            'arhiva_nume': self.inp_arhiva_nume.text().strip(),
            'arhiva_dim_gb': self.inp_arhiva_dim.value(),
            'arhiva_fisiere': self.inp_arhiva_fisiere.value(),
            'clasificare': self.inp_clasificare.currentText(),
            'baza_legala': self.inp_baza_legala.text().strip(),
            'nr_aprobare': self.inp_nr_aprobare.text().strip(),
            'observatii': self.inp_observatii.toPlainText().strip(),
        }

        try:
            prefix = self.config.get('institutie', 'prefix', fallback='MAPN') if hasattr(self.config, 'get') else 'MAPN'
            record_id = self.db.insert_transfer(data, self.operator['nume'], self.operator['id'], prefix)
            QMessageBox.information(self, "Succes", "Transfer înregistrat cu succes.")
            self._clear_form()
            self.transfer_saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"A apărut o eroare: {e}")

    def _clear_form(self):
        for field in [self.inp_src_institutie, self.inp_src_pc, self.inp_src_medium, self.inp_src_sn,
                      self.inp_pers_nume, self.inp_pers_functie, self.inp_pers_legitimatie,
                      self.inp_transfer_sn, self.inp_transfer_label, self.inp_dst_institutie,
                      self.inp_dst_pc, self.inp_arhiva_nume, self.inp_baza_legala, self.inp_nr_aprobare]:
            field.clear()
        self.inp_transfer_cap.setValue(0)
        self.inp_arhiva_dim.setValue(0)
        self.inp_arhiva_fisiere.setValue(0)
        self.inp_observatii.clear()
        self.inp_clasificare.setCurrentIndex(0)
        self.inp_transfer_medium.setCurrentIndex(0)
