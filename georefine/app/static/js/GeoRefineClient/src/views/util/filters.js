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

        // Decorate filter groups.
        _.each(GeoRefine.app.filterGroups, function(filterGroup, filterGroupId){
            // Define getFilters method for each filter group.
            // @TODO! Move this into a separate function, rather than having
            // it be a method of the filter group ?
            filterGroup.getFilters = function(){
                var filters = [];
                _.each(filterGroup.models, function(model){
                    var modelFilters = model.get('filters');
                    if (modelFilters){
                        filters.push({
                            'source': {
                                'type': model.getFilterType ? model.getFilterType() : null,
                            'id': model.id
                            },
                            'filters': modelFilters
                        });
                    }
                });
                return filters;
            };

            // Add registration function to set id on new members, for 
            // determining filter sources w/in the group.
            filterGroup.on('add', function(model){
                var filterGroupIds = model.get("filterGroupIds") || {};
                if (! filterGroupIds[filterGroupId]){
                    filterGroupIds[filterGroupId] = Date.now() + Math.random();
                }
                model.set("filterGroupIds", filterGroupIds);
            });

        });
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

    // Define deserializeConfigState hook for filter groups.
    var filterGroups_deserializeConfigState = function(configState, state){
        if (! configState.filterGroups){
            return;
        }

        // Create collections for filter groups.
        var filterGroups = {};

        _.each(configState.filterGroups, function(filterGroupDef){
            var filterGroup = new Backbone.Collection();
            filterGroups[filterGroupDef.id] = filterGroup;
        });

        // Set editor in state object.
        state.filterGroups = filterGroups;
    };

    // Objects to expose.
    var filtersUtil = {
        filterObjectGroupsToArray: filterObjectGroupsToArray,
        setUpFilterGroups: setUpFilterGroups,
        updateModelFilters: updateModelFilters,
        alterStateHooks : [
            filterGroups_alterState
        ],
        deserializeConfigStateHooks: [
            filterGroups_deserializeConfigState
        ]
    };
    return filtersUtil;
});
