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
	"text!./templates/GeoRefineClient.html"
		],
function($, Backbone, _, ui, _s, Facets, MapView, Charts, Windows, Util, template){

    var requests_endpoint = _s.sprintf('%s/projects/execute_requests/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);

	var GeoRefineClientView = Backbone.View.extend({

		events: {
			'click .filters-editor-container .title': 'toggleFiltersEditor',
			"click .add-map-button": "addMapView",
			"click .add-chart-button": "addChartView"
		},

		initialize: function(){
			$(this.el).addClass('georefine-client');

            this.data_view_counter = 0;

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
				_this.setUpFacets();
                _this.setUpSummaryBar();
                _this.setUpFiltersEditor();
				_this.setUpInitialState();
                _this.resize();
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
            var $select = $('<select></select>');
            _.each(this.facet_quantity_fields.models, function(model){
                var $option = $(_s.sprintf('<option value="%s">%s</option>', model.cid, model.get('label')));
                $option.appendTo($select);
            }, this);
            $select.appendTo('.filters-editor .quantity-field', this.el);

            // When the quantity field selector changes, update the facets and summary bar.
            var _this = this;
            $select.on('change', function(){
                var val = $select.val();
                var selected_field = _this.facet_quantity_fields.getByCid(val);
                _.each(_this.facets.models, function(facet){
                    facet.set('quantity_field', selected_field);
                }, _this);

                _this.summary_bar.model.set('quantity_field', selected_field);
            });
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

			var w =  new Windows.views.WindowView({
				model: new Backbone.Model(_.extend({}, {
					"inline-block": true,
					"width": 500,
					"height": 500,
					"x": dv_offset.left + (this.data_view_counter % 5) * 20,
					"y": dv_offset.top + (this.data_view_counter % 5) * 20,
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

        // Extend a query by merging in other queries.
        // Note: this modifies the target query in-place.
        extendQuery: function(target_q){
            var array_params = ['SELECT','FROM', 'WHERE', 'GROUP_BY', 'ORDER_BY'];
            var boolean_params =['SELECT_GROUP_BY'];

            _.each(Array.prototype.slice.call(arguments, 1), function(source_q) {
                _.each(array_params, function(param){
                    if (target_q.hasOwnProperty(param)){
                        _.each(source_q[param], function(source_q_value){
                            if (target_q[param].indexOf(source_q_value) != -1){
                                target_q[param].push(source_q_value);
                            }
                        });
                    }
                    else{
                        if (source_q.hasOwnProperty(param)){
                            target_q[param] = JSON.parse(JSON.stringify(source_q[param]));
                        }
                    }
                });

                _.each(boolean_params, function(param){
                    if (source_q.hasOwnProperty(param)){
                        target_q[param] = source_q[param];
                    }
                });
            });

            return target_q;
        },

        // Add a model's filters to a query.
        addFiltersToQuery: function(model, filter_attrs, q){
            if (! (q['WHERE'] instanceof Array)){
                q['WHERE'] = [];
            }

            _.each(filter_attrs, function(filter_attr){
                filters = model.get(filter_attr);
                filter_array = this._filterObjectGroupsToArray(filters);
                _.each(filter_array, function(f){
                    q['WHERE'].push(f);
                }, this);
            }, this)
        },

        makeKeyedInnerQuery: function(model, key, filter_attrs){
            // Set include filters to primary and base by default.
            filter_attrs = filter_attrs || ['primary_filters', 'base_filters'];

            // Shortcuts.
            var qfield  = model.get('quantity_field');

            // Initialize query definition.
            // Note: 'ID' must be 'inner' to conform to conventions.
            var inner_q = {
                'ID': 'inner',
                'SELECT_GROUP_BY': true,
            };

            // Merge the quantity field's inner query parameters.
            this.extendQuery(inner_q, qfield.get('inner_query'));

            // Add the facet's filters.
            this.addFiltersToQuery(model, filter_attrs, inner_q);

            // Add the facet's key entities as group_by paramters.
            inner_q['GROUP_BY'].push(key['KEY_ENTITY']);
            if (key['LABEL_ENTITY']){
                inner_q['GROUP_BY'].push(key['LABEL_ENTITY']);
            }

            return inner_q;
        },

        makeKeyedOuterQuery: function(model, key, inner_query, query_id){

            // Shortcuts.
            var qfield  = model.get('quantity_field');

            // Initialize the outer query.
            var outer_q = {
                'ID': query_id || 'outer',
                'FROM': [{'ID': 'inner', 'TABLE': inner_query}],
                'SELECT_GROUP_BY': true,
                'GROUP_BY': []
            };

            // Add the quantity field's outer query parameters.
            this.extendQuery(outer_q, qfield.get('outer_query'));

            // Add key entities as group_by paramters.
            var gb_attrs = ['KEY_ENTITY'];
            if (key['LABEL_ENTITY']){
                gb_attrs.push('LABEL_ENTITY');
            }
            _.each(gb_attrs, function(gb_attr){
                outer_q['GROUP_BY'].push({
                    'ID': key[gb_attr]['ID'],
                    'EXPRESSION': _s.sprintf("{{inner.%s}}", key[gb_attr]['ID'])
                });
            });

            return outer_q;
        },

        makeKeyedQueryRequest: function(model, key, filter_attrs){
            // This function assembles two sets of queries:
            // The inner query selects a data set, and optionally groups it.
            // That query uses the filters.
            // In some cases we will make separate queries for base filters, and for primary filters.
            // The outer query does a secondary grouping and aggregation.
            // This allows us to do things like:
            // 'select sum(dataset.xy) group by dataset.category from
            // (select data.x * data.y where data.x > 7 group by data.category) as dataset

            // Shortcuts.
            var qfield  = model.get('quantity_field');

            // Get the inner query.
            var inner_q = this.makeKeyedInnerQuery(model, key, filter_attrs);

            // Get the outer query.
            var outer_q = this.makeKeyedOuterQuery(model, key, inner_q, 'outer');

            // Assemble the keyed result parameters.
            var keyed_results_parameters = {
                "KEY": key,
                "QUERIES": [outer_q]
            };

            // Assemble keyed query request.
            keyed_query_request = {
                'ID': 'keyed_results',
                'REQUEST': 'execute_keyed_queries',
                'PARAMETERS': keyed_results_parameters
            };

            return keyed_query_request;
        },

		setUpFacets: function(){
			var facets = {};
			var lji = new Util.util.LumberjackInterpreter();

            var _app = this;

			// The 'getData' functions will be called with a facet model as 'this'.
			var listFacetGetData = function(){
                var _this = this;
                var qfield = this.get('quantity_field');

                // Copy the key entity.
                var key = JSON.parse(JSON.stringify(_this.get('KEY')));

                // Assemble request.
                var keyed_query_req = _app.makeKeyedQueryRequest(_this, key);
                var requests = [];
                requests.push(keyed_query_req);

                // Execute the requests.
				$.ajax({
					url: requests_endpoint,
					type: 'POST',
					data: {'requests': JSON.stringify(requests)},
					error: Backbone.wrapError(function(){}, _this, {}),
					success: function(data, status, xhr){
                        var results = data.results;
                        var count_entity = qfield.get('outer_query')['SELECT'][0];

						// Generate choices from data.
						var choices = [];
						_.each(results['keyed_results'], function(result){
                            value = result['data']['outer'][count_entity['ID']];
							choices.push({
								id: result['key'],
								label: result['label'],
								count: value,
                                count_label: _s.sprintf(qfield.get('format') || '%s', value)
							});
						});
						_this.set('choices', choices);
					}
				});
			};

			numericFacetGetData = function() {
                var facet_model = this;

                // Copy the key entity.
                var key = JSON.parse(JSON.stringify(facet_model.get('KEY')));

                // Shortcuts.
                var qfield  = facet_model.get('quantity_field');
                if (! qfield){
                    return;
                }

                // Set base filters on key entity context.
                if (! key['KEY_ENTITY']['CONTEXT']){
                    key['KEY_ENTITY']['CONTEXT'] = {};
                }
                var key_context = key['KEY_ENTITY']['CONTEXT'];

                _app.addFiltersToQuery(facet_model, ['base_filters'], key_context);

                // Get the base query.
                var base_inner_q = _app.makeKeyedInnerQuery(facet_model, key, ['base_filters']);
                var base_outer_q = _app.makeKeyedOuterQuery(facet_model, key, base_inner_q, 'base');

                // Get the primary query.
                var primary_inner_q = _app.makeKeyedInnerQuery(facet_model, key, ['base_filters', 'primary_filters']);
                var primary_outer_q = _app.makeKeyedOuterQuery(facet_model, key, primary_inner_q, 'primary');

                // Assemble the keyed result parameters.
                var keyed_results_parameters = {
                    "KEY": key,
                    "QUERIES": [base_outer_q, primary_outer_q]
                };

                // Assemble keyed query request.
                var keyed_query_request = {
                    'ID': 'keyed_results',
                    'REQUEST': 'execute_keyed_queries',
                    'PARAMETERS': keyed_results_parameters
                };

                var _this = this;

                // Assemble request.
                var requests = [];
                requests.push(keyed_query_request);

                // Execute the requests.
				$.ajax({
					url: requests_endpoint,
					type: 'POST',
					data: {'requests': JSON.stringify(requests)},
					error: Backbone.wrapError(function(){}, _this, {}),
					success: function(data, status, xhr){

                        var results = data.results;
                        var count_entity = qfield.get('outer_query')['SELECT'][0];

						// Parse data into histograms.
						var base_histogram = [];
						var primary_histogram = [];

						// Generate stats and choices from data.
                        var range_min = null;
                        var range_max = null;
						var choices = [];
						_.each(results['keyed_results'], function(result){
							bucket_label = result['label'];
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

                            if (! range_min <= bmin){
                                range_min = bmin;
                            }

                            if (! range_max >= bmax){
                               range_max = bmax; 
                            }

                            if (result['data']['base']){
                                var base_bucket = {
                                    bucket: bucket_label,
                                    min: bmin,
                                    max: bmax,
                                    count: result['data']['base'][count_entity['ID']]
                                };
                                base_histogram.push(base_bucket);

                                // Get primary count (if present).
                                var primary_count = 0.0;
                                if (result['data'].hasOwnProperty('primary')){
                                    var primary_count = result['data']['primary'][count_entity['ID']];
                                }
                                var primary_bucket = _.extend({}, base_bucket, {
                                    count: primary_count
                                });
                                primary_histogram.push(primary_bucket);
                            }
						});

						base_histogram = _.sortBy(base_histogram, function(b){return b.count});
						primary_histogram = _.sortBy(primary_histogram, function(b){return b.count;});

						_this.set({
                            base_histogram: base_histogram,
                            filtered_histogram: primary_histogram,
                            range_min: range_min,
                            range_max: range_max
						});
					}
				});
			};

            timeSliderFacetGetData = function(){
				var _this = this;

                var qfield = this.get('quantity_field');

                // Copy the key entity.
                var key = JSON.parse(JSON.stringify(_this.get('KEY')));

                // Assemble request.
                var keyed_query_req = _app.makeKeyedQueryRequest(_this, key);
                var requests = [];
                requests.push(keyed_query_req);

				$.ajax({
					url: requests_endpoint,
					type: 'POST',
					data: {'requests': JSON.stringify(requests)},
					error: Backbone.wrapError(function(){}, _this, {}),
					success: function(data, status, xhr){

                        var results = data.results;
                        var count_entity = qfield.get('outer_query')['SELECT'][0];

						// Generate choices from data.
                        var choices = [];
						_.each(results['keyed_results'], function(result){
                            value = result['data']['outer'][count_entity['ID']];
                            choices.push({
                                'id': result['key'],
                                'label': result['label'],
                                'value': value
                            });
                        }, _this);

                        // Sort choices.
                        choices = _.sortBy(choices, function(choice){
                            return choice['label'];
                        });

						_this.set('choices', choices);
					}
				});
            };

            // The 'formatFilter' functions will be called with a facet view as 'this'.
            listFacetFormatFilters = function(selected_values){
                var formatted_filters = [];
                if (selected_values.length > 0){
                    formatted_filters = [
                        [this.model.get('filter_entity'), 'in', selected_values]
                        ];
                }
                return formatted_filters;
            };

            numericFacetFormatFilters = function(selected_values){
                var formatted_filters = [
                    [this.model.get('filter_entity'), '>=', selected_values['selection_min']],
                    [this.model.get('filter_entity'), '<=', selected_values['selection_max']],
                ];
                return formatted_filters;
            };

            timeSliderFacetFormatFilters = function(selected_value){
                var formatted_filters = [
                    [this.model.get('filter_entity'), '==', selected_value]
                    ];
                return formatted_filters;
            };

			// For each facet definition...
			_.each(GeoRefine.config.facets.facets, function(facet){

				var model, view;

				if (facet.type == 'list'){
					model = new Facets.models.FacetModel(_.extend({
                        primary_filters: {},
                        base_filters: {}
                    }, facet, {
						choices: []
					}));
					model.getData = listFacetGetData;
					view = new Facets.views.ListFacetView({ model: model });

                    // This function will be called with the view as 'this'.
                    view.formatChoiceCountLabels = function(choices){
                        var labels = [];
                        var count_entity = this.model.get('count_entity');
                        _.each(choices, function(choice){
                            var label = "";
                            if (count_entity && count_entity.format){
                                label = _s.sprintf(count_entity.format, choice['count']);
                            }
                            else{
                                label = choice['count'];
                            }
                            labels.push(label);
                        });
                        return labels;
                    };

                    view.formatFilters = listFacetFormatFilters;
				}

				else if (facet.type == 'numeric'){
					model = new Facets.models.FacetModel(_.extend({}, facet, {
						filtered_histogram: [],
						base_histogram: [],
					}));
					model.getData = numericFacetGetData;
					view = new Facets.views.NumericFacetView({ model: model });
                    view.formatFilters = numericFacetFormatFilters;

				}

				else if (facet.type == 'time-slider'){
					model = new Facets.models.FacetModel(_.extend({}, facet, {
					}));
					model.getData = timeSliderFacetGetData;
					view = new Facets.views.TimeSliderFacetView({ model: model });
                    view.formatFilters = timeSliderFacetFormatFilters;
                }
                
                // Setup the facet's primary filter group config.
                _.each(facet.primary_filter_groups, function(filter_group_id, key){
                    var filter_group = this.filter_groups[filter_group_id];
                    filter_group.add(model);

                    // When the filter group changes, change the facet's primary filters.
                    filter_group.on('change:filters', function(){
                        var primary_filters = _.clone(model.get('primary_filters')) || {} ;
                        // A facet should not use its own selection in the filters.
                        primary_filters[filter_group_id] = _.filter(filter_group.getFilters(), function(filterObj){
                            return (filterObj.source.cid != model.cid);
                        });
                        model.set('primary_filters', primary_filters);
                    });

                    // Initialize primary filters.
                    var primary_filters = _.clone(model.get('primary_filters')) || {} ;
                    primary_filters[filter_group_id] = _.filter(filter_group.getFilters(), function(filterObj){
                        return (filterObj.source.cid != model.cid);
                    });
                    model.set('primary_filters', primary_filters);

                }, this);

                // Setup the facet's base filter group config.
                _.each(facet.base_filter_groups, function(filter_group_id, key){
                    var filter_group = this.filter_groups[filter_group_id];
                    filter_group.on('change:filters', function(){
                        var base_filters = _.clone(model.get('base_filters')) || {};
                        base_filters[filter_group_id] = filter_group.getFilters();
                        model.set('base_filters', base_filters);
                    });

                    // Initialize base filters.
                    var base_filters = _.clone(model.get('base_filters')) || {};
                    base_filters[filter_group_id] = filter_group.getFilters();
                    model.set('base_filters', base_filters);

                }, this);

                // Have the facet update when its query or base filters or count entities change.
                if (model.getData){

                    // helper function to get a timeout getData function.
                    var _timeoutGetData = function(){
                        var delay = 500;
                        return setTimeout(function(){
                            //console.log("getData", model.id, arguments);
                            model.getData();
                            model.set('_fetch_timeout', null);
                        }, delay);
                    };

                    model.on('change:primary_filters change:base_filters change:quantity_field', function(){
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

            this.facets = facet_collection_model;
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

                // Convert to url params.
                var url_params = [_s.sprintf('PARAMS=%s', JSON.stringify(params))];

                // Generate url by appending url params to map endpoint.
                var service_url = map_endpoint + '?' + url_params.join('&') + '&';
                
                model.set('service_url', service_url);
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
			var charts_config = GeoRefine.config.charts;

			// Generate models from fields.
			var processed_fields = {};
			_.each(['category', 'quantity'], function(field_type){
				var fields = charts_config[_s.sprintf('%s_fields', field_type)] || [];
				var field_models = [];
				_.each(fields, function(field){
                    var entity_model = null;
                    if (field_type == 'category'){
					    entity_model = new Backbone.Model(field['KEY']['KEY_ENTITY']);
                    }
                    else if (field_type =='quantity'){
                        var quantity_entity = field['outer_query']['SELECT'][0];
					    entity_model = new Backbone.Model(quantity_entity);
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
                console.log("datasource getData", arguments);

                var cfield = q.get('category_field');
                var qfield = q.get('quantity_field');

                if (! cfield || ! qfield){
                    return;
                }

                // Copy the key entity.
                var key = JSON.parse(JSON.stringify(cfield.get('KEY')));

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
                            if (result['data']['base']){

                                var base_value = result['data']['base'][count_entity['ID']];
                                var primary_value = 0;
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

                                chart_data.push(chart_datum);
                            }
                        });

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
                    $(this.el).html('<span class="text">Currently selected: <span class="data"></span></span>');
                    // Trigger update when model data changes.
					this.model.on('change:data', this.onDataChange, this);

                    // Get data when parameters change.
                    if (this.model.getData){

                        // helper function to get a timeout getData function.
                        var _timeoutGetData = function(){
                            var delay = 500;
                            return setTimeout(function(){
                                //console.log("getData", model.id, arguments);
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

					var formatted_selected = _s.sprintf(format, data.selected);
					var formatted_total = _s.sprintf(format, data.total);
					var percentage = 100.0 * data.selected/data.total;
					$(".data", this.el).html(_s.sprintf('<span class="selected">%s</span> <span class="percentage">(%.1f%% of %s total)</span>', formatted_selected, percentage, formatted_total));

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

		setUpInitialState: function(){
			var initial_state = GeoRefine.config.initial_state;

            // Initialize facets.
            if (initial_state.facets){
                var initial_qfield_id = initial_state.facets.initial_quantity_field_id;
                if (initial_qfield_id){
                    var $qfield_select = $('.filters-editor .quantity-field select', this.el);
                    var qfield = this.facet_quantity_fields.get(initial_qfield_id);
                    $qfield_select.val(qfield.cid).change();
                }
            }

			// Initialize Data Views.
			_.each(initial_state.data_views, function(data_view, i){

                // TESTING!
                if (i != -1){
                    return;
                }

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

							chart_editor[_s.sprintf("%s_field_selector", field_type)].model.set(_s.sprintf("selected_field", field_type), field);

						}
					}, this);

					this.createDataViewWindow(chart_editor, {
						"title": "Chart"
					});
				}


			}, this);
			
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
                                /*
                                _this.resize();
                                _this.resizeStop();
                                */
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
            this.resizeVerticalTab($('.filters-editor-tab', this.el)); 
        },

		resizeVerticalTab: function($vt){
			var $rc = $('.rotate-container', $vt);
			$rc.css('width', $rc.parent().height());
			$rc.css('height', $rc.parent().width());
		},

    });

	return GeoRefineClientView;

});

