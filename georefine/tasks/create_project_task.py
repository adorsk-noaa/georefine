"""
Task for creating a GeoRefine project.
"""
from georefine.app.projects.util.services import create_project
import task_manager
import logging


class LoggerLogHandler(logging.Handler):
    """ Custom log handler that logs messages to another
    logger. This can be used to chain together loggers. """
    def __init__(self, logger=None, **kwargs):
        logging.Handler.__init__(self, **kwargs)
        self.logger = logger

    def emit(self, record):
        self.logger.log(record.levelno, self.format(record))

class CreateProjectTask(task_manager.Task):

    def __init__(self, input_path=None, ingest_kwargs={}, **kwargs):
        super(CreateProjectTask, self).__init__(**kwargs)
        if not kwargs.get('data', None):
            self.data = {}
        self.input_path = input_path
        self.ingest_kwargs = ingest_kwargs

    def call(self):
        self.progress = 1
        self.logger.info("Starting...")
        project = create_project(self.input_path, logger=self.logger,
                                 ingest_kwargs=self.ingest_kwargs)
        self.data['project_id'] = project.id
        self.logger.info("Completed.")
