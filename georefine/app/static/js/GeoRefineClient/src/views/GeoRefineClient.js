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

			var _this = this;
			$(document).ready(function(){
				_this.setUpWindows();
				_this.setUpFilterGroups();
				_this.setUpSummaryBar();
				_this.setUpFacets();
				_this.setUpInitialState();
			});

			return this;
		},

		onReady: function(){
		},

        setUpFilterGroups: function(){
            this.filter_groups = {};

            // Initialize filter groups.
			_.each(GeoRefine.config.filter_groups, function(filter_group_config){
                var filter_group = new Backbone.Collection();
                this.filter_groups[filter_group_config.id] = filter_group;
                filter_group.getFilters = function(){
                    var filters = [];
                    _.each(filter_group.models, function(model){
                        var model_filters = model.get('filters');
                        if (model_filters){
                            filters.push({
                                'source': {
                                    'type': model.getFilterType ? model.getFilterType() : null,
                                    'cid': model.cid
                                },
                                'filters': model_filters
                            });
                        }
                    });
                    return filters;
                };
            }, this);

            // Add listeners for synchronizing linked groups.
			_.each(GeoRefine.config.filter_groups, function(filter_group_config){
                _.each(filter_group_config.linked_groups, function(linked_group_id){
                    var main_group = this.filter_groups[filter_group_config.id];
                    var linked_group = this.filter_groups[linked_group_id];
                    _.each(['add', 'remove'], function(evnt){
                        linked_group.on(evnt, function(model){main_group[evnt](model)});
                    });
                }, this);
            }, this);
        },

		createDataViewWindow: function(data_view, opts){
			opts = opts || {};
			$data_views = $('.data-views', this.el);
			var dv_offset = $data_views.offset();

			var w =  new Windows.views.WindowView({
				model: new Backbone.Model(_.extend({}, {
					"inline-block": true,
					"width": $data_views.width(),
					"height": $data_views.height(),
					"x": dv_offset.left,
					"y": dv_offset.top,
					"showFooter": false,
					"scrollable": false
				}, opts))
			});

			w.on("resize", function(){
				Util.util.fillParent(data_view.el);
				data_view.trigger('resize');
			});

			w.on("resizeStop", function(){
				data_view.trigger('resizeStop');
				Util.util.unsetWidthHeight(data_view.el);
			});
			w.on("dragStop", function(){data_view.trigger('pagePositionChange');});
			w.on("minimize", function(){data_view.trigger('deactivate');});
			w.on("cascade", function(){data_view.trigger('activate');});
			w.on("close", function(){data_view.trigger('remove');});

			$(w.getBody()).append(data_view.el);
			w.resize();
			w.resizeStop();
			data_view.trigger('ready');
		},

		addMapView: function(){
			var map_editor = this.createMapEditor();
			this.createDataViewWindow(map_editor, {
				"title": "Map"
			});
		},

		addChartView: function(){
			var chart_editor = this.createChartEditor();
			this.createDataViewWindow(chart_editor, {
				"title": "Chart"
			});
		},

		setUpWindows: function(){
			$.window.prepare({
				"dock": "right",
				"dockArea": $('.data-views', this.el),
				"handleScrollbar": false
			});
		},

		setUpFacets: function(){
			var facets = {};
			var lji = new Util.util.LumberjackInterpreter();

			var endpoint = _s.sprintf('%s/projects/get_aggregates/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);

			// The 'getData' functions will be called with a facet model as 'this'.
			var listFacetGetData = function(){
				var data = {
					'filters': JSON.stringify(this.get('query_filters')),
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

							var unfiltered_bucket = {
								bucket: leaf.label,
								min: bmin,
								max: bmax,
								count: leaf.data[1].value
							};
							base_histogram.push(unfiltered_bucket);

							var filtered_bucket = _.extend({}, unfiltered_bucket);
							filtered_bucket.count = leaf.data[0].value;
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

            // The 'formatFilter' functions will be called with a facet view as 'this'.
            listFacetFormatFilters = function(selected_values){
                var formatted_filters = [];
                if (selected_values.length > 0){
                    formatted_filters = [{entity: {expression: this.model.get('grouping_entity').expression}, op: 'in', value: selected_values}];
                }
                return formatted_filters;
            };

            numericFacetFormatFilters = function(selected_values){
                var formatted_filters = [
                    { 'entity': {'expression': this.model.get('grouping_entity').expression}, 'op': '>=', 'value': selected_values['selection_min']},
                    { 'entity': {'expression': this.model.get('grouping_entity').expression}, 'op': '<=', 'value': selected_values['selection_max']}
                ];
                return formatted_filters;
            };

            timeSliderFacetFormatFilters = function(selected_value){
                var formatted_filters = [{'entity': {expression: this.model.get('grouping_entity').expression}, op: '==', value: selected_value}];
                return formatted_filters;
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
                    view.formatFilters = listFacetFormatFilters;
				}

				else if (facet.type == 'numeric'){
					model = new Facets.models.FacetModel(_.extend({}, facet, {
						filtered_histogram: [],
						base_histogram: []
					}));
					model.getData = numericFacetGetData;
					view = new Facets.views.NumericFacetView({ model: model });
                    view.formatFilters = numericFacetFormatFilters;
				}

				else if (facet.type == 'time-slider'){
					model = new Facets.models.FacetModel(_.extend({}, facet, {
					}));
                    model.formatFilters = timeSliderFacetFormatFilters;
					view = new Facets.views.TimeSliderFacetView({ model: model });
                }
                
                // Setup the facet's filter group config.
                _.each(facet.filter_groups, function(filter_group_id, key){
                    var filter_group = this.filter_groups[filter_group_id];
                    filter_group.add(model);

                    // When the filter group changes, change the facet's query filters.
                    filter_group.on('change:filters', function(){
                        var all_filters = filter_group.getFilters();
                        var keep_filters = [];
                        // A facet should not use its own selection in the filters.
                        _.each(all_filters, function(filter){
                            if (filter.source.cid != model.cid){
                                keep_filters = keep_filters.concat(filter.filters);
                            }
                        });
                        model.set('query_filters', keep_filters);
                    });
                }, this);

                // Have the facet update when its query filters change.
                if (model.getData){
                    model.on('change:query_filters', function(){
                        model.getData();
                    });
                }

                // Save the facet objects to the registry.
				facets[model.cid] = {
					model: model,
					view: view
				};
			}, this);

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

            // Initialize the facets.
			_.each(facet_collection_model.models, function(model){
                if (model.getData){
                    model.getData();
                }
            });

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

			_.extend(map_config.default_layer_options, {
				maxExtent: map_config.max_extent
			});

			// This method will be called with a layer model as 'this'.
			updateServiceUrlLocalDataLayer = function(attr, options){
				params = [
					['filters', this.get('filters')]
				];
                _.each(['data_entity', 'geom_entity', 'geom_id_entity', 'grouping_entities'], function(entity_attr){
                    entity_model = this.get(entity_attr);
                    if (entity_model){
                        params.push([entity_attr, entity_model.toJSON()]);
                    }
                }, this);
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
						//proc_layer.max_extent = bboxToMaxExtent(proc_layer.max_extent);
						proc_layer.max_extent = proc_layer.max_extent;
					}

					// Create model for layer.
					var model = new Backbone.Model(_.extend({},	map_config.default_layer_attributes, proc_layer, {
						'layer_category': layer_category,
						'options': _.extend({}, map_config.default_layer_options, proc_layer.options)
					}));


					// Handle service url updates for various layer types.
					if (proc_layer.source == 'local_getmap'){
                        _.each(['data_entity', 'geom_entity', 'geom_id_entity'], function(entity_attr){
                            if (proc_layer[entity_attr]){
                                var entity_model = new Backbone.Model(_.extend({}, proc_layer[entity_attr], {}));
                                model.set(entity_attr, entity_model);
                            }
                        });

                        if (proc_layer['grouping_entities']){
                            grouping_entities_collection = new Backbone.Collection();
                            _.each(proc_layer['grouping_entities'], function(grouping_entity){
                                var entity_model = new Backbone.Model(_.extend({}, grouping_entity, {}));
                                grouping_entities_collection.add(entity_model);
                            });
                            model.set('grouping_entities', grouping_entities_collection);
                        }

                        // Have layer model listen for filter changes.
                        // @TODO: put filter groups in layers?
                        _.each(map_config.filter_groups, function(filter_group_id){
                            var filter_group = this.filter_groups[filter_group_id];
                            filter_group.on('change:filters', function(){
                                var filters = [];
                                _.each(filter_group.getFilters(), function(filter){
                                    filters = filters.concat(filter.filters);
                                });
                                model.set('filters', filters);
                            });
                        }, this);

                        updateServiceUrlLocalDataLayer.call(model);
                        model.on('change:data_entity change:geom_entity change:grouping_entities change:filters', updateServiceUrlLocalDataLayer, model);
                    }

					else if (proc_layer.source == 'local_geoserver'){
						var service_url = _s.sprintf("%s/%s/wms", GeoRefine.config.geoserver_url, proc_layer.workspace);
						model.set('service_url', service_url);
					}

					layer_collection.add(model);
				}, this);
				processed_layers[layer_category] = layer_collection;
			}, this);

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

			// Set datasource query to listen to filter group changes.
            _.each(charts_config.filter_groups, function(filter_group_id){
                var filter_group = this.filter_groups[filter_group_id];
                filter_group.on('change:filters', function(){
                    filters = [];
                    _.each(filter_group.getFilters(), function(filter){
                        filters = filters.concat(filter.filters);
                    });
                    model.set('filters', filters);
                });
            }, this);

            // Change the query when filters change.
			this.model.on('change:filters', function(){
				var q = datasource.get("query");
				q.set("filters", this.model.get("filters"));
			}, this);

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
            var summary_bar_config = GeoRefine.config.summary_bar;

			var summary_bar_model = new Backbone.Model({
				"fields": summary_bar_config.quantity_fields,
				"filters": [],
				"selected_field": null,
				"data": {}
			});

			// Listen for filter changes.
            _.each(summary_bar_config.filter_groups, function(filter_group_id){
                var filter_group = this.filter_groups[filter_group_id];
                filter_group.on('change:filters', function(){
                    filters = [];
                    _.each(filter_group.getFilters(), function(filter){
                        filters = filters.concat(filter.filters);
                    });
                    model.set('filters', filters);
                });
            }, this);

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
					this.model.on('change:filters', this.onFiltersChange, this);
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

				setSelectedField: function(field_id){
					this.$select.val(field_id);
					this.model.set('selected_field', this.fields[field_id]);
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

				onFiltersChange: function(){
					if (this.model.get('selected_field')){
						this.model.getData();
					}
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

			this.summary_bar = new SummaryBarView({
				model: summary_bar_model,
				el: $(_s.sprintf("#%s-summary-bar", this.model.cid), this.el)
			});
		},

		onFiltersChange: function(){
		},

		setUpInitialState: function(){
			var initial_state = GeoRefine.config.initial_state;

			// Initialize summary bar.
			this.summary_bar.setSelectedField(initial_state.summary_bar.selected);

			// Initialize Data Views.
			_.each(initial_state.data_views, function(data_view){

				// Handle map data views.
				if (data_view.type == 'map'){
					var map_editor = this.createMapEditor();

					// Handle initial extents.
					if (data_view.hasOwnProperty("initial_extent")){
						map_editor.map_view.model.set('initial_extent', data_view.initial_extent);
					}

					// Handle layer configs.
					_.each(data_view.layers, function(layer){
						map_editor.map_view.layers.get(layer.id).set(layer.attributes);
					});

					// Create window.
					this.createDataViewWindow(map_editor, {
						"title": "Map"
					});
				}

				// Handle chart data views.
				else if (data_view.type == 'chart'){
					var chart_editor = this.createChartEditor();
					_.each(["category", "quantity"], function(field_type){
						var field_attr = _s.sprintf("initial_%s_field", field_type);
						if (data_view.hasOwnProperty(field_attr)){
							var fields = chart_editor.model.get('datasource').get('schema').get(field_type + "_fields");
							var field = fields.get(data_view[field_attr].id);
							field.set(data_view[field_attr].attributes);
							field.get('entity').set(data_view[field_attr].entity);
							chart_editor[_s.sprintf("%s_field_selector", field_type)].model.set(_s.sprintf("selected_field", field_type), field);
						}
					}, this);
					this.createDataViewWindow(chart_editor, {
						"title": "Chart"
					});
				}


			}, this);
			
		}

	});


	return GeoRefineClientView;

});

