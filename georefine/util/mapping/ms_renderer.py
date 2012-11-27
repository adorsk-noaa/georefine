import mapscript as ms


class MapScriptRenderer(object):

    def render_map(self, **kwargs):
        mapObj = self.get_mapObj(**kwargs)

        for layer in kwargs.get('layers', []):
            layerObj = self.get_layerObj(mapObj=mapObj, **layer)

        if kwargs.get('wms_parameters'):
            wms_request = ms.OWSRequest()
            for k, v in kwargs['wms_parameters'].items():
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
            if not mapObj.extent:
                mapObj.extent = self.get_rectObj()

        if kwargs.has_key('imagecolor'):
            mapObj.imagecolor = ms.colorObj(*kwargs['imagecolor'])

        if kwargs.has_key('projection'):
            mapObj.setProjection(kwargs['projection'])
        else:
            if not mapObj.getProjection():
                mapObj.setProjection("init=epsg:4326")

        for attr in ['width', 'height']:
            if kwargs.has_key(attr):
                setattr(mapObj, attr, kwargs[attr])

        if kwargs.get('apply_sld'):
            mapObj.applySLD(kwargs['apply_sld'])

        if kwargs.get('apply_sld_url'):
            mapObj.applySLDUrl(kwargs['apply_sld_url'])

        if not mapObj.name:
            mapObj.name = "MAP"

        if not mapObj.status:
            mapObj.status = ms.MS_ON

        if not mapObj.web.metadata.get('ows_enable_request'):
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

        if kwargs.get('type'):
            layerObj.type = getattr(ms, 'MS_LAYER_%s' % kwargs['type'].upper())
        
        if kwargs.get('connectiontype'):
            layerObj.setConnectionType(
                getattr(ms, 'MS_%s' % kwargs['connectiontype']), '')

        if kwargs.get('extent'):
            layerObj.extent = self.get_rectObj(kwargs['extent'])

        if kwargs.get('units'):
            layerObj.units = getattr(ms, 'MS_%s', kwargs['units'])

        if kwargs.get('apply_sld'):
            layerObj.applySLD(*kwargs['apply_sld'])

        if kwargs.get('apply_sld_url'):
            layerObj.applySLDUrl(*kwargs['apply_sld_url'])

        for cls in kwargs.get('classes', []):
            classObj = self.get_classObj(layerObj=layerObj, **cls)

        if kwargs.get('projection'):
            layerObj.setProjection(kwargs['projection'])
            
        return layerObj

    def get_classObj(self, layerObj=None, **kwargs):
        if layerObj:
            classObj = ms.classObj(layerObj)
        else:
            classObj = ms.classObj()
        if kwargs.get('expression'):
            classObj.setExpression(kwargs['expression'])
        if kwargs.get('style'):
            styleObj = self.get_styleObj(classObj=classObj, **kwargs['style'])
        return classObj

    def get_styleObj(self, classObj=None, **kwargs):
        if classObj:
            styleObj = ms.styleObj(classObj)
        else:
            styleObj = ms.styleObj(classObj)
        for attr, value in kwargs.items():
            if 'color' in attr:
                if isinstance(value, dict):
                    value = self.get_colorObj(**value)
                else:
                    value = self.get_colorObj(*value)
            setattr(styleObj, attr, value)
        return styleObj

    def get_colorObj(self, r=None, b=None, g=None):
        return ms.colorObj(int(r), int(b), int(g))

    def imgObj_to_bytes(self, img):
        return img.getBytes()
