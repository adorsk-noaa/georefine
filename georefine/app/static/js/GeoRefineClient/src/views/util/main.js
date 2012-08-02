define([
	"./facets",
	"./summaryBar",
	"./requests",
	"./filters",
	"./state",
	"./dataViews",
], 
function(facetsUtil, summaryBarUtil, requestsUtil, filtersUtil, stateUtil, dataViewsUtil){

    var GeoRefineViewsUtil = {
		facetsUtil: facetsUtil,
		summaryBarUtil: summaryBarUtil,
		requestsUtil: requestsUtil,
		filtersUtil: filtersUtil,
		stateUtil: stateUtil,
		dataViewsUtil: dataViewsUtil
	};

	return GeoRefineViewsUtil;

});
