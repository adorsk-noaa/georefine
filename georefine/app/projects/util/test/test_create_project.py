import unittest
from georefine.app import app
from georefine.app.test.db_testcase import DBTestCase
from georefine.app.projects.util import services as services
import tempfile
from georefine.app.projects.util import data_generator as dg
import logging
import shutil
import os


logging.basicConfig()

class CreateProjectTest(DBTestCase):
    def setUp(self):
        DBTestCase.setUp(self)
        self.tmp_dir = tempfile.mkdtemp(prefix="gr.app.")
        self.data_dir = os.path.join(self.tmp_dir, "data")
        self.static_dir = os.path.join(self.tmp_dir, "static")
        app.config['DATA_DIR'] = self.data_dir
        app.static_folder = self.static_dir

    def tearDown(self):
        if self.tmp_dir and self.tmp_dir.startswith('/tmp') and \
        os.path.exists(self.tmp_dir) and False:
            shutil.rmtree(self.tmp_dir)
        DBTestCase.tearDown(self)

    def test_create_project(self):
        # Create project file.
        pfile = dg.generate_project_file()
        proj = services.create_project(project_file=pfile)
    
if __name__ == '__main__':
    unittest.main()
