from fiona import collection


class FionaShapefileReader(object):
    def __init__(self, shapefile=""):
        self.c = collection(shapefile, "r")
        self.schema = self.get_schema()
        self.crs = self.c.crs
        self.shapetype = self.c.schema['geometry'].upper()

    def get_schema(self):
        return self.c.schema

    def records(self):
        return self.c.__iter__()

def get_shapefile_reader(shapefile=""):
    return FionaShapefileReader(shapefile=shapefile)
