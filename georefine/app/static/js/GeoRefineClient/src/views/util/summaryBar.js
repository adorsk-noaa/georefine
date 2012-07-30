define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
	"./requests",
		],
function($, Backbone, _, _s, Util, requestsUtil){

    setUpSummaryBar = function(){
        var model = new Backbone.Model({
            "id": "summary_bar",
            "primary_filters": {},
            "base_filters": {},
            "quantity_field": null,
            "data": {}
        });

        // Listen for filter changes.
        _.each(['primary', 'base'], function(filterCategory){
            var groupIds = GeoRefine.config.summary_bar[filterCategory + "_filter_groups"];
            _.each(groupIds, function(filterGroupId){
                var filterGroup = GeoRefine.app.filterGroups[filterGroupId];
                filterGroup.on('change:filters', function(){
                    var filters = _.clone(model.get(filterCategory + '_filters')) || {};
                    filters[filterGroupId] = filterGroup.getFilters();
                    model.set(attr + '_filters', filters);
                });
            });
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

            return deferred;
        };

        // Define summary bar class.
        var SummaryBarView = Backbone.View.extend({
            initialize: function(){
                $(this.el).html('<div class="text"><div>Currently selected <span class="field"></span>:<div class="selected"></div><div class="total"></div></div>');
                // Trigger update when model data changes.
                this.model.on('change:data', this.onDataChange, this);

                // Get data when parameters change.
                if (this.model.getData){
                    var _this = this;
                    this.model.on('change:primary_filters change:base_filters change:quantity_field', function(){
                        this.model.getData();
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
                _.each(GeoRefine.app.facets.facetCollection.models, function(facetModel){
                    facetMmodel.set('total', data.total);
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

        return GeoRefine.app.summaryBar;
    };

    // Objects to expose.
    var summaryBarUtil = {
        setUpSummaryBar: setUpSummaryBar
    };
    return summaryBarUtil;
});
