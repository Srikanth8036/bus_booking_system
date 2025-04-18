from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schemas.schemas import Base

DATABASE_URL = "sqlite:///./bus_booking.db"


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.engine = create_engine(
                DATABASE_URL, connect_args={"check_same_thread": False}
            )
            cls._instance.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=cls._instance.engine
            )
        return cls._instance

    def get_session(self):
        return self.SessionLocal()


def get_db():
    db = Database().get_session()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    db_instance = Database()
    Base.metadata.create_all(bind=db_instance.engine)
