import shutil
from datetime import datetime
from pathlib import Path


class BackupService:
    def __init__(self, db_path: str, backup_dir: str = "backups", max_backups: int = 30):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.max_backups = max_backups

    def create_backup(self) -> str:
        if not self.db_path.exists():
            raise FileNotFoundError("Baza de date nu există.")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"transferuri_backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_name
        shutil.copy2(self.db_path, backup_path)
        self._rotate_backups()
        return str(backup_path)

    def _rotate_backups(self):
        backups = sorted(self.backup_dir.glob("transferuri_backup_*.db"), key=lambda p: p.stat().st_mtime)
        while len(backups) > self.max_backups:
            oldest = backups.pop(0)
            oldest.unlink()

    def list_backups(self):
        return sorted(self.backup_dir.glob("transferuri_backup_*.db"), reverse=True)
