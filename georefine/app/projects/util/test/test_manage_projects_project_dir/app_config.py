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

map = {
		"max_extent" : [-180,-90,180,90],
		"graticule_intervals": [10.0],
		#"resolutions": [0.025, 0.0125, 0.00625, 0.003125, 0.0015625, 0.00078125],
		"default_layer_options" : {
			"transitionEffect": 'resize'
			},
		"default_layer_attributes": {
			"disabled": True
			},

		"base_filters" : [],
		"data_layers" : [
			{
				"id": "test1.layer",
				"name": "Test1.Layer",
				"source": "local_getmap",
				"layer_type": 'WMS',
				"layer_category": 'data',
				"options": {},
				"params": {
					"transparent": True
					},
				"entity": {
					"expression": "{Test1.id}",
					"label": "Test1.ID",
					"min": 0,
					"max": 5,
					},
				"filters": [],
				"disabled": False
				}
			],
		"base_layers": [
			{
				"id": "nurc:Img_Sample",
				"name": "nurc:Img_Sample",
				"source": "local_geoserver",
				"workspace": "nurc",
				"layer_type": "WMS",
				"layer_category": "base",
				"max_extent": "-180,-90,180,90",
				"options": {},
				"params": {
					"transparent": False,
					"layers": "nurc:Img_Sample"
					},
				"disabled": False
				}
			],
		"overlay_layers": [
				{
					"id": "nyc_roads:nyc_buildings",
					"name": "nyc_buildings",
					"source": "local_geoserver",
					"workspace": "nyc_roads",
					"layer_type": "WMS",
					"layer_category": "overlay",
					"max_extent": "-180,-90,180,90",
					"options": {},
					"params": {
						"transparent": True,
						"layers": "nyc_roads:nyc_buildings"
						},
					"disabled": False
					}
				]
		}

summary_bar = {
		"quantity_fields": [
			{
				'id': 'Test1.id:sum',
				'label': 'Test1.IDs',
				'entity': {
					'expression': 'func.sum({Test1.id})'
					}
				},
			{
				'id': 'Test1.id:avg',
				'label': 'Test1.IDs avg',
				'entity': {
					'expression': 'func.avg({Test1.id})'
					}
				}
			]
		}
		
initial_state = {
		"summary_bar": {
			"selected": "Test1.id:sum"
			},

		"data_views": [
			{
				"type": "map",
				"initial_extent": [-10, -10, 10, 10],
				"layers": [
					{
						"id":"nurc:Img_Sample",
						"attributes": {
							"disabled": True
							}
						}
					]
				},
			{
				"type": "chart",
				"initial_category_field": {
					"id": "Test1.name"
					},
				"initial_quantity_field": {
					"id": "Test1.id:sum",
					"attributes": {
						},
					"entity": {
						"min": 0
						}
					}
				}
			]
		}

