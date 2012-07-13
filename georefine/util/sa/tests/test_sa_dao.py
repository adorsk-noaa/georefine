import unittest
from georefine.util.sa.tests.basetest import BaseTest
from georefine.util.sa.sa_dao import SA_DAO

from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, Integer, String, Float
from sqlalchemy.orm import relationship, mapper
from sqlalchemy import MetaData
from geoalchemy import *
from geoalchemy.postgis import PGComparator
from pprint import pprint


class SA_DAO_Test(BaseTest):

    def test_SA_DAO(self):

        sa_dao = SA_DAO(connection=self.connection, schema=self.schema)

        """
        simple_q = {
                'ID': 'simple_q',
                'SELECT': [{'ID': 't1_id', 'EXPRESSION': '{test1.id}'}],
                'FROM': ['test1'],
                'WHERE': [{'ENTITY': {'ID': 't1_id'}, 'OP': '==', 'VALUE': 1}],
                'GROUP_BY': [{'ID': 't1_id'}],
                'ORDER_BY': [{'ENTITY': {'ID': 't1_id'}}]
                }
        results = sa_dao.execute_queries(query_defs=[simple_q])
        print results
        """

        """
        join_q = {
                'ID': 'join_q',
                'AS_DICTS': True,
                'SELECT': [
                    {'ID': 't2_id', 'EXPRESSION': 'func.count({test2.id})'},
                    {'ID': 't1_id', 'EXPRESSION': '{test1.id}'}
                    ],
                'FROM': [{'ID': 'test1', 'JOINS': ['test1_test2', 'test2']}],
                'WHERE': [{'ENTITY': 't1_id', 'OP': '==', 'VALUE': 1}],
                'GROUP_BY': [{'ID': 't1_id'}],
                'ORDER_BY': [{'ENTITY': {'ID': 't1_id'}}]
                }
        results = sa_dao.execute_queries(query_defs=[join_q])
        print results
        """

        """
        sql = sa_dao.get_sql(**join_q)
        print sql
        """

        """
        aggs = sa_dao.get_aggregates(
                SELECT = [
                    {'ID': 't2_id', 'EXPRESSION': 'func.count({test2.id})'},
                    ],
                FROM = [{'TABLE': 'test1', 'JOINS': ['test1_test2', 'test2']}],
                WHERE = [],
                GROUP_BY = [
                    #{'ID': 't1_id', 'EXPRESSION': '{test1.id}', 'AS_HISTOGRAM': True, 'ALL_VALUES': True},
                    {'EXPRESSION': '{test1.id}', 'ALL_VALUES': True, 'LABEL_ENTITY': '{test1.id}'}
                    ]
                )
        import simplejson as json
        print json.dumps(aggs, indent=2)
        """

        # Test nested subquery in from clause.
        """
        nested_q = {
                'ID': 'nested_q',
                'SELECT': [{'ID': 't2_id', 'EXPRESSION': '{test2.id}'}],
                'FROM': [{'ID': 'test2', 'JOINS': ['test1_test2', 'test1']}],
                'WHERE': [{'ENTITY': {'ID': 't1_id', 'EXPRESSION': '{test1.id}'}, 'OP': 'in', 'VALUE': [1,3]}],
                }
        subq_q = {
                'ID': 'subq_q',
                'AS_DICTS': True,
                'SELECT': [{'ID': 'id_count', 'EXPRESSION': 'func.count({subq.t2_id})'}],
                'FROM': [{'ID': 'subq', 'TABLE': nested_q}]
                }
        results = sa_dao.execute_queries(query_defs=[subq_q])
        print results
        print sa_dao.get_sql(**subq_q)
        """


    def setUp(self):
        super(SA_DAO_Test, self).setUp()
        self.schema = self.setUpSchemaAndData1()

        
if __name__ == '__main__':
    unittest.main()
