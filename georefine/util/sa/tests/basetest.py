import unittest
from sqlalchemy.orm import sessionmaker
from georefine.app import db

class BaseTest(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.engine = db.engine
		cls.Session = sessionmaker()

	def setUp(self):
		connection = self.engine.connect()

		# begin a non-ORM transaction
		self.trans = connection.begin()

		# bind an individual Session to the connection
		self.session = self.Session(bind=connection)

	def tearDown(self):
		# rollback - everything that happened with the
		# Session above (including calls to commit())
		# is rolled back.
		self.trans.rollback()
		self.session.close()
