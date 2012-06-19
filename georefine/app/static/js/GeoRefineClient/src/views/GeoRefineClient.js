define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"use!ui",
	"_s",
	"Facets",
	"MapView",
	"Charts",
	"Windows",
	"Util",
	"text!./templates/summary_bar.html",
	"text!./templates/GeoRefineClient.html"
		],
function($, Backbone, _, ui, _s, Facets, MapView, Charts, Windows, Util, summary_bar_template, template){

	var GeoRefineClientView = Backbone.View.extend({

		events: {
			"click .add-map-button": "addMapView",
			"click .add-chart-button": "addChartView"
		},

		initialize: function(){
			$(this.el).addClass('georefine-client');
			this.render();
			this.on('ready', this.onReady, this);
		},

		render: function(){
			var html = _.template(template, {model: this.model});
			$(this.el).html(html);

			this.setUpWindows();
			this.setUpSummaryBar();
			this.setUpFacets();

			return this;
		},

		onReady: function(){
		},

		addMapView: function(){

			var map_editor = this.createMapEditor();

			var w = new Windows.views.WindowView({
				model: new Backbone.Model({
					"title": "Map",
					"inline-block": true,
				})
			});

			w.on("resize", function(){
				Util.util.fillParent(map_editor.el);
				map_editor.resize();
			});

			w.on("resizeStop", function(){
				map_editor.resizeStop();
				Util.util.unsetWidthHeight(map_editor.el);
			});
			w.on("dragStop", function(){map_editor.trigger('pagePositionChange');});
			w.on("minimize", function(){map_editor.deactivate();});
			w.on("cascade", function(){map_editor.activate();});
			w.on("close", function(){map_editor.remove();});

			$(w.getBody()).append(map_editor.el);
			w.resize();
			w.resizeStop();
			map_editor.trigger('ready');
			map_editor.map_view.map.zoomToMaxExtent();
		},

		addChartView: function(){
			var chart_editor = this.createChartEditor();

			var w = new Windows.views.WindowView({
				model: new Backbone.Model({
					"title": "Chart",
					"inline-block": true,
				})
			});

			w.on("resize", function(){
				Util.util.fillParent(chart_editor.el);
				chart_editor.resize();
			});

			w.on("resizeStop", function(){
				chart_editor.resizeStop();
				Util.util.unsetWidthHeight(chart_editor.el);
			});
			w.on("dragStop", function(){chart_editor.trigger('pagePositionChange');});
			w.on("minimize", function(){chart_editor.deactivate();});
			w.on("cascade", function(){chart_editor.activate();});
			w.on("close", function(){chart_editor.remove();});

			$(w.getBody()).append(chart_editor.el);
			w.resize();
			w.resizeStop();
			chart_editor.trigger('ready');
		},

		setUpWindows: function(){
			$.window.prepare({
				"dock": "top",
				"dockArea": $('.dock', this.el),
				"minWinLong": 100,
			});
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

		createMapEditor: function(){

			var aggregates_endpoint = _s.sprintf('%s/projects/get_aggregates/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);
			var map_endpoint = _s.sprintf('%s/projects/get_map/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);

			var map_config = _.extend({}, GeoRefine.config.map);

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

					// Initialize processed layer.
					var proc_layer = _.extend({}, layer);

					// If Layer has maxextent, create OpenLayers bounds from it.
					if (proc_layer.max_extent){
						proc_layer.max_extent = bboxToMaxExtent(proc_layer.max_extent);
					}

					// Create model for layer.
					var model = new Backbone.Model(_.extend({},	map_config.default_layer_attributes, proc_layer, {
						'layer_category': layer_category,
						'options': _.extend({}, map_config.default_layer_options, proc_layer.options)
					}));

					// Handle service url updates for various layer types.
					if (proc_layer.source == 'local_getmap'){
						if (proc_layer.entity){
							var entity_model = new Backbone.Model(_.extend({}, proc_layer.entity,{}));
							model.set('entity', entity_model);
						}
						updateServiceUrlLocalDataLayer.call(model);
						model.on('change:entity change:filters', updateServiceUrlLocalDataLayer, model);
					}
					else if (proc_layer.source == 'local_geoserver'){
						var service_url = _s.sprintf("%s/%s/wms", GeoRefine.config.geoserver_url, proc_layer.workspace);
						model.set('service_url', service_url);
					}

					layer_collection.add(model);
				});
				processed_layers[layer_category] = layer_collection;
			});

			var map_model = new Backbone.Model(_.extend({
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

			var map_view = new MapView.views.MapViewView({
				model: map_model
			});

			var mapeditor_model = new Backbone.Model({
				data_layers: processed_layers['data'],
				base_layers: processed_layers['base'],
				overlay_layers: processed_layers['overlay'],
				map_view: map_view
			});

			var mapeditor_view = new MapView.views.MapEditorView({
				model: mapeditor_model
			});

			return mapeditor_view;

		},


		createChartEditor: function(){
			var lji = new Util.util.LumberjackInterpreter();
			var aggregates_endpoint = _s.sprintf('%s/projects/get_aggregates/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);
			var charts_config = GeoRefine.config.charts;

			// Generate models from fields.
			var processed_fields = {};
			_.each(['category', 'quantity'], function(field_type){
				var fields = charts_config[_s.sprintf('%s_fields', field_type)] || [];
				var field_models = [];
				_.each(fields, function(field){
					entity_model = new Backbone.Model(field['entity']);
					field_model = new Backbone.Model(_.extend({}, field, {
						'field_type': field_type,
								'entity': entity_model
					}));

					field_models.push(field_model);
				});

				processed_fields[field_type] = new Backbone.Collection(field_models);
			});


			// Create schema model from fields.
			var schema = new Charts.models.SchemaModel({
				'category_fields': processed_fields['category'],
				'quantity_fields': processed_fields['quantity']
			});

			// Create datasource.
			var datasource = new Charts.models.DataSourceModel({'schema':  schema });
			datasource.getData = function() {
				var q = datasource.get('query');
				var data = {
					'filters': JSON.stringify(q.get('filters')),
					'data_entities': JSON.stringify(q.get('data_entities')),
					'grouping_entities': JSON.stringify(q.get('grouping_entities')),
				};
				var _this = this;
				$.ajax({
					url: aggregates_endpoint,
					type: 'GET',
					data: data,
					complete: function(xhr, status){
						datasource.set('loading', false);
					},
					error: Backbone.wrapError(function(){}, _this, {}),
					success: function(data, status, xhr){
						datasource.set('data', lji.parse(data));
					}
				});
			};

			// Create model.
			var chart_model = new Charts.models.XYChartModel({});

			// Create chart editor.
			var chart_editor_model = new Backbone.Model({
				'chart': chart_model,
				'datasource': datasource
			});
			var chart_editor_view = new Charts.views.ChartEditorView({
				'model': chart_editor_model
			});

			return chart_editor_view;
		},

		setUpSummaryBar: function(){
			var lji = new Util.util.LumberjackInterpreter();
			var aggregates_endpoint = _s.sprintf('%s/projects/get_aggregates/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);

			var summary_bar_model = new Backbone.Model({
				"fields": GeoRefine.config.summary_bar.quantity_fields,
				"filters": [],
				"selected_field": null,
				"data": {}
			});
			summary_bar_model.getData = function(){
				var _this =  summary_bar_model;
				var data = {
					'filters': JSON.stringify(_this.get('filters')),
					'data_entities': JSON.stringify([_this.get('selected_field').entity]),
					'with_unfiltered': true
				};
				var _this = this;
				$.ajax({
					url: aggregates_endpoint,
					type: 'GET',
					data: data,
					complete: function(xhr, status){
					},
					error: Backbone.wrapError(function(){}, _this, {}),
					success: function(data, status, xhr){
						var parsed_data = lji.parse(data);
						_this.set({
							"data": {
								"filtered": parsed_data[0].data[0].value,
								"unfiltered": parsed_data[0].data[1].value
							}
						});
					}
				});
			};

			var SummaryBarView = Backbone.View.extend({
				events: {
					'change select': 'onSelectChange'
				},
				initialize: function(){
					this.fields = {};
					this.initialRender();
					this.model.on('change:selected_field', this.onSelectedFieldChange, this);
					this.model.on('change:data', this.onDataChange, this);
				},
				initialRender: function(){
					$(this.el).html(summary_bar_template, {});
					this.$select = $('select', this.el);
					_.each(this.model.get('fields'), function(field){
						this.$select.append($(_s.sprintf('<option value="%s">%s</option>', field.id, field.label )));
						this.fields[field.id] = field;
					}, this);

				},
				render: function(){
				},

				onSelectChange: function(e){
					if (! this.selectInitialized){
						this.$select.children('option:first').remove();
						this.selectInitialized = true;
					}
					this.model.set('selected_field', this.fields[this.$select.val()]);
				},
				
				onSelectedFieldChange: function(){
					this.model.getData();
				},

				onDataChange: function(){
					var formatter = this.model.get('selected_field').formatter || function(value){return value};
					var data = this.model.get('data');
					var formatted_selected = formatter(data.filtered);
					var formatted_unfiltered = formatter(data.unfiltered);
					var percentage = 100.0 * data.filtered/data.unfiltered;

					$(".data", this.el).html(_s.sprintf("%s (%.1f%% of %s total)", formatted_selected, percentage, formatted_unfiltered));
				}

			});
			var summary_bar_view = new SummaryBarView({
				model: summary_bar_model,
				el: $(_s.sprintf("#%s-summary-bar", this.model.cid), this.el)
			});
		}

	});


	return GeoRefineClientView;

});

