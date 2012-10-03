require([
  "jquery",
  "use!backbone",
  "use!underscore",
  "_s",
  "use!ui",
  "GeoRefineClient"
],

function($, Backbone, _, _s, ui, GeoRefineClient){

    // Define initial facets state.
    var facetsEditorState = {

        quantity_fields: {
            'qf_1': {
                'id': 'qf_1',
                'label': 'Quantity Field 1',
                'info': 'QF1 Info',
                'value_type': 'numeric',
                'inner_query': {},
                'outer_query': {},
                'key_entity_expression': '',
            }
        },

        facets: {
            'f1': {
                'id': 'f1',
                'label': 'Facet 1',
                'info' : 'Facet 1 info',
                'type': 'list',
                'KEY': {},
                'primary_filter_groups': [],
                'base_filter_groups': [],
                'filter_entity': {}
            }
        }

    };

    GeoRefine = {};
    GeoRefine.config = {
        context_root: 'test_context_root',
        defaultInitialState: {
            facetsEditor: facetsEditorState
        }
    };

    grc = new GeoRefineClient.views.GeoRefineClientView({
        el: $('#main')
    });

	$(document).ready(function(){
	});
});
