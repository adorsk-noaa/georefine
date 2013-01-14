import unittest
from georefine.app.projects.util.test.test_services import (
    ProjectsCommonTestCase)
from georefine.tasks.create_project_task import CreateProjectTask
import os
import shutil
import tempfile
import logging


logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

class CreateProjectTaskTestCase(ProjectsCommonTestCase):
    def test_create_project_task(self):
        task = CreateProjectTask(input_path=self.test_project_file, logger=logger)
        task.call()
        self.assertEquals(task.data,  {'project_id': 1})

if __name__ == '__main__':
    unittest.main()
