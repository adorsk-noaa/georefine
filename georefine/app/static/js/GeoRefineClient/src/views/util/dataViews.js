define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
	"Windows",
	"./mapview",
	"./charts",
		],
function($, Backbone, _, _s, Util, Windows, mapViewUtil, chartsUtil){

    setUpDataViews = function(){
        // Initialize counter.
        GeoRefine.app.dataViews.counter = 0;

        // Initialize defaults.
        GeoRefine.app.dataViews.defaults = {
            width: 500,
            height: 500
        };
    };

    createDataViewWindow = function(dataView, opts){
        opts = opts || {};
        $dataViews = $('.data-views', GeoRefine.app.view.el);
        var dvOffset = $dataViews.offset();

        // Set default title.
        opts.title = opts.title || 'Window';

        // Add window number to title.
        opts.title = _s.sprintf("%d &middot; %s", GeoRefine.app.dataViews.counter, opts.title);

        // Merge with defaults.
        var opts = _.extend({
            "inline-block": true,
            "width": GeoRefine.app.dataViews.defaults.width,
            "height": GeoRefine.app.dataViews.defaults.height,
            // The next two lines slightly offset successive views.
            "x": (GeoRefine.app.dataViews.counter % 5) * 20,
            "y": (GeoRefine.app.dataViews.counter % 5) * 20,
            "showFooter": false,
            "scrollable": false
        }, opts);

        // Add offset to x, y
        opts.x += dvOffset.left;
        opts.y += dvOffset.top;

        // Create window for data view.
        var w =  new Windows.views.WindowView({
            model: new Backbone.Model(opts)
        });

        // Connect window events to data view.
        w.on("resize", function(){
            Util.util.fillParent(dataView.el);
            dataView.trigger('resize');
        });

        w.on("resizeStop", function(){
            dataView.trigger('resizeStop');
            Util.util.unsetWidthHeight(dataView.el);
        });
        w.on("dragStop", function(){dataView.trigger('pagePositionChange');});
        w.on("minimize", function(){dataView.trigger('deactivate');});
        w.on("cascade", function(){dataView.trigger('activate');});
        w.on("close", function(){
            dataView.trigger('remove');
            w.model = null;
            w.remove();
        });

        // Add the data view to the window and initialize.
        $(w.getBody()).append(dataView.el);
        w.resize();
        w.resizeStop();
        dataView.trigger('ready');

        // Bump counter.
        GeoRefine.app.dataViews.counter += 1;
    };

    setUpWindows = function(){
        $.window.prepare({
            "dock": "right",
            "dockArea": $('.data-views', this.el),
            "handleScrollbar": false
        });
    };

    createMapView = function(opts){
        var mapEditor = mapViewUtil.createMapEditor();
        
        // Set initial extent if given.
        if (opts.initialExtent){
            mapEditor.view.map_view.model.set('initial_extent', opts.initialExtent);
        }

        // Update filters.
        _.each(['base', 'primary'], function(filterCategory){
            mapViewUtil.updateMapEditorFilters(mapEditor, filterCategory, {silent: true});
        });

        // Set attributes on individual layers.
        _.each(opts.layers, function(layer){
            var layerModel = mapEditor.view.map_view.layers.get(layer.id);
            layerModel.set(layer.attributes);
        });

        createDataViewWindow(mapEditor.view, {
            "title": "Map"
        });
    };

    createChartView = function(opts){
        var chartEditor = chartsUtil.createChartEditor();

        // Update filters.

        var schema = chartEditor.model.get('datasource').get('schema');

        // Set category/quantity field attributes if given.
        _.each(opts.fields, function(fieldAttributes){
            var fields = schema.get(fieldAttributes.type);
            var field = fields.get(fieldAttributes.id);
            field.set(fieldAttributes);
        });

        // Select initial category/quantity fields.
        _.each(["category", "quantity"], function(fieldType){
            var initialField = opts["initial_" + fieldType + "_field"];
            if (initialField){
                var fields = schema.get(fieldType);
                var field = fields.get(initialField.id);
                var fieldSelector = chartEditor[_s.sprintf("%s_field_selector", field_type)];
                fieldSelector.model.set("selected_field", field);
            }
        });

        createDataViewWindow(chartEditor.view, {
            "title": "Chart"
        });
    };

    var actionHandlers = {};
    actionHandlers.dataViewsCreateDataView = function(opts){
        switch(opts.type){
            case 'map':
                createMapView(opts);
                break;
            case 'chart':
                createChartView(opts);
                break;
        }
    };



    // Objects to expose.
    var dataViewUtil = {
        actionHandlers: actionHandlers,
        setUpDataViews: setUpDataViews,
        setUpWindows: setUpWindows,
        createMapView: createMapView,
        createChartView: createChartView,
    };
    return dataViewUtil;
});
