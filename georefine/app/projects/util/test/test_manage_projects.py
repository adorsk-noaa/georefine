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

class ManageProjectsTestCase(DBTestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_project_file = dg.generate_project_file()

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.test_project_file)

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
        project = services.create_project(project_file=self.test_project_file)
        self.assertTrue(getattr(project, 'id', None) is not None)

    def test_delete_project(self):
        project = services.create_project(project_file=self.test_project_file)
        dir_attrs = ['data_dir', 'static_dir']
        project_dirs = [getattr(project, dir_attr) for dir_attr in dir_attrs]

        delete_result = services.delete_project(project)
        self.assertTrue(delete_result)
        for dir_ in project_dirs:
            self.assertFalse(os.path.exists(dir_))

        num_layers = db.session.query(project_models.MapLayer).count()
        self.assertEquals(num_layers, 0)

    def test_execute_query(self):
        project = services.create_project(project_file=self.test_project_file)
        q = {
            "ID": "primary_q",
            "SELECT" : [
                {'EXPRESSION': '__Src1__id', 'ID': 'id'},
                {'EXPRESSION': '__Src1__float_', 'ID': 'float_'},
            ],
        }

        results = services.execute_queries(project, [q])
        print results

    def test_get_keyed_results(self):
        project = services.create_project(project_file=self.test_project_file)
        bucket_entity1 = {
            'ID': 'bucket', 
            'EXPRESSION': '__Src1__float_',
            'AS_HISTOGRAM': True, 
            'ALL_VALUES': True, 
            'MIN': 0, 
            'MAX': 10, 
            'NUM_CLASSES': 5
        }
        key = {
            "KEY_ENTITY" : bucket_entity1
        }

        primary_q = {
            "AS_DICTS": True, 
            "ID": "primary_q",
            "SELECT" : [
                {'ID': "src1_id", 'EXPRESSION': '__Src1__id'},
            ],
            "GROUP_BY": [
                {"ID": "src1_id"},
                bucket_entity1,
            ],
            "SELECT_GROUP_BY": True,
        }

        results = services.execute_keyed_queries(project, key, [primary_q])
        print results


if __name__ == '__main__':
    unittest.main()
