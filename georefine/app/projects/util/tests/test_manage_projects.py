import unittest
from georefine.util.sa.tests.basetest import BaseTest
from georefine.app.projects.models import Project
from georefine.app import db
import os

class Manage_Projects_Test(BaseTest):

	def test(self):
		pass

	def setUp(self):
		super(Manage_Projects_Test, self).setUp()

		db.drop_all()
		db.create_all()

		#project_dir = os.path.join(os.path.basename(__FILE__), 'test_manage_projects_project_dir')

		project = Project(id=1, name="test", dir=project_dir)
		#db.session.add(project)
		#db.session.commit()

if __name__ == '__main__':
	unittest.main()
