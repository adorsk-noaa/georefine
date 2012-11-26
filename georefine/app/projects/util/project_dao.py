from sa_dao.sqlalchemy_dao import SqlAlchemyDAO
from sqlalchemy.schema import Column
from sqlalchemy.sql import *


class ProjectDAO(SqlAlchemyDAO):
    """ Extension of SqlAlchemyDAO, w/ addition
    of a method to handle spatial queries for spatialite. """

    # Add BuildMbr func for spatialite index queries.
    valid_funcs = SqlAlchemyDAO.valid_funcs + ['func.BuildMbr']

    def get_spatialite_spatial_query(self, query_def, geom_entity_def,
                                     frame_entity_def):
        # Get normal query.
        q, q_registries = self.get_query(query_def, return_registries=True)

        # Get entities from registry.
        geom_entity = self.get_registered_entity(q_registries['sources'],
                                                 q_registries['entities'],
                                                 geom_entity_def)

        frame_entity = self.get_registered_entity(q_registries['sources'],
                                                 q_registries['entities'],
                                                 frame_entity_def)
        # Get entity's element.
        geom_el = geom_entity.proxies[0]

        # If element is a column...
        if isinstance(geom_el, Column):
            # Get its table.
            geom_table = geom_el.table

            
            TODO!!!
            #  @TODO: make this version dependent...only newer sqlites 
            # seem to have spatialindex popualted?

            # Create subquery on spatial index for the table, using
            # the frame entity.
            idx_sql = """
            ROWID FROM SpatialIndex
            """
            idx_subq = subquery(
                'idx_subq', [idx_sql], 
                and_(
                    (literal_column('search_frame') == frame_entity),
                    (literal_column('f_table_name') == geom_table.name)
                )
            )

            geom_rowid = literal_column(geom_table.name + ".ROWID")
            idx_rowid = literal_column('idx_subq.ROWID')
            q = q.select_from(
                geom_table.join( idx_subq, geom_rowid == idx_rowid))

        return q
