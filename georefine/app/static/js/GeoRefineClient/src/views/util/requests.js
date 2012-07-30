define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
	"./filters"
		],
function($, Backbone, _, _s, Util, filtersUtil){

    // Extend a query by merging in other queries.
    // Note: this modifies the target query in-place.
    var extendQuery = function(target_q){
        var array_params = ['SELECT','FROM', 'WHERE', 'GROUP_BY', 'ORDER_BY'];
        var boolean_params =['SELECT_GROUP_BY'];

        _.each(Array.prototype.slice.call(arguments, 1), function(source_q) {
            _.each(array_params, function(param){
                if (target_q.hasOwnProperty(param)){
                    _.each(source_q[param], function(source_q_value){
                        if (target_q[param].indexOf(source_q_value) == -1){
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
    };

    // Add a model's filters to a query.
    var addFiltersToQuery = function(model, filter_attrs, q){
        if (! (q['WHERE'] instanceof Array)){
            q['WHERE'] = [];
        }

        _.each(filter_attrs, function(filter_attr){
            filters = model.get(filter_attr);
            filter_array = filtersUtil.filterObjectGroupsToArray(filters);
            _.each(filter_array, function(f){
                q['WHERE'].push(f);
            });
        }, this)
    };

    var makeKeyedInnerQuery = function(model, key, filter_attrs){
        // Set include filters to primary and base by default.
        filter_attrs = filter_attrs || ['primary_filters', 'base_filters'];

        // Shortcuts.
        var qfield  = model.get('quantity_field');

        // Initialize query definition.
        // Note: 'ID' must be 'inner' to conform to conventions.
        var inner_q = {
            'ID': 'inner',
            'SELECT_GROUP_BY': true,
            'GROUP_BY': []
        };

        // Merge the quantity field's inner query parameters.
        extendQuery(inner_q, qfield.get('inner_query'));

        // Add the filters.
        addFiltersToQuery(model, filter_attrs, inner_q);

        // Add key entities as group_by paramters.
        inner_q['GROUP_BY'].push(key['KEY_ENTITY']);
        if (key['LABEL_ENTITY']){
            inner_q['GROUP_BY'].push(key['LABEL_ENTITY']);
        }

        return inner_q;
    };

    var makeKeyedOuterQuery = function(model, key, inner_query, query_id){

        key = JSON.parse(JSON.stringify(key));

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
        extendQuery(outer_q, qfield.get('outer_query'));

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
    };

    var makeKeyedQueryRequest = function(model, key, filter_attrs){
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
        var inner_q = makeKeyedInnerQuery(model, key, filter_attrs);

        // Get the outer query.
        var outer_q = makeKeyedOuterQuery(model, key, inner_q, 'outer');

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
    };

    // Objects to expose.
    var requestsUtil = {
        extendQuery: extendQuery,
        addFiltersToQuery: addFiltersToQuery,
        makeKeyedInnerQuery: makeKeyedInnerQuery,
        makeKeyedOuterQuery: makeKeyedOuterQuery,
        makeKeyedQueryRequest: makeKeyedQueryRequest
    };

    return requestsUtil;
});