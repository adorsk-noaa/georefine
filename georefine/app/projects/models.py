from georefine.app import db 
from sqlalchemy import (Table, Column, Integer, String, Text, ForeignKey,
                        PickleType)
from sqlalchemy.orm import mapper, relationship


class Project(object):
    def __init__(self, id=None, name=None, schema=None, app_config=None):
        self.id = id
        self.name = name
        self.schema = schema
        self.app_config = app_config

project_table = Table('project_projects', db.metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('schema', PickleType),
        Column('app_config', PickleType),
        Column('layers_schema', PickleType),
        )
mapper(Project, project_table)

class MapLayer(object):
    def __init__(self, id=None, layer_id=None, project=None, tbl=None, 
                 sld=None):
        self.id = id
        self.layer_id = layer_id
        self.project = project
        self.tbl = tbl
        self.sld = sld

maplayer_table = Table('project_maplayers', db.metadata,
        Column('id', Integer, primary_key=True),
        Column('layer_id', String),
        Column('project_id', Integer, ForeignKey(project_table.c.id)),
        Column('tbl', String),
        Column('sld', Text),
        )
mapper(MapLayer, maplayer_table, properties={
    'project': relationship(Project, backref="maplayers")
})

