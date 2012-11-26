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
from StringIO import StringIO
import os
from PIL import Image


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
        if not hasattr(self, 'tmp_dir') or not os.path.exists(self.tmp_dir):
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
    def clearDirs(cls):
        if hasattr(cls, 'tmp_dir') and cls.tmp_dir.startswith('/tmp') and \
           os.path.exists(cls.tmp_dir):
            shutil.rmtree(cls.tmp_dir)

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


class ProjectsServicesCommonTestCase(ProjectsCommonTestCase):
    rollback_each_time = True
    refresh_db_each_time = False
    clear_dirs_each_time = False

    @classmethod
    def setUpClass(cls):
        super(ProjectsServicesCommonTestCase, cls).setUpClass()
        cls.setUpDirs()
        cls.spatializeDB(cls.getConnection())
        cls.con = cls.getConnection()
        cls.session = cls.getSession(cls.con)
        cls.refresh_db(bind=cls.session.bind)
        cls.project = services.create_project(cls.test_project_file,
                                              session=cls.session)
    @classmethod
    def tearDownClass(cls):
        cls.clearDirs()
        super(ProjectsServicesCommonTestCase, cls).tearDownClass()

    @classmethod
    def get_source_defs(cls):
        return dg.generate_source_defs()

class ProjectsServicesTestCase(ProjectsServicesCommonTestCase):
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

class ProjectsServicesMapCommonTestCase(ProjectsServicesCommonTestCase):

    def bytes_to_img(self, img_data):
        img_file = StringIO(img_data)
        img = Image.open(img_file)
        return img

    def img_is_blank(self, img_data):
        img = self.bytes_to_img(img_data)
        for pix in img.getdata():
            if pix != (255,255,255,):
                return False
        return True

    def show_img(self, img_data):
        self.bytes_to_img(img_data).show()

class ProjectsServicesDataMapTestCase(ProjectsServicesMapCommonTestCase):

    @classmethod
    def get_db_uri(cls):
        """ Need to use disk-based db in order for mapping backend to access
        backend. """
        if not hasattr(cls, 'db_file'):
            hdnl, cls.db_file = tempfile.mkstemp(suffix=".db.sqlite", dir=cls.tmp_dir)
        return "sqlite:///%s" % cls.db_file

    def test_get_data_map(self):
        data_entity = {
            'EXPRESSION': 'func.sum(__Src1__float_)', 
            'ID': 'data',
            'MIN': 0,
            'MAX': 10,
        }
        geom_entity = {'EXPRESSION': '__Src1__geom', 'ID': 'geom'}
        geom_id_entity = {'EXPRESSION': '__Src1__id', 'ID': 'id'}
        query = {
            "ID": "query",
            "SELECT" : [
                data_entity,
                geom_entity,
                geom_id_entity,
            ],
            "GROUP_BY": [
                geom_entity,
                geom_id_entity,
            ]
        }
        wms_parameters = {
            'SERVICE': 'WMS',
            'VERSION': '1.1.1',
            'REQUEST': 'GetMap',
            'STYLES': '',
            'FORMAT': 'image/png',
            'SRS': 'EPSG:4326',
            'BBOX': '0,0,5,5',
            'WIDTH': 200,
            'HEIGHT': 200,
        }
        img = services.get_data_map(self.project, query, data_entity=data_entity,
                geom_id_entity=geom_id_entity, geom_entity=geom_entity, 
                wms_parameters=wms_parameters)
        self.assertFalse(self.img_is_blank(img))
        #self.show_img(img)

class ProjectsServicesLayerMapTestCase(ProjectsServicesMapCommonTestCase):

    def test_get_layer_map(self):
        layer = self.project.layers[0]
        wms_parameters = {
            'SERVICE': 'WMS',
            'VERSION': '1.1.1',
            'REQUEST': 'GetMap',
            'LAYERS': layer.layer_id,
            'STYLES': '',
            'FORMAT': 'image/png',
            'SRS': 'EPSG:4326',
            'BBOX': '0,0,15,15',
            'WIDTH': 200,
            'HEIGHT': 200,
        }
        img = services.get_layer_map(layer, wms_parameters=wms_parameters)
        self.assertFalse(self.img_is_blank(img))

if __name__ == '__main__':
    unittest.main()
