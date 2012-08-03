define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
	"./serialization",
		],
function($, Backbone, _, _s, Util, serializationUtil){

    // Sets up filters from application state.
    var setUpFilterGroups = function(){
        GeoRefine.app.filterGroups = GeoRefine.app.state.filterGroups;
    };

    // Merge a set of grouped filter objects into a list.
    // filter objects are keyed by filter group id.
    var filterObjectGroupsToArray = function(groups){
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


    // Update model's filter attributes by getting filters from its
    // filter groups.
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
