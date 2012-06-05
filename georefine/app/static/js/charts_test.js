require([
  "jquery",
  "use!backbone",
  "use!underscore",
  "_s",
  "use!ui",
  "Dialogs",
  "Charts",
  "Util",
],
function($, Backbone, _, _s, ui, Dialogs, Charts, Util){
	
	var setupCharts = function(opts){

		var facets = {};
		var lji = new Util.util.LumberjackInterpreter();

		var endpoint = _s.sprintf('/projects/get_aggregates/%s/', GeoRefine.config.project_id);

		var charts_config = GeoRefine.config.charts;
	
		var processed_fields = {};
		_.each(['category', 'quantity'], function(field_type){
			var fields = charts_config[_s.sprintf('%s_fields', field_type)] || [];

			var field_models = [];

			_.each(fields, function(field){
				entity_model = new Backbone.Model(field['entity']);

				field_model = new Backbone.Model(_.extend({}, field, {
					'field_type': field_type,
					'entity': entity_model
				}));

				field_models.push(field_model);
			});

			processed_fields[field_type] = new Backbone.Collection(field_models);
		});


		var schema = new Charts.models.SchemaModel({
			'category_fields': processed_fields['category'],
			'quantity_fields': processed_fields['quantity']
		});

		var datasource = new Charts.models.DataSourceModel({'schema':  schema });


		datasource.getData = function() {
			var q = datasource.get('query');
			var data = {
				'filters': JSON.stringify(q.get('filters')),
				'data_entities': JSON.stringify(q.get('data_entities')),
				'grouping_entities': JSON.stringify(q.get('grouping_entities')),
			};
			var _this = this;
			$.ajax({
				url: endpoint,
				type: 'GET',
				data: data,
				complete: function(xhr, status){
					datasource.set('loading', false);
				},
				error: Backbone.wrapError(function(){}, _this, {}),
				success: function(data, status, xhr){
					datasource.set('data', lji.parse(data));
				}
			});
		};

		var chart_model = new Charts.models.XYChartModel({
		});

		var chart_editor_model = new Backbone.Model({
			'chart': chart_model,
			'datasource': datasource
		});

		var chart_editor = new Charts.views.ChartEditorView({
			el: $('#main'),
			'model': chart_editor_model
		});
	}

	setupCharts();

});
