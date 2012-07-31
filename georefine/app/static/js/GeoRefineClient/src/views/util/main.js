define([
	"./facets",
	"./requests",
	"./filters",
	"./state",
	"./dataViews",
], 
function(facetsUtil, requestsUtil, filtersUtil, stateUtil, dataViewsUtil){

    var GeoRefineViewsUtil = {
		facetsUtil: facetsUtil,
		requestsUtil: requestsUtil,
		filtersUtil: filtersUtil,
		stateUtil: stateUtil,
		dataViewsUtil: dataViewsUtil
	};

	return GeoRefineViewsUtil;

});
