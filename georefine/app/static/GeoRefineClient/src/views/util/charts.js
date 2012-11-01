define([
	"jquery",
	"backbone",
	"underscore",
	"_s",
	"Util",
    "Charts",
    "./requests",
    "./functions",
    "./filters",
    "./format"
		],
function($, Backbone, _, _s, Util, Charts, requestsUtil, functionsUtil, filtersUtil, formatUtil){

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

    var connectChartEditor = function(chartEditor){

        // Connect the datasource's query to filter changes.
        var datasource = chartEditor.model.get('datasource');
        var q = datasource.get('query');
        _.each(['primary', 'base'], function(filterCategory){
            var groupIds = datasource.get(filterCategory + "_filter_groups");
            _.each(groupIds, function(groupId){
                var filterGroup = GeoRefine.app.filterGroups[groupId];
                filterGroup.on('change:filters', function(){
                    var filters = _.clone(q.get(filterCategory + '_filters')) || {};
                    filters[groupId] = filterGroup.getFilters();
                    q.set(filterCategory + '_filters', filters);
                }, q);

                // Remove callback when query is removed.
                q.on('remove', function(){
                    filterGroup.off(null, null, q);
                });
            });
        });
    };

    var disconnectChartEditor = function(chartEditor){
        // Disconnect datasource's query from filter changes.
        var q = chartEditor.model.get('datasource').get('query');
        _.each(['primary', 'base'], function(filterCategory){
            var groupIds = chartEditor.model.get(filterCategory + "_filter_groups");
            _.each(groupIds, function(groupId){
                var filterGroup = GeoRefine.app.filterGroups[groupId];
                filterGroup.off(null, null, q);
            });
        });

    };

    var createChartEditor = function(model){
        // Customize chart editor view to add formatting to field selectors.
        var GRChartEditorView = Charts.views.ChartEditorView.extend({
            getFieldSelectorClass: function(){
                SelectorBaseClass = Charts.views.ChartEditorView.prototype.getFieldSelectorClass.apply(this, arguments);
                GRSelector = SelectorBaseClass.extend({
                    formatter: function(){
                        var orig = SelectorBaseClass.prototype.formatter.apply(this, arguments);
                        return formatUtil.GeoRefineTokenFormatter(orig);
                    }
                });
                return GRSelector;
            }
        });

        var chartEditorView = new GRChartEditorView({
            'model': model
        });

        return chartEditorView

    };

    var decorateChartEditor = function(chartEditor){
        // Set number formatting on chart editor.
        chartEditor.chart_view.formatQuantityLabel = function(formatString, value){
            return Util.util.friendlyNumber(value,1);
        };

        // Set getData function on datasource.
        var datasource = chartEditor.model.get('datasource');
        datasource.getData = datasourceGetData;
    };

    var initializeChartEditor = function(chartEditor){
        // Decorate the chart editor.
        decorateChartEditor(chartEditor);

        // Set filters on datasource query.
        var q = chartEditor.model.get('datasource').get('query');
        _.each(['base', 'primary'], function(filterCategory){
            filtersUtil.updateModelFilters(q, filterCategory, {silent: true});
        });
    };

    // Create chart editor from config defaults.
    var createChartEditorModel = function(opts){
        var chartsConfig = _.extend({}, GeoRefine.config.charts);

        // Create models for fields.
        var processedFields = {};

        // For each field category...
        _.each(['category', 'quantity'], function(fieldType){
            var fields = chartsConfig[_s.sprintf('%s_fields', fieldType)] || [];
            var fieldModels = [];

            // For each field...
            _.each(fields, function(field){
                // Initialize entity model.
                var entityModel = null;

                // Create entity model for category field.
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
                // Create entity model for quantity field.
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

                // Assmeble the field model.
                fieldModel = new Backbone.Model(_.extend(
                            {}, 
                            field, 
                            {
                                'field_type': fieldType,
                                'entity': entityModel 
                            }
                            ));

                // Save the field model.
                fieldModels.push(fieldModel);
            });

            // Save the field collection.
            processedFields[fieldType] = new Backbone.Collection(fieldModels);
        });


        // Create schema model from fields.
        var schema = new Charts.models.SchemaModel({
            'category_fields': processedFields['category'],
            'quantity_fields': processedFields['quantity']
        });

        // Create datasource.
        var datasource = new Charts.models.DataSourceModel({
            'schema':  schema ,
            'primary_filter_groups': chartsConfig.primary_filter_groups,
            'base_filter_groups': chartsConfig.base_filter_groups,
        });

        // Create chart model.
        var chartModel = new Charts.models.XYChartModel({});

        // Create chart editor model.
        var chartEditorModel = new Backbone.Model({
            chart: chartModel,
            datasource: datasource,
            type: 'chart'
        });

        return chartEditorModel;
    }

    var selectFields = function(chartEditor, opts){
        _.each(['category', 'quantity'], function(fieldCategory){
            var fieldOpts = opts[fieldCategory + 'Field'];
            if (fieldOpts){
                // Get field from schema.
                var schema = chartEditor.model.get("datasource").get("schema");
                var fields = schema.get(fieldCategory + "_fields");
                var fieldModel = fields.get(fieldOpts.id);

                // Select field in its category's selector.
                var selector = chartEditor.fieldSelectors[fieldCategory];
                selector.field_select.model.set('selection', fieldModel.cid);
            }
        });
    };

    // Objects to expose.
    var chartsUtil = {
        createChartEditor: createChartEditor,
        createChartEditorModel: createChartEditorModel,
        connectChartEditor: connectChartEditor,
        disconnectChartEditor: disconnectChartEditor,
        initializeChartEditor: initializeChartEditor,
        selectFields: selectFields
    };
    return chartsUtil;
});
