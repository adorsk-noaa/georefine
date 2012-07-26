import unittest
from georefine.util.sa.tests.basetest import BaseTest
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
from georefine.app.projects.util import services
from georefine.app import db
import os

_basedir = os.path.abspath(os.path.dirname(__file__))

class Services_Test(BaseTest):

    def setUp(self):
        super(Services_Test, self).setUp()
        db.session.bind = self.connection
        self.schema = self.setUpSchemaAndData1()
        #manage_projects.setUpSchema(self.project)      
        #manage_projects.setUpData(self.project)

    def testGetKeyedResults(self):
        return #INACTIVE
        project = Project(id=1, name='test')
        project.schema = self.schema

        bucket_entity1 = {'ID': 'bucket', 'EXPRESSION': '{{test1.id}}', 'AS_HISTOGRAM': True, 'ALL_VALUES': True, 'MIN': 0, 'MAX': 5, 'NUM_BUCKETS': 5}
        #bucket_entity2 = {'ID': 'bucket', 'EXPRESSION': '{{test1.id}}', 'AS_HISTOGRAM': True, 'NUM_BUCKETS': 10, 'CONTEXT': {
            #"WHERE": [["{{test1.id}}", "in", [2,3]]]
            #}}

        key = {
                #"KEY_ENTITY" : {'EXPRESSION': '{{test1.id}}', 'ALL_VALUES': True},
                #"LABEL_ENTITY" : {'EXPRESSION': '{{test1.name}}'}
                "KEY_ENTITY" : bucket_entity1
                }

        primary_q = {
                "AS_DICTS": True, 
                "ID": "primary_q",
                "SELECT" : [
                    {'ID': "t1id", 'EXPRESSION': '{{test1.id}}'},
                    ],
                "GROUP_BY": [
                    {"ID": "t1id"},
                    bucket_entity1
                    ],
                "SELECT_GROUP_BY": True,
                }

        results = services.get_keyed_results(project, key, [primary_q])
        print results

    def testProject30KeyedResults(self):
        return #INACTIVE
        project = db.session.query(Project).filter(Project.id == 30).one()
        project.schema = manage_projects.getProjectSchema(project)

        import simplejson as json
        json_params = '''
        {
   "KEY":{
      "KEY_ENTITY":{
         "ID":"substrate_id",
         "EXPRESSION":"{{result.substrate.id}}"
      },
      "LABEL_ENTITY":{
         "ID":"substrate_name",
         "EXPRESSION":"{{result.substrate.name}}"
      }
   },
   "QUERIES":[
      {
         "SELECT":[
            {
               "ID":"count_cell_id",
               "EXPRESSION":"func.count({{inner.cell_id}})"
            }
         ],
         "FROM":[
            {
               "ID": "inner",
               "TABLE":{
                  "SELECT":[
                     {
                        "ID":"cell_id",
                        "EXPRESSION":"{{result.cell.id}}"
                     }
                  ],
                  "FROM":[],
                  "GROUP_BY":[
                     {"ID":"cell_id"},
                     {"ID":"substrate_id","EXPRESSION":"{{result.substrate.id}}" }, 
                     {"ID":"substrate_name","EXPRESSION":"{{result.substrate.name}}"}
                  ],
                  "WHERE":[
                    ["{{result.t}}", "==", "2009"]
                  ],
                  "ORDER_BY":[

                  ],
                  "ID":"inner",
                  "SELECT_GROUP_BY":true
               }
            }
         ],
         "GROUP_BY":[
                     {"ID":"substrate_id","EXPRESSION":"{{inner.substrate_id}}" }, 
                     {"ID":"substrate_name","EXPRESSION":"{{inner.substrate_name}}"}
         ],
         "WHERE":[],
         "ORDER_BY":[],
         "ID":"outer",
         "SELECT_GROUP_BY":true
      }
   ]
}
        '''


        params = json.loads(json_params)
        results = services.get_keyed_results(project, params['KEY'], params['QUERIES'])
        print results



    def testProjects30Map(self):
        return
        project = db.session.query(Project).filter(Project.id == 30).one()
        project.schema = manage_projects.getProjectSchema(project)

        request = {'args': {}}
        import simplejson as json

        json_parms = '''
        {"QUERY":{"ID":"outer","FROM":[{"ID":"inner","TABLE":{"ID":"inner","SELECT_GROUP_BY":true,"SELECT":[{"ID":"x_data","EXPRESSION":"func.sum({{result.x}}/{{result.cell.area}})"}],"GROUP_BY":[{"ID":"x_cell_id","EXPRESSION":"{{result.cell.id}}"},{"ID":"x_cell_geom","EXPRESSION":"RawColumn({{result.cell.geom}})"}],"WHERE":[{},["{{result.x}}",">=",0],["{{result.x}}","<=",6254998.2334],["{{result.t}}","==",2009]]}}],"SELECT":[{"ID":"x_geom_id","EXPRESSION":"{{inner.x_cell_id}}"},{"ID":"x_geom","EXPRESSION":"RawColumn({{inner.x_cell_geom}})"},{"ID":"x_data","EXPRESSION":"{{inner.x_data}}"}]},"GEOM_ID_ENTITY":{"ID":"x_geom_id"},"GEOM_ENTITY":{"ID":"x_geom"},"DATA_ENTITY":{"ID":"x_data","max":0.25,"min":0}}
        '''
        params = json.loads(json_parms)

        wms_parms = {}
        raw_wms_parms = 'TRANSPARENT=TRUE&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&FORMAT=image/png&SRS=EPSG:4326&BBOX=-79,31,-72.6,37.4&WIDTH=256&HEIGHT=256'
        kvs = raw_wms_parms.split('&')
        for kv in kvs:
            k, v = kv.split('=')
            wms_parms[k] = v
            
        # Parse WMS parameters.
        MAP_PARAMETERS = {}
        for wms_parameter in ['BBOX', 'FORMAT', 'WIDTH', 'HEIGHT', 'TRANSPARENT', 'SRS']:
            value = wms_parms.get(wms_parameter)
            if wms_parameter == 'WIDTH' or wms_parameter == 'HEIGHT':
                value = int(value)
            MAP_PARAMETERS[wms_parameter] = value

        map_image = services.get_map(
                project, 
                MAP_PARAMETERS = MAP_PARAMETERS,
                **params
                )

        return

    def testProjects30(self):
        project = db.session.query(Project).filter(Project.id == 30).one()
        project.schema = manage_projects.getProjectSchema(project)

        requests_json = '''
[{"ID":"keyed_results","REQUEST":"execute_keyed_queries","PARAMETERS":{"KEY":{"KEY_ENTITY":{"ID":"x","EXPRESSION":"{{result.x}}","ALL_VALUES":true,"AS_HISTOGRAM":true,"MIN":0,"MAX":100,"NUM_BUCKETS":5,"CONTEXT":{"WHERE":[["{{result.t}}","==",2008]]}}},"QUERIES":[{"ID":"base","FROM":[{"ID":"inner","TABLE":{"ID":"inner","SELECT_GROUP_BY":true,"GROUP_BY":["{{result.cell.id}}",{"ID":"cell_area"},{"ID":"x","EXPRESSION":"{{result.x}}","ALL_VALUES":true,"AS_HISTOGRAM":true,"MIN":0,"MAX":100,"NUM_BUCKETS":5,"CONTEXT":{"WHERE":[["{{result.t}}","==",2008]]}}],"SELECT":[{"ID":"cell_area","EXPRESSION":"{{result.cell.area}}/1000000.0"}],"WHERE":[["{{result.t}}","==",2008]]}}],"SELECT_GROUP_BY":true,"GROUP_BY":[{"ID":"x","EXPRESSION":"{{inner.x}}"},{"ID":"x_bucket_label","EXPRESSION":"{{inner.x_bucket_label}}"}],"SELECT":[{"ID":"sum_cell_area","EXPRESSION":"func.sum({{inner.cell_area}})"}]},{"ID":"primary","FROM":[{"ID":"inner","TABLE":{"ID":"inner","SELECT_GROUP_BY":true,"GROUP_BY":["{{result.cell.id}}",{"ID":"cell_area"},{"ID":"x","EXPRESSION":"{{result.x}}","ALL_VALUES":true,"AS_HISTOGRAM":true,"MIN":0,"MAX":100,"NUM_BUCKETS":5,"CONTEXT":{"WHERE":[["{{result.t}}","==",2008]]}}],"SELECT":[{"ID":"cell_area","EXPRESSION":"{{result.cell.area}}/1000000.0"}],"WHERE":[["{{result.t}}","==",2008]]}}],"SELECT_GROUP_BY":true,"GROUP_BY":[{"ID":"x","EXPRESSION":"{{inner.x}}"},{"ID":"x_bucket_label","EXPRESSION":"{{inner.x_bucket_label}}"}],"SELECT":[{"ID":"sum_cell_area","EXPRESSION":"func.sum({{inner.cell_area}})"}]}]}}]
        '''
        import simplejson as json
        request_defs = json.loads(requests_json)

        results = {}
        for request_def in request_defs:

            formatted_parms = {}
            for k, v in request_def['PARAMETERS'].items():
                formatted_parms[str(k)] = v

            if request_def['REQUEST'] == 'execute_keyed_queries':
                    
                r = services.execute_keyed_queries(
                        project = project,
                        **formatted_parms
                        )

            elif request_def['REQUEST'] == 'execute_queries':
                r = services.execute_queries(
                    project = project,
                    **formatted_parms
                    )

            results[request_def['ID']] = r

        #print "r is: ", json.dumps(results, indent=2)
        dstats = []
        for d in r:
            l = d['label'][1:]
            l = l[:-1]
            mn, mx = l.split(',')
            stats = {'min': mn, 'max': mx, 'label': d['label']}
            for k, v in stats.items():
                v = v.strip()
                if k == 'label': pass
                elif v == '...':
                    v = 1e20
                    if k == 'min': v = v * -1
                else:
                    v = float(v)
                stats[k] = v
            dstats.append(stats)
        sorted_stats = sorted(dstats, key=lambda s: s['min'])
        for ss in sorted_stats: print ss['label']
        #print len(r)


if __name__ == '__main__':
    unittest.main()
