import unittest

from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, Integer, String, Float, MetaData, create_engine
from sqlalchemy.orm import relationship, mapper
from geoalchemy import *
from geoalchemy.postgis import PGComparator
from sqlalchemy.orm import sessionmaker

class My_Test(unittest.TestCase):

    def testFoo(self):
		print "foo"

    def setUp(self):
        self.engine = create_engine('postgresql+zxjdbc://gr:gr@localhost/gr')
        self.Session = sessionmaker()
        connection = self.engine.connect()

        # begin a non-ORM transaction
        self.trans = connection.begin()

        # bind an individual Session to the connection
        self.session = self.Session(bind=connection)

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

