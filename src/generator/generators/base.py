"""
base.py — Abstract Base Class cho tất cả Generator modules
"""
from abc import ABC, abstractmethod
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from faker import Faker
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import FAKER_LOCALE, RANDOM_SEED


class BaseGenerator(ABC):
    """
    Base class cung cấp:
    - Kết nối SQLAlchemy
    - Faker instance (Vietnamese locale)
    - Seed cố định để reproducible
    - Helper methods chung
    """

    def __init__(self, connection_url: str):
        self.engine = create_engine(connection_url, echo=False, pool_pre_ping=True)
        self.fake = Faker(FAKER_LOCALE)
        Faker.seed(RANDOM_SEED)
        random.seed(RANDOM_SEED)

    def get_session(self) -> Session:
        return Session(self.engine)

    def truncate_table(self, table_name: str) -> None:
        """Xóa dữ liệu cũ trước khi generate (idempotent)."""
        with self.engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
            conn.commit()

    def status_choices(self) -> str:
        return random.choice(["active", "inactive", "pending"])

    def vn_phone(self) -> str:
        prefix = random.choice(["090", "091", "098", "086", "096", "097", "032", "033", "034"])
        return prefix + "".join([str(random.randint(0, 9)) for _ in range(7)])

    @abstractmethod
    def run(self) -> None:
        """Implement logic sinh dữ liệu trong subclass."""
        pass
