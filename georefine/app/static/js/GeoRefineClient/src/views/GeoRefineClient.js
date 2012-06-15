define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"use!ui",
	"_s",
	"Facets",
	"MapView",
	"Windows",
	"Util",
	"text!./templates/GeoRefineClient.html"
		],
function($, Backbone, _, ui, _s, Facets, MapView, Windows, Util, template){

	var GeoRefineClientView = Backbone.View.extend({

		events: {
		},

		initialize: function(){
			$(this.el).addClass('georefine-client');
			this.render();
			this.on('ready', this.onReady, this);
		},

		render: function(){
			var html = _.template(template, {model: this.model});
			$(this.el).html(html);

			this.setUpFacets();
			this.setUpMapView();

			return this;
		},

		onReady: function(){
		},

		setUpFacets: function(){
			var facets = {};
			var lji = new Util.util.LumberjackInterpreter();

			var endpoint = _s.sprintf('%s/projects/get_aggregates/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);

			// The 'getData' functions will be called with a facet model as 'this'.
			var listFacetGetData = function(){
				var data = {
					'filters': JSON.stringify(this.get('filters')),
					'data_entities': JSON.stringify([this.get('count_entity')]),
					'grouping_entities': JSON.stringify([this.get('grouping_entity')]),
				};
				var _this = this;
				$.ajax({
					url: endpoint,
					type: 'GET',
					data: data,
					error: Backbone.wrapError(function(){}, _this, {}),
					success: function(data, status, xhr){
						// Set total.
						var total = data.data[0].value;
						_this.set('total', total, {silent:true});

						// Format choices.
						var choices = [];
						var leafs = lji.parse(data);
						_.each(leafs, function(leaf){
							choices.push({
								id: leaf.id,
								label: leaf.label,
								count: leaf.data[0].value
							});
						});
						_this.set('choices', choices);
					}
				});
			};

			numericFacetGetData = function() {
				var data = {
					'filters': JSON.stringify(this.get('filters')),
					'data_entities': JSON.stringify([this.get('count_entity')]),
					'grouping_entities': JSON.stringify([this.get('grouping_entity')]),
					'with_unfiltered': true,
					'base_filters': JSON.stringify(this.get('base_filters'))
				};
				var _this = this;
				$.ajax({
					url: endpoint,
					type: 'GET',
					data: data,
					error: Backbone.wrapError(function(){}, _this, {}),
					success: function(data, status, xhr){

						// Parse data into histograms.
						var base_histogram = [];
						var filtered_histogram = [];

						var leafs = lji.parse(data);
						_.each(leafs, function(leaf){
							bucket_label = leaf.label;
							var minmax_regex = /(-?\d+(\.\d*)?)\s*,\s*(-?\d+(\.\d*)?)/;
							var match = minmax_regex.exec(bucket_label);
							var bmin, bmax;
							if (match != null){
								bmin = parseFloat(match[1]);
								bmax = parseFloat(match[3]);
							}
							else{
								return;
							}

							var base_bucket = {
								bucket: leaf.label,
								min: bmin,
								max: bmax,
								count: leaf.data[0].value
							};
							base_histogram.push(base_bucket);

							var filtered_bucket = _.extend({}, base_bucket);
							filtered_bucket.count = leaf.data[1].value;
							filtered_histogram.push(filtered_bucket);

						});

						base_histogram = _.sortBy(base_histogram, function(b){return b.count});
						filtered_histogram = _.sortBy(filtered_histogram, function(b){return b.count;});

						_this.set({
							base_histogram: base_histogram,
							filtered_histogram: filtered_histogram
						});
					}
				});
			};

			// For each facet definition...
			_.each(GeoRefine.config.facets, function(facet){

				var model, view;

				if (facet.type == 'list'){
					model = new Facets.models.FacetModel(_.extend({}, facet, {
						choices: []
					}));
					model.getData = listFacetGetData;
					view = new Facets.views.ListFacetView({ model: model });
				}

				else if (facet.type == 'numeric'){
					model = new Facets.models.FacetModel(_.extend({}, facet, {
						filtered_histogram: [],
						base_histogram: []
					}));
					model.getData = numericFacetGetData;
					view = new Facets.views.NumericFacetView({ model: model });
				}

				facets[model.cid] = {
					model: model,
					view: view
				};
			});

			// Create facet collection.
			var facet_models = [];
			_.each(facets, function(facet){
				facet_models.push(facet['model'])
			});
			facet_collection_model = new Facets.models.FacetCollection(facet_models, {});
			facet_collection_view = new Facets.views.FacetCollectionView({
				el: $(_s.sprintf('#%s-facets', this.model.cid)),
				model: facet_collection_model,
			});
			_.each(facets,function(facet){
				facet_collection_view.addFacetView(facet['view']);
			});

			facet_collection_view.updateFacets({force: true});

		},

		setUpMapView : function(){

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

			var mapeditor_m = new Backbone.Model({
				data_layers: processed_layers['data'],
				base_layers: processed_layers['base'],
				overlay_layers: processed_layers['overlay'],
				map_view: map_v
			});

			var mapeditor_v = new MapView.views.MapEditorView({
				model: mapeditor_m
			});

			fillParent= function(el){
				$parent= $(el).parent();
				$(el).css('width', $parent.width());
				$(el).css('height', $parent.height());
			};

			// Setup dock area.
			$.window.prepare({
				"dock": "top",
				"dockArea": $('#log')
			});

			var map_w = new Windows.views.WindowView({
				model: new Backbone.Model({
					"title": "Map",
					"inline-block": true,
				})
			});
			map_w.on("resize", function(){
				fillParent(mapeditor_v.el);
				mapeditor_v.resize();
			});
			map_w.on("resizeStop", function(){mapeditor_v.resizeStop();});
			map_w.on("dragStop", function(){mapeditor_v.trigger('pagePositionChange');});
			map_w.on("minimize", function(){mapeditor_v.deactivate();});
			map_w.on("cascade", function(){mapeditor_v.activate();});
			map_w.on("close", function(){mapeditor_v.remove();});

			$(map_w.getBody()).append(mapeditor_v.el);

			$(document).ready(function(){
				map_w.resize();
				mapeditor_v.trigger('ready');
				map_v.map.zoomToMaxExtent();
			});

		}

	});


	return GeoRefineClientView;

});

