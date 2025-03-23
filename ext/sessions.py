import asyncio
import logging
import pickle
from enum import StrEnum
from pathlib import Path

logger = logging.getLogger("bot." + __name__)


class Category(StrEnum):
    EXCLUDED_SENDERS = "excluded_senders"
    INFORMED = "informed"


class Sessions:
    def __init__(self, storage_path: Path = None):
        self.sessions = {Category.EXCLUDED_SENDERS: {}, Category.INFORMED: {}}
        self.sessions_filename = ".sessions.pickle"
        self.storage_path = storage_path or Path(__file__).parent.parent.joinpath(
            "storage"
        )
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.sessions_path = self.storage_path / self.sessions_filename
        self.locker = asyncio.Lock()

    @property
    def excluded_senders(self):
        return self.sessions[Category.EXCLUDED_SENDERS]

    @property
    def informed(self):
        return self.sessions[Category.INFORMED]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.sessions)

    async def add(self, category: Category, group_id: int, value):
        async with self.locker:
            self.sessions[category].setdefault(group_id, set()).add(value)
            await self.save()

    async def remove(self, category: Category, group_id: int, value):
        async with self.locker:
            self.sessions[category][group_id].discard(value)
            await self.save()

    def is_exists(self, category: Category, group_id: int, value):
        return value in self.sessions.get(category, {}).get(group_id, set())

    def _save(self):
        try:
            with self.sessions_path.open("wb") as f:
                pickle.dump(self.sessions, f)
        except Exception as e:
            logger.error(e)

    async def save(self):
        try:
            # Run the blocking I/O operation in a separate thread
            await asyncio.to_thread(self._save)
        except Exception as e:
            logger.error(f"Error during save: {e}")

    def load(self, storage_file: str = None) -> None:
        if not self.storage_path.exists():
            return None
        if self.sessions_path.exists():
            try:
                with self.sessions_path.open("rb") as f:
                    self.sessions = pickle.load(f)
                    logger.debug(f"Loaded: {self.sessions}")
            except Exception as e:
                logger.error(e)
