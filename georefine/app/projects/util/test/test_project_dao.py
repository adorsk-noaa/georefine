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
            record = {
                'id': None,
                'geom': WKTSpatialElement(
                    dg.generate_multipolygon_wkt(x=i, y=i)
                ),
            }
            cls.dao.connection.execute(sources['Src1'].insert(values=record))

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

if __name__ == '__main__':
    unittest.main()
