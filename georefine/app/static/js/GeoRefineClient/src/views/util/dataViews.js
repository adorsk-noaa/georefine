define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
	"Windows",
	"./mapview",
	"./charts",
	"./serialization",
		],
function($, Backbone, _, _s, Util, Windows, mapViewUtil, chartsUtil, serializationUtil){

    var setUpDataViews = function(){
        // Shortcut to dataViews state.
        var dvState = GeoRefine.app.state.dataViews || {};

        // Initialize counter.
        GeoRefine.app.dataViews.counter = dvState.counter || 0;

        // Initialize defaults.
        GeoRefine.app.dataViews.defaults = dvState.defaults || {
            width: 500,
            height: 500
        };

        // Initialize collection.
        GeoRefine.app.dataViews.dataViews = dvState.dataViews || new Backbone.Collection();

        // Create any initial data views.
        _.each(GeoRefine.app.dataViews.dataViews, function(dataView){
            addFloatingDataView(dataView);
        });
    };

    var setUpWindows = function(){
        $.window.prepare({
            "dock": "right",
            "dockArea": $('.data-views', this.el),
            "handleScrollbar": false
        });
    };

    // Define data view factory functions.
    var dataViewFactories = {};
    dataViewFactories['map'] = mapViewUtil.createMapEditor;
    dataViewFactories['chart'] = chartsUtil.createChartEditor;

    // Define data view initialization functions.
    var dataViewInitializers = {};
    dataViewInitializers['map'] = mapViewUtil.initializeMapEditor;
    dataViewInitializers['chart'] = chartsUtil.initializeChartEditor;

    // Dispatcher function for initializing.
    var initializeDataView = function(dataView){
        var initializer = dataViewInitializers[dataView.model.get('type')];
        if (initializer){
            console.log("here")
            initializer(dataView);
        }
    };

    // Define data view connect functions.
    var dataViewConnectors = {};
    dataViewConnectors['map'] = {
        connect: mapViewUtil.connectMapEditor,
        disconnect: mapViewUtil.disconnectMapEditor
    };
    dataViewConnectors['chart'] = {
        connect: chartsUtil.connectChartEditor,
        disconnect: chartsUtil.disconnectChartEditor
    };

    // Dispatcher function for connecting.
    var getDataViewConnector = function(dataView, connect){
        var connector = dataViewConnectors[dataView.model.get('type')];
        if (connector){
            return (connect) ? connector.connect : connector.disconnect;
        }
    };
    var connectDataView = function(dataView){
        console.log("connecting");
        connect = getDataViewConnector(dataView, true);
        if (connect){
            connect(dataView);
        }
    };
    var disconnectDataView = function(dataView){
        disconnect = getDataViewConnector(dataView, false);
        if (disconnect){
            disconnect(dataView);
        }
    };


    // View that combines DataView and Window models.
    var FloatingDataViewView = Backbone.View.extend({

        initialize: function(){

            this.initialRender();

            // Connect window events to data view.
            this.window.on("resize", function(){
                Util.util.fillParent(this.dataView.el);
                this.dataView.trigger('resize');
            }, this);

            this.window.on("resizeStop", function(){
                this.dataView.trigger('resizeStop');
                Util.util.unsetWidthHeight(this.dataView.el);
            }, this);

            _.each(['pagePositionChange', 'deactive', 'activate'], function(event){
                this.window.on(event, function(){
                    this.dataView.trigger(event);
                }, this);
            }, this);

            this.window.on("close", this.remove, this);

            // Resize.
            this.window.resize();
            this.window.resizeStop();

            this.dataView.trigger('ready');

            // Bump counter.
            GeoRefine.app.dataViews.counter += 1;
        },

        initialRender: function(){
            this.renderDataView();
            this.renderWindow();
            $(this.window.getBody()).append(this.dataView.el);
        },

        renderDataView: function(){
            var factory = dataViewFactories[this.model.get('dataView').get('type')];
            this.dataView = factory(this.model.get('dataView'));
        },

        renderWindow : function(){
            var $dataViews = $('.data-views', GeoRefine.app.view.el);
            var dvOffset = $dataViews.offset();

            this.window = new Windows.views.WindowView({
                model: this.model.get('window')
            });
        },

        remove: function(){
            this.trigger('remove');
            this.dataView.trigger('remove');
            this.window.trigger('remove');
        }
    });

    var addFloatingDataView = function(model){
        // Set default id if none given.
        if (! model.id){
            model.id = model.cid;
        }

        // Create floating data view.
        var floatingDataView = new FloatingDataViewView({
            model: model
        });

        // Initialize and connect data view.
        initializeDataView(floatingDataView.dataView);
        connectDataView(floatingDataView.dataView);

    };

    // Create default data view window model.
    var createDefaultWindowModel = function(opts){
        opts = opts || {};

        // Get data views container offset.
        $dataViews = $('.data-views', GeoRefine.app.view.el);
        var dvOffset = $dataViews.offset();

        // Set default title.
        opts.title = opts.title || 'Window';

        // Add window number to title.
        opts.title = _s.sprintf("%d &middot; %s", GeoRefine.app.dataViews.counter, opts.title);

        // Merge with defaults.
        opts = _.extend({
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

        // Create model.
        var model = new Backbone.Model(opts);

        return model;

    };

    // Factories for creating default dataView models.
    var dataViewModelFactories = {};
    dataViewModelFactories['map'] = mapViewUtil.createMapEditorModel;
    dataViewModelFactories['chart'] = chartsUtil.createChartEditorModel;

    createDataViewModel = function(opts){
        opts = opts || {};

        var factory = dataViewModelFactories[opts.type];
        if (factory){
            return factory(opts);
        }

    };

    // Create a new data view from config defaults.
    var createDataView = function(opts){
        opts = opts || {};

        // Get window model.
        var windowModel = createDefaultWindowModel(opts.window);

        // Create default dataView model for given type.
        var dataViewModel = createDataViewModel(opts.dataView);

        if (windowModel && dataViewModel){
            // Create floating data view model.
            var floatingDataViewModel = new Backbone.Model({
                window: windowModel,
                dataView: dataViewModel
            });

            // Create floating data view.
            addFloatingDataView(floatingDataViewModel);
        }
    };

    var actionHandlers = {};
    actionHandlers.dataViews_createDataView = function(opts){
        createDataView(opts);
    };

    actionHandlers.dataViews_setMapLayerAttributes = function(opts){
        var dataView = GeoRefine.app.dataViews.registry[opts.id];
        var mapEditor = dataView.dataView;
        _.each(opts.layers, function(layer){
            var layer = mapViewUtil.getMapEditorLayers(mapEditor, {layers: [layer]}).pop();
            layer.model.set(layer.attributes);
        });
    };

    actionHandlers.dataViews_selectChartFields = function(opts){
        var dataView = GeoRefine.app.dataViews.registry[opts.id];
        var chartEditor = dataView.dataView;
        chartsUtil.selectFields(chartEditor, opts);
    };

    // Define alterState hook to add states of data views.
    dataViews_alterState = function(state){
        state.dataViews = state.dataViews || {};

        state.dataViews.dataViews = {};
        _.each(GeoRefine.app.dataViews.registry, function(dataView, id){
            state.dataViews.dataViews[id] = {
                dataView: serializationUtil.serialize(dataView.dataView.model, state.serializationRegistry),
                window: serializationUtil.serialize(dataView.window.model, state.serializationRegistry)
            }
        });
    };

    // Objects to expose.
    var dataViewUtil = {
        actionHandlers: actionHandlers,
        setUpDataViews: setUpDataViews,
        setUpWindows: setUpWindows,
        createDataView: createDataView,
        alterStateHooks: [
            dataViews_alterState
        ]
    };
    return dataViewUtil;
});
