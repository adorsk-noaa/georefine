import mapscript as ms
import sys, os, re, struct
import colorsys
import bisect


output_formats = {
    'image/gif': {
        'driver': 'GD/GIF',
        'mimetype': 'image/gif',
        'imagemode': ms.MS_IMAGEMODE_RGBA,
        'extension': 'gif',
        'transparent': ms.MS_ON
    }
}

class MapScriptRenderer(object):

    def renderLayers(self, 
                     mapfile=None,
                     wms_parameters={},
                     layers=[]
                 ):
        mapObj = self.get_mapObj(mapfile=mapfile)

        for layer in layers:
            layerObj = self.get_layerObj(**layer)
            mapObj.insertLayer(layerObj)

        wms_request = ms.OWSRequest()
        for k, v in wms_parameters.items():
            wms_request.setParameter(k,v)
        mapObj.loadOWSParameters(wms_request)

        img = mapObj.draw()
        return img.getBytes()

    def get_rectObj(self, bounds=[-180.0, -90.0, 180.0, 90.0]):
        if isinstance(bounds, str):
            bounds = [float(b) for b in bounds.split(',')]
        return ms.rectObj(*bounds)

    def get_mapObj(self, **kwargs):
        if kwargs.get('mapfile'):
            mapObj = ms.mapObj(kwargs['mapfile'])
        else:
            mapObj = ms.mapObj()

        if kwargs.has_key('extent'):
            mapObj.extent = self.get_rectObj(kwargs['extent'])
        else:
            mapObj.extent = self.get_rectObj()

        if kwargs.has_key('imagecolor'):
            mapObj.imagecolor = ms.colorObj(*kwargs['imagecolor'])

        if kwargs.has_key('projection'):
            mapObj.setProjection(kwargs['projection'])
        else:
            mapObj.setProjection = "init=epsg:4326"

        mapObj.name = "MAP"
        mapObj.status = ms.MS_ON

        return mapObj

    def get_outputFormatObj(self, format_id='image/gif'):
        format_def = output_formats[format_id]
        outputFormatObj = ms.outputFormatObj(format_def['driver'])
        for attr in ['mimetype', 'imagemode', 'extension', 'transparent']:
            setattr(outputFormatObj, attr, format_def[attr])

    def get_layerObj(self, **kwargs):
        layerObj = ms.layerObj()
        layerObj.status = ms.MS_ON
        layerObj.metadata.set('ows_enable_request', '*')
        layerObj.type = getattr(ms, 'MS_LAYER_%s' % kwargs['type'])
        for attr in [
            'name',
            'connection',
            'data',
            'labelitem',
        ]:
            if kwargs.has_key(attr):
                setattr(layerObj, attr, kwargs[attr])
        
        if kwargs.get('connectiontype'):
            layerObj.setConnectionType(
                getattr(ms, 'MS_%s' % kwargs['connectiontype']), '')

        if kwargs.get('extent'):
            layerObj.extent = self.get_rectObj(kwargs['extent'])

        if kwargs.get('units'):
            layerObj.units = getattr(ms, 'MS_%s', kwargs['units'])

        if kwargs.get('sld'):
            layerObj.applySLD(kwargs['sld'])

        if kwargs.get('projection'):
            layerObj.setProjection(kwargs['projection'])
            
        return layerObj
