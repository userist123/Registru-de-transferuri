import sys
from pathlib import Path
from configparser import ConfigParser
from PyQt6.QtWidgets import QApplication, QMessageBox
from database.db import DatabaseManager
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow

def load_config() -> ConfigParser:
    config = ConfigParser()
    config_path = Path(__file__).parent / "config.ini"
    if not config_path.exists():
        config['General'] = {
            'institutie': 'Ministerul Apărării Naționale',
            'prefix_nr': 'MAPN',
            'auto_backup_on_close': 'true',
            'verificare_hash_startup': 'true'
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
    else:
        config.read(config_path, encoding='utf-8')
    return config

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Registru Transferuri Media v3.0")

    config = load_config()
    db_path = Path(__file__).parent / "transferuri.db"
    db = DatabaseManager(str(db_path))

    login = LoginDialog(db)
    if login.exec() != LoginDialog.DialogCode.Accepted:
        sys.exit(0)

    operator = login.authenticated_operator
    if not operator:
        sys.exit(0)

    window = MainWindow(db, operator, config)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
