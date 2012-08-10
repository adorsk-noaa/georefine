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
	"text!./templates/shareLinkTooltip.html"
		],
function($, Backbone, _, ui, qtip, _s, Facets, MapView, Charts, Windows, Util, GeoRefineViewsUtil, template, shareLinkTooltipTemplate){

	var GeoRefineClientView = Backbone.View.extend({

		events: {
			"click .add-map-button": "addMapView",
			"click .add-chart-button": "addChartView",
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
                GeoRefine.app.config = serializedState.config;
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
            GeoRefineViewsUtil.dataViewsUtil.setUpWindows();
            GeoRefineViewsUtil.dataViewsUtil.setUpDataViews();

            this.makeShareLinkTooltip();

            this.resize();
            /*
            var stateDeferred = this.loadState();

            stateDeferred.done(function(){
                GeoRefine.app.initialized = true;
                // Call post initialize hooks.
                _.each([GeoRefineViewsUtil.facetsUtil], function(module){
                    _.each(module.postInitializeHooks, function(hook){
                        hook();
                    });
                });
            });
            */

			return this;
		},

		onReady: function(){
		},


		addMapView: function(){
            GeoRefineViewsUtil.dataViewsUtil.createFloatingDataView({
                dataView: {
                    type: 'map',
                }
            });
		},

		addChartView: function(){
            GeoRefineViewsUtil.dataViewsUtil.createFloatingDataView({
                dataView: {
                    type: 'chart'
                }
            });
		},

        resize: function(){
            this.resizeLefPanel();
            this.resizeRightPanel();
        },

        resizeLefPanel: function(){
            GeoRefine.app.facetsEditor.resize();
        },

        resizeRightPanel: function(){
            var $rp = $('.georefine-app-right-panel', this.el);
            // Get height of header.
            var headerHeight = $('> .header', $rp).outerHeight(true);
            // Set body height to be remainder.
            var bodyHeight = $rp.height() - headerHeight;
            $('> .body', $rp).height(bodyHeight);
        },

        makeShareLinkTooltip: function(){
            var $ttBody = $(_.template(shareLinkTooltipTemplate, {}));
            $('.share-link-button', this.el).qtip({
                content: {
                    text: $ttBody
                },
                position: {
                    my: 'top right',
                    at: 'bottom right'
                },
                show: {
                    event: 'click'
                },
                hide: {
                    fixed: true,
                    event: 'unfocus'
                },
                events: {
                    render: function(event, api){
                        // Toggle when target is clicked.
                        $(api.elements.target).on('click', function(clickEvent){
                            // Stop propagation.
                            clickEvent.preventDefault();

                            // Toggle the menu.
                            api.toggle();
                        });
                    },

                    show: function(event, api){
                        // Hide the link.
                        $('input.link', $ttBody).hide();

                        // Show loading.
                        $('.loading', $ttBody).show();

                        // Get state.
                        var serializedState = GeoRefineViewsUtil.stateUtil.serializeState();
                        var jsonState = JSON.stringify(serializedState);

                        // Execute key request.
                        var deferred = $.ajax({
                            url: GeoRefine.app.keyedStringsEndpoint,
                            type: 'POST',
                            data: {'s': jsonState},
                        });

                        // When key request finishes...
                        deferred.then(function(data){
                            // Assemble link url from key.
                            // @TODO
                            var linkUrl = data.key;

                            // Fill in link url in the tooltip.
                            $('input.link', $ttBody).val(linkUrl);

                            // Deactivate loading.
                            $('.loading', $ttBody).hide();

                            // Show the link.
                            $('input.link', $ttBody).show();

                        });
                    }
                }
            });
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
                        handler: 'facets_facetsEditorSetQField',
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
                                handler: 'facets_addFacet',
                                opts: {
                                    fromDefinition: true,
                                    category: 'base',
                                    defId: 'timestep',
                                    facetId: 'tstep'
                                }
                            },
                            // Initialize facet.
                            {
                                type: 'action',
                                handler: 'facets_initializeFacet',
                                opts: {
                                    category: 'base',
                                    id: 'tstep'
                                }
                            },
                            // Connect facet.
                            {
                                type: 'action',
                                handler: 'facets_connectFacet',
                                opts: {
                                    category: 'base',
                                    id: 'tstep'
                                }
                            },
                            // Load data.
                            {
                                type: 'action',
                                handler: 'facets_getData',
                                opts: {
                                    category: 'base',
                                    id: 'tstep'
                                }
                            },
                            // Select first choice.
                            {
                                type: 'action',
                                handler: 'facets_setSelection',
                                opts: {
                                    category: 'base',
                                    id: 'tstep',
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
                                handler: 'summaryBar_initialize',
                            },
                            // Connect summary bar.
                            {
                                type: 'action',
                                handler: 'summaryBar_connect',
                            },
                            // Get data for summary bar.
                            {
                                type: 'action',
                                handler: 'summaryBar_getData',
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
                                handler: 'facets_addFacet',
                                opts: {
                                    fromDefinition: true,
                                    category: 'primary',
                                    defId: 'substrates',
                                    facetId: 'initSubstrates'
                                }
                            },
                            // Initialize facet.
                            {
                                type: 'action',
                                handler: 'facets_initializeFacet',
                                opts: {
                                    category: 'primary',
                                    id: 'initSubstrates'
                                }
                            },
                            // Connect facet.
                            {
                                type: 'action',
                                handler: 'facets_connectFacet',
                                opts: {
                                    category: 'primary',
                                    id: 'initSubstrates'
                                }
                            },
                            // Load data.
                            {
                                type: 'action',
                                handler: 'facets_getData',
                                opts: {
                                    category: 'primary',
                                    id: 'initSubstrates'
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
                                        handler: 'dataViews_createFloatingDataView',
                                        opts: {
                                            id: 'initialMap',
                                            dataView: {
                                                type: 'map'
                                            }
                                        }
                                    },
                                    {
                                        type: 'action',
                                        handler: 'dataViews_setMapLayerAttributes',
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
                                        handler: 'dataViews_createFloatingDataView',
                                        opts: {
                                            id: 'initialChart',
                                            dataView: {
                                                type: 'chart'
                                            }
                                        }
                                    },
                                    {
                                        type: 'action',
                                        handler: 'dataViews_selectChartFields',
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

            var deferred = $.when(action());
            
            deferred.then(function(){
                // Set initialized state.
                console.log("All Done.");
                var serializedState = stateUtil.serializeState();
                console.log("serializedState is: ", serializedState);
                console.log("json state: ");
                console.log(JSON.stringify(serializedState));
            });

            return deferred;
        },

    });

	return GeoRefineClientView;

});

