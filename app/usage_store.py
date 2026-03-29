import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .config import FREE_LIMIT, USAGE_DB_PATH


@dataclass
class UsageRecord:
    device_id: str
    used: int
    is_pro: bool


class UsageStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or USAGE_DB_PATH
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_records (
                    device_id TEXT PRIMARY KEY,
                    used INTEGER NOT NULL DEFAULT 0,
                    is_pro INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            connection.commit()

    def get_or_create(self, device_id: str) -> UsageRecord:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT device_id, used, is_pro FROM usage_records WHERE device_id = ?",
                (device_id,),
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO usage_records (device_id, used, is_pro) VALUES (?, 0, 0)",
                    (device_id,),
                )
                connection.commit()
                return UsageRecord(device_id=device_id, used=0, is_pro=False)
            return UsageRecord(
                device_id=row["device_id"],
                used=row["used"],
                is_pro=bool(row["is_pro"]),
            )

    def increment(self, device_id: str) -> UsageRecord:
        record = self.get_or_create(device_id)
        with self._connect() as connection:
            connection.execute(
                "UPDATE usage_records SET used = used + 1 WHERE device_id = ?",
                (device_id,),
            )
            connection.commit()
        return self.get_or_create(device_id)

    def reset(self, device_id: str) -> UsageRecord:
        with self._connect() as connection:
            connection.execute(
                "UPDATE usage_records SET used = 0 WHERE device_id = ?",
                (device_id,),
            )
            connection.commit()
        return self.get_or_create(device_id)

    @staticmethod
    def remaining(record: UsageRecord) -> int:
        if record.is_pro:
            return FREE_LIMIT
        return max(FREE_LIMIT - record.used, 0)
