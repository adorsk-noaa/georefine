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



	var GeoRefineClientView = Backbone.View.extend({

		events: {
			'click .facets-editor-container .title': 'toggleFiltersEditor',
			"click .add-map-button": "addMapView",
			"click .add-chart-button": "addChartView"
		},

		initialize: function(){
            // Save app to global namespace.
            GeoRefine.app = {
                model: this.model,
                view: this,
                id: this.cid,
                facets: {
                    definitions: GeoRefine.config.facets.definitions,
                    registry: {}
                },
                summaryBar: {}
            };

            // Set endpoints.
            GeoRefine.app.requestsEndpoint = _s.sprintf('%s/projects/execute_requests/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);
            GeoRefine.app.keyedStringsEndpoint = _s.sprintf('%s/ks/getKey/', GeoRefine.config.context_root);

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
				_this.setUpFilterGroups();
				GeoRefineViewsUtil.facetsUtil.setUpFacetCollection();
				GeoRefineViewsUtil.facetsUtil.setUpFacetsEditor();
                _this.loadState();
                /*
				_this.setUpWindows();
                _this.setUpSummaryBar();
				_this.setUpInitialState();
                _this.resize();
                */
			});

			return this;
		},

		onReady: function(){
		},

        setUpFilterGroups: function(){
            var filterGroups = {};

            // Initialize filter groups.
			_.each(GeoRefine.config.filter_groups, function(groupConfig){
                var filterGroup = new Backbone.Collection();
                filterGroups[groupConfig.id] = filterGroup;
                filterGroup.getFilters = function(){
                    var filters = [];
                    _.each(filterGroup.models, function(model){
                        var modelFilters = model.get('filters');
                        if (modelFilters){
                            filters.push({
                                'source': {
                                    'type': model.getFilterType ? model.getFilterType() : null,
                                    'cid': model.cid
                                },
                                'filters': modelFilters
                            });
                        }
                    });
                    return filters;
                };
            });

            // Add listeners for synchronizing linked groups.
			_.each(GeoRefine.config.filter_groups, function(groupConfig){
                _.each(groupConfig.linked_groups, function(linkedGroupId){
                    var mainGroup = filterGroups[groupConfig.id];
                    var linkedGroup = filterGroups[linkedGroupId];
                    _.each(['add', 'remove'], function(evnt){
                        linkedGroup.on(evnt, function(model){
                            mainGroup[evnt](model)
                        });
                    });
                });
            });

            // Save to global namespaced variable.
            GeoRefine.app.filterGroups = filterGroups;
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
					url: GeoRefine.app.keyedStringsEndpoint,
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
					url: GeoRefine.app.requestsEndpoint,
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
            var $filtersEditor = $('.facets-editor-container', this.el);
            var $table = $('.facets-editor-table', this.el);
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
            var $table = $('.facets-editor-table', this.el);
            Util.util.fillParent($table);
            this.resizeVerticalTab($('.facets-editor-tab', this.el)); 
            var $sbc = $('.facets-editor-table .summary-bar-container');
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

            // Shortcut.
            var stateUtil = GeoRefineViewsUtil.stateUtil;

            var actionQueue = {
                async: false,
                actions: [
                    // Setup quantity field.
                    {
                        type: 'action',
                        handler: 'facetsFacetsEditorSetQField',
                        opts: {
                            id: 'result.x:sum'
                        }
                    },

                    // Setup timestep facet.
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
                                    id: 'timestep'
                                }
                            },
                            // Initialize facet.
                            {
                                type: 'action',
                                handler: 'facetsInitializeFacet',
                                opts: {
                                    id: 'timestep'
                                }
                            },
                            // Connect facet.
                            {
                                type: 'action',
                                handler: 'facetsConnectFacet',
                                opts: {
                                    id: 'timestep'
                                }
                            },
                            // Load data.
                            {
                                type: 'action',
                                handler: 'facetsGetData',
                                opts: {
                                    id: 'timestep'
                                }
                            },
                            // Select first choice.
                            {
                                type: 'action',
                                handler: 'facetsSetSelection',
                                opts: {
                                    id: 'timestep',
                                    index: 1
                                }
                            },

                        ]
                    },

                    // Setup summary bar.
                    {
                        type: 'actionQueue',
                        async: false,
                        actions: [
                            // Initialize summary bar.
                            {
                                type: 'action',
                                handler: 'summaryBarInitialize',
                            },

                            // Connect summary bar.
                            {
                                type: 'action',
                                handler: 'summaryBarConnect',
                            },
                            // Get data for summary bar.
                            {
                                type: 'action',
                                handler: 'summaryBarGetData',
                            },
                        ]
                    },

                    // Setup substrate facets.
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
                            // Initialize facet.
                            {
                                type: 'action',
                                handler: 'facetsInitializeFacet',
                                opts: {
                                    id: 'substrates'
                                }
                            },
                            // Connect facet.
                            {
                                type: 'action',
                                handler: 'facetsConnectFacet',
                                opts: {
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
            };
            var action = stateUtil.processActionQueue(actionQueue);
            var deferred = action();

            // Load after quantity field state is set up.
            $.when(deferred).then(function(){
                console.log("All Done.");
            });
        },


    });

	return GeoRefineClientView;

});

