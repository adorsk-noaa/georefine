import os
import sys
import java.lang

from java.io import File as JFile
from java.util import HashMap
from org.geotools.data import FileDataStoreFinder
from org.geotools.data import DataStoreFinder
from org.geotools.data.simple import SimpleFeatureSource
from org.geotools.map import DefaultMapContext
from org.geotools.swing import JMapFrame
from org.geotools.renderer.lite import StreamingRenderer
from java.awt.image import BufferedImage
from java.awt import Rectangle
from java.awt import Color
from java.io import ByteArrayOutputStream
from javax.imageio import ImageIO
from org.python.core.util import StringUtil
from StringIO import StringIO
from org.python.core import Py
from com.vividsolutions.jts.geom import Point as JPoint
from org.geotools.jdbc import VirtualTable
from org.geotools.geometry.jts import ReferencedEnvelope
from org.geotools.referencing import CRS

class GeoToolsMapRenderer(object):

	def __init__(self):
		pass

	def renderMap(map_context=None, connection_parameters=None):

		# File test.
		"""
		map_file = "%s/tests/test_gis_data/ne_110m_admin_1_states_provinces_shp.shp" % os.path.dirname(__file__)
		data_file = JFile(map_file)

		data_store = FileDataStoreFinder.getDataStore(data_file)
		feature_source = data_store.getFeatureSource()
		"""

		# DB test.
		from georefine.app import db
		from georefine.util.sa.sa_dao import SA_DAO
		from georefine.app.projects.util import manage_projects
		from georefine.app.projects.models import Project
		project_dir = '/home/adorsk/projects/gr/georefine/georefine/app/projects/util/tests/test_manage_projects_project_dir'
		project = Project(id=1, name='test', dir=project_dir)
		project.schema = manage_projects.getProjectSchema(project)
		manage_projects.setUpSchema(project)		
		#manage_projects.setUpData(project)

		dao = SA_DAO(session=db.session, primary_class=project.schema.primary_class)
		connection_parameters = dao.get_connection_parameters()

		gt_to_sa_map = {
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
				gt_params.put(gt_param, value)
		gt_params.put("dbtype", "postgis")
		gt_params.put("schema", "public")

		data_store = DataStoreFinder.getDataStore(gt_params)

		sql = "select id as geom_id, geom from projects1_test1"
		vtable = VirtualTable("vtable", sql)
		vtable.setPrimaryKeyColumns(["geom_id"])
		# metadatata = intententional typo. GT needs to fix the name.
		vtable.addGeometryMetadatata("geom", JPoint, 4326)

		data_store.addVirtualTable(vtable)
		feature_source = data_store.getFeatureSource("vtable")
		#


		gt_map = DefaultMapContext()
		gt_map.setTitle('foo')
		gt_map.addLayer(feature_source, None)

		"""
		print "gt map is: ", gt_map
		JMapFrame.showMap(gt_map)
		raw_input("foo")
		"""

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
		byte_array_output_stream = ByteArrayOutputStream()
		ImageIO.write(buffered_image, "jpg", byte_array_output_stream)
		byte_array = byte_array_output_stream.toByteArray()

		raw_image = Py.newString(StringUtil.fromBytes(byte_array))
		print raw_image

		"""
		gt_map = DefaultMapContext()

		for layer in map_context.get('layers', []):
			data_store = layer.get('data_store')
			style = layer.get('style')
			gt_map.addLayer(feature_source, style)

		"""

		



