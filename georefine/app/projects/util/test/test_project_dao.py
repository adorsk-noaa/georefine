import unittest
from georefine.app import app
from georefine.app import db
from georefine.app.test.db_testcase import DBTestCase
from georefine.app.projects.util.project_dao import ProjectDAO
from georefine.app.projects import models as project_models
from georefine.app.projects.util import manage_projects as manage
from georefine.app.projects.util import data_generator as dg
from georefine.app.projects.util.test.test_services import ProjectsServicesCommonTestCase
import re
import logging


class ProjectsProjectDAOTestCase(ProjectsServicesCommonTestCase):

    def test_get_spatial_query(self):
        geom_entity = {'EXPRESSION': '__Src1__geom', 'ID': 'geom'}
        frame_entity= {
            'EXPRESSION': 'func.BuildMbr(0,0,10,10)',
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
        dao = manage.get_dao(self.project)
        q = dao.get_spatialite_spatial_query(query, geom_entity, frame_entity)
        formatted_sql = re.sub('\s+', ' ', dao.query_to_raw_sql(q))
        expected_sql = """SELECT AsBinary("Src1".geom) AS geom FROM "Src1" JOIN (SELECT ROWID FROM SpatialIndex WHERE search_frame = BuildMbr(0, 0, 10, 10) AND f_table_name = 'Src1') AS idx_subq ON Src1.ROWID = idx_subq.ROWID GROUP BY "Src1".geom"""
        self.assertEquals(formatted_sql, expected_sql)

if __name__ == '__main__':
    unittest.main()
