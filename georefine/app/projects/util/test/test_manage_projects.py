import unittest
from georefine.app import app
from georefine.app import db
from georefine.app.test.db_testcase import DBTestCase
from georefine.app.projects.util import services as services
from georefine.app.projects import models as project_models
import tempfile
from georefine.app.projects.util import data_generator as dg
import logging
import shutil
import os


logging.basicConfig()

class ManageProjectTest(DBTestCase):
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

    def xtest_create_project(self):
        pfile = dg.generate_project_file()
        project = services.create_project(project_file=pfile)
        self.assertTrue(getattr(project, 'id', None) is not None)

    def test_delete_project(self):
        pfile = dg.generate_project_file()
        project = services.create_project(project_file=pfile)
        dir_attrs = ['data_dir', 'static_dir']
        project_dirs = [getattr(project, dir_attr) for dir_attr in dir_attrs]

        delete_result = services.delete_project(project)
        self.assertTrue(delete_result)
        for dir_ in project_dirs:
            self.assertFalse(os.path.exists(dir_))

        num_layers = db.session.query(project_models.MapLayer).count()
        self.assertEquals(num_layers, 0)
    
if __name__ == '__main__':
    unittest.main()
