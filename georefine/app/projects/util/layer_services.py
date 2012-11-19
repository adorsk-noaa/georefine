from georefine.app import db as db
import platform


def get_map(layer, wms_parameters={}, **kwargs):

    # Render w/ GeoTools if using jython.
    if platform.system() == 'Java':
        from georefine.util.mapping.gt_renderer import (
            GeoToolsMapRenderer, mapSqlAlchemyConnectionParameters)

        # Initialize GeoTools Renderer.
        gt_renderer = GeoToolsMapRenderer()

        # Get connection parameters.
        sa_connection_parameters = dao.get_connection_parameters()
        gt_connection_parameters = mapSqlAlchemyConnectionParameters(sa_connection_parameters)

        # Generate sql.
        sql = dao.get_sql(QUERY)

        # Render map image.
        img = gt_renderer.renderMap(
            connection_parameters = gt_connection_parameters,
            sql = sql,
            data_entity = DATA_ENTITY, 
            geom_id_entity = GEOM_ID_ENTITY, 
            geom_entity = GEOM_ENTITY, 
            map_parameters= MAP_PARAMETERS,
            **kwargs
            )

    # Otherwise render w/ mapscript.
    else:
        from georefine.util.mapping.ms_renderer import MapScriptRenderer
        renderer = MapScriptRenderer()

        if 'postgres' in db.engine.url.drivername:
            connectiontype = 'POSTGIS'
            ms_connection_str = "host=%s password=%s dbname=%s user=%s" % (
                db.engine.url.host, db.engine.url.password, 
                db.engine.url.database, db.engine.url.username)
            ms_data_str = "geom FROM %s USING UNIQUE id USING srid=4326" % (
                str(layer.tbl))
        elif 'sqlite' in db.engine.url.drivername:
            connectiontype = 'OGR'
            ms_connection_str = db.engine.url.database
            ms_data_str = "SELECT AsBinary(geom) from %s" % layer.tbl

        layers = [{
            'name': str(layer.layer_id),
            'connection': ms_connection_str,
            'connectiontype': connectiontype,
            'data': ms_data_str,
            'projection': 'init=epsg:4326',
            'type': 'POLYGON',
            'sld': {
                'doc': layer.sld
            }
        }]

        imgObj = renderer.renderLayers(
            wms_parameters=wms_parameters,
            layers=layers
        )

        img = renderer.imgObj_to_bytes(imgObj)

    return img

    #return open('/data/burger.png').read()

def create_layers_for_project(project, data_dir, session=db.session):
    # Create layer record in db.

    map_layers_dir = os.path.join(
        data_dir, 'data', "map_layers", "data", "shapefiles"
    )

    # Read layer metadata from layers dir.
    # Layers dir is expected to contain a set of directories, where
    # each directory contains data and metadata for a layer.
    for layer_id in os.listdir(map_layers_dir):
        layer_dir = os.path.join(map_layers_dir, layer_id)


def create_layer_for_project(project, layer_dir, session=db.session):
    # record whether layer has sld here too.
    # Read big blob o' metadata from layers spreadsheet. or an individual
    # metadata.json in each layer dir. that might be better. yah.

    # Copy layer files to subdir of project's data dir.
    layer_storage_dir = os.path.join(project.data_dir, 'layers', layer_id)

    # Create and saver layer model.
    layer_model = MapLayer(
        layer_id=layer,
        project=project,
        sld=sld,
        # other metadata here? Generic pickle blob to reconstitute later.
    )

    session.add(layer_model)
    session.commit()

