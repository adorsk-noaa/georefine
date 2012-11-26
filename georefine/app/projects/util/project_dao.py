from sa_dao.sqlalchemy_dao import SqlAlchemyDAO
from sqlalchemy.schema import Column
from sqlalchemy.sql import *


class ProjectDAO(SqlAlchemyDAO):
    """ Extension of SqlAlchemyDAO, w/ addition
    of a method to handle spatial queries for spatialite. """

    # Add GIS funcs.
    valid_funcs = SqlAlchemyDAO.valid_funcs + [
        'func.BuildMbr',
    ]

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

            # Create subquery on spatial index for the table, using
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

            geom_rowid = literal_column(geom_table.name + ".ROWID")
            q = q.where(geom_rowid.in_(idx_select))

        return q
