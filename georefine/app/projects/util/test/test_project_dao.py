import unittest
from georefine.app import app
from georefine.app import db
from georefine.app.test.db_testcase import DBTestCase
from georefine.app.projects.util.project_dao import ProjectDAO
from georefine.app.projects import models as project_models
from georefine.app.projects.util import manage_projects as manage
from georefine.app.projects.util import data_generator as dg
from georefine.app.projects.util.test.test_services import ProjectsServicesCommonTestCase
from sqlalchemy import *
from geoalchemy import *
import re
import os
import logging


class ProjectsProjectDAOTestCase(DBTestCase):

    rollback_each_time = False

    @classmethod
    def setUpClass(cls):
        super(ProjectsProjectDAOTestCase, cls).setUpClass()
        metadata = MetaData()
        sources = {}

        sources['Src1'] = Table(
            'Src1', metadata,
            Column('id', Integer, primary_key=True),
            GeometryExtensionColumn('geom', MultiPolygon(2)),
        )
        GeometryDDL(sources['Src1'])

        sources['Src2'] = Table(
            'Src2', metadata,
            Column('id', Integer, primary_key=True),
            Column('src1_id', Integer, ForeignKey('Src1.id')),
            Column('value', Float),
        )

        cls.schema = {
            'metadata': metadata,
            'sources': sources,
        }

        cls.connection = cls.getConnection()
        cls.spatializeDB(cls.connection)
        cls.dao = ProjectDAO(cls.connection, cls.schema)
        metadata.create_all(bind=cls.connection)

        n = 10
        for i in range(n):
            src1_record = {
                'id': None,
                'geom': WKTSpatialElement(
                    dg.generate_multipolygon_wkt(x=i, y=i)
                ),
            }
            cls.dao.connection.execute(sources['Src1'].insert(values=src1_record))

            for j in range(2):
                src2_record = {
                    'id': None,
                    'src1_id': i,
                    'value': i,
                }
                cls.dao.connection.execute(sources['Src2'].insert(values=src2_record))

    def test_spatial_query(self):
        geom_entity = {'EXPRESSION': '__Src1__geom', 'ID': 'geom'}
        frame_entity= {
            'EXPRESSION': 'func.BuildMbr(5,5,6,6)',
            'ID': 'frame_',
        }
        query = {
            "ID": "query",
            "SELECT" : [
                geom_entity,
            ],
            "GROUP_BY": [
                geom_entity,
            ]
        }
        q = self.dao.get_spatialite_spatial_query(query, geom_entity, frame_entity)
        rows = self.dao.connection.execute(q).fetchall()
        self.assertEquals(len(rows), 3)

    def test_nested_query(self):
        geom_entity = {'EXPRESSION': '__Src2__Src1__geom', 'ID': 'geom'}
        geom_id_entity = {'EXPRESSION': '__Src2__Src1__id', 'ID': 'geom_id'}
        value_entity = {'EXPRESSION': 'func.sum(__Src2__value)', 'ID': 'value'}
        frame_entity = {
            'EXPRESSION': 'func.BuildMbr(0,0,2,2)',
            'ID': 'frame_',
        }
        inner_query = {
            "ID": 'inner',
            'SELECT': [
                geom_entity,
                value_entity
            ],
            "GROUP_BY": [
                geom_entity,
                geom_id_entity,
            ]
        }
        outer_query = {
            "ID": "outer",
            "SELECT" : [
                {'EXPRESSION': '__inner__%s' %geom_entity['ID']},
                {'EXPRESSION': '__inner__%s' % value_entity['ID']},
            ],
            "FROM": [{'ID': 'inner', 'SOURCE': inner_query}]
        }
        q = self.dao.get_spatialite_spatial_query(outer_query, geom_entity, frame_entity)
        rows = self.dao.connection.execute(q).fetchall()
        print rows

if __name__ == '__main__':
    unittest.main()
