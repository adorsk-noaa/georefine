require([
  "jquery",
  "use!backbone",
  "use!underscore",
  "_s",
  "use!ui",
  "Facets",
  "Util",
],

function($, Backbone, _, _s, ui, Facets, Util){

	var facets = {};

	// @TODO: NEED TO CREATE THIS FROM APP CONFIG.
	list_facet_model = new Facets.models.FacetModel({
		id: 'habitat_type.substrate.id',
		label: 'Substrates',
		type: 'multiselect',
		grouping_entity: {
			'expression': '{Test1.name}'
		},
		count_entity: {
			'expression': '{Test1.id}',
			'aggregate_funcs': ['sum']
		},
		choices: []
	});

	window.m = list_facet_model;

	var lji = new Util.util.LumberjackInterpreter();

	list_facet_model.getData = function() {
		// @TODO: NEED TO PUT PROJECT ID IN HERE.
		var endpoint = '/projects/get_aggregates/1/';

		var data = {
			'filters': JSON.stringify(this.get('filters')),
			'data_entities': JSON.stringify([this.get('count_entity')]),
			'grouping_entities': JSON.stringify([this.get('grouping_entity')]),
		};

		var _this = this;
		$.ajax({
			url: endpoint,
			complete: function(xhr, status){
			},
			type: 'GET',
			data: data,
			error: Backbone.wrapError(function(){}, _this, {}),
			success: function(data, status, xhr){
				// Set total.
				var total = data.data[0].value;
				_this.set('total', total, {silent:true});

				// Format choices.
				var choices = [];
				var leafs = lji.parse(data);
				_.each(leafs, function(leaf){
					choices.push({
						id: leaf.id,
						label: leaf.label,
						count: leaf.data[0].value
					});
				});
				_this.set('choices', choices);
			}
		});
	};

	list_facet_view = new Facets.views.ListFacetView({
		model: list_facet_model
	});
	facets['list_facet'] = {
		model: list_facet_model,
		view: list_facet_view
	};

	// Define fetch method for each choice facet model.
	_.each(facets, function(facet){
		facet['model'].sync = function(method, model, options) {
			if (method == 'read'){
				options = options || {};
				url_params= [];
				filters = paramsToFilters(model.get('parameters'));
				url_params.push('FILTERS=' + JSON.stringify(filters));
				url_params.push('ID_FIELD=' + model.get('count_id_field'));
				url_params.push('LABEL_FIELD=' + model.get('count_label_field'));
				url_params.push('VALUE_FIELD=' + model.get('count_value_field'));
				options.url = '/habitat/get_choice_facet/?' + url_params.join('&');
			}
			Backbone.sync(method, model, options);
		};
	});

	// Create facet collection from models.
	facet_models = [];
	_.each(facets, function(facet){
		facet_models.push(facet['model'])
	});
	f_fc = new Facets.models.FacetCollection(facet_models, {});

	// Create collection view.
	f_fv = new Facets.views.FacetCollectionView({
		el: $('#main'),
		model: f_fc,
	});

	// Add facet views to the collection view.
	_.each(facets,function(facet){
		f_fv.addFacetView(facet['view']);
	});

});
