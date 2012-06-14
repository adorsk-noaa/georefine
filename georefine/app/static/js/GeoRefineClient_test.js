require([
  "jquery",
  "use!backbone",
  "use!underscore",
  "_s",
  "use!ui",
  "GeoRefineClient"
],
function($, Backbone, _, _s, ui, GeoRefineClient){
	
	console.log('here');

	var grc_m = new Backbone.Model();

	var grc_v = new GeoRefineClient.views.GeoRefineClientView({
		model: grc_m,
		el: $("#main")
	});

	$(document).ready(function(){
	});

});
