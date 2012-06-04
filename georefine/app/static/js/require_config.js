var ASSETS_BASEURL = '/static/sasi_assets';
var JQPLOT_BASE = '/js/jqplot';

var require = {
	deps: [],

	paths: {
		text: ASSETS_BASEURL + "/js/require.js/plugins/text",
		use: ASSETS_BASEURL + "/js/require.js/plugins/use",
		jquery: ASSETS_BASEURL + "/js/jquery",
		underscore: ASSETS_BASEURL + "/js/underscore",
		backbone: ASSETS_BASEURL + "/js/backbone",
		ui: ASSETS_BASEURL + "/js/jquery.ui/jquery-ui",
		_s: ASSETS_BASEURL + "/js/underscore.string",
		openlayers: ASSETS_BASEURL + "/js/openlayers/openlayers",
		jqplot: ASSETS_BASEURL + JQPLOT_BASE + "/jquery.jqplot.min",
		jqp_bar: ASSETS_BASEURL + JQPLOT_BASE + "/plugins/jqplot.barRenderer.min",
		jqp_cat_axis_renderer: ASSETS_BASEURL + JQPLOT_BASE + "/plugins/jqplot.categoryAxisRenderer.min",
		jqp_log_axis_renderer: ASSETS_BASEURL + JQPLOT_BASE + "/plugins/jqplot.logAxisRenderer.min",
		flot: ASSETS_BASEURL + "/js/flot/jquery.flot"
	},
	
	use: {
		backbone: {
		  deps: ["use!underscore", "jquery"],
		  attach: "Backbone"
		},

		underscore: {
		  attach: "_"
		},

		ui: {
		  deps: ["jquery"],
		  attach: "ui"
		},

		_s: {
		  deps: ["use!underscore"],
		  attach: "_s"
		},

		openlayers: {
		  attach: "ol"
		},

		jqplot: {
		  deps: ["jquery"],
		  attach: "jqplot"
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

		flot: {
		  deps: ["jquery"],
		  attach: "flot"
		},

	},

	packages: [
		{
		  "name": "FacetApp",
		  "location": ASSETS_BASEURL + "/js/facet_app/src"
		},

		{
		  "name": "Facets",
		  "location": ASSETS_BASEURL + "/js/facets/src"
		},

		{
		  "name": "MapView",
		  "location": ASSETS_BASEURL + "/js/mapview/src"
		},
		
		{
		  "name": "Dialogs",
		  "location": ASSETS_BASEURL + "/js/dialogs/src"
		},

		{
		  "name": "ExportDialog",
		  "location": ASSETS_BASEURL + "/js/export_dialog/src"
		},

		{
		  "name": "Charts",
		  "location": ASSETS_BASEURL + "/js/charts/src"
		}
	]

};
