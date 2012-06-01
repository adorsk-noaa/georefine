import unittest
from georefine.util.sa.tests.basetest import BaseTest
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
from georefine.app.projects.util import services
from georefine.app import db
import os

_basedir = os.path.abspath(os.path.dirname(__file__))

class Services_Test(BaseTest):

	def setUp(self):
		super(Services_Test, self).setUp()
		project_dir = os.path.join(_basedir, 'test_manage_projects_project_dir')
		self.project = Project(id=1, name='testproject', dir=project_dir)
		manage_projects.setUpSchema(self.project)

	def test(self):
		for e in services.get_entities(self.project):
			print e.name

	def tearDown(self):
		manage_projects.tearDownSchema(self.project)
		super(Services_Test, self).tearDown()

if __name__ == '__main__':
	unittest.main()
