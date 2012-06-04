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

	// Assumes that GeoRefine.config has been set.
	var setupFacets = function(opts){

		var facets = {};
		var lji = new Util.util.LumberjackInterpreter();

		var endpoint = _s.sprintf('/projects/get_aggregates/%s/', GeoRefine.config.project_id);

		// The 'getData' functions will be called with a facet model as 'this'.
		var listFacetGetData = function(){
			var data = {
				'filters': JSON.stringify(this.get('filters')),
				'data_entities': JSON.stringify([this.get('count_entity')]),
				'grouping_entities': JSON.stringify([this.get('grouping_entity')]),
			};
			var _this = this;
			$.ajax({
				url: endpoint,
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

		numericFacetGetData = function() {
			var data = {
				'filters': JSON.stringify(this.get('filters')),
				'data_entities': JSON.stringify([this.get('count_entity')]),
				'grouping_entities': JSON.stringify([this.get('grouping_entity')]),
				'with_unfiltered': true,
				'base_filters': JSON.stringify(this.get('base_filters'))
			};
			var _this = this;
			$.ajax({
				url: endpoint,
				type: 'GET',
				data: data,
				error: Backbone.wrapError(function(){}, _this, {}),
				success: function(data, status, xhr){

					// Parse data into histograms.
					var base_histogram = [];
					var filtered_histogram = [];

					var leafs = lji.parse(data);
					_.each(leafs, function(leaf){
						bucket_label = leaf.label;
						var minmax_regex = /(.*) to (.*)/;
						var match = minmax_regex.exec(bucket_label);
						var bmin = parseFloat(match[1]);
						var bmax = parseFloat(match[2]);

						var base_bucket = {
							bucket: leaf.label,
							min: bmin,
							max: bmax,
							count: leaf.data[0].value
						};
						base_histogram.push(base_bucket);

						var filtered_bucket = _.extend({}, base_bucket);
						filtered_bucket.count = leaf.data[1].value;
						filtered_histogram.push(filtered_bucket);

					});

					base_histogram = _.sortBy(base_histogram, function(b){return b.count});
					filtered_histogram = _.sortBy(filtered_histogram, function(b){return b.count;});

					_this.set({
						base_histogram: base_histogram,
						filtered_histogram: filtered_histogram
					});
				}
			});
		};

		// For each facet definition...
		_.each(GeoRefine.config.facets, function(facet){

			var model, view;

			if (facet.type == 'list'){
				model = new Facets.models.FacetModel(_.extend({}, facet, {
					choices: []
				}));
				model.getData = listFacetGetData;
				view = new Facets.views.ListFacetView({ model: model });
			}

			else if (facet.type == 'numeric'){
				model = new Facets.models.FacetModel(_.extend({}, facet, {
					filtered_histogram: [],
					base_histogram: []
				}));
				model.getData = numericFacetGetData;
				view = new Facets.views.NumericFacetView({ model: model });
			}

			facets[model.cid] = {
				model: model,
				view: view
			};
		});

		// Create facet collection.
		var facet_models = [];
		_.each(facets, function(facet){
			facet_models.push(facet['model'])
		});
		facet_collection_model = new Facets.models.FacetCollection(facet_models, {});
		facet_collection_view = new Facets.views.FacetCollectionView({
			el: $('#main'),
			model: facet_collection_model,
		});
		_.each(facets,function(facet){
			facet_collection_view.addFacetView(facet['view']);
		});

		facet_collection_view.updateFacets({force: true});

	};

	// Call the setup function.
	setupFacets();

});
