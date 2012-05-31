from sqlalchemy import create_engine
from georefine.config import config as gr_conf

def get_engine():
	return create_engine(gr_conf['DB_URI'])
