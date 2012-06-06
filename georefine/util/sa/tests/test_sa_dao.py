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

	def test(self):

		sa_dao = SA_DAO(session=self.session, primary_class=self.schema['primary_class'])

		filter_1 = {'entity': {'expression': '-1 * {TestClass1.id}'}, 'op': 'in', 'value': [-1, -2]}

		#q = sa_dao.get_filtered_query(filters=[filter_1])

		#sa_dao.get_entities(entity_class=self.schema['classes']['TestClass2'])

		data_entities = [
				{'expression': '{TestClass1.id}', 'label': 'area_label', 'aggregate_funcs': ['sum']},
				]

		grouping_entities= [
				{'expression': '{TestClass1.id}', 'label': 'hist_id', 'as_histogram': True, 'all_values': True, 'num_buckets': 10},
				#{'expression': '{TestClass1.children.name}', 'label': 'name_id', 'all_values': True}
				]

		aggregates = sa_dao.get_aggregates(data_entities=data_entities, grouping_entities=grouping_entities, filters=[])

	def setUp(self):
		super(SA_DAO_Test, self).setUp()

		schema = {}
		self.schema = schema

		schema['classes'] = {}

		class TestClass1(object):
			id = None
			children = []
		schema['classes']['TestClass1'] = TestClass1

		class TestClass2(object):
			id = None
			name = ""
		schema['classes']['TestClass2'] = TestClass2

		schema['primary_class'] = TestClass1

		metadata = MetaData()

		test1_table = Table('test1', metadata,
				Column('id', Integer, primary_key=True)
				)

		test2_table = Table('test2', metadata,
				Column('id', Integer, primary_key=True),
				Column('name', String)
				)

		test1_test2_table = Table('test1_test2', metadata,
				Column('test1_id', Integer, primary_key=True),
				Column('test2_id', Integer, primary_key=True),
				ForeignKeyConstraint(['test1_id'], [test1_table.c.id]),
				ForeignKeyConstraint(['test2_id'], [test2_table.c.id])
				)

		mapper(
				TestClass1, 
				test1_table,
				properties = {
					'children': relationship(TestClass2, secondary=test1_test2_table)
					}
				)

		mapper(
				TestClass2, 
				test2_table,
				properties = {
					}
				)

		metadata.create_all(self.session.bind)

		tc1s = []
		tc2s = []
		for i in range(5):
			tc1 = TestClass1()
			tc1s.append(tc1)
			self.session.add(tc1)

			tc2 = TestClass2()
			tc2.name = "tc2_%s" % i
			tc2s.append(tc2)
			self.session.add(tc2)

		self.session.commit()

		for i in range(len(tc1s)):
			tc1 = tc1s[i]
			child_tc2s = [tc2s[i], tc2s[ (i + 1) % len(tc1s)]]
			for c in child_tc2s:
				tc2 = self.session.query(TestClass2).filter(TestClass2.id == c.id).one()
				tc1.children.append(tc2)
		
		self.session.commit()


if __name__ == '__main__':
	unittest.main()
