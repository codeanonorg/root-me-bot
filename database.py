from contextlib import ContextDecorator
from copy import deepcopy
from dataclasses import dataclass, field
import json
from json.decoder import JSONDecodeError
from typing import Any, Iterable, Tuple, Union
from model import User
from pathlib import Path


@dataclass
class Database:
    filename: Path
    autocommit: bool = field(default=False)
    data: dict[str, User] = field(init=False)

    def __post_init__(self):
        try:
            with self.filename.open("r") as f:
                self.data = {
                    uid: User(**data)
                    for uid, data in json.load(f).values()
                }
        except (FileNotFoundError, JSONDecodeError):
            self.filename.write_text("{}")
            self.data = dict()

    def transaction(self) -> "TransactionContext":
        return TransactionContext(self)

    def set_user(self, user: User) -> None:
        self.data[user.id_auteur] = user
        if self.autocommit:
            self.save()

    def get_user(self, user_id: str) -> Union[User, None]:
        return self.data.get(user_id)

    def remove_user(self, user_id: str) -> bool:
        if user_id in self.data:
            del self.data[user_id]
            if self.autocommit:
                self.save()
            return True
        return False

    def iter_ids(self) -> Iterable[str]:
        return self.data.keys()

    def iter_users(self) -> Iterable[User]:
        return self.data.values()

    def save(self) -> None:
        data = {uid: user.dict() for uid, user in self.data.items()}
        with self.filename.open("w") as f:
            json.dump(data, f, default=str)

    def reset(self) -> None:
        self.data = {}
        self.save()


@dataclass
class TransactionContext(ContextDecorator):
    db: Database
    _old_autocommit: bool = field(init=False)
    _old_data: dict[str, User] = field(init=False)

    def __post_init__(self):
        self._old_autocommit = self.db.autocommit
        self._old_data = deepcopy(self.db.data)

    def __enter__(self):
        self.db.autocommit = False

    def __exit__(self, *exc: Tuple[Any]):
        if len(exc) == 0:
            self.db.save()
        else:
            self.db.data = self._old_data
        self.db.autocommit = self._old_autocommit
        return False
