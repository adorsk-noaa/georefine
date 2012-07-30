define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Facets",
	"Util",
	"./requests",
	"./functions",
	"./format"
		],
function($, Backbone, _, _s, Facets, Util, requestsUtil, functionsUtil, formatUtil){

    // Create facet collection container at the given div.
    var createFacetCollection = function(opts){
        var model = new Backbone.Collection();
        var view = new Facets.views.FacetCollectionView({
            el: opts.el,
            model: model
        });

        return {
            model: model,
            view: view
        };
    };

    // Create a list facet.
    var createNumericFacet = function(opts){

        // If opts had selection or range, 
        // convert to model.
        _.each(['selection', 'range'], function(attr){
            if (opts[attr]){
                opts[attr] = new Backbone.Model(_.extend({
                    min: null,
                    max: null
                }, opts[attr]));
            }
        });

        // Create model and view.
        var model = new Backbone.Model(_.extend({
            filtered_histogram: [],
            base_histogram: [],
            selection: new Backbone.Model({
                min: null,
                max: null
            }),
            range: new Backbone.Model({
                min: null,
                max: null
            })
        }, opts));

        var view = new Facets.views.NumericFacetView({
            model: model
        })

        // Define getData function for model.
        model.getData = function(){
            var opts = opts || {updateRange: false};
            var _this = this;

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
                url: requests_endpoint,
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


        // Define the formatFilters function for the view.
        view.formatFilters = function(selection){
            var _this = this;
            var filter_entity = _this.model.get('filter_entity');
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
        view.formatter = function(format, value){
            return formatUtil.GeoRefineFormatter(format, value);
        };

        return {
            id: opts.id,
            model: model,
            view: view
        };
        
    };

    // Create a time slider facet.
    var createTimeSliderFacet = function(opts){

        // Create model and view.
        var model = new Backbone.Model(_.extend({}, opts));
        var view = new Facets.views.TimeSliderFacetView({
            model: model
        })

        // Define getData function for model.
        model.getData = function(){
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
                url: requests_endpoint,
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
        view.formatFilters = function(selection){
            var _this = this;
            var formatted_filters = [
                [_this.model.get('filter_entity'), '==', selection]
                ];
            return formatted_filters;
        };

        return {
            id: opts.id,
            model: model,
            view: view
        };
        
    };

    // Create a list facet.
    var createListFacet = function(opts){

        // Create model and view.
        var model = new Backbone.Model(_.extend({
            choices: []
        }, opts));
        var view = new Facets.views.ListFacetView({
            model: model
        })

        // Define getData function for model.
        model.getData = function(){
            var _this = this;
            var qfield = this.get('quantity_field');

            // Copy the key entity.
            var key = JSON.parse(JSON.stringify(_this.get('KEY')));

            // Assemble request.
            var keyed_query_req = requestsUtil.makeKeyedQueryRequest(_this, key);
            var requests = [];
            requests.push(keyed_query_req);

            // Execute requests and save the deferred object.
            var deferred = $.ajax({
                url: requests_endpoint,
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
                            count_label: _grFormat(qfield.get('format') || '%s', value)
                        });
                    });
                    _this.set('choices', choices);
                }
            });

            return deferred;
        };

        // Define the formatFilters function for the view.
        view.formatFilters = function(selection){
            var _this = this;
            var formatted_filters = [];
            if (selection.length > 0){
                formatted_filters = [
                    [_this.model.get('filter_entity'), 'in', selection]
                ];
            }
            return formatted_filters;
        };

        // Define formatChoiceCountLabels function for the view.
        view.formatChoiceCountLabels = function(choices){
            var _this = this;
            var labels = [];
            var count_entity = _this.model.get('count_entity');
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

        return {
            id: opts.id,
            model: model,
            view: view
        };
        
    };


    // Create a facet from the given options.
    // This is a dispatcher for type-specific functions.
    var createFacet = function(opts){

        // Create facet models and views.
        var facet = null;
        switch (opts.type){
            case 'list':
                facet = createListFacet(opts); 
                break;
            case 'numeric':
                facet = createNumericFacet(opts); 
                break;
            case 'timeSlider':
                facet = createTimeSliderFacet(opts); 
                break;
        }

        return facet;
    };

    // Setup event chains for a facet.
    var connectFacetEvents = function(facet, filterGroups, opts){

        // Setup the facet's primary filter groups.
        _.each(facet.model.get('primary_filter_groups'), function(filterGroupId, key){
            var filterGroup = filterGroups[filterGroupId];
            filterGroup.add(facet.model);
            filter_group.on('change:filters', function(){
                var primaryFilters = _.clone(facet.model.get('primary_filters')) || {} ;
                // A facet should not use its own selection in the filters.
                primaryFilters[filterGroupId] = _.filter(filterGroup.getFilters(), 
                    function(filterObj){
                        return (filterObj.source.cid != facet.model.cid);
                    });
                facet.model.set('primary_filters', primary_filters);
            });

        });

        // Setup the facet's base filter group config.
        _.each(facet.model.get('base_filter_groups'), function(filterGroupId, key){
            var filterGroup = filterGroups[filterGroupId];
            filterGroup.on('change:filters', function(){
                var baseFilters = _.clone(model.get('base_filters')) || {};
                baseFilters[filterGroupId] = filterGroup.getFilters();
                model.set('base_filters', baseFilters);
            });
        });

        // Have the facet update when its query or base filters or count entities change.
        if (facet.model.getData){

            // helper function to get a timeout getData function.
            var _timeoutGetData = function(changes){
                var delay = 500;
                return setTimeout(function(){
                    var getDataOpts = {};
                    // For numeric facet, add update range flag
                    // for base_filter changes.
                    if (facet.model.get('type') == 'numeric' 
                        && changes && changes.changes 
                        && changes.changes['base_filters']){
                            getDataOpts.updateRange = true;
                        }
                    facet.model.getData(getDataOpts);
                    facet.model.set('_fetch_timeout', null);
                }, delay);
            };

            facet.model.on('change:primary_filters change:base_filters change:quantity_field', function(){

                var changes = arguments[2];
                // We delay the get data call a little, in case multiple things are changing.
                // The last change will get executed.
                var fetch_timeout = facet.model.get('_fetch_timeout');
                // If we're fetching, clear the previous fetch.
                if (fetch_timeout){
                    clearTimeout(fetch_timeout);
                }
                // Start a new fetch.
                facet.model.set('_fetch_timeout', _timeoutGetData(changes));
            });
        }
    };

    // Remove a facet.

    // Objects to expose.
    var facetsUtil = {
        createFacetCollection: createFacetCollection,
        connectFacetEvents: connectFacetEvents,
        actionHandlers: {
            facetsCreateFacet: function(){
                console.log("facetsCreateFacet");
            }
        }
    };
    return facetsUtil;
});
