define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
	"./serialization",
		],
function($, Backbone, _, _s, Util, serializationUtil){
    // Merge a set of grouped filter objects into a list.
    // filter objects are keyed by filter group id.
    filterObjectGroupsToArray = function(groups){
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
    };

    setUpFilterGroups = function(){
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
    };

    var updateModelFilters = function(model, filterCategory, opts){
        var filters = _.clone(model.get(filterCategory + '_filters')) || {} ;
        _.each(model.get(filterCategory + '_filter_groups'), function(filterGroupId, key){
            var filterGroup = GeoRefine.app.filterGroups[filterGroupId];
            filters[filterGroupId] = filterGroup.getFilters();
        });
        var setObj = {};
        setObj[filterCategory + '_filters'] = filters;
        model.set(setObj, opts);
    };

    // Define alterState hook for saving filterGroup state.
    var filterGroups_alterState = function(state){
        // Save filter group ids.
        state.filterGroups = state.filterGroups || {};
        _.each(GeoRefine.app.filterGroups, function(filterGroup, id){
            state.filterGroups[id] = serializationUtil.serialize(filterGroup, state.serializationRegistry);
        });
    };

    // Objects to expose.
    var filtersUtil = {
        filterObjectGroupsToArray: filterObjectGroupsToArray,
        setUpFilterGroups: setUpFilterGroups,
        updateModelFilters: updateModelFilters,
        alterStateHooks : [
            filterGroups_alterState
        ]
    };
    return filtersUtil;
});
