define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
	"./requests",
	"./filters",
	"./format",
	"./serialization",
		],
function($, Backbone, _, _s, Util, requestsUtil, filtersUtil, formatUtil, serializationUtil){

    setUpSummaryBar = function(){
        
        var model = GeoRefine.app.state.summaryBar;

        // Define getData function.
        model.getData = function(){
            var _this = this;

            // Shortcuts.
            var qfield = _this.get('quantity_field');
            if (! qfield){
                return;
            }

            // Get the 'selected' query.
            var selected_inner_q = {
                'ID': 'inner',
                'SELECT_GROUP_BY': true,
            };
            requestsUtil.extendQuery(selected_inner_q, qfield.get('inner_query'));
            requestsUtil.addFiltersToQuery(model, ['primary_filters', 'base_filters'], selected_inner_q);
            var selected_q = {
                'ID': 'selected',
                'FROM': [{'ID': 'inner', 'TABLE': selected_inner_q}],
                'SELECT_GROUP_BY': true,
            };
            requestsUtil.extendQuery(selected_q, qfield.get('outer_query'));

            // Get the 'total' query.
            var total_inner_q = {
                'ID': 'inner',
                'SELECT_GROUP_BY': true,
            };
            requestsUtil.extendQuery(total_inner_q, qfield.get('inner_query'));
            requestsUtil.addFiltersToQuery(model, ['base_filters'], total_inner_q);
            var total_q = {
                'ID': 'total',
                'FROM': [{'ID': 'inner', 'TABLE': total_inner_q}],
                'SELECT_GROUP_BY': true,
            };
            requestsUtil.extendQuery(total_q, qfield.get('outer_query'));
            
            // Assemble request.
            var totals_request = {
                'ID': 'totals',
                'REQUEST': 'execute_queries',
                'PARAMETERS': {'QUERIES': [selected_q, total_q]}
            };

            var requests = [totals_request];

            var deferred = $.ajax({
                url: GeoRefine.app.requestsEndpoint,
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

            return deferred;
        };

        // Define summary bar class.
        var SummaryBarView = Backbone.View.extend({
            initialize: function(){
                $(this.el).html('<div class="inner"><div class="text"><div>Currently selected <span class="field"></span>:<div class="selected"></div><div class="total"></div></div></div>');
                // Trigger update when model data changes.
                this.model.on('change:data', this.onDataChange, this);
            },

            onDataChange: function(){
                var format = this.model.get('quantity_field').get('format') || "%s";
                var data = this.model.get('data');

                // Do nothing if data is incomplete.
                if (data.selected == null || data.total == null){
                    return;
                }

                var formatter = formatUtil.GeoRefineFormatter;
                var formatted_selected = formatter(format, data.selected);
                var formatted_total = formatter(format, data.total);
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

                this.trigger('change:size');

            }
        });

        var view = new SummaryBarView({
            el: $(".facets-panel .summary-bar", GeoRefine.app.view.el),
            model: model
        });

        // Assign to global namespace variable.
        GeoRefine.app.summaryBar = {
            model: model,
            view: view
        };

        return GeoRefine.app.summaryBar;
    };


    var connectSummaryBar = function(opts){
        // Listen for filter changes.
        _.each(['primary', 'base'], function(filterCategory){
            var groupIds = GeoRefine.app.summaryBar.model.get(filterCategory + "_filter_groups");
            _.each(groupIds, function(filterGroupId){
                var filterGroup = GeoRefine.app.filterGroups[filterGroupId];
                filterGroup.on('change:filters', function(){
                    var filters = _.clone(GeoRefine.app.summaryBar.model.get(filterCategory + '_filters')) || {};
                    filters[filterGroupId] = filterGroup.getFilters();
                    GeoRefine.app.summaryBar.model.set(filterCategory + '_filters', filters);
                });
                // Remove callback when model is removed.
                GeoRefine.app.summaryBar.model.on('remove', function(){
                    filterGroup.off(null, null, this);
                }, GeoRefine.app.summaryBar.model);
            });
        });

        // Listen for quantity field changes.
        var qFieldSelect = GeoRefine.app.facetsEditor.view.qFieldSelect;
        qFieldSelect.model.on('change:selection', function(){
            var fieldCid = qFieldSelect.model.get('selection');
            var selectedField = GeoRefine.app.facetsEditor.model.get('quantity_fields').getByCid(fieldCid);
            this.set('quantity_field', selectedField);
        }, GeoRefine.app.summaryBar.model);

        // Remove callback when model is removed.
        GeoRefine.app.summaryBar.model.on('remove', function(){
            qFieldSelect.model.off(null, null, this);
        }, GeoRefine.app.summaryBar.model);

        // Get data when parameters change.
        if (GeoRefine.app.summaryBar.model.getData){
            GeoRefine.app.summaryBar.model.on('change:primary_filters change:base_filters change:quantity_field', function(){
                GeoRefine.app.summaryBar.model.getData();
            });
        }
    };

    var actionHandlers =  {};

    // Initialize summary bar.  Sets filters, qfield.
    actionHandlers.summaryBarInitialize = function(opts){

        // Set quantity field.
        var qfield_cid = GeoRefine.app.facetsEditor.view.qFieldSelect.model.get('selection');
        var qfield = GeoRefine.app.facetsEditor.model.get('quantity_fields').getByCid(qfield_cid);

        GeoRefine.app.summaryBar.model.set({quantity_field: qfield }, {silent: true});

        // Set filters.
        _.each(['base', 'primary'], function(filterCategory){
            filtersUtil.updateModelFilters(GeoRefine.app.summaryBar.model, filterCategory, {silent: true});
        });
    };

    // Connect summaryBar.
    actionHandlers.summaryBarConnect = function(opts){
        connectSummaryBar(opts);
    };

    // getData action handler.
    actionHandlers.summaryBarGetData = function(opts){
        // Call get data.
        if (GeoRefine.app.summaryBar.model.getData){
            return GeoRefine.app.summaryBar.model.getData(opts);
        }
    };

    // Define alterState hook for saving summaryBar state.
    var summaryBar_alterState = function(state){
        // Serialize summary bar and save to state.
        state.summaryBar = serializationUtil.serialize(GeoRefine.app.summaryBar.model, state.serializationRegistry);
    };

    // Define deserializeConfigState hook for loading summaryBar state.
    var summaryBar_deserializeConfigState = function(configState, state){

        // Create model for summary bar.
        var summaryBarModel = new Backbone.Model(configState.summaryBar);

        // Set summary bar in state object.
        state.summaryBar = summaryBarModel;
    };

    // Objects to expose.
    var summaryBarUtil = {
        setUpSummaryBar: setUpSummaryBar,
        actionHandlers: actionHandlers,
        alterStateHooks: [
            summaryBar_alterState
        ],
        deserializeConfigStateHooks: [
            summaryBar_deserializeConfigState
        ]
    };
    return summaryBarUtil;
});
