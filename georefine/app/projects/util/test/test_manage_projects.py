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


class ProjectsCommonTestCase(DBTestCase):

    rollback_each_time = True
    refresh_db_each_time = True
    clear_dirs_each_time = True

    @classmethod
    def setUpClass(cls):
        super(ProjectsCommonTestCase, cls).setUpClass()
        cls.test_project_file = dg.generate_project_file(
            source_defs=cls.get_source_defs())

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.test_project_file)
        super(ProjectsCommonTestCase, cls).tearDownClass()

    def setUp(self):
        DBTestCase.setUp(self)
        if not hasattr(self, 'tmpdir') or not os.path.exists(self.tmpdir):
            self.setUpDirs()

    def tearDown(self):
        if self.clear_dirs_each_time:
            self.clearDirs()
        DBTestCase.tearDown(self)

    @classmethod
    def setUpDirs(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="gr.app.")
        self.data_dir = os.path.join(self.tmp_dir, "data")
        self.static_dir = os.path.join(self.tmp_dir, "static")
        app.config['DATA_DIR'] = self.data_dir
        app.static_folder = self.static_dir

    @classmethod
    def clearDirs(self):
        if hasattr(self, 'tmp_dir') and self.tmp_dir.startswith('/tmp') and \
           os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    @classmethod
    def get_source_defs(cls):
        return None

class ManageProjectsTestCase(ProjectsCommonTestCase):

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


class ProjectServicesTestCase(ProjectsCommonTestCase):
    rollback_each_time = True
    refresh_db_each_time = False
    clear_dirs_each_time = False

    @classmethod
    def setUpClass(cls):
        super(ProjectServicesTestCase, cls).setUpClass()
        cls.setUpDirs()
        cls.con = cls.getConnection()
        cls.session = cls.getSession(cls.con)
        cls.refresh_db(bind=cls.session.bind)
        cls.project = services.create_project(cls.test_project_file,
                                              session=cls.session)
    @classmethod
    def tearDownClass(cls):
        services.delete_project(cls.project, session=cls.session)
        cls.clearDirs()
        super(ProjectServicesTestCase, cls).tearDownClass()

    @classmethod
    def get_source_defs(cls):
        return [
            {
                'id':  'Src1',
                'cols': [
                    {
                        'name': 'id',
                        'kwargs': {
                            'type_': 'Integer',
                            'primary_key': True,
                        },
                        'data': lambda n, r: None,
                    },
                    {
                        'name': 'float_',
                        'kwargs': {
                            'type_': 'Float',
                        },
                        'data': lambda n, r: float(n),
                    },
                    {
                        'class': 'GeometryExtensionColumn',
                        'name': 'geom',
                        'kwargs': {
                            'type_': 'MultiPolygon(2)',
                        },
                        'csv_name': 'geom_wkt',
                        'data': dg.generate_multipolygon_wkt,
                    },
                ],
                'GeometryDDL': True,
            }
        ]

    def test_execute_query(self):
        q = {
            "ID": "primary_q",
            "SELECT" : [
                {'EXPRESSION': '__Src1__id', 'ID': 'id'},
                {'EXPRESSION': '__Src1__float_', 'ID': 'float_'},
            ],
        }

        results = services.execute_queries(self.project, [q])
        expected_results = {'primary_q': [{u'float_': 0.0, u'id': 1}, {u'float_': 1.0, u'id': 2}, {u'float_': 2.0, u'id': 3}, {u'float_': 3.0, u'id': 4}, {u'float_': 4.0, u'id': 5}, {u'float_': 5.0, u'id': 6}, {u'float_': 6.0, u'id': 7}, {u'float_': 7.0, u'id': 8}, {u'float_': 8.0, u'id': 9}, {u'float_': 9.0, u'id': 10}]}
        self.assertEquals(results, expected_results)

    def test_get_keyed_results(self):
        bucket_entity = {
            'ID': 'bucket', 
            'EXPRESSION': '__Src1__id',
            'AS_HISTOGRAM': True, 
            'ALL_VALUES': True, 
            'MIN': 0, 
            'MAX': 10, 
            'NUM_CLASSES': 2,
        }
        key = {
            "KEY_ENTITY" : bucket_entity
        }

        primary_q = {
            "ID": "primary_q",
            "SELECT" : [
                {'ID': "count", 'EXPRESSION': 'func.count(__Src1__id)'},
            ],
            "GROUP_BY": [
                bucket_entity,
            ],
            "SELECT_GROUP_BY": True,
        }


        results = services.execute_keyed_queries(self.project, key, [primary_q])
        expected_results = [{'data': {'primary_q': {u'count': 4, u'bucket': u'[0.0, 5.0)'}}, 'key': '[0.0, 5.0)', 'label': '[0.0, 5.0)'}, {'data': {'primary_q': {u'count': 5, u'bucket': u'[5.0, 10.0)'}}, 'key': '[5.0, 10.0)', 'label': '[5.0, 10.0)'}]
        self.assertEquals(results, expected_results)


if __name__ == '__main__':
    unittest.main()
