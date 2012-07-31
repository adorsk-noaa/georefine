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
			'click .facets-editor-container .title': 'toggleFiltersEditor',
			"click .add-map-button": "addMapView",
			"click .add-chart-button": "addChartView"
		},

		initialize: function(){
            // Save app to global namespace.
            GeoRefine.app = {
                model: this.model,
                view: this,
                id: this.cid,
                facets: {
                    definitions: GeoRefine.config.facets.definitions,
                    registry: {}
                },
                summaryBar: {},
                dataViews: {}
            };

            // Set endpoints.
            GeoRefine.app.requestsEndpoint = _s.sprintf('%s/projects/execute_requests/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);
            GeoRefine.app.keyedStringsEndpoint = _s.sprintf('%s/ks/getKey/', GeoRefine.config.context_root);
            GeoRefine.app.mapEndpoint = _s.sprintf('%s/projects/get_map/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);

			$(this.el).addClass('georefine-client');

            this.data_view_counter = 1;
            this.data_view_defaults = {
                width: 500,
                height: 500
            };

			this.render();
			this.on('ready', this.onReady, this);

		},

		render: function(){
			var html = _.template(template, {model: this.model});
			$(this.el).html(html);

			var _this = this;
			$(document).ready(function(){
				GeoRefineViewsUtil.filtersUtil.setUpFilterGroups();
				GeoRefineViewsUtil.facetsUtil.setUpFacetCollection();
				GeoRefineViewsUtil.facetsUtil.setUpFacetsEditor();
				GeoRefineViewsUtil.dataViewsUtil.setUpWindows();
				GeoRefineViewsUtil.dataViewsUtil.setUpDataViews();
                _this.resize();
                _this.loadState();
			});

			return this;
		},

		onReady: function(){
		},


		addMapView: function(){
            GeoRefineViewsUtil.dataViewsUtil.createMapView();
		},

		addChartView: function(){
            GeoRefineViewsUtil.dataViewsUtil.createChartView();
		},

        expandContractTab: function(opts){
            var _this = this;
            var expand = opts.expand;
            var $tc = opts.tab_container;
            var $table = opts.table;
            var dim = opts.dimension;


            // Calculate how much to change dimension.
            var delta = parseInt($tc.css('max' + _s.capitalize(dim)), 10) - parseInt($tc.css('min' + _s.capitalize(dim)), 10);
            if (! expand){
                delta = -1 * delta;
            }

            // Animate field container dimension.
            $tc.addClass('changing');

            // Toggle button text
            var button_text = ($('button.toggle', $tc).html() == '\u25B2') ? '\u25BC' : '\u25B2';
            $('button.toggle', $tc).html(button_text);

            // Execute the animation.
            var tc_dim_opts = {};
            tc_dim_opts[dim] = parseInt($tc.css(dim),10) + delta;
            $tc.animate(
                    tc_dim_opts,
                    {
                        complete: function(){
                            $tc.removeClass('changing');

                            if (expand){
                                $tc.addClass('expanded')
                            }
                            else{
                                $tc.removeClass('expanded');
                                Util.util.fillParent($table);
                            }
                        }
                    }
                    );

            // Animate cell dimension.
            $tc.parent().animate(tc_dim_opts);

            // Animate table dimension.
            var table_dim_opts = {};
            table_dim_opts[dim] = parseInt($table.css(dim),10) + delta;
            $table.animate(table_dim_opts);
        },

        toggleFiltersEditor: function(){
            var $filtersEditor = $('.facets-editor-container', this.el);
            var $table = $('.facets-editor-table', this.el);
            if (! $filtersEditor.hasClass('changing')){
                this.expandContractTab({
                    expand: ! $filtersEditor.hasClass('expanded'),
                    tab_container: $filtersEditor,
                    table: $table,
                    dimension: 'width'
                });
            }
        },

        resize: function(){
            this.resizeFiltersEditor();
        },

        resizeFiltersEditor: function(){
            var $table = $('.facets-editor-table', this.el);
            Util.util.fillParent($table);
            this.resizeVerticalTab($('.facets-editor-tab', this.el)); 
            var $sbc = $('.facets-editor-table .summary-bar-container');
            $sbc.parent().css('height', $sbc.height());
        },

		resizeVerticalTab: function($vt){
			var $rc = $('.rotate-container', $vt);
			$rc.css('width', $rc.parent().height());
			$rc.css('height', $rc.parent().width());
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
                                    // Update layer urls.
                                    {
                                        type: 'action',
                                        handler: 'dataViewsMapUpdateLayerUrls',
                                        opts: {
                                            id: 'initialMap',
                                            layers: [
                                                {id: 'x'}
                                            ]
                                        }
                                    },
                                    // Activate layers.
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
            });
        },


    });

	return GeoRefineClientView;

});

