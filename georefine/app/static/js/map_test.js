require([
  "jquery",
  "use!backbone",
  "use!underscore",
  "_s",
  "use!ui",
  "use!openlayers",
  "MapView",
  "Util",
],
function($, Backbone, _, _s, ui, ol, MapView, Util){
	
	var setupMapView = function(opts){

		var aggregates_endpoint = _s.sprintf('%s/projects/get_aggregates/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);
		var map_endpoint = _s.sprintf('%s/projects/get_map/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);

		var map_config = GeoRefine.config.map;

		bboxToMaxExtent = function(bbox){
			var extent_coords = _.map(bbox.split(','), function(coord){
				return parseFloat(coord);
			});
			return new OpenLayers.Bounds(extent_coords);
		};

		// Process map extent.
		map_config.max_extent = bboxToMaxExtent(map_config.max_extent);

		_.extend(map_config.default_layer_options, {
			maxExtent: map_config.max_extent
		});

		// This method will be called with a layer as 'this'.
		updateServiceUrlLocalDataLayer = function(attr, options){
			params = [
				['data_entity', this.get('entity')],
				['filters', this.get('filters')]
					];
			url_params = [];
			_.each(params, function(p){
				url_params.push(_s.sprintf("%s=%s", p[0], JSON.stringify(p[1])));
				this.set('service_url', map_endpoint + '?' + url_params.join('&') + '&');
			},this);
		};
		
		var processed_layers = {};
		_.each(['data', 'base', 'overlay'], function(layer_category){
			var layers = map_config[_s.sprintf('%s_layers', layer_category)];
			var layer_collection = new Backbone.Collection();
			_.each(layers, function(layer){

				// If Layer has maxextent, create OpenLayers bounds from it.
				if (layers.max_extent){
					layer.max_extent = bboxToMaxExtent(layer.max_extent);
				}

				// Create model for layer.
				var model = new Backbone.Model(_.extend({},	map_config.default_layer_attributes, layer, {
					'layer_category': layer_category,
					'options': _.extend({}, map_config.default_layer_options, layer.options)
				}));

				// Handle service url updates for various layer types.
				if (layer.source == 'local_getmap'){
					if (layer.entity){
						var entity_model = new Backbone.Model(_.extend({}, layer.entity,{}));
						model.set('entity', entity_model);
					}
					updateServiceUrlLocalDataLayer.call(model);
					model.on('change:entity change:filters', updateServiceUrlLocalDataLayer, model);
				}
				else if (layer.source == 'local_geoserver'){
					var service_url = _s.sprintf("%s/%s/wms", GeoRefine.config.geoserver_url, layer.workspace);
					model.set('service_url', service_url);
				}
				
				layer_collection.add(model);
			});
			processed_layers[layer_category] = layer_collection;
		});

		var map_m = new Backbone.Model(_.extend({
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
			map_config, {
			})
		);

		var map_v = new MapView.views.MapViewView({
			model: map_m
		});
		window.m = map_v.map;

		var mapeditor_m = new Backbone.Model({
			data_layers: processed_layers['data'],
			base_layers: processed_layers['base'],
			overlay_layers: processed_layers['overlay'],
			map: map_v
		});

		var mapeditor_v = new MapView.views.MapEditorView({
			el: $('#main'),
			model: mapeditor_m
		});

		$(document).ready(function(){
			mapeditor_v.trigger('ready');
			map_v.map.zoomToMaxExtent();
		});
		
	};

	setupMapView();

});
