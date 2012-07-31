define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
    "Charts",
    "./requests",
    "./functions"
		],
function($, Backbone, _, _s, Util, Charts, requestsUtil, functionsUtil){

    // This function will be used by chart datasources to
    // get data.
    // The 'this' object will be a datasource model.
    datasourceGetData = function() {
        var q = this.get('query');
        if (! q){
            return;
        }

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
        requestsUtil.addFiltersToQuery(q, ['base_filters'], key_context);

        // Get the base query.
        var base_inner_q = requestsUtil.makeKeyedInnerQuery(q, key, ['base_filters']);
        var base_outer_q = requestsUtil.makeKeyedOuterQuery(q, key, base_inner_q, 'base');

        // Get the primary query.
        var primary_inner_q = requestsUtil.makeKeyedInnerQuery(q, key, ['base_filters', 'primary_filters']);
        var primary_outer_q = requestsUtil.makeKeyedOuterQuery(q, key, primary_inner_q, 'primary');

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

        var _this = this;
        var deferred = $.ajax({
            url: GeoRefine.app.requestsEndpoint,
            type: 'POST',
            data: {'requests': JSON.stringify(requests)},
            complete: function(){
                _this.set('loading', false);
            },
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
                        var bminmax = functionsUtil.parseBucketLabel(result['label']);
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

                _this.set('data', chart_data);
            }
        });
    };


    createChartEditor = function(){
        var chartsConfig = GeoRefine.config.charts;

        // Create models for fields.
        var processedFields = {};
        _.each(['category', 'quantity'], function(fieldType){
            var fields = chartsConfig[_s.sprintf('%s_fields', fieldType)] || [];
            var fieldModels = [];
            _.each(fields, function(field){
                var entityModel = null;
                if (fieldType == 'category'){
                    var entityDefaults = {};
                    if (field.value_type == 'numeric'){
                        _.extend(entityDefaults, {
                            "num_classes": 5,
                            "min": 0,
                            "maxauto": true
                        });
                    }
                    entityModel = new Backbone.Model(
                        _.extend(entityDefaults, field['KEY']['KEY_ENTITY'])
                        );
                }
                else if (fieldType =='quantity'){
                    var entityDefaults = {
                        'min': 0,
                'maxauto': true
                    };
                    var quantityEntity = field['outer_query']['SELECT'][0];
                    entityModel = new Backbone.Model(
                            _.extend(entityDefaults, quantityEntity)
                            );
                }
            fieldModel = new Backbone.Model(_.extend({}, 
                        field, 
                        {
                            'field_type': fieldType,
                       'entity': entityModel 
                        }));

            fieldModels.push(fieldModel);
            });

            processedFields[fieldType] = new Backbone.Collection(fieldModels);
        });


        // Create schema model from fields.
        var schema = new Charts.models.SchemaModel({
            'category_fields': processedFields['category'],
            'quantity_fields': processedFields['quantity']
        });

        // Create datasource.
        var datasource = new Charts.models.DataSourceModel({'schema':  schema });

        // Set getData function.
        datasource.getData = datasourceGetData;


        // Connect the datasource's query to filter changes.
        var q = datasource.get('query');
        // Have layer model listen for filter changes.
        _.each(['primary', 'base'], function(filterCategory){
            var groupIds = chartsConfig[filterCategory + "_filter_groups"];
            _.each(groupIds, function(groupId){
                var filterGroup = GeoRefine.app.filterGroups[groupId];
                filterGroup.on('change:filters', function(){
                    var filters = _.clone(q.get(filterCategory + '_filters')) || {};
                    filters[groupId] = filterGroup.getFilters();
                    model.set(filterCategory + '_filters', filters);
                });
            }, this);
        });

        // Create chart model.
        var chartModel = new Charts.models.XYChartModel({});

        // Create chart editor.
        var chartEditorModel = new Backbone.Model({
            'chart': chartModel,
            'datasource': datasource
        });
        var chartEditorView = new Charts.views.ChartEditorView({
            'model': chartEditorModel
        });

        // Set number formatting on chart editor.
        chartEditorView.chart_view.formatQuantityLabel = function(formatString, value){
            return Util.util.friendlyNumber(value,1);
        };

        return {
            model: chartEditorModel,
            view: chartEditorView
        };
    };

    var updateChartEditorFilters = function(chartEditor, filterCategory, opts){
        var q = chartEditor.model.get('datasource').get('query');
        var filters = _.clone(q.get(filterCategory + '_filters')) || {} ;
        _.each(q.get(filterCategory + '_filter_groups'), function(filterGroupId, key){
            var filterGroup = GeoRefine.app.filterGroups[filterGroupId];
            filters[filterGroupId] = filterGroup.getFilters();
        });
        var setObj = {};
        setObj[filterCategory + '_filters'] = filters;
        q.set(setObj, opts);
    };

    // Objects to expose.
    var chartsUtil = {
        createChartEditor: createChartEditor
    };
    return chartsUtil;
});
