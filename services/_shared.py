import os
from types import TracebackType
from typing import Optional, Type

from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
)
from sqlalchemy.orm import sessionmaker

load_dotenv()

connection_str = "mysql+mysqlconnector://{}:{}@{}:{}/{}".format(
    os.environ["MYSQL_USER"],
    os.environ["MYSQL_PASS"],
    os.environ["MYSQL_URI"],
    os.environ["MYSQL_PORT"],
    "nikodex",
)

engine = create_engine(connection_str, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class SessionManager:
    def __enter__(self):
        self.session = SessionLocal()
        return self.session

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ):
        if exc_type:
            print("ERR in DB!")
            print(exc_value)
            self.session.rollback()
            return False

        self.session.close()
