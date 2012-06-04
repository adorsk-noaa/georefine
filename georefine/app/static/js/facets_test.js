require([
  "jquery",
  "use!backbone",
  "use!underscore",
  "_s",
  "use!ui",
  "MapView"
],

function($, Backbone, _, _s, ui, MapView){
	console.log('here');
	/*

	var sasi_max_extent = new OpenLayers.Bounds(-79, 31, -65, 45);
	var default_layer_options = {
		maxExtent: sasi_max_extent,
		transitionEffect: 'resize'
	};

	var base_filters = [
		{'field': 'time', 'op': '==', 'value': '2009'},
        {'field': 'tag', 'op': '==', 'value': 'gc30_all'}
	];

	var default_layer_properties = {
		//disabled: false
		disabled: true
	};

	var data_layer_definitions = [
		{
			id: "data1",
			layer_id: 'test-data-layer',
			name: 'Y',
			layer_type: 'WMS',
			layer_category: 'data',
			options: _.extend({}, default_layer_options,{
			}),
			params: {
				transparent: true
			},
			field: new Backbone.Model({
				field_id: 'Y',
				field: 'Y',
				label: 'Y',
				'min': .6,
				'max': .7,
				minauto: false,
				maxauto: false
			}),
			filters: base_filters,
			disabled: false
		},
		{
			id: "data2",
			layer_id: 'test-data-layer2',
			name: 'X',
			layer_type: 'WMS',
			layer_category: 'data',
			options: _.extend({}, default_layer_options,{
			}),
			params: {
				transparent: true
			},
			field: new Backbone.Model({
				field_id: 'X',
				field: 'X',
				label: 'X',
				'min': 0,
				'max': 1,
				minauto: true,
				maxauto: true
			}),
			filters: base_filters,
			disabled: true
		}
	];

	setServiceUrl = function(attr, options){
		params = [
			['RESULT_FIELD', this.get('field')],
			['FILTERS', this.get('filters')]
				];
		url_params = [];
		_.each(params, function(p){
			url_params.push(_s.sprintf("%s=%s", p[0], JSON.stringify(p[1])));
			this.set('service_url', '/results/get_map?' + url_params.join('&') + '&');
		},this);
	};

	var data_layers = new Backbone.Collection();
	_.each(data_layer_definitions, function(d){
		var layer_model = new Backbone.Model(_.extend({}, default_layer_properties, d, {
		}));
		setServiceUrl.call(layer_model);
		layer_model.on('change:field change:filters', setServiceUrl, layer_model);
		data_layers.add(layer_model);
	});


	var base_layer_definitions = [
		{
			id: "base1",
			layer_id: 'base1',
			name: 'Base1',
			layer_type: 'WMS',
			layer_category: 'base',
			options: _.extend({}, default_layer_options,{
			}),
			params: {
			},
			service_url: '/basemap/get_map'
		},
		{
			id: "base2",
			layer_id: 'base2',
			name: 'Base2',
			layer_type: 'WMS',
			layer_category: 'base',
			options: _.extend({}, default_layer_options,{
			}),
			params: {
			},
			service_url: '/basemap/get_map',
		}
	];

	var base_layers = new Backbone.Collection();
	_.each(base_layer_definitions, function(d){
		var layer_model = new Backbone.Model(_.extend({}, default_layer_properties, d, {
		}));
		base_layers.add(layer_model);
	});

	var overlay_layer_definitions = [
		{
			id: "ol1",
			layer_id: 'ol1',
			name: 'Overlay1',
			layer_type: 'WMS',
			layer_category: 'overlay',
			options: _.extend({}, default_layer_options,{
			}),
			params: {
				transparent: true
			},
			//service_url: '/basemap/get_map',
			service_url: 'http://isse.cr.usgs.gov/arcgis/services/Orthoimagery/USGS_EDC_Ortho_HRO/ImageServer/WMSServer',
		},
		{
			id: "ol2",
			layer_id: 'ol22',
			name: 'Overlay2',
			layer_type: 'WMS',
			layer_category: 'overlay',
			options: _.extend({}, default_layer_options,{
			}),
			params: {
			},
			service_url: '/basemap/get_map',
			disabled: true
		}
	];

	var overlay_layers = new Backbone.Collection();
	_.each(overlay_layer_definitions, function(d){
		var layer_model = new Backbone.Model(_.extend({}, default_layer_properties, d, {
		}));
		overlay_layers.add(layer_model);
	});


	var map_m = new Backbone.Model({
		layers: new Backbone.Collection(),
		options: {
			allOverlays: true,
			maxExtent: sasi_max_extent,
			restrictedExtent: sasi_max_extent,
			resolutions: [0.025, 0.0125, 0.00625, 0.003125, 0.0015625, 0.00078125]
		},
		graticule_intervals: [2]
	});

	var map_v = new MapView.views.MapViewView({
		model: map_m
	});

	var mapeditor_m = new Backbone.Model({
		data_layers: data_layers,
		base_layers: base_layers,
		overlay_layers: overlay_layers,
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
	*/

});
