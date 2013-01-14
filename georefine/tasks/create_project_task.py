"""
Task for creating a GeoRefine project.
"""
from georefine.app.projects.util.services import create_project
import task_manager
import logging


class CreateProjectTask(task_manager.Task):

    def __init__(self, input_path=None, ingest_kwargs={}, **kwargs):
        super(CreateProjectTask, self).__init__(**kwargs)
        if not kwargs.get('data', None):
            self.data = {}
        self.input_path = input_path
        self.ingest_kwargs = ingest_kwargs
        
        self.msg_logger = task_manager.get_message_logger(self)
        self.progress_logger = task_manager.get_progress_logger(self)

    def call(self):
        self.progress_logger.info(1)
        self.status = 'running'
        self.msg_logger.info("Starting...")
        project = create_project(self.input_path, msg_logger=self.msg_logger,
                                 progress_logger=self.progress_logger,
                                 ingest_kwargs=self.ingest_kwargs)
        self.data['project_id'] = project.id
        self.msg_logger.info("Completed.")
        self.progress_logger.info(100)
        self.status = 'resolved'
