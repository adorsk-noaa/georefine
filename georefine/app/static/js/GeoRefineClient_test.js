require([
  "jquery",
  "use!backbone",
  "use!underscore",
  "_s",
  "use!ui",
  "GeoRefineClient"
],
function($, Backbone, _, _s, ui, GeoRefineClient){

	GeoRefine.config = {
		"context_root" : "/georefine",
		"geoserver_url": "/geoserver",
		"project_id" : 1,

		// Start Facets.
		"facets": [
			{
				"label":"Substrates",
				"count_entity":{
					"expression":"func.sum({Test1.id})"
				},
				"type":"list",
				"id":"list_facet",
				"grouping_entity":{
					"expression":"{Test1.name}"
				}
			},
			{
				"label":"Numeric Facet",
				"count_entity":{
					"expression":"func.sum({Test1.id})"
				},
				"type":"numeric",
				"id":"numeric_facet",
				"grouping_entity":{
					"expression":"{Test1.id}",
					"all_values":"true",
					"num_buckets":25,
					"as_histogram":"true"
				}
			}
		],
		// End Facets.

		// Start Map.
		"map": {
			"default_layer_attributes":{
				"disabled":true
			},
			"default_layer_options":{
				"transitionEffect":"resize"
			},
			"base_filters":[

			],
			"max_extent":"-180,-90,180,90",
			"graticule_intervals":[
				10.0
			],
			"data_layers":[
				{
					"layer_category":"data",
					"filters":[

					],
					"source":"local_getmap",
					"disabled":false,
					"params":{
						"transparent":true
					},
					"id":"test1.layer",
					"entity":{
						"label":"Test1.ID",
						"expression":"{Test1.id}",
						"max":5,
						"min":0
					},
					"layer_type":"WMS",
					"options":{

					},
					"name":"Test1.Layer"
				}
			],
			"overlay_layers":[
				{
					"layer_category":"overlay",
					"source":"local_geoserver",
					"workspace":"nyc_roads",
					"disabled":false,
					"max_extent":"-180,-90,180,90",
					"params":{
						"transparent":true,
						"layers":"nyc_roads:nyc_buildings"
					},
					"id":"nyc_roads:nyc_buildings",
					"layer_type":"WMS",
					"options":{

					},
					"name":"nyc_buildings"
				}
			],
			"base_layers":[
				{
					"layer_category":"base",
					"source":"local_geoserver",
					"workspace":"nurc",
					"disabled":false,
					"max_extent":"-180,-90,180,90",
					"params":{
						"transparent":false,
						"layers":"nurc:Img_Sample"
					},
					"id":"nurc:Img_Sample",
					"layer_type":"WMS",
					"options":{

					},
					"name":"nurc:Img_Sample"
				}
			]
		},
		// End Map.

		// Start charts.
		"charts": {
			"category_fields": [
			{
				'id': 'Test1.name',
				'entity': {
					'expression': '{Test1.name}',
					'all_values': true
				},
				'label': 'Test1.Name',
				'value_type': 'categorical',
			},
			{
				'id': 'Test1.id',
				'entity': {
					'expression': '{Test1.id}',
					'all_values': true,
					'as_histogram': true,
					'label_type': 'numeric_histogram',
					'num_buckets': 10,
					//'min': 0,
					//'max': 3000,
					minauto: true,
					maxauto: true
				},
				'label': 'Test1.ID',
				'value_type': 'numeric',
			}
			],

				"quantity_fields": [
				{
					'id': 'Test1.id:sum',
					'label': 'Test1.ID: Sum',
					'value_type': 'numeric',
					'entity': {
						'expression': 'func.sum({Test1.id})',
						'min': 0,
						'maxauto': true,
					}
				}
			]
		}
		// End charts.
	};
	
	var grc_m = new Backbone.Model();

	var grc_v = new GeoRefineClient.views.GeoRefineClientView({
		model: grc_m,
		el: $("#main")
	});

	$(document).ready(function(){
	});

});
