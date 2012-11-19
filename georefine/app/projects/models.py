from georefine.app import db 
from sqlalchemy import (Table, Column, Integer, String, Text, ForeignKey,
                        PickleType)
from sqlalchemy.orm import mapper, relationship, backref


class Project(object):
    def __init__(self, id=None, name=None, schema=None, app_config=None,
                 data_dir=None, static_dir=None, static_url=None):
        self.id = id
        self.name = name
        self.schema = schema
        self.app_config = app_config

project_table = Table('project_projects', db.metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('schema', PickleType),
        Column('app_config', PickleType),
        Column('data_dir', String),
        Column('static_dir', String),
        Column('static_url', String),
        )

class MapLayer(object):
    def __init__(self, id=None, layer_id=None, project=None, dir_=None,
                 metadata=None):
        self.id = id
        self.layer_id = layer_id
        self.project = project
        self.dir_
        self.metadata = metadata

maplayer_table = Table('project_maplayers', db.metadata,
        Column('id', Integer, primary_key=True),
        Column('layer_id', String),
        Column('project_id', Integer, ForeignKey(project_table.c.id)),
        Column('dir_', String),
        Column('metadata', PickleType),
        )

mapper(Project, project_table, properties={
    'maplayers': relationship(
        MapLayer,
        cascade="all, delete-orphan",
        single_parent=True,
    )
})
mapper(MapLayer, maplayer_table, properties={
    'project': relationship(Project)
})

