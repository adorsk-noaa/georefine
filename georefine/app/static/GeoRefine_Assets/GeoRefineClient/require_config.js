if (typeof GRC_BASE_PATH == 'undefined'){
  GRC_BASE_PATH = "";
}
if (typeof ASSETS_PATH == 'undefined'){
  ASSETS_PATH = GRC_BASE_PATH;
}

if (typeof BASE_URL == 'undefined'){
  BASE_URL = GRC_BASE_PATH;
}

var config= {
  baseUrl: GRC_BASE_PATH,
  deps: [],
  paths: {
    requireLib: ASSETS_PATH + "/js/require",
    text: ASSETS_PATH + "/js/requirejs-text",
    rless: ASSETS_PATH + "/js/rless",
    less: ASSETS_PATH + "/js/less.js/dist/less-1.3.1",
    jquery: ASSETS_PATH + "/js/jquery",
    underscore: ASSETS_PATH + "/js/underscore.js/underscore",
    backbone: ASSETS_PATH + "/js/backbone",
    _s: ASSETS_PATH + "/js/underscore.string",
    jqplot: ASSETS_PATH + "/js/jqplot/jquery.jqplot.min",
    jqp_bar: ASSETS_PATH + "/js/jqplot/plugins/jqplot.barRenderer.min",
    jqp_cat_axis_renderer: ASSETS_PATH + "/js/jqplot/plugins/jqplot.categoryAxisRenderer.min",
    jqp_log_axis_renderer: ASSETS_PATH + "/js/jqplot/plugins/jqplot.logAxisRenderer.min",
    flot: ASSETS_PATH + "/js/flot/jquery.flot",
    DataTables: ASSETS_PATH + "/js/DataTables/media/js/jquery.dataTables.min",
    jqForm: ASSETS_PATH + "/js/jquery.form",
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
    },

    tabble: {
      deps: ["ui"]
    }
  },

  packages: [
    {
      "name": "Facets",
      "location": ASSETS_PATH + "/js/facets/src"
    },

    {
      "name": "MapView",
      "location": ASSETS_PATH + "/js/mapview/src"
    },

    {
      "name": "Dialogs",
      "location": ASSETS_PATH + "/js/dialogs/src"
    },

    {
      "name": "ExportDialog",
      "location": ASSETS_PATH + "/js/export_dialog/src"
    },

    {
      "name": "Charts",
      "location": ASSETS_PATH + "/js/charts/src"
    },

    {
      "name": "Util",
      "location": ASSETS_PATH + "/js/util/src"
    },

    {
      "name": "Windows",
      "location": ASSETS_PATH + "/js/windows/src"
    },

    {
      "name": "uiExtras",
      "location": ASSETS_PATH + "/js/jquery.ui.extras"
    },

    {
      "name": "Menus",
      "location": ASSETS_PATH + "/js/menus/src"
    },

    {
      "name": "TableSelect",
      "location": ASSETS_PATH + "/js/table_select/src"
    },

    {
      "name": "TaskStatus",
      "location": ASSETS_PATH + "/js/task_status/src"
    },

    {
      "name": "GeoRefineClient",
      "location": GRC_BASE_PATH + "/src"
    },

    {
      "name": "CommonStyles",
      "location": ASSETS_PATH + "/js/commonStyles/src"
    },

    {
      "name": "qtip",
      "location": ASSETS_PATH + "/js/jquery.qtip",
      "main": "jquery.qtip",
    },

    {
      "name": "ui",
      "location": ASSETS_PATH + "/js/jquery.ui",
      "main": "js/jquery-ui-1.9.1.custom.js"
    },

    {
      "name": "jqwindow",
      "location": ASSETS_PATH + "/js/jquery.window",
      "main": "jquery.window"
    },

    {
      "name": "openlayers",
      "location": ASSETS_PATH + "/js/openlayers",
      "main": "OpenLayers"
    },

    {
      "name": "tabble",
      "location": ASSETS_PATH + "/js/jquery.ui.tabble",
      "main": "jquery.ui.tabble"
    }
  ]

};

if (typeof require == 'undefined'){
  require = {};
}
for (var k in config){
  require[k] = config[k]
}
