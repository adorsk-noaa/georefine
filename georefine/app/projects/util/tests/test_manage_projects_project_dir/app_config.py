facets = [
		{
			'id': 'list_facet',
			'label': 'Substrates',
			'type': 'list',
			'grouping_entity': {
				'expression': '{Test1.name}'
				},
			'count_entity': {
				'expression': '{Test1.id}',
				'aggregate_funcs': ['sum']
				},
			},

		{
			'id': 'numeric_facet',
			'label': 'Numeric Facet',
			'type': 'numeric',
			'grouping_entity': {
				'expression': '{Test1.id}',
				'as_histogram': true,
				'num_buckets': 25,
				'all_values': true
				},
			'count_entity': {
				'expression': '{Test1.id}',
				'aggregate_funcs': ['sum']
				}
			}
		]
