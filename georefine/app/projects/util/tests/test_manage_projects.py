import unittest
from georefine.util.sa.tests.basetest import BaseTest
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
import georefine.app.projects.util.tests.data_generator as data_generator
from georefine.app import db
import os
import tempfile
import shutil
from sqlalchemy.orm import scoped_session, sessionmaker


class Manage_Projects_Test(BaseTest):

    def setUp(self):
        super(Manage_Projects_Test,self).setUp()
        self.project_dir = tempfile.mkdtemp(prefix="mp.")
        db.session = scoped_session(sessionmaker(bind=self.connection))
        #db.metadata.drop_all(bind=db.session.bind)
        #db.metadata.create_all(bind=db.session.bind)

    def test(self):
        _basedir = os.path.abspath(os.path.dirname(__file__))
        data_generator.generate_project_dir(self.project_dir)
        project = Project(name='test', dir=self.project_dir)
        db.session.add(project)
        db.session.commit()
        project.schema = manage_projects.getProjectSchema(project)
        manage_projects.setUpSchema(project)        
        manage_projects.setUpData(project)
    
    def tearDown(self):
        super(Manage_Projects_Test,self).tearDown()
        shutil.rmtree(self.project_dir)
        #self.trans.commit()

if __name__ == '__main__':
    unittest.main()
