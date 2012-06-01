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
		self.project = Project(id=1, name='test', dir=project_dir)
		self.project.schema = manage_projects.getProjectSchema(self.project)
		manage_projects.setUpSchema(self.project)		
		manage_projects.setUpData(self.project)

	def test(self):
		id_entity = {'expression': '{Test1.id}', 'id': 'id'}
		name_entity = {'expression': '{Test1.name}', 'id': 'name'}

		# Test aggregates.
		data_entities = [id_entity]
		grouping_entities = [name_entity]
		aggregates = services.get_aggregates(self.project, data_entities=data_entities, grouping_entities=grouping_entities)
		#print aggregates

		map = services.get_map(self.project)
		#print map

	def tearDown(self):
		manage_projects.tearDownSchema(self.project)
		super(Services_Test, self).tearDown()

if __name__ == '__main__':
	unittest.main()
