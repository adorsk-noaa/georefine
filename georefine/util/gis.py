from shapely import wkb, wkt
import shapely.geometry as geometry

def geojson_to_wkb(geojson):
    s = geometry.shape(geojson)
    return wkb.dumps(geometry.shape(geojson))

def geojson_to_wkt(geojson):
    s = geometry.shape(geojson)
    return wkt.dumps(geometry.shape(geojson))
