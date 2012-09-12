from georefine.app.projects.models import Project, MapLayer
from georefine.app import db
import georefine.util.shapefile as shp_util
import georefine.util.gis as gis_util
from sqlalchemy import Column, Float, Integer, String
from geoalchemy import *
from geoalchemy.geometry import Geometry
import os, shutil, csv

def getProjectSchema(project):
    schema_file = os.path.join(project.dir, 'schema.py')
    schema_source = open(schema_file, 'rb').read()
    compiled_schema = compile(schema_source, '<schema>', 'exec') 
    schema = {}
    exec compiled_schema in schema

    # Prefix tables w/ project id.
    for t in schema['metadata'].tables.values():
        t.name = "projects%s_%s" % (project.id, t.name)

    return schema

def getProjectAppConfig(project):
    app_config_file = os.path.join(project.dir, 'app_config.py')
    app_config_source = open(app_config_file, 'rb').read()
    compiled_app_config= compile(app_config_source, '<app_config>', 'exec') 
    app_config = {}
    exec compiled_app_config in app_config

    return app_config

def setUpSchema(project): 
    schema = getProjectSchema(project)
    
    # Create tables.
    schema['metadata'].create_all(bind=db.session.bind)

def setUpData(project):
    schema = getProjectSchema(project)

    # Load data (in order defined by schema).
    for t in schema['ordered_sources']:
        table = t['source']

        # Get the filename for the table.
        table_filename = os.path.join(project.dir, 'data', "%s.csv" % (t['id']))

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
            db.session.execute(t['source'].insert().values(**processed_row))

        table_file.close()
        db.session.commit()

    ingest_map_layers(project, schema)

def ingest_map_layers(project, schema):
    map_layers_dir = os.path.join(
        project.dir, 'data', "map_layers", "data", "shapefiles"
    )

    if not os.path.isdir(map_layers_dir):
        return

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
        table = Table(tname, schema['metadata'], *table_cols)
        GeometryDDL(table)
        table.create(bind=db.session.bind)

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

            db.session.execute(table.insert().values(**processed_row))
        db.session.commit()

        # Read SLD (if any).
        sld = None
        sld_file = os.path.join(map_layers_dir, layer, "%s.sld" % layer)
        if os.path.isfile(sld_file):
            sld = open(sld_file, "rb").read()

        # Create and saver layer model.
        layer_model = MapLayer(
            layer_id=layer,
            project=project,
            tbl=tname,
            sld=sld
        )
        db.session.add(layer_model)
        db.session.commit()

def tearDownSchema(schema): 
    schema['metadata'].drop_all(bind=db.session.bind)

def deleteProject(project_id, delete_project_dir=True):
    project = db.session.query(Project).filter(Project.id == project_id).one()
    schema = getProjectSchema(project)
    tearDownSchema(schema)

    if delete_project_dir:
        shutil.rmtree(project.dir)

    db.session.delete(project)
    db.session.commit()





