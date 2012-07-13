import sys
import re
import copy

from sqlalchemy.sql import *
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

    def __init__(self, connection=None, schema=None):
        self.connection = connection
        self.schema = schema

    # Given a list of query definitions, return results.
    def execute_queries(self, query_defs=[]):
        results = {}
        for query_def in query_defs:
            rows = self.connection.execute(self.get_query(**query_def)).fetchall()
            if query_def.get('AS_DICTS'):
                q_results = [dict(zip(row.keys(), row)) for row in rows]
            else:
                q_results = rows
            results[query_def['ID']] = q_results
        return results
        

    # Return a query object for the given query definition. 
    def get_query(self, FROM=[], SELECT=[], WHERE=[], GROUP_BY=[], ORDER_BY=[], SELECT_GROUP_BY=False, **kwargs):

        # Initialize registries.
        table_registry = {}
        entity_registry = {}

        # Process 'from'.
        from_obj = []
        for table_def in FROM:
            # Process any joins the table has and add to from obj.
            table = self.add_joins(table_registry, table_def)
            from_obj.append(table)

        # Process 'select'.
        columns = []
        for entity_def in SELECT:
            entity = self.get_registered_entity(table_registry, entity_registry, entity_def)
            columns.append(entity)

        # Process 'where'.
        wheres = []
        for where_def in WHERE:
            if not where_def: continue

            # Default operator is '=='.
            if not where_def.has_key('OP'): where_def['OP'] = '=='

            # Get registered entity.
            entity = self.get_registered_entity(table_registry, entity_registry, where_def['ENTITY'])

            # Handle mapped operators.
            if self.ops.has_key(where_def['OP']):
                op = getattr(entity, self.ops[where_def['OP']])
                where = op(where_def['VALUE'])
            # Handle all other operators.
            else:
                where = mapped_entity.op(where_def['OP'])(where_def['VALUE'])
            wheres.append(where)
        # Combine wheres into one clause.
        whereclause = None
        if len(wheres) > 0:
            whereclause = wheres[0]
            if len(wheres) > 1:
                for where in wheres[1:]: 
                    whereclause = whereclause.and_(where)
            
        # Process 'group_by'.
        group_by = []
        for entity_def in GROUP_BY:
            if not entity_def: continue

            entity_def = self.prepare_entity_def(entity_def)

            # Get registered entity.
            entity = self.get_registered_entity(table_registry, entity_registry, entity_def)

            # If entity is a histogram entity, get histogram entities for grouping.
            if entity_def.get('AS_HISTOGRAM'):
                bucket_id_entity, bucket_label_entity = self.get_histogram_entities(table_registry, entity_registry, entity_def)
                group_by.extend([bucket_id_entity, bucket_label_entity])

            # Otherwise just use the plain entity for grouping.
            else:
                group_by.append(entity)

        # Process 'order_by'.
        order_by = []
        for order_by_def in ORDER_BY:
            if not order_by_def: continue
            # If def is a string, we assume it's an entity id.
            if isinstance(order_by_def, str):
                order_by_def = {'ENTITY': order_by_def}
            # Get registered entity.
            entity = self.get_registered_entity(table_registry, entity_registry, order_by_def['ENTITY'])

            # Assign direction.
            if order_by_def.get('DIRECTION') == 'desc':
                order_by_entity = desc(entity)
            else:
                order_by_entity = asc(entity)

            order_by.append(order_by_entity)

        # If 'select_group_by' is true, add group_by entities to select.
        if SELECT_GROUP_BY:
            columns.extend(group_by)


        # Return the query object.
        q = select(
                columns=columns, 
                from_obj=from_obj,
                whereclause=whereclause,
                group_by=group_by,
                order_by=order_by
                )
        return q

    # Prepare a table definition for use.
    def prepare_table_def(self, table_def):
        # If item is a string, we assume the string represents a table name.
        if isinstance(table_def, str):
            table_def = {'TABLE': table_def}

        # If table def has no 'ID' attribute, we use the TABLE by convention.
        table_def.setdefault('ID', table_def['TABLE'])

        return table_def

    # Get or register a table in a table registry.
    def get_registered_table(self, table_registry, table_def):
        table_def = self.prepare_table_def(table_def)

        # Process table if it's not in the registry.
        if not table_registry.has_key(table_def['ID']):

            # If 'table' is not a string, we assume it's a query object and process it.
            if not isinstance(table_def['TABLE'], str):
                table = self.get_query(**table_def['TABLE']).alias(table_def['ID'])

            # Otherwise we lookup the table in the given schema.
            else:
                table = self.schema['tables'][table_def['TABLE']]

            # Save the aliased table to the registry.
            table_registry[table_def['ID']] = table.alias(table_def['ID'])

        return table_registry[table_def['ID']]

    # Add joins to table.
    def add_joins(self, table_registry, table_def):
        table_def = self.prepare_table_def(table_def)

        # Get or register the table.
        table = self.get_registered_table(table_registry, table_def)

        # Recursively process joins.
        for join_def in table_def.get('JOINS', []):
            # Convert to list if given as a non-list.
            if not isinstance(join_def, list):
                join_def = [join_def]

            # Get onclause if given.
            if len(join_def) > 1:
                onclause = join_def[1]
            else:
                onclause = None

            table = table.join(self.add_joins(table_registry, join_def[0]), onclause=onclause)

        return table

    def prepare_entity_def(self, entity_def):
        # If item is a string, we assume the string represents an entity expression.
        if isinstance(entity_def, str):
            entity_def = {'EXPRESSION': entity_def}
        # If item has no ID, assign an arbitrary id.
        entity_def.setdefault('ID', str(id(entity_def)))
        return entity_def


    # Get or register an entity.
    def get_registered_entity(self, table_registry, entity_registry, entity_def):

        entity_def = self.prepare_entity_def(entity_def)

        # Map and register entity if not in the registry.
        if not entity_registry.has_key(entity_def['ID']):

            mapped_entities = {}

            # Replace entity tokens in expression w/ mapped entities.
            # This will be called for each token match.
            def replace_token_with_mapped_entity(m):
                token = m.group(1)
                (table_id, column_id) = token.split('.')
                table = self.get_registered_table(table_registry, table_id)
                mapped_entities[token] = table.c[column_id]
                return "mapped_entities['%s']" % token

            entity_code = re.sub('{{(.*?)}}', replace_token_with_mapped_entity, entity_def['EXPRESSION'])

            # Evaluate and label.
            mapped_entity = eval(entity_code)
            mapped_entity = mapped_entity.label(entity_def['ID'])

            # Register.
            entity_registry[entity_def['ID']] = mapped_entity

        return entity_registry[entity_def['ID']]

    
    def get_keyed_results(self, key_def, query_defs):
        
        # Initialize keyed results.
        keyed_results = {}

        # Shortcut for key entity.
        key_entity = key_def['KEY_ENTITY']
        key_entity = self.prepare_entity_def(key_entity)

        # If all values should be selected for the key entity...
        if key_entity.get('ALL_VALUES'):

            # If key entity is histogram, then generate the keys and labels.
            if key_entity.get('AS_HISTOGRAM'):
                # Generate the label entity.
                label_entity = key_def.setdefault('LABEL_ENTITY', 
                        {'ID': self.get_bucket_id_label(key_def['KEY_ENTITY'])})
                keys_labels = self.get_all_histogram_keys(key_def)

            # Otherwise select the keys and labels per the key_def...
            else:

                # If there was no label entity, use the key entity as the label entity.
                label_entity = key_def.setdefault('LABEL_ENTITY', dict(
                    key_def['KEY_ENTITY'].items() 
                    + {'ID': key_entity['ID'] + "_label"}.items() ) )
                
                # Select keys and labels.
                # We merge the key query attributes with our overrides.
                keys_labels = self.execute_queries([
                    dict(key_def.items() + {
                        'ID': 'keylabel_q', 
                        'AS_DICTS': True, 
                        'SELECT': [key_entity, label_entity],
                        }.items() )
                    ]).values()[0]

            # Shortcuts to key and label ids.
            key_id = key_entity['ID']
            label_id = label_entity['ID']

            # Pre-seed keyed results with keys and labels.
            for key_label in keys_labels:
                key = key_label[key_id]
                label = key_label[label_id]

                keyed_results[key] = {
                        "key": key,
                        "label": label,
                        "data": {}
                        }

        # Otherwise, if not all values for the key entity...
        else:
            # If there was no label entity, use the key entity as the label entity.
            label_entity = key_def.setdefault('LABEL_ENTITY', dict(
                key_def['KEY_ENTITY'].items() 
                + {'ID': key_entity['ID'] + "_label"}.items() ) )

        # Add key and label entities to primary queries.
        for query_def in query_defs:
            SELECT = query_def.get('SELECT', [])
            SELECT.extend([key_def['KEY_ENTITY'], key_def['LABEL_ENTITY']])

        # Execute primary queries.
        results = self.execute_queries(query_defs)

        # For each result set...
        for result_set_id, result_set in results.items():
            # For each result in the result set...
            for result in result_set:

                # Get the result's key and label.
                result_key = result[key_id]
                result_label = result[label_id]

                # Get or create the keyed result.
                keyed_result = keyed_results.setdefault(result_key, {
                    "key": result_key,
                    "label": result_label,
                    "data": {}
                    })
                
                # Add the result to the keyed_result data.
                keyed_result['data'][result_set_id] = result

        # Return the keyed results.
        return keyed_results.values()
                

    def get_all_histogram_keys(self, key_def):

        # Get min/max for key entity if not provided.
        key_entity_def = key_def['KEY_ENTITY']
        if key_entity_def.get('MIN') == None or key_entity_def.get('MAX') == None:
            SELECT = []
            for m in ['MIN', 'MAX']:
                minmax_entity_def = {'ID': m, 'EXPRESSION': "func.%s(%s)" % (m.lower(), key_entity_def.get('EXPRESSION'))}
                SELECT.append(minmax_entity_def)

            # We merge the key query attributes with our overrides.
            minmax = self.execute_queries([
                dict(key_def.items() + {
                    'ID': 'stats_q', 
                    'AS_DICTS': True, 
                    'SELECT': SELECT}.items()
                    ) 
                ]).values()[0][0]

            # set MIN and MAX only if not provided.
            for m in ['MIN', 'MAX']:
                key_entity_def.setdefault(m, minmax[m])

        # Generate buckets.
        return self.get_histogram_buckets(key_def)

    # Get aggregates in tree form.
    def get_aggregates(self, SELECT=[], FROM=[], GROUP_BY=[], WHERE=[], ORDER_BY=[], BASE_WHERE=[], **kwargs):

        # Prepare SELECT and GROUP_BY entities.
        for entity_defs in [SELECT, GROUP_BY]:
            for i in range(len(entity_defs)):
                entity_defs[i] = self.prepare_entity_def(entity_defs[i])

        # Scan for histogram entities in GROUP_BY.
        histogram_entity_defs = []
        for entity_def in GROUP_BY:
            if isinstance(entity_def, dict) and entity_def.get('AS_HISTOGRAM'):
                histogram_entity_defs.append(entity_def)

        # Get min/max for histogram entities using BASE_WHERE.
        histogram_stats = {}
        for histogram_entity_def in histogram_entity_defs:
            # If the entity does not have MIN and MAX set, get them.
            # We do this by altering the primary query.
            # Altered query will select only the min/max for the histogram entity 
            # and remove it from the group by.
            # It will also use the 'base where' conditions.
            # This will allow for common histogram min/max stats to be used for base and primary queries.
            if not histogram_entity_def.has_key('MIN') or not histogram_entity_def.has_key('MAX'):
                min_entity_def = {'ID': 'MIN', 'EXPRESSION': "func.min(%s)" % histogram_entity_def['EXPRESSION']}
                max_entity_def = {'ID': 'MAX', 'EXPRESSION': "func.max(%s)" % histogram_entity_def['EXPRESSION']}
                altered_GROUP_BY = [entity_def for entity_def in GROUP_BY if entity_def != histogram_entity_def ]
                stats = self.execute_queries([{
                    'ID': 'minmax_q',
                    'SELECT': [min_entity_def, max_entity_def],
                    'FROM': FROM,
                    'GROUP_BY' : altered_GROUP_BY,
                    'WHERE' : BASE_WHERE,
                    'ORDER_BY' : ORDER_BY,
                    'AS_DICTS': True
                    }]).values()[0][0]

                # Override MIN and MAX if not provided.
                for stat in ['MIN', 'MAX']:
                    histogram_entity_def.setdefault(stat, stats[stat])

        # Get tree skeletons based on the GROUP BY entities.
        group_by_values = {}
        group_by_appendices = []
        for entity_def in GROUP_BY:
            entity_def.setdefault('LABEL_TYPE', 'alpha')

            # Add label entity to non-histogram fields, if not already provided.
            if not entity_def.get('AS_HISTOGRAM'):
                entity_def.setdefault('LABEL_ENTITY', {'EXPRESSION': entity_def['EXPRESSION']})
                entity_def['LABEL_ENTITY'] = self.prepare_entity_def(entity_def['LABEL_ENTITY'])
                #entity_def['LABEL_ENTITY'].setdefault('ID', "%s--label" % entity_def['ID'])

                # Save label entity to add to GROUP_BY.
                # @TODO: Super kludgy.
                group_by_appendices.append(entity_def['LABEL_ENTITY'])

            # Get values for entities which are configured to
            # include all values, with labels.
            values = []
            if entity_def.get('ALL_VALUES'):
                for v in self.get_entity_values(entity_def, FROM=FROM, WHERE=BASE_WHERE, ORDER_BY=ORDER_BY):
                    if entity_def.get('AS_HISTOGRAM'):
                        node_label = v[entity_def['ID']]
                        node_id = v[self.get_bucket_id_label(entity_def)]
                    else: 
                        node_label = v[entity_def['LABEL_ENTITY']['ID']]
                        node_id = v[entity_def['ID']]

                    values.append({
                        'id': node_id,
                        'label': node_label,
                        'label_type': entity_def['LABEL_TYPE']
                        })
            group_by_values[entity_def['ID']] = values 

        # Get the aggregates, including the group by entities in the select.
        aggregates = self.execute_queries([{
            'ID': 'aggs_q',
            'AS_DICTS': True,
            'SELECT': SELECT,
            'FROM': FROM,
            'GROUP_BY': GROUP_BY + group_by_appendices,
            'ORDER_BY': ORDER_BY,
            'SELECT_GROUP_BY': True
            }]).values()[0]

        # Initialize result tree with aggregates.
        result_tree = {'label': '', 'id': 'root'}
        for aggregate in aggregates:
            current_node = result_tree
            for entity_def in GROUP_BY:

                # Initialize children if not yet set.
                if not current_node.has_key('children'):
                    current_node['children'] = {}
                    for value in group_by_values.get(entity_def['ID'], []):
                        current_node['children'][value['id']] = {'label': value['label'], 'id': value['id']}

                # Set current node to next tree node (initializing if not yet set).
                if entity_def.get('AS_HISTOGRAM'):
                    node_id = aggregate[self.get_bucket_id_label(entity_def)]
                    node_label = aggregate[entity_def['ID']]
                else:
                    node_id = aggregate[entity_def['ID']]
                    node_label = aggregate[entity_def['LABEL_ENTITY']['ID']]

                current_node = current_node['children'].setdefault(node_id, {})

                current_node['id'] = node_id
                current_node['label'] = node_label
                current_node['label_type'] = entity_def['LABEL_TYPE']

            # We should now be at a leaf. Set leaf's data.
            current_node['data'] = []
            for entity_def in SELECT:
                current_node['data'].append({
                    'label': entity_def['ID'],
                    'value': aggregate.get(entity_def['ID'])
                    })

        # Set default values for unvisited leafs.
        default_value = []
        for entity_def in SELECT:
            default_value.append({
                'label': entity_def['ID'],
                'value': 0
                })

        # Process tree recursively to set values on unvisited leafs and calculate branch values.
        self._process_aggregates_tree(result_tree, default_value_func=lambda: copy.deepcopy(default_value))

        # Merge in aggregates for higher grouping levels (if any).
        if len(GROUP_BY) > 0:
            parent_tree = self.get_aggregates(
                    SELECT=SELECT, 
                    FROM=FROM, 
                    GROUP_BY=GROUP_BY[:-1], 
                    ORDER_BY=ORDER_BY,
                    WHERE=WHERE,
                    BASE_WHERE=BASE_WHERE,
                    **kwargs
                    )
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

    def get_entity_values(self, entity_def, FROM=[], WHERE=[], ORDER_BY=[]):
        # Handle histogram entities separately.
        if entity_def.get('AS_HISTOGRAM'):
            return self.get_histogram_buckets(entity_def)
        # Otherwise...
        else:
            # If the entity has a label entity, add it to the select.
            SELECT = [entity_def]
            if entity_def.has_key('LABEL_ENTITY'):
                SELECT.append(entity_def['LABEL_ENTITY'])

            # Return the values.
            values = self.execute_queries([{
                'ID': 'getvalues_q',
                'SELECT': SELECT,
                'FROM': FROM,
                'WHERE': WHERE,
                'ORDER_BY': ORDER_BY,
                'AS_DICTS': True
                }]).values()[0]
            return values

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
            drivername = self.connection.engine.url.drivername
            m = re.match("(.*)\+zxjdbc", drivername)
            if m:
                dialect = self.get_dialect(m.group(1))
            # Otherwise use the normal session dialect.
            else:
                dialect = self.connection.dialect
        else:
            dialect = self.get_dialect(dialect)

        comp = compiler.SQLCompiler(dialect, q)
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

    def get_bucket_parameters(self, entity_def):
        entity_min = entity_def['MIN']
        entity_max = entity_def['MAX']
        num_buckets = entity_def.get('NUM_BUCKETS', 10)
        bucket_width = (entity_max - entity_min)/float(num_buckets)
        return entity_min, entity_max, num_buckets, bucket_width


    # Get all buckets for a histogram entity, not just those buckets which have data.
    def get_histogram_buckets(self, entity_def):
        entity_def = self.prepare_entity_def(entity_def)

        entity_min, entity_max, num_buckets, bucket_width = self.get_bucket_parameters(entity_def)

        # Generate bucket values.
        buckets = []
        for b in range(1, num_buckets + 1):
            bucket_min = entity_min + (b - 1) * bucket_width
            bucket_max = entity_min + (b) * bucket_width
            bucket_name = "[%s, %s)" % (bucket_min, bucket_max)
            buckets.append({
                entity_def['ID']: bucket_name,
                self.get_bucket_id_label(entity_def): b
                })
        buckets.append({
            entity_def['ID']: "[%s, ...)" % entity_max,
            self.get_bucket_id_label(entity_def): num_buckets + 1
            })

        return buckets


    # Get histogram entities for a given entity.
    def get_histogram_entities(self, table_registry, entity_registry, entity_def):
        entity_def = self.prepare_entity_def(entity_def)

        entity_min, entity_max, num_buckets, bucket_width = self.get_bucket_parameters(entity_def)

        # Get or register entity.
        entity = self.get_registered_entity(table_registry, entity_registry, entity_def)

        # Get bucket field entities.
        # Can use the line below in case db doesn't have width_bucket function.
        #bucket_id_entity = func.greatest(func.round( (((mapped_entity - entity_min)/entity_range) * num_buckets ) - .5) + 1, num_buckets).label(self.get_bucket_id_label(entity))
        bucket_id_entity = func.width_bucket(entity, entity_min, entity_max, num_buckets).label(self.get_bucket_id_label(entity_def))
        bucket_label_entity = case(
                [(bucket_id_entity == num_buckets + 1, '[' + cast( entity_max, String) + ', ...)')],
                else_ = '[' + cast(entity_min + bucket_width * (bucket_id_entity - 1), String ) + ', ' + cast(entity_min + bucket_width * (bucket_id_entity), String) + ')' ).label(entity_def['ID'])

        # Return the histogram entities.
        return bucket_id_entity, bucket_label_entity

    def get_bucket_id_label(self, entity_def):
        return "%s--bucket-id" % entity_def['ID']

    
    def get_dialect(self, dialect):
        try:
            dialects_module = __import__("sqlalchemy.dialects", fromlist=[dialect])
            return getattr(dialects_module, dialect).dialect()
        except:
            return None

    def get_connection_parameters(self):
        engine = self.connection.engine
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

