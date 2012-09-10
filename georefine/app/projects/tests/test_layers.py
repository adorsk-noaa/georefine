import unittest
from georefine.util.sa.tests.spatialite import SpatialiteTestCase
import georefine.app as gr
import georefine.app.db as db
from georefine.app.projects.models import Project, MapLayer
import georefine.app.projects.util.manage_projects as manage_projects
import georefine.app.projects.util.tests.data_generator as data_generator
import tempfile
import shutil


class LayersTest(SpatialiteTestCase):

    def setUp(self):
        super(LayersTest, self).setUp()

        db.engine = self.engine
        db.session = scoped_session(sessionmaker(bind=self.connection))
        db.init_db()

        self.project_dir = tempfile.mkdtemp(prefix="lt.")

        gr.app.config['TESTING'] = True
        self.app = gr.app.test_client()
        self.base_path = '/projects'

    def tearDown(self):
        super(LayersTest, self).tearDown()
        shutil.rmtree(self.project_dir)

    def test_getMap(self):
        data_generator.generate_project_dir(self.project_dir)
        project = Project(name='test', dir=self.project_dir)
        db.session.add(project)
        db.session.commit()

        manage_projects.setUpSchema(project)        
        manage_projects.setUpData(project)

        layer = db.session.query(MapLayer).first()

        wms_params = {
            "LAYERS": layer.layer_id,
            "SERVICE": "WMS",
            "VERSION": "1.1.0",
            "REQUEST": u"GetMap",
            "STYLES": '',
            "FORMAT": "image/gif",
            "SRS": "EPSG:4326",
            "BBOX": "0,0,5,5",
            "WIDTH": "256",
            "HEIGHT": "256",
        }

        r = self.app.get("%s/layer/%s/wms" % (self.base_path, layer.layer_id), 
                         query_string=wms_params)

if __name__ == '__main__':
    unittest.main()
