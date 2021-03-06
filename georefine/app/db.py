from georefine.app import app
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)
metadata = MetaData()
session = scoped_session(sessionmaker(bind=engine))

def init_db(bind=engine, checkfirst=True, **kwargs):
    metadata.create_all(bind=bind, checkfirst=checkfirst, **kwargs)

def clear_db(bind=engine):
	metadata.drop_all(bind=bind)

def get_session_w_external_trans(session_=None, new_connection=False):
    if not session_:
        session_ = session()
    if new_connection:
        con = session_.bind.engine.connect()
    else:
        con = session_.bind
    trans = con.begin()
    session = sessionmaker(bind=con)()
    return con, trans, session
