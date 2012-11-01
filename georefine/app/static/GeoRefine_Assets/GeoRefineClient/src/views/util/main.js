define([
	"./facets",
	"./summaryBar",
	"./requests",
	"./filters",
	"./state",
	"./dataViews",
	"./infotips"
], 
function(facetsUtil, summaryBarUtil, requestsUtil, filtersUtil, stateUtil, dataViewsUtil, infotipsUtil){

    var GeoRefineViewsUtil = {
		facetsUtil: facetsUtil,
		summaryBarUtil: summaryBarUtil,
		requestsUtil: requestsUtil,
		filtersUtil: filtersUtil,
		stateUtil: stateUtil,
		dataViewsUtil: dataViewsUtil,
		infotipsUtil: infotipsUtil
	};

	return GeoRefineViewsUtil;

});
