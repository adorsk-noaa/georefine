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
        $dataViews = $('.data-views', this.el);
        var dvOffset = $data_views.offset();

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
            Util.util.fillParent(data_view.el);
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

    createMapView = function(){
        var mapEditor = mapViewUtil.createMapEditor();
        createDataViewWindow(mapEditor, {
            "title": "Map"
        });
    };

    createChartView = function(){
        var chartEditor = chartsUtil.createChartEditor();
        createDataViewWindow(chartEditor, {
            "title": "Chart"
        });
    };


    // Objects to expose.
    var dataViewUtil = {
        setUpWindows: setUpWindows,
        createMapView: createMapView,
        createChartView: createChartView,
    };
    return dataViewUtil;
});
