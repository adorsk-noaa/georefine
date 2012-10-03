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
            opts = opts || {};
			$(this.el).addClass('georefine-client');

            // Listen for ready event.
            this.on('ready', this.onReady, this);

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
                state: {},
                tokens: {}
            };

            // Set endpoints
            GeoRefine.app.requestsEndpoint = _s.sprintf('%s/projects/execute_requests/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);
            GeoRefine.app.keyedStringsEndpoint = _s.sprintf('%s/ks', GeoRefine.config.context_root);
            GeoRefine.app.dataLayerEndpoint = _s.sprintf('%s/projects/get_map/%s/', GeoRefine.config.context_root, GeoRefine.config.project_id);
            GeoRefine.app.WMSLayerEndpoint = _s.sprintf('%s/projects/%s/layer', GeoRefine.config.context_root, GeoRefine.config.project_id);

            // Set tokens.
            GeoRefine.app.tokens = {
                PROJECT_STATIC_DIR: GeoRefine.config.project_static_dir
            };

            // Parse url hash for options.
            var hash = window.location.hash;

            // Parse state key.
            if (keyMatch = /\/stateKey=(.*)\//.exec(hash)){
                opts.stateKey = keyMatch[1];
            }

            // Deferred object for handling state load.
            var stateDeferred = $.Deferred();

            // If a state key was given...
            if (opts.stateKey){
                // Load the state from the server.
                $.ajax({
                    url: GeoRefine.app.keyedStringsEndpoint + '/getString/' + opts.stateKey,
                    type: 'GET',
                    success: function(data){
                        // Deserialize and save the resulting state string.
                        serializedState = JSON.parse(data.s);
                        GeoRefine.app.state = GeoRefineViewsUtil.stateUtil.deserializeState(serializedState);
                        // Resolve the deferred.
                        stateDeferred.resolve();
                    }
                });
            }

            // Otherwise if serialized state was passed in options...
            else if (opts.serializedState){
                GeoRefine.app.state = GeoRefineViewsUtil.stateUtil.deserializeState(opts.serializedState);
                // Resolve the deferred.
                stateDeferred.resolve();
            }

            // Otherwise, get state from config.
            else{
                var configState = GeoRefine.config.defaultInitialState;
                GeoRefine.app.state = GeoRefineViewsUtil.stateUtil.deserializeConfigState(configState);
                // Resolve the deferred.
                stateDeferred.resolve();
            }

            // When stateDeferred resolves, continue...
            var _this = this;
            stateDeferred.then(function(){
                // Do initial render.
                _this.initialRender();

                // Process initial actions.
                var actionsDeferred = _this.executeInitialActions();

                // When actions are done...
                actionsDeferred.done(function(){

                    // Set initialized.
                    GeoRefine.app.initialized = true;

                    // Trigger ready.
                    _this.trigger("ready");

                    _this.postInitialize();

                });

            });
        },

        postInitialize: function(){
            // Listen for window resize events.
            this.on('resize', this.resize, this);
            var _this = this;
            var onWindowResize = function(){
                if (_this._windowResizeTimeout){
                    clearTimeout(_this.windowResizeTimeout);
                }
                _this.windowResizeTimeout = setTimeout(function(){
                    _this._windowResizeTimeout = false;
                    _this.trigger('resize');
                }, 200);
            };
            $(window).resize(onWindowResize);

            // Call post initialize hooks.
            _.each(GeoRefineViewsUtil, function(module){
                _.each(module.postInitializeHooks, function(hook){
                    hook();
                });
            });

            // Setup infotips.
            GeoRefineViewsUtil.infotipsUtil.setUpInfotips({
                el: this.el
            });
        },

		initialRender: function(){
			var html = _.template(template, {model: this.model});
			$(this.el).html(html);
            GeoRefineViewsUtil.filtersUtil.setUpFilterGroups();
            GeoRefineViewsUtil.facetsUtil.setUpFacetsEditor();
            GeoRefineViewsUtil.dataViewsUtil.setUpWindows();
            GeoRefineViewsUtil.dataViewsUtil.setUpDataViews();

            this.makeShareLinkTooltip();
		},

		onReady: function(){
            this.resize();
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
            this.resizeLeftCell();
            this.resizeRightCell();
        },

        resizeLeftCell: function(){
            GeoRefine.app.facetsEditor.trigger('resize');
        },

        resizeRightCell: function(){
            var $rc = $('.right-cell', this.el);
            // Get height of header.
            var headerHeight = $('> .inner > .header', $rc).outerHeight(true);
            // Set body height to be remainder.
            var bodyHeight = $rc.height() - headerHeight;
            $('> .inner > .body', $rc).height(bodyHeight);
        },

        makeShareLinkTooltip: function(){
            var $ttBody = $(_.template(shareLinkTooltipTemplate, {}));
            $('.share-link-button', this.el).qtip({
                content: {
                    text: $ttBody
                },
                position: {
                    my: 'top right',
                    at: 'bottom right',
                    adjust: {
                        y: 5
                    }
                },
                show: {
                    event: 'click'
                },
                hide: {
                    fixed: true,
                    event: 'unfocus'
                },
                style: {
                    classes: 'share-link-tooltip',
                    tip: false
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
                        // Set loading text.
                        $('input.link', $ttBody).prop('disabled', true);
                        $('input.link', $ttBody).val('  loading...');
                        $('input.link', $ttBody).addClass('loading');

                        // Get state.
                        var serializedState = GeoRefineViewsUtil.stateUtil.serializeState();
                        var jsonState = JSON.stringify(serializedState);

                        deferred = $.ajax({
                            url: GeoRefine.app.keyedStringsEndpoint + '/getKey/',
                            type: 'POST',
                            data: {'s': jsonState},
                        });

                        // When key request finishes...
                        deferred.then(function(data){
                            // Assemble link url from key.
                            var keyStateHash = _s.sprintf('#/stateKey=%s/', data.key);
                            var linkUrl = window.location.origin + window.location.pathname + keyStateHash;
                            // Fill in link url in the tooltip after a slight delay.
                            setTimeout(function(){
                                $('input.link', $ttBody).val(linkUrl);
                                $('input.link', $ttBody).removeClass('loading');
                                $('input.link', $ttBody).prop('disabled', false);
                            }, 1500);

                        });
                    }
                }
            });
        },

        executeInitialActions: function(){

            var deferred = $.Deferred();

            // If there were initial actions, process them.
            if (GeoRefine.app.state.initialActionQueue){
                var actionsFunc = GeoRefineViewsUtil.stateUtil.processActionQueue(GeoRefine.app.state.initialActionQueue);
                // Resolve the deferred when actions complete.
                $.when(actionsFunc()).then(function(){
                    deferred.resolve();
                });
            }
            // Otherwise resolve the deferred immediately.
            else{
                deferred.resolve();
            }

            return deferred;
        },

    });

	return GeoRefineClientView;

});

