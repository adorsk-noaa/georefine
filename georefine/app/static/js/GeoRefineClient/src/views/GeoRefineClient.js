define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"use!ui",
    "use!qtip",
	"_s",
	"Facets",
	"MapView",
	"Charts",
	"Windows",
	"Util",
	"./util/main",
	"text!./templates/GeoRefineClient.html",
		],
function($, Backbone, _, ui, qtip, _s, Facets, MapView, Charts, Windows, Util, GeoRefineViewsUtil, template){



	var GeoRefineClientView = Backbone.View.extend({

		events: {
			"click .add-map-button": "addMapView",
			"click .add-chart-button": "addChartView"
		},

		initialize: function(opts){
			$(this.el).addClass('georefine-client');

            // Initialize global namespace variable.
            GeoRefine.app = {
                model: this.model,
                view: this,
                id: this.cid,
                config: {},
                filterGroups: null,
                facets: {},
                summaryBar: {},
                dataViews: {},
                state: {}
            };

            // If no serialized state object was given, get state from config.
            if (! opts.serializedState){
                var configState = GeoRefine.config.defaultInitialState;
                GeoRefine.app.state = GeoRefineViewsUtil.stateUtil.deserializeConfigState(configState);
                GeoRefine.app.config = GeoRefine.config;
            }
            // Otherwise deserialize serialized state.
            else{
                serializedState = opts.serializedState;
                GeoRefine.app.state = GeoRefineViewsUtil.stateUtil.deserializeState(serializedState);
                // Set config from state.
                GeoRefine.app.config = state.config;
            }

        
            // Set endpoints.
            GeoRefine.app.requestsEndpoint = _s.sprintf('%s/projects/execute_requests/%s/', GeoRefine.app.config.context_root, GeoRefine.app.config.project_id);
            GeoRefine.app.keyedStringsEndpoint = _s.sprintf('%s/ks/getKey/', GeoRefine.app.config.context_root);
            GeoRefine.app.mapEndpoint = _s.sprintf('%s/projects/get_map/%s/', GeoRefine.app.config.context_root, GeoRefine.app.config.project_id);

            // Do initial render.
			this.initialRender();

            // Listen for ready event.
			this.on('ready', this.onReady, this);
		},

		initialRender: function(){
			var html = _.template(template, {model: this.model});
			$(this.el).html(html);
            GeoRefineViewsUtil.filtersUtil.setUpFilterGroups();
            GeoRefineViewsUtil.facetsUtil.setUpFacetsEditor();
            GeoRefineViewsUtil.facetsUtil.setUpFacetCollection();
            GeoRefineViewsUtil.summaryBarUtil.setUpSummaryBar();
            GeoRefineViewsUtil.dataViewsUtil.setUpWindows();
            GeoRefineViewsUtil.dataViewsUtil.setUpDataViews();

            // When summaryBar size changes, update its parent container size.
            var sbView = GeoRefine.app.summaryBar.view;
            sbView.on('change:size', function(){
                console.log("here, change size");
                $(sbView.el).parent().height($(sbView.el).outerHeight());
            });

            this.resize();
            this.loadState();

			return this;
		},

		onReady: function(){
		},


		addMapView: function(){
            GeoRefineViewsUtil.dataViewsUtil.createDataView({
                type: 'map'
            });
		},

		addChartView: function(){
            GeoRefineViewsUtil.dataViewsUtil.createDataView({
                type: 'chart'
            });
		},

        resize: function(){
            GeoRefine.app.facetsEditor.view.resize();
        },


        loadState: function(state){

            // Shortcut.
            var stateUtil = GeoRefineViewsUtil.stateUtil;

            var actionQueue = {
                async: false,
                actions: [
                    // Setup quantity field.
                    {
                        type: 'action',
                        handler: 'facetsFacetsEditorSetQField',
                        opts: {
                            id: 'result.x:sum'
                        }
                    },

                    // Setup timestep facet.
                    {
                        type: 'actionQueue',
                        async: false,
                        actions: [
                            // Create facet.
                            {
                                type: 'action',
                                handler: 'facetsCreateFacet',
                                opts: {
                                    fromDefinition: true,
                                    id: 'timestep'
                                }
                            },
                            // Initialize facet.
                            {
                                type: 'action',
                                handler: 'facetsInitializeFacet',
                                opts: {
                                    id: 'timestep'
                                }
                            },
                            // Connect facet.
                            {
                                type: 'action',
                                handler: 'facetsConnectFacet',
                                opts: {
                                    id: 'timestep'
                                }
                            },
                            // Load data.
                            {
                                type: 'action',
                                handler: 'facetsGetData',
                                opts: {
                                    id: 'timestep'
                                }
                            },
                            // Select first choice.
                            {
                                type: 'action',
                                handler: 'facetsSetSelection',
                                opts: {
                                    id: 'timestep',
                                    index: 1
                                }
                            },

                        ]
                    },

                    // Setup summary bar.
                    {
                        type: 'actionQueue',
                        async: false,
                        actions: [
                            // Initialize summary bar.
                            {
                                type: 'action',
                                handler: 'summaryBarInitialize',
                            },
                            // Connect summary bar.
                            {
                                type: 'action',
                                handler: 'summaryBarConnect',
                            },
                            // Get data for summary bar.
                            {
                                type: 'action',
                                handler: 'summaryBarGetData',
                            },
                        ]
                    },

                    // Setup substrate facets.
                    {
                        type: 'actionQueue',
                        async: false,
                        actions: [
                            // Create facet.
                            {
                                type: 'action',
                                handler: 'facetsCreateFacet',
                                opts: {
                                    fromDefinition: true,
                                    id: 'substrates'
                                }
                            },
                            // Initialize facet.
                            {
                                type: 'action',
                                handler: 'facetsInitializeFacet',
                                opts: {
                                    id: 'substrates'
                                }
                            },
                            // Connect facet.
                            {
                                type: 'action',
                                handler: 'facetsConnectFacet',
                                opts: {
                                    id: 'substrates'
                                }
                            },
                            // Load data.
                            {
                                type: 'action',
                                handler: 'facetsGetData',
                                opts: {
                                    id: 'substrates'
                                }
                            }
                        ]
                    },

                    // Setup Data views.
                    {
                        type: 'actionQueue',
                        async: true,
                        actions: [
                            /*
                            // Mapview.
                            {
                                type: 'actionQueue',
                                async: false,
                                actions: [
                                    // Create map.
                                    {
                                        type: 'action',
                                        handler: 'dataViewsCreateDataView',
                                        opts: {
                                            id: 'initialMap',
                                            type: 'map',
                                        }
                                    },
                                    {
                                        type: 'action',
                                        handler: 'dataViewsMapSetLayerAttributes',
                                        opts: {
                                            id: 'initialMap',
                                            layers: [
                                                {
                                                    id: 'x',
                                                    attributes: {
                                                        disabled: false
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                            },
                            */
                            // ChartView.
                            {
                                type: 'actionQueue',
                                async: false,
                                actions: [
                                    // Create chart.
                                    {
                                        type: 'action',
                                        handler: 'dataViewsCreateDataView',
                                        opts: {
                                            id: 'initialChart',
                                            type: 'chart',
                                        }
                                    },
                                    {
                                        type: 'action',
                                        handler: 'dataViewsChartsSelectFields',
                                        opts: {
                                            id: 'initialChart',
                                            categoryField: {id: 'substrates'},
                                            quantityField: {id: 'result.cell.area:sum'}
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            };
            var action = stateUtil.processActionQueue(actionQueue);
            var deferred = action();

            // Load after quantity field state is set up.
            $.when(deferred).then(function(){
                console.log("All Done.");
                var serializedState = stateUtil.serializeState();
                console.log("serializedState is: ", serializedState);
                /*
                console.log("json state: ");
                console.log(JSON.stringify(serializedState));
                */
            });
        },

    });

	return GeoRefineClientView;

});

