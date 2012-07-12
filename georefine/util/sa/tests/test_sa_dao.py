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
                'id': 'simple_q',
                'select': [{'id': 't1_id', 'expression': '{test1.id}'}],
                'from': ['test1'],
                'where': [{'entity': 't1_id', 'op': '==', 'value': 1}],
                'group_by': ['t1_id'],
                'order_by': ['t1_id']
                }
        results = sa_dao.execute_queries(query_defs=[simple_q])
        print results
        """

        join_q = {
                'id': 'join_q',
                'select': [
                    {'id': 't2_id', 'expression': 'func.count({test2.id})'},
                    {'id': 't1_id', 'expression': '{test1.id}'}
                    ],
                'from': [{'id': 'test1', 'joins': ['test1_test2', 'test2']}],
                'where': [{'entity': 't1_id', 'op': '==', 'value': 1}],
                'group_by': ['t1_id'],
                'order_by': ['t1_id']
                }
        results = sa_dao.execute_queries(query_defs=[join_q])
        #print results

        sql = sa_dao.get_sql(query_def=join_q)
        print sql

    def setUp(self):
        super(SA_DAO_Test, self).setUp()

        self.schema = {}

        metadata = MetaData()

        self.schema['test1'] = Table('test1', metadata,
                Column('id', Integer, primary_key=True)
                )


        self.schema['test2'] = Table('test2', metadata,
                Column('id', Integer, primary_key=True),
                Column('name', String)
                )

        self.schema['test1_test2'] = Table('test1_test2', metadata,
                Column('test1_id', Integer, primary_key=True),
                Column('test2_id', Integer, primary_key=True),
                ForeignKeyConstraint(['test1_id'], [self.schema['test1'].c.id]),
                ForeignKeyConstraint(['test2_id'], [self.schema['test2'].c.id])
                )

        metadata.create_all(self.connection)

        tc1s = []
        tc2s = []
        for i in range(5):
            tc1 = {
                    "id": i
                    }
            tc1s.append(tc1)
            self.connection.execute(self.schema['test1'].insert(), [tc1])

            tc2 = {
                    "id": i,
                    "name": "tc2_%s" % i
                    }
            tc2s.append(tc2)
            self.connection.execute(self.schema['test2'].insert(), [tc2])

        self.session.commit()

        for i in range(len(tc1s)):
            tc1 = tc1s[i]
            child_tc2s = [tc2s[i], tc2s[ (i + 1) % len(tc1s)]]
            for tc2 in child_tc2s:
                tc1_tc2 = {
                        "test1_id": tc1['id'],
                        "test2_id": tc2['id']
                        }
                self.connection.execute(self.schema['test1_test2'].insert(), [tc1_tc2])
        
if __name__ == '__main__':
    unittest.main()
