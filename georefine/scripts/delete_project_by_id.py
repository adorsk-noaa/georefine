from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
from georefine.app import db
from sqlalchemy.orm import sessionmaker

import sys

def main():
    project_id = sys.argv[1]

    delete_project_dir = False
    delete_dir_msg = ""
    if len(sys.argv) > 2:
        delete_project_dir = True
        delete_dir_msg = ", and its directory."

    print >> sys.stderr, "Deleting project%s." % delete_dir_msg
    confirm = raw_input("Type 'y' to confirm: ")
    if confirm == 'y':
        manage_projects.deleteProject(int(project_id), delete_project_dir)
    else:
        "You did not type 'y', nothing has been done, exiting."
        
if __name__ == '__main__':
    main()
