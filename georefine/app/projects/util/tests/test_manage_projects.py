import unittest
from georefine.util.sa.tests.basetest import BaseTest
from georefine.app.projects.models import Project
from georefine.app import db
import os

class Manage_Projects_Test(BaseTest):

	def setUp(self):
		super(Manage_Projects_Test,self).setUp()
		db.metadata.drop_all(bind=db.session.bind)
		db.metadata.create_all(bind=db.session.bind)

	def test(self):
		_basedir = os.path.abspath(os.path.dirname(__file__))
		project_dir = os.path.join(_basedir, 'test_manage_projects_project_dir')

		from time import time
		project = Project(name=time(), dir=project_dir)

		db.session.add(project)
		db.session.commit()
	
if __name__ == '__main__':
	unittest.main()
