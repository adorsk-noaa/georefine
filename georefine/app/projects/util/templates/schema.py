from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, Integer, String, Float
from sqlalchemy.orm import relationship, mapper
from sqlalchemy import MetaData
from geoalchemy import *


sources = {}
ordered_sources = []
metadata = MetaData()

{% for source in sources %}
sources['{{source.id}}'] = Table(
    '{{source.id}}', 
    metadata,
    {% for col in source.col_strs %}
    {{col}},
    {%- endfor %}
)

{% if source.GeometryDDL %}
GeometryDDL(sources['{{source.id}}'])
{% endif %}

ordered_sources.append({'id': '{{source.id}}', 'source': sources['{{source.id}}']})
{% endfor %}

# This dictionary contains the schema objects GeoRefine will use.
schema = {
    'sources': sources,
    'ordered_sources': ordered_sources,
    'metadata': metadata,
}
