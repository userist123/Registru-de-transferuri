"""Registru Transferuri Media v2.0 - Entry Point"""
import sys, logging
from pathlib import Path
from configparser import ConfigParser
from PyQt6.QtWidgets import QApplication, QMessageBox
from database.db import DatabaseManager
from ui.main_window import MainWindow

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    cfg = ConfigParser()
    cfg_file = Path("config.ini")
    if not cfg_file.exists():
        cfg['General'] = {'prefix_nr': 'MAPN', 'institutie': 'MApN', 'versiune': '2.0.0'}
        cfg['Database'] = {'path': 'transferuri.db'}
        with open(cfg_file, 'w') as f:
            cfg.write(f)
    cfg.read('config.ini')
    return cfg

def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("Registru Transferuri")
    
    try:
        config = load_config()
        db = DatabaseManager(config.get('Database', 'path', fallback='transferuri.db'))
        
        operator_name = "Administrator"
        window = MainWindow(db, config, operator_name)
        window.show()
        
        return app.exec()
    except Exception as e:
        QMessageBox.critical(None, "Eroare Critică", f"Aplicația nu poate porni:\\n{str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
