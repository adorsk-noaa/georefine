import pyspatialite
import sys
sys.modules['pysqlite2'] = pyspatialite
import unittest
from sqlalchemy import (create_engine, MetaData)
from sqlalchemy.orm import (scoped_session, sessionmaker)
import tempfile
import os


class SpatialiteTestCase(unittest.TestCase):
    def setUp(self):
        self.delete_on_tearDown = True
        code, self.dbfile = tempfile.mkstemp(suffix=".sqlite")
        self.engine = create_engine("sqlite:///%s" % self.dbfile)
        self.connection = self.engine.connect()
        self.session = scoped_session(sessionmaker(bind=self.connection))
        self.connection.execute("SELECT InitSpatialMetaData()") 

    def tearDown(self):
        if self.delete_on_tearDown:
            os.remove(self.dbfile)

if __name__ == '__main__':
    unittest.main()
