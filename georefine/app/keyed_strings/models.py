from georefine.app import db 
from sqlalchemy import Table, Column, String, Text
from sqlalchemy.orm import mapper

class KeyedString(object):
    query = db.session.query_property()

    def __init__(self, key=None, s=None):
        self.key = key
        self.s = s

table = Table('keyed_string_data', db.metadata,
        Column('key', String, primary_key=True),
        Column('s', Text),
        )

mapper(KeyedString, table)
