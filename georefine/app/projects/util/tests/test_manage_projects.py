import unittest
from georefine.util.sa.tests.basetest import BaseTest
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
from georefine.app import db
import os

class Manage_Projects_Test(BaseTest):

	def setUp(self):
		super(Manage_Projects_Test,self).setUp()
		#db.metadata.drop_all(bind=db.session.bind)
		#db.metadata.create_all(bind=db.session.bind)

	def test(self):
		_basedir = os.path.abspath(os.path.dirname(__file__))
		project_dir = os.path.join(_basedir, 'test_manage_projects_project_dir')

		project = Project(id=1, name='test', dir=project_dir)
		project.schema = manage_projects.getProjectSchema(project)
		manage_projects.setUpSchema(project)		
		manage_projects.setUpData(project)

if __name__ == '__main__':
	unittest.main()
