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

		var endpoint = _s.sprintf('/projects/get_map/%s/', GeoRefine.config.project_id);

		var map_config = GeoRefine.config.map;
		map_config = {
			max_extent : new OpenLayers.Bounds(-79, 31, -65, 45),

			resolutions: [0.025, 0.0125, 0.00625, 0.003125, 0.0015625, 0.00078125],

			default_layer_options : {
				transitionEffect: 'resize'
			},

			default_layer_attributes: {
				disabled: true
			},

			base_filters : [],

			data_layers : [
			{
				id: "test1.layer",
				name: 'Test1.Layer',
				local: true,
				layer_type: 'WMS',
				layer_category: 'data',
				options: {},
				params: {
					transparent: true
				},
				entity: new Backbone.Model({
					expression: '{Test1.id}',
					label: 'Test1.ID',
					min: 0,
					max: 1,
				}),
				filters: [],
				disabled: false
			}],

			base_layers: [],
			overlay_layers: []
		};

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
				this.set('service_url', endpoint + '?' + url_params.join('&') + '&');
			},this);
		};
		
		var processed_layers = {};
		_.each(['data', 'base', 'overlay'], function(layer_category){
			var layers = map_config[_s.sprintf('%s_layers', layer_category)];
			var layer_collection = new Backbone.Collection();
			_.each(layers, function(layer){
				var model = new Backbone.Model(_.extend({},	map_config.default_layer_attributes, layer, {
					'layer_category': layer_category,
					'options': _.extend({}, map_config.default_layer_options, layer.options)
				}));

				if (layer_category == 'data' && layer.local){
					updateServiceUrlLocalDataLayer.call(model);
					model.on('change:entity change:filters', updateServiceUrlLocalDataLayer, model);
				}
				layer_collection.add(model);
			});
			processed_layers[layer_category] = layer_collection;
		});

		var map_m = new Backbone.Model({
			layers: new Backbone.Collection(),
			options: {
				allOverlays: true,
				maxExtent: map_config.max_extent,
				restrictedExtent: map_config.max_extent,
				resolutions: map_config.resolutions
			},
			graticule_intervals: [2]
		});

		var map_v = new MapView.views.MapViewView({
			model: map_m
		});

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
