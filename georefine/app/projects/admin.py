from georefine.config import config as gr_conf
from georefine.app import db
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
import traceback


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

        return ProjectCreationForm(form, obj, csrf_enabled=False)
    

    def create_model(self, form):
        con, trans, session = db.get_session_w_external_trans(self.session)
        try:
            model = self.model()
            form.populate_obj(model)

            # Ingest project file.
            project_file = request.files.get('project_file')
            filename = secure_filename(project_file.filename)

            tmp_dir1 = tempfile.mkdtemp(prefix="gr1.")
            tmp_filename = os.path.join(tmp_dir1, filename)
            project_file.save(tmp_filename)

            # Unpack the project file.
            tmp_dir2 = tempfile.mkdtemp(prefix="gr2.")
            tar = tarfile.open(tmp_filename)
            tar.extractall(tmp_dir2)
            tar.close()

            session.add(model)
            session.commit()

        except Exception, ex:
            flash(
                gettext('Failed to create model. %(error)s, %(tb)s', 
                        error=str(ex), tb=traceback.format_exc()), 'error')
            trans.rollback()
            con.close()
            return False

        # Setup the project's tables and data.
        try:
            projects_manage.setUpSchema(model, tmp_dir2, session)
            projects_manage.setUpAppConfig(model, tmp_dir2)
            projects_manage.setUpMapLayers(model, tmp_dir2, session)
            projects_manage.setUpData(model, tmp_dir2, session)

        except Exception, ex:
            print "-" * 60
            traceback.print_exc()
            print "-" * 60
            flash(
                gettext(
                    'Unable to setup model schema or data. %(error)s, %(tb)s', 
                    error=str(ex), tb=traceback.format_exc()
                ), 
                'error'
            )
            trans.rollback()
            con.close()
            return False

        trans.commit()
        con.close()
        return True

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
