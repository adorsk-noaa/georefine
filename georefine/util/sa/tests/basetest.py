import unittest
from sqlalchemy.orm import sessionmaker
from georefine.app import db

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
