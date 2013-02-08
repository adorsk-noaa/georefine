from georefine.app import db 
from sqlalchemy import (Table, Column, Integer, String, Text, ForeignKey,
                        PickleType)
from sqlalchemy.orm import mapper, relationship, backref


class Project(object):
    def __init__(self, id=None, name=None, schema=None, data_dir=None, 
                 static_dir=None, static_url=None):
        self.id = id
        self.name = name
        self.schema = schema
        self.data_dir = data_dir
        self.static_dir = static_dir
        self.static_url = static_url

project_table = Table('project_projects', db.metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('schema', PickleType),
        Column('data_dir', String),
        Column('db_uri', String),
        Column('static_dir', String),
        Column('static_url', String),
        )

mapper(Project, project_table)
