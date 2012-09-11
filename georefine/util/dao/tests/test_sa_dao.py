import unittest
from georefine.util.dao.tests.basetest import BaseTest
from georefine.util.dao.gr_sa_dao import GeoRefine_SA_DAO

from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, Integer, String, Float
from sqlalchemy import MetaData
from sqlalchemy.sql import *
from geoalchemy import *
from geoalchemy.postgis import PGComparator
from pprint import pprint


class SA_DAO_Test(BaseTest):

    def setUp(self):
        super(SA_DAO_Test, self).setUp()
        self.schema = self.setUpSchemaAndData1()
        self.dao = GeoRefine_SA_DAO(
            connection=self.connection, 
            schema=self.schema
        )

    def test_query_elements(self):
        simple_q = {
            'ID': 'simple_q',
            'SELECT': [{'ID': 't1_id', 'EXPRESSION': '{{test1.id}}'}],
            'FROM': ['test1'],
            'WHERE': [[{'ID': 't1_id', 'TYPE': 'ENTITY'}, '==', 1]],
            'GROUP_BY': [{'ID': 't1_id'}],
            'ORDER_BY': [{'ENTITY': {'ID': 't1_id'}}],
        }
        results = self.dao.execute_queries(query_defs=[simple_q])
        assert results['simple_q'][0]['t1_id'] == 1

    def test_join_query(self):
        join_q = {
            'ID': 'join_q',
            'AS_DICTS': True,
            'SELECT': [
                {'ID': 't2_id', 'EXPRESSION': 'func.count({{test2.id}})'},
                {'ID': 't1_id', 'EXPRESSION': '{{test1.id}}'}
            ],
            'FROM': [{'SOURCE': 'test1', 'JOINS': ['test1_test2', 'test2']}],
            'WHERE': [[{'ID': 't1_id', 'TYPE': 'ENTITY'}, '==', 1]],
            'GROUP_BY': [{'ID': 't1_id'}],
            'ORDER_BY': [{'ENTITY': {'ID': 't1_id'}}]
        }
        results = self.dao.execute_queries(query_defs=[join_q])
        assert results['join_q'][0]['t1_id'] == 1
        assert results['join_q'][0]['t2_id'] == 2

    def test_get_raw_sql(self):
        simple_q = {
            'ID': 'simple_q',
            'SELECT': [{'ID': 't1_id', 'EXPRESSION': '{{test1.id}}'}],
            'FROM': ['test1'],
            'WHERE': [[{'ID': 't1_id', 'TYPE': 'ENTITY'}, '==', 1]],
            'GROUP_BY': [{'ID': 't1_id'}],
            'ORDER_BY': [{'ENTITY': {'ID': 't1_id'}}],
        }
        sql = self.dao.get_sql(simple_q)
        assert isinstance(sql, unicode)

    def test_subq(self):
        nested_q = {
            'ID': 'nested_q',
            'SELECT': [{'ID': 't2_id', 'EXPRESSION': '{{test2.id}}'}],
            'FROM': [{'SOURCE': 'test2', 'JOINS': ['test1_test2', 'test1']}],
            'WHERE': [[{'ID': 't1_id', 'EXPRESSION': '{{test1.id}}', 'TYPE':
                        'ENTITY'}, 'in', [1,3]]],
        }
        subq_q = {
            'ID': 'subq_q',
            'AS_DICTS': True,
            'SELECT': [{'ID': 'id_count', 'EXPRESSION':
                        'func.count({{subq.t2_id}})'}],
            'FROM': [{'ID': 'subq', 'SOURCE': nested_q}]
        }

        results = self.dao.execute_queries(query_defs=[subq_q])
        assert results['subq_q'][0]['id_count'] == 4

    def test_keyed_results(self):
        bucket_entity = {'ID': 'bucket', 'EXPRESSION': '{{test1.id}}', 'AS_HISTOGRAM': True, 'ALL_VALUES': True, 'MIN': 0, 'MAX': 5, 'NUM_CLASSES': 5}
        bucket_entity2 = {'ID': 'bucket', 'EXPRESSION': '{{test1.id}}', 'AS_HISTOGRAM': True, 'NUM_CLASSES': 10, 'ALL_VALUES': True, 'CONTEXT': {
            #"WHERE": [["{{test1.id}}", "in", [2,3]]]
        },
        'MIN': -1,
        'MINAUTO': True,
        'MAX': 5,
        'MAXAUTO': True,
        }

        key_def = {
        #"KEY_ENTITY" : {'EXPRESSION': '{{test1.id}}', 'ALL_VALUES': True},
        #"LABEL_ENTITY" : {'EXPRESSION': '{{test1.name}}'}
        "KEY_ENTITY" : bucket_entity2
        }

        primary_q = {
        "AS_DICTS": True, 
        "ID": "primary_q",
        "SELECT" : [
        {'ID': "t1id", 'EXPRESSION': '{{test1.id}}'},
        ],
        "GROUP_BY": [
        {"ID": "t1id"},
        bucket_entity2
        ],
        "SELECT_GROUP_BY": True,
        }

        keyed_results = self.dao.get_keyed_results(key_def, [primary_q])
        import simplejson as json
        #print json.dumps(keyed_results, indent=2)

if __name__ == '__main__':
    unittest.main()
