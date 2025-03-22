import logging
import pickle
from enum import StrEnum
from pathlib import Path

logger = logging.getLogger("bot." + __name__)


class Category(StrEnum):
    EXCLUDED_SENDERS = "excluded_senders"
    INFORMED = "informed"


class Sessions:
    def __init__(self, storage_path: Path):
        self.sessions = {Category.EXCLUDED_SENDERS: {}, Category.INFORMED: {}}
        self.sessions_filename = ".sessions.pickle"
        self.storage_path = storage_path

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

    def add(self, category: Category, group_id: int, value):
        self.sessions[category].setdefault(group_id, set()).add(value)
        self.save()

    def remove(self, category: Category, group_id: int, value):
        self.sessions[category][group_id].discard(value)
        self.save()

    def is_exists(self, category: Category, group_id: int, value):
        return value in self.sessions.get(category, {}).get(group_id, set())

    def add_excluded_sender(self, sender_id, group_id: int):
        self.add(Category.EXCLUDED_SENDERS, group_id, sender_id)

    def remove_excluded_sender(self, sender_id, group_id: int):
        category = Category.EXCLUDED_SENDERS
        if group_id in self.sessions[category]:
            self.remove(category, group_id, sender_id)  # remove

    def is_excluded_sender(self, sender_id: int, group_id: int):
        category = Category.EXCLUDED_SENDERS
        return self.is_exists(category, group_id, sender_id)

    def save(self, storage_file: str = None):
        storage_file = storage_file or self.sessions_filename
        self.storage_path.mkdir(parents=True, exist_ok=True)
        excluded_senders_path = self.storage_path / storage_file
        try:
            with excluded_senders_path.open("wb") as f:
                pickle.dump(self.sessions, f)
        except Exception as e:
            logger.error(e)

    def load(self, storage_file: str = None) -> None:
        storage_file = storage_file or self.sessions_filename
        if not self.storage_path.exists():
            return None
        sessions_path = self.storage_path / storage_file
        if sessions_path.exists():
            try:
                with sessions_path.open("rb") as f:
                    self.sessions = pickle.load(f)
                    logger.debug(f"Loaded: {self.sessions}")
            except Exception as e:
                logger.error(e)
