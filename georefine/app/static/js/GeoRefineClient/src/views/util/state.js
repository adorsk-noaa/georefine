define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"Util",
	"./facets",
	"./summaryBar",
		],
function($, Backbone, _, _s, Util, facetsUtil, summaryBarUtil){

    // Registry for action handlers, to be populated
    // by other modules as well.
    var actionHandlers = {};
    _.each([facetsUtil, summaryBarUtil], function(module){
        _.each(module.actionHandlers, function(handler, id){
            actionHandlers[id] = handler;
        });
    });

    // TESTING! Test handler.
    actionHandlers['testHandler'] = function(opts){
        console.log("executing", JSON.stringify(opts));
        return $.Deferred(function(){
            var _this = this;
            setTimeout(function(){
                console.log('testHandler', JSON.stringify(opts));
                _this.resolve();
            }, opts.delay || 200);
        });

    };

    // Convert an action definition to an action function.
    var processAction = function(action){
        // Get handler for action.
        var handler = actionHandlers[action.handler];
        // Return handler bound w/ action opts.
        return function(){
            return handler(action.opts); 
        };
    };

    // Convert an action queue definition to an action function.
    var processActionQueue = function(actionQueue){

        var action = function(){
            var deferred = $.Deferred();

            // If there were child actions...
            if (actionQueue.actions.length > 0){

                // Convert child actions into action functions.
                var actionFuncs = [];
                _.each(actionQueue.actions, function(action){
                    var actionFunc = null;
                    if (action.type == 'action'){
                        actionFunc = processAction(action);
                    }
                    else if (action.type == 'actionQueue'){
                        actionFunc = processActionQueue(action);
                    }
                    actionFuncs.push(actionFunc);
                });


                // Deferred representing deferred form final child action.
                var finalDeferred = null;

                // If async, execute actions in parallel.
                if (actionQueue.async){
                    var deferreds = [];
                    _.each(actionFuncs, function(actionFunc){
                        deferreds.push(actionFunc());
                    });
                    finalDeferred = $.when.apply($, deferreds);
                }

                // Otherwise, execute actions in sequence.
                else{
                    // Initialize with first action.
                    finalDeferred = $.when(actionFuncs[0]());
                    // Trigger subsequent subactions in sequence.
                    for (var i = 1; i < actionFuncs.length; i++){
                        var i_ = i;
                        finalDeferred = finalDeferred.pipe(function(){
                            return $.when(actionFuncs[i_]());
                        });
                    }
                }

                // When final deferred is complete, resolve.
                finalDeferred.done(function(){
                    deferred.resolve();
                });
            }
            // If there were no child actions, resolve immediately.
            else{
                deferred.resolve();
            }

            return deferred;
        };

        return action;
    };

    // Objects to expose.
    var stateUtil = {
        processActionQueue: processActionQueue
    };

    return stateUtil;
});
