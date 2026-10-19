from sqlmodel import SQLModel, Session, create_engine
import os
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

engine = create_engine(database_url, echo=True)

def create_tables() -> None:
    """Create all tables that do not exist yet."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Provide a new database session
    """
    with Session(engine) as session:
        yield session
    
