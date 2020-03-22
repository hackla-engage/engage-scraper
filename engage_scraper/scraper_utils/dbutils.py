import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_postgres_tables(Base, engine):
    Base.metadata.create_all(engine)


def create_postgres_connection():
    username = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    hostname = os.getenv('POSTGRES_HOST', "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv('POSTGRES_DB')
    engine = create_engine(
        f"postgresql+psycopg2://{username}:{password}@{hostname}:{port}/{db}")
    return engine


def create_postgres_session(engine):
    Session = sessionmaker(bind=engine)
    return Session
