import sys
from sqlalchemy.sql import *
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

    def __init__(self, connection=None, schema=None):
        self.connection = connection
        self.schema = schema

    # Given a list of query definitions, return results.
    def execute_queries(self, query_defs=[]):
        results = {}
        for query_def in query_defs:
            rows = self.connection.execute(self.get_query(query_def)).fetchall()
            if query_def.get('as_dicts'):
                q_results = [dict(zip(row.keys(), row)) for row in rows]
            else:
                q_results = rows
            results[query_def['id']] = q_results
        return results
        

    # Return a query object for the given query definition. 
    def get_query(self, query_def=None):

        # Initialize registries.
        table_registry = {}
        entity_registry = {}

        # Process 'from'.
        from_obj = []
        for table_def in query_def.get('from', []):
            # Process any joins the table has and add to from obj.
            table = self.add_joins(table_registry, table_def)
            from_obj.append(table)

        # Process 'select'.
        columns = []
        for entity_def in query_def.get('select', []):
            entity = self.get_registered_entity(table_registry, entity_registry, entity_def)
            columns.append(entity)

        # Process 'where'.
        wheres = []
        for where_def in query_def.get('where', []):
            if not where_def: continue

            # Default operator is '=='.
            if not where_def.has_key('op'): where_def['op'] = '=='

            # Get registered entity.
            entity = self.get_registered_entity(table_registry, entity_registry, where_def['entity'])

            # Handle mapped operators.
            if self.ops.has_key(where_def['op']):
                op = getattr(entity, self.ops[where_def['op']])
                where = op(where_def['value'])
            # Handle all other operators.
            else:
                where = mapped_entity.op(f['op'])(f['value'])
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
        for entity_def in query_def.get('group_by', []):
            if not entity_def: continue
            # Get registered entity.
            entity = self.get_registered_entity(table_registry, entity_registry, entity_def)
            group_by.append(entity)

        # Process 'order_by'.
        order_by = []
        for order_by_def in query_def.get('order_by', []):
            if not order_by_def: continue
            # If def is a string, we assume it's an entity id.
            if isinstance(order_by_def, str):
                order_by_def = {'entity': order_by_def}
            # Get registered entity.
            entity = self.get_registered_entity(table_registry, entity_registry, order_by_def['entity'])

            # Assign direction.
            if order_by_def.get('direction') == 'desc':
                order_by_entity = desc(entity)
            else:
                order_by_entity = asc(entity)

            order_by.append(order_by_entity)

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
            table_def = {'id': table_def}

        # If table def has no 'table' attribute, we use the id by convention.
        table_def.setdefault('table', table_def['id'])

        return table_def

    # Get or register a table in a table registry.
    def get_registered_table(self, table_registry, table_def):

        table_def = self.prepare_table_def(table_def)

        # Process table if it's not in the registry.
        if not table_registry.has_key(table_def['id']):

            # If 'table' is not a string, we assume it's a query object and process it.
            if not isinstance(table_def['table'], str):
                table = self.get_query(table_def['table'])

            # Otherwise we lookup the table in the given schema.
            else:
                table = self.schema[table_def['table']]

            # Save the aliased table to the registry.
            table_registry[table_def['id']] = table.alias(table_def['id'])

        return table_registry[table_def['id']]

    # Add joins to table.
    def add_joins(self, table_registry, table_def):
        table_def = self.prepare_table_def(table_def)

        # Get or register the table.
        table = self.get_registered_table(table_registry, table_def)

        # Recursively process joins.
        for join_def in table_def.get('joins', []):
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
        # If item is a string, we assume the string represents an entity id.
        if isinstance(entity_def, str):
            entity_def = {'id': entity_def}
        return entity_def


    # Get or register an entity.
    def get_registered_entity(self, table_registry, entity_registry, entity_def):

        entity_def = self.prepare_entity_def(entity_def)

        # Map and register entity if not in the registry.
        if not entity_registry.has_key(entity_def['id']):

            mapped_entities = {}

            # Replace entity tokens in expression w/ mapped entities.
            # This will be called for each token match.
            def replace_token_with_mapped_entity(m):
                token = m.group(1)
                (table_id, column_id) = token.split('.')
                table = table_registry[table_id]
                mapped_entities[token] = table.c[column_id]
                return "mapped_entities['%s']" % token

            entity_code = re.sub('{(.*?)}', replace_token_with_mapped_entity, entity_def['expression'])

            # Evaluate and label.
            mapped_entity = eval(entity_code)
            mapped_entity = mapped_entity.label(entity_def['id'])

            # Register.
            entity_registry[entity_def['id']] = mapped_entity

        return entity_registry[entity_def['id']]

    # Get raw sql for given query parameters.
    def get_sql(self, query_def=None, dialect=None, **kwargs):
        q = self.get_query(query_def=query_def, **kwargs)
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

