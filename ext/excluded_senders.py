import logging
import pickle
from pathlib import Path

logger = logging.getLogger("bot." + __name__)


class ExcludedSenders:
    def __init__(self, storage_path: Path):
        self.excluded_senders = {}
        self.excluded_senders_filename = ".excluded_senders.pickle"
        self.storage_path = storage_path

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.excluded_senders)

    def add_excluded_sender(self, sender_id, group_id):
        self.excluded_senders.setdefault(group_id, set()).add(sender_id)
        self.save_excluded_senders()

    def remove_excluded_sender(self, sender_id, group_id):
        if group_id in self.excluded_senders:
            self.excluded_senders[group_id].discard(sender_id)
            self.save_excluded_senders()

    def is_excluded_sender(self, sender_id, group_id):
        return (
            group_id in self.excluded_senders
            and sender_id in self.excluded_senders[group_id]
        )

    def save_excluded_senders(self, storage_file: str = None):
        storage_file = storage_file or self.excluded_senders_filename
        self.storage_path.mkdir(parents=True, exist_ok=True)
        excluded_senders_path = self.storage_path / storage_file
        try:
            with excluded_senders_path.open("wb") as f:
                pickle.dump(self.excluded_senders, f)
        except Exception as e:
            logger.error(e)

    def load_excluded_senders(self, storage_file: str = None) -> None:
        storage_file = storage_file or self.excluded_senders_filename
        if not self.storage_path.exists():
            return None
        excluded_senders_path = self.storage_path / storage_file
        if excluded_senders_path.exists():
            try:
                with excluded_senders_path.open("rb") as f:
                    self.excluded_senders = pickle.load(f)
                    logger.debug(f"Loaded: {self.excluded_senders}")
            except Exception as e:
                logger.error(e)
