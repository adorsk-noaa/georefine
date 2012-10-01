from georefine.config import config as gr_conf
from . import models
from .util import manage_projects as projects_manage
from .util import services as projects_services

import flask
from flask import (request, redirect, url_for, flash)
import flask_admin
from flask_admin.base import expose
from flask_admin.contrib import sqlamodel
from flask.ext.admin.babel import gettext, ngettext, lazy_gettext
from flask_login import login_required, current_user
import flask_wtf
from werkzeug import secure_filename
import tempfile
import os
import shutil
import tarfile


class ProjectsAdmin(sqlamodel.ModelView):

    list_columns = ['name']
    form_columns = ['name']

    def __init__(self, session, endpoint='projects_admin', url='projects', **kwargs):
        super(self.__class__, self).__init__(
            models.Project,
            session, 
            url=url,
            endpoint=endpoint, 
            **kwargs
        )

    def is_accessible(self):
        return current_user.is_authenticated()

    def create_form(self, form, obj=None):
        """ Modify project creation form to add file field. """
        base_class = super(self.__class__, self).get_create_form()

        class ProjectCreationForm(base_class):
            project_file = flask_wtf.FileField('Project File')
            def __init__(self, *args, **kwargs):
                super(self.__class__, self).__init__(*args, **kwargs)

        return ProjectCreationForm(form, obj)
    

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            self.session.add(model)
            self.session.commit()
        except Exception, ex:
            flash(gettext('Failed to create model. %(error)s', error=str(ex)), 'error')
            return False

        # Setup project directory.
        project_dir = os.path.join(gr_conf['PROJECT_FILES_DIR'], str(model.id))
        os.mkdir(project_dir)
        model.dir = project_dir
        self.session.add(model)
        self.session.commit()

        # Upload project file.
        project_file = request.files.get('project_file')
        if project_file:
            filename = secure_filename(project_file.filename)

            # HACK.
            # @TODO: fix this later.
            tmp_dir = tempfile.mkdtemp(prefix="gr.")
            tmp_filename = os.path.join(tmp_dir, filename)
            project_file.save(tmp_filename)

            # Unpack the project file to the project dir.
            tar = tarfile.open(tmp_filename)
            tar.extractall(project_dir)
            tar.close()

            # Setup the project's tables and data.
            projects_manage.setUpSchema(model)
            projects_manage.setUpData(model)
            return True
        else:
            flash(gettext('Failed to create project. %(error)s', 
                          error="No file."), 'error')
            return False

    def delete_model(self, model):
        """
            Delete model.

            :param model:
                Model to delete
        """
        # Remove project maplayers.
        try:
            layers_schema =  projects_manage.get_project_layers_schema(model)
            layers_schema['metadata'].drop_all(bind=self.session.connection())
        except Exception, e:
            flash(gettext('Could not remove project layer tables. %(error)s', 
                          error=str(e)), 'error')
            return False

        # Remove project tables.
        try:
            schema =  projects_manage.getProjectSchema(model)
            schema['metadata'].drop_all(bind=self.session.connection())
        except Exception, e:
            flash(gettext('Could not remove project tables. %(error)s', 
                          error=str(e)), 'error')
            return False
            
        # Remove project directory.
        try:
            shutil.rmtree(model.dir)
        except Exception, e:
            flash(gettext('Could not remove project directory. %(error)s', 
                          error=str(e)), 'error')
            return False

        return super(self.__class__, self).delete_model(model)
