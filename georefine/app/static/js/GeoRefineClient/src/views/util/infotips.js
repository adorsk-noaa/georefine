define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"_s",
	"qtip",
		],
function($, Backbone, _, _s, qtip){

    // Create infotips within a given element.
    var setUpInfotips = function(opts){
        opts.selector = opts.selector || '.info-button';
        $(opts.el).on('click', opts.selector, function(event) {
            $(this).qtip({
                overwrite: false,
                content: {
                    text: $('> .content', this)
                },
                position: {
                    my: 'left center',
                    at: 'right center'
                },
                show: {
                    event: 'click',
                },
                hide: {
                    fixed: true,
                    event: 'unfocus'
                },
                style: {
                    classes: 'infotip',
                    tip: false
                },
                events: {
                    render: function(event, api){
                        // Toggle when target is clicked.
                        $(api.elements.target).on('click', function(clickEvent){
                            clickEvent.preventDefault();
                            api.toggle();
                        });
                    },
                },
            });

            $(this).qtip('show')

        });
    };

    // Objects to expose.
    var infotipsUtil = {
        setUpInfotips: setUpInfotips
    };
    return infotipsUtil;
});
