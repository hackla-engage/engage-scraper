import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def create_postgres_connection():
    uri = os.getenv('POSTGRES_URI')
    db = os.getenv('POSTGRES_DB')
    engine = create_engine('postgresql+psycopg2://{}/{}'.format(uri,db))
    return engine

def create_postgres_session(engine):
    Session = sessionmaker(bind=engine)
    return Session