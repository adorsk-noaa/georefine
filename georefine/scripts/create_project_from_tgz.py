from georefine.app.projects.util.services import create_project
import logging
import argparse


argparser = argparse.ArgumentParser()
argparser.add_argument('project_file')
argparser.add_argument('--db-uri')
argparser.add_argument('--commit-interval', default=int(1e5), type=int)

args = argparser.parse_args()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


ingest_kwargs = {'commit_interval': args.commit_interval}

p = create_project(args.project_file, logger=logger, db_uri=args.db_uri,
                   ingest_kwargs=ingest_kwargs)
print "project id: ", p.id
