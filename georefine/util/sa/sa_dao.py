from sqlalchemy.orm import aliased, class_mapper, join
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.orm.properties import RelationshipProperty
from sqlalchemy.sql import func, asc
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

	def get_entities(self, entity_class=None, filters=[]):
		if entity_class:
			primary_alias = aliased(entity_class)
		else:
			primary_alias = aliased(self.primary_class)

		return self.get_filtered_query(primary_alias = primary_alias, filters=filters).all()

	def get_filtered_query(self, primary_alias=None, filters=[]):

		# If no alias was given, registry with aliased primary class.
		if not primary_alias:
			primary_alias = aliased(self.primary_class)

		# Initialize registry and query.
		q_registry = {self.primary_class.__name__: primary_alias}
		q = self.session.query(primary_alias).distinct(primary_alias.id)

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

		# Return query.
		return q

	
	# Get aggregates query.
	# Note: this assumes that the primary_class has a single 'id' field for joining.
	def get_aggregates_query(self, data_entities=[], grouping_entities=[], filters=None):

		# Get base query as subquery, and select only the primary class id.
		bq_primary_alias = aliased(self.primary_class)
		bq = self.get_filtered_query(primary_alias=bq_primary_alias, filters=filters).with_entities(bq_primary_alias.id)
		bq = bq.subquery()

		# Initialize primary class alias and registry for main query.
		q_primary_alias = aliased(self.primary_class)
		q_registry = {self.primary_class.__name__: q_primary_alias}

		# Initialize list of entities for the main query.
		q_entities = set()

		# Create the main query, and join the basequery on the primary class id.
		q = self.session.query(q_primary_alias).join(bq, q_primary_alias.id == bq.c.id)

		# Register entities.
		for entity in data_entities + grouping_entities:
			q = self.register_entity_dependencies(q, q_registry, entity)

		# Add labeled aggregate entities to query entities.
		for entity in data_entities:

			# Set default aggregate functions.
			entity.setdefault('aggregate_funcs', ['sum'])

			mapped_entity = self.get_mapped_entity(q_registry, entity)

			# Make individual entities for each aggregate function.
			for func_name in entity['aggregate_funcs']:
				aggregate_func = getattr(func, func_name)
				label = entity.get('label', entity['id'])
				aggregate_label = self.get_aggregate_label(label, func_name)
				aggregate_entity = aggregate_func(mapped_entity).label(aggregate_label)
				q_entities.add(aggregate_entity)

		# Process grouping entities.
		for entity in grouping_entities:
			mapped_entity = self.get_mapped_entity(q_registry, entity)

			# Handle histogram fields.
			if entity.get('as_histogram'):
				q = self.add_bucket_grouping_to_query(q, q_entities, entity, mapped_entity)

			# Handle other fields.
			else:
				q_entities.add(mapped_entity)
				q = q.group_by(mapped_entity)

				# If entity field has a label entity, add it.
				if entity.has_key('label_entity'):
					mapped_label_entity = self.get_mapped_entity(q_registry, entity['label_entity'])
					q_entities.add(mapped_label_entity)
					q = q.group_by(mapped_label_entity)

		# Only select required entities.
		q = q.with_entities(*q_entities)

		return q

	# Helper function for creating aggregate field labels.
	def get_aggregate_label(self, entity_label, func_name):
		return "%s--%s" % (entity_label, func_name)

	def get_aggregates(self, data_entities=[], grouping_entities=[], **kwargs):

		# Set default aggregate functions on data entities.
		for entity in data_entities:
			entity.setdefault('id', str(id(entity)))
			entity.setdefault('label', entity['id'])
			entity.setdefault('aggregate_funcs', ['sum'])
	
		# Process grouping entities.
		grouping_entity_values = {}
		for entity in grouping_entities:
			entity.setdefault('id', str(id(entity)))
			entity.setdefault('label', entity['id'])
			entity.setdefault('label_type', 'alpha')

			# Add label to non-histogram fields.
			if not entity.get('as_histogram', False):
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

		# Get aggregate results as dictionaries.
		rows = self.get_aggregates_query(data_entities=data_entities, grouping_entities=grouping_entities, **kwargs).all()
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
				for func_name in entity['aggregate_funcs']:
					aggregate_label = self.get_aggregate_label(entity['label'], func_name)
					current_node['data'].append({
						'label': aggregate_label,
						'value': aggregate.get(aggregate_label)
						})

		# Set default values for unvisited leafs.
		default_value = []
		for entity in data_entities: 
			for func_name in entity['aggregate_funcs']:
				aggregate_label = self.get_aggregate_label(entity['label'], func_name)
				default_value.append({
					'label': aggregate_label,
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
		simple_entity = {
				'expression': entity.get('expression'),
				'aggregate_funcs': ['min', 'max']
				}
		aggregates = self.get_aggregates(data_entities=[simple_entity], filters=filters)
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


	def get_mapped_entity(self, registry, entity):

		mapped_entities = {}

		# Set defaults on entity.
		entity.setdefault('id', str(id(entity)))
		entity.setdefault('label', entity['id'])

		# Replace entity tokens in expression w/ mapped entities.
		# This will be called for each token match.
		def replace_token_with_mapped_entity(m):
			entity_id = m.group(1)
			parts = entity_id.split('.')
			parent_id = '.'.join(parts[:-1])
			child_attr = parts[-1]
			mapped_parent = registry.get(parent_id)
			mapped_entity = getattr(mapped_parent, child_attr)
			mapped_entities[entity_id] = mapped_entity
			return "mapped_entities['%s']" % entity_id

		entity_code = re.sub('{(.*?)}', replace_token_with_mapped_entity, entity['expression'])

		# Evaluate and label.
		mapped_entity = eval(entity_code).label(entity['label'])

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

	# Get a mapserver connection string.
	def get_mapserver_connection_string(self):

		# Get engine associated with the session.
		engine = self.session.bind.engine

		# Map mapserver connection parts to SA's url elements.
		mapserver_to_sa = {
				"host": "host",
				"dbname" : "database",
				"user": "username",
				"password": "password",
				"port": "port"
				}

		# Add connection parts if present.
		connection_parts = []
		for ms_name, sa_name in mapserver_to_sa.items():
			sa_value = getattr(engine.url, sa_name)
			if sa_value: connection_parts.append("%s=%s" % (ms_name, sa_value))

		# Return the combined connection string.
		return " ".join(connection_parts)

	def get_base_mapserver_query(self, filters):

		# Get base query as subquery, and select only the primary class id.
		bq_primary_alias = aliased(self.primary_class)
		bq = self.get_filtered_query(primary_alias=bq_primary_alias, filters=filters).with_entities(bq_primary_alias.id)
		bq = bq.subquery()

		# Initialize primary class alias and registry for main query.
		q_primary_alias = aliased(self.primary_class)
		q_registry = {self.primary_class.__name__: q_primary_alias}

		# Create the main query, and join the basequery on the primary class id.
		q = self.session.query(q_primary_alias).join(bq, q_primary_alias.id == bq.c.id)

		# Initialize list of entities for the main query.
		q_entities = set()

		return q, q_primary_alias, q_registry, q_entities

	# Compile a query into raw sql.
	def query_to_raw_sql(self, q):
		dialect = q.session.bind.dialect
		statement = q.statement
		comp = compiler.SQLCompiler(dialect, statement)
		comp.compile()
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
