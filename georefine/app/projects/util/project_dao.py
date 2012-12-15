from sa_dao.sqlalchemy_dao import SqlAlchemyDAO
from sqlalchemy.schema import Column
from sqlalchemy.sql import *
from geoalchemy import *


class ProjectDAO(SqlAlchemyDAO):
    """ Extension of SqlAlchemyDAO, w/ addition
    of a method to handle spatial queries for spatialite. """

    # Add GIS funcs.
    valid_funcs = SqlAlchemyDAO.valid_funcs + [
        'func.BuildMbr',
        'func.ST_AsBinary',
        'func.ST_AsText',
        'func.ST_Intersects',
    ]

    def get_spatialite_spatial_query(
        self, query_def=None, geom_entity_def=None, frame_entity_def=None):

        # Get normal query.
        q, q_registries = self.get_query(query_def, return_registries=True)

        # Get entities from registry.
        geom_entity = self.get_registered_entity(
            source_registry=q_registries['sources'],
            entity_registry=q_registries['entities'],
            entity_def=geom_entity_def
        )

        frame_entity = self.get_registered_entity(
            source_registry=q_registries['sources'],
            entity_registry=q_registries['entities'],
            entity_def=frame_entity_def
        )
        # Get entity's source element.
        geom_el = self.get_source_entity(geom_entity)

        # If element is a column...
        if isinstance(geom_el, (Column, RawColumn,)):
            # Get its table.
            geom_table = geom_el.table

            # Create bquery on spatial index for the table, using
            # the frame entity.
            idx_sql = """
            """
            idx_select = select(
                ["ROWID FROM SpatialIndex"],
                and_(
                    # CAREFUL! Order matters here for spatialite.
                    (literal_column('f_table_name') == geom_table.name),
                    (literal_column('search_frame') == frame_entity),
                )
            )

            geom_parent_clause = self.get_table_parent_clause(q, geom_table)

            # Assumes single-column primary key.
            geom_id = [c for c in geom_table.primary_key.columns][0]
            geom_parent_clause.append_whereclause(geom_id.in_(idx_select))

        return q

    def get_table_parent_clause(self, clause, table):
        """ Get clause which contains a given table in a query
        via depth-first search. """
        child_froms = clause.locate_all_froms()
        if table in child_froms:
            return clause
        else:
            for from_ in child_froms:
                if isinstance(from_, Alias):
                    from_ = from_.original
                if isinstance(from_, Select):
                    parent = self.get_table_parent_clause(from_, table)
                    if parent is not None: return parent
            return None

    def get_entity_parent(self, froms, entity):
        """ Get first occurence of entity in query tree, starting
        from the bottom of the tree via depth-first search. """
        parent = None
        for from_ in froms:
            if isinstance(from_, Alias):
                parent = self.get_entity_parent(from_.original.froms, entity)
            elif isinstance(from_, Join) :
                parent = self.get_entity_parent([from_.right, from_.left], entity)

            # If no deeper parent was found, check the current set of columns.
            if parent is None:
                if hasattr(from_, 'columns') and entity.key in from_.columns:
                    col = from_.columns[entity.key]
                    if col is entity:
                        parent = from_

        return parent

    def alter_col(self, col):
        if isinstance(col, GeometryExtensionColumn):
            col = RawColumn(col)
        return col

    def get_source_entity(self, entity):
        print "gse"
        """ Get the original source element for a given entity. 
        If entity is an alias to a column, returns the original column.
        """
        while True:
            if getattr(entity, 'proxies', None) is not None:
                entity = entity.proxies[0]
            elif getattr(entity, 'column', None) is not None:
                entity = entity.column
            else:
                return entity
