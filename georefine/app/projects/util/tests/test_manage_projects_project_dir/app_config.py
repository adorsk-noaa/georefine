facets = [
		{
			'id': 'list_facet',
			'label': 'Substrates',
			'type': 'list',
			'grouping_entity': {
				'expression': '{Test1.name}'
				},
			'count_entity': {
				'expression': 'func.sum({Test1.id})'
				},
			},

		{
			'id': 'numeric_facet',
			'label': 'Numeric Facet',
			'type': 'numeric',
			'grouping_entity': {
				'expression': '{Test1.id}',
				'as_histogram': 'true',
				'num_buckets': 25,
				'all_values': 'true'
				},
			'count_entity': {
				'expression': 'func.sum({Test1.id})',
				}
			}
		]

charts = {
		'category_fields': [
			{
				'id': 'Test1.name',
				'entity': {
					'expression': '{Test1.name}',
					'all_values': True,
					},
				'label': 'Test1.Name',
				'value_type': 'categorical',
				},
			{
				'id': 'Test1.id',
				'entity': {
					'expression': '{Test1.id}',
					'all_values': 'true',
					'as_histogram': 'true',
					'label_type': 'numeric_histogram',
					'num_buckets': 10,
					'minauto': 'true',
					'maxauto': 'true'
					},
				'label': 'Test1.ID',
				'value_type': 'numeric',
				}
			],

		'quantity_fields' : [
			{
				'id': 'Test1.id:sum',
				'label': 'Test1.ID: Sum',
				'value_type': 'numeric',
				'entity': {
					'expression': 'func.sum({Test1.id})',
					'min': 0,
					'maxauto': 'true',
					}
				}
			]
		}
