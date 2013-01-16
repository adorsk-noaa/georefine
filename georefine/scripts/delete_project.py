from georefine.app.projects.util.services import delete_project_by_id
import logging
import argparse

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('project_id')
    argparser.add_argument('--verbose', '-v', action='store_true')

    args = argparser.parse_args()

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if args.verbose:
        handler = logging.StreamHandler()
    else:
        handler = logging.NullHandler()
    logger.addHandler(handler)

    delete_project_by_id(args.project_id, logger=logger)

if __name__ == '__main__':
    main()
