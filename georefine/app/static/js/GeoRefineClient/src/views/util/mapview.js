define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
    "MapView",
    "./requests",
    "./filters"
		],
function($, Backbone, _, _s, Util, MapView, requestsUtil, filtersUtil){

    // Define layer connectors.
    var layerConnectors = {};

    layerConnectors['default'] = {
        connect: function(layer){
            if (layer.model.get('source') == 'georefine_data_layer'){
                return connectLocalDataLayer(layer);
            }
        },
        disconnect: function(layer){
            if (layer.model.get('source') == 'georefine_data_layer'){
                return disconnectLocalDataLayer(layer);
            }
        }
    };

    layerConnectors['georefine_data_layer'] = {
        connect: function(layer){
            // Change query parameters when layer parameters change.
            layer.model.on('change:data_entity change:primary_filters change:base_filters', layer.model.updateQueryParameters, layer.model);
            // Change service url when query parameters change.
            layer.model.on('change:query_parameters', layer.model.updateServiceUrl, layer.model);
        },
        disconnect: function(layer){
            layer.model.off(null, layer.model.updateServiceUrl);
            layer.model.off(null, layer.model.updateQueryParameters);
        }
    };

    // Connect a layer.  These are a dispatcher functions.
    var getLayerConnector = function(layer, connect){
        var connector = layerConnectors[layer.model.get('source')];
        if (! connector){
            connector = layerConnectors['default'];
        }
        return (connect) ? connector.connect : connector.disconnect;
    };
    var connectLayer = function(layer){
        getLayerConnector(layer, true)(layer);
    };

    var disconnectLayer = function(layer){
        getLayerConnector(layer, false)(layer);
    };

    // Connect/disconnect a map editor.
    var connectMapEditor = function(mapEditor){
        // Connect enabled layers.
        _.each(mapEditor.mapView.layerRegistry, function(layer){
            if (! layer.model.get('disabled')){
                connectLayer(layer);
            }
        });
        
    };

    var disconnectMapEditor = function(mapEditor){
        // Disconnect layers.
        _.each(mapEditor.mapView.layerRegistry, function(layer){
            disconnectLayer(layer);
        });
    };



    // This function will be used by local data layers to set their
    // service url query parameters.
    // The 'this' object will be a layer model.
    var updateQueryParametersLocalDataLayerModel = function(){
        var model = this;

        // Get query.
        var inner_q = {
            'ID': 'inner',
            'SELECT_GROUP_BY': true
        };
        requestsUtil.extendQuery(inner_q, model.get('inner_query'));
        requestsUtil.addFiltersToQuery(model, ['primary_filters', 'base_filters'], inner_q);
        var outer_q = {
            'ID': 'outer',
            'FROM': [{'ID': 'inner', 'SOURCE': inner_q}]
        };
        requestsUtil.extendQuery(outer_q, model.get('outer_query'));

        // Assemble parameters.
        var params = {
            'QUERY': outer_q,
            'GEOM_ID_ENTITY': model.get('geom_id_entity'),
            'GEOM_ENTITY': model.get('geom_entity'),
            'DATA_ENTITY': model.get('data_entity'),
        };

        // Set stringified parameters.
        var jsonParams = JSON.stringify(params);
        model.set('query_parameters', jsonParams);
    };

    // This function is used by local data layers to set their
    // service URLs on change.
    // The 'this' object will be a layer model.
    var updateServiceUrlLocalDataLayerModel = function(){
        var model = this;

        // Deferred object to trigger after url has been set.
        var deferred = $.Deferred();

        // Get shortened parameters key.
        $.ajax({
            url: GeoRefine.app.keyedStringsEndpoint + '/getKey/',
            type: 'POST',
            data: {'s': model.get('query_parameters')},
            // After we get the key back, add it as a query parameter.
            // and set the service_url.
            success: function(data, status, xhr){
                var url_params = [_s.sprintf('PARAMS_KEY=%s', data.key)];
                var service_url = GeoRefine.app.dataLayerEndpoint + '?' + url_params.join('&') + '&';

                // Resolve after load end.
                var onLoadEnd = function(){
                    deferred.resolve();
                    // Disconnect after.
                    model.off('load:end', onLoadEnd);
                };
                model.on('load:end', onLoadEnd);

                // Set the url.
                model.set('service_url', service_url);
            },
            error: function(){
                deferred.reject();
            }
        });

        return deferred;
    };

    // Define layer decorators.
    var layerDecorators = {};
    layerDecorators['default'] = function(layer){

        // Set model to remove callbacks when remove is triggered.
        layer.model.on('remove', function(){ this.off(); }, layer.model);

        // Set default onDisabledChange function for model and 
        // connect to disabled events.
        layer.model.onDisabledChange = function(){
            // Tie visibility to disabled state.
            layer.model.set('visible', ! layer.model.get('disabled'));
            // Connect or disconnect layer.
            if (layer.model.get('disabled')){
                disconnectLayer(layer);
            }
            else{
                connectLayer(layer);
            }
        };
        layer.model.on('change:disabled', function(){
            layer.model.onDisabledChange();
        }, layer.model);
    };

    // Local getmap layer decorator.
    layerDecorators['georefine_data_layer'] = function(layer){

        // Call default decorator.
        layerDecorators['default'](layer);

        // Listen for filter changes.
        _.each(['primary', 'base'], function(filterCategory){
            var groupIds = layer.model.get(filterCategory + "_filter_groups");
            _.each(groupIds, function(groupId){
                var filterGroup = GeoRefine.app.filterGroups[groupId];
                filterGroup.on('change:filters', function(){
                    var filters = _.clone(layer.model.get(filterCategory + '_filters')) || {};
                    filters[groupId] = filterGroup.getFilters();
                    layer.model.set(filterCategory + '_filters', filters);
                }, layer.model);

                // Remove callback when layer is removed.
                layer.model.on('remove', function(){
                    filterGroup.off(null, null, layer.model);
                });
            });
        });

        // Set updateQueryParameters method.
        layer.model.updateQueryParameters = updateQueryParametersLocalDataLayerModel;

        // Set updateServiceUrl method.
        layer.model.updateServiceUrl = updateServiceUrlLocalDataLayerModel;

        // Override onDisabledChange to set visible only after
        // service url has changed.
        layer.model.onDisabledChange = function(){
            // If disabled, then turn visibility off and disconnect.
            if (layer.model.get('disabled')){
                layer.model.set('visible', false);
                disconnectLayer(layer);
            }
            // Otherwise if enabled...
            else{
                // Update filters.
                _.each(['base', 'primary'], function(filterCategory){
                    filtersUtil.updateModelFilters(layer.model, filterCategory);
                });
                // Manually call update query parameters.
                layer.model.updateQueryParameters();

                // If query parameters have changed, then
                // update the service url and connect.
                if (layer.model.hasChanged('query_parameters')){
                    var deferred = layer.model.updateServiceUrl();
                    deferred.then(function(){
                        layer.model.set('visible', true);
                        connectLayer(layer);
                    });
                }
                // Otherwise just set visibility and connect.
                else{
                    layer.model.set('visible', true);
                    connectLayer(layer);
                }
            }
        }
    };

    var decorateLayer = function(layer){
        var decorator = layerDecorators[layer.model.get('source')];
        if (! decorator){
            decorator = layerDecorators['default'];
        }
        decorator(layer);
    };

    // Define layer initializers.
    var layerInitializers = {};
    layerInitializers['georefine_data_layer'] = function(layer){
        // Set filters.
        _.each(['base', 'primary'], function(filterCategory){
            filtersUtil.updateModelFilters(layer.model, filterCategory, {silent: true});
        });
    };

    // Initialize a layer.
    var initializeLayer = function(layer){
        // Initialize the layer.
        var initializer = layerInitializers[layer.model.get('source')];
        if (initializer){
            initializer(layer);
        }
    };

    // Create a map editor.
    var createMapEditor = function(model){
        var mapEditorView = new MapView.views.MapEditorView({
            model: model
        });

        return mapEditorView;
    };

    // Decorate a map editor.
    var decorateMapEditor = function(mapEditor){
        // Decorate the map layers.
        _.each(mapEditor.mapView.layerRegistry, function(layer){
            decorateLayer(layer);
        });
    };

    // Initializer a map editor.
    var initializeMapEditor = function(mapEditor){
        decorateMapEditor(mapEditor);

        // Initialize layers (if enabled).
        _.each(mapEditor.mapView.layerRegistry, function(layer){
            if (! layer.model.get('disabled')){
                initializeLayer(layer);
            }
        });

    };

    // Create a map editor model from the config defaults.
    var createMapEditorModel = function(opts){

        opts = opts || {};
        opts.layers = opts.layers || {};

        // Get map config from config.
        var mapConfig = _.extend({}, GeoRefine.config.maps);

        // Set default max extent on layers to be
        // map's max extent.
        _.extend(mapConfig.default_layer_options, {
            maxExtent: mapConfig.max_extent
        });

        // Create layer collections from config.
        var layerCollections = {};
        _.each(['data', 'base', 'overlay'], function(layerCategory){
            var layers = mapConfig[_s.sprintf('%s_layers', layerCategory)];
            var layerCollection = new Backbone.Collection();

            // Create layer models.
            _.each(layers, function(layerDef){

                // Clone the layer definition.
                var layerDef = JSON.parse(JSON.stringify(layerDef));

                // Merge in provided layer attributes.
                if (opts.layers[layerDef.id]){
                    _.extend(layerDef, opts.layers[layerDef.id]);
                }

                // Set layer category.
                layerDef.layer_category = layerCategory;

                // Create layer model from definition.
                var layerModel = createLayerModelFromDef(mapConfig, layerDef);

                // Add to collection.
                layerCollection.add(layerModel);
            });

            // Save the layer collection.
            layerCollections[layerCategory] = layerCollection;

        });

        // Create map model.
        var mapModel = new Backbone.Model(
                _.extend({
                    layers: new Backbone.Collection(),
                    options: {
                        allOverlays: true,
                        maxExtent: mapConfig.max_extent,
                        restrictedExtent: mapConfig.max_extent,
                        resolutions: mapConfig.resolutions,
                        theme: null
                    },
                    graticule_intervals: [2]
                }, 
                mapConfig,
                opts.map)
                );

        // Create Map Editor model.
        var mapEditorModel = new Backbone.Model({
            data_layers: layerCollections['data'],
            base_layers: layerCollections['base'],
            overlay_layers: layerCollections['overlay'],
            map: mapModel,
            type: 'map'
        });

        return mapEditorModel;

    };

    createLayerModelFromDef = function(mapConfig, layerDef){
        // Create model for layer.
        var layerModel = new Backbone.Model(_.extend({}, 
                mapConfig.default_layer_attributes, 
                layerDef,
                {
                    options: _.extend({}, 
                        mapConfig.default_layer_options, 
                        layerDef.options
                        ),
                    // Have layers include map's filter groups.
                    primary_filter_groups: mapConfig.primary_filter_groups,
                    base_filter_groups: mapConfig.base_filter_groups,
                    // Set initial visible state per disabled state.
                    visible: (layerDef.visible != null) ? layerDef.visible : ! layerDef.disabled
                }
                ));

        // Handle customizations for specific layer types.
        if (layerDef.source == 'georefine_data_layer'){
            _.each(['data_entity', 'geom_entity', 'geom_id_entity'], function(entity_attr){
                if (layerDef[entity_attr]){
                    var entityModel = new Backbone.Model(layerDef[entity_attr]);
                    layerModel.set(entity_attr, entityModel);
                }
            });
        }
        else if (layerDef.source == 'georefine_wms_layer'){
            var service_url = _s.sprintf("%s/%s/wms", GeoRefine.app.WMSLayerEndpoint, layerModel.id);
            layerModel.set('service_url', service_url);
        }

        return layerModel;
    };

    var getMapEditorLayers = function(mapEditor, opts){
        var layers = [];
        _.each(opts.layers, function(layerOpts){
            var layer = mapEditor.mapView.layerRegistry[layerOpts.id];
            if (layer){
                layers.push(layer);
            }
        });
        return layers;
    };

    // Objects to expose.
    var mapViewUtil = {
        createMapEditor: createMapEditor,
        createMapEditorModel: createMapEditorModel,
        initializeMapEditor: initializeMapEditor,
        connectMapEditor: connectMapEditor,
        connectMapEditor: connectMapEditor,
        getMapEditorLayers: getMapEditorLayers
    };
    return mapViewUtil;
});
