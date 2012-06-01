from georefine.config import config as gr_conf
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(gr_conf['DB_URI'], convert_unicode=True)
metadata = MetaData()
session = scoped_session(sessionmaker(bind=engine))

def init_db():
    metadata.create_all(bind=engine)

def clear_db():
	metadata.drop_all(bind=engine)
