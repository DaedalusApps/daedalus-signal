"""
DaedalusSignal Database Setup
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

Base = declarative_base()


def init_db():
    """Initialize the database with all tables."""
    from app import models  # noqa: F401
    Base.metadata.create_all(engine)


def get_session():
    """Get a database session."""
    return Session()


def close_session(session):
    """Close a database session."""
    session.close()
