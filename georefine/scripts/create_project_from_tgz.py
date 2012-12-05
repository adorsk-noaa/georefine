from georefine.app.projects.util.services import create_project
import logging
import argparse


argparser = argparse.ArgumentParser()
argparser.add_argument('project_file')
argparser.add_argument('--db-uri')


args = argparser.parse_args()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
p = create_project(args.project_file, logger=logger, db_uri=args.db_uri)
print "project id: ", p.id
