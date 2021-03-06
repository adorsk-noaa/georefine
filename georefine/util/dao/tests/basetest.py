import unittest
from sqlalchemy.orm import sessionmaker
from georefine.app import db
from sqlalchemy import MetaData
from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, Integer, String, Float

class BaseTest(unittest.TestCase):

    def setUp(self):
        self.engine = db.engine
        self.Session = sessionmaker()
        self.connection = self.engine.connect()

        # begin a non-ORM transaction
        self.trans = self.connection.begin()

        # bind an individual Session to the connection
        self.session = self.Session(bind=self.connection)

    def tearDown(self):
        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()
        self.session.close()

    def setUpSchemaAndData1(self):
        schema = {}
        sources = {}
        ordered_sources = []

        metadata = MetaData()

        sources['test1'] = Table('test1', metadata,
                Column('id', Integer, primary_key=True),
                Column('name', String)
                )
        ordered_sources.append(sources['test1'])


        sources['test2'] = Table('test2', metadata,
                Column('id', Integer, primary_key=True),
                Column('name', String)
                )
        ordered_sources.append(sources['test2'])

        sources['test1_test2'] = Table('test1_test2', metadata,
                Column('test1_id', Integer, primary_key=True),
                Column('test2_id', Integer, primary_key=True),
                ForeignKeyConstraint(['test1_id'], [sources['test1'].c.id]),
                ForeignKeyConstraint(['test2_id'], [sources['test2'].c.id])
                )
        ordered_sources.append(sources['test1_test2'])
        schema['sources'] = sources
        schema['ordered_sources'] = sources

        metadata.create_all(self.connection)

        tc1s = []
        tc2s = []
        for i in range(5):
            tc1 = {
                    "id": i,
                    "name": "tc1_%s" % i
                    }
            tc1s.append(tc1)
            self.connection.execute(schema['sources']['test1'].insert(), [tc1])

            tc2 = {
                    "id": i,
                    "name": "tc2_%s" % i
                    }
            tc2s.append(tc2)
            self.connection.execute(schema['sources']['test2'].insert(), [tc2])

        for i in range(len(tc1s)):
            tc1 = tc1s[i]
            child_tc2s = [tc2s[i], tc2s[ (i + 1) % len(tc1s)]]
            for tc2 in child_tc2s:
                tc1_tc2 = {
                        "test1_id": tc1['id'],
                        "test2_id": tc2['id']
                        }
                self.connection.execute(schema['sources']['test1_test2'].insert(), [tc1_tc2])

        return schema
