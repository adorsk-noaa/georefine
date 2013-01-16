"""
Task for creating a GeoRefine project.
"""
from georefine.app.projects.util.services import delete_project
from georefine.app import db
from georefine.app.projects.models import Project
import task_manager
import logging


class DeleteProjectTask(task_manager.Task):

    def __init__(self, project_id=None, **kwargs):
        super(DeleteProjectTask, self).__init__(**kwargs)
        self.project_id = project_id
        if not kwargs.get('data', None):
            self.data = {}
        self.msg_logger = task_manager.get_message_logger(self)
        self.progress_logger = task_manager.get_progress_logger(self)

    def call(self):
        self.progress_logger.info(1)
        self.status = 'running'
        self.msg_logger.info("Starting...")
        project = db.session.query(Project).get(self.project_id)
        if project:
            delete_project(project)
        self.msg_logger.info("Completed.")
        self.progress_logger.info(100)
        self.status = 'resolved'
