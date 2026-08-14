import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List

class BackupService:
    def __init__(self, db_path: str, backup_dir: str = "backups"):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, operator_name: str) -> Path:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Baza de date {self.db_path} nu exista.")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.backup_dir / f"backup_transferuri_{timestamp}.db"
        
        shutil.copy2(self.db_path, dest)
        self._prune_old_backups(keep=30)
        return dest

    def _prune_old_backups(self, keep: int = 30):
        backups = sorted(self.backup_dir.glob("backup_transferuri_*.db"), key=lambda f: f.stat().st_mtime)
        if len(backups) > keep:
            for old in backups[:-keep]:
                try:
                    old.unlink()
                except Exception:
                    pass

    def list_backups(self) -> List[Path]:
        return sorted(self.backup_dir.glob("backup_transferuri_*.db"), key=lambda f: f.stat().st_mtime, reverse=True)
