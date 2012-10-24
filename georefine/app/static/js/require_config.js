if (typeof STATIC_BASEURL == 'undefined'){
    STATIC_BASEURL = '/static';
}

if (typeof ASSETS_BASEURL == 'undefined'){
    ASSETS_BASEURL = STATIC_BASEURL + '/assets/';
}

var JQPLOT_BASE = 'js/jqplot';

var require = {
	deps: [],

	paths: {
		text: ASSETS_BASEURL + "js/require.js/plugins/text",
		jquery: ASSETS_BASEURL + "js/jquery",
		underscore: ASSETS_BASEURL + "js/underscore",
		backbone: ASSETS_BASEURL + "js/backbone",
		ui: ASSETS_BASEURL + "js/jquery.ui/jquery-ui",
		_s: ASSETS_BASEURL + "js/underscore.string",
		openlayers: ASSETS_BASEURL + "js/openlayers/openlayers",
		jqplot: ASSETS_BASEURL + JQPLOT_BASE + "/jquery.jqplot.min",
		jqp_bar: ASSETS_BASEURL + JQPLOT_BASE + "/plugins/jqplot.barRenderer.min",
		jqp_cat_axis_renderer: ASSETS_BASEURL + JQPLOT_BASE + "/plugins/jqplot.categoryAxisRenderer.min",
		jqp_log_axis_renderer: ASSETS_BASEURL + JQPLOT_BASE + "/plugins/jqplot.logAxisRenderer.min",
		flot: ASSETS_BASEURL + "js/flot/jquery.flot",
		jqwindow: ASSETS_BASEURL + "js/jquery.window/jquery.window",
		qtip: ASSETS_BASEURL + "js/jquery.qtip/jquery.qtip"
	},
	
	shim: {
		underscore: {
		  exports: "_"
		},

		backbone: {
		  deps: ["underscore", "jquery"],
		  exports: "Backbone"
		},

		ui: {
		  deps: ["jquery"],
		},

		_s: {
		  deps: ["underscore"],
		},

		openlayers: {},

		jqplot: {
		  deps: ["jquery"],
		},

		jqp_bar: {
		  deps: ["jqplot"],
		},

		jqp_cat_axis_renderer: {
		  deps: ["jqplot"],
		},

		jqp_log_axis_renderer: {
		  deps: ["jqplot"],
		},

		jqwindow: {
		  deps: ["jquery", "ui"]
		},

		qtip: {
		  deps: ["jquery"]
		},

        uiExtras: {
            deps: ["jquery", "ui"]
        },

		DataTables: {
		  deps: ["jquery"]
		},

		jqForm: {
		  deps: ["jquery"]
		}
	},

	packages: [
		{
		  "name": "FacetApp",
		  "location": ASSETS_BASEURL + "js/facet_app/src"
		},

		{
		  "name": "Facets",
		  "location": ASSETS_BASEURL + "js/facets/src"
		},

		{
		  "name": "MapView",
		  "location": ASSETS_BASEURL + "js/mapview/src"
		},
		
		{
		  "name": "Dialogs",
		  "location": ASSETS_BASEURL + "js/dialogs/src"
		},

		{
		  "name": "ExportDialog",
		  "location": ASSETS_BASEURL + "js/export_dialog/src"
		},

		{
		  "name": "Charts",
		  "location": ASSETS_BASEURL + "js/charts/src"
		},

		{
		  "name": "Util",
		  "location": ASSETS_BASEURL + "js/util/src"
		},

		{
		  "name": "Windows",
		  "location": ASSETS_BASEURL + "js/windows/src"
		},

		{
		  "name": "GeoRefineClient",
		  "location": STATIC_BASEURL + "js/GeoRefineClient/src"
		},

        {
            "name": "uiExtras",
            "location": ASSETS_BASEURL + "js/jquery.ui.extras"
        },

        {
            "name": "Menus",
            "location": ASSETS_BASEURL + "js/menus/src"
        }
	]

};
