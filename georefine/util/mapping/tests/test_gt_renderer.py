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
        schema = self.setUpSchemaAndData()
        self.dao = SA_DAO(connection=self.connection, schema=schema)
        renderer = GeoToolsMapRenderer()

        """
        #data_entity = {"expression": "func.sum({TestClass1.id})", "num_classes": 5, "min": 1, "max": 5}
        map_parameters = {
                "width": 600,
                "height": 600,
                "bbox": "-10,-10,10,10",
                "format": "image/png",
                "transparent": True
                }
        print renderer.renderMap(dao=self.dao, data_entity=data_entity, map_parameters=map_parameters)
        """
    
    def setUpSchemaAndData(self):

        schema = {}
        tables = {}
        ordered_tables = []

        metadata = MetaData()

        tables['test1'] = Table('test1', metadata,
                Column('id', Integer, primary_key=True),
                Column('name', String),
                GeometryExtensionColumn('geom', Polygon(2)),
                )
        GeometryDDL(tables['test1'])
        ordered_tables.append(tables['test1'])

        tables['test2'] = Table('test2', metadata,
                Column('id', Integer, primary_key=True),
                Column('name', String)
                )
        ordered_tables.append(tables['test2'])

        tables['test1_test2'] = Table('test1_test2', metadata,
                Column('test1_id', Integer, primary_key=True),
                Column('test2_id', Integer, primary_key=True),
                ForeignKeyConstraint(['test1_id'], ['test1.id']),
                ForeignKeyConstraint(['test2_id'], ['test2.id'])
                )
        ordered_tables.append(tables['test1_test2'])

        schema['tables'] = tables
        schema['ordered_tables'] = tables

        metadata.create_all(self.connection)

        t1s = []
        t2s = []
        for i in range(5):

            vertices = []
            vertices.append([i, i])
            vertices.append([i, i + 1])
            vertices.append([i + 1, i + 1])
            vertices.append([i + 1, i])
            vertices.append(vertices[0])
            wkt_geom = "POLYGON((%s))" % ', '.join(["%s %s" % (v[0], v[1]) for v in vertices])

            t1 = {
                "id": i,
                "name": "t1_%s" % i,
                "geom": WKTSpatialElement(wkt_geom)
            }
            t1s.append(t1)
            self.connection.execute(schema['tables']['test1'].insert().values(**t1))

            t2 = {
                "id": i,
                "name": "t2_%s" % i,
            }
            t2s.append(t2)
            self.connection.execute(schema['tables']['test2'].insert().values(**t2))

        for i in range(len(t1s)):
            t1 = t1s[i]
            child_t2s = [t2s[i], t2s[ (i + 1) % len(t1s)]]
            for t2 in child_t2s:
                t1_t2 = {
                        "test1_id": t1['id'],
                        "test2_id": t2['id']
                        }
                self.connection.execute(schema['tables']['test1_test2'].insert().values(**t1_t2))

        return schema

if __name__ == '__main__':
    unittest.main()
