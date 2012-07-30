define([
	"./facets",
	"./requests",
	"./filters",
	"./state"
], 
function(facetsUtil, requestsUtil, filtersUtil, stateUtil){

    var GeoRefineViewsUtil = {
		facetsUtil: facetsUtil,
		requestsUtil: requestsUtil,
		filtersUtil: filtersUtil,
		stateUtil: stateUtil
	};

	return GeoRefineViewsUtil;

});
