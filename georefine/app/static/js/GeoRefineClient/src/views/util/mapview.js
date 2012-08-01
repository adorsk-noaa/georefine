define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
    "MapView",
    "./requests"
		],
function($, Backbone, _, _s, Util, MapView, requestsUtil){

    var setLocalDataLayerConnections = function(layerModel, connect){
        if (connect){
            // Change query parameters when layer parameters change.
            layerModel.on('change:data_entity change:primary_filters change:base_filters', layerModel.updateQueryParameters, layerModel);
            // Change service url when query parameters change.
            layerModel.on('change:query_parameters', layerModel.updateServiceUrl, layerModel);
        }
        else{
            layerModel.off(null, layerModel.updateServiceUrl);
            layerModel.off(null, layerModel.updateQueryParameters);
        };
    };

    var setLayerConnections = function(layerModel, connect){
        if (layerModel.get('source') == 'local_getmap'){
            return setLocalDataLayerConnections(layerModel, connect);
        }
    };

    // This function will be used by local data layers to set their
    // service url query parameters.
    // The 'this' object will be a layer model.
    var updateQueryParametersLocalDataLayer = function(){
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
            'FROM': [{'ID': 'inner', 'TABLE': inner_q}]
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
    var updateServiceUrlLocalDataLayer = function(){
        var model = this;

        // Deferred object to trigger after url has been set.
        var deferred = $.Deferred();

        // Get shortened parameters key.
        $.ajax({
            url: GeoRefine.app.keyedStringsEndpoint,
            type: 'POST',
            data: {'s': model.get('query_parameters')},
            // After we get the key back, add it as a query parameter.
            // and set the service_url.
            success: function(data, status, xhr){
                var url_params = [_s.sprintf('PARAMS_KEY=%s', data.key)];
                var service_url = GeoRefine.app.mapEndpoint + '?' + url_params.join('&') + '&';

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


    // Create a map editor window.
    var createMapEditor = function(){

        var mapConfig = _.extend({}, GeoRefine.config.maps);

        // Set default max extent on layers to be
        // map's max extent.
        _.extend(mapConfig.default_layer_options, {
            maxExtent: mapConfig.max_extent
        });


        // Process layers from config.
        var processedLayers = {};
        _.each(['data', 'base', 'overlay'], function(layerCategory){
            var layers = mapConfig[_s.sprintf('%s_layers', layerCategory)];
            var layerCollection = new Backbone.Collection();

            _.each(layers, function(layer){
                // Initialize processed layer.
                var procLayer = _.extend({
                    options: {}
                }, layer);

                // Create model for layer.
                var model = new Backbone.Model(_.extend({},	
                    mapConfig.default_layer_attributes, 
                    procLayer, 
                    {
                        layer_category: layerCategory,
                        options: _.extend({}, 
                            mapConfig.default_layer_options, 
                            procLayer.options
                        ),
                        // Have layers include map's filter groups.
                        primary_filter_groups: mapConfig.primary_filter_groups,
                        base_filter_groups: mapConfig.base_filter_groups,
                        // Set initial visible state per disabled state.
                        visible: (layer.visible != null) ? layer.visible : ! layer.disabled
                    }
                ));

                // Set model to remove callbacks when remove is triggered.
                model.on('remove', function(){
                    this.off();
                }, model);

                // Set default onDisabledChange function for model and 
                // connect to disabled events.
                model.onDisabledChange = function(){
                    // Tie visibility to disabled state.
                    this.set('visible', ! this.get('disabled'));
                    // Connect layer.
                    setLayerConnections(this, ! this.get('disabled'));
                };
                model.on('change:disabled', function(){
                    this.onDisabledChange();
                }, model);

                // If the layer isn't disabled initially, then connect it.
                if (! model.get('disabled')){
                    setLayerConnections(model, true);
                }

                // Handle customizations for specific layer types.
                // @TODO: break this out into sub functions for cleanliness?
                if (procLayer.source == 'local_getmap'){
                    _.each(['data_entity', 'geom_entity', 'geom_id_entity'], function(entity_attr){
                        if (procLayer[entity_attr]){
                            var entityModel = new Backbone.Model(procLayer[entity_attr]);
                            model.set(entity_attr, entityModel);
                        }
                    });

                    // Have layer model listen for filter changes.
                    _.each(['primary', 'base'], function(filterCategory){
                        var groupIds = mapConfig[filterCategory + "_filter_groups"];
                        _.each(groupIds, function(groupId){
                            var filterGroup = GeoRefine.app.filterGroups[groupId];
                            filterGroup.on('change:filters', function(){
                                var filters = _.clone(model.get(filterCategory + '_filters')) || {};
                                filters[groupId] = filterGroup.getFilters();
                                model.set(filterCategory + '_filters', filters);
                            }, model);

                            // Remove callback when model is removed.
                            model.on('remove', function(){
                                filterGroup.off(null, null, model);
                            });
                        });
                    });

                    // Set updateQueryParameters method.
                    model.updateQueryParameters= updateQueryParametersLocalDataLayer;

                    // Set updateServiceUrl method.
                    model.updateServiceUrl = updateServiceUrlLocalDataLayer;

                    // Override onDisabledChange to set visible only after
                    // service url has changed.
                    model.onDisabledChange = function(){
                        var _this = this;
                        // If disabled, then disconnect and turn visibility off.
                        if (_this.get('disabled')){
                            _this.set('visible', false);
                            setLayerConnections(_this, false);
                        }
                        // Otherwise if enabled...
                        else{
                            // Update filters.
                            _.each(['base', 'primary'], function(filterCategory){
                                updateLayerFilters(_this, filterCategory);
                            });
                            // Manually call update query parameters.
                            _this.updateQueryParameters();

                            // If query parameters have changed, then
                            // update the service url and connect.
                            if (_this.hasChanged('query_parameters')){
                                var deferred = _this.updateServiceUrl();
                                deferred.then(function(){
                                    _this.set('visible', true);
                                    setLayerConnections(_this, true);
                                });
                            }
                            // Otherwise just set visibility and connect.
                            else{
                                _this.set('visible', true);
                                setLayerConnections(_this, true);
                            }
                        }
                    }

                }

                else if (procLayer.source == 'local_geoserver'){
                    var service_url = _s.sprintf("%s/%s/wms", GeoRefine.config.geoserver_url, procLayer.workspace);
                    model.set('service_url', service_url);
                }

                // Add layer to layer collection.
                layerCollection.add(model);

            }, this);
            processedLayers[layerCategory] = layerCollection;
        }, this);

        // Setup map model.
        var mapModel = new Backbone.Model(_.extend({
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
        mapConfig
        ));

        // Setup the mapview.
        var mapView = new MapView.views.MapViewView({
            model: mapModel
        });

        // Setup the map editor.
        var mapEditorModel = new Backbone.Model({
            data_layers: processedLayers['data'],
            base_layers: processedLayers['base'],
            overlay_layers: processedLayers['overlay'],
            map_view: mapView
        });
        var mapEditorView = new MapView.views.MapEditorView({
            model: mapEditorModel
        });

        return {
            model: mapEditorModel,
            view: mapEditorView
        };

    };

    var updateLayerFilters = function(layerModel, filterCategory, opts){
        var groupIds = layerModel.get(filterCategory + "_filter_groups");
        _.each(groupIds, function(groupId){
            _.each(groupIds, function(groupId){
                var filters = _.clone(layerModel.get(filterCategory + '_filters')) || {} ;
                var filterGroup = GeoRefine.app.filterGroups[groupId];
                filters[groupId] = filterGroup.getFilters();
                var setObj = {};
                setObj[filterCategory + '_filters'] = filters;
                layerModel.set(setObj, opts);
            });
        });
    };

    var getMapEditorLayerModels = function(mapEditor, opts){
        var layerModels = [];
        _.each(opts.layers, function(layer){
            var layerModel = mapEditor.view.map_view.layers.get(layer.id);
            layerModels.push(layerModel);
        });
        return layerModels;
    };

    // Objects to expose.
    var mapViewUtil = {
        createMapEditor: createMapEditor,
        getMapEditorLayerModels: getMapEditorLayerModels
    };
    return mapViewUtil;
});
