import sys
import configparser
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from database.db import DatabaseManager
from ui.theme import DARK_STYLE
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config_path = Path(__file__).parent / "config.ini"
    if config_path.exists():
        config.read(config_path, encoding='utf-8')
    else:
        config['institutie'] = {'nume': 'MAPN', 'prefix': 'MAPN'}
        config['database'] = {'path': 'transferuri.db'}
    return config


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)

    config = load_config()
    db_path = config.get('database', 'path', fallback='transferuri.db')
    db = DatabaseManager(db_path)

    login = LoginDialog(db)
    if login.exec() != LoginDialog.DialogCode.Accepted:
        sys.exit(0)

    window = MainWindow(db, login.authenticated_operator, config)
    window.show()

    exit_code = app.exec()
    db.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
