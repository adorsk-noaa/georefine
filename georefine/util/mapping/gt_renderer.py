import os
import sys
import re
import java.lang

from java.io import File as JFile
from java.util import HashMap
from org.geotools.data import DataStoreFinder
from org.geotools.map import DefaultMapContext
from org.geotools.renderer.lite import StreamingRenderer
from java.awt.image import BufferedImage
from java.awt import Rectangle
from java.awt import Color
from java.io import ByteArrayOutputStream
from javax.imageio import ImageIO
from org.python.core.util import StringUtil
from org.python.core import Py
from com.vividsolutions.jts.geom import Polygon as JPolygon
from org.geotools.jdbc import VirtualTable
from org.geotools.geometry.jts import ReferencedEnvelope
from org.geotools.referencing import CRS
from org.geotools.factory import CommonFactoryFinder
from org.geotools.filter.text.cql2 import CQL


class GeoToolsMapRenderer(object):

    def __init__(self):
        self.style_factory = CommonFactoryFinder.getStyleFactory(None)
        self.filter_factory = CommonFactoryFinder.getFilterFactory(None)

    def renderMap(self, connection_parameters=None, sql=None, geom_id_entity=None, geom_entity=None, data_entity=None, map_parameters={}):

        # Put connection parameters into a java HashMap.
        params_hashmap = HashMap()
        for param, value in connection_parameters.items():
            if value:
                params_hashmap.put(param, value)

        # Get data store.
        data_store = DataStoreFinder.getDataStore(params_hashmap)

        # Create VirtualTable from sql.
        vtable = VirtualTable("vtable", sql)

        # Set primary key.
        vtable.setPrimaryKeyColumns([geom_id_entity['ID']])

        # metadatata = intententional typo. GT needs to fix the name.
        vtable.addGeometryMetadatata("geom", JPolygon, 4326)

        # Create feature source from virtual table.
        data_store.addVirtualTable(vtable)
        feature_source = data_store.getFeatureSource("vtable")

        # Add styling classes if there was a value entity.
        if data_entity:
            # Generate class bounds.
            num_classes = data_entity.get('num_classes', 25)
            vmin = float(data_entity.get('min', 0))
            vmax = float(data_entity.get('max', 1))
            vrange = vmax - vmin
            class_width = vrange/num_classes
            classes = [(None, vmin)]
            for i in range(num_classes):
                classes.append((vmin + i * class_width, vmin + (i + 1) * class_width))
            classes.append((vmax, None))

            # Generate style rules for classes.
            rules = []
            for c in classes:
                rule = self.create_rule(c[0], c[1], vmin, vrange, attr=data_entity['ID'])
                rules.append(rule)
            feature_type_style = self.style_factory.createFeatureTypeStyle(rules)
            style = self.style_factory.createStyle()
            style.featureTypeStyles().add(feature_type_style)
        else:
            style = None

        # Setup map.
        gt_map = DefaultMapContext()
        gt_map.addLayer(feature_source, style)
        gt_renderer = StreamingRenderer()
        gt_renderer.setMapContent(gt_map)
        image_bounds = Rectangle(0, 0, map_parameters.get('WIDTH', 100), map_parameters.get('HEIGHT', 100))

        # Set image type based on format.
        image_format = map_parameters.get('FORMAT', 'image/png')
        if image_format == 'image/jpeg':
            image_type = BufferedImage.TYPE_INT_RGB
        else:
            image_type = BufferedImage.TYPE_INT_ARGB

        buffered_image = BufferedImage(image_bounds.width, image_bounds.height, image_type)
        graphics = buffered_image.createGraphics()

        # Set background color if not transparent.
        if not map_parameters.get('TRANSPARENT'):
            graphics.setPaint(Color.WHITE)
            graphics.fill(image_bounds)

        crs = CRS.decode(map_parameters.get('SRS', "EPSG:4326"))
        bbox = map_parameters.get('BBOX', '-180,-90,180,90')
        coords = [float(coord) for coord in bbox.split(",")]
        map_bounds = ReferencedEnvelope(coords[0], coords[2], coords[1], coords[3], crs)

        gt_renderer.paint(graphics, image_bounds, map_bounds)

        # Release the JDBC connection and map content.
        data_store.dispose()
        gt_renderer.getMapContent().dispose()

        # Return raw image.
        byte_array_output_stream = ByteArrayOutputStream()
        informal_format = re.match('image/(.*)', image_format).group(1)
        ImageIO.write(buffered_image, informal_format, byte_array_output_stream)
        byte_array = byte_array_output_stream.toByteArray()
        raw_image = Py.newString(StringUtil.fromBytes(byte_array))
        return raw_image

    def create_rule(self, local_min, local_max, global_min, global_range, attr="value"):
        rule = self.style_factory.createRule()
        cql_filters = []
        if not local_min == None:
            cql_filters.append("%s >= %s" % (attr, local_min))
        if not local_max == None:
            cql_filters.append("%s < %s" % (attr, local_max))
        cql = " and ".join(cql_filters)
        gt_filter = CQL.toFilter(cql)
        rule.setFilter(gt_filter)
        if local_min == None:
            brightness = 1.0
        else:
            brightness = 1.0 - (local_min - global_min)/global_range

        color = Color.HSBtoRGB(0.0, 0.0, brightness)

        fill = self.style_factory.createFill(
                self.filter_factory.literal(color),
                self.filter_factory.literal(1)
                )
        symbolizer = self.style_factory.createPolygonSymbolizer(None, fill, None)
        rule.symbolizers().add(symbolizer)
        return rule


# Helper function to map SqlAlchemy connection parameters 
# to GeoTools parameters.
def mapSqlAlchemyConnectionParameters(sa_params={}):
    gt_to_sa_map = {
            "dbtype": "drivername",
            "host": "host",
            "port": "port",
            "database": "database",
            "user": "username",
            "passwd": "password"
            }
    gt_params = {}
    for gt_param, sa_param in gt_to_sa_map.items():
        value = sa_params.get(sa_param)
        if value:
            # Handle postgres.
            if sa_param == "drivername" and "postgresql" in value:
                value = "postgis"
                gt_params["schema"] = "public"
            gt_params[gt_param] = value

    return gt_params

    



        



