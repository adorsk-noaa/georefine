define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"use!ui",
    "use!qtip",
	"_s",
	"Facets",
	"MapView",
	"Charts",
	"Windows",
	"Util",
	"./util/main",
	"text!./templates/GeoRefineClient.html",
	"text!./templates/flyout_template.html"
		],
function($, Backbone, _, ui, qtip, _s, Facets, MapView, Charts, Windows, Util, GeoRefineViewsUtil, template, flyout_template){


    var requests_endpoint = _s.sprintf('%s/projects/execute_requests/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);
    var keyed_strings_endpoint = _s.sprintf('%s/ks/getKey/', GeoRefine.config.context_root);

	var GeoRefineClientView = Backbone.View.extend({

		events: {
			'click .filters-editor-container .title': 'toggleFiltersEditor',
			"click .add-map-button": "addMapView",
			"click .add-chart-button": "addChartView"
		},

		initialize: function(){
			$(this.el).addClass('georefine-client');

            this.data_view_counter = 1;
            this.data_view_defaults = {
                width: 500,
                height: 500
            };

			this.render();
			this.on('ready', this.onReady, this);

		},

		render: function(){
			var html = _.template(template, {model: this.model});
			$(this.el).html(html);

			var _this = this;
			$(document).ready(function(){
				_this.setUpFacets();
                _this.loadState();
                /*
				_this.setUpWindows();
				_this.setUpFilterGroups();
                _this.setUpSummaryBar();
                _this.setUpFiltersEditor();
				_this.setUpInitialState();
                _this.resize();
                */
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

            _.each(this.filter_groups, function(fg, fg_id){
                fg.on('change:filters', function(){
                });
            });
        },

        setUpFiltersEditor: function(){
            // Generate quantity field collection from config.
            this.facet_quantity_fields = new Backbone.Collection();
            _.each(GeoRefine.config.facets.quantity_fields, function(field){
                var model = new Backbone.Model(_.extend({}, field));
                this.facet_quantity_fields.add(model);
            }, this);

            // Setup quantity field selector.
            var choices = [];
            _.each(this.facet_quantity_fields.models, function(model){
                choices.push({
                    value: model.cid,
                    label: model.get('label'),
                    info: model.get('info')
                });
            });
            this.filters_qfield_select = new Util.views.InfoSelectView({
                el : $('.quantity-field-info-select', this.el),
                model: new Backbone.Model({
                    "choices": choices
                })
            });

            // When the quantity field selector changes, update the facets and summary bar.
            var _this = this;
            this.filters_qfield_select.model.on('change:selection', function(){
                var val = _this.filters_qfield_select.model.get('selection');
                var selected_field = _this.facet_quantity_fields.getByCid(val);
                _.each(_this.facets.models, function(facet){
                    facet.set('quantity_field', selected_field);
                }, _this);
                _this.summary_bar.model.set('quantity_field', selected_field);
            });

            // Resize the filters editor.
            $('.filters-editor', this.el).height();
        },

        // Helper function for merging a set of grouped filter objects into a list.
        // filter objects are keyed by filter group id.
        _filterObjectGroupsToArray: function(groups){
            filters_hash = {};
            _.each(groups, function(group){
                _.each(group, function(filter_obj){
                    var key = JSON.stringify(filter_obj.filters);
                    filters_hash[key] = filter_obj;
                });
            });
            var combined_filters = [];
            _.each(filters_hash, function(filter_obj){
                if (filter_obj.filters){
                    combined_filters = combined_filters.concat(filter_obj.filters);
                }
            });

            return combined_filters;
        },
    
		createDataViewWindow: function(data_view, opts){
			opts = opts || {};
			$data_views = $('.data-views', this.el);
			var dv_offset = $data_views.offset();

            // Set default title.
            opts.title = opts.title || 'Window';

            // Add window number to title.
            opts.title = _s.sprintf("%d &middot; %s", this.data_view_counter, opts.title);

            // Merge with defaults.
            var opts = _.extend({
                "inline-block": true,
                "width": this.data_view_defaults.width,
                "height": this.data_view_defaults.height,
                "x": (this.data_view_counter % 5) * 20,
                "y": (this.data_view_counter % 5) * 20,
                "showFooter": false,
                "scrollable": false
            }, opts);

            // Add offset to x, y
            opts.x += dv_offset.left;
            opts.y += dv_offset.top;

			var w =  new Windows.views.WindowView({
				model: new Backbone.Model(opts)
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
			w.on("close", function(){
                data_view.trigger('remove');
                w.model = null;
                w.remove();
            });

			$(w.getBody()).append(data_view.el);
			w.resize();
			w.resizeStop();
			data_view.trigger('ready');

            this.data_view_counter += 1;
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
            // Shortcut for facets util functions.
            var facetsUtil = GeoRefineViewsUtil.facetsUtil;

            // Setup facets collection.
			var $facets = $(_s.sprintf('#%s-facets', this.model.cid));
            this.facets = facetsUtil.createFacetCollection({el: $facets});
		},

		createMapEditor: function(){

			var map_endpoint = _s.sprintf('%s/projects/get_map/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);

			var map_config = _.extend({}, GeoRefine.config.maps);

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
            var _app = this;
			updateServiceUrlLocalDataLayer = function(attr, options){
                var model = this;

                // Url needs to include the query, geom entity, geom id entity, value entity,

                // A list of parameters to be added to the service url.
				var params = [];

                // Get query.
                var inner_q = {
                    'ID': 'inner',
                    'SELECT_GROUP_BY': true
                };
                _app.extendQuery(inner_q, model.get('inner_query'));
                _app.addFiltersToQuery(model, ['primary_filters', 'base_filters'], inner_q);
                var outer_q = {
                    'ID': 'outer',
                    'FROM': [{'ID': 'inner', 'TABLE': inner_q}]
                };
                _app.extendQuery(outer_q, model.get('outer_query'));

                // Assemble parameters.
                var params = {
                    'QUERY': outer_q,
                    'GEOM_ID_ENTITY': model.get('geom_id_entity'),
                    'GEOM_ENTITY': model.get('geom_entity'),
                    'DATA_ENTITY': model.get('data_entity'),
                };

                // Get shortened parameters key.
				$.ajax({
					url: keyed_strings_endpoint,
					type: 'POST',
					data: {'s': JSON.stringify(params)},
                    complete: function(){
                    },
					error: Backbone.wrapError(function(){
                        console.log("error", arguments);
                    }, model, {}),
                    // After we get the key back, add it as a query parameter.
                    // and set the service_url.
					success: function(data, status, xhr){
                        var url_params = [_s.sprintf('PARAMS_KEY=%s', data.key)];
                        var service_url = map_endpoint + '?' + url_params.join('&') + '&';
                        model.set('service_url', service_url);
                    }
                });
			};

			var processed_layers = {};
			_.each(['data', 'base', 'overlay'], function(layer_category){
				var layers = map_config[_s.sprintf('%s_layers', layer_category)];
				var layer_collection = new Backbone.Collection();
				_.each(layers, function(layer){

					// Initialize processed layer.
					var proc_layer = _.extend({
                        options: {}
                    }, layer);

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

                        // Have layer model listen for filter changes.
                        _.each(map_config.primary_filter_groups, function(filter_group_id){
                            var filter_group = this.filter_groups[filter_group_id];
                            filter_group.on('change:filters', function(){
                                var filters = _.clone(model.get('primary_filters')) || {};
                                filters[filter_group_id] = filter_group.getFilters();
                                model.set('primary_filters', filters);
                            });
                        }, this);

                        // Listen for base filter changes.
                        _.each(map_config.base_filter_groups, function(filter_group_id, key){
                            var filter_group = this.filter_groups[filter_group_id];
                            filter_group.on('change:filters', function(){
                                var filters = _.clone(model.get('base_filters')) || {};
                                filters[filter_group_id] = filter_group.getFilters();
                                model.set('base_filters', filters);
                            });
                        }, this);

                        // Update service url when related model attributes change.
                        model.on('change:data_entity change:primary_filters change:base_filters', updateServiceUrlLocalDataLayer, model);

                        // Initialize service url.
                        updateServiceUrlLocalDataLayer.call(model);
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
            map_config
            ));

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
			var charts_config = GeoRefine.config.charts;

			// Generate models from fields.
			var processed_fields = {};
			_.each(['category', 'quantity'], function(field_type){
				var fields = charts_config[_s.sprintf('%s_fields', field_type)] || [];
				var field_models = [];
				_.each(fields, function(field){
                    var entity_model = null;
                    if (field_type == 'category'){
                        var entity_defaults = {};
                        if (field.value_type == 'numeric'){
                            _.extend(entity_defaults, {
                                "num_classes": 5,
                                "min": 0,
                                "maxauto": true
                            });
                        }
					    entity_model = new Backbone.Model(
                            _.extend(entity_defaults, field['KEY']['KEY_ENTITY'])
                        );
                    }
                    else if (field_type =='quantity'){
                        var entity_defaults = {
                            'min': 0,
                            'maxauto': true
                        };
                        var quantity_entity = field['outer_query']['SELECT'][0];
					    entity_model = new Backbone.Model(
                            _.extend(entity_defaults, quantity_entity)
                        );
                    }
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

            var q = datasource.get('query');

            var _app = this;
			datasource.getData = function() {
                var cfield = q.get('category_field');
                var qfield = q.get('quantity_field');

                if (! cfield || ! qfield){
                    return;
                }

                // Copy the key entity.
                var key = JSON.parse(JSON.stringify(cfield.get('KEY')));

                // Merge in values from the category field's entity model.
                _.each(cfield.get('entity').toJSON(), function(v, k){
                    key['KEY_ENTITY'][k.toUpperCase()] = v;
                });

                // Set base filters on key entity context.
                if (! key['KEY_ENTITY']['CONTEXT']){
                    key['KEY_ENTITY']['CONTEXT'] = {};
                }
                var key_context = key['KEY_ENTITY']['CONTEXT'];
                _app.addFiltersToQuery(q, ['base_filters'], key_context);

                // Get the base query.
                var base_inner_q = _app.makeKeyedInnerQuery(q, key, ['base_filters']);
                var base_outer_q = _app.makeKeyedOuterQuery(q, key, base_inner_q, 'base');

                // Get the primary query.
                var primary_inner_q = _app.makeKeyedInnerQuery(q, key, ['base_filters', 'primary_filters']);
                var primary_outer_q = _app.makeKeyedOuterQuery(q, key, primary_inner_q, 'primary');

                // Assemble the keyed result parameters.
                var keyed_results_parameters = {
                    "KEY": key,
                    "QUERIES": [base_outer_q, primary_outer_q]
                };

                // Assemble keyed query request.
                var requests = [];
                var keyed_query_request = {
                    'ID': 'keyed_results',
                    'REQUEST': 'execute_keyed_queries',
                    'PARAMETERS': keyed_results_parameters
                };
                requests.push(keyed_query_request);

				$.ajax({
					url: requests_endpoint,
					type: 'POST',
					data: {'requests': JSON.stringify(requests)},
                    complete: function(){
                        datasource.set('loading', false);
                    },
					error: Backbone.wrapError(function(){
                        console.log("error", arguments);
                    }, q, {}),
					success: function(data, status, xhr){
                        var results = data.results;
                        var count_entity = qfield.get('outer_query')['SELECT'][0];

                        // Format data for chart.
                        var chart_data = [];

                        _.each(results['keyed_results'], function(result){
                            var base_value = null;
                            if (result['data']['base']){
                                var base_value = result['data']['base'][count_entity['ID']];
                            }

                            var primary_value = null;
                            if (result['data']['primary']){
                                primary_value = result['data']['primary'][count_entity['ID']];
                            }

                            var chart_datum = {
                                id: result.key,
                                label: result.label,
                                data: {
                                    'primary': {value: primary_value},
                                    'base': {value: base_value}
                                }
                            };

                            // If key is a histogram key...
                            if (key['KEY_ENTITY']['AS_HISTOGRAM']){
                                // Get min/max for the bucket.
                                var bminmax = _app.getBucketMinMax(result['label']);
                                chart_datum.min = bminmax.min;
                                chart_datum.max = bminmax.max;

                                // Format the label.
                                var f_minmax = {};
                                _.each(['min', 'max'], function(minmax){
                                    f_minmax[minmax] = Util.util.friendlyNumber(chart_datum[minmax], 1);
                                });
                                var formatted_label = _s.sprintf("[%s, %s)", f_minmax.min, f_minmax.max);
                                chart_datum.label = formatted_label;
                            }

                            chart_data.push(chart_datum);
                        });

                        // If key is histogram, sort data.
                        if (key['KEY_ENTITY']['AS_HISTOGRAM']){
                            chart_data = _.sortBy(chart_data, function(datum){
                                return datum.min;
                            });
                        }


						datasource.set('data', chart_data);
					}
				});
			};

			// Listen for primary filter changes.
            _.each(charts_config.primary_filter_groups, function(filter_group_id){
                var filter_group = this.filter_groups[filter_group_id];
                filter_group.on('change:filters', function(){
                    var filters = _.clone(q.get('primary_filters')) || {};
                    filters[filter_group_id] = filter_group.getFilters();
                    q.set('primary_filters', filters);
                });
            }, this);

            // Listen for base filter changes.
            _.each(charts_config.base_filter_groups, function(filter_group_id, key){
                var filter_group = this.filter_groups[filter_group_id];
                filter_group.on('change:filters', function(){
                    var base_filters = _.clone(q.get('base_filters')) || {};
                    base_filters[filter_group_id] = filter_group.getFilters();
                    q.set('base_filters', base_filters);
                });
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

            // Set number formatting on chart editor.
            chart_editor_view.chart_view.formatQuantityLabel = function(formatString, value){
                return Util.util.friendlyNumber(value,1);
            };

			return chart_editor_view;
		},

		setUpSummaryBar: function(){
            var summary_bar_config = GeoRefine.config.summary_bar;

			var model = new Backbone.Model({
                "id": "summary_bar",
				"primary_filters": {},
				"base_filters": {},
				"quantity_field": null,
                "data": {}
			});

			// Listen for primary filter changes.
            _.each(summary_bar_config.primary_filter_groups, function(filter_group_id){
                var filter_group = this.filter_groups[filter_group_id];
                filter_group.on('change:filters', function(){
                    var filters = _.clone(model.get('query_filters')) || {};
                    filters[filter_group_id] = filter_group.getFilters();
                    model.set('primary_filters', filters);
                });
            }, this);

            // Listen for base filter changes.
            _.each(summary_bar_config.base_filter_groups, function(filter_group_id, key){
                var filter_group = this.filter_groups[filter_group_id];
                filter_group.on('change:filters', function(){
                    var base_filters = _.clone(model.get('base_filters')) || {};
                    base_filters[filter_group_id] = filter_group.getFilters();
                    model.set('base_filters', base_filters);
                });
            }, this);


            var _app = this;
			model.getData = function(){
				var _this = this;

                // Shortcuts.
                var qfield = _this.get('quantity_field');

                // If there's no quantity field don't do anything.
                if (! qfield){
                    return;
                }

                // Get the 'selected' query.
                var selected_inner_q = {
                    'ID': 'inner',
                    'SELECT_GROUP_BY': true,
                };
                _app.extendQuery(selected_inner_q, qfield.get('inner_query'));
                _app.addFiltersToQuery(model, ['primary_filters', 'base_filters'], selected_inner_q);
                var selected_q = {
                    'ID': 'selected',
                    'FROM': [{'ID': 'inner', 'TABLE': selected_inner_q}],
                    'SELECT_GROUP_BY': true,
                };
                _app.extendQuery(selected_q, qfield.get('outer_query'));

                // Get the 'total' query.
                var total_inner_q = {
                    'ID': 'inner',
                    'SELECT_GROUP_BY': true,
                };
                _app.extendQuery(total_inner_q, qfield.get('inner_query'));
                _app.addFiltersToQuery(model, ['base_filters'], total_inner_q);
                var total_q = {
                    'ID': 'total',
                    'FROM': [{'ID': 'inner', 'TABLE': total_inner_q}],
                    'SELECT_GROUP_BY': true,
                };
                _app.extendQuery(total_q, qfield.get('outer_query'));
                
                // Assemble request.
                var totals_request = {
                    'ID': 'totals',
                    'REQUEST': 'execute_queries',
                    'PARAMETERS': {'QUERIES': [selected_q, total_q]}
                };

                var requests = [totals_request];

				$.ajax({
					url: requests_endpoint,
					type: 'POST',
					data: {'requests': JSON.stringify(requests)},
					error: Backbone.wrapError(function(){}, _this, {}),
					success: function(data, status, xhr){
                        var results = data.results;
                        var count_entity = qfield.get('outer_query')['SELECT'][0];

                        var selected = results['totals']['selected'][0][count_entity['ID']];
                        var total = results['totals']['total'][0][count_entity['ID']];
                        model.set('data', {
                            "selected": selected,
                            "total": total
                        });
					}
				});
			};

			var SummaryBarView = Backbone.View.extend({
				initialize: function(){
                    $(this.el).html('<div class="text"><div>Currently selected <span class="field"></span>:<div class="selected"></div><div class="total"></div></div>');
                    // Trigger update when model data changes.
					this.model.on('change:data', this.onDataChange, this);

                    // Get data when parameters change.
                    if (this.model.getData){

                        // helper function to get a timeout getData function.
                        var _timeoutGetData = function(){
                            var delay = 500;
                            return setTimeout(function(){
                                model.getData();
                                model.set('_fetch_timeout', null);
                            }, delay);
                        };

                        this.model.on('change:primary_filters change:base_filters change:quantity_field', function(){

                            // We delay the get data call a little, in case multiple things are changing.
                            // The last change will get executed.
                            var fetch_timeout = model.get('_fetch_timeout');
                            // If we're fetching, clear the previous fetch.
                            if (fetch_timeout){
                                clearTimeout(fetch_timeout);
                            }
                            // Start a new fetch.
                            model.set('_fetch_timeout', _timeoutGetData(arguments));
                        });
                    }
				},

				onDataChange: function(){
					var format = this.model.get('quantity_field').get('format') || "%s";
					var data = this.model.get('data');

                    // Do nothing if data is incomplete.
                    if (data.selected == null || data.total == null){
                        return;
                    }

					var formatted_selected = _grFormat(format, data.selected);
					var formatted_total = _grFormat(format, data.total);
					var percentage ;
                    if (data.total == 0 && data.selected == 0){
                        percentage = 100.0;
                    }
                    else{
                        percentage = 100.0 * data.selected/data.total;
                    }

					$(".text .field", this.el).html(_s.sprintf("'%s'", this.model.get('quantity_field').get('label')));
					$(".text .selected", this.el).html(formatted_selected);
					$(".text .total", this.el).html(_s.sprintf('(%.1f%% of %s total)', percentage, formatted_total));

                    // Set totals on facets.
                    _.each(_app.facets.models, function(facet_model){
                        facet_model.set('total', data.total);
                    });

				}
			});

			this.summary_bar = new SummaryBarView({
				model: model,
				el: $(".filters-editor .summary-bar", this.el)
			});
		},

        expandContractTab: function(opts){
            var _this = this;
            var expand = opts.expand;
            var $tc = opts.tab_container;
            var $table = opts.table;
            var dim = opts.dimension;


            // Calculate how much to change dimension.
            var delta = parseInt($tc.css('max' + _s.capitalize(dim)), 10) - parseInt($tc.css('min' + _s.capitalize(dim)), 10);
            if (! expand){
                delta = -1 * delta;
            }

            // Animate field container dimension.
            $tc.addClass('changing');

            // Toggle button text
            var button_text = ($('button.toggle', $tc).html() == '\u25B2') ? '\u25BC' : '\u25B2';
            $('button.toggle', $tc).html(button_text);

            // Execute the animation.
            var tc_dim_opts = {};
            tc_dim_opts[dim] = parseInt($tc.css(dim),10) + delta;
            $tc.animate(
                    tc_dim_opts,
                    {
                        complete: function(){
                            $tc.removeClass('changing');

                            if (expand){
                                $tc.addClass('expanded')
                            }
                            else{
                                $tc.removeClass('expanded');
                                Util.util.fillParent($table);
                            }
                        }
                    }
                    );

            // Animate cell dimension.
            $tc.parent().animate(tc_dim_opts);

            // Animate table dimension.
            var table_dim_opts = {};
            table_dim_opts[dim] = parseInt($table.css(dim),10) + delta;
            $table.animate(table_dim_opts);
        },

        toggleFiltersEditor: function(){
            var $filtersEditor = $('.filters-editor-container', this.el);
            var $table = $('.filters-editor-table', this.el);
            if (! $filtersEditor.hasClass('changing')){
                this.expandContractTab({
                    expand: ! $filtersEditor.hasClass('expanded'),
                    tab_container: $filtersEditor,
                    table: $table,
                    dimension: 'width'
                });
            }
        },

        resize: function(){
            this.resizeFiltersEditor();
        },

        resizeFiltersEditor: function(){
            var $table = $('.filters-editor-table', this.el);
            Util.util.fillParent($table);
            this.resizeVerticalTab($('.filters-editor-tab', this.el)); 
            var $sbc = $('.filters-editor-table .summary-bar-container');
            $sbc.parent().css('height', $sbc.height());
        },

		resizeVerticalTab: function($vt){
			var $rc = $('.rotate-container', $vt);
			$rc.css('width', $rc.parent().height());
			$rc.css('height', $rc.parent().width());
		},

		setUpInitialState: function(){
			var initial_state = GeoRefine.config.initial_state;

            // Initialize facet quantity field.
            var initial_qfield_id = initial_state.facet_quantity_field;
            if (initial_qfield_id){
                var qfield = this.facet_quantity_fields.get(initial_qfield_id);
                this.filters_qfield_select.model.set('selection', qfield.cid);
            }

            // Initialize facets.
            if (initial_state.facets){
            }

            // Connect the facets to events.




			// Initialize Data Views.
            
            // Get the number of data views we can put per row in the data view container.
            var views_per_row = Math.floor($('.data-views', this.el).width()/this.data_view_defaults.width);
            var row = -1;
            var column = 0;
			_.each(initial_state.data_views, function(data_view, i){


                // TESTING!
                if (i != i){
                    return;
                }

                // Get the position for each view.
                if (column == 0){
                    row += 1;
                }
                var pos = {
                    x: column * (this.data_view_defaults.width + 15),
                    y: row * (this.data_view_defaults.height + 15)
                };

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
					this.createDataViewWindow(map_editor, _.extend({"title": "Map"}, pos));
				}

				// Handle chart data views.
				else if (data_view.type == 'chart'){
					var chart_editor = this.createChartEditor();

					_.each(["category", "quantity"], function(field_type){

						var field_attr = _s.sprintf("initial_%s_field", field_type);

						if (data_view.hasOwnProperty(field_attr)){
							var fields = chart_editor.model.get('datasource').get('schema').get(field_type + "_fields");
							var field = fields.get(data_view[field_attr].id);

							chart_editor[_s.sprintf("%s_field_selector", field_type)].model.set(_s.sprintf("selected_field", field_type), field);

						}
					}, this);

					this.createDataViewWindow(chart_editor, _.extend({"title": "Chart"}, pos));
				}

                column = (column + 1) % views_per_row;

			}, this);
			
		},

        loadState: function(state){
            var state = {
                actionQueue: {
                    async: true,
                    actions: [
                        {
                            type: 'actionQueue',
                            async: false,
                            actions: [
                                // Facets.
                                {
                                    type: 'actionQueue',
                                    async: false,
                                    actions: [
                                        // Substrates facet.
                                        {
                                            type: 'actionQueue',
                                            async: false,
                                            actions: [
                                                // Create facet.
                                                {
                                                    type: 'action',
                                                    handler: 'facetsCreateFacet',
                                                    opts: {
                                                        fromDefinition: true,
                                                        id: 'substrates'
                                                    }
                                                },
                                                // Load data.
                                                {
                                                    type: 'action',
                                                    handler: 'facetsGetData',
                                                    opts: {
                                                        id: 'substrates'
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                            ]
                        }
                    ]
                }
            };
            var loadStateAction = GeoRefineViewsUtil.stateUtil.processActionQueue(state.actionQueue);            
            var dfd = loadStateAction();
            dfd.done(function(){console.log("all done")});
        },


    });

	return GeoRefineClientView;

});

