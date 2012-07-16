from georefine.app import app
from georefine.config import config as gr_conf
from flask import Blueprint, request, redirect, render_template, flash, g, session, url_for, jsonify, json, Response
from werkzeug import secure_filename
from jinja2 import Markup
from georefine.app import db
from georefine.app.projects.forms import CreateProjectForm
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects as projects_manage
from georefine.app.projects.util import services as projects_services
import os
import tarfile

bp = Blueprint('projects', __name__, url_prefix='/projects', template_folder='templates')
context_root = "/%s" % app.config['APPLICATION_ROOT']
geoserver_url = "/geoserver"

@bp.route('/view/client/<int:project_id>/')
def georefine_client(project_id):
    project = Project.query.get(project_id)
    project.app_config = projects_manage.getProjectAppConfig(project)
    georefine_config = {
        "context_root": context_root,
        "geoserver_url": geoserver_url,
        "project_id": project_id,
        "filter_groups": project.app_config.get('filter_groups', {}),
        "facets": project.app_config.get('facets', {}),
        "facet_quantity_fields": project.app_config.get('facet_quantity_fields', {}),
        "charts": project.app_config.get('charts', {}),
        "map": project.app_config.get('map', {}),
        "summary_bar": project.app_config.get('summary_bar', {}),
        "initial_state": project.app_config.get('initial_state', {}),
    }
    json_georefine_config = json.dumps(georefine_config)
    return render_template("projects/georefine_client.html", context_root=context_root, georefine_config=Markup(json_georefine_config))

@bp.route('/test_facets/<int:project_id>/')
def test_facets(project_id):
    project = Project.query.get(project_id)
    project.app_config = projects_manage.getProjectAppConfig(project)
    json_facets = json.dumps(project.app_config.get('facets', '{}'))
    return render_template("projects/test_facets.html", context_root=context_root, project_id=project.id, facets=Markup(json_facets))

@bp.route('/test_charts/<int:project_id>/')
def test_charts(project_id):
    project = Project.query.get(project_id)
    project.app_config = projects_manage.getProjectAppConfig(project)
    json_charts = json.dumps(project.app_config.get('charts', '{}'))
    return render_template("projects/test_charts.html", context_root=context_root, project_id=project.id, charts=Markup(json_charts))

@bp.route('/test_map/<int:project_id>/')
def test_map(project_id):
    project = Project.query.get(project_id)
    project.app_config = projects_manage.getProjectAppConfig(project)
    json_map = json.dumps(project.app_config.get('map', '{}'))
    return render_template("projects/test_map.html", context_root=context_root, project_id=project.id, map=Markup(json_map), geoserver_url=geoserver_url)

@bp.route('/')
def home():
    return 'home'

@bp.route('/create_project/', methods=['GET', 'POST'])
def create_project():
    form = CreateProjectForm(request.form)
    if form.validate_on_submit():
        project = Project(name=form.name.data)

        # Create a directory for the project.
        # @TODO: change this to use project id or uuid later.
        project_dir = os.path.join(gr_conf['PROJECT_FILES_DIR'], project.name)
        os.mkdir(project_dir)

        project.dir = project_dir
        db.session.add(project)
        db.session.commit()

        project_file = request.files['project_file']
        if project_file:
            filename = secure_filename(project_file.filename)

            # HACK.
            # @TODO: fix this later.
            tmp_filename = os.path.join('/tmp', filename)
            project_file.save(tmp_filename)

            # Unpack the project file to the project dir.
            tar = tarfile.open(tmp_filename)
            tar.extractall(project_dir)
            tar.close()
            return "file is: {}".format(filename)
    else:
        flash('bad file')
    
    return render_template("projects/create_project.html", form=form)

@bp.route('/query_data/<int:project_id>/', methods=['GET', 'POST'])
def query_data(project_id):
    project = Project.query.get(project_id)
    project.schema = projects_manage.getProjectSchema(project)

    # Parse request parameters.
    data_entities = json.loads(request.args.get('data_entities', '[]'))
    grouping_entities = json.loads(request.args.get('grouping_entities', '[]'))
    sorting_entities = json.loads(request.args.get('sorting_entities', '[]'))
    filters = json.loads(request.args.get('filters', '[]'))

    results = projects_services.query_data(
            project, 
            data_entities = data_entities, 
            grouping_entities = grouping_entities, 
            sorting_entities = sorting_entities, 
            filters = filters
            )
    return jsonify(result=results)

@bp.route('/get_keyed_results/<int:project_id>/', methods=['GET', 'POST'])
def get_keyed_results(project_id):
    project = Project.query.get(project_id)
    project.schema = projects_manage.getProjectSchema(project)

    # Parse request parameters.
    key_def = json.loads(request.args.get('KEY', '{}'))
    query_defs= json.loads(request.args.get('QUERIES', '[]'))

    results = projects_services.get_keyed_results(
            project = project,
            key_def=key_def,
            query_defs = query_defs
            )

    return jsonify(results=results)

@bp.route('/get_aggregates/<int:project_id>/', methods=['GET', 'POST'])
def get_aggregates(project_id):
    project = Project.query.get(project_id)
    project.schema = projects_manage.getProjectSchema(project)

    # Parse request parameters.
    SELECT = json.loads(request.args.get('SELECT', '[]'))
    GROUP_BY = json.loads(request.args.get('GROUP_BY', '[]'))
    WHERE = json.loads(request.args.get('WHERE', '[]'))
    WITH_BASE = json.loads(request.args.get('WITH_BASE', 'false'))
    BASE_WHERE = json.loads(request.args.get('BASE_WHERE', '[]'))

    result = projects_services.get_aggregates(
            project, 
            SELECT = SELECT,
            GROUP_BY = GROUP_BY,
            WHERE = WHERE,
            WITH_BASE = WITH_BASE,
            BASE_WHERE = BASE_WHERE
            )

    return jsonify(result)

@bp.route('/get_map/<int:project_id>/', methods=['GET'])
def get_map(project_id):
    project = Project.query.get(project_id)
    project.schema = projects_manage.getProjectSchema(project)

    # Parse request parameters.
    data_entity = json.loads(request.args.get('data_entity', 'null'))
    geom_id_entity = json.loads(request.args.get('geom_id_entity', 'null'))
    geom_entity = json.loads(request.args.get('geom_entity', 'null'))
    grouping_entities = json.loads(request.args.get('grouping_entities', '[]'))
    filters = json.loads(request.args.get('filters', '[]'))

    # Parse WMS parameters.
    map_parameters = {}
    for wms_parameter in ['BBOX', 'FORMAT', 'WIDTH', 'HEIGHT', 'TRANSPARENT', 'SRS']:
        value = request.args.get(wms_parameter)
        if wms_parameter == 'WIDTH' or wms_parameter == 'HEIGHT':
            value = int(value)
        map_parameters[wms_parameter] = value

    map_image = projects_services.get_map(
            project, 
            data_entity=data_entity,
            geom_id_entity=geom_id_entity, 
            geom_entity=geom_entity,
            grouping_entities=grouping_entities,
            filters=filters,
            map_parameters=map_parameters
            )
    return Response(map_image, mimetype=map_parameters['FORMAT'])

