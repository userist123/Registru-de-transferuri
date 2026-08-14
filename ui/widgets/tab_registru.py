from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateEdit, QInputDialog, QFileDialog, QDialog, QTextBrowser
)
from PyQt6.QtCore import Qt, QDate
from database.db import DatabaseManager
from services.export_service import ExportService
from configparser import ConfigParser

class TabRegistru(QWidget):
    def __init__(self, db: DatabaseManager, operator: dict, config: ConfigParser):
        super().__init__()
        self.db = db
        self.operator = operator
        self.config = config
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        filter_box = QHBoxLayout()
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Căutare după Nr. Reg, Instituție, Persoană, Serie S/N...")
        self.txt_search.textChanged.connect(self.load_data)
        filter_box.addWidget(self.txt_search, 2)

        self.cb_clf = QComboBox()
        self.cb_clf.addItems(["Toate", "Neclasificat", "Secret de Serviciu", "Secret", "Strict Secret", "Strict Secret de Importanță Deosebită"])
        self.cb_clf.currentIndexChanged.connect(self.load_data)
        filter_box.addWidget(QLabel("Clasificare:"))
        filter_box.addWidget(self.cb_clf)

        self.cb_status = QComboBox()
        self.cb_status.addItems(["Toate", "activ", "anulat"])
        self.cb_status.currentIndexChanged.connect(self.load_data)
        filter_box.addWidget(QLabel("Status:"))
        filter_box.addWidget(self.cb_status)

        btn_refresh = QPushButton("🔄 Reîmprospătează")
        btn_refresh.clicked.connect(self.load_data)
        filter_box.addWidget(btn_refresh)

        layout.addLayout(filter_box)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Nr. Registru", "Data Înregistrării", "Clasificare", "Sursă",
            "Predător", "Mediu / Serie", "Destinație", "Status", "Semnat"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.show_details)
        layout.addWidget(self.table)

        action_bar = QHBoxLayout()

        self.btn_details = QPushButton("👁️ Vizualizare Fișă Completă")
        self.btn_details.clicked.connect(self.show_details)
        action_bar.addWidget(self.btn_details)

        self.btn_sign = QPushButton("✍️ Semnează Formal Transfer")
        self.btn_sign.setObjectName("btn_primary")
        self.btn_sign.clicked.connect(self.sign_selected)
        action_bar.addWidget(self.btn_sign)

        self.btn_cancel = QPushButton("🚫 Anulează Înregistrare")
        self.btn_cancel.setObjectName("btn_danger")
        self.btn_cancel.clicked.connect(self.cancel_selected)
        action_bar.addWidget(self.btn_cancel)

        action_bar.addStretch()

        self.btn_export_csv = QPushButton("📊 Export CSV")
        self.btn_export_csv.clicked.connect(self.export_csv)
        action_bar.addWidget(self.btn_export_csv)

        self.btn_export_html = QPushButton("📑 Raport Registru (Tipar / PDF)")
        self.btn_export_html.clicked.connect(self.export_html)
        action_bar.addWidget(self.btn_export_html)

        layout.addLayout(action_bar)

    def load_data(self):
        filters = {}
        txt = self.txt_search.text().strip()
        if txt:
            filters['text'] = txt
        clf = self.cb_clf.currentText()
        if clf != "Toate":
            filters['clasificare'] = clf
        st = self.cb_status.currentText()
        if st != "Toate":
            filters['status'] = st

        transfers = self.db.get_all_transfers(filters)
        self.table.setRowCount(len(transfers))

        for row, t in enumerate(transfers):
            self.table.setItem(row, 0, QTableWidgetItem(t['nr']))
            self.table.setItem(row, 1, QTableWidgetItem(t['date_created'][:19].replace('T', ' ')))
            
            clf_item = QTableWidgetItem(t['clasificare'])
            if 'Strict Secret' in t['clasificare']:
                clf_item.setForeground(Qt.GlobalColor.magenta)
            elif 'Secret' in t['clasificare']:
                clf_item.setForeground(Qt.GlobalColor.red)
            elif 'Serviciu' in t['clasificare']:
                clf_item.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 2, clf_item)

            self.table.setItem(row, 3, QTableWidgetItem(t['src_institutie']))
            self.table.setItem(row, 4, QTableWidgetItem(f"{t['pers_nume']}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{t['transfer_medium']} ({t['transfer_sn'] or 'Fara S/N'})"))
            self.table.setItem(row, 6, QTableWidgetItem(t['dst_institutie']))
            
            st_item = QTableWidgetItem(t['status'].upper())
            if t['status'] == 'anulat':
                st_item.setForeground(Qt.GlobalColor.red)
            else:
                st_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 7, st_item)

            semn_txt = f"DA ({t['semnat_de'] or 'Operator'})" if t['semnat_operator'] else "NU"
            semn_item = QTableWidgetItem(semn_txt)
            if t['semnat_operator']:
                semn_item.setForeground(Qt.GlobalColor.cyan)
            self.table.setItem(row, 8, semn_item)

            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, t['id'])

    def _get_selected_id(self):
        sel = self.table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "Atenție", "Vă rugăm să selectați un transfer din tabel.")
            return None
        return self.table.item(sel, 0).data(Qt.ItemDataRole.UserRole)

    def show_details(self):
        tid = self._get_selected_id()
        if not tid:
            return
        t = self.db.get_transfer_by_id(tid)
        if not t:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Fișă Transfer {t['nr']}")
        dialog.resize(650, 600)
        dlg_layout = QVBoxLayout(dialog)

        browser = QTextBrowser()
        semn = f"DA (Semnat de {t['semnat_de']} la {t['semnat_la']})" if t['semnat_operator'] else "NESEMNAT"
        
        info_html = f"""
        <h2 style=\"color: #58a6ff;\">Fișă Înregistrare: {t['nr']}</h2>
        <hr/>
        <table style=\"width: 100%; font-size: 13px;\">
            <tr><td><strong>Data Creării:</strong></td><td>{t['date_created']}</td></tr>
            <tr><td><strong>Operator Înregistrare:</strong></td><td>{t['operator']}</td></tr>
            <tr><td><strong>Nivel Clasificare:</strong></td><td><span style=\"color: #f85149; font-weight: bold;\">{t['clasificare']}</span></td></tr>
            <tr><td><strong>Status:</strong></td><td><strong>{t['status'].upper()}</strong></td></tr>
            <tr><td><strong>Semnătură Formală:</strong></td><td>{semn}</td></tr>
            <tr><td><strong>Bază Legală:</strong></td><td>{t['baza_legala'] or 'N/A'}</td></tr>
            <tr><td><strong>Nr. Aprobare:</strong></td><td>{t['nr_aprobare'] or 'N/A'}</td></tr>
        </table>
        <h3 style=\"color: #58a6ff;\">Detalii Traseu & Actori</h3>
        <table style=\"width: 100%; font-size: 13px;\">
            <tr><td><strong>Instituție Sursă:</strong></td><td>{t['src_institutie']} (PC: {t['src_pc_nume']})</td></tr>
            <tr><td><strong>Persoană Predătoare:</strong></td><td>{t['pers_nume']} ({t['pers_functie'] or 'N/A'}, Clearance: {t['pers_autorizatie']})</td></tr>
            <tr><td><strong>Instituție Destinație:</strong></td><td>{t['dst_institutie']} (PC: {t['dst_pc_nume'] or 'N/A'})</td></tr>
        </table>
        <h3 style=\"color: #58a6ff;\">Suport Fizic & Conținut</h3>
        <table style=\"width: 100%; font-size: 13px;\">
            <tr><td><strong>Tip Mediu:</strong></td><td>{t['transfer_medium']}</td></tr>
            <tr><td><strong>Serie Hardware (S/N):</strong></td><td><strong>{t['transfer_sn'] or 'N/A'}</strong></td></tr>
            <tr><td><strong>Etichetă Inventar:</strong></td><td>{t['transfer_label'] or 'N/A'}</td></tr>
            <tr><td><strong>Pachet / Arhivă:</strong></td><td>{t['arhiva_nume'] or 'Transfer Direct'}</td></tr>
            <tr><td><strong>Hash SHA-256 Pachet:</strong></td><td><code style=\"color: #38bdf8;\">{t['arhiva_hash'] or 'N/A'}</code></td></tr>
        </table>
        <h3 style=\"color: #58a6ff;\">Garanție Integritate Bază de Date</h3>
        <p><strong>Hash Înregistrare Canonic (SHA-256):</strong><br/><code style=\"color: #4ade80;\">{t['hash_inregistrare']}</code></p>
        """
        browser.setHtml(info_html)
        dlg_layout.addWidget(browser)

        btn_close = QPushButton("Închide")
        btn_close.clicked.connect(dialog.accept)
        dlg_layout.addWidget(btn_close)

        dialog.exec()

    def sign_selected(self):
        tid = self._get_selected_id()
        if not tid:
            return
        t = self.db.get_transfer_by_id(tid)
        if t['semnat_operator']:
            QMessageBox.information(self, "Informație", "Această înregistrare este deja semnată formal.")
            return

        pin, ok = QInputDialog.getText(
            self, "Confirmare Semnare Formală",
            f"Introduceți PIN-ul operatorului ({self.operator['nume']}) pentru a semna transferul {t['nr']}:",
            QLineEdit.EchoMode.Password
        )
        if not ok or not pin:
            return

        if not self.db.verify_pin(pin, self.operator['pin_hash'], self.operator['salt']):
            QMessageBox.critical(self, "Eroare", "Codul PIN este incorect. Semnarea a fost refuzată.")
            return

        self.db.semneaza_transfer(tid, self.operator['nume'], self.operator['id'])
        QMessageBox.information(self, "Succes", f"Înregistrarea {t['nr']} a fost semnată cu succes.")
        self.load_data()

    def cancel_selected(self):
        tid = self._get_selected_id()
        if not tid:
            return
        t = self.db.get_transfer_by_id(tid)
        if t['status'] == 'anulat':
            QMessageBox.warning(self, "Atenție", "Această înregistrare este deja anulată.")
            return

        motiv, ok = QInputDialog.getText(
            self, "Anulare Transfer",
            f"Introduceți MOTIVUL OBLIGATORIU pentru anularea transferului {t['nr']}:"
        )
        if not ok or not motiv.strip():
            QMessageBox.warning(self, "Anulare", "Anularea fără motiv este interzisă conform normelor de audit.")
            return

        self.db.anuleaza_transfer(tid, motiv.strip(), self.operator['nume'], self.operator['id'])
        QMessageBox.information(self, "Succes", f"Transferul {t['nr']} a fost anulat și marcat în jurnalul de audit.")
        self.load_data()

    def export_csv(self):
        transfers = self.db.get_all_transfers()
        if not transfers:
            QMessageBox.warning(self, "Export", "Nu există date de exportat.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvare Raport CSV", "export_transferuri.csv", "Fișiere CSV (*.csv)")
        if path:
            try:
                ExportService.export_csv(transfers, path)
                QMessageBox.information(self, "Export Reușit", f"Datele au fost exportate în:\\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Eroare Export", f"Eroare: {str(e)}")

    def export_html(self):
        transfers = self.db.get_all_transfers()
        if not transfers:
            QMessageBox.warning(self, "Export", "Nu există date de exportat.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvare Raport Registru", "registru_transferuri.html", "Fișiere HTML (*.html)")
        if path:
            try:
                inst = self.config.get('General', 'institutie', fallback='Ministerul Apărării Naționale')
                html = ExportService.generate_html_report(transfers, inst)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(html)
                QMessageBox.information(self, "Raport Generat", f"Raportul oficial a fost salvat în:\\n{path}\\n\\nPoate fi deschis în browser sau tipărit direct ca PDF.")
            except Exception as e:
                QMessageBox.critical(self, "Eroare Raport", f"Eroare: {str(e)}")
