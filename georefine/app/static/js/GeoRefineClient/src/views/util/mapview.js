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

    // This function is used by local data layers to set their
    // service URLs on change.
    // The 'this' object will be a layer model.
    var updateServiceUrlLocalDataLayer = function(attr, options){
        var model = this;

        // We assemble a query, and then get a shortened key for the query.

        // A list of parameters for the map query.
        var params = [];

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

        // Get shortened parameters key.
        var deferred = $.ajax({
            url: GeoRefine.app.keyedStringsEndpoint,
            type: 'POST',
            data: {'s': JSON.stringify(params)},
            // After we get the key back, add it as a query parameter.
            // and set the service_url.
            success: function(data, status, xhr){
                var url_params = [_s.sprintf('PARAMS_KEY=%s', data.key)];
                var service_url = map_endpoint + '?' + url_params.join('&') + '&';
                model.set('service_url', service_url);
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
        var processed_layers = {};
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
                        {'layer_category': layer_category,
                            'options': _.extend({}, 
                                mapConfig.default_layer_options, 
                                procLayer.options)
                        })
                    );


                // Handle service url updates for various layer types.
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
                            });
                    }, this);
                    });

                    // Update service url when related model attributes change.
                    model.on('change:data_entity change:primary_filters change:base_filters', updateServiceUrlLocalDataLayer, model);

                    // Initialize service url.
                    updateServiceUrlLocalDataLayer.call(model);
                }

                else if (procLayer.source == 'local_geoserver'){
                    var service_url = _s.sprintf("%s/%s/wms", GeoRefine.config.geoserver_url, proc_layer.workspace);
                    model.set('service_url', service_url);
                }

                layerCollection.add(model);
            }, this);
            processedLayers[layerCategory] = layerCollection;
        }, this);

        // Setup map model.
        var mapModel = new Backbone.Model(_.extend({
            layers: new Backbone.Collection(),
            options: {
                allOverlays: true,
                maxExtent: map_config.max_extent,
                restrictedExtent: map_config.max_extent,
                resolutions: map_config.resolutions,
                theme: null
            },
            graticule_intervals: [2]
        }, 
        map_config
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

        return mapEditorView;

    };

    // Objects to expose.
    var mapViewUtil = {
        createMapEditor: createMapEditor
    };
    return mapViewUtil;
});
