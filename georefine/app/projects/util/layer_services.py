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
