import unittest
from georefine.util.sa.tests.basetest import BaseTest
from georefine.util.mapping.gt_renderer import GeoToolsMapRenderer
from georefine.util.sa.sa_dao import SA_DAO

from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, Integer, String, Float
from sqlalchemy.orm import relationship, mapper
from sqlalchemy import MetaData
from geoalchemy import *
from geoalchemy.postgis import PGComparator
from pprint import pprint

class GeoToolsMapRendererTest(BaseTest):

	def testRendering(self):
		self.dao = SA_DAO(session=self.session, primary_class=self.schema['primary_class'])
		renderer = GeoToolsMapRenderer()

		data_entity = {"expression": "func.sum({TestClass1.id})", "num_classes": 5, "min": 1, "max": 5}
		map_parameters = {
				"width": 600,
				"height": 600,
				"bbox": "-10,-10,10,10",
				"format": "image/png",
				"transparent": True
				}
		print renderer.renderMap(dao=self.dao, data_entity=data_entity, map_parameters=map_parameters)
	
	def setUp(self):
		super(GeoToolsMapRendererTest, self).setUp()

		schema = {}
		self.schema = schema

		schema['classes'] = {}

		class TestClass1(object):
			id = None
			geom = None
			children = []
		schema['classes']['TestClass1'] = TestClass1

		class TestClass2(object):
			id = None
			name = ""
		schema['classes']['TestClass2'] = TestClass2

		schema['primary_class'] = TestClass1

		self.metadata = MetaData()

		test1_table = Table('test1', self.metadata,
				Column('id', Integer, primary_key=True),
				GeometryExtensionColumn('geom', Polygon(2)),
				)
		GeometryDDL(test1_table)

		test2_table = Table('test2', self.metadata,
				Column('id', Integer, primary_key=True),
				Column('name', String)
				)

		test1_test2_table = Table('test1_test2', self.metadata,
				Column('test1_id', Integer, primary_key=True),
				Column('test2_id', Integer, primary_key=True),
				ForeignKeyConstraint(['test1_id'], [test1_table.c.id]),
				ForeignKeyConstraint(['test2_id'], [test2_table.c.id])
				)

		mapper(
				TestClass1, 
				test1_table,
				properties = {
					'children': relationship(TestClass2, secondary=test1_test2_table),
					'geom': GeometryColumn(test1_table.c.geom)
					}
				)

		mapper(
				TestClass2, 
				test2_table,
				properties = {
					}
				)

		self.metadata.drop_all(self.session.bind, checkfirst=True)
		self.metadata.create_all(self.session.bind, checkfirst=True)

		tc1s = []
		tc2s = []
		for i in range(5):

			vertices = []
			vertices.append([i, i])
			vertices.append([i, i + 1])
			vertices.append([i + 1, i + 1])
			vertices.append([i + 1, i])
			vertices.append(vertices[0])
			geom = "POLYGON((%s))" % ', '.join(["%s %s" % (v[0], v[1]) for v in vertices])

			tc1 = TestClass1()
			tc1.geom = geom
			tc1s.append(tc1)
			self.session.add(tc1)

			tc2 = TestClass2()
			tc2.name = "tc2_%s" % i
			tc2s.append(tc2)
			self.session.add(tc2)

		self.session.commit()
		self.trans.commit()

		"""
		for i in range(len(tc1s)):
			tc1 = tc1s[i]
			child_tc2s = [tc2s[i], tc2s[ (i + 1) % len(tc1s)]]
			for c in child_tc2s:
				tc2 = self.session.query(TestClass2).filter(TestClass2.id == c.id).one()
				tc1.children.append(tc2)
		self.session.commit()
		"""
	def tearDown(self):
		self.metadata.drop_all(self.session.bind, checkfirst=True)


if __name__ == '__main__':
	unittest.main()
