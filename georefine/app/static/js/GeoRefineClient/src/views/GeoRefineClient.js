define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"use!ui",
	"_s",
	"text!./templates/GeoRefineClient.html"
		],
function($, Backbone, _, ui, _s, template){

	var GeoRefineClientView = Backbone.View.extend({

		events: {
		},

		initialize: function(){
			$(this.el).addClass('gr-client');
			this.render();
			this.on('ready', this.onReady, this);
		},

		render: function(){
			var html = _.template(template, {model: this.model.toJSON()});
			$(this.el).html(html);

			return this;
		},

		onReady: function(){
		}

	});

	return GeoRefineClientView;
});
		
