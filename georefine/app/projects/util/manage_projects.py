from georefine.app.projects.models import Project, MapLayer
from georefine.app import app, db
import georefine.util.shapefile as shp_util
import georefine.util.gis as gis_util
from sqlalchemy import Column, Float, Integer, String, MetaData
from geoalchemy import *
from geoalchemy.geometry import Geometry
import os, shutil, csv

def setUpSchema(project, data_dir, session=db.session): 
    schema_code = open(os.path.join(data_dir, "schema.py"), "rb").read()
    compiled_schema = compile(schema_code, '<schema>', 'exec') 
    schema_objs = {}
    exec compiled_schema in schema_objs
    schema = schema_objs['schema']
    for t in schema['metadata'].tables.values():
        t.name = "projects%s_%s" % (project.id, t.name)
    schema['metadata'].create_all(bind=session.bind)
    project.schema = schema

def setUpAppConfig(project, data_dir): 
    app_config_code = open(os.path.join(data_dir, "app_config.py"), "rb").read()
    compiled_app_config= compile(app_config_code, '<app_config>', 'exec') 
    app_config_objs = {}
    exec compiled_app_config in app_config_objs
    project.app_config = app_config_objs['app_config']

def setUpData(project, data_dir, session=db.session):
    schema = project.schema

    # Load data (in order defined by schema).
    for t in schema['ordered_sources']:
        table = t['source']

        # Get the filename for the table.
        table_filename = os.path.join(data_dir, 'data', "%s.csv" % (t['id']))

        # Read rows from data file.
        table_file = open(table_filename, 'rb') 
        reader = csv.DictReader(table_file)

        for row in reader:
            processed_row = {}
            # Parse values for columns.
            for c in table.columns:
                # Cast the value per the column's type.
                try:
                    # Defaults.
                    key = c.name
                    cast = str
                    if isinstance(c.type, Float):
                        cast = float
                    elif isinstance(c.type, Integer):
                        cast = int
                    elif isinstance(c.type, Geometry):
                        if row.has_key(c.name + "_wkt"):
                            key = c.name + "_wkt"
                            cast = WKTSpatialElement
                        if row.has_key(c.name + "_wkb"):
                            key = c.name + "_wkb"
                            cast = WKBSpatialElement

                    # Skip row if no corresponding key.
                    if not row.has_key(key): 
                        continue

                    # Handle empty values.
                    is_blank = False
                    if cast == float or cast == int:
                        if row[key] == '' or row[key] == None:
                            is_blank = True
                    elif not row[key]: 
                        is_blank = True
                    
                    # Process value if not blank.
                    if not is_blank:
                        processed_row[c.name] = cast(row[key])

                except Exception, err:
                    raise Exception, "Error: %s\n Table was: %s, row was: %s, column was: %s, cast was: %s" % (err, table.name, row, c.name, cast)
            # Insert values.
            # Note: geoalchemy doesn't seem to like bulk inserts yet, so we do it one at a time.
            session.execute(t['source'].insert().values(**processed_row))

        table_file.close()
        session.commit()

def setUpMapLayers(project, data_dir, session=db.session): 
    layers_schema = {
        'metadata': MetaData(),
        'sources': {},
        'ordered_sources': []
    }

    map_layers_dir = os.path.join(
        data_dir, 'data', "map_layers", "data", "shapefiles"
    )

    for layer in os.listdir(map_layers_dir):
        shp_file = os.path.join(map_layers_dir, layer, "%s.shp" % layer)
        reader = shp_util.get_shapefile_reader(shp_file)
        tname = "p_%s__l_%s" % (project.id, layer)
        geom_type = eval("%s(2)" % reader.schema['geometry'])
        if reader.schema['geometry'] == 'Polygon':
            geom_type = MultiPolygon(2)

        table_cols = [
            Column('id', Integer, primary_key=True),
            GeometryExtensionColumn('geom', geom_type)
        ]
        for p, p_type in reader.schema['properties'].items():
            if p_type == 'int':
                col_type = Integer
            elif p_type == 'str':
                col_type = String
            table_cols.append(Column(p, col_type))
        table = Table(tname, layers_schema['metadata'], *table_cols)
        GeometryDDL(table)

        layers_schema['sources'][layer] = table
        layers_schema['ordered_sources'].append(table)
        table.create(bind=session.bind)

        # Ingest layer data.
        for record in reader.records():
            if reader.schema['geometry'] == 'Polygon':
                record['geometry']['type'] = 'MultiPolygon'
                record['geometry']['coordinates'] = [
                    record['geometry']['coordinates']
                ]
            row = record['properties']
            processed_row = {}
            for c in table.columns:
                try:
                    key = c.name

                    # Id columns get record's id.
                    if key == 'id':
                        processed_row['id'] = record['id']

                    # Geometry columns get the record's geometry.
                    elif isinstance(c.type, Geometry):
                        geom_wkt = gis_util.geojson_to_wkt(record['geometry'])
                        processed_row['geom'] = WKTSpatialElement(geom_wkt)
                    else:
                        cast = str
                        if isinstance(c.type, Float):
                            cast = float
                        elif isinstance(c.type, Integer):
                            cast = int

                        # Otherwise skip if no corresponding key.
                        if not row.has_key(key): 
                            continue

                        # Handle empty values.
                        is_blank = False
                        if cast == float or cast == int:
                            if row[key] == '' or row[key] == None:
                                is_blank = True
                        elif not row[key]: 
                            is_blank = True
                        
                        # Process value if not blank.
                        if not is_blank:
                            processed_row[c.name] = cast(row[key])

                except Exception, err:
                    raise Exception, "Error: %s\n Table was: %s, row was: %s, column was: %s, cast was: %s" % (err, table.name, row, c.name, cast)

            session.execute(table.insert().values(**processed_row))

        session.commit()

        # Read SLD (if any).
        sld = None
        sld_file = os.path.join(map_layers_dir, layer, "%s.sld" % layer)
        if os.path.isfile(sld_file):
            sld = open(sld_file, "rb").read()

        # Create and saver layer model.
        layer_model = MapLayer(
            layer_id=layer,
            project=project,
            tbl=table.name,
            sld=sld
        )
        session.add(layer_model)
        session.commit()

        project.layers_schema = layers_schema

def setUpStaticFiles(project, data_dir):
    # Make project dir in static files storage location.
    project_static_dir = os.path.join(
        app.config['PROJECT_STATIC_FILES_DIR'],
        "project_%s" % project.id
    )
    os.mkdir(project_static_dir)
    
    # Copy static files (if any).
    static_dir_name = app.config['PROJECT_STATIC_DIR_NAME']
    static_files_dir = os.path.join(data_dir, static_dir_name)
    if os.path.isdir(static_files_dir):
        shutil.copytree(
            static_files_dir, 
            os.path.join(project_static_dir, static_dir_name)
        )

    # Save the project's static dir and url to the dir.
    project.static_files_dir = project_static_dir
    project.static_files_url = app.config['PROJECT_STATIC_FILES_URL'](project)


