import mapscript as ms


class MapScriptRenderer(object):

    def renderLayers(self, 
                     map_parameters={},
                     wms_parameters={},
                     layers=[]
                 ):
        mapObj = self.get_mapObj(**map_parameters)

        for layer in layers:
            layerObj = self.get_layerObj(mapObj=mapObj, **layer)

        if wms_parameters:
            wms_request = ms.OWSRequest()
            for k, v in wms_parameters.items():
                wms_request.setParameter(str(k),str(v))
            mapObj.loadOWSParameters(wms_request)

        #mapObj.save('/tmp/foo.map')
        img = mapObj.draw()
        return img

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
            mapObj.setProjection("init=epsg:4326")

        for attr in ['width', 'height']:
            if kwargs.has_key(attr):
                setattr(mapObj, attr, kwargs[attr])

        mapObj.name = "MAP"
        mapObj.status = ms.MS_ON

        mapObj.web.metadata.set('ows_enable_request', '*')

        return mapObj

    def get_outputFormatObj(self, format_id='image/gif'):
        format_def = output_formats[format_id]
        outputFormatObj = ms.outputFormatObj(format_def['driver'])
        for attr in ['mimetype', 'imagemode', 'extension', 'transparent']:
            setattr(outputFormatObj, attr, format_def[attr])

    def get_layerObj(self, mapObj=None, **kwargs):
        layerObj = ms.layerObj(mapObj)
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
            sld = kwargs['sld']
            layerObj.applySLD(sld['doc'], sld.get('stylelayer'))

        if kwargs.get('projection'):
            layerObj.setProjection(kwargs['projection'])
            
        return layerObj

    def imgObj_to_bytes(self, img):
        return img.getBytes()
