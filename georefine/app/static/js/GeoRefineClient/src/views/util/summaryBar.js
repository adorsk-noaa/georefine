define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
	"./requests",
	"./facets",
	"./format",
		],
function($, Backbone, _, _s, Util, requestsUtil, facetsUtil, formatUtil){

    // shortcut.
    var _summaryBar;

    setUpSummaryBar = function(){
        var model = new Backbone.Model({
            "id": "summary_bar",
            "primary_filters": {},
            "base_filters": {},
            "quantity_field": null,
            "data": {}
        });

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
                $(this.el).html('<div class="text"><div>Currently selected <span class="field"></span>:<div class="selected"></div><div class="total"></div></div>');
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

                // Set totals on facets.
                _.each(GeoRefine.app.facets.facetCollection.models, function(facetModel){
                    facetModel.set('total', data.total);
                });
            }
        });

        var view = new SummaryBarView({
            el: $(".facets-editor .summary-bar", GeoRefine.app.view.el),
            model: model
        });

        // Assign to global namespace variable.
        GeoRefine.app.summaryBar = {
            model: model,
            view: view
        };

        // Set shortcut.
        _summaryBar = GeoRefine.app.summaryBar;

        return GeoRefine.app.summaryBar;
    };


    var updateSummaryBarFilters = function(summaryBar, filterCategory, opts){
        var filters = _.clone(summaryBar.model.get(filterCategory + '_filters')) || {} ;
        _.each(summaryBar.model.get(filterCategory + '_filter_groups'), function(filterGroupId, key){
            var filterGroup = GeoRefine.app.filterGroups[filterGroupId];
            filters[filterGroupId] = filterGroup.getFilters();
        });
        var setObj = {};
        setObj[filterCategory + '_filters'] = filters;
        summaryBar.model.set(setObj, opts);
    };

    var connectSummaryBar = function(opts){
        // Listen for filter changes.
        _.each(['primary', 'base'], function(filterCategory){
            var groupIds = _summaryBar.model.get(filterCategory + "_filter_groups");
            _.each(groupIds, function(filterGroupId){
                var filterGroup = GeoRefine.app.filterGroups[filterGroupId];
                filterGroup.on('change:filters', function(){
                    var filters = _.clone(_summaryBar.model.get(filterCategory + '_filters')) || {};
                    filters[filterGroupId] = filterGroup.getFilters();
                    _summaryBar.model.set(filterCategory + '_filters', filters);
                });
            });
        });
        // Get data when parameters change.
        if (_summaryBar.model.getData){
            _summaryBar.model.on('change:primary_filters change:base_filters change:quantity_field', function(){
                _summaryBar.model.getData();
            });
        }
    };

    var actionHandlers =  {};

    // Initialize summary bar.  Sets filters, qfield.
    actionHandlers.summaryBarInitialize = function(opts){

        // Set quantity field.
        console.log(GeoRefine.app.facets);
        var qfield_cid = GeoRefine.app.facets.facetEditor.qFieldSelect.model.get('selection');
        var qfield = GeoRefine.app.facets.qFields.getByCid(qfield_cid);

        _summaryBar.model.set({quantity_field: qfield }, {silent: true});

        // Set filters.
        _.each(['base', 'primary'], function(filterCategory){
            updateSummaryBarFilters(_summaryBar, filterCategory, {silent: true});
        });
    };

    // Connect summaryBar.
    actionHandlers.summaryBarConnect = function(opts){
        connectSummaryBar(opts);
    };

    // getData action handler.
    actionHandlers.summaryBarGetData = function(opts){
        // Call get data.
        if (_summaryBar.model.getData){
            return _summaryBar.model.getData(opts);
        }
    };

    // Objects to expose.
    var summaryBarUtil = {
        setUpSummaryBar: setUpSummaryBar,
        actionHandlers: actionHandlers
    };
    return summaryBarUtil;
});
