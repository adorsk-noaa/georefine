from georefine import config
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(config.SQLALCHEMY_DATABASE_URI, convert_unicode=True)
metadata = MetaData()
session = scoped_session(sessionmaker(bind=engine))

def init_db():
    metadata.create_all(bind=engine, checkfirst=True)

def clear_db():
	metadata.drop_all(bind=engine)

def get_session_w_external_trans(orig_session):
    con = orig_session.bind.connect()
    trans = con.begin()
    new_session = sessionmaker()(bind=con)
    return con, trans, new_session
