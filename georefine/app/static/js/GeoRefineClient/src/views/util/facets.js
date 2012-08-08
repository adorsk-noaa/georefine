define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Facets",
	"Util",
	"./summaryBar",
	"./requests",
	"./filters",
	"./functions",
	"./format",
	"./serialization",
		],
function($, Backbone, _, _s, Facets, Util, summaryBarUtil, requestsUtil, filtersUtil, functionsUtil, formatUtil, serializationUtil){

    var setUpFacetsEditor = function(){

        // Get facets editor model from state, or create a new model. 
        var facetsEditorModel = GeoRefine.app.state.facetsEditor || new Backbone.Model();

        // Create facets editor view.
        var facetsEditorView = new Facets.views.FacetsEditorView({
            el: $('.facets-editor', GeoRefine.app.view.el),
            model: facetsEditorModel,
        });

        // Add references to the the facetsEditor and summaryBar in the app variable.
        GeoRefine.app.facetsEditor = facetsEditorView;

        GeoRefine.app.summaryBar = facetsEditorView.subViews.summaryBar;

        // Decorate summary bar.
        summaryBarUtil.decorateSummaryBar();

        // Setup initial facets.
        _.each(['primary', 'base'], function(facetCategory){
            var facetCollectionView = facetsEditorView.subViews[facetCategory + "_facets"];
            if (facetCollectionView){
                // Decorate and connect any initial facets.
                _.each(facetCollectionView.registry, function(facetView, id){
                    decorateFacet(facetView);
                    connectFacet(facetView);
                });

                // Decorate and connect newly added facets.
                facetCollectionView.on('addFacetView', function(view){
                    decorateFacet(view);
                    connectFacet(view);
                });

                // Disconnect facets when removed.
                facetCollectionView.off('removeFacetView', function(view){
                    disconnectFacet(view)
                });

            }
        });

        // Initialize w/ getData calls???
        // @TODO: later, for the case of when
        // data in the db would be dynamic.


    };

    // Define functions for decorating facets.
    var facetDecorators = {};

    // Numeric facet decorator.
    facetDecorators['numeric'] = function(numericFacet){

        var model = numericFacet.model;

        // Define getData function for model.
        model.getData = function(opts){
            // 'this' is a numeric facet model.
            var _this = this;
            var opts = opts || {updateRange: false};

            // Shortcuts.
            var qfield  = _this.get('quantity_field');
            if (! qfield){
                return;
            }

            // Copy the key entity.
            var key = JSON.parse(JSON.stringify(_this.get('KEY')));

            // Set base filters on key entity context.
            if (! key['KEY_ENTITY']['CONTEXT']){
                key['KEY_ENTITY']['CONTEXT'] = {};
            }
            var key_context = key['KEY_ENTITY']['CONTEXT'];

            requestsUtil.addFiltersToQuery(_this, ['base_filters'], key_context);

            // Get the base query.
            var base_inner_q = requestsUtil.makeKeyedInnerQuery(_this, key, ['base_filters']);
            var base_outer_q = requestsUtil.makeKeyedOuterQuery(_this, key, base_inner_q, 'base');

            // Get the primary query.
            var primary_inner_q = requestsUtil.makeKeyedInnerQuery(_this, key, ['base_filters', 'primary_filters']);
            var primary_outer_q = requestsUtil.makeKeyedOuterQuery(_this, key, primary_inner_q, 'primary');

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

            // Assemble request.
            var requests = [keyed_query_request];

            // Start the request and save the deferred object.
            var deferred = $.ajax({
                url: GeoRefine.app.requestsEndpoint,
                type: 'POST',
                data: {
                    'requests': JSON.stringify(requests)
                },
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
                        var bucketLabel = result['label'];
                        var bminmax = functionsUtil.parseBucketLabelMax(bucketLabel);

                        if (bminmax.min < range_min || range_min == null){
                            range_min = bminmax.min;
                        }

                        if (bminmax.max > range_max || range_max == null){
                           range_max = bminmax.max; 
                        }

                        if (result['data']['base']){
                            var base_bucket = {
                                bucket: bucket_label,
                                min: bminmax.min,
                                max: bminmax.max,
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
                    });

                    if (opts.updateRange){
                        _this.get('range').set({
                            min: range_min,
                            max: range_max
                        });
                    }

                }
            });

            return deferred;
        };


        // Define the formatFilters function for facet.
        numericFacet.formatFilters = function(selection){
            // 'this' is a numeric facet view.
            var filter_entity = this.model.get('filter_entity');
            var formatted_filters = [];
            _.each(['min', 'max'], function(minmax){
                var val = parseFloat(selection[minmax]);
                if (! isNaN(val)){
                    var op = (minmax == 'min') ? '>=' : '<=';
                    formatted_filters.push([filter_entity, op, val]);
                }
            });
            return formatted_filters;
        };

        // Define formatter for the view.
        numericFacet.formatter = function(format, value){
            return formatUtil.GeoRefineFormatter(format, value);
        };
        
    };

    // Time slider facet decorator.
    facetDecorators['timeSlider'] = function(timeSliderFacet){

        // Shortcut to the model.
        var model = timeSliderFacet.model;

        // Define getData function for model.
        model.getData = function(){
            // 'this' is a timeSliderFacet model.
            var _this = this;
            
            // Shorcut.
            var qfield = _this.get('quantity_field');

            // Copy the key entity.
            var key = JSON.parse(JSON.stringify(_this.get('KEY')));

            // Assemble request.
            var keyed_query_req = requestsUtil.makeKeyedQueryRequest(_this, key);
            var requests = [keyed_query_req];

            // Start request and save the deferred object.
            var deferred = $.ajax({
                url: GeoRefine.app.requestsEndpoint,
                type: 'POST',
                data: {
                    'requests': JSON.stringify(requests)
                },
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

            return deferred;
        };

        // Define formatFilters function for the view.
        timeSliderFacet.formatFilters = function(selection){
            var _this = this;
            var formatted_filters = [
                [_this.model.get('filter_entity'), '==', selection]
                ];
            return formatted_filters;
        };
    };

    // List facet decorator.
    facetDecorators['list'] = function(listFacet){

        // Shortcut to model.
        var model = listFacet.model;

        // Define getData function for model.
        model.getData = function(){
            // 'this' is a list facet model.
            var _this = this;
            var qfield = this.get('quantity_field');
            if (! qfield){
                return;
            }

            // Copy the key entity.
            var key = JSON.parse(JSON.stringify(_this.get('KEY')));

            // Assemble request.
            var keyed_query_req = requestsUtil.makeKeyedQueryRequest(_this, key);
            var requests = [];
            requests.push(keyed_query_req);

            // Execute requests and save the deferred object.
            var deferred = $.ajax({
                url: GeoRefine.app.requestsEndpoint,
                type: 'POST',
                data: {
                    'requests': JSON.stringify(requests)
                },
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
                            count_label: formatUtil.GeoRefineFormatter(qfield.get('format') || '%s', value)
                        });
                    });
                    _this.set('choices', choices);
                }
            });

            return deferred;
        };

        // Define the formatFilters function for the view.
        listFacet.formatFilters = function(selection){
            // 'this' is a listFacetView.
            var formatted_filters = [];
            if (selection.length > 0){
                formatted_filters = [
                    [this.model.get('filter_entity'), 'in', selection]
                ];
            }
            return formatted_filters;
        };

        // Define formatChoiceCountLabels function for the view.
        listFacet.formatChoiceCountLabels = function(choices){
            // 'this' is a listFacetView.
            var labels = [];
            var count_entity = this.model.get('count_entity');
            _.each(choices, function(choice){
                var label = "";
                if (count_entity && count_entity.format){
                    label = formatUtil.GeoRefineFormatter(count_entity.format || '%s', choice['count']);
                }
                else{
                    label = choice['count'];
                }
                labels.push(label);
            });
            return labels;
        };
    };


    // Decorate a facet.
    // This is a dispatcher for type-specific decorators.
    var decorateFacet = function(facet){

        var decorator = facetDecorators[facet.model.get('type')];
        if (decorator){
            decorator(facet);
        }
    };

    var updateFacetModelPrimaryFilters = function(facetModel, opts){
        var primaryFilters = _.clone(facetModel.get('primary_filters')) || {} ;
        _.each(facetModel.get('primary_filter_groups'), function(filterGroupId, key){
            var filterGroup = GeoRefine.app.filterGroups[filterGroupId];
            // A facet should not use its own selection in the filters.
            primaryFilters[filterGroupId] = _.filter(filterGroup.getFilters(),
                function(filterObj){
                    return (filterObj.source.cid != facetModel.cid);
                });
        });
        facetModel.set({'primary_filters': primaryFilters}, opts);
    };

    // Setup event chains for a facet.
    var connectFacet = function(facetView, opts){

        // Setup the facet's primary filter groups.
        _.each(facetView.model.get('primary_filter_groups'), function(filterGroupId, key){
            var filterGroup = GeoRefine.app.filterGroups[filterGroupId];
            filterGroup.add(facetView.model);
            filterGroup.on('change:filters', function(){
                updateFacetModelPrimaryFilters(this);
            }, facetView.model);
            // Remove callback when model is removed.
            facetView.model.on('remove', function(){
                filterGroup.off(null, null, this);
            }, facetView.model);
        });

        // Setup the facet's base filter group config.
        _.each(facetView.model.get('base_filter_groups'), function(filterGroupId, key){
            var filterGroup = GeoRefine.app.filterGroups[filterGroupId];
            filterGroup.on('change:filters', function(){
                filtersUtil.updateModelFilters(this, 'base');
            }, facetView.model);
            // Remove callback when model is removed.
            facetView.model.on('remove', function(){
                filterGroup.off(null, null, this);
            }, facetView.model);
        });

        // Listen for quantity field changes.
        var qFieldSelect = GeoRefine.app.facetsEditor.qFieldSelect;
        qFieldSelect.model.on('change:selection', function(){
            var fieldCid = qFieldSelect.model.get('selection');
            var selectedField = GeoRefine.app.facetsEditor.model.get('quantity_fields').getByCid(fieldCid);
            this.set('quantity_field', selectedField);
        }, facetView.model);
        // Remove callback when model is removed.
        facetView.model.on('remove', function(){
            qFieldSelect.model.off(null, null, this);
        }, facetView.model);

        // Update totals when the summary bar totals change.
        GeoRefine.app.summaryBar.model.on('change:data', function(){
            var data = GeoRefine.app.summaryBar.model.get('data');
            this.set('total', data.total);
        }, facetView.model);
        // Remove callback when model is removed.
        facetView.model.on('remove', function(){
            GeoRefine.app.summaryBar.model.off(null, null, this);
        }, facetView.model);

        // Have the facet update when its query or base filters or count entities change.
        if (facetView.model.getData){

            // helper function to get a timeout getData function.
            var _timeoutGetData = function(changes){
                var delay = 500;
                return setTimeout(function(){
                    var getDataOpts = {};
                    // For numeric facet, add update range flag
                    // for base_filter changes.
                    if (facetView.model.get('type') == 'numeric' 
                        && changes && changes.changes 
                        && changes.changes['base_filters']){
                            getDataOpts.updateRange = true;
                        }
                    facetView.model.getData(getDataOpts);
                    facetView.model.set('_fetch_timeout', null);
                }, delay);
            };

            facetView.model.on('change:primary_filters change:base_filters change:quantity_field', function(){

                var changes = arguments[2];
                // We delay the get data call a little, in case multiple things are changing.
                // The last change will get executed.
                var fetch_timeout = this.get('_fetch_timeout');
                // If we're fetching, clear the previous fetch.
                if (fetch_timeout){
                    clearTimeout(fetch_timeout);
                }
                // Start a new fetch.
                this.set('_fetch_timeout', _timeoutGetData(changes));
            }, facetView.model);
        }

    };

    // Helper function to get facetView.
    var getFacetViewFromEditor = function(opts){
        var facetCollection = GeoRefine.app.facetsEditor.subViews[opts.category + '_facets'];
        return facetCollection.registry[opts.id];
    };

    // Define action handlers for state loading.
    var actionHandlers = {};

    // addFacet action handler.
    actionHandlers.facets_addFacet = function(opts){
        // Shortcut to facetsEditor.
        var facetsEditor = GeoRefine.app.facetsEditor;

        if (opts.fromDefinition){
            // Get definition from predefined facets.
            var facetDef = null;
            var predefinedFacets = facetsEditor.model.get('predefined_facets');
            if (predefinedFacets){
                facetDefModel = predefinedFacets.get(opts.defId);
                if (facetDefModel){
                    facetDef = facetDefModel.get('facetDef');
                }
            }

            if (facetDef){

                // Set id on facetDef.
                facetDef.id = opts.facetId;

                // Create model from definition.
                var facetModel = facetsEditor.createFacetModelFromDef(facetDef);

                // Add to primary facet collection.
                // This will trigger handlers (see above)
                // to decorate and connect the facet.
                facetsEditor.model.get(opts.category + '_facets').add(facetModel);
            }
        }
    };

    // Initialize a facet.  Sets filters, qfield.
    actionHandlers.facets_initializeFacet = function(opts){
        // Shortcut to facetsEditor.
        var facetsEditor = GeoRefine.app.facetsEditor;

        // Get facet model.
        var facet = getFacetViewFromEditor(opts);

        // Set quantity field.
        var qfield_cid = facetsEditor.qFieldSelect.model.get('selection');
        var qfield = facetsEditor.model.get('quantity_fields').getByCid(qfield_cid);
        facet.model.set({quantity_field: qfield }, {silent: true});

        // Set filters.
        updateFacetModelPrimaryFilters(facet.model, {silent: true});
        filtersUtil.updateModelFilters(facet.model, 'base', {silent: true});

        // Set totals.
        if (GeoRefine.app.summaryBar && GeoRefine.app.summaryBar.model){
            var data = GeoRefine.app.summaryBar.model.get('data');
            if (data){
                var total = parseFloat(data.total);
                if (! isNaN(total)){
                    facet.model.set('total', total);
                }
            }
        }
    };

    // Connect facet.
    actionHandlers.facets_connectFacet = function(opts){
        // Get facet.
        var facet = GeoRefine.app.facets.registry[opts.id];
        connectFacet(facet, opts);
    };

    // getData action handler.
    actionHandlers.facets_getData = function(opts){
        // Get facet.
        var facet = getFacetViewFromEditor(opts);

        // Call get data.
        if (facet.model.getData){
            return facet.model.getData(opts);
        }
    };

    // Set Selection action handler.
    actionHandlers.facets_setSelection = function(opts){
        // Get facet.
        var facet = getFacetViewFromEditor(opts);

        // Set facet selection.
        if (facet.model.get('type') == 'timeSlider'){
            if (opts.index != null){
                var choice = facet.model.get('choices')[opts.index];
                facet.model.set('selection', choice.id);
            }
        }
    };

    // setQField action handler.
    actionHandlers.facets_facetsEditorSetQField = function(opts){
        var facetsEditor = GeoRefine.app.facetsEditor;
        var qfield = facetsEditor.model.get('quantity_fields').get(opts.id);
        facetsEditor.qFieldSelect.model.set('selection', qfield.cid);
    };

    // Define alterState hook for saving facetEditor state.
    var facetEditor_alterState = function(state){
        state.facetEditor = state.facetEditor || {};
        // Save facet editor's selected field.
        var qFieldSelect = GeoRefine.app.facetsEditor.view.qFieldSelect;
        var fieldCid = qFieldSelect.model.get('selection');
        var selectedField = GeoRefine.app.facetsEditor.model.get('quantity_fields').getByCid(fieldCid);
        state.facetEditor.selectedField = serializationUtil.serialize(selectedField, state.serializationRegistry);
    };

    // Define alterState hook for saving state of facets.
    var facets_alterState = function(state){
        state.facets = state.facets || {};

        // Save summary attributes.
        state.facets.facets = {};
        _.each(GeoRefine.app.facets.registry, function(facet, id){
            state.facets.facets[id] = serializationUtil.serialize(facet.model, state.serializationRegistry);
        });
    };

    // Define deserializeConfigState hook for facets editor.
    var facetsEditor_deserializeConfigState = function(configState, state){
        if (! configState.facetsEditor){
            return;
        }

        // Create model for facets editor.
        var facetsEditorModel = new Backbone.Model();

        // Make collections and models for facet editor sub-collections.
        _.each(['quantity_fields', 'base_facets', 'primary_facets', 'predefined_facets'], function(attr){
            var collection = new Backbone.Collection();
            _.each(configState.facetsEditor[attr], function(modelDef){
                var model = new Backbone.Model(_.extend({}, modelDef));
                collection.add(model);
            });
            facetsEditorModel.set(attr, collection);
        });

        // Make sub-models.
        _.each(['summary_bar'], function(attr){
            var modelDef = configState.facetsEditor[attr];
            var model = new Backbone.Model(_.extend({}, modelDef));
            facetsEditorModel.set(attr, model);
        });

        // Set editor in state object.
        state.facetsEditor = facetsEditorModel;
    };


    // Objects to expose.
    var facetsUtil = {
        setUpFacetsEditor: setUpFacetsEditor,
        connectFacet: connectFacet,
        actionHandlers: actionHandlers,
        alterStateHooks: [
            facetEditor_alterState,
            facets_alterState
        ],
        deserializeConfigStateHooks: [
            facetsEditor_deserializeConfigState
        ]
    };
    return facetsUtil;
});
