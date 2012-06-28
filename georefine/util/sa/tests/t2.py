import unittest
from georefine.util.sa.tests.basetest import BaseTest
from georefine.util.sa.sa_dao import SA_DAO

from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, Integer, String, Float
from sqlalchemy.orm import relationship, mapper
from sqlalchemy import MetaData
from geoalchemy import *
from geoalchemy.postgis import PGComparator
from sqlalchemy.orm import class_mapper
from pprint import pprint


class SA_DAO_Test(BaseTest):

    def test_SA_DAO(self):

        sa_dao = SA_DAO(session=self.session, primary_class=self.schema['primary_class'])
        """
        r_entity = {'expression': '{Result}', 'label': 'Result'}
        r_id_entity = {'expression': '{Result.id}', 'label': 'foo'}
        for r in sa_dao.execute_query(data_entities=[r_id_entity])[0:5]:
            print r.keys()
        """

        #"""
        complex_entity = {'expression': 'func.sum({Result.acell.area} + {Result.bcell.area})', 'label': 'complex'}
        substrate_grouping_entity = {'expression': '{Result.substrate.id}', 'label': 'substrate_id', 'all_values': True}

        data_entities = [complex_entity]
        grouping_entities = [substrate_grouping_entity]

        aggregates = sa_dao.get_aggregates(data_entities=data_entities, grouping_entities=grouping_entities, filters=[])
        print pprint(aggregates)

        #"""

    def setUp(self):
        super(SA_DAO_Test, self).setUp()

        schema = {}
        self.schema = schema

        schema['classes'] = {}

        class Result(object):
            id = None
            acell = None
            bcell = None
            substrate = None 
        schema['classes']['Result'] = Result

        class ACell(object):
            id = None
            area = None
        schema['classes']['ACell'] = ACell

        class BCell(object):
            id = None
            area = None
        schema['classes']['BCell'] = BCell

        class Substrate(object):
            id = None
        schema['classes']['Substrate'] = Substrate

        schema['primary_class'] = Result

        metadata = MetaData()

        acell_table = Table('acell', metadata,
                Column('id', Integer, primary_key=True),
                Column('area', Float)
                )
        mapper(ACell, acell_table)

        bcell_table = Table('bcell', metadata,
                Column('id', Integer, primary_key=True),
                Column('area', Float)
                )
        mapper(BCell, bcell_table)

        substrate_table = Table('substrate', metadata,
                Column('id', Integer, primary_key=True),
                )
        mapper(Substrate, substrate_table)

        result_table = Table('result', metadata,
                Column('id', Integer, primary_key=True),
                Column('acell_id', Integer, ForeignKey('acell.id')),
                Column('bcell_id', Integer, ForeignKey('bcell.id')),
                Column('substrate_id', Integer, ForeignKey('substrate.id')),
                )
        mapper(Result, result_table, properties={
            'acell': relationship(ACell),
            'bcell': relationship(BCell),
            'substrate': relationship(Substrate),
            })

        metadata.create_all(self.session.bind)

        acells = []
        bcells = []
        substrates = []
        for i in range(2):
            acell = ACell()
            acell.id = i * 2
            acell.area = acell.id * 10
            acells.append(acell)
            self.session.add(acell)

            bcell = BCell()
            bcell.id = (i * 2) + 1
            bcell.area = bcell.id * 10
            bcells.append(bcell)
            self.session.add(acell)

            substrate = Substrate()
            substrate.id = i
            substrates.append(substrate)
            self.session.add(substrate)

        self.session.commit()

        self.results = []
        for a in acells:
            for b in bcells:
                for s in substrates:
                    r1 = Result()
                    r1.acell = a
                    r1.bcell = b
                    r1.substrate = s
                    self.results.append(r1)
                    self.session.add(r1)

                    r2 = Result()
                    r2.acell = a
                    r2.bcell = b
                    r2.substrate = s
                    self.results.append(r2)
                    self.session.add(r2)
        
        self.session.commit()


if __name__ == '__main__':
    unittest.main()
