import unittest
import sys
from georefine.util.sa.tests.basetest import BaseTest
from georefine.util.mapping.gt_renderer import GeoToolsMapRenderer, mapSqlAlchemyConnectionParameters
from georefine.util.sa.sa_dao import SA_DAO

from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, Integer, String, Float
from sqlalchemy import MetaData
from sqlalchemy.sql import select
from geoalchemy import *
from geoalchemy.postgis import PGComparator
from pprint import pprint

class GeoToolsMapRendererTest(BaseTest):

    def setUp(self):
        super(GeoToolsMapRendererTest, self).setUp()
        self.schema = self.setUpSchemaAndData()
        self.trans.commit()

    def tearDown(self):
        self.schema['metadata'].drop_all(self.connection)

    def testRendering(self):
        dao = SA_DAO(connection=self.connection, schema=self.schema)
        renderer = GeoToolsMapRenderer()

        # Get connection parameters.
        sa_connection_parameters = dao.get_connection_parameters()
        gt_connection_parameters = mapSqlAlchemyConnectionParameters(sa_connection_parameters)

        # Define query.
        q = {
            "SELECT": [
                {"ID": "geom", "EXPRESSION": 'RawColumn({{test1.geom}})'},
                {"ID": "geom_id", "EXPRESSION": '{{test1.id}}'},
                {"ID": "value", "EXPRESSION": '{{test1.id}}'},
                ]
        }

        # Generate SQL.
        sql = dao.get_sql(q)

        """
        t1 = self.schema['tables']['test1']
        g = RawColumn(t1.c.geom)
        q = select([g, t1.c.id.label('value'), t1.c.id.label('geom_id')])
        sql = dao.query_to_raw_sql(q)
        """

        print >> sys.stderr, "sql is: ", sql

        # Define entities.
        geom_id_entity = {"ID": "geom_id"}
        geom_entity = {"ID": "geom"}
        value_entity = {"ID": "value"}

        # Define map parameters.
        map_parameters = {
                "WIDTH": 600,
                "HEIGHT": 600,
                "BBOX": "-10,-10,10,10",
                "FORMAT": "image/png",
                "TRANSPARENT": True
                }
        img = renderer.renderMap(
            connection_parameters = gt_connection_parameters,
            sql = sql,
            geom_id_entity = geom_id_entity,
            geom_entity = geom_entity,
            value_entity = value_entity,
            map_parameters = map_parameters
            )

        print img
    
    def setUpSchemaAndData(self):

        schema = {}
        tables = {}
        ordered_tables = []

        metadata = MetaData()
        schema['metadata'] = metadata

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
