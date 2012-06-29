from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
from georefine.app import db
from sqlalchemy.orm import sessionmaker

import sys

def main():
    project_name = sys.argv[1]
    project_dir = sys.argv[2]

    # Setup transactional session.
    Session = sessionmaker()
    connection = db.engine.connect()
    transaction = connection.begin()
    db.session = Session(bind=connection)


    print >> sys.stderr, "Creating project '%s' using dir '%s'" % (project_name, project_dir)
    project = Project(name=project_name, dir=project_dir)
    db.session.add(project)
    db.session.commit()
    print >> sys.stderr, "Project id is: %s" % project.id

    print >> sys.stderr, "Setting up project schema..."
    manage_projects.setUpSchema(project)

    print >> sys.stderr, "Ingesting project data..."
    manage_projects.setUpData(project)

    # Commit the transaction.
    transaction.commit()
    db.session.close()


if __name__ == '__main__':
    main()
