import sys
from sqlalchemy.orm import aliased, class_mapper, join
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.orm.properties import RelationshipProperty
from sqlalchemy.sql import func, asc, distinct, and_
from sqlalchemy.sql.expression import column
import copy
import re
from sqlalchemy.sql import compiler

from sqlalchemy import cast, String, case

class SA_DAO(object):

    ops = {
            '==': '__eq__',
            '!=': '__ne__',
            '<': '__lt__',
            '>': '__gt__',
            '<=': '__le__',
            '>=': '__ge__',
            'in': 'in_',
            'intersects': 'intersects',
            }

    def __init__(self, session=None, primary_class=None):
        self.session = session
        self.primary_class = primary_class

    def execute_query(self, **kwargs):
        return self.get_query(**kwargs).all()

    def get_query(self, primary_alias=None, data_entities=[], grouping_entities=[], filters=[], return_registry=False):

        # If no alias was given, registry with aliased primary class.
        if not primary_alias:
            primary_alias = aliased(self.primary_class)

        # Initialize registry and query.
        q_entities = set()
        q_registry = {self.primary_class.__name__: primary_alias}
        q = self.session.query(primary_alias.id)

        # Register entities.
        for entity in data_entities + grouping_entities:
            q = self.register_entity_dependencies(q, q_registry, entity)

        # Add select entities to query.
        for entity in data_entities:
            mapped_entity = self.get_mapped_entity(q_registry, entity)
            q_entities.add(mapped_entity)

        # Add grouping entities to query.
        for entity in grouping_entities:
            mapped_entity = self.get_mapped_entity(q_registry, entity)

            # Handle histogram fields.
            if entity.get('as_histogram'):
                q = self.add_bucket_grouping_to_query(q, q_entities, entity, mapped_entity)

            # Handle non-histogram fields.
            else:
                q = q.group_by(mapped_entity)

                # If entity field has a label entity, add it.
                if entity.has_key('label_entity'):
                    mapped_label_entity = self.get_mapped_entity(q_registry, entity['label_entity'])
                    q_entities.add(mapped_label_entity)
                    q = q.group_by(mapped_label_entity)

        # Process filters.
        for f in filters:

            # Skip empty filters.
            if not f: continue

            # Default operator is '=='.
            if not f.has_key('op'): f['op'] = '=='

            # Register filter entities.
            q = self.register_entity_dependencies(q, q_registry, f['entity'])
            mapped_entity = self.get_mapped_entity(q_registry, f['entity'])

            # Handle mapped operators.
            if self.ops.has_key(f['op']):
                op = getattr(mapped_entity, self.ops[f['op']])
                q = q.filter(op(f['value']))

            # Handle all other operators.
            else:
                q = q.filter(mapped_entity.op(f['op'])(f['value']))

        # Only select required entities.
        q = q.with_entities(*q_entities)

        # Return query (and registry if specified).
        if return_registry:
            return q, q_registry
        else:
            return q


    # Helper function for creating aggregate field labels.
    def get_aggregate_label(self, entity_label, func_name):
        return "%s--%s" % (entity_label, func_name)

    def get_aggregates(self, data_entities=[], grouping_entities=[], **kwargs):

        # Set default aggregate functions on data entities.
        for entity in data_entities:
            entity.setdefault('id', str(id(entity)))
            entity.setdefault('label', entity['id'])
    
        # Process grouping entities.
        grouping_entity_values = {}
        for entity in grouping_entities:
            entity.setdefault('id', str(id(entity)))
            entity.setdefault('label', entity['id'])
            entity.setdefault('label_type', 'alpha')

            # Add label to non-histogram fields.
            if not entity.get('as_histogram'):
                entity.setdefault('label_entity', {'expression': entity['expression']})
                entity['label_entity'].setdefault('label', "%s--label" % entity['id'])

            # Generate values for grouping entities which are configured to
            # include all values, with labels.
            values = []
            if entity.get('all_values'):
                for v in self.get_entity_values(entity):
                    if entity.get('as_histogram'):
                        node_label = v[entity['label']]
                        node_id = v[self.get_bucket_id_label(entity)]
                    else:
                        node_label = v[entity['label_entity']['label']]
                        node_id = v[entity['label']]

                    values.append({
                        'id': node_id,
                        'label': node_label,
                        'label_type': entity['label_type']
                        })
            grouping_entity_values[entity['id']] = values 

        # Get base query and registry .
        bq_primary_alias = aliased(self.primary_class)
        bq, bq_registry = self.get_query(primary_alias=bq_primary_alias, data_entities=data_entities, grouping_entities=grouping_entities, return_registry=True, **kwargs)

        # Add data entity parent keys.
        bq_parent_keys = []
        for entity in data_entities + grouping_entities:
            bq_parent_keys.extend(self.get_entity_parent_keys(bq_registry, entity))
        for pk in bq_parent_keys:
            bq = bq.group_by(pk)
        bq = bq.with_entities(*bq_parent_keys)

        # Create main query by joining on the base query and grouping by the grouping entities.
        subq = bq.subquery()
        q, q_registry = self.get_query(data_entities=data_entities, grouping_entities=grouping_entities, return_registry=True)
        q_parent_keys = []
        for entity in data_entities + grouping_entities:
            q_parent_keys.extend(self.get_entity_parent_keys(q_registry, entity))
        for pk in q_parent_keys:
            q.add_column(pk)
            q = q.group_by(pk)

        join_criteria = []
        for i in range(len(q_parent_keys)):
            bq_pk = bq_parent_keys[i]
            q_pk = q_parent_keys[i]
            join_criteria.append(q_pk == bq_pk)
        q = q.join(subq, and_(*join_criteria))

        # Get aggregate results as dictionaries.
        # Include grouping entities as data entities, so that we can select them.
        rows = self.get_query(data_entities=data_entities + grouping_entities, grouping_entities=grouping_entities, **kwargs).all()
        aggregates = [dict(zip(row.keys(), row)) for row in rows]

        # Initialize result tree with aggregates.
        result_tree = {'label': '', 'id': 'root'}
        for aggregate in aggregates:
            current_node = result_tree
            for entity in grouping_entities:

                # Initialize children if not yet set.
                if not current_node.has_key('children'):
                    current_node['children'] = {}
                    for value in grouping_entity_values.get(entity['id'], []):
                        current_node['children'][value['id']] = {'label': value['label'], 'id': value['id']}

                # Set current node to next tree node (initializing if not yet set).
                if entity.get('as_histogram'):
                    node_id = aggregate[self.get_bucket_id_label(entity)]
                    node_label = aggregate[entity['label']]
                else:
                    node_id = aggregate[entity['label']]
                    node_label = aggregate[entity['label_entity']['label']]

                current_node = current_node['children'].setdefault(node_id, {})

                current_node['id'] = node_id
                current_node['label'] = node_label
                current_node['label_type'] = entity['label_type']

            # We should now be at a leaf. Set leaf's data.
            current_node['data'] = []
            for entity in data_entities:
                current_node['data'].append({
                    'label': entity['label'],
                    'value': aggregate.get(entity['label'])
                    })

        # Set default values for unvisited leafs.
        default_value = []
        for entity in data_entities: 
            default_value.append({
                'label': entity['label'],
                'value': 0
                })

        # Process tree recursively to set values on unvisited leafs and calculate branch values.
        self._process_aggregates_tree(result_tree, default_value_func=lambda: copy.deepcopy(default_value))

        # Merge in aggregates for higher grouping levels (if any).
        if len(grouping_entities) > 0:
            parent_tree = self.get_aggregates(data_entities=data_entities, grouping_entities=grouping_entities[:-1], **kwargs)
            self._merge_aggregates_trees(parent_tree, result_tree)

        return result_tree

    # Helper function to recursively process aggregates result tree.
    def _process_aggregates_tree(self, node, default_value_func=None):
        if node.has_key('children'):
            for child in node['children'].values():
                self._process_aggregates_tree(child, default_value_func)
        else:
            # Set default value on node if it's blank.
            if not node.has_key('data') and default_value_func: node['data'] = default_value_func()
    
    # Helper function to recursively merge tree1 into tree2.
    # Modifies tree2 in-place.
    def _merge_aggregates_trees(self, node1, node2):
        if node1.has_key('children'):
            for child_key in node1['children'].keys():
                self._merge_aggregates_trees(node1['children'][child_key], node2.setdefault('children',{}).setdefault(child_key,{}))
        node2['data'] = node1['data']

    def get_entity_min_max(self, entity, filters=[]):
        min_entity = {'expression': "func.min(%s)" % entity.get('expression'), 'label': 'min'}
        max_entity = {'expression': "func.max(%s)" % entity.get('expression'), 'label': 'max'}
        aggregates = self.get_aggregates(data_entities=[min_entity, max_entity], filters=filters)
        entity_min = aggregates['data'][0]['value']
        entity_max = aggregates['data'][1]['value']
        return entity_min, entity_max

    def register_entity_dependencies(self, q, registry, entity):

        for m in re.finditer('{(.*?)}', entity['expression']):
            entity_id = m.group(1)

            # Process dependencies, from left to right.
            # Here parent refers to the table which contains the entity, grandparent is the table to which
            # the parent should be joined.
            parts = entity_id.split('.')
            for i in range(2, len(parts)):
                parent_id = '.'.join(parts[:i])

                if registry.has_key(parent_id):
                    continue
                else:
                    grandparent_id = '.'.join(parts[:i-1])
                    parent_attr = parts[i-1]
                    mapped_grandparent = registry.get(grandparent_id)
                    parent_prop = class_mapper(mapped_grandparent._AliasedClass__target).get_property(parent_attr)
                    if isinstance(parent_prop, RelationshipProperty):
                        mapped_parent = aliased(parent_prop.mapper.class_)
                        registry[parent_id] = mapped_parent
                        q = q.join(mapped_parent, getattr(mapped_grandparent, parent_attr))
        return q

    # @TODO: HACK FOR NOW.  ASSUMES ALL CLASSES USE 'id' AS PRIMARY KEY.  GENERALIZE THIS LATER.
    def get_entity_parent_keys(self, registry, entity):
        parent_keys = []
        for m in re.finditer('{(.*?)}', entity['expression']):
            entity_id = m.group(1)

            # Here parent refers to the table which contains the entity, grandparent is the table to which
            # the parent should be joined.
            # Assumes that the entity has already been registered.
            parts = entity_id.split('.')

            # If entity component is a direct property off the main parent, there are no parent properties.
            if len(parts) <= 2:
                pass
            # Otherwise, get the keys which are used to connect the parent.
            else:
                parent_id = '.'.join(parts[:-1])
                mapped_parent = registry[parent_id]
                parent_keys.append(mapped_parent.id)
        for i in range(len(parent_keys)):
            parent_keys[i] = parent_keys[i].label("%s_pk%s" % (entity['label'], i))
            
        return parent_keys



    def get_mapped_entity(self, registry, entity):

        # Set default label on entity if none given.
        entity.setdefault('id', str(id(entity)))
        entity.setdefault('label', entity['id'])

        # Create key for entity (expression + label).
        entity_key = "%s-%s" % (entity['expression'], entity['label'] )

        # Return entity if already in registry.
        if registry.has_key(entity_key):
            return registry[entity_key]

        mapped_entities = {}

        # Set defaults on entity.
        entity.setdefault('id', str(id(entity)))
        entity.setdefault('label', entity['id'])

        # Replace entity tokens in expression w/ mapped entities.
        # This will be called for each token match.
        def replace_token_with_mapped_entity(m):
            entity_id = m.group(1)
            parts = entity_id.split('.')
            if len(parts) == 1:
                parent_id = parts[0]
                mapped_entity = registry.get(parent_id)
            else:
                parent_id = '.'.join(parts[:-1])
                child_attr = parts[-1]
                mapped_parent = registry.get(parent_id)
                mapped_entity = getattr(mapped_parent, child_attr)
            mapped_entities[entity_id] = mapped_entity
            return "mapped_entities['%s']" % entity_id

        entity_code = re.sub('{(.*?)}', replace_token_with_mapped_entity, entity['expression'])

        # Evaluate and label.
        mapped_entity = eval(entity_code)
        if isinstance(mapped_entity, AliasedClass): pass
        else:
            mapped_entity = mapped_entity.label(entity['label'])

        # Register.
        registry[entity_key] = mapped_entity

        return mapped_entity
    

    # Select values for a given entity.
    def get_entity_values(self, entity, as_dicts=True):

        # If entity is a histogram entity, handle separately.
        if entity.get('as_histogram'):
            return self.get_histogram_buckets(entity)

        else:
            # Initialize registry and query.
            primary_alias = aliased(self.primary_class)
            q_registry = {self.primary_class.__name__: primary_alias}
            q_entities = set()
            q = self.session.query(primary_alias)

            # Initialize entities queue.
            entities = [entity]

            # Process entities.
            for entity in entities:

                # If entity has label entity, add to entity list.
                if entity.get('label_entity'):
                    entities.append(entity['label_entity'])

                q = self.register_entity_dependencies(q, q_registry, entity)
                mapped_entity = self.get_mapped_entity(q_registry, entity)

                q_entities.add(mapped_entity)
                q = q.group_by(mapped_entity)
                    
            q = q.with_entities(*q_entities)

            rows = q.all()

            # Return field values
            if as_dicts:
                return [dict(zip(row.keys(), row)) for row in rows]
            else: 
                return rows
    
    # Get all buckets for a histogram entity, not just those buckets which have data.
    def get_histogram_buckets(self, entity):
        # Get min, max if not provided.
        entity_min = 0
        entity_max = 0
        if (not entity.has_key('min') or not entity.has_key('max')):
            entity_min, entity_max = self.get_entity_min_max(entity)

        # Override calculated min/max if values were provided.
        if entity.has_key('min'): entity_min = entity.get('min')
        if entity.has_key('max'): entity_max = entity.get('max')

        num_buckets = entity.get('num_buckets', 10)

        # Get bucket width.
        bucket_width = (entity_max - entity_min)/float(num_buckets)

        # Generate bucket values.
        buckets = []
        for b in range(1, num_buckets + 1):
            bucket_min = entity_min + (b - 1) * bucket_width
            bucket_max = entity_min + (b) * bucket_width
            bucket_name = "[%s, %s)" % (bucket_min, bucket_max)
            buckets.append({
                entity['label']: bucket_name,
                self.get_bucket_id_label(entity): b
                })
        buckets.append({
            entity['label']: "[%s, ...)" % entity_max,
            self.get_bucket_id_label(entity): num_buckets + 1
            })

        return buckets

    def get_bucket_id_label(self, entity):
        return "%s--bucket-id" % entity['label']
    

    # Add bucket entity to query.
    def add_bucket_grouping_to_query(self, q, q_entities, entity, mapped_entity):
        # Get min, max if not provided.
        entity_min = 0
        entity_max = 0
        if (not entity.has_key('min') or not entity.has_key('max')):
            entity_min, entity_max = self.get_entity_min_max(entity)

        # Override calculated min/max if values were provided.
        if entity.has_key('min'): entity_min = entity.get('min')
        if entity.has_key('max'): entity_max = entity.get('max')

        num_buckets = entity.get('num_buckets', 10)
        entity_range = entity_max - entity_min

        bucket_width = (entity_max - entity_min)/float(num_buckets)

        # Get bucket field entities.

        # Can use the line below in case db doesn't have width_bucket function.
        #bucket_id_entity = func.greatest(func.round( (((mapped_entity - entity_min)/entity_range) * num_buckets ) - .5) + 1, num_buckets).label(self.get_bucket_id_label(entity))
        bucket_id_entity = func.width_bucket(mapped_entity, entity_min, entity_max, num_buckets).label(self.get_bucket_id_label(entity))
        q_entities.add(bucket_id_entity)
        bucket_label_entity = case(
                [(bucket_id_entity == num_buckets + 1, '[' + cast( entity_max, String) + ', ...)')], 
                else_ = '[' + cast(entity_min + bucket_width * (bucket_id_entity - 1), String ) + ', ' + cast(entity_min + bucket_width * (bucket_id_entity), String) + ')'  ).label(entity['label'])
        q_entities.add(bucket_id_entity)
        q_entities.add(bucket_label_entity)

        q = q.group_by(column(bucket_id_entity._label), column(bucket_label_entity._label))

        return q

    # Get raw sql for given query parameters.
    def get_sql(self, dialect=None, **kwargs):
        q = self.get_query(**kwargs)
        return self.query_to_raw_sql(q, dialect=dialect)

    # Compile a query into raw sql.
    def query_to_raw_sql(self, q, dialect=None):

        # Get dialect object.
        if not dialect:
            # If using jython w/ zxjdbc, need to get normal dialect
            # for bind parameter substitution.
            drivername = q.session.bind.engine.url.drivername
            m = re.match("(.*)\+zxjdbc", drivername)
            if m:
                dialect = self.get_dialect(m.group(1))
            # Otherwise use the normal session dialect.
            else:
                dialect = q.session.bind.dialect
        else:
            dialect = self.get_dialect(dialect)

        statement = q.statement
        comp = compiler.SQLCompiler(dialect, statement)
        enc = dialect.encoding
        params = {}
        for k,v in comp.params.iteritems():
            if isinstance(v, unicode):
                v = v.encode(enc)
            if isinstance(v, str):
                v = comp.render_literal_value(v, str)
            params[k] = v
        raw_sql = (comp.string.encode(enc) % params).decode(enc)
        return raw_sql
    
    def get_dialect(self, dialect):
        try:
            dialects_module = __import__("sqlalchemy.dialects", fromlist=[dialect])
            return getattr(dialects_module, dialect).dialect()
        except:
            return None

    def get_connection_parameters(self):
        engine = self.session.bind.engine
        connection_parameters = {}
        parameter_names = [
                "drivername",
                "host",
                "database",
                "username",
                "password",
                "port"
                ]
        for parameter in parameter_names:
            connection_parameters[parameter] = getattr(engine.url, parameter)

        return connection_parameters

