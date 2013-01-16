import unittest
from georefine.app.projects.util.test.test_services import (
    ProjectsCommonTestCase)
from georefine.app.projects.util.services import create_project
from georefine.tasks.delete_project_task import DeleteProjectTask
import os
import shutil
import tempfile
import logging


logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

class DeleteProjectTaskTestCase(ProjectsCommonTestCase):
    def test_delete_project_task(self):
        project = create_project(input_path=self.test_project_file)
        task = DeleteProjectTask(project_id=project.id)
        task.call()
        self.assertEquals(task.status,  'resolved')

if __name__ == '__main__':
    unittest.main()
