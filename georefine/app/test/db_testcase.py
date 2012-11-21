import pyspatialite
import sys
sys.modules['pysqlite2'] = pyspatialite
import unittest
from georefine.app import app
from georefine.app import db
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

class DBTestCase(unittest.TestCase):

    rollback_each_time = True
    refresh_db_each_time = False

    @classmethod
    def get_db_uri(cls):
        return 'sqlite://'

    @classmethod
    def spatializeDB(clz, con):
        con.execute("SELECT InitSpatialMetaData()") 

    @classmethod
    def getConnection(cls):
        engine = create_engine(cls.get_db_uri())
        return engine.connect()

    @classmethod
    def getSession(cls, con=None):
        if not con:
            con = cls.getConnection()
        return scoped_session(sessionmaker(bind=con))

    def setUp(self):
        if self.rollback_each_time:
            self.con = self.getConnection()
            self.trans = self.con.begin()
            
        db.session = self.getSession(self.con)
        if self.refresh_db_each_time:
            self.refresh_db(bind=db.session.bind)

    def tearDown(self):
        if self.rollback_each_time:
            self.trans.rollback()

    @classmethod
    def refresh_db(clz, bind=None):
        db.clear_db(bind=bind)
        db.init_db(bind=bind)
