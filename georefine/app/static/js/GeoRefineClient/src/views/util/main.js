define([
	"./facets",
	"./requests",
	"./filters"
], 
function(facetsUtil, requestsUtil, filtersUtil){

    var GeoRefineViewsUtil = {
		facetsUtil: facetsUtil,
		requestsUtil: requestsUtil,
		filtersUtil: filtersUtil
	};

	return GeoRefineViewsUtil;

});
