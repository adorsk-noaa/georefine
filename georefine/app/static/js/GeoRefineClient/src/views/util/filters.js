define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
		],
function($, Backbone, _, _s, Util){
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

    // Objects to expose.
    var filtersUtil = {
        filterObjectGroupsToArray: filterObjectGroupsToArray
    };
    return filtersUtil;
});
