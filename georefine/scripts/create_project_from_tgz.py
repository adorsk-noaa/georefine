import sys
from georefine.app.projects.util.services import create_project
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
p = create_project(sys.argv[1], logger=logger)
print "project id: ", p.id
