import os
import sys
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

	def renderMap(self, dao=None, id_entity=None, geom_entity=None, data_entity=None, filters=[], map_context=None):

		# Get connection parameters.
		connection_parameters = dao.get_connection_parameters()
		gt_to_sa_map = {
				"dbtype": "drivername",
				"host": "host",
				"port": "port",
				"database": "database",
				"user": "username",
				"passwd": "password"
				}

		gt_params = HashMap()
		for gt_param, sa_param in gt_to_sa_map.items():
			value = connection_parameters.get(sa_param)
			if value:

				# Handle postgres.
				if sa_param == "drivername" and "postgresql" in value:
					value = "postgis"
					gt_params.put("schema", "public")

				gt_params.put(gt_param, value)

		data_store = DataStoreFinder.getDataStore(gt_params)

		# Create raw sql query.
		if id_entity == None:
			id_entity = {'expression': "{%s.id}" % dao.primary_class.__name__, "label": "id"}
		if geom_entity == None:
			geom_entity = {'expression': "{%s.geom}.RAW" % dao.primary_class.__name__, "label": "geom"}
		data_entity['label'] = 'value'

		data_entities = [id_entity, geom_entity, data_entity]
		grouping_entities = [id_entity, geom_entity]
		sql = dao.get_sql(data_entities=data_entities, grouping_entities=grouping_entities, filters=filters)

		# Create VirtualTable from query.
		vtable = VirtualTable("vtable", sql)
		vtable.setPrimaryKeyColumns(["id"])
		# metadatata = intententional typo. GT needs to fix the name.
		vtable.addGeometryMetadatata("geom", JPolygon, 4326)

		# Create feature source from virtual table.
		data_store.addVirtualTable(vtable)
		feature_source = data_store.getFeatureSource("vtable")

		# Generate class bounds.
		num_classes = data_entity.get('num_classes', 10)
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
			rule = self.create_rule(c[0], c[1], vmin, vrange)
			rules.append(rule)
		feature_type_style = self.style_factory.createFeatureTypeStyle(rules)
		style = self.style_factory.createStyle()
		style.featureTypeStyles().add(feature_type_style)

		# Setup map.
		# @TODO: FROM WMS PARMS.
		gt_map = DefaultMapContext()
		gt_map.addLayer(feature_source, style)
		gt_renderer = StreamingRenderer()
		gt_renderer.setMapContent(gt_map)
		image_bounds = Rectangle(0, 0, 400, 400)
		buffered_image = BufferedImage(image_bounds.width, image_bounds.height, BufferedImage.TYPE_INT_RGB)
		graphics = buffered_image.createGraphics()
		graphics.setPaint(Color.WHITE)
		graphics.fill(image_bounds)
		crs = CRS.decode("EPSG:4326")
		map_bounds = ReferencedEnvelope(-10.0, 10.0, -10.0, 10.0, crs)

		#gt_renderer.paint(graphics, image_bounds, gt_map.getMaxBounds())
		gt_renderer.paint(graphics, image_bounds, map_bounds)

		# Release the JDBC connection.
		data_store.dispose()

		# Return raw image.
		byte_array_output_stream = ByteArrayOutputStream()
		ImageIO.write(buffered_image, "jpg", byte_array_output_stream)
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
			brightness = 0
		else:
			brightness = (local_min - global_min)/global_range
		color = Color.HSBtoRGB(0.0, 0.0, brightness)
		fill = self.style_factory.createFill(
				self.filter_factory.literal(color),
				self.filter_factory.literal(0.5)
				)
		symbolizer = self.style_factory.createPolygonSymbolizer(None, fill, None)
		rule.symbolizers().add(symbolizer)
		return rule


		



